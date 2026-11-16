"""Multi-root failure diagnosis with discriminating evidence (01 §12, 09 C8, 14 §7, ADD25 §4.4, A14/A46, B31, C31).

Each symptom is classified independently from the evidence fields it carries; multiple
causes per run are kept as separate trails and routed to the earliest responsible stage.
"""
from __future__ import annotations

from ..util import new_id, now_iso

FAILURE_CLASSES = ("SOURCE_ACCESS", "OBSERVATION_GAP", "HYPOTHESIS_ERROR", "STYLE_DECISION_GAP", "SKILL_RECIPE_GAP",
                   "PROMPT_COMPILER_GAP", "PROVIDER_LIMIT", "PROVIDER_EXECUTION", "MODEL_CAPABILITY_GAP", "ASSET_PREP",
                   "ASSET_CONSTRUCTION_GAP", "RENDER_ENGINE", "MOTION_LOGIC", "ANIMATION_GAP", "INTEGRATION",
                   "EVALUATION_ERROR", "GENERALIZATION_FAIL")
STAGE_OF = {"SOURCE_ACCESS": "SOURCE_OBSERVATION", "OBSERVATION_GAP": "SOURCE_OBSERVATION", "HYPOTHESIS_ERROR": "CAUSE_INFERENCE",
            "STYLE_DECISION_GAP": "STYLE_CONDITIONS", "SKILL_RECIPE_GAP": "OPERATION_DESIGN", "PROMPT_COMPILER_GAP": "PROMPT_COMPILATION",
            "PROVIDER_LIMIT": "PROVIDER_RESULT", "MODEL_CAPABILITY_GAP": "PROVIDER_RESULT", "PROVIDER_EXECUTION": "PROVIDER_RESULT",
            "ASSET_PREP": "ASSET_FAMILY", "ASSET_CONSTRUCTION_GAP": "ASSET_FAMILY", "RENDER_ENGINE": "RENDER", "MOTION_LOGIC": "RENDER",
            "ANIMATION_GAP": "RENDER", "INTEGRATION": "RENDER", "EVALUATION_ERROR": "HUMAN_REVIEW", "GENERALIZATION_FAIL": "STYLE_CONDITIONS"}


def classify(symptom: dict) -> dict:
    """Discriminating rules over concrete evidence. Never defaults everything to 'more frame analysis'."""
    ev = symptom.get("evidence", {})
    cls, test = None, None
    if ev.get("source_hash_mismatch") or ev.get("source_missing"):
        cls, test = "SOURCE_ACCESS", "re-hash source and rebind"
    elif ev.get("relation_never_inspected") or ev.get("only_thumbnail_seen"):
        cls, test = "OBSERVATION_GAP", "inspect native crop + neighbours of the cited frames"
    elif ev.get("compiled_payload_missing_clause"):
        cls, test = "PROMPT_COMPILER_GAP", "diff skill clause set vs payload segments"
    elif ev.get("decision_absent_for_conditions"):
        cls, test = "STYLE_DECISION_GAP", "compile with conditions; expect MISSING_STYLE_DECISION"
    elif ev.get("no_operation_for_decision"):
        cls, test = "SKILL_RECIPE_GAP", "operator registry lookup for decision operations"
    elif ev.get("http_error") or ev.get("invalid_image_bytes"):
        cls, test = "PROVIDER_EXECUTION", "replay raw response; decode bytes"
    elif ev.get("request_correct") and ev.get("output_ignores_reference"):
        cls, test = "MODEL_CAPABILITY_GAP", "same request with stronger reference/edit route or provider"
    elif ev.get("mask_mismatch") or ev.get("recompose_holes") or ev.get("opaque_claimed_transparent"):
        cls, test = "ASSET_CONSTRUCTION_GAP", "recompose layers against approved canonical"
    elif ev.get("renderer_crash") or ev.get("ffprobe_mismatch"):
        cls, test = "RENDER_ENGINE", "ffprobe + rerender with same scene graph"
    elif ev.get("pan_only") or ev.get("contact_drift") or ev.get("prop_floats"):
        cls, test = "MOTION_LOGIC", "motion evidence residual + contact anchor trace"
    elif ev.get("hypothesis_prediction_failed"):
        cls, test = "HYPOTHESIS_ERROR", "compare predicted visible change with actual output"
    elif ev.get("reviewer_saw_metadata_only"):
        cls, test = "EVALUATION_ERROR", "re-review actual frames"
    elif ev.get("holdout_worse"):
        cls, test = "GENERALIZATION_FAIL", "frozen skill on second unlike subject"
    if cls is None:
        return {"finding_id": new_id("diag"), "symptom": symptom["symptom"], "failure_classes": ["UNCLASSIFIED_NEEDS_EVIDENCE"],
                "discriminating_test": "collect evidence fields; do not guess", "correction_scope": None}
    return {"finding_id": new_id("diag"), "symptom": symptom["symptom"], "failure_classes": [cls], "discriminating_test": test,
            "evidence_paths": symptom.get("evidence_paths", []), "correction_scope": STAGE_OF[cls], "severity": symptom.get("severity", "HIGH"),
            "at": now_iso()}


def diagnose_run(symptoms: list[dict]) -> dict:
    findings = [classify(s) for s in symptoms]
    classes = sorted({c for f in findings for c in f["failure_classes"]})
    from ..investigation.controller import HANDOFF_ORDER
    scopes = [f["correction_scope"] for f in findings if f["correction_scope"]]
    earliest = sorted(scopes, key=HANDOFF_ORDER.index)[0] if scopes else None
    return {"findings": findings, "distinct_failure_classes": classes, "separate_trails": len(findings),
            "fix_first_stage": earliest, "everything_blamed_on_reference_analysis": classes == ["OBSERVATION_GAP"] and len(findings) > 1}
