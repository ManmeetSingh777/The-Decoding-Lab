"""Transactional spend-reservation ledger (R07).

Row: (reservation_id, auth_id, provider, logical_job_id, estimated_max_cost, status, actual_cost, provider_receipt).
Statuses: RESERVED -> SETTLED | SETTLED_COST_UNKNOWN | RELEASED | LIABILITY_UNKNOWN.

* reserve-before-submit happens in ONE `BEGIN IMMEDIATE` SQLite transaction that sums every open or settled
  exposure for the authorization, so concurrent processes/threads cannot overrun a cap;
* settle-on-receipt is idempotent (a second settle of the same job is a no-op, never double counted);
* uncertain acceptance keeps the estimate as an outstanding LIABILITY (counts against the cap) until a human
  reconciles it; a DEFINITELY rejected request releases its reservation;
* repeating a logical job returns its existing reservation instead of reserving again.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from ..util import Blocked, canonical_json, new_id, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS reservations (
  reservation_id TEXT PRIMARY KEY, auth_id TEXT NOT NULL, provider TEXT NOT NULL, logical_job_id TEXT NOT NULL,
  estimated_max_cost REAL NOT NULL, status TEXT NOT NULL, actual_cost REAL, provider_receipt TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, history TEXT NOT NULL,
  UNIQUE(auth_id, logical_job_id));
"""
OPEN = ("RESERVED", "LIABILITY_UNKNOWN", "SETTLED_COST_UNKNOWN")


class SpendLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        c = self._conn()
        try:
            self._retry(lambda: c.executescript(SCHEMA))
        finally:
            c.close()

    @staticmethod
    def _retry(fn, attempts: int = 200):
        """journal-mode switches and DDL can return SQLITE_BUSY without the busy handler under multi-process start-up."""
        for i in range(attempts):
            try:
                return fn()
            except sqlite3.OperationalError as e:
                if "locked" not in str(e) and "busy" not in str(e):
                    raise
                time.sleep(0.01 * min(20, i + 1))
        raise Blocked("LEDGER_LOCK_TIMEOUT")

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        c.execute("PRAGMA busy_timeout=30000")
        self._retry(lambda: c.execute("PRAGMA journal_mode=WAL"))
        return c

    def _row(self, c, auth_id: str, job: str):
        r = c.execute("SELECT reservation_id, status, estimated_max_cost, actual_cost, provider_receipt FROM reservations "
                      "WHERE auth_id=? AND logical_job_id=?", (auth_id, job)).fetchone()
        return None if r is None else {"reservation_id": r[0], "status": r[1], "estimated_max_cost": r[2], "actual_cost": r[3],
                                       "provider_receipt": r[4]}

    @staticmethod
    def _exposure(c, auth_id: str) -> float:
        settled = c.execute("SELECT COALESCE(SUM(actual_cost),0) FROM reservations WHERE auth_id=? AND status='SETTLED'",
                            (auth_id,)).fetchone()[0]
        open_ = c.execute(f"SELECT COALESCE(SUM(estimated_max_cost),0) FROM reservations WHERE auth_id=? AND status IN "
                          f"({','.join('?' * len(OPEN))})", (auth_id, *OPEN)).fetchone()[0]
        return float(settled) + float(open_)

    def exposure(self, auth_id: str) -> float:
        c = self._conn()
        try:
            return self._exposure(c, auth_id)
        finally:
            c.close()

    def reserve(self, *, auth_id: str, provider: str, cap_usd: float, logical_job_id: str, estimated_max_cost: float) -> dict:
        if estimated_max_cost is None or estimated_max_cost < 0:
            raise Blocked("COST_UNKNOWN_STOP", "no verified cost estimate; refusing to reserve")
        c = self._conn()
        try:
            for attempt in range(50):
                try:
                    c.execute("BEGIN IMMEDIATE")
                    break
                except sqlite3.OperationalError:
                    time.sleep(0.05 * (attempt + 1))
            else:
                raise Blocked("LEDGER_LOCK_TIMEOUT")
            try:
                ex = self._row(c, auth_id, logical_job_id)
                if ex and ex["status"] != "RELEASED":
                    c.execute("COMMIT")
                    return {**ex, "reused": True}
                exposure = self._exposure(c, auth_id)
                if exposure + estimated_max_cost > cap_usd + 1e-9:
                    c.execute("ROLLBACK")
                    raise Blocked("SPEND_CAP_EXCEEDED", f"exposure {exposure:.4f} + reservation {estimated_max_cost:.4f} > cap {cap_usd}")
                rid = ex["reservation_id"] if ex else new_id("res")
                hist = canonical_json([{"status": "RESERVED", "at": now_iso(), "est": estimated_max_cost}])
                if ex:
                    c.execute("UPDATE reservations SET status='RESERVED', estimated_max_cost=?, actual_cost=NULL, updated_at=?, history=? "
                              "WHERE reservation_id=?", (estimated_max_cost, now_iso(), hist, rid))
                else:
                    c.execute("INSERT INTO reservations VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                              (rid, auth_id, provider, logical_job_id, float(estimated_max_cost), "RESERVED", None, None, now_iso(), now_iso(), hist))
                c.execute("COMMIT")
                return {"reservation_id": rid, "status": "RESERVED", "estimated_max_cost": estimated_max_cost, "reused": False}
            except Blocked:
                raise
            except Exception:
                c.execute("ROLLBACK")
                raise
        finally:
            c.close()

    def _transition(self, rid: str, to: str, allowed_from: tuple, **cols) -> dict:
        c = self._conn()
        try:
            self._retry(lambda: c.execute("BEGIN IMMEDIATE"))
            r = c.execute("SELECT status, history FROM reservations WHERE reservation_id=?", (rid,)).fetchone()
            if r is None:
                c.execute("ROLLBACK")
                raise Blocked("RESERVATION_NOT_FOUND", rid)
            if r[0] == to or r[0] not in allowed_from:
                c.execute("COMMIT")
                return {"reservation_id": rid, "status": r[0], "changed": False}
            import json as _j
            hist = _j.loads(r[1]) + [{"status": to, "at": now_iso(), **{k: v for k, v in cols.items()}}]
            sets = ["status=?", "updated_at=?", "history=?"] + [f"{k}=?" for k in cols]
            c.execute(f"UPDATE reservations SET {', '.join(sets)} WHERE reservation_id=?",
                      [to, now_iso(), canonical_json(hist)] + list(cols.values()) + [rid])
            c.execute("COMMIT")
            return {"reservation_id": rid, "status": to, "changed": True}
        finally:
            c.close()

    def settle(self, rid: str, *, actual_cost: float | None, receipt: dict | str) -> dict:
        rc = receipt if isinstance(receipt, str) else canonical_json(receipt)
        if actual_cost is None:
            return self._transition(rid, "SETTLED_COST_UNKNOWN", ("RESERVED", "LIABILITY_UNKNOWN"), provider_receipt=rc)
        return self._transition(rid, "SETTLED", ("RESERVED", "LIABILITY_UNKNOWN", "SETTLED_COST_UNKNOWN"),
                                actual_cost=float(actual_cost), provider_receipt=rc)

    def release(self, rid: str, *, reason: str) -> dict:
        return self._transition(rid, "RELEASED", ("RESERVED", "LIABILITY_UNKNOWN"), provider_receipt=canonical_json({"released": reason}))

    def mark_liability(self, rid: str, *, reason: str) -> dict:
        return self._transition(rid, "LIABILITY_UNKNOWN", ("RESERVED",), provider_receipt=canonical_json({"uncertain": reason}))

    def rows(self, auth_id: str | None = None) -> list[dict]:
        c = self._conn()
        try:
            q = "SELECT reservation_id, auth_id, provider, logical_job_id, estimated_max_cost, status, actual_cost, provider_receipt FROM reservations"
            rs = c.execute(q + (" WHERE auth_id=?" if auth_id else "") + " ORDER BY created_at", (auth_id,) if auth_id else ()).fetchall()
            keys = ("reservation_id", "auth_id", "provider", "logical_job_id", "estimated_max_cost", "status", "actual_cost", "provider_receipt")
            return [dict(zip(keys, r)) for r in rs]
        finally:
            c.close()
