"""Sixth special source: locate the volcano-start → brand-Earth-logo-entrance interval (Addendum 26 §2).

Boundaries come only from actual decoded frames. Without a frame classifier (offline,
no authorized VLM) the locator returns candidate cut boundaries plus a local witness
packet for HUMAN review; it never guesses timestamps and never auto-locks when more than
one plausible opening or logo event exists (ADD26-D04). Locking requires an explicit
human confirmation referencing the witness packet.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Optional

from ..util import Blocked, digest, now_iso

SOURCE_SPECIFIC_EXCLUSIONS = (
    "brand earth logo", "earth logo", "studio logo", "volcano composition", "exact volcanic layout",
    "logo reveal timing as a universal rule", "always put a volcano before a logo",
)
STATUSES = ("SIXTH_SOURCE_NOT_AVAILABLE", "CANDIDATE_BOUNDARIES_AWAITING_HUMAN_REVIEW",
            "PROPOSED_AWAITING_HUMAN_CONFIRMATION", "AMBIGUOUS_REQUIRES_REVIEW", "LOCKED", "SOURCE_MISMATCH")

# classifier(frame_record) -> {"volcano": float 0..1, "earth_logo": float 0..1}
FrameClassifier = Callable[[dict], dict]


@dataclass
class SixthIntroLocatorResult:
    status: str
    clip_sha256: str | None
    clip_file: str | None
    search_window_frames: list | None
    candidate_starts: list = field(default_factory=list)
    candidate_logo_entrances: list = field(default_factory=list)
    proposed_interval: dict | None = None
    context_frames: dict | None = None
    witness_packet: list = field(default_factory=list)
    classifier_kind: str = "NONE"
    boundary_criteria: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


BOUNDARY_CRITERIA = {
    "start": "first presented frame at which the volcano scene is the dominant whole-frame content and remains so "
             "(a preceding dissolve frame where the prior scene still dominates is NOT the start)",
    "end": "first presented frame at which the brand Earth logo has visibly entered (inclusive); later logo hold "
           "frames are context, not the boundary",
    "context": "keep adjacent frames before start and after end to distinguish dissolves and holds",
    "evidence": "actual decoded frames only; no guessed durations, no rounded timestamps",
}


def _runs(flags: list[bool]) -> list[tuple[int, int]]:
    out, s = [], None
    for i, f in enumerate(flags):
        if f and s is None:
            s = i
        if not f and s is not None:
            out.append((s, i - 1))
            s = None
    if s is not None:
        out.append((s, len(flags) - 1))
    return out


def locate_sixth_intro(clip_path: Optional[str | Path], clip_sha: Optional[str], index: list[dict] | None, *,
                       cut_frames: list[int] | None = None, classifier: FrameClassifier | None = None,
                       classifier_kind: str = "NONE", search_window_s: tuple[float, float] = (0.0, 240.0),
                       context: int = 30, min_run: int = 6, threshold: float = 0.6) -> SixthIntroLocatorResult:
    if clip_path is None or not Path(clip_path).exists() or not index:
        return SixthIntroLocatorResult("SIXTH_SOURCE_NOT_AVAILABLE", None, None, None, boundary_criteria=BOUNDARY_CRITERIA,
                                       notes=["No sixth clip present: no filename, timestamps or event fabricated."],
                                       created_at=now_iso())
    lo_t, hi_t = search_window_s
    win = [r for r in index if lo_t <= r["pts_time"] <= hi_t]
    if not win:
        raise Blocked("EMPTY_SEARCH_WINDOW")
    w0, w1 = win[0]["presentation_index"], win[-1]["presentation_index"]
    res = SixthIntroLocatorResult("CANDIDATE_BOUNDARIES_AWAITING_HUMAN_REVIEW", clip_sha, Path(clip_path).name,
                                  [w0, w1], classifier_kind=classifier_kind, boundary_criteria=BOUNDARY_CRITERIA,
                                  created_at=now_iso())
    if classifier is None:
        cands = [c for c in (cut_frames or []) if w0 <= c <= w1]
        res.candidate_starts = [{"frame_index": c, "pts": index[c]["pts"], "pts_time": index[c]["pts_time"],
                                 "basis": "LOCAL_SCENE_CUT_ONLY"} for c in cands]
        res.candidate_logo_entrances = list(res.candidate_starts)
        res.witness_packet = [{"frame_index": max(0, c + d), "role": f"cut{c}{d:+d}"} for c in cands for d in (-2, -1, 0, 1, 2)
                              if 0 <= c + d < len(index)]
        res.notes.append("No authorized frame classifier/VLM: which cut is the volcano start and which is the logo "
                         "entrance must be decided by a human from the local witness thumbnails.")
        return res
    scores = [classifier(r) for r in win]
    volc = _runs([s.get("volcano", 0) >= threshold for s in scores])
    logo = _runs([s.get("earth_logo", 0) >= threshold for s in scores])
    volc = [(a + w0, b + w0) for a, b in volc if b - a + 1 >= min_run]
    logo = [(a + w0, b + w0) for a, b in logo if b - a + 1 >= min_run]
    res.candidate_starts = [{"frame_index": a, "pts": index[a]["pts"], "pts_time": index[a]["pts_time"], "run_end": b,
                             "basis": classifier_kind} for a, b in volc]
    res.candidate_logo_entrances = [{"frame_index": a, "pts": index[a]["pts"], "pts_time": index[a]["pts_time"], "run_end": b,
                                     "basis": classifier_kind} for a, b in logo]
    pairs = [(v, l) for v in volc for l in logo if l[0] > v[0]]
    if len(volc) == 1 and len(logo) == 1 and pairs:
        (vs, _), (ls, _) = pairs[0]
        res.status = "PROPOSED_AWAITING_HUMAN_CONFIRMATION"
        res.proposed_interval = {"start_frame_index": vs, "end_frame_index_inclusive": ls,
                                 "start_pts": index[vs]["pts"], "end_pts": index[ls]["pts"],
                                 "start_pts_time": index[vs]["pts_time"], "end_pts_time": index[ls]["pts_time"],
                                 "frame_count": ls - vs + 1}
        res.context_frames = {"before": [max(0, vs - context), vs - 1], "after": [ls + 1, min(len(index) - 1, ls + context)]}
        res.witness_packet = [{"frame_index": i, "role": r} for i, r in
                              ((vs - 1, "pre_start"), (vs, "start"), (vs + 1, "post_start"),
                               (ls - 1, "pre_logo"), (ls, "logo_entrance"), (ls + 1, "logo_hold")) if 0 <= i < len(index)]
    elif not volc or not logo:
        res.status = "CANDIDATE_BOUNDARIES_AWAITING_HUMAN_REVIEW"
        res.notes.append("Classifier found no complete volcano→logo pair; human review required.")
    else:
        res.status = "AMBIGUOUS_REQUIRES_REVIEW"
        res.notes.append(f"{len(volc)} volcano runs and {len(logo)} logo runs: no arbitrary automatic lock.")
        res.witness_packet = [{"frame_index": c["frame_index"], "role": "candidate_start"} for c in res.candidate_starts] + \
                             [{"frame_index": c["frame_index"], "role": "candidate_logo"} for c in res.candidate_logo_entrances]
    return res


def lock_sixth_interval(result: dict, *, start_frame_index: int, end_frame_index_inclusive: int, confirmed_by: str,
                        index: list[dict], witness_packet_sha: str, context: int = 30) -> dict:
    """Human confirmation → immutable SpecialIntroSelection. Rejects unsupported boundaries."""
    if result["status"] == "SIXTH_SOURCE_NOT_AVAILABLE":
        raise Blocked("SIXTH_SOURCE_NOT_AVAILABLE")
    if not confirmed_by or confirmed_by.upper() in ("AUTO", "AGENT", "MODEL"):
        raise Blocked("HUMAN_CONFIRMATION_REQUIRED", "lock needs a named human reviewer")
    if witness_packet_sha != digest(result.get("witness_packet", [])):
        raise Blocked("WITNESS_PACKET_MISMATCH", "confirmation does not reference the presented witness packet")
    n = len(index)
    if not (0 <= start_frame_index < end_frame_index_inclusive < n):
        raise Blocked("BAD_INTERVAL")
    a, b = start_frame_index, end_frame_index_inclusive
    return {
        "record_type": "SpecialIntroSelection", "status": "LOCKED", "clip_sha256": result["clip_sha256"],
        "clip_file": result["clip_file"], "start_frame_index": a, "end_frame_index_inclusive": b,
        "start_pts": index[a]["pts"], "end_pts": index[b]["pts"], "start_pts_time": index[a]["pts_time"],
        "end_pts_time": index[b]["pts_time"], "frame_count": b - a + 1,
        "context_before": [max(0, a - context), a - 1], "context_after": [b + 1, min(n - 1, b + context)],
        "confirmed_by": confirmed_by, "witness_packet_sha": witness_packet_sha, "locked_at": now_iso(),
        "separate_from_first15": True, "coverage_status_key": "special_sixth_clip_coverage",
        "forbidden_source_specific_copies": list(SOURCE_SPECIFIC_EXCLUSIONS),
        "study_focus": "artwork→perspective→temporal transformation→attention (transferable transition decisions only)",
    }


def is_source_specific_branding(text: str) -> bool:
    t = (text or "").lower()
    return any(x in t for x in SOURCE_SPECIFIC_EXCLUSIONS) or ("logo" in t and ("brand" in t or "earth" in t))
