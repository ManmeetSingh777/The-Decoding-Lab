"""Portable cross-environment handoff (Addendum 24 D3/D4, ADD25-R01/R02, ADD26-R01, ADD27 §7).

export: coherent SQLite snapshot (backup API, never a naked WAL copy) + hash-verified file
manifest; excludes source MP4s, secrets and caches. import: verifies every hash, rebinds
original films by SHA256 (STOP if bytes differ) and reports MISSING_ARTIFACT honestly.
"""
from __future__ import annotations

import os
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from ..util import Blocked, atomic_write_json, digest, now_iso, read_json, sha256_file
from .workspace import Workspace

INCLUDE_DIRS = ("state", "skills", "artifacts", "vision", "investigation", "frames", "reports", "logs", "runs", "config", "providers")
EXCLUDE_SUFFIX = (".mp4", ".mov", ".mkv", ".m4v", ".tmp", ".sqlite-wal", ".sqlite-shm", ".pyc")
EXCLUDE_NAMES = (".env", "issuer.key")
SECRET_PATTERNS = (re.compile(rb"RUNWARE_API_KEY\s*=\s*\S{8,}"), re.compile(rb"Bearer\s+[A-Za-z0-9_\-]{16,}"),
                   re.compile(rb"sk-[A-Za-z0-9]{20,}"))
MAX_FILE_BYTES = 200 * 1024 * 1024


def _secret_free(p: Path) -> bool:
    if p.stat().st_size > 20 * 1024 * 1024:
        return True
    b = p.read_bytes()
    return not any(r.search(b) for r in SECRET_PATTERNS)


def export_handoff(ws: Workspace, out_zip: str | Path, *, reason: str = "switch-coding-agent") -> dict:
    out_zip = Path(out_zip)
    manifest, omitted = [], []
    with tempfile.TemporaryDirectory() as td:
        snap = Path(td) / "vme.sqlite"
        st = ws.store()
        try:
            st.event("CHECKPOINT", None, {"reason": reason})
            snap_sha = st.snapshot_to(snap)
        finally:
            st.close()
        tmp_zip = out_zip.with_suffix(".tmp.zip")
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(snap, "store/vme.sqlite")
            manifest.append({"path": "store/vme.sqlite", "sha256": snap_sha, "bytes": snap.stat().st_size})
            for d in INCLUDE_DIRS:
                base = ws.root / d
                if not base.exists():
                    continue
                for p in sorted(base.rglob("*")):
                    if not p.is_file():
                        continue
                    rel = p.relative_to(ws.root).as_posix()
                    if p.suffix.lower() in EXCLUDE_SUFFIX or p.name in EXCLUDE_NAMES:
                        omitted.append({"path": rel, "reason": "EXCLUDED_BY_POLICY"})
                        continue
                    if p.stat().st_size > MAX_FILE_BYTES:
                        omitted.append({"path": rel, "sha256": sha256_file(p), "reason": "MISSING_ARTIFACT_SIZE", "required_path": rel})
                        continue
                    if not _secret_free(p):
                        omitted.append({"path": rel, "reason": "SECRET_PATTERN_DETECTED"})
                        continue
                    z.write(p, rel)
                    manifest.append({"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size})
            lock = read_json(ws.state_dir / "SOURCE_LOCK.json") if (ws.state_dir / "SOURCE_LOCK.json").exists() else {"sources": []}
            hand = {"schema": "vme.handoff/1", "exported_at": now_iso(), "reason": reason, "files": manifest, "omitted": omitted,
                    "source_films_required": [{"file_name": s["file_name"], "sha256": s["sha256"], "role": s.get("role")}
                                              for s in lock.get("sources", [])],
                    "note": "Original MP4s are NOT included; place them in a folder and import with --sources to rebind by SHA256."}
            hand["manifest_sha"] = digest(manifest)
            z.writestr("HANDOFF_MANIFEST.json", __import__("json").dumps(hand, indent=2, sort_keys=True))
        os.replace(tmp_zip, out_zip)
    return {"zip": str(out_zip), "sha256": sha256_file(out_zip), "files": len(manifest), "omitted": omitted,
            "manifest_sha": hand["manifest_sha"]}


def import_handoff(zip_path: str | Path, new_root: str | Path, *, sources_folder: str | Path | None = None) -> dict:
    new_root = Path(new_root)
    if new_root.exists() and any(new_root.iterdir()):
        raise Blocked("IMPORT_TARGET_NOT_EMPTY", str(new_root))
    new_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        hand = __import__("json").loads(z.read("HANDOFF_MANIFEST.json"))
        for n in z.namelist():
            if n.startswith("/") or ".." in Path(n).parts:
                raise Blocked("UNSAFE_ZIP_PATH", n)
        z.extractall(new_root)
    bad, missing = [], []
    for f in hand["files"]:
        p = new_root / f["path"]
        if not p.exists():
            missing.append(f["path"])
        elif sha256_file(p) != f["sha256"]:
            bad.append(f["path"])
    for o in hand["omitted"]:
        if o.get("reason") == "MISSING_ARTIFACT_SIZE":
            missing.append(o["path"])
    con = sqlite3.connect(str(new_root / "store" / "vme.sqlite"))
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    rebound: list[dict] = []
    unbound: list[dict] = []
    if sources_folder:
        from ..reference.probe import discover_sources
        have = {sha256_file(p): p for p in discover_sources(sources_folder)}
        for s in hand["source_films_required"]:
            (rebound if s["sha256"] in have else unbound).append({**s, "path": str(have.get(s["sha256"], ""))})
    else:
        unbound = hand["source_films_required"]
    status = "COMPLETE" if not bad and not missing and integrity == "ok" and not unbound else (
        "CORRUPT" if bad or integrity != "ok" else "INCOMPLETE")
    rep = {"status": status, "hash_mismatches": bad, "missing_artifacts": missing, "sqlite_integrity": integrity,
           "sources_rebound": rebound, "sources_unbound": unbound, "imported_at": now_iso(), "from_zip": str(zip_path)}
    Workspace(new_root).ensure()
    atomic_write_json(new_root / "state" / "IMPORT_REPORT.json", rep)
    if bad or integrity != "ok":
        raise Blocked("HANDOFF_CORRUPT", f"{len(bad)} hash mismatches; integrity={integrity}", report=rep)
    return rep


def exact_next_operation(ws: Workspace) -> dict:
    """Recompute the single next operation from DB state (not from chat): pending jobs first, then packets, then problems."""
    st = ws.store()
    try:
        pend = st.conn.execute("SELECT job_key, state, task_uuid FROM jobs WHERE state IN "
                               "('INTENT_PERSISTED','IN_FLIGHT','RESPONSE_SAVED','UNKNOWN_BILLING')").fetchall()
        vdir = ws.root / "providers" / "anthropic"
        for tp in sorted(vdir.glob("task_*.json")) if vdir.exists() else []:
            j = read_json(tp)
            if j.get("state") in ("SUBMISSION_ATTEMPTED", "SUBMISSION_UNCERTAIN"):
                return {"kind": "RECONCILE_VISION_SUBMISSION", "custom_id": j["task_id"], "state": j["state"],
                        "command": "human: check the Anthropic console for this custom_id, then reconcile_uncertain(... batch_id=... | "
                                   "not_submitted_evidence=...); never resubmit blindly"}
        if pend:
            k, s, t = pend[0]
            return {"kind": "RECONCILE_PROVIDER_JOB", "job_key": k, "state": s, "task_uuid": t,
                    "command": f"vme resume --verify   # reconcile task {t} before any retry"}
        pk = st.conn.execute("SELECT packet_id, pass_id, start_frame, state FROM packets WHERE state!='SEMANTIC_COMMITTED' "
                             "ORDER BY film_sha256, pass_id, start_frame LIMIT 1").fetchone()
        if pk:
            return {"kind": "RUN_VISION_PACKET", "packet_id": pk[0], "pass_id": pk[1], "start_frame": pk[2], "state": pk[3],
                    "command": f"vme vision resume --pass {pk[1]}"}
        probs = st.list("ActiveArtProblem")
        if probs:
            p = probs[-1]
            return {"kind": "ACTIVE_ART_PROBLEM", "cluster_id": p["cluster_id"], "owner_stage": p["owner_stage"],
                    "next_action": p["next_action_and_exact_input"], "command": f"vme investigate questions --cluster {p['cluster_id']}"}
        gates = st.list("VisualGateState")
        for g in gates:
            if g["state"].startswith("AWAITING"):
                return {"kind": "AWAIT_HUMAN_REVIEW", "run_id": g["run_id"], "state": g["state"],
                        "command": f"vme review serve --run {g['run_id']}"}
        pending = []
        lock_p = ws.state_dir / "SOURCE_LOCK.json"
        if lock_p.exists():
            lock = read_json(lock_p)
            unconfirmed = [s["file_name"] for s in lock.get("sources", []) if str(s.get("basis", "")).startswith("PROPOSED")]
            if unconfirmed:
                pending.append(f"confirm source roles by SHA256 in config/source_roles.json (proposed: {unconfirmed})")
        six_p = ws.state_dir / "SIXTH_LOCATOR_STATUS.json"
        if six_p.exists() and read_json(six_p).get("status") != "LOCKED":
            pending.append("lock the sixth volcano→logo interval from the local witness packet (vme selection sixth-lock ...)")
        stopped = [t for t in st.list("LoopTransition") if t["status"] == "STOPPED"]
        for t in stopped:
            pending.append(f"loop {t['run_id']} stopped at {t['stage']}: {t.get('stop_reason')}")
        if pending:
            return {"kind": "AWAIT_HUMAN_DECISIONS", "pending": pending,
                    "command": "vme status --detailed   # then the user decides; no paid work without vme authorize"}
        return {"kind": "NONE_PENDING", "command": "vme status --detailed"}
    finally:
        st.close()
