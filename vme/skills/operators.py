"""Registered producing operators (spec 14 T5, 15 §3.5, 20 STEP 4). Unknown operators are refused.

Each operator declares the provider/local capabilities it needs. Provider-backed operators
execute ONLY through `StyleImageGateway` with an issued `CompiledImageJob`; local operators
(layer/mask/composite/render) operate on real raster bytes.
"""
from __future__ import annotations

from ..util import Blocked

OPERATORS: dict[str, dict] = {
    "op.whole_scene": {"kind": "whole_scene", "backend": "provider", "requires": ["textToImage"],
                       "outputs": ["WHOLE_SCENE"], "identity_reference_required": False},
    "op.world_plate": {"kind": "world_plate", "backend": "provider", "requires": ["textToImage"],
                       "outputs": ["WORLD_PLATE"], "identity_reference_required": False, "content_slots": ["setting"],
                       "note": "clean environment with NO actor, so separately generated actors are never duplicated (R18)"},
    "op.canonical_character": {"kind": "canonical_character", "backend": "provider", "requires": ["textToImage"],
                               "outputs": ["CHARACTER_CANONICAL"], "identity_reference_required": False},
    "op.guided_pose_edit": {"kind": "guided_pose_edit", "backend": "provider", "requires": ["imageEdit", "referenceImages"],
                            "outputs": ["CHARACTER_STATE"], "identity_reference_required": True},
    "op.hand_prop_contact": {"kind": "guided_pose_edit", "backend": "provider", "requires": ["imageEdit", "referenceImages"],
                             "outputs": ["CHARACTER_STATE"], "identity_reference_required": True},
    "op.face_view_state": {"kind": "guided_pose_edit", "backend": "provider", "requires": ["imageEdit", "referenceImages"],
                           "outputs": ["CHARACTER_STATE"], "identity_reference_required": True},
    "op.region_edit": {"kind": "region_edit", "backend": "provider", "requires": ["imageEdit", "mask"],
                       "outputs": ["WHOLE_SCENE"], "identity_reference_required": False},
    "op.layer_extract": {"kind": "layer_extract", "backend": "local", "requires": ["mask_source"],
                         "outputs": ["LAYER", "MASK"], "identity_reference_required": False},
    "op.clean_plate": {"kind": "clean_plate", "backend": "provider", "requires": ["imageEdit", "mask"],
                       "outputs": ["CLEAN_PLATE"], "identity_reference_required": False},
    "op.composite": {"kind": "composite", "backend": "local", "requires": [], "outputs": ["WHOLE_SCENE"],
                     "identity_reference_required": False},
    "op.motion_render": {"kind": "motion_render", "backend": "renderer", "requires": ["remotion", "ffmpeg"],
                         "outputs": ["MP4"], "identity_reference_required": False},
}

PROVIDER_OPERATION_KINDS = ("whole_scene", "world_plate", "canonical_character", "guided_pose_edit", "region_edit", "clean_plate")


def get_operator(op_id: str) -> dict:
    if op_id not in OPERATORS:
        raise Blocked("UNKNOWN_OPERATOR", op_id)
    return OPERATORS[op_id]


def registered() -> dict:
    return dict(OPERATORS)


def provider_supports(op_id: str, caps: dict) -> list[str]:
    """Return list of missing capabilities for running op on this provider snapshot."""
    op = get_operator(op_id)
    if op["backend"] != "provider":
        return []
    have = set(caps.get("supported_capabilities", []))
    return [r for r in op["requires"] if r not in have]
