"""Witness bundles and cross-frame event graphs (spec 14 §3, ADD25 §2.5, ADD26 §4.1/§4.3, ADD26-F03/F04).

Every witness names its observer and evidence kind. SYNTHETIC_FIXTURE taint propagates:
any record built from synthetic evidence is synthetic and can never be reported as a
Kurzgesagt observation (ADD25-A02).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

from ..util import Blocked, digest, is_sha256, is_vague_statement

EVIDENCE_KINDS = ("FULL_FRAME", "NATIVE_CROP", "TEMPORAL_COMPARE", "CROSS_SEQUENCE", "ORIGINAL_OUTPUT", "SYNTHETIC_FIXTURE", "AUDIO_SIGNAL")
OBSERVERS = ("VLM", "HUMAN", "SYNTHETIC_FIXTURE", "ORIGINAL_OUTPUT_REVIEW", "LOCAL_SIGNAL_ANALYSIS")


@dataclass
class Witness:
    witness_id: str
    film_sha256: str
    sequence_id: str
    frame_start: int
    frame_end: int
    evidence_kind: str
    observer: str
    visible_relation: str
    image_sha256: str | None = None
    region: dict | None = None
    parent_full_frame_witness: str | None = None
    temporal_neighbor_witnesses: list = field(default_factory=list)
    subject_class: str | None = None          # e.g. "biped", "machine", "landscape"; for cross-case contrast
    scene_specific_facts: list = field(default_factory=list)
    observation_ids: list = field(default_factory=list)
    limits: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def synthetic(self) -> bool:
        return self.observer == "SYNTHETIC_FIXTURE" or self.evidence_kind == "SYNTHETIC_FIXTURE" or \
            self.film_sha256.startswith("SYNTHETIC")


@dataclass
class WitnessBundle:
    bundle_id: str
    question_id: str | None
    visible_effect: str
    witnesses: list
    contrasting_witness_ids: list = field(default_factory=list)
    unobservables: list = field(default_factory=list)
    competing_explanations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def ws(self) -> list[Witness]:
        return [w if isinstance(w, Witness) else Witness(**w) for w in self.witnesses]

    @property
    def synthetic(self) -> bool:
        return any(w.synthetic for w in self.ws())

    @property
    def films(self) -> set:
        return {w.film_sha256 for w in self.ws()}

    @property
    def subject_classes(self) -> set:
        return {w.subject_class for w in self.ws() if w.subject_class}


def validate_bundle(b: WitnessBundle, *, purpose: str = "style_decision") -> dict:
    """Return {ok, problems, evidence_scope}. Purpose 'style_decision' needs whole-context evidence."""
    problems = []
    ws = b.ws()
    ids = {w.witness_id: w for w in ws}
    if not ws:
        problems.append("NO_WITNESS")
    for w in ws:
        if w.evidence_kind not in EVIDENCE_KINDS:
            problems.append(f"BAD_EVIDENCE_KIND:{w.witness_id}")
        if w.observer not in OBSERVERS:
            problems.append(f"UNKNOWN_OBSERVER:{w.witness_id}")
        if not w.synthetic and not is_sha256(w.film_sha256):
            problems.append(f"UNANCHORED_WITNESS:{w.witness_id}")
        if w.frame_end < w.frame_start:
            problems.append(f"BAD_FRAME_SPAN:{w.witness_id}")
        if is_vague_statement(w.visible_relation):
            problems.append(f"VAGUE_VISIBLE_RELATION:{w.witness_id}")
        if w.observer == "LOCAL_SIGNAL_ANALYSIS" and w.evidence_kind != "AUDIO_SIGNAL":
            problems.append(f"LOCAL_SIGNAL_OBSERVER_ON_VISUAL_EVIDENCE:{w.witness_id}")
        if w.evidence_kind == "AUDIO_SIGNAL":
            if w.observer != "LOCAL_SIGNAL_ANALYSIS":
                problems.append(f"AUDIO_SIGNAL_WRONG_OBSERVER:{w.witness_id}")
            parent = ids.get(w.parent_full_frame_witness or "")
            # an audio onset is evidence ONLY together with the full frame it coincides with: same film, same frame span (±1)
            if not parent or parent.evidence_kind not in ("FULL_FRAME", "SYNTHETIC_FIXTURE"):
                problems.append(f"AUDIO_WITHOUT_FULL_FRAME_CONTEXT:{w.witness_id}")
            elif parent.film_sha256 != w.film_sha256 or abs(parent.frame_start - w.frame_start) > 1:
                problems.append(f"AUDIO_PARENT_MISALIGNED:{w.witness_id}")
        if w.evidence_kind == "NATIVE_CROP":
            parent = ids.get(w.parent_full_frame_witness or "")
            if not parent or parent.evidence_kind not in ("FULL_FRAME", "SYNTHETIC_FIXTURE"):
                problems.append(f"CROP_WITHOUT_FULL_FRAME_CONTEXT:{w.witness_id}")
            if purpose == "style_decision" and not w.temporal_neighbor_witnesses and \
                    not any(x.evidence_kind == "TEMPORAL_COMPARE" for x in ws):
                problems.append(f"CROP_WITHOUT_TEMPORAL_CONTEXT:{w.witness_id}")
    if purpose == "style_decision" and not any(w.evidence_kind in ("FULL_FRAME", "SYNTHETIC_FIXTURE") for w in ws):
        problems.append("NO_WHOLE_FRAME_WITNESS")
    scope = "SINGLE_SOURCE_LEAD"
    if len(b.films) >= 2 and len(b.subject_classes) >= 2 and b.contrasting_witness_ids:
        scope = "CROSS_FILM_CROSS_SUBJECT"
    elif len(b.films) >= 2:
        scope = "CROSS_FILM_SAME_SUBJECT_CLASS"
    return {"ok": not problems, "problems": problems, "evidence_scope": scope, "synthetic": b.synthetic,
            "bundle_sha": digest(b.to_dict())}


def build_event_graph(observations: list[dict]) -> dict:
    """CrossFrameEventGraph: timeline of changes, persistent states and links from per-frame records."""
    obs = sorted(observations, key=lambda o: int(str(o["frame_id"]).split(":")[1]))
    events, holds = [], []
    for prev, cur in zip(obs, obs[1:]):
        ch = cur.get("changed_since_prior_frame") or []
        if ch:
            events.append({"from": prev["frame_id"], "to": cur["frame_id"], "changes": ch,
                           "links": cur.get("simultaneous_event_links", []),
                           "camera_vs_drawing": cur.get("camera_vs_actor_vs_drawing_state", "UNKNOWN")})
        else:
            holds.append({"frame": cur["frame_id"], "reason": cur.get("no_significant_change_reason")})
    ambiguous = [e for e in events if any(isinstance(c, dict) and c.get("kind") in ("INFERRED_CAMERA", "UNKNOWN")
                                          for c in e["changes"]) and "redraw" in str(e).lower()]
    return {"frames": [o["frame_id"] for o in obs], "change_events": events, "holds": holds,
            "camera_vs_redraw_ambiguities": ambiguous, "graph_sha": digest(events)}


def reverse_timeline_check(graph: dict, expected_frames: list[str]) -> dict:
    """Walk end→start: every expected frame present; no silent jumps (ADD25 §2.5 step 6)."""
    present = set(graph["frames"])
    missing = [f for f in reversed(expected_frames) if f not in present]
    return {"ok": not missing, "missing_frames": missing[:50], "events_checked": len(graph["change_events"])}


def camera_attribution_guard(event: dict) -> None:
    """ADD26-F04: movement may not be attributed to camera when redraw evidence exists, without follow-up."""
    kinds = {c.get("kind") for c in event.get("changes", []) if isinstance(c, dict)}
    if "INFERRED_CAMERA" in kinds and "INFERRED_NEW_DRAWING" in kinds:
        raise Blocked("CAMERA_VS_REDRAW_UNRESOLVED", "requires native/temporal follow-up before a motion skill")
    if event.get("asserted_cause") == "CAMERA_ONLY" and "INFERRED_NEW_DRAWING" in kinds:
        raise Blocked("CAMERA_ATTRIBUTION_CONTRADICTS_REDRAW")
