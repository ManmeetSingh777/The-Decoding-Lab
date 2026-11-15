"""Addendum 28 — versioned multiscale investigation protocol `VME-A28-1` (prompt contract P0–P6).

Every source-vision request carries `protocol = {version, sha, pass_id}` and a typed binding (source, sequence, target
images, prior boundary, active cluster, controlling problem, competing explanations, required response). The protocol
sha is the hash of THESE frozen templates, so a different executor (another coding model, another machine) can prove it
sends the same instructions — or must declare an explicit migrated version.

The templates teach the investigation PROCESS. They cannot make a model perceive correctly; `assess_sufficiency`
diagnoses answers that cannot control a producing choice (ST28-08/12, MODEL_STANDARD_DRIFT) without keyword-rejecting a
substantive, differently supported alternative, which is retained as a competing hypothesis instead.
"""
from __future__ import annotations

import re

from ..util import Blocked, digest, is_vague_statement

PROTOCOL_VERSION = "VME-A28-1"

P0 = """You are an investigator of visual ARTISTIC CONSTRUCTION and TEMPORAL RELATIONSHIPS. Discover source-supported choices that could
become reusable production methods for DIFFERENT ORIGINAL subjects. You are NOT asked to identify objects only, copy subject-specific
features, infer proprietary software, generate artwork or give generic praise.
Consult in order: the actual presented target images and their identities; whole-frame/scene context; adjacent frames and the persisted
event boundary; the selected quality cluster; the single active missing producer decision; the existing competing explanations. Use only
what visible (or genuinely available audible) evidence supports; label every proposed cause an INFERENCE.
WHOLE -> PARTS -> WHOLE: first state what the whole image/sequence visually accomplishes (focal subject, readable large shapes, supporting
world, near/far organisation, attention, simultaneous activity, change through time); then isolate the minimum high-impact part and
finishing relationships that explain that effect; then return to whole-image readability. Avoid disconnected micro-geometry.
For EVERY submitted target frame, state which established actor/object/art states persist and which visible relations change; give a precise
reason when nothing meaningful changes. Reconcile open events across packet boundaries. Do not label a pan / 3D camera / pose swap / new
drawing as fact merely because frames differ: these are alternatives until discriminated.
For each consequential gap state the missing choice a producer would have to make for a NEW original subject, the actual witnesses that could
resolve it, the conditions/contrasts and which generation, edit, drawing-state, asset or animation operation would change. If unknown,
output UNKNOWN plus exactly what further visual evidence is needed — never invented style rules.
Never write standalone conclusions ("polished", "vibrant", "flat vector", "great lighting", "fluid motion", "premium", "in <studio> style")
without a specific visible relationship and consequence. Never promote a palette, exact proportion, isolated pose, topic or exact scene to a
universal rule. Treat conflicting examples as evidence that narrows the condition.
Output strict records separating VISIBLE_FACT, POSSIBLE_MECHANISM, CONDITIONAL_PRODUCTION_CHOICE and REMAINING_UNKNOWN. A beautiful
explanation that changes no operation is not a usable skill."""

PASSES = {
    "P1": ("FULL_FRAME_AND_TEMPORAL_PACKET", """Looking at the complete artwork in each actual target frame and its neighbouring context, describe the
focal and supporting subjects as DESIGNED ENTITIES. Identify composition/space/shape hierarchy and what is visibly different at t versus t-1:
silhouettes, art states, expressions, hands, occlusions, light/colour organisation, world layers, apparent camera versus object motion,
attention and concurrent events, with frame ids and spans. In unchanged spans preserve state identities (persistent_state_ids) and say which
choices stay unchanged. If resolution prevents understanding, request native crops (native_detail_followups) without declaring a result.
If salient behaviour does not fit the current atlas, name it in unexplained_phenomena with witnesses and connected dimensions."""),
    "P2": ("HIGH_IMPACT_LINKED_MECHANISM", """For the active quality cluster identify the MOST CONSEQUENTIAL unexplained visible result in whole-frame
context. Track coherent outer shapes, part anatomy, negative space, relative proportions, material/colour/light boundaries, edge/finish,
actor/world and attention. Use unlike reference examples to see which relationships persist or adapt. State what is observed, which
interpretations are plausible and which contrary witness would falsify each. Write no style conclusion yet."""),
    "P3": ("NEXT_DISCRIMINATING_QUESTION", """Review the active-problem DAG and the operation plan. Choose the EARLIEST highest-impact missing producing
decision that more source evidence could change. State ONE question tied to it, the exact witnesses/crops, a realistic contrast, and at
least two evidence outcomes that lead to DIFFERENT production decisions or operator inputs. No fixed question list. Route API/compiler/
renderer failures to engineering instead of asking a source-art question."""),
    "P4": ("CONSTRUCTION_GRADE_ANSWER", """Answer the controlling question with source-visible facts first; separate inferences, alternatives, limits and
contradicting witnesses. Then the conditional decision for a NEW subject (applicability, visual role, material/view/action constraints,
variation, exceptions, invariants), the actual generation/edit operation, real reference-image roles (REFERENCE_REQUIRED when the decision
cannot be carried by text), identity/mask/layer/anchor/art-state needs, expected assets and the animation consumer. If a critical relation
is unknown, return a targeted source study request or missing operation, not adjectives. State the visible gain with vs without the
decision. Label the rule UNVERIFIED_UNTIL_ORIGINAL_ART_REVIEW."""),
    "P5": ("ADVERSARIAL_COMPLETENESS_AND_REINSPECTION", """Starting from the intended FULL finished original image/moving shot and the declared skill and
operation DAG, find any visually consequential detail, acting state, layer, relation, timing, material or cross-category dependency still
left to uncontrolled improvisation, even when every category has an answer. For source-grounded uncertainty inspect the supplied full frames,
NATIVE crops and temporal neighbours; return {"relations":[{"relation","dimensions"}], "changes_vs_neighbours", "uncertainty",
"phenomenon_dimensions"} and say UNKNOWN for what the pixels do not show."""),
    "P6": ("COLD_START_RESTORATION", """You are resuming using ONLY versioned durable artifacts. Verify source hashes, protocol version, committed raw
evidence, actor/event states, the 2-5 active gaps, the one controlling missing decision, competing explanations, frozen skill/prompt/
reference hashes, output defects, authorization and in-flight receipts. State fact vs inference vs unknown. Do NOT add style rules from a
recap. Reconcile unknown paid submissions instead of resending. Resume the first uncommitted operation with identical inputs."""),
}
PASS_ORDER = ("P0", "P1", "P2", "P3", "P4", "P5", "P6")
REQUIRED_BINDING = ("protocol", "source", "sequence", "target_images", "prior_boundary", "active_cluster", "controlling_problem",
                    "current_competing_explanations", "required_response")
CALIBRATION_PAIRS = [   # SYNTHETIC teaching examples only — never facts about any real film (28_WORKED_INVESTIGATION...)
    {"label": "SYNTHETIC", "weak": "The space explorer has expressive eyes, nice shadows and smooth limbs.",
     "why_weak": "no frame, no viewpoint, no linked relation, no contrast, no producing action",
     "useful": "At the fictional hero's three-quarter turn (SYN:0200-0248) the near cheek contour grows, the far eye is partly hidden and "
               "the helmet rim passes in front of the far brow while world light stays fixed; candidate mechanisms: authored alternate "
               "drawing vs deformable mesh (pixels do not discriminate). New action requires an approved canonical drawing, front and "
               "three-quarter head states via guided edits, and a hand+prop contact state; a flattened rotation would fail."},
    {"label": "SYNTHETIC", "weak": "Blue and orange palette, dark purple backgrounds, bright characters.",
     "why_weak": "copies hex-like palette, no role relation, no counterexample",
     "useful": "Across a focal close-up and a distant world shot, focal value contrast stays higher than background contrast even when "
               "illumination changes; a subdued-subject counterexample exists; decision is role-level (focus value hierarchy), not hues."},
]


def protocol_payload() -> dict:
    return {"version": PROTOCOL_VERSION, "P0": P0, "passes": {k: list(v) for k, v in PASSES.items()}, "binding": list(REQUIRED_BINDING),
            "calibration": CALIBRATION_PAIRS}


PROTOCOL_SHA = digest(protocol_payload())


def pass_instructions(pass_id: str) -> str:
    if pass_id == "P0":
        return f"PROTOCOL {PROTOCOL_VERSION} sha={PROTOCOL_SHA} pass=P0\n{P0}"
    if pass_id not in PASSES:
        raise Blocked("UNKNOWN_PROTOCOL_PASS", pass_id)
    name, text = PASSES[pass_id]
    return f"PROTOCOL {PROTOCOL_VERSION} sha={PROTOCOL_SHA} pass={pass_id} ({name})\n{P0}\n\n{pass_id}: {text}"


def bind(**fields) -> dict:
    """Typed P0 binding — a run never guesses a missing field."""
    missing = [k for k in REQUIRED_BINDING if k not in fields or fields[k] is None]
    if missing:
        raise Blocked("PROTOCOL_BINDING_MISSING", str(missing))
    p = fields["protocol"]
    if p.get("version") != PROTOCOL_VERSION or p.get("sha") != PROTOCOL_SHA:
        raise Blocked("PROTOCOL_VERSION_MISMATCH", f"{p.get('version')}/{str(p.get('sha'))[:12]} != {PROTOCOL_VERSION}/{PROTOCOL_SHA[:12]}")
    return {k: fields[k] for k in REQUIRED_BINDING}


def verify_protocol(version: str, sha: str, *, migration: dict | None = None) -> dict:
    """Cross-environment drift control (A28 §5.3): identical protocol or an explicit recorded migration."""
    if version == PROTOCOL_VERSION and sha == PROTOCOL_SHA:
        return {"status": "IDENTICAL_PROTOCOL"}
    if migration and migration.get("from_sha") == sha and migration.get("to_sha") == PROTOCOL_SHA and migration.get("calibration_report"):
        return {"status": "EXPLICIT_MIGRATION", "migration": migration}
    raise Blocked("PROTOCOL_DRIFT", f"stored {version}/{sha[:12]} vs code {PROTOCOL_VERSION}/{PROTOCOL_SHA[:12]}; no recorded migration")


# ---- sufficiency for a producing choice (ST28-08/12, MODEL_STANDARD_DRIFT_TEST) ------------------------------
_RELATIONAL = re.compile(r"\b(while|as|relative to|against|behind|in front of|overlap|occlud|separat|together|contrast|changes? with|"
                         r"stays|persist|than|across|between|follows|before|after)\b", re.I)


def assess_sufficiency(answer: dict, *, producing_operator: str, known_witness_ids: set[str]) -> dict:
    """Is this answer able to control a producing choice? Field presence is NOT enough. Returns verdict + reasons.

    INSUFFICIENT_FOR_PRODUCING_CHOICE when facts are adjective-only, uncited, non-relational, or no branch changes the named operator.
    A substantive answer is SUFFICIENT even if it disagrees with existing decisions (that disagreement is handled as a competing
    hypothesis by the caller, never keyword-rejected)."""
    reasons = []
    facts = answer.get("SOURCE_VISIBLE_FACTS") or []
    cited = [f for f in facts if set(f.get("witness_ids") or []) & known_witness_ids]
    if not cited:
        reasons.append("NO_FACT_CITES_A_REAL_WITNESS")
    relational = [f for f in cited if _RELATIONAL.search(f.get("relation", "")) and not is_vague_statement(f.get("relation", ""))]
    if cited and not relational:
        reasons.append("FACTS_ARE_NOT_RELATIONAL_OR_ARE_ADJECTIVE_ONLY")
    if is_vague_statement(answer.get("CONSTRUCTION_EXPLANATION", "")) or len(answer.get("CONSTRUCTION_EXPLANATION", "").split()) < 6:
        reasons.append("MECHANISM_HYPOTHESIS_ABSENT_OR_VAGUE")
    brs = [b for b in answer.get("BRANCHES") or [] if b.get("operation_id") == producing_operator and b.get("construction_action")]
    if answer.get("answer_status") not in ("UNKNOWN", "REFUTED") and not brs:
        reasons.append("NO_BRANCH_CHANGES_THE_PRODUCING_OPERATOR")
    if brs and all(is_vague_statement(b["construction_action"]) for b in brs):
        reasons.append("BRANCH_ACTION_IS_ADJECTIVE_ONLY")
    if not answer.get("REMAINING_UNKNOWN") and answer.get("answer_status") != "OBSERVED":
        reasons.append("NO_DECLARED_UNKNOWNS_FOR_AN_INFERRED_ANSWER")
    return {"verdict": "SUFFICIENT_FOR_PRODUCING_CHOICE" if not reasons else "INSUFFICIENT_FOR_PRODUCING_CHOICE", "reasons": reasons,
            "cited_fact_count": len(cited), "relational_fact_count": len(relational)}


def competing_hypothesis(existing_decision: dict | None, answer: dict, assessment: dict) -> dict | None:
    """A sufficient answer whose action differs from an accepted decision is kept as a SEPARATE unverified hypothesis (ST28-19)."""
    if not existing_decision or assessment["verdict"] != "SUFFICIENT_FOR_PRODUCING_CHOICE":
        return None
    old = {b["construction_action"] for b in existing_decision.get("branches", [])}
    new = {b.get("construction_action") for b in answer.get("BRANCHES") or []}
    if new and not new & old:
        return {"status": "COMPETING_HYPOTHESIS_UNVERIFIED", "against_decision": existing_decision["decision_id"],
                "against_version": existing_decision.get("version"), "alternative_actions": sorted(x for x in new if x),
                "witness_ids": sorted({w for f in answer.get("SOURCE_VISIBLE_FACTS") or [] for w in f.get("witness_ids") or []}),
                "resolution_needed": "discriminating source evidence; the accepted decision is NOT overwritten"}
    return None
