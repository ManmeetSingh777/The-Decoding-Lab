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
    "VISION_OUTPUT_VERIFIED", "RESPONSE_IDENTITY_BOUND", "ARTISTIC_CLAIM_UNVERIFIED", "NATIVE_DETAIL_REVIEWED", "ARTISTICALLY_EXPLAINED",
    "SOURCE_ARTISTICALLY_REVIEWED", "UNKNOWN_OR_FAILED",
)
PACKET_STATES = ("PLANNED", "INPUTS_READY", "REQUEST_IN_FLIGHT", "RESULT_RECEIVED", "VALIDATED",
                 "SEMANTIC_COMMITTED", "QUARANTINED", "RETRY_WAIT", "BLOCKED_CONSENT", "UNKNOWN_BILLING",
                 "NEEDS_REINSPECTION", "SUPERSEDED_BY_SPLIT", "INSPECTION_INSUFFICIENT")

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
        # R3-C08: pts_time is a REQUIRED identity field — null / missing / non-numeric never passes; it must equal the submitted
        # native-timebase manifest exactly (to 1 µs)
        pt = o.get("pts_time")
        if isinstance(pt, bool) or not isinstance(pt, (int, float)):
            problems.append(f"PTS_MISSING_OR_NON_NUMERIC:{o['frame_id']}")
        elif abs(float(pt) - float(m["pts_time"])) > 1e-6:
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
        return {"ok": False, "status": "NEEDS_REINSPECTION", "problems": problems, "weak": weak,
                "format_valid": not any(p.startswith(("FIELDS_MISSING", "NO_PACKET", "NO_BOUNDARY", "MISSING_FRAME", "DUPLICATE")) for p in problems),
                "identity_valid": not any(p.startswith(("PTS_", "SOURCE_SHA", "IMAGE_HASH")) for p in problems)}
    insp = assess_inspection(obs, want, graph, boundary)
    return {"ok": True, "status": "VALIDATED" if insp["adequate"] else "INSPECTION_INSUFFICIENT", "problems": [], "weak": weak,
            "observations": obs, "transition_graph": graph, "boundary": boundary, "question_update": response.get("question_update"),
            "format_valid": True, "identity_valid": True, "inspection": insp}


# ------------------------------------------------------------------------------------------------------------------- R3-C08
INSPECTION_STATUSES = ("FORMAT_VALID", "EVIDENCE_IDENTITY_VALID", "ARTISTIC_INSPECTION_ADEQUATE", "INSPECTION_INSUFFICIENT",
                       "SOURCE_REVIEWED", "SKILL_CANDIDATE", "TRANSFER_QUALIFIED")
# artistic dimensions every frame must ADDRESS: substantively, as an explicit source-grounded N/A, or as an explicit targeted unknown
ADDRESSED_DIMENSIONS = ("character_face_limb_contact_state", "visible_layer_depth_attention_state", "camera_vs_actor_vs_drawing_state",
                        "material_finish_or_colour_change", "simultaneous_event_links")
STATE_CHANGE_DIMS = {"ART_STATE_TRANSFORMATION", "CHARACTER_FACE_ACTING", "DEPTH_VIEWPOINT", "MOTION_ACTING", "CHARACTER_BODY_HAND_CONTACT"}
_PLACEHOLDER = {"", "unknown", "none", "n/a", "na", "null", "unknown (mock)", "simulated", "-"}


def _words(s) -> int:
    return len(str(s).split())


def _addressing(v) -> str:
    """SUBSTANTIVE | NOT_APPLICABLE | EXPLICIT_UNKNOWN | UNADDRESSED (a bare 'UNKNOWN', null, [] or {} addresses nothing)."""
    if isinstance(v, dict):
        if "not_applicable" in v:
            r = v["not_applicable"]
            return "NOT_APPLICABLE" if isinstance(r, str) and _words(r) >= 4 and not is_vague_statement(r) else "UNADDRESSED"
        if "unknown" in v:
            return "EXPLICIT_UNKNOWN" if _words(v.get("unknown", "")) >= 3 and str(v.get("next_witness", "")).strip() else "UNADDRESSED"
        return "SUBSTANTIVE" if any(_addressing(x) == "SUBSTANTIVE" for x in v.values()) else "UNADDRESSED"
    if isinstance(v, list):
        return "SUBSTANTIVE" if any(_addressing(x) == "SUBSTANTIVE" for x in v) else "UNADDRESSED"
    if isinstance(v, str):
        s = v.strip()
        return "UNADDRESSED" if s.lower() in _PLACEHOLDER or _words(s) < 4 or is_vague_statement(s) else "SUBSTANTIVE"
    return "UNADDRESSED"


def assess_inspection(obs: list, want: dict, graph, boundary) -> dict:
    """Per-frame ARTISTIC_INSPECTION_ADEQUATE vs INSPECTION_INSUFFICIENT with NAMED gaps (frame id + exact pts). Field presence is
    not depth: every visible entity needs relations, every dimension must be addressed, every change attributed and described for
    the entity that changed, coinciding changes linked, audio events at the frame linked, and persistence justified."""
    per: dict[str, dict] = {}
    any_change = False
    for o in obs:
        if not isinstance(o, dict) or o.get("frame_id") not in want:
            continue
        fid, m = o["frame_id"], want[o["frame_id"]]
        gaps: list[dict] = []
        unknowns: list[dict] = []
        g = lambda kind, **kw: gaps.append({"frame_id": fid, "pts_time": m["pts_time"], "gap": kind, **kw})
        ents = [e if isinstance(e, str) else str((e or {}).get("id")) for e in o.get("actually_visible_actor_and_object_ids") or []]
        kinds = o.get("entity_kinds") or {}
        if not ents and _addressing({"not_applicable": o.get("no_visible_entities_reason", "")}) != "NOT_APPLICABLE":
            g("ENTITIES_NOT_ENUMERATED")
        rels = [r for r in o.get("visible_design_relations") or [] if isinstance(r, dict) and isinstance(r.get("relation"), str)
                and not is_vague_statement(r["relation"]) and r.get("dimensions")]
        if len(rels) < max(1, len(ents)):
            g("DESIGN_RELATIONS_TOO_FEW", have=len(rels), need=max(1, len(ents)))
        named = {e for r in rels for e in r.get("entity_ids") or []}
        for e in ents:
            if rels and any(r.get("entity_ids") for r in rels) and e not in named:
                g("ENTITY_WITHOUT_RELATION", entity_id=e)
        for f in ADDRESSED_DIMENSIONS:
            if f == "character_face_limb_contact_state" and kinds and not any(k == "character" for k in kinds.values()):
                continue                                         # no character visible: this dimension is irrelevant by enumeration
            a = _addressing(o.get(f))
            if a == "UNADDRESSED":
                g("DIMENSION_NOT_ADDRESSED", dimension=f)
            elif a == "EXPLICIT_UNKNOWN":
                unknowns.append({"frame_id": fid, "pts_time": m["pts_time"], "dimension": f, "unknown": o[f].get("unknown"),
                                 "next_witness": o[f].get("next_witness")})
        changes = [c for c in o.get("changed_since_prior_frame") or [] if isinstance(c, dict)]
        if changes:
            any_change = True
            if _addressing(o.get("camera_vs_actor_vs_drawing_state")) not in ("SUBSTANTIVE", "EXPLICIT_UNKNOWN"):
                g("CHANGE_UNATTRIBUTED")
            changed_ents = sorted({e for c in changes for e in c.get("entity_ids") or []})
            for c in changes:
                if _words(c.get("what", "")) < 4 or is_vague_statement(str(c.get("what", ""))) or not c.get("entity_ids"):
                    g("CHANGE_UNDERDESCRIBED", change=str(c.get("what", ""))[:80])
            for e in changed_ents:
                if kinds.get(e, "character") == "character" and not any(e in (r.get("entity_ids") or []) and set(r["dimensions"]) & STATE_CHANGE_DIMS
                                                                       for r in rels):
                    g("STATE_CHANGE_WITHOUT_RELATION", entity_id=e)
            if len(changed_ents) > 1 and _addressing(o.get("simultaneous_event_links")) != "SUBSTANTIVE":
                g("SIMULTANEOUS_EVENTS_UNLINKED", entity_ids=changed_ents)
        else:
            r = o.get("no_significant_change_reason")
            if not isinstance(r, str) or _words(r) < 4 or is_vague_statement(r):
                g("PERSISTENCE_UNJUSTIFIED")
        if m.get("audio_events") and _addressing(o.get("audiovisual_links")) != "SUBSTANTIVE":
            g("AV_LINK_MISSING", audio_events=m["audio_events"])
        per[fid] = {"status": "ARTISTIC_INSPECTION_ADEQUATE" if not gaps else "INSPECTION_INSUFFICIENT", "gaps": gaps,
                    "open_unknowns": unknowns, "pts_time": m["pts_time"]}
    packet_gaps = []
    if any_change and isinstance(graph, dict) and not graph.get("edges"):
        packet_gaps.append({"gap": "TRANSITION_GRAPH_EMPTY"})
    if any(o.get("actually_visible_actor_and_object_ids") for o in obs if isinstance(o, dict)) and \
            not (isinstance(boundary, dict) and boundary.get("active_objects")):
        packet_gaps.append({"gap": "BOUNDARY_STATE_EMPTY"})
    adequate = bool(per) and all(v["status"] == "ARTISTIC_INSPECTION_ADEQUATE" for v in per.values()) and not packet_gaps
    return {"adequate": adequate, "per_frame": per, "packet_gaps": packet_gaps,
            "open_unknowns": [u for v in per.values() for u in v["open_unknowns"]]}


def audit_phenomenon_coverage(observations: list[dict], expected: list[dict]) -> list[dict]:
    """INDEPENDENT auditor check (R3-C08): every phenomenon enumerated by a party that did not write the observations (local signal
    detectors, the P5 adversarial sweep, a human) must be covered inside its exact frame interval by the right typed evidence.
    Returns one NAMED gap per uncovered phenomenon (with its interval), never a blanket pass."""
    by_idx: dict[int, dict] = {}
    for o in observations:
        try:
            by_idx[int(str(o["frame_id"]).split(":")[1])] = o
        except (KeyError, ValueError, IndexError):
            continue

    def covered(ph, o) -> bool:
        ents = set(ph.get("entity_ids") or [])
        rels = [r for r in o.get("visible_design_relations") or [] if isinstance(r, dict)]
        rel_dims = {d for r in rels if not ents or ents & set(r.get("entity_ids") or ents) for d in r.get("dimensions") or []}
        ch = [c for c in o.get("changed_since_prior_frame") or [] if isinstance(c, dict)]
        k = ph["kind"]
        if k == "TEMPORAL_OVERLAP":
            links = o.get("simultaneous_event_links") or []
            return _addressing(links) == "SUBSTANTIVE" and (not ents or ents <= {e for l in links if isinstance(l, dict)
                                                                                for e in l.get("entity_ids") or []})
        if k == "HAND_CONTACT":
            return "CHARACTER_BODY_HAND_CONTACT" in rel_dims and _addressing(o.get("character_face_limb_contact_state")) == "SUBSTANTIVE"
        if k == "ALTERNATE_STATE":
            return any(c.get("kind") == "INFERRED_NEW_DRAWING" and (not ents or ents & set(c.get("entity_ids") or [])) for c in ch)
        if k == "CAMERA_ATTRIBUTION":
            return _addressing(o.get("camera_vs_actor_vs_drawing_state")) == "SUBSTANTIVE"
        if k == "LIGHTING_RELATION":
            return "MATERIAL_LIGHT_FINISH" in rel_dims
        if k == "SCENE_TRANSITION":
            return any(c.get("kind") in ("OBSERVED_DIFF", "INFERRED_CAMERA", "INFERRED_NEW_DRAWING") and "transition" in str(c.get("what", "")).lower()
                       for c in ch) or "TRANSITION" in " ".join(rel_dims)
        if k == "AUDIO_EVENT":
            return _addressing(o.get("audiovisual_links")) == "SUBSTANTIVE"
        if k == "VISUAL_CHANGE":
            return bool(ch) and _addressing(o.get("camera_vs_actor_vs_drawing_state")) in ("SUBSTANTIVE", "EXPLICIT_UNKNOWN")
        return False
    gaps = []
    for ph in expected:
        a, b = int(ph["frames"][0]), int(ph["frames"][1])
        frames = [by_idx[i] for i in range(a, b + 1) if i in by_idx]
        if not frames:
            gaps.append({**ph, "gap": "PHENOMENON_FRAMES_NOT_INSPECTED", "interval": [a, b]})
        elif not any(covered(ph, o) for o in frames):
            gaps.append({**ph, "gap": f"PHENOMENON_NOT_EXPLAINED:{ph['kind']}", "interval": [a, b],
                         "next": f"native reinspection of frames {a}..{b} for {ph['kind']}"})
    return gaps
