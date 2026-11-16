"""R3-C10 — a skill branch that is OWNED is not yet IMPLEMENTED in pixels. Promotion order per high-impact branch:

  OWNED_UNVERIFIED            the production ledger names an owner (compiled request/track exists)
  VISUAL_EFFECT_EXHIBITED     the real returned output and its ABLATION (branch removed/altered, everything else identical) differ INSIDE the
                              branch's declared region/part and stay stable OUTSIDE it (unrelated regions/actors unchanged)
  HUMAN_VISUALLY_APPROVED     a named human compared the output with the source construction decision (authority VISUAL_QUALIFICATION)

A model self-attestation never advances a step. Synthetic/simulated provider output can exhibit wiring but is labelled so and can never
be HUMAN_VISUALLY_APPROVED for transfer (evidence_origin must be REAL_VLM and the image a REAL provider output).
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

from ..util import Blocked, digest, now_iso

STATUSES = ("OWNED_UNVERIFIED", "VISUAL_EFFECT_EXHIBITED", "NO_VISIBLE_EFFECT", "EFFECT_LEAKS_OUTSIDE_REGION", "HUMAN_VISUALLY_APPROVED",
            "HUMAN_VISUALLY_REJECTED")


def _arr(png: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.float32)


def region_effect(with_branch: bytes, ablated: bytes, region: dict, *, min_inside: float = 4.0, max_outside_ratio: float = 0.35) -> dict:
    a, b = _arr(with_branch), _arr(ablated)
    if a.shape != b.shape:
        raise Blocked("ABLATION_SHAPE_MISMATCH", f"{a.shape} vs {b.shape}")
    d = np.abs(a - b).mean(axis=2)
    x, y, w, h = (int(region[k]) for k in ("x", "y", "w", "h"))
    m = np.zeros_like(d, dtype=bool)
    m[y:y + h, x:x + w] = True
    inside = float(d[m].mean()) if m.any() else 0.0
    outside = float(d[~m].mean()) if (~m).any() else 0.0
    status = ("NO_VISIBLE_EFFECT" if inside < min_inside else
              "EFFECT_LEAKS_OUTSIDE_REGION" if outside > max_outside_ratio * inside else "VISUAL_EFFECT_EXHIBITED")
    return {"inside_mean_abs_diff": round(inside, 3), "outside_mean_abs_diff": round(outside, 3), "status": status}


def qualify_branch_output(store, *, decision_id: str, branch_when: dict, region: dict, output_png: bytes, ablated_png: bytes,
                          output_label: str, evidence_origin: str, expected_change: str) -> dict:
    """Measure the branch's visible effect on the REAL returned images; record it. Never approves anything by itself."""
    if not expected_change or len(expected_change.split()) < 4:
        raise Blocked("EXPECTED_VISIBLE_CHANGE_NOT_PREDICTED", "state, before looking, what the branch should visibly change and where")
    eff = region_effect(output_png, ablated_png, region)
    qid = "VQ-" + digest([decision_id, branch_when, digest(output_png.hex()), digest(ablated_png.hex())])[:16]
    rec = {"qualification_id": qid, "decision_id": decision_id, "branch_when": branch_when, "region": region, "expected_change": expected_change,
           **eff, "output_label": output_label, "evidence_origin": evidence_origin,
           "transfer_eligible": output_label == "REAL_PROVIDER_OUTPUT" and evidence_origin == "REAL_VLM", "at": now_iso()}
    store.put("VisualQualification", qid, rec)
    return rec


def human_visual_verdict(store, qualification_id: str, *, verdict: str, by: str, statement: str) -> dict:
    from ..state.authority import AuthorityRegistry
    q = store.get("VisualQualification", qualification_id)
    if q is None:
        raise Blocked("UNKNOWN_QUALIFICATION", qualification_id)
    if verdict == "APPROVED" and q["status"] != "VISUAL_EFFECT_EXHIBITED":
        raise Blocked("NO_MEASURED_EFFECT_TO_APPROVE", f"{qualification_id} is {q['status']}")
    if verdict == "APPROVED" and not q["transfer_eligible"]:
        raise Blocked("SIMULATED_OUTPUT_CANNOT_QUALIFY", "only a REAL provider output from REAL_VLM evidence can be visually qualified")
    a = AuthorityRegistry(store).issue("VISUAL_QUALIFICATION", scope={"qualification_id": qualification_id}, verdict=verdict, by=by,
                                       statement=statement, evidence={"decision_id": q["decision_id"]})
    store.put("VisualQualification", qualification_id, {**q, "status": "HUMAN_VISUALLY_APPROVED" if verdict == "APPROVED" else
                                                         "HUMAN_VISUALLY_REJECTED", "authority_id": a["authority_id"]})
    return store.get("VisualQualification", qualification_id)
