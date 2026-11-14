"""First-15 deterministic sequence selection across five base films (Addendum 25 §1.2–1.4).

Candidates must carry visual witness rationales authored by an identified observer
(HUMAN, VLM or SYNTHETIC fixture). Numerical motion/scene scores alone never select
a sequence (ADD25-S05). Roles W/C/T are sampling roles, not style categories.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any

from ..util import Blocked, digest, is_vague_statement, now_iso, require_fields

ROLES = ("C", "W", "T")  # fixed selection ORDER per film: C first protects character learning
OPPORTUNITY_AREAS = {
    "character": ("character_shape", "body_face_relation", "whole_body_acting", "hand_prop"),
    "world": ("complete_world", "integrated_object_artwork", "colour_material_finish"),
    "change": ("viewpoint", "state_substitution", "choreographed_coexistence", "spatial_transformation"),
}
ALL_OPPORTUNITIES = tuple(x for v in OPPORTUNITY_AREAS.values() for x in v)
OBSERVERS = ("HUMAN", "VLM", "SYNTHETIC_FIXTURE")
EXCLUDED_CONTENT = ("SPONSOR", "OUTRO", "CREDITS", "INTRO_CARD")

CANDIDATE_REQUIRED = ("film_sha", "candidate_id", "start_frame_index", "end_frame_index_inclusive", "start_pts",
                      "end_pts", "actual_frame_count", "key_witness_frame_ids", "whole_visual_quality_statement",
                      "selection_role_candidates", "observer")


@dataclass
class CandidateSequence:
    film_sha: str
    candidate_id: str
    start_frame_index: int
    end_frame_index_inclusive: int
    start_pts: float
    end_pts: float
    actual_frame_count: int
    key_witness_frame_ids: list
    whole_visual_quality_statement: str
    selection_role_candidates: list
    observer: str
    visible_actors_or_entities: list = field(default_factory=list)
    art_construction_opportunity: list = field(default_factory=list)
    whole_world_opportunity: list = field(default_factory=list)
    view_motion_opportunity: list = field(default_factory=list)
    face_pose_contact_opportunity: list = field(default_factory=list)
    simultaneous_events: list = field(default_factory=list)
    visible_proof_for_each_opportunity: dict = field(default_factory=dict)
    opportunities: list = field(default_factory=list)       # subset of ALL_OPPORTUNITIES
    actor_class: str | None = None                           # e.g. "biped_human", "creature", None
    new_question_contributed: str = ""
    known_limitations: list = field(default_factory=list)
    content_label: str = "MAIN_FILM"
    observer_rank: int = 100                                 # administrative aid; lower = stronger, needs rationale
    event_start_frame: int | None = None                     # true action start if wider than shot
    event_end_frame: int | None = None
    estimated_vision_cost: str = "BLOCKED_FOR_PRICE_VERIFICATION"
    sample_uncertainty: str = ""
    indispensable_reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def validate_candidate(c: dict, index_len: int | None = None) -> list[str]:
    """Return list of rejection reasons (empty = eligible). Implements C1/C7 + S05."""
    reasons = []
    try:
        require_fields(c, CANDIDATE_REQUIRED, "CANDIDATE_INCOMPLETE")
    except Blocked as b:
        return [b.code + ":" + ",".join(b.data.get("missing", []))]
    if c["observer"] not in OBSERVERS:
        reasons.append("UNKNOWN_OBSERVER")
    a, z = c["start_frame_index"], c["end_frame_index_inclusive"]
    if a < 0 or z < a:
        reasons.append("BAD_BOUNDARIES")
    if c["actual_frame_count"] != z - a + 1:
        reasons.append("FRAME_COUNT_MISMATCH")
    if index_len is not None and z >= index_len:
        reasons.append("BOUNDARY_BEYOND_INDEX")
    if not all(a <= f <= z for f in c["key_witness_frame_ids"]):
        reasons.append("WITNESS_OUTSIDE_INTERVAL")
    if is_vague_statement(c["whole_visual_quality_statement"]):
        reasons.append("NO_WHOLE_ARTWORK_EVIDENCE")  # S05 / vague
    if not c.get("visible_proof_for_each_opportunity") and c.get("opportunities"):
        reasons.append("OPPORTUNITY_WITHOUT_VISIBLE_PROOF")
    for o in c.get("opportunities", []):
        if o not in ALL_OPPORTUNITIES:
            reasons.append(f"UNKNOWN_OPPORTUNITY:{o}")
        elif o not in c.get("visible_proof_for_each_opportunity", {}):
            reasons.append(f"OPPORTUNITY_UNPROVEN:{o}")
    if c.get("content_label", "MAIN_FILM") in EXCLUDED_CONTENT and not c.get("indispensable_reason"):
        reasons.append("SPONSOR_OUTRO_EXCLUDED")
    return reasons


def expand_to_event(c: dict) -> dict:
    """ADD25-S04: expand/relink to include true pre-action and settle frames (contiguous; never skip)."""
    c = dict(c)
    es, ee = c.get("event_start_frame"), c.get("event_end_frame")
    changed = []
    if es is not None and es < c["start_frame_index"]:
        changed.append(("start", c["start_frame_index"], es))
        c["start_frame_index"] = es
    if ee is not None and ee > c["end_frame_index_inclusive"]:
        changed.append(("end", c["end_frame_index_inclusive"], ee))
        c["end_frame_index_inclusive"] = ee
    if changed:
        c["actual_frame_count"] = c["end_frame_index_inclusive"] - c["start_frame_index"] + 1
        c["boundary_expansions"] = changed
        c["pts_needs_reresolution"] = True
    return c


def _overlap(a: dict, b: dict) -> float:
    if a["film_sha"] != b["film_sha"]:
        return 0.0
    lo = max(a["start_frame_index"], b["start_frame_index"])
    hi = min(a["end_frame_index_inclusive"], b["end_frame_index_inclusive"])
    if hi < lo:
        return 0.0
    return (hi - lo + 1) / min(a["actual_frame_count"], b["actual_frame_count"])


def _adds_new(c: dict, selected: list[dict]) -> set:
    have = set().union(*[set(s.get("opportunities", [])) for s in selected]) if selected else set()
    return set(c.get("opportunities", [])) - have


def propose_selection(candidates: list[dict], base_film_shas: list[str], *, index_lengths: dict | None = None,
                      per_film: int = 3) -> dict:
    """Deterministic 3x5 assignment. Returns SelectedSequenceManifest or a BLOCKED record."""
    if len(base_film_shas) != 5:
        return {"status": "BLOCKED", "reason": "BASE_FILM_COUNT_NOT_FIVE", "base_film_count": len(base_film_shas),
                "selected": [], "note": "No false five-film report (ADD25-S01)."}
    trace: list[dict] = []
    eligible: dict[str, list[dict]] = {f: [] for f in base_film_shas}
    rejected = []
    for c0 in candidates:
        c = expand_to_event(c0)
        if c["film_sha"] not in eligible:
            rejected.append({"candidate_id": c["candidate_id"], "reasons": ["NOT_A_BASE_FILM"]})
            continue
        why = validate_candidate(c, (index_lengths or {}).get(c["film_sha"]))
        if why:
            rejected.append({"candidate_id": c["candidate_id"], "reasons": why})
        else:
            eligible[c["film_sha"]].append(c)
    # Deduplicate near-identical intervals within a film (ADD25-S02): keep stronger rank.
    for f, lst in eligible.items():
        lst.sort(key=lambda x: (x.get("observer_rank", 100), x["candidate_id"]))
        kept: list[dict] = []
        for c in lst:
            dup = next((k for k in kept if _overlap(c, k) >= 0.6), None)
            if dup:
                rejected.append({"candidate_id": c["candidate_id"], "reasons": [f"DUPLICATE_OF:{dup['candidate_id']}"]})
            else:
                kept.append(c)
        eligible[f] = kept
    selected: list[dict] = []
    substitutions = []
    for f in base_film_shas:
        film_pick: list[dict] = []
        for role in ROLES:
            pool = [c for c in eligible[f] if c not in film_pick]
            fitting = [c for c in pool if role in c["selection_role_candidates"]]
            if role == "C":
                # strongest character first, preferring actor classes not yet selected in other films
                seen_classes = {s.get("actor_class") for s in selected}
                fitting.sort(key=lambda c: (c.get("actor_class") in seen_classes, c.get("observer_rank", 100), c["candidate_id"]))
            else:
                fitting.sort(key=lambda c: (-len(_adds_new(c, selected + film_pick)), c.get("observer_rank", 100), c["candidate_id"]))
            pick = fitting[0] if fitting else None
            sub = None
            if pick is None and pool:
                pool.sort(key=lambda c: (-len(_adds_new(c, selected + film_pick)), c.get("observer_rank", 100), c["candidate_id"]))
                pick = pool[0]
                sub = {"film_sha": f, "role": role, "candidate_id": pick["candidate_id"],
                       "reason": f"ROLE_SUBSTITUTION: no witnessed role-{role} candidate in this film",
                       "missing_coverage": role}
                substitutions.append(sub)
            if pick is None:
                trace.append({"film": f, "role": role, "result": "NO_CANDIDATE"})
                continue
            alternatives = [c["candidate_id"] for c in fitting[1:4]]
            film_pick.append({**pick, "selection_role": role, "role_substitution": sub,
                              "rejected_alternatives": alternatives,
                              "why_alternatives_rejected": "ranked lower by role order / redundancy / observer rank"})
            trace.append({"film": f, "role": role, "picked": pick["candidate_id"], "alternatives": alternatives,
                          "new_opportunities": sorted(_adds_new(pick, selected + film_pick[:-1]))})
        selected.extend(film_pick)
    # Cross-film reconcile: replace a fully redundant pick if an unselected candidate adds a missing opportunity.
    replacements = []
    for i, s in enumerate(list(selected)):
        others = selected[:i] + selected[i + 1:]
        if _adds_new(s, others):
            continue
        alts = [c for c in eligible[s["film_sha"]] if c["candidate_id"] not in {x["candidate_id"] for x in selected}
                and s["selection_role"] in c["selection_role_candidates"] and _adds_new(c, others)]
        if alts:
            alts.sort(key=lambda c: (-len(_adds_new(c, others)), c.get("observer_rank", 100)))
            new = {**alts[0], "selection_role": s["selection_role"], "role_substitution": s.get("role_substitution"),
                   "rejected_alternatives": [s["candidate_id"]], "why_alternatives_rejected": "replaced redundant pick"}
            replacements.append({"removed": s["candidate_id"], "added": new["candidate_id"]})
            selected[i] = new
    ledger = coverage_ledger(selected)
    complete = len(selected) == 5 * per_film
    status = "PROPOSED_AWAITING_USER_REVIEW" if complete else "NEEDS_SELECTION_REVIEW"
    for k, s in enumerate(selected):
        s["question_cluster_id"] = f"QC_{k:02d}_{s['selection_role']}"
    manifest = {
        "record_type": "SelectedSequenceManifest", "status": status, "created_at": now_iso(),
        "selected": selected, "selected_count": len(selected), "target": 5 * per_film,
        "substitutions": substitutions, "replacements": replacements, "rejected": rejected,
        "selection_trace": trace, "coverage_ledger": ledger,
        "approval": {"user_approved_selection_and_budget": False},
        "observers": sorted({s["observer"] for s in selected}),
    }
    manifest["manifest_sha"] = digest({k: v for k, v in manifest.items() if k != "created_at"})
    return manifest


def coverage_ledger(selected: list[dict]) -> dict:
    """§1.4: which observed opportunities the first 15 do and do NOT show."""
    out: dict[str, Any] = {}
    for area, opps in OPPORTUNITY_AREAS.items():
        out[area] = {}
        for o in opps:
            refs = [s["candidate_id"] for s in selected if o in s.get("opportunities", [])]
            films = sorted({s["film_sha"][:12] for s in selected if o in s.get("opportunities", [])})
            out[area][o] = {"sequences": refs or "NOT_SEEN_IN_INITIAL_SET", "films": films}
    missing = [o for o in ALL_OPPORTUNITIES if not any(o in s.get("opportunities", []) for s in selected)]
    out["largest_unknowns"] = missing
    out["note"] = "Proves intentional selection only; does not declare any style skill learned."
    return out


def navigation_candidates_from_survey(film_sha: str, survey: dict, *, min_frames: int = 120) -> list[dict]:
    """Real-film offline helper: shots long enough to be candidate windows, WITHOUT visual rationale.

    These are deliberately ineligible for selection until a HUMAN or authorized VLM supplies
    whole-artwork witness statements (ADD25-S05). They make the pending work concrete.
    """
    out = []
    for s in survey["shots"]:
        if s["frame_count"] >= min_frames:
            out.append({"film_sha": film_sha, "candidate_id": f"nav_{film_sha[:8]}_{s['shot_id']}",
                        "start_frame_index": s["start_frame_index"], "end_frame_index_inclusive": s["end_frame_index_inclusive"],
                        "start_pts": s["start_pts_time"], "end_pts": s["end_pts_time"], "actual_frame_count": s["frame_count"],
                        "key_witness_frame_ids": [], "whole_visual_quality_statement": "",
                        "selection_role_candidates": [], "observer": "NONE_SURVEY_ONLY",
                        "status": "AWAITING_VISUAL_RATIONALE"})
    return out
