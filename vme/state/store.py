"""Transactional SQLite (WAL) store for every durable record.

All learning state is disk-owned (Addendum 24 D1). Records are append-only and
versioned: an update writes a new version row; nothing committed is overwritten.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, List

from ..util import Blocked, canonical_json, digest, now_iso

SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS records (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    rtype TEXT NOT NULL,
    rid TEXT NOT NULL,
    version INTEGER NOT NULL,
    body TEXT NOT NULL,
    body_sha TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(rtype, rid, version)
);
CREATE INDEX IF NOT EXISTS records_type ON records(rtype, rid);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    ref TEXT,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS packets (
    packet_id TEXT PRIMARY KEY,
    film_sha256 TEXT NOT NULL,
    pass_id TEXT NOT NULL,
    cluster_id TEXT NOT NULL,
    start_frame INTEGER NOT NULL,
    end_frame INTEGER NOT NULL,
    state TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    provider_task_id TEXT,
    manifest_sha TEXT,
    response_path TEXT,
    response_sha TEXT,
    semantic_manifest_sha TEXT,
    cost_usd REAL,
    error TEXT,
    updated_at TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS frame_vision (
    film_sha256 TEXT NOT NULL,
    frame_index INTEGER NOT NULL,
    pass_id TEXT NOT NULL,
    status TEXT NOT NULL,
    packet_id TEXT,
    image_sha TEXT,
    observation_sha TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(film_sha256, frame_index, pass_id)
);
CREATE TABLE IF NOT EXISTS jobs (
    job_key TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    state TEXT NOT NULL,
    provider TEXT NOT NULL,
    task_uuid TEXT,
    payload_sha TEXT,
    response_path TEXT,
    cost_usd REAL,
    updated_at TEXT NOT NULL,
    body TEXT NOT NULL
);
"""


class Store:
    """Thin transactional wrapper. One writer at a time (single decision owner)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.path), isolation_level=None, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=FULL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(_DDL)
        with self.tx():
            self.conn.execute("INSERT OR IGNORE INTO meta(k,v) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))

    def close(self) -> None:
        try:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.Error:
            pass
        self.conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                yield self.conn
            except BaseException:
                self.conn.execute("ROLLBACK")
                raise
            else:
                self.conn.execute("COMMIT")

    # ---- versioned typed records -------------------------------------------------
    def put(self, rtype: str, rid: str, body: Any, *, conn: sqlite3.Connection | None = None) -> int:
        text = canonical_json(body)
        sha = digest(body)

        def _do(c: sqlite3.Connection) -> int:
            row = c.execute("SELECT MAX(version), (SELECT body_sha FROM records WHERE rtype=? AND rid=? ORDER BY version DESC LIMIT 1) FROM records WHERE rtype=? AND rid=?",
                            (rtype, rid, rtype, rid)).fetchone()
            ver = (row[0] or 0)
            if row[1] == sha:
                return ver  # idempotent: identical body already latest
            ver += 1
            c.execute("INSERT INTO records(rtype,rid,version,body,body_sha,created_at) VALUES(?,?,?,?,?,?)",
                      (rtype, rid, ver, text, sha, now_iso()))
            return ver

        if conn is not None:
            return _do(conn)
        with self.tx() as c:
            return _do(c)

    def get(self, rtype: str, rid: str, version: int | None = None) -> Any | None:
        if version is None:
            row = self.conn.execute("SELECT body FROM records WHERE rtype=? AND rid=? ORDER BY version DESC LIMIT 1", (rtype, rid)).fetchone()
        else:
            row = self.conn.execute("SELECT body FROM records WHERE rtype=? AND rid=? AND version=?", (rtype, rid, version)).fetchone()
        return json.loads(row[0]) if row else None

    def versions(self, rtype: str, rid: str) -> list[dict]:
        rows = self.conn.execute("SELECT version, body, body_sha, created_at FROM records WHERE rtype=? AND rid=? ORDER BY version", (rtype, rid)).fetchall()
        return [{"version": v, "body": json.loads(b), "sha": s, "created_at": t} for v, b, s, t in rows]

    def list(self, rtype: str) -> list[Any]:
        rows = self.conn.execute(
            "SELECT r.body FROM records r JOIN (SELECT rid, MAX(version) mv FROM records WHERE rtype=? GROUP BY rid) m "
            "ON r.rid=m.rid AND r.version=m.mv WHERE r.rtype=? ORDER BY r.seq", (rtype, rtype)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def list_types(self) -> List[str]:
        return [r[0] for r in self.conn.execute("SELECT DISTINCT rtype FROM records ORDER BY rtype")]

    def event(self, kind: str, ref: str | None, body: Any, *, conn: sqlite3.Connection | None = None) -> None:
        c = conn or self.conn
        if conn is None:
            with self.tx() as cc:
                cc.execute("INSERT INTO events(kind,ref,body,created_at) VALUES(?,?,?,?)", (kind, ref, canonical_json(body), now_iso()))
        else:
            c.execute("INSERT INTO events(kind,ref,body,created_at) VALUES(?,?,?,?)", (kind, ref, canonical_json(body), now_iso()))

    def events(self, kind: str | None = None) -> List[dict]:
        if kind:
            rows = self.conn.execute("SELECT seq,kind,ref,body,created_at FROM events WHERE kind=? ORDER BY seq", (kind,)).fetchall()
        else:
            rows = self.conn.execute("SELECT seq,kind,ref,body,created_at FROM events ORDER BY seq").fetchall()
        return [{"seq": s, "kind": k, "ref": r, "body": json.loads(b), "at": t} for s, k, r, b, t in rows]

    # ---- coherent snapshot for portable handoff ---------------------------------
    def snapshot_to(self, dest: str | Path) -> str:
        """Coherent copy via SQLite backup API (never a naked WAL file copy)."""
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        target = sqlite3.connect(str(dest))
        with self._lock:
            self.conn.backup(target)
        target.execute("PRAGMA journal_mode=DELETE")
        target.close()
        from ..util import sha256_file
        return sha256_file(dest)

    def integrity_ok(self) -> bool:
        return self.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def open_store(path: str | Path) -> Store:
    s = Store(path)
    if not s.integrity_ok():
        raise Blocked("STORE_CORRUPT", str(path))
    return s
