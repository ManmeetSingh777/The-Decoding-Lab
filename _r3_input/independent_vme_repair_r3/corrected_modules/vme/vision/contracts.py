"""Per-frame vision contracts and validation (ADD25 §2.3, spec 10 §3, A61–A63, B04/B05, ADD25-F02..F07).

`SENT` is not `SEEN`: a frame advances to VISION_OUTPUT_VERIFIED only when the
provider response contains a valid frame-specific record whose echoed image hash
matches the exact bytes we submitted for that frame.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any

from ..util import is_vague_statement

# Per-frame coverage statuses; ordered weakest → strongest. Separate claims, never merged.
COVERAGE_STATUSES = (
    "INDEXED_ONLY", "SURVEYED_FOR_SELECTION", "AUTOMATED_VISUAL_FEATURES", "SENT_TO_VISION",
    "VISION_OUTPUT_VERIFIED", "NATIVE_DETAIL_REVIEWED", "ARTISTICALLY_EXPLAINED", "UNKNOWN_OR_FAILED",
)
PACKET_STATES = ("PLANNED", "INPUTS_READY", "REQUEST_IN_FLIGHT", "RESULT_RECEIVED", "VALIDATED",
                 "SEMANTIC_COMMITTED", "QUARANTINED", "RETRY_WAIT", "BLOCKED_CONSENT", "UNKNOWN_BILLING",
                 "NEEDS_REINSPECTION")

FRAME_OBSERVATION_FIELDS = (
    "frame_id", "source_sha", "pts_time", "request_id", "submitted_image_sha", "active_question_ids",
    "scene_and_world_state", "actually_visible_actor_and_object_ids", "focal_whole_artwork_state",
    "visible_design_relations", "character_face_limb_contact_state", "visible_layer_depth_attention_state",
    "changed_since_prior_frame", "simultaneous_event_links", "camera_vs_actor_vs_drawing_state",
    "material_finish_or_colour_change", "native_detail_followups", "source_fact_statements",
    "hypothesis_or_uncertainty", "raw_response_path", "confidence_limitations",
    "persistent_state_ids", "unexplained_phenomena",          # Addendum 28 (ST28-01/06)
)
DIFF_KINDS = ("OBSERVED_DIFF", "INFERRED_3D", "INFERRED_CAMERA", "INFERRED_NEW_DRAWING", "UNKNOWN")


@dataclass
class FrameManifestItem:
    frame_id: str
    source_sha: str
    presentation_index: int
    pts: int
    pts_time: float
    image_sha: str
    width: int
    height: int
    scale_factor: float
    is_target: bool
    raw_identity_sha: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SemanticBoundaryState:
    scene_world: str = "UNKNOWN"
    active_objects: list = field(default_factory=list)           # [{id, identity, art_treatment, drawing_state}]
    open_events: list = field(default_factory=list)              # [{event_id, kind, started_frame, actors}]
    attention: str = "UNKNOWN"
    hypotheses: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)
    last_frame_index: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def frame_id_for(film_sha: str, index: int) -> str:
    return f"{film_sha[:16]}:{index}"


def validate_packet_response(response: Any, target_manifest: list[dict], prior_boundary: dict | None,
                             *, images_actually_sent: int) -> dict:
    """Return {ok, status, problems, observations, transition_graph, boundary} — no side effects."""
    problems: list[str] = []
    weak: list[str] = []
    if not isinstance(response, dict):
        return {"ok": False, "status": "QUARANTINED", "problems": ["RESPONSE_NOT_OBJECT"]}
    receipt = response.get("receipt", {})
    if receipt.get("images_received") is not None and receipt["images_received"] != images_actually_sent:
        problems.append(f"PROVIDER_RECEIVED_{receipt['images_received']}_OF_{images_actually_sent}_IMAGES")
    obs = response.get("frame_observations")
    if not isinstance(obs, list):
        if isinstance(response.get("summary"), str):
            problems.append("SUMMARY_INSTEAD_OF_PER_FRAME_ENTRIES")
        else:
            problems.append("NO_FRAME_OBSERVATIONS")
        return {"ok": False, "status": "NEEDS_REINSPECTION", "problems": problems, "weak": weak}
    want = {m["frame_id"]: m for m in target_manifest}
    got_ids = [o.get("frame_id") for o in obs if isinstance(o, dict)]
    dups = {i for i in got_ids if got_ids.count(i) > 1}
    if dups:
        problems.append(f"DUPLICATE_FRAME_ENTRIES:{sorted(str(d) for d in dups)[:5]}")
    missing = [fid for fid in want if fid not in got_ids]
    extra = [fid for fid in got_ids if fid not in want]
    if missing:
        problems.append(f"MISSING_FRAME_ENTRIES:{missing[:10]}")
    if extra:
        problems.append(f"UNREQUESTED_FRAME_ENTRIES:{extra[:10]}")
    hash_mismatch = []
    for o in obs:
        if not isinstance(o, dict) or o.get("frame_id") not in want:
            continue
        m = want[o["frame_id"]]
        absent = [f for f in FRAME_OBSERVATION_FIELDS if f not in o and f not in ("raw_response_path",)]
        if absent:
            problems.append(f"FIELDS_MISSING:{o['frame_id']}:{absent[:4]}")
        if o.get("submitted_image_sha") != m["image_sha"]:
            hash_mismatch.append(o["frame_id"])
        if o.get("source_sha") != m["source_sha"]:
            problems.append(f"SOURCE_SHA_MISMATCH:{o['frame_id']}")
        if o.get("pts_time") is not None and abs(float(o["pts_time"]) - m["pts_time"]) > 1e-6:
            problems.append(f"PTS_MISMATCH:{o['frame_id']}")
        changes = o.get("changed_since_prior_frame") or []
        if not changes and not o.get("no_significant_change_reason"):
            problems.append(f"UNCHANGED_WITHOUT_REASON:{o['frame_id']}")
        for c in changes:
            if isinstance(c, dict) and c.get("kind") not in DIFF_KINDS:
                problems.append(f"BAD_DIFF_KIND:{o['frame_id']}")
        if not str(o.get("focal_whole_artwork_state", "")).strip():
            problems.append(f"EMPTY_FRAME_ENTRY:{o['frame_id']}")
        elif is_vague_statement(str(o.get("focal_whole_artwork_state", ""))):
            weak.append(o["frame_id"])
        # A fluent scene summary without ANY typed source-visible design/event
        # relation is not a construction-grade observation. An entirely empty
        # frame should be explicitly described as an observed source fact.
        relations = o.get("visible_design_relations") or []
        facts = o.get("source_fact_statements") or []
        if not relations and not facts:
            problems.append(f"NO_TYPED_SOURCE_VISUAL_FACTS:{o['frame_id']}")
        for rel in relations:
            if (not isinstance(rel, dict) or not isinstance(rel.get("relation"), str)
                    or is_vague_statement(rel.get("relation", ""))):
                problems.append(f"UNUSABLE_SOURCE_DESIGN_RELATION:{o['frame_id']}")
    if hash_mismatch:
        return {"ok": False, "status": "QUARANTINED", "problems": problems + [f"IMAGE_HASH_MISMATCH:{hash_mismatch[:5]}"],
                "weak": weak}
    # A generic per-frame description is not an artistically verified observation.
    # Preserve the exact weak ids for targeted reinspection; do not promote them.
    if weak:
        problems.append(f"ARTISTIC_FRAME_OBSERVATIONS_INSUFFICIENT:{weak[:10]}")
    texts = [str(o.get("focal_whole_artwork_state", "")) for o in obs if isinstance(o, dict)]
    if len(texts) > 1 and len(set(texts)) == 1 and not all(o.get("no_significant_change_reason") for o in obs[1:]):
        problems.append("GENERIC_UNDIFFERENTIATED_ENTRIES")
    graph = response.get("packet_transition_graph")
    if not isinstance(graph, dict) or "edges" not in graph:
        problems.append("NO_PACKET_TRANSITION_GRAPH")
    boundary = response.get("boundary_state")
    if not isinstance(boundary, dict):
        problems.append("NO_BOUNDARY_STATE")
    elif prior_boundary:
        # A63: every event open at the previous boundary must be reconciled (continued or closed).
        recon = {e.get("event_id"): e.get("resolution") for e in response.get("reconciled_events", [])}
        for ev in prior_boundary.get("open_events", []):
            if ev.get("event_id") not in recon:
                problems.append(f"BOUNDARY_EVENT_NOT_RECONCILED:{ev.get('event_id')}")
        # ST28-06: identities active at the previous boundary must persist or be explicitly ended in the first target frame
        first = next((o for o in sorted([x for x in obs if isinstance(x, dict) and x.get("frame_id") in want],
                                        key=lambda x: list(want).index(x["frame_id"]))), None)
        if first is not None:
            carried = set(first.get("persistent_state_ids") or []) | set(first.get("ended_state_ids") or [])
            # Boundary objects are documented as structured {id, identity, ...} entries.
            # Earlier tests used only strings; comparing dicts to a set crashed.
            prior_ids = []
            for obj in prior_boundary.get("active_objects", []):
                oid = obj.get("id") if isinstance(obj, dict) else obj
                if not isinstance(oid, str) or not oid:
                    problems.append("BOUNDARY_OBJECT_WITHOUT_STABLE_ID")
                else:
                    prior_ids.append(oid)
            lost = [oid for oid in prior_ids if oid not in carried]
            if lost:
                problems.append(f"BOUNDARY_IDENTITY_NOT_RECONCILED:{lost[:5]}")
    if problems:
        return {"ok": False, "status": "NEEDS_REINSPECTION", "problems": problems, "weak": weak}
    return {"ok": True, "status": "VALIDATED", "problems": [], "weak": weak, "observations": obs,
            "transition_graph": graph, "boundary": boundary, "question_update": response.get("question_update")}
