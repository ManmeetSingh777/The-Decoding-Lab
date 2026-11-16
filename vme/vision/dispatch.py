"""R3 F06/F09 — the ONE constructor for every external source-analysis request (P1–P6).

`prepare_verified_request` builds the system text from the live versioned protocol (`pass_instructions(pass_id)`: P0 + Pn) plus a
pass-specific output shape, the typed P0 binding, and an image manifest whose byte digests are computed HERE from the exact bytes that
will be sent (never from a model echo). The returned `request_sha` covers system text, user text, every image byte digest, provider
profile, parser contract and preprocessing, so changing any of them — even with an unchanged version label — yields a different
request identity and invalidates dependent caches.

The manifest's `submitted_witness_ids` is the ONLY authority for which witnesses an answer may cite (consumed by
`style.authoring.author_decision`). A provider response that echoes ids or hashes is identity binding, not artistic understanding:
evidence statuses progress LOCAL_BYTES_VERIFIED → SUBMITTED → RESPONSE_RECEIVED → IDENTITY_BOUND → ARTISTIC_CLAIM_UNVERIFIED and only
a human/native review (vme.state.authority) can add SOURCE_ARTISTICALLY_REVIEWED.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..util import Blocked, canonical_json, digest, sha256_bytes, read_json
from .protocol import PROTOCOL_SHA, PROTOCOL_VERSION, bind, pass_instructions

PASS_FOR_KIND = {"frame_packet": "P1", "window_rationale": "P2", "character_dossier": "P2", "question_answer": "P4",
                 "native_detail": "P5", "reinspection": "P5", "adversarial_sweep": "P5", "cold_start": "P6"}
IMAGE_ROLES = ("TARGET", "CONTEXT", "NATIVE_CROP", "NEIGHBOUR", "CONTRAST", "WITNESS")
EVIDENCE_STATUSES = ("LOCAL_BYTES_VERIFIED", "SUBMITTED", "RESPONSE_RECEIVED", "IDENTITY_BOUND", "ARTISTIC_CLAIM_UNVERIFIED",
                     "SOURCE_ARTISTICALLY_REVIEWED")
PARSER_CONTRACT_SHA = digest((Path(__file__).with_name("contracts.py")).read_text(encoding="utf-8"))


def image_entry(*, role: str, png: bytes, witness_id: str, source_sha256: str, frame_index: int, pts, width: int, height: int,
                raw_frame_sha256: str | None = None, region: dict | None = None, label: str | None = None) -> dict:
    """One image as it WILL be sent. The byte digest is computed from the bytes themselves."""
    if role not in IMAGE_ROLES:
        raise Blocked("BAD_IMAGE_ROLE", role)
    if pts is None or frame_index is None:
        raise Blocked("WITNESS_WITHOUT_TEMPORAL_ID", witness_id)
    if not source_sha256 or len(source_sha256) < 16:
        raise Blocked("IMAGE_WITHOUT_SOURCE_IDENTITY", witness_id)
    return {"role": role, "witness_id": witness_id, "source_sha256": source_sha256, "frame_index": int(frame_index), "pts": pts,
            "region": region, "width": int(width), "height": int(height), "raw_frame_sha256": raw_frame_sha256,
            "image_bytes_sha256": sha256_bytes(png), "kind": "NATIVE_CROP" if region else "FULL_FRAME",
            "label": label or f"{role} {witness_id} frame={source_sha256[:16]}:{frame_index} pts={pts}", "_bytes": png}


def prepare_verified_request(*, pass_id: str, kind: str, shape: str, source_shas: list[str], selection: dict, images: list[dict],
                             prior_boundary: dict | None, active_cluster: dict | None, controlling_problem: dict | None,
                             competing_explanations: list | None, required_response: dict, provider_profile: dict,
                             payload: dict, preprocess_contract: dict | None = None) -> dict:
    if PASS_FOR_KIND.get(kind) != pass_id:
        raise Blocked("PROTOCOL_PASS_MISMATCH", f"{kind} must use {PASS_FOR_KIND.get(kind)}, not {pass_id}")
    if not images:
        raise Blocked("NO_SOURCE_IMAGES_FOR_SOURCE_REQUEST", kind)
    seen = set()
    for im in images:
        if sha256_bytes(im["_bytes"]) != im["image_bytes_sha256"]:
            raise Blocked("LOCAL_IMAGE_BYTES_CHANGED", im["witness_id"])
        if im["source_sha256"] not in source_shas:
            raise Blocked("IMAGE_SOURCE_NOT_IN_REQUEST_SCOPE", im["witness_id"])
        key = (im["witness_id"], im["image_bytes_sha256"])
        if key in seen:
            raise Blocked("DUPLICATE_IMAGE_IN_REQUEST", im["witness_id"])
        seen.add(key)
    system = pass_instructions(pass_id) + "\n\nPASS-SPECIFIC OUTPUT SHAPE:\n" + shape
    manifest = [{k: v for k, v in im.items() if k != "_bytes"} for im in images]
    binding = bind(protocol={"version": PROTOCOL_VERSION, "sha": PROTOCOL_SHA, "pass_id": pass_id},
                   source={"sha256s": sorted(set(source_shas))}, sequence=selection,
                   target_images=[{k: m[k] for k in ("witness_id", "role", "frame_index", "pts", "image_bytes_sha256", "region")}
                                  for m in manifest],
                   prior_boundary=prior_boundary or {}, active_cluster=active_cluster or {}, controlling_problem=controlling_problem or {},
                   current_competing_explanations=competing_explanations or [], required_response=required_response)
    user_text = canonical_json({"binding": binding, **payload})
    request_sha = digest({"system_text": system, "user_text": user_text, "images": [m["image_bytes_sha256"] for m in manifest],
                          "provider": provider_profile, "parser_contract": PARSER_CONTRACT_SHA, "preprocess": preprocess_contract or {}})
    return {"pass_id": pass_id, "kind": kind, "system": system, "user_text": user_text, "binding": binding,
            "labelled_images": [(im["label"], im["_bytes"], im["width"], im["height"]) for im in images],
            "byte_manifest": manifest, "submitted_witness_ids": sorted({m["witness_id"] for m in manifest}),
            "source_shas": sorted(set(source_shas)), "request_sha": request_sha, "system_sha": digest(system),
            "user_text_sha": digest(user_text), "parser_contract_sha": PARSER_CONTRACT_SHA, "protocol_sha": PROTOCOL_SHA,
            "evidence_status": ["LOCAL_BYTES_VERIFIED"]}


def submit_source_request(vis, task_id: str, prepared: dict, *, auth_task: str = "source_vision") -> dict:
    """Submit through the adapter's durable journal; the journal keeps the exact manifest/system/user digests."""
    return vis.request_json(task_id, prepared["kind"], prepared["system"], prepared["user_text"], prepared["labelled_images"],
                            source_shas=prepared["source_shas"], auth_task=auth_task, manifest=prepared)


def submitted_manifest(vis, task_id: str) -> dict:
    """Read the LOCAL journal record of what was actually sent for task_id (never the model reply)."""
    p = vis.state / f"task_{task_id}.json"
    if not p.exists():
        raise Blocked("NO_SUBMISSION_JOURNAL", task_id)
    j = read_json(p)
    man = j.get("manifest")
    if not man or not man.get("submitted_witness_ids"):
        raise Blocked("NO_SUBMISSION_MANIFEST", task_id)
    return man


def capture_index(vis) -> list[dict]:
    """Sanitized outbound request capture (system/user digests, byte manifest) for REAL_REQUEST_CAPTURE_INDEX.json."""
    out = []
    for p in sorted(vis.state.glob("task_*.json")):
        j = read_json(p)
        m = j.get("manifest") or {}
        out.append({"custom_id": j["task_id"], "kind": j.get("kind"), "state": j.get("state"), "pass_id": m.get("pass_id"),
                    "protocol_sha": m.get("protocol_sha"), "system_sha": m.get("system_sha"), "user_text_sha": m.get("user_text_sha"),
                    "request_sha": m.get("request_sha"), "parser_contract_sha": m.get("parser_contract_sha"),
                    "byte_manifest": m.get("byte_manifest"), "evidence_status": j.get("evidence_status"),
                    "raw_sha256": j.get("raw_sha256"), "batch_id": j.get("batch_id")})
    return out


def system_text_from_journal(vis, task_id: str) -> str | None:
    j = read_json(vis.state / f"task_{task_id}.json")
    return (j.get("manifest") or {}).get("system")


def dumps_manifest(prepared: dict) -> str:
    return json.dumps({k: v for k, v in prepared.items() if k not in ("labelled_images",)}, sort_keys=True, default=str)
