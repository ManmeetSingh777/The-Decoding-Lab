"""Multi-gap register, qualitative pairwise ranking and connected cluster selection (01 §2, A08/A09, B12, C06, C30).

No numeric beauty scores: each criterion is a qualitative level with a written reason,
and the ranking records WHY each higher gap beats the next one.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

from ..util import Blocked, is_vague_statement, require_fields

LEVELS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
CRITERIA = ("salience", "breadth", "upstream_position", "method_likelihood", "leverage_per_cost", "interaction")
IMPLEMENTATION_LOCI = ("source_extraction", "diagnosis", "skill_input", "model_provider", "layer_separation",
                       "animation_code", "integration", "evaluation", "unsupported_capability")
FIRST_ITERATION_REQUIRED = ("character", "world", "viewpoint_or_motion")


@dataclass
class GapCandidate:
    gap_id: str
    run_id: str
    visual_symptom: str
    affected_original_outputs: list
    source_witness_ids: list
    scope_and_salience: str
    candidate_causes: list            # [{cause, discriminating_check}]
    expected_visual_signature: str
    implementation_locus: str
    criteria: dict                    # criterion -> {"level": HIGH|MEDIUM|LOW, "reason": str}
    area: str                         # character | world | viewpoint_or_motion | colour_material | other
    depends_on: list = field(default_factory=list)
    status: str = "OPEN"
    priority_reasoning: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def validate_gap(g: dict) -> list[str]:
    problems = []
    try:
        require_fields(g, ("gap_id", "visual_symptom", "source_witness_ids", "candidate_causes",
                           "expected_visual_signature", "implementation_locus", "criteria"), "GAP_INCOMPLETE")
    except Blocked as b:
        return [b.code]
    if is_vague_statement(g["visual_symptom"]):
        problems.append("GENERIC_SYMPTOM")  # e.g. 'needs polish'
    if len(g["source_witness_ids"]) < 2:
        problems.append("CONDITIONAL_EVIDENCE_LIMITED")  # recorded, not fatal
    for c in g["candidate_causes"]:
        if not c.get("discriminating_check"):
            problems.append("CAUSE_WITHOUT_DISCRIMINATING_CHECK")
    if g["implementation_locus"] not in IMPLEMENTATION_LOCI:
        problems.append("BAD_LOCUS")
    for k in CRITERIA:
        v = g["criteria"].get(k)
        if not v or v.get("level") not in LEVELS or not v.get("reason"):
            problems.append(f"CRITERION_UNREASONED:{k}")
    return problems


def _key(g: dict) -> tuple:
    c = g["criteria"]
    return tuple(-LEVELS[c[k]["level"]] for k in CRITERIA)


def rank_gaps(gaps: list[dict]) -> dict:
    fatal = {g["gap_id"]: validate_gap(g) for g in gaps}
    usable = [g for g in gaps if not any(p in ("GAP_INCOMPLETE", "GENERIC_SYMPTOM", "BAD_LOCUS") or p.startswith("CRITERION_")
                                         for p in fatal[g["gap_id"]])]
    if len(usable) < 2:
        return {"status": "INSUFFICIENT_GAPS", "detail": "several distinct evidenced gaps required (A08)",
                "rejected": {k: v for k, v in fatal.items() if v}}
    ordered = sorted(usable, key=lambda g: (_key(g), g["gap_id"]))
    explanations = []
    for hi, lo in zip(ordered, ordered[1:]):
        decisive = next((k for k in CRITERIA if LEVELS[hi["criteria"][k]["level"]] != LEVELS[lo["criteria"][k]["level"]]), None)
        if decisive:
            explanations.append({"higher": hi["gap_id"], "lower": lo["gap_id"], "decisive_criterion": decisive,
                                 "because": f"{hi['criteria'][decisive]['reason']} vs {lo['criteria'][decisive]['reason']}"})
        else:
            explanations.append({"higher": hi["gap_id"], "lower": lo["gap_id"], "decisive_criterion": None,
                                 "because": "tie on all criteria; ordered by id — user may override with a recorded reason"})
    return {"status": "RANKED", "ranked_ids": [g["gap_id"] for g in ordered], "pairwise": explanations,
            "warnings": {k: v for k, v in fatal.items() if v}}


def select_cluster(gaps: list[dict], ranked_ids: list[str], *, first_iteration: bool, max_size: int = 5,
                   user_override: dict | None = None) -> dict:
    """Connected 2–5 gap cluster seeded at the top gap; unrelated high gaps stay queued (A09)."""
    by = {g["gap_id"]: g for g in gaps}
    order = list(ranked_ids)
    if user_override:
        if not user_override.get("reason"):
            raise Blocked("OVERRIDE_REASON_REQUIRED")
        order = [user_override["gap_id"]] + [x for x in order if x != user_override["gap_id"]]
    adj: dict[str, set] = {gid: set() for gid in by}
    for g in gaps:
        for d in g.get("depends_on", []):
            if d in adj:
                adj[g["gap_id"]].add(d)
                adj[d].add(g["gap_id"])
    seed = order[0]
    cluster = [seed]
    frontier = [seed]
    while frontier and len(cluster) < max_size:
        cur = frontier.pop(0)
        for n in sorted(adj[cur], key=lambda x: order.index(x) if x in order else 999):
            if n not in cluster and len(cluster) < max_size:
                cluster.append(n)
                frontier.append(n)
    areas = {by[g]["area"] for g in cluster}
    missing_first = [a for a in FIRST_ITERATION_REQUIRED if a not in areas] if first_iteration else []
    if missing_first:
        # pull the highest-ranked gap of each missing area if it is connected to anything in the cluster
        for a in missing_first:
            cand = next((x for x in order if by[x]["area"] == a and x not in cluster), None)
            if cand and len(cluster) < max_size and (adj[cand] & set(cluster)):
                cluster.append(cand)
        areas = {by[g]["area"] for g in cluster}
        missing_first = [a for a in FIRST_ITERATION_REQUIRED if a not in areas]
    if len(cluster) < 2:
        return {"status": "NO_CONNECTED_CLUSTER", "seed": seed, "detail": "top gap has no linked gap; stage as independent subchange"}
    excluded = [x for x in order if x not in cluster]
    links = sorted({tuple(sorted((a, b))) for a in cluster for b in adj[a] if b in cluster})
    return {"status": "CLUSTER_SELECTED" if not missing_first else "CLUSTER_MISSING_FIRST_ITERATION_AREAS",
            "cluster_gap_ids": cluster, "dependency_links": [list(l) for l in links], "excluded_queue": excluded,
            "missing_first_iteration_areas": missing_first,
            "target_quality": " + ".join(by[g]["expected_visual_signature"] for g in cluster[:2])}
