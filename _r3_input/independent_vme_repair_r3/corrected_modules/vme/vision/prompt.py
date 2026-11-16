"""Vision-agent request built from typed manifest + active questions (ADD25 §2.4, ADD27 §2 steps A–H).

SOURCE ANALYSIS ONLY. This text never becomes an image-generation aesthetic clause.
"""
from __future__ import annotations

from ..util import digest
from .protocol import PROTOCOL_SHA, PROTOCOL_VERSION, bind, pass_instructions

VISION_PROMPT_VERSION = f"{PROTOCOL_VERSION}/P1"

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

# Content-addressed semantics, not a manually-maintained version label.
# Parser and image-transform digests are separately added by the runner.
VISION_PROMPT_SHA = digest({"instructions": pass_instructions("P1") + "\n\n" + _TEMPLATE,
                            "version": VISION_PROMPT_VERSION, "protocol_sha": PROTOCOL_SHA})


def build_vision_request(packet_id: str, target_manifest: list[dict], context_manifest: list[dict],
                         active_questions: list[dict], prior_boundary: dict | None, *, source: dict | None = None,
                         sequence: dict | None = None, active_cluster: dict | None = None, controlling_problem: dict | None = None,
                         competing: list | None = None) -> dict:
    if not 1 <= len(active_questions) <= 4:
        active_questions = active_questions[:4] or [{"question_id": "NONE", "text": "No active question: record observations only."}]
    binding = bind(
        protocol={"version": PROTOCOL_VERSION, "sha": PROTOCOL_SHA, "pass_id": "P1"},
        source=source or {"sha": (target_manifest[0].get("source_sha") if target_manifest else None), "stream_id": "0:v:0",
                          "real_resolution": [target_manifest[0].get("width"), target_manifest[0].get("height")] if target_manifest else None,
                          "source_role_lock_state": "UNSTATED"},
        sequence=sequence or {"current_packet_start": target_manifest[0]["frame_id"] if target_manifest else None,
                              "current_packet_end": target_manifest[-1]["frame_id"] if target_manifest else None,
                              "context_frame_ids": [m["frame_id"] for m in context_manifest]},
        target_images=[{"frame_id": m["frame_id"], "pts": m.get("pts"), "bytes_sha": m["image_sha"]} for m in target_manifest],
        prior_boundary=prior_boundary or {"actor_ids": [], "object_ids": [], "drawing_states": [], "open_events": [], "attention": "UNKNOWN",
                                          "unfinished_hypotheses": []},
        active_cluster=active_cluster or {"cluster_id": "INITIAL_EVERY_FRAME_PASS", "deficits": [], "open_decisions": []},
        controlling_problem=controlling_problem or {"missing_producer_choice": (active_questions[0].get("text") if active_questions else "NONE")},
        current_competing_explanations=competing or [],
        required_response={"per_frame_records": True, "packet_event_delta": True, "new_source_questions": True, "uncertainty": True,
                           "next_boundary": True})
    req = {
        "prompt_version": VISION_PROMPT_VERSION,
        "prompt_content_sha": VISION_PROMPT_SHA,
        "protocol": binding["protocol"],
        "binding": binding,
        "instructions": pass_instructions("P1") + chr(10) * 2 + _TEMPLATE,
        "packet_id": packet_id,
        "target_frames": [{"frame_id": m["frame_id"], "image_sha": m["image_sha"], "pts_time": m["pts_time"],
                           "order": i} for i, m in enumerate(target_manifest)],
        "context_frames": [{"frame_id": m["frame_id"], "image_sha": m["image_sha"], "pts_time": m["pts_time"],
                            "role": "CONTEXT_NOT_TARGET"} for m in context_manifest],
        "active_questions": active_questions,
        "prior_boundary_state": prior_boundary or {},
        "required_output_schema": "FrameObservation[] (+persistent_state_ids, ended_state_ids, unexplained_phenomena) + packet_transition_graph "
                                  "+ boundary_state + reconciled_events + question_update",
    }
    req["request_sha"] = digest(req)
    return req
