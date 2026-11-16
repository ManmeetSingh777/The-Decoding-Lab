"""Character-first manufacture contracts (spec 16, Addendum 24 B–C, A58–A60, B21, B27, C20–C22).

Canonical whole illustration FIRST → canonical-conditioned whole view/pose/face/hand+prop
states → only then the minimum separable layers and clean plates. No tube/SVG actors.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

from ..util import Blocked, is_vague_statement

CHARACTER_QUESTION_FAMILIES = (
    "whole_design_identity", "silhouette_at_meaningful_states", "character_specific_proportions",
    "shape_organization_and_art_finish", "face_construction_and_identity", "expression_as_whole_actor",
    "hands_arms_and_contact", "views_scale_environmental_integration", "illustration_diversity_without_style_collapse",
    "construction_to_tool_translation")
CHARACTER_ANSWER_FIELDS = ("observed_whole_visual_effect", "source_witnesses", "contrasting_witnesses", "artistic_relationships",
                           "candidate_cause", "what_is_actor_specific", "what_transfers", "condition_of_use",
                           "expected_new_art_change", "actual_art_operation", "unresolved_production_ambiguity")
_BANNED_SHALLOW = ("bold eyes", "big eyes", "rounded body", "appealing character", "cute", "head-to-body ratio", "head to body ratio")


def validate_character_answer(family: str, ans: dict, registered_ops: dict) -> dict:
    """Add24 B2: reject 'bold eyes'/'rounded body'/bare ratios and claims without exact frame witnesses."""
    p = []
    if family not in CHARACTER_QUESTION_FAMILIES:
        p.append("UNKNOWN_FAMILY")
    for f in CHARACTER_ANSWER_FIELDS:
        if f not in ans:
            p.append(f"MISSING:{f}")
    txt = " ".join(str(ans.get(k, "")) for k in ("observed_whole_visual_effect", "artistic_relationships", "what_transfers")).lower()
    if any(b in txt for b in _BANNED_SHALLOW) and not ans.get("artistic_relationships"):
        p.append("SHALLOW_PART_LABEL")
    if any(b in txt for b in _BANNED_SHALLOW) and is_vague_statement(str(ans.get("artistic_relationships", ""))):
        p.append("SHALLOW_PART_LABEL")
    if not ans.get("source_witnesses"):
        p.append("NO_EXACT_FRAME_WITNESS")
    if not ans.get("contrasting_witnesses"):
        p.append("NO_UNLIKE_ACTOR_CONTRAST")
    op = (ans.get("actual_art_operation") or {}).get("operation_id")
    if op not in registered_ops:
        p.append("NO_ART_OPERATION")
    import re
    if re.search(r"\b\d+(\.\d+)?\s*(:|/)\s*\d+", txt) and "condition" not in txt:
        p.append("BARE_RATIO_AS_CONSTANT")
    return {"ok": not p, "problems": p}


def cross_actor_witness_group(witnesses: list[dict], production_problem: str) -> dict:
    """Add24 B1 (a)–(f): whole actor in scene, crops if needed, consecutive states or UNKNOWN,
    a DIFFERENT actor/subject class from another film, a contrast/exception, the production problem."""
    whole = [w for w in witnesses if w["evidence_kind"] in ("FULL_FRAME", "SYNTHETIC_FIXTURE")]
    temporal = [w for w in witnesses if w["evidence_kind"] == "TEMPORAL_COMPARE"]
    films = {w["film_sha256"] for w in witnesses}
    classes = {w.get("subject_class") for w in witnesses if w.get("subject_class")}
    contrast = [w for w in witnesses if "exception" in w["visible_relation"].lower() or w.get("is_contrast")]
    status = {"a_whole_actor_in_scene": bool(whole), "b_native_crops": any(w["evidence_kind"] == "NATIVE_CROP" for w in witnesses),
              "c_consecutive_states": "PRESENT" if temporal else "UNKNOWN",
              "d_different_actor_other_film": len(films) >= 2 and len(classes) >= 2,
              "e_contrast_or_documented_absence": bool(contrast), "f_production_problem": bool(production_problem)}
    scope = "INVESTIGATION_START_ONLY"
    if all(status[k] for k in ("a_whole_actor_in_scene", "d_different_actor_other_film", "e_contrast_or_documented_absence",
                               "f_production_problem")) and temporal:
        scope = "SUPPORTED_FOR_CONDITIONAL_DECISION"
    return {"status": status, "scope": scope, "never_universal_from_one_actor": True}


@dataclass
class AnimationDemandPlan:
    character_id: str
    views: list
    expressions: list
    gestures: list
    contacts: list               # [{hand_side, prop_id, event_id}]
    depth_orders: list
    camera_scales: list
    occluded_surfaces_to_create: list
    independent_parts: list

    def to_dict(self) -> dict:
        return asdict(self)


def derive_animation_demand(character_id: str, shot_actions: list[dict]) -> AnimationDemandPlan:
    """A60: decide states, contacts, layers and hidden surfaces from intended motion BEFORE art generation."""
    views, exprs, gests, contacts, depth, scales, occl, parts = [], [], [], [], [], [], [], []
    for a in shot_actions:
        if a.get("actor") != character_id:
            continue
        if a.get("view") and a["view"] not in views:
            views.append(a["view"])
        if a.get("expression"):
            exprs.append(a["expression"])
        if a.get("gesture"):
            gests.append(a["gesture"])
        if a.get("contact_prop"):
            contacts.append({"hand_side": a.get("hand_side", "UNSPECIFIED"), "prop_id": a["contact_prop"], "event_id": a["event_id"]})
            depth.append({"event_id": a["event_id"], "order": ["far_arm", "torso", "prop", "near_hand"]})
        if a.get("moves_part"):
            parts.append(a["moves_part"])
            occl.append({"behind_part": a["moves_part"], "needs": "clean_plate_or_hidden_surface_art"})
        if a.get("camera_scale"):
            scales.append(a["camera_scale"])
    for c in contacts:
        if c["hand_side"] == "UNSPECIFIED":
            raise Blocked("CONTACT_HAND_SIDE_UNSPECIFIED", c["event_id"])
    return AnimationDemandPlan(character_id, views or ["canonical"], exprs, gests, contacts, depth, scales, occl, parts)


def character_construction_plan(character_id: str, brief_id: str, skill_hash: str, demand: AnimationDemandPlan) -> dict:
    seq = [{"step": "canonical", "operator": "op.canonical_character", "depends_on": [], "output": f"{character_id}:canonical",
            "kind": "CHARACTER_CANONICAL", "whole_drawing": True}]
    for v in demand.views:
        if v != "canonical":
            seq.append({"step": f"view:{v}", "operator": "op.face_view_state", "depends_on": [f"{character_id}:canonical"],
                        "output": f"{character_id}:view:{v}", "kind": "CHARACTER_STATE", "whole_drawing": True,
                        "identity_reference": f"{character_id}:canonical"})
    for e in demand.expressions:
        seq.append({"step": f"expr:{e}", "operator": "op.face_view_state", "depends_on": [f"{character_id}:canonical"],
                    "output": f"{character_id}:expr:{e}", "kind": "CHARACTER_STATE", "whole_drawing": True,
                    "identity_reference": f"{character_id}:canonical", "note": "integrated face drawing, not feature tweening"})
    for c in demand.contacts:
        seq.append({"step": f"grip:{c['prop_id']}", "operator": "op.hand_prop_contact", "depends_on": [f"{character_id}:canonical"],
                    "output": f"{character_id}:grip:{c['prop_id']}", "kind": "CHARACTER_STATE", "whole_drawing": True,
                    "identity_reference": f"{character_id}:canonical", "hand_and_prop_in_one_drawing": True,
                    "hand_side": c["hand_side"], "prop_id": c["prop_id"]})
    whole_outputs = [s["output"] for s in seq]
    for part in demand.independent_parts:
        seq.append({"step": f"layer:{part}", "operator": "op.layer_extract", "depends_on": whole_outputs,
                    "output": f"{character_id}:layer:{part}", "kind": "LAYER", "whole_drawing": False})
        seq.append({"step": f"clean_plate:{part}", "operator": "op.clean_plate", "depends_on": [f"{character_id}:layer:{part}"],
                    "output": f"{character_id}:clean_plate:{part}", "kind": "CLEAN_PLATE", "whole_drawing": False})
    plan = {"character_id": character_id, "original_brief_id": brief_id, "style_skill_version_hash": skill_hash,
            "canonical_art_route": "op.canonical_character", "generation_sequence": seq,
            "identity_reference_rule": "every derived state conditions on the APPROVED canonical image bytes",
            "hand_prop_construction_routes": [s for s in seq if s.get("hand_and_prop_in_one_drawing")],
            "layer_and_occlusion_method": "segment only parts that move independently, after whole poses; clean plates for exposed areas",
            "required_action_states": [s["output"] for s in seq if s["kind"] == "CHARACTER_STATE"],
            "demand": demand.to_dict(), "svg_or_tube_actor_allowed": False}
    validate_construction_order(plan)
    return plan


def validate_construction_order(plan: dict) -> None:
    seq = plan["generation_sequence"]
    if not seq or seq[0]["operator"] != "op.canonical_character":
        raise Blocked("CANONICAL_NOT_FIRST", "character must start from a whole canonical illustration")
    seen_layer = False
    for s in seq:
        if s["kind"] == "LAYER":
            seen_layer = True
        if s["kind"] == "CHARACTER_STATE":
            if seen_layer:
                raise Blocked("LAYERS_BEFORE_WHOLE_POSE", s["step"])
            if not s.get("identity_reference"):
                raise Blocked("STATE_WITHOUT_CANONICAL_IDENTITY", s["step"])
        if s["operator"] in ("op.hand_prop_contact",) and not s.get("hand_and_prop_in_one_drawing"):
            raise Blocked("HAND_AND_PROP_GENERATED_SEPARATELY", s["step"])
        if s.get("kind") == "SVG_ACTOR" or s.get("operator", "").startswith("svg"):
            raise Blocked("SVG_TUBE_ACTOR_FORBIDDEN", s["step"])
