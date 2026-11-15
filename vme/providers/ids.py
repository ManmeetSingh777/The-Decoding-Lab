"""Provider identifier contracts (R01, R04).

Anthropic Message Batches: `custom_id` must match ^[A-Za-z0-9_-]{1,64}$ (docs: messages/batches/create).
We derive it from a hash of a CANONICAL REQUEST DESCRIPTOR (source sha, sequence, pass, exact frame hashes,
question hash, provider/model, instruction hash, schema hash ...), so a restart never mints a new id for the
same logical request. A reused custom_id is NOT an across-batch idempotency guarantee; the durable intent
journal in `vision/claude_adapter.py` is what prevents blind resubmission.

Runware: `taskUUID` must be a UUID version 4. It is generated ONCE per logical job with `uuid.uuid4()`, persisted
with the exact request-body hash before any network call, and reused only to query/reconcile that task.
"""
from __future__ import annotations

import re
import uuid

from ..util import Blocked, digest

CUSTOM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
KIND_PREFIX = {"frame_packet": "fp", "window_rationale": "wr", "question_answer": "qa", "native_detail": "nd",
               "reinspection": "ri", "calibration": "cb"}


def validate_custom_id(cid: str) -> str:
    if not isinstance(cid, str) or not CUSTOM_ID_RE.fullmatch(cid):
        raise Blocked("INVALID_CUSTOM_ID", f"custom_id {cid!r} (len {len(cid) if isinstance(cid, str) else '?'}) "
                                           "must match ^[A-Za-z0-9_-]{1,64}$")
    return cid


def custom_id_for(kind: str, descriptor: dict) -> str:
    """Short stable id: 'vme_<kind2>_' + 40 hex of the canonical descriptor hash (47 chars)."""
    if kind not in KIND_PREFIX:
        raise Blocked("UNKNOWN_REQUEST_KIND", kind)
    return validate_custom_id(f"vme_{KIND_PREFIX[kind]}_{digest({'kind': kind, **descriptor})[:40]}")


def packet_descriptor(plan) -> dict:
    """Canonical descriptor of a frame packet: everything that defines the request, nothing process-specific."""
    return {"source_sha": plan.film_sha256, "pass": plan.pass_id, "cluster": plan.cluster_id,
            "targets": list(plan.target_indices), "context": list(plan.context_before) + list(plan.context_after),
            "frame_manifest_sha": plan.frame_manifest_sha, "model": plan.model_version, "prompt_version": plan.prompt_version,
            "transform": plan.transform_version}


def packet_custom_id(plan) -> str:
    return custom_id_for("frame_packet", packet_descriptor(plan))


def new_task_uuid4() -> str:
    return str(uuid.uuid4())


def validate_uuid4(s: str) -> str:
    try:
        u = uuid.UUID(str(s))
    except (ValueError, TypeError):
        raise Blocked("NON_V4_TASK_UUID", f"{s!r} is not a UUID")
    if u.version != 4 or str(u) != str(s).lower():
        raise Blocked("NON_V4_TASK_UUID", f"{s} has version {u.version}; Runware taskUUID must be UUIDv4")
    return str(u)
