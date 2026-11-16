"""Adapters from internal persisted records to the spec's typed contract envelopes (02 schema v1.2, 21 schema v1.3).

Used by schema-conformance tests and the audit export; structural typing only, never artistic evidence.
"""
from __future__ import annotations

from ..util import digest, sha256_bytes


def env02(record_type: str, record: dict) -> dict:
    return {"schema_version": "1.2", "record_type": record_type, "record": record}


def env21(contract_type: str, data: dict) -> dict:
    return {"contract_type": contract_type, "data": data}


# ---- 02 -------------------------------------------------------------------------------------
def frame_coverage_ledger(summary: dict, vision_status_totals: dict) -> dict:
    return env02("FrameCoverageLedger", {
        "film_sha256": summary["film_sha256"], "video_path": summary["video_path"], "frame_count_decoded": summary["frame_count_decoded"],
        "pts_index_path": summary["index_path"], "pts_index_sha256": summary["index_sha256"],
        "frame_status_manifest_path": "store/vme.sqlite#frame_vision", "status_totals": {"INDEXED_ONLY": summary["frame_count_decoded"], **vision_status_totals},
        "unaccounted_frame_ranges": [], "video_model_subsampling_checked": True, "complete_frame_index": summary["complete_frame_index"],
        "complete_vision_proof": False, "created_at": summary.get("indexed_at", "")})


def semantic_packet_checkpoint(ck: dict) -> dict:
    keys = ("packet_id", "film_sha256", "analysis_pass_id", "question_cluster_id", "start_frame", "end_frame", "model_version", "status",
            "source_frame_manifest_sha", "boundary_state_path", "per_frame_semantic_manifest_sha", "unresolved_questions",
            "next_frame_index", "exact_next_action")
    return env02("SemanticPacketCheckpoint", {k: ck[k] for k in keys})


def prompt_authority_trace(job_trace: dict, payload: dict, ref_shas: list) -> dict:
    segs = []
    for i, s in enumerate(job_trace["segments"]):
        auth = {"STYLE": "PINNED_STYLE_SKILL", "CONTENT": "ORIGINAL_BRIEF"}[s["authority"]]
        segs.append({"segment_id": f"seg{i}", "text_sha": sha256_bytes(s["text"].encode()), "authority": auth,
                     "source_id": s.get("clause_id") or s.get("brief_field_path"), "operation_id": job_trace["operator"]})
    return env02("PromptAuthorityTrace", {
        "compiled_request_hash": digest(payload), "style_skill_hashes": [job_trace["skill_hash"]], "original_brief_hash": job_trace["brief_hash"],
        "model_id": payload["model"], "segments": segs, "runtime_style_invention_prohibited": True,
        "prompt_text_sha": sha256_bytes(payload["positivePrompt"].encode()), "reference_image_hashes": list(ref_shas)})


def art_approval(a: dict) -> dict:
    return env02("ArtApproval", {"approval_id": a["approval_id"], "run_id": a["run_id"], "original_brief_id": a["original_brief_id"],
                                 "image_hashes": a["image_hashes"], "skill_versions": a["skill_versions"],
                                 "verdict": "ARTWORK_APPROVED" if a["verdict"] == "APPROVED" else "ARTWORK_REJECTED",
                                 "user_feedback": [str(x) for x in a.get("defects", [])], "signed_at": a["signed_at"], "signed_by": a["signed_by"]})


def asset_approval(a: dict) -> dict:
    return env02("AssetApproval", {k: a[k] for k in ("approval_id", "run_id", "approved_art_ids", "asset_manifest_sha256",
                                                     "character_family_ids", "signed_at", "signed_by")}
                 | {"verdict": "ASSETS_APPROVED" if a["verdict"] == "APPROVED" else "ASSETS_REJECTED"})


def visual_gate_state(g: dict) -> dict:
    return env02("VisualGateState", {k: g[k] for k in ("run_id", "state", "required_art_approval_ids", "required_asset_approval_ids",
                                                       "authorized_render_art_hashes", "authorized_render_asset_hashes", "blocked_reasons")})


def visual_review(r: dict) -> dict:
    return env02("VisualReview", {"review_id": r["review_id"], "run_id": r["run_id"], "verdict": r["verdict"],
                                  "top_remaining_gaps": r["top_remaining_gaps"], "recommended_next_focus": r.get("preferred_next_focus", ""),
                                  "feedback": f"submitted by {r['submitted_by']}", "timestamp": r["timestamp"], "submitted_by": "USER"})


def conditional_style_decision(d: dict, recipe_id: str) -> dict:
    status = {"RESEARCH_ONLY": "CANDIDATE", "EXECUTABLE_CANDIDATE": "SOURCE_SUPPORTED", "DEMONSTRATED": "PRODUCTION_DEMONSTRATED",
              "TRANSFERABLE": "TRANSFER_DEMONSTRATED"}[d["status"]]
    br = d["branches"][0]
    return env02("ConditionalStyleDecision", {
        "decision_id": d["decision_id"], "witness_ids": d.get("evidence_frame_ids") or ["SYNTHETIC"], "visible_quality": d["target_quality"],
        "applies_when": {k: str(v) for k, v in br["when"].items()}, "design_operation": br["construction_action"],
        "invariants": [d["invariant_visual_relation"]], "adapts_with": d["adaptive_visual_choices"], "exceptions": d["exceptions"],
        "original_freedom": d.get("creative_freedom") or ["original subject identity"], "dependencies": d.get("dependencies", []),
        "visual_prediction": d.get("expected_visible_effect") or d["target_quality"], "production_recipe_id": recipe_id,
        "prompt_template_ids": [c for b in d["branches"] for c in b["clause_ids"]], "evidence_status": status,
        "unknowns": [str(u) for u in d.get("uncertainty", [])] or ["profile view behaviour"]})


def character_construction_plan(p: dict) -> dict:
    return env02("CharacterConstructionPlan", {
        "character_id": p["character_id"], "original_brief_id": p["original_brief_id"], "style_skill_version_hash": p["style_skill_version_hash"],
        "canonical_art_route": p["canonical_art_route"], "silhouette_design_decisions": ["D-SYN-CHAR-WHOLE"],
        "face_design_decisions": ["D-SYN-FACE-VIEW"], "required_action_states": p["required_action_states"],
        "generation_sequence": [s["step"] for s in p["generation_sequence"]], "identity_reference_rule": p["identity_reference_rule"],
        "hand_prop_construction_routes": [s["step"] for s in p["hand_prop_construction_routes"]],
        "layer_and_occlusion_method": p["layer_and_occlusion_method"], "expected_output_paths": [s["output"] for s in p["generation_sequence"]]})


def provider_call(result: dict, brief_id: str, payload: dict) -> dict:
    return env02("ProviderCall", {
        "call_id": result["job_id"], "provider": "runware", "model_id": payload["model"], "task": "TEXT_TO_IMAGE" if not payload.get("inputs") else "REFERENCE_CONDITIONING",
        "request_sha256": result["request_body_sha256"], "input_brief_id": brief_id, "authorized_external_source_upload": False,
        "reference_ids": result["reference_shas"], "status": "SUCCEEDED", "usage_cost_status": "NONE" if result["adapter_kind"] != "REAL" else "REPORTED",
        "cost_usd": None, "outputs": [o["path"] for o in result["outputs"]], "output_hashes": [o["sha256"] for o in result["outputs"]],
        "created_at": result["committed_at"]})


# ---- 21 -------------------------------------------------------------------------------------
def frame_witness(w: dict, film_sha_hex: str) -> dict:
    reg = w.get("region") or {}
    return env21("FrameWitness", {"film_sha256": film_sha_hex, "frame_index": w["frame_start"], "pts": float(w["frame_start"]) / 60.0,
                                  "visible_relation": w["visible_relation"], "scene_specific_facts": w.get("scene_specific_facts", []),
                                  "native_regions": [reg] if reg else [], "limits": w.get("limits") or "SYNTHETIC fixture witness"})


def question_trace(q: dict) -> dict:
    return env21("QuestionTrace", {"id": q["question_id"], "cluster_id": q["cluster_id"], "visible_target": q["exact_artistic_unknown"],
                                   "production_unknown": q["missing_producing_operation"], "witness_ids": q["observed_contrast_with_witness_ids"],
                                   "evidence_needed": [str(x) for x in q["planned_witness_or_input_ids"]],
                                   "answer_status": q["answer_status"], "answer": q["effect_on_skill_version_and_compiled_job"],
                                   "next_ids": [], "operator_affected": q["missing_producing_operation"]})


def style_decision(d: dict) -> dict:
    status = {"RESEARCH_ONLY": "CANDIDATE", "EXECUTABLE_CANDIDATE": "SUPPORTED", "DEMONSTRATED": "SUPPORTED", "TRANSFERABLE": "SUPPORTED"}[d["status"]]
    return env21("StyleDecision", {
        "id": d["decision_id"], "evidence_ids": d.get("evidence_frame_ids") or ["SYNTHETIC"], "visible_effect": d["target_quality"],
        "conditions": {k: str(v) for k, v in d["branches"][0]["when"].items()}, "construction_action": d["branches"][0]["construction_action"],
        "invariants": [d["invariant_visual_relation"]], "adaptations": d["adaptive_visual_choices"], "exceptions": d["exceptions"],
        "free_content": d.get("creative_freedom") or ["original identity"], "dependencies": d.get("dependencies", []),
        "operation_ids": sorted({o for b in d["branches"] for o in b["operation_node_ids"]}),
        "predicted_pixels_change": d.get("expected_visible_effect") or d["target_quality"],
        "source_specific_excluded": d.get("forbidden_source_specific_copies") or ["none declared"], "status": status})


def operation_node(n: dict) -> dict:
    from ..skills.operators import OPERATORS
    return env21("OperationNode", {"id": n["id"], "kind": OPERATORS[n["operator"]]["kind"], "decisions": n.get("decisions", []),
                                   "inputs": n.get("inputs", []), "required_capabilities": OPERATORS[n["operator"]]["requires"] or ["local"],
                                   "outputs": n.get("outputs", []), "depends_on": n.get("depends_on", [])})


def skill_clause(c: dict) -> dict:
    return env21("SkillClause", {k: c[k] for k in ("id", "decision_id", "priority", "template", "allowed_content_slots", "reference_roles")}
                 | {"operation_id": c["operation_id"]})


def character_plan(p: dict, canonical_art_id: str) -> dict:
    states = [{"id": s["step"], "view": s["step"].split(":")[1] if s["step"].startswith("view") else "canonical",
               "pose": s["step"], "expression": s["step"].split(":")[1] if s["step"].startswith("expr") else "neutral", "full_art_asset": s["output"]}
              for s in p["generation_sequence"] if s["kind"] == "CHARACTER_STATE"]
    hp = [{"hand": s["hand_side"], "prop": s["prop_id"], "visible_side": "near", "state_id": s["step"]} for s in p["hand_prop_construction_routes"]]
    return env21("CharacterPlan", {"character_id": p["character_id"], "style_version": p["style_skill_version_hash"],
                                   "canonical_art_id": canonical_art_id, "whole_design_decisions": ["D-SYN-CHAR-WHOLE", "D-SYN-FACE-VIEW"],
                                   "required_pose_states": states, "hand_prop_interactions": hp})


def raster_asset(o: dict) -> dict:
    return env21("RasterAsset", {k: o[k] for k in ("id", "sha256", "width", "height", "pixel_mode", "has_nonopaque_alpha", "coordinate_space",
                                                   "origin_x", "origin_y", "owner", "skill_version")})


def semantic_checkpoint(ck: dict, boundary: dict) -> dict:
    return env21("SemanticCheckpoint", {"film_sha256": ck["film_sha256"], "committed_packet_id": ck["packet_id"], "next_frame": ck["next_frame_index"],
                                        "active_scene": boundary.get("scene_world", "UNKNOWN"),
                                        "objects": [o.get("id", str(o)) if isinstance(o, dict) else str(o) for o in boundary.get("active_objects", [])],
                                        "actions": [e.get("event_id", "?") for e in boundary.get("open_events", [])],
                                        "active_questions": [str(q) for q in ck["unresolved_questions"]], "unresolved_theories": [],
                                        "current_skill_versions": [], "provider_request_state": None})


def prompt_trace(job_trace: dict, payload: dict, ref_shas: list) -> dict:
    return env21("PromptTrace", {"brief_hash": job_trace["brief_hash"], "skill_hash": job_trace["skill_hash"],
                                 "decision_ids": job_trace["selected_decisions"], "clause_ids": job_trace["clause_ids"],
                                 "reference_sha256s": list(ref_shas), "model_air_id": payload["model"],
                                 "operation_graph_sha": digest(job_trace["scene_art_plan"]["dependency_graph"]),
                                 "provider_payload_sha": digest(payload),
                                 "authority": {"style": "frozen_skill_clauses", "content": "original_brief_slots",
                                               "identity": "approved_identity_assets", "technical": "provider_capabilities"}})


def audit_row(row: dict) -> dict:
    return env21("AuditRow", {k: row[k] for k in ("id", "module", "entrypoint", "test_command", "result", "evidence", "status")})
