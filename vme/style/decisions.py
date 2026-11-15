"""Witness → conditional transferable style decision (spec 09 C1–C5, 14 T1–T7, ADD25 §4.1).

Separates SOURCE_FACT / SCENE_FACT / VAGUE / STYLE_CANDIDATE; runs the C4 source-
independence challenge with two unlike substitute subjects; enforces conditions,
invariants, adaptations, exceptions and a registered producing operation before any
decision can leave RESEARCH_ONLY. Interface I provenance gate lives in provenance.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field

from ..util import Blocked, digest, is_vague_statement, now_iso
from ..investigation.evidence import WitnessBundle, validate_bundle
from ..selection.sixth import is_source_specific_branding

DECISION_STATUSES = ("RESEARCH_ONLY", "EXECUTABLE_CANDIDATE", "DEMONSTRATED", "TRANSFERABLE")
CONDITION_KEYS = ("subject_kind", "role", "material", "view", "scale", "action", "environment")
_NUMERIC_RATIO = re.compile(r"\b\d+(\.\d+)?\s*(:|x|×|/)\s*\d+(\.\d+)?\b|\bratio\s+of\s+\d|#[0-9a-f]{6}\b|\brgb\s*\(", re.I)


@dataclass
class DecisionBranch:
    when: dict                      # subset of CONDITION_KEYS -> value
    construction_action: str
    clause_ids: list
    reference_role_ids: list
    operation_node_ids: list
    priority: int = 100
    mandatory_reference_role_ids: list | None = None   # None = legacy (all roles mandatory)

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["mandatory_reference_role_ids"] is None:
            d.pop("mandatory_reference_role_ids")
        return d


@dataclass
class ConditionalVisualDecision:
    decision_id: str
    version: int
    target_quality: str
    branches: list                                   # [DecisionBranch]
    invariant_visual_relation: str
    adaptive_visual_choices: list
    visible_shape_and_artwork_relationships: list
    scene_coherence_relationships: list
    temporal_or_pose_relationships: list
    applicability_constraints: list
    exceptions: list
    forbidden_source_specific_copies: list
    evidence_frame_ids: list
    contrasting_evidence_ids: list
    uncertainty: list
    required_asset_slots: list
    expected_visible_effect: str
    creative_freedom: list
    dependencies: list
    observed_relation_ids: list                      # provenance parents (Interface I)
    origin_type: str                                 # SOURCE_OBSERVED | CROSS_SOURCE_INFERRED | APPROVED_STYLE_REVISION | MODEL_SUGGESTED_UNVERIFIED ...
    status: str = "RESEARCH_ONLY"
    research_only_reason: str | None = None
    evidence_scope: str = "SINGLE_SOURCE_LEAD"
    synthetic: bool = False
    substitution_challenge: list = field(default_factory=list)
    dimension_tags: list = field(default_factory=list)      # Addendum 27 completeness dimensions this decision governs
    created_at: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["branches"] = [b if isinstance(b, dict) else asdict(b) for b in self.branches]
        return d


def classify_statement(text: str, scene_specific_facts: list[str]) -> str:
    """SCENE_FACT if it names declared source-specific objects/values; VAGUE if adjectives only."""
    t = (text or "").lower()
    if is_source_specific_branding(t):
        return "SCENE_FACT"
    for f in scene_specific_facts:
        terms = [w for w in re.findall(r"[a-z]{4,}", f.lower()) if w not in _GENERIC_WORDS]
        if terms and sum(1 for w in terms if w in t) >= max(1, (len(terms) + 1) // 2):
            return "SCENE_FACT"
    if _NUMERIC_RATIO.search(t) and not re.search(r"(when|if|for|relative|range|varies|depending|conditional)", t):
        return "SCENE_FACT"  # unconditional copied constants are source facts; conditional measured relations may transfer
    if is_vague_statement(t):
        return "VAGUE"
    return "STYLE_CANDIDATE"


_GENERIC_WORDS = {"with", "that", "this", "from", "into", "their", "there", "these", "those", "which", "where", "when",
                  "have", "has", "shot", "frame", "scene", "source", "film", "visible", "shows", "large", "small"}


def substitution_challenge(reusable_text: str, substitutes: list[dict], scene_specific_facts: list[str]) -> list[dict]:
    """C4: verbally substitute ≥2 unlike original subjects; the rule must still read as a decision."""
    if len(substitutes) < 2 or len({s["subject_kind"] for s in substitutes}) < 2:
        raise Blocked("SUBSTITUTION_CHALLENGE_NEEDS_TWO_UNLIKE_SUBJECTS")
    out = []
    for s in substitutes:
        txt = reusable_text.replace("{subject}", s["noun"]).replace("${subject}", s["noun"])
        verdict = classify_statement(txt, scene_specific_facts)
        out.append({"substitute": s, "rendered": txt[:300], "verdict": verdict})
    return out


def witness_to_decision(bundle: WitnessBundle, proposal: dict, *, registered_operators: dict,
                        substitutes: list[dict] | None) -> ConditionalVisualDecision:
    """T1–T5. Raises Blocked for structurally invalid input; otherwise returns a decision whose
    `status`/`research_only_reason` truthfully reflect what is missing."""
    vb = validate_bundle(bundle)
    if not vb["ok"]:
        raise Blocked("INVALID_WITNESS_BUNDLE", ";".join(vb["problems"]))
    facts = sorted({f for w in bundle.ws() for f in w.scene_specific_facts})
    reusable = " ".join([proposal.get("invariant_visual_relation", ""),
                         *[b.get("construction_action", "") for b in proposal.get("branches", [])],
                         proposal.get("expected_visible_effect", "")])
    cls = classify_statement(reusable, facts)
    if cls == "SCENE_FACT":
        raise Blocked("SCENE_FACT_NOT_STYLE", "reusable fields copy source-specific facts/branding/ratios", facts=facts)
    if cls == "VAGUE":
        raise Blocked("VAGUE_STYLE_DECISION", "needs a picture-producing relation, not adjectives")
    # NOTE: text substitution is only a copying LINT, never evidence of visual transfer. The REAL authoring path
    # passes substitutes=None and relies on contrasting witnesses from other subjects/films instead.
    chal = substitution_challenge(reusable, substitutes, facts) if substitutes is not None else         [{"verdict": "STYLE_CANDIDATE", "note": "NOT_RUN: conditionality judged from contrasting witnesses, not word swaps"}]
    if any(c["verdict"] != "STYLE_CANDIDATE" for c in chal):
        raise Blocked("FAILS_SOURCE_INDEPENDENCE_CHALLENGE", str([c["verdict"] for c in chal]))
    branches = [DecisionBranch(**b) for b in proposal.get("branches", [])]
    reason = None
    if not branches or any(not b.when for b in branches):
        reason = "MISSING_CONDITIONS"
    elif any(k not in CONDITION_KEYS for b in branches for k in b.when):
        raise Blocked("UNKNOWN_CONDITION_KEY")
    elif not proposal.get("exceptions") or not proposal.get("adaptive_visual_choices"):
        reason = "MISSING_EXCEPTIONS_OR_ADAPTATIONS"              # B14
    elif not all(b.operation_node_ids for b in branches) or any(o not in registered_operators
                                                               for b in branches for o in b.operation_node_ids):
        reason = "NO_REGISTERED_PRODUCING_OPERATION"              # B15 / ADD25-Q04 / ADD26-S02
    elif not all(b.clause_ids for b in branches):
        reason = "NO_SKILL_CLAUSE"
    elif proposal.get("origin_type") in ("MODEL_SUGGESTED_UNVERIFIED", "UNKNOWN_ORIGIN"):
        reason = "UNVERIFIED_ORIGIN"
    status = "RESEARCH_ONLY" if reason else "EXECUTABLE_CANDIDATE"
    scope = vb["evidence_scope"]
    return ConditionalVisualDecision(
        decision_id=proposal["decision_id"], version=int(proposal.get("version", 1)),
        target_quality=proposal["target_quality"], branches=[b.to_dict() for b in branches],
        invariant_visual_relation=proposal.get("invariant_visual_relation", ""),
        adaptive_visual_choices=proposal.get("adaptive_visual_choices", []),
        visible_shape_and_artwork_relationships=proposal.get("visible_shape_and_artwork_relationships", []),
        scene_coherence_relationships=proposal.get("scene_coherence_relationships", []),
        temporal_or_pose_relationships=proposal.get("temporal_or_pose_relationships", []),
        applicability_constraints=proposal.get("applicability_constraints", []),
        exceptions=proposal.get("exceptions", []),
        forbidden_source_specific_copies=sorted(set(proposal.get("forbidden_source_specific_copies", [])) | set(facts)),
        evidence_frame_ids=[w.witness_id for w in bundle.ws()], contrasting_evidence_ids=bundle.contrasting_witness_ids,
        uncertainty=proposal.get("uncertainty", []), required_asset_slots=proposal.get("required_asset_slots", []),
        expected_visible_effect=proposal.get("expected_visible_effect", ""), creative_freedom=proposal.get("creative_freedom", []),
        dependencies=proposal.get("dependencies", []), observed_relation_ids=proposal.get("observed_relation_ids", []),
        origin_type=proposal.get("origin_type", "UNKNOWN_ORIGIN"), status=status, research_only_reason=reason,
        evidence_scope=scope, synthetic=bundle.synthetic, substitution_challenge=chal,
        dimension_tags=proposal.get("dimension_tags", []), created_at=now_iso())


def transfer_status(decision: dict) -> str:
    """Single-source evidence never yields a transferable rule (B11); demonstration needs real outputs."""
    if decision["status"] == "RESEARCH_ONLY":
        return "RESEARCH_ONLY"
    if decision.get("evidence_scope") == "SINGLE_SOURCE_LEAD":
        return "CONDITIONAL_CANDIDATE_LIMITED_SCOPE"
    return decision["status"]


def decision_sha(decision: dict) -> str:
    return digest({k: v for k, v in decision.items() if k not in ("created_at",)})
