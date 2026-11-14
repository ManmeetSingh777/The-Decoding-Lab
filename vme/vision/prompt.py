"""Vision-agent request built from typed manifest + active questions (ADD25 §2.4, ADD27 §2 steps A–H).

SOURCE ANALYSIS ONLY. This text never becomes an image-generation aesthetic clause.
"""
from __future__ import annotations

from ..util import digest

VISION_PROMPT_VERSION = "vision-investigator/1"

_TEMPLATE = """ROLE: Visual-artwork and temporal construction investigator.
INPUT: original consecutive image frames with manifest [frame ID -> actual image], current whole-scene/character state and 1-4 active high-impact questions.
SCOPE: Only source-visible evidence; never claim source art-making software or intent.
FIRST (Step A): inspect the complete picture for each frame at normal displayed scale. Identify the focal artwork, its deliberate shape/part relationships, supporting world, material/colour organization, depth and notable simultaneous visible activity.
(Step B): enumerate visible art systems (whole drawing, subparts, art treatment, layer relationships, role in the complete design), not only semantic nouns.
SECOND (Step C): compare EVERY target image to its real neighbor images in time. Identify preserved identity and changes of whole-actor drawing, face/eyes/hands, contact, world layers, apparent camera changes and moving focal emphasis. Label each change OBSERVED_DIFF, INFERRED_3D, INFERRED_CAMERA, INFERRED_NEW_DRAWING or UNKNOWN.
THIRD (Steps D-E): seek evidence relevant to the active questions; identify which visible relations appear to create the sought high-impact quality and which NEW-SUBJECT producer decision they bear on. Do not promote a source fact to style. Separate OBSERVED, INFERENCE, UNKNOWN.
FOURTH: for EACH target frame emit a typed FrameObservation with the exact frame ID and the submitted image's identity; concise specific visual facts and temporal relations; if nothing meaningful changes, explain what persists without inventing novelty (no_significant_change_reason).
FIFTH (Steps F-H): emit a PacketTransitionGraph of linked simultaneous changes, reconcile every open event from the prior boundary state, list visually significant elements NOT explained by the current model (dimension extensions allowed), and the single unanswered HIGH-IMPACT question the next source frames/crops should resolve.
DO NOT: use "vibrant", "dynamic", "professional", "clean vector" as standalone explanations; write fixed palettes/character coordinates as universal style; infer proprietary source tooling; hide missing frames; repeat empty prose; confuse character-art changes with camera motion; invent unseen features.
IF visual evidence is inadequate, state UNKNOWN + exact missing image/viewpoint.
OUTPUT: strict schema, no natural-language summary instead of frame entries."""


def build_vision_request(packet_id: str, target_manifest: list[dict], context_manifest: list[dict],
                         active_questions: list[dict], prior_boundary: dict | None) -> dict:
    if not 1 <= len(active_questions) <= 4:
        active_questions = active_questions[:4] or [{"question_id": "NONE", "text": "No active question: record observations only."}]
    req = {
        "prompt_version": VISION_PROMPT_VERSION,
        "instructions": _TEMPLATE,
        "packet_id": packet_id,
        "target_frames": [{"frame_id": m["frame_id"], "image_sha": m["image_sha"], "pts_time": m["pts_time"],
                           "order": i} for i, m in enumerate(target_manifest)],
        "context_frames": [{"frame_id": m["frame_id"], "image_sha": m["image_sha"], "pts_time": m["pts_time"],
                            "role": "CONTEXT_NOT_TARGET"} for m in context_manifest],
        "active_questions": active_questions,
        "prior_boundary_state": prior_boundary or {},
        "required_output_schema": "FrameObservation[] + packet_transition_graph + boundary_state + reconciled_events + question_update",
    }
    req["request_sha"] = digest(req)
    return req
