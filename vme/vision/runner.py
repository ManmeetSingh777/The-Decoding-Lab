"""Bounded per-frame packet planning, WAL state machine, crash points and semantic resume.

Spec 10 §3–§6, Addendum 24 D2, Addendum 25 §2.2, A19/A61–A66, B03–B08, ADD25-F01..F08/R01/R02.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

from ..util import (Blocked, atomic_write_bytes, atomic_write_json, canonical_json, digest, now_iso,
                    read_json, sha256_file)
from ..state.store import Store
from .contracts import frame_id_for, validate_packet_response
from .prompt import VISION_PROMPT_VERSION, build_vision_request

TRANSFORM_VERSION = "png-native/1"
CRASH_ENV = "VME_CRASH_AT"
CRASH_POINTS = ("after_inputs_ready", "after_inflight_commit", "after_submit_before_save", "after_raw_response",
                "mid_semantic_commit", "after_semantic_commit")


class SimulatedCrash(BaseException):
    """In-process crash (tests); subprocess drills use a hard os._exit instead."""


def maybe_crash(point: str) -> None:
    at = os.environ.get(CRASH_ENV)
    if at == point:
        if os.environ.get("VME_CRASH_HARD") == "1":
            os._exit(97)  # real kill: no cleanup, no finally blocks
        raise SimulatedCrash(point)


@dataclass
class PacketPlan:
    packet_id: str
    film_sha256: str
    pass_id: str
    cluster_id: str
    target_indices: list
    context_before: list
    context_after: list
    model_version: str
    prompt_version: str
    transform_version: str
    frame_manifest_sha: str
    idempotency_key: str

    def to_dict(self) -> dict:
        return asdict(self)


def plan_packets(index: list[dict], start: int, end_inclusive: int, *, film_sha: str, pass_id: str, cluster_id: str,
                 model_version: str, max_images: int, target_per_packet: int = 8, context: int = 2) -> list[PacketPlan]:
    """Contiguous non-overlapping target packets covering EXACTLY [start..end] (ADD25-F01, F07)."""
    if not (0 <= start <= end_inclusive < len(index)):
        raise Blocked("RANGE_OUTSIDE_INDEX", f"[{start},{end_inclusive}] of {len(index)}")
    if max_images < 1:
        raise Blocked("PROVIDER_ACCEPTS_NO_IMAGES")
    # shrink context first, then targets, so target coverage is never sacrificed
    ctx = min(context, max(0, (max_images - 1) // 2))
    per = max(1, min(target_per_packet, max_images - 2 * ctx))
    plans = []
    i = start
    while i <= end_inclusive:
        j = min(end_inclusive, i + per - 1)
        tgt = list(range(i, j + 1))
        before = [k for k in range(i - ctx, i) if k >= 0]
        after = [k for k in range(j + 1, j + 1 + ctx) if k < len(index)]
        man = [{"i": k, "pts": index[k]["pts"], "sha": index[k]["frame_content_sha256"]} for k in before + tgt + after]
        msha = digest(man)
        pid = digest({"film": film_sha, "s": i, "e": j, "manifest": msha, "pass": pass_id, "cluster": cluster_id,
                      "model": model_version, "prompt": VISION_PROMPT_VERSION, "transform": TRANSFORM_VERSION})[:32]
        plans.append(PacketPlan(f"pkt_{pid}", film_sha, pass_id, cluster_id, tgt, before, after, model_version,
                                VISION_PROMPT_VERSION, TRANSFORM_VERSION, msha, f"idem_{pid}"))
        i = j + 1
    covered = [k for p in plans for k in p.target_indices]
    if covered != list(range(start, end_inclusive + 1)):
        raise Blocked("PLAN_COVERAGE_BUG")
    return plans


FrameLoader = Callable[[dict], dict]  # index record -> {"png": bytes, "png_sha": str, "raw_sha": str, "w","h","scale"}


class PacketRunner:
    def __init__(self, store: Store, vision_dir: str | Path, index: list[dict], frame_loader: FrameLoader,
                 provider, *, source_is_synthetic: bool, active_questions: list[dict] | None = None):
        self.store = store
        self.vdir = Path(vision_dir)
        self.index = index
        self.load = frame_loader
        self.provider = provider
        self.synthetic = source_is_synthetic
        self.questions = active_questions or []
        if provider.kind == "MOCK" and not source_is_synthetic:
            raise Blocked("MOCK_PROVIDER_ON_REAL_SOURCE_FORBIDDEN",
                          "mock observations must never enter real film coverage")

    # ---- ledger helpers -----------------------------------------------------------
    def _row(self, pid: str):
        return self.store.conn.execute("SELECT state, provider_task_id, response_path, response_sha, manifest_sha, body "
                                       "FROM packets WHERE packet_id=?", (pid,)).fetchone()

    def _set(self, pid: str, state: str, c=None, **cols) -> None:
        sets = ", ".join([f"{k}=?" for k in cols] + ["state=?", "updated_at=?"])
        vals = list(cols.values()) + [state, now_iso(), pid]
        (c or self.store.conn).execute(f"UPDATE packets SET {sets} WHERE packet_id=?", vals)
        self.store.event("PACKET_STATE", pid, {"state": state, **{k: v for k, v in cols.items() if k != "body"}}, conn=c)

    def register(self, plans: list[PacketPlan]) -> None:
        with self.store.tx() as c:
            for p in plans:
                c.execute("INSERT OR IGNORE INTO packets(packet_id,film_sha256,pass_id,cluster_id,start_frame,end_frame,state,"
                          "idempotency_key,manifest_sha,updated_at,body) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                          (p.packet_id, p.film_sha256, p.pass_id, p.cluster_id, p.target_indices[0], p.target_indices[-1],
                           "PLANNED", p.idempotency_key, p.frame_manifest_sha, now_iso(), canonical_json(p.to_dict())))

    def packet_dir(self, p: PacketPlan) -> Path:
        return self.vdir / p.pass_id / p.packet_id

    def prior_boundary(self, p: PacketPlan) -> dict | None:
        row = self.store.conn.execute(
            "SELECT packet_id FROM packets WHERE film_sha256=? AND pass_id=? AND end_frame=? AND state='SEMANTIC_COMMITTED'",
            (p.film_sha256, p.pass_id, p.target_indices[0] - 1)).fetchone()
        if not row:
            return None
        bp = self.vdir / p.pass_id / row[0] / "boundary.json"
        return read_json(bp) if bp.exists() else None

    # ---- the transaction sequence ---------------------------------------------------
    def _inputs(self, p: PacketPlan) -> tuple[list[dict], list[dict], list[bytes]]:
        tgt: list[dict] = []
        ctx: list[dict] = []
        imgs_t: list[bytes] = []
        imgs_c: list[bytes] = []
        for k in p.context_before + p.target_indices + p.context_after:
            rec = self.index[k]
            fr = self.load(rec)
            if fr["raw_sha"] != rec["frame_content_sha256"]:
                raise Blocked("INPUT_FRAME_IDENTITY_MISMATCH", f"frame {k}")
            item = {"frame_id": frame_id_for(p.film_sha256, k), "source_sha": p.film_sha256[:16],
                    "presentation_index": k, "pts": rec["pts"], "pts_time": rec["pts_time"], "image_sha": fr["png_sha"],
                    "width": fr["w"], "height": fr["h"], "scale_factor": fr.get("scale", 1.0),
                    "is_target": k in p.target_indices, "raw_identity_sha": rec["frame_content_sha256"]}
            (tgt if item["is_target"] else ctx).append(item)
            (imgs_t if item["is_target"] else imgs_c).append(fr["png"])
        return tgt, ctx, imgs_t + imgs_c

    def run(self, p: PacketPlan) -> str:
        row = self._row(p.packet_id)
        if row is None:
            self.register([p])
            row = self._row(p.packet_id)
        state = row[0]
        if state == "SEMANTIC_COMMITTED":
            return state
        if state in ("BLOCKED_CONSENT", "UNKNOWN_BILLING"):
            return state
        d = self.packet_dir(p)
        tgt, ctx, imgs = self._inputs(p)
        man_sha = digest({"targets": tgt, "context": ctx})
        prior = self.prior_boundary(p)
        req = build_vision_request(p.packet_id, tgt, ctx, self.questions, prior)
        req["film_sha256"] = p.film_sha256
        if state in ("PLANNED", "RETRY_WAIT", "NEEDS_REINSPECTION", "INPUTS_READY", "QUARANTINED"):
            atomic_write_json(d / "input.json", {"plan": p.to_dict(), "targets": tgt, "context": ctx, "request": req,
                                                 "input_manifest_sha": man_sha})
            with self.store.tx() as c:
                self._set(p.packet_id, "INPUTS_READY", c)
            maybe_crash("after_inputs_ready")
            state = "INPUTS_READY"
        response = None
        if state == "INPUTS_READY":
            task_id = f"{p.idempotency_key}-{uuid.uuid5(uuid.NAMESPACE_URL, p.packet_id)}"
            with self.store.tx() as c:  # persist task id BEFORE submitting (no blind re-bill)
                self._set(p.packet_id, "REQUEST_IN_FLIGHT", c, provider_task_id=task_id)
            maybe_crash("after_inflight_commit")
            try:
                response = self.provider.submit(task_id, req, imgs)
            except Blocked as b:
                if b.code == "PROVIDER_PENDING":       # submitted; result not ready yet → stays in flight, reconciled later
                    return "REQUEST_IN_FLIGHT"
                if b.code in ("PROVIDER_REFUSAL", "PROVIDER_EXECUTION"):
                    with self.store.tx() as c:
                        self._set(p.packet_id, "NEEDS_REINSPECTION", c, error=b.code)
                    return "NEEDS_REINSPECTION"
                with self.store.tx() as c:
                    st = "BLOCKED_CONSENT" if b.code in ("NO_PROVIDER_AUTHORIZATION", "NO_SOURCE_UPLOAD_CONSENT",
                                                          "NETWORK_DISABLED", "SOURCE_NOT_IN_CONSENT_SCOPE",
                                                          "COST_UNKNOWN_STOP", "SPEND_CAP_EXCEEDED") else "RETRY_WAIT"
                    self._set(p.packet_id, st, c, error=b.code)
                return st
            maybe_crash("after_submit_before_save")
            state = "REQUEST_IN_FLIGHT"
        if state == "REQUEST_IN_FLIGHT" and response is None:
            task_id = self._row(p.packet_id)[1]
            try:
                q = self.provider.query(task_id)
            except Blocked as b:
                with self.store.tx() as c:
                    self._set(p.packet_id, "NEEDS_REINSPECTION", c, error=b.code)
                return "NEEDS_REINSPECTION"
            if q is not None and q.get("status") == "PENDING":
                return "REQUEST_IN_FLIGHT"
            if q is None:
                with self.store.tx() as c:
                    self._set(p.packet_id, "UNKNOWN_BILLING", c, error="CANNOT_QUERY_PENDING_TASK")
                return "UNKNOWN_BILLING"
            if q.get("status") == "COMPLETED":
                response = q["response"]
            elif q.get("status") == "NOT_FOUND":
                # never reached the provider: safe to submit with the SAME idempotency task id
                response = self.provider.submit(task_id, req, imgs)
            else:
                with self.store.tx() as c:
                    self._set(p.packet_id, "UNKNOWN_BILLING", c, error=f"PENDING_STATUS_{q.get('status')}")
                return "UNKNOWN_BILLING"
        if response is not None:
            raw = response if isinstance(response, str) else canonical_json(response)
            rsha = atomic_write_bytes(d / "response.json", raw.encode("utf-8"))
            with self.store.tx() as c:
                self._set(p.packet_id, "RESULT_RECEIVED", c, response_path=str(d / "response.json"), response_sha=rsha)
            maybe_crash("after_raw_response")
            state = "RESULT_RECEIVED"
        if state == "RESULT_RECEIVED":
            rp = Path(self._row(p.packet_id)[2])
            if sha256_file(rp) != self._row(p.packet_id)[3]:
                with self.store.tx() as c:
                    self._set(p.packet_id, "QUARANTINED", c, error="RAW_RESPONSE_HASH_MISMATCH")
                return "QUARANTINED"
            try:
                parsed = read_json(rp)
                if isinstance(parsed, str):
                    import json as _j
                    parsed = _j.loads(parsed)
            except Exception:
                with self.store.tx() as c:
                    self._set(p.packet_id, "NEEDS_REINSPECTION", c, error="CORRUPT_JSON_RESPONSE")
                return "NEEDS_REINSPECTION"
            v = validate_packet_response(parsed, tgt, prior, images_actually_sent=len(imgs))
            if not v["ok"]:
                with self.store.tx() as c:
                    self._set(p.packet_id, v["status"], c, error=";".join(v["problems"])[:1000])
                atomic_write_json(d / "validation.json", v)
                return v["status"]
            return self._commit(p, d, v, tgt, rp)
        return state

    def _commit(self, p: PacketPlan, d: Path, v: dict, tgt: list[dict], rp: Path) -> str:
        lines = []
        for o in v["observations"]:
            o = dict(o)
            o["raw_response_path"] = str(rp)
            lines.append(canonical_json(o))
        frames_sha = atomic_write_bytes(d / "frames.jsonl", ("\n".join(lines) + "\n").encode("utf-8"))
        boundary = dict(v["boundary"])
        boundary["last_frame_index"] = p.target_indices[-1]
        bsha = atomic_write_json(d / "boundary.json", boundary)
        nxt = p.target_indices[-1] + 1
        checkpoint = {
            "packet_id": p.packet_id, "film_sha256": p.film_sha256, "analysis_pass_id": p.pass_id,
            "question_cluster_id": p.cluster_id, "start_frame": p.target_indices[0], "end_frame": p.target_indices[-1],
            "model_version": p.model_version, "status": "SEMANTIC_COMMITTED",
            "source_frame_manifest_sha": p.frame_manifest_sha, "boundary_state_path": str(d / "boundary.json"),
            "boundary_sha": bsha, "per_frame_semantic_manifest_sha": frames_sha,
            "unresolved_questions": boundary.get("open_questions", []), "weak_frames": v.get("weak", []),
            "transition_graph": v["transition_graph"], "question_update": v.get("question_update"),
            "next_frame_index": nxt, "exact_next_action": f"run packet starting at frame {nxt} (pass {p.pass_id})",
            "provider_kind": self.provider.kind,
        }
        atomic_write_json(d / "checkpoint.json", checkpoint)
        with self.store.tx() as c:
            for o, m in zip(sorted(v["observations"], key=lambda x: int(x["frame_id"].split(":")[1])), tgt):
                tk = getattr(self.provider, "transport_kind", "NETWORK")
                status = ("VISION_OUTPUT_VERIFIED" if self.provider.kind == "REAL" and tk == "NETWORK" else
                          "SIMULATED_TRANSPORT_FIXTURE" if self.provider.kind == "REAL" else "MOCK_VERIFIED_SYNTHETIC")
                c.execute("INSERT OR REPLACE INTO frame_vision(film_sha256,frame_index,pass_id,status,packet_id,image_sha,"
                          "observation_sha,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                          (p.film_sha256, m["presentation_index"], p.pass_id, status, p.packet_id, m["image_sha"],
                           digest(o), now_iso()))
            maybe_crash("mid_semantic_commit")
            self.store.put("SemanticPacketCheckpoint", p.packet_id, checkpoint, conn=c)
            self._set(p.packet_id, "SEMANTIC_COMMITTED", c, semantic_manifest_sha=frames_sha)
        maybe_crash("after_semantic_commit")
        return "SEMANTIC_COMMITTED"

    # ---- resume ---------------------------------------------------------------------
    def verify_committed(self) -> list[str]:
        """Re-hash committed packet artefacts; quarantine any that no longer match (append-only)."""
        bad = []
        rows = self.store.conn.execute("SELECT packet_id, pass_id, semantic_manifest_sha FROM packets WHERE state='SEMANTIC_COMMITTED'").fetchall()
        for pid, pas, fsha in rows:
            f = self.vdir / pas / pid / "frames.jsonl"
            if not f.exists() or sha256_file(f) != fsha:
                bad.append(pid)
                with self.store.tx() as c:
                    self._set(pid, "QUARANTINED", c, error="COMMITTED_ARTIFACT_HASH_MISMATCH")
                    c.execute("DELETE FROM frame_vision WHERE packet_id=?", (pid,))
        return bad

    def resume(self, plans: list[PacketPlan]) -> dict:
        bad = self.verify_committed()
        results = {}
        for p in plans:
            results[p.packet_id] = self.run(p)
            if results[p.packet_id] in ("UNKNOWN_BILLING", "BLOCKED_CONSENT"):
                break  # stop for human reconciliation / consent
        return {"quarantined_on_verify": bad, "results": results}


def coverage_for_range(store: Store, film_sha: str, pass_id: str, start: int, end_inclusive: int) -> dict:
    rows = store.conn.execute("SELECT frame_index, status FROM frame_vision WHERE film_sha256=? AND pass_id=? AND "
                              "frame_index BETWEEN ? AND ?", (film_sha, pass_id, start, end_inclusive)).fetchall()
    seen = {i: s for i, s in rows}
    expected = list(range(start, end_inclusive + 1))
    missing = [i for i in expected if i not in seen]
    from ..reference.frame_index import ranges
    return {"expected": len(expected), "verified": len(seen), "missing_count": len(missing),
            "missing_ranges": ranges(missing), "statuses": sorted(set(seen.values())),
            "complete": not missing, "real_vlm": all(s == "VISION_OUTPUT_VERIFIED" for s in seen.values()) and bool(seen)}
