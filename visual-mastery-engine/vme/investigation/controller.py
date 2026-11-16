"""The single decision owner: `ActiveArtProblem` + dynamic ONE-next-question derivation (Addendum 26 §3).

Q0–Q7 (Addendum 25) are used here as *reasoning dimensions* that a derived question and
its answer plan must engage; they are never emitted as a fixed questionnaire. The next
question is derived from the earliest incomplete causal handoff of the current problem,
grounded in a real visible contrast, and must state how alternative answers change an
actual producing operation (Addendum 26 §3.2).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field
from typing import Callable

from ..util import Blocked, digest, is_vague_statement, new_id, now_iso

HANDOFF_ORDER = ("SOURCE_OBSERVATION", "CAUSE_INFERENCE", "STYLE_CONDITIONS", "OPERATION_DESIGN",
                 "PROMPT_COMPILATION", "PROVIDER_RESULT", "ASSET_FAMILY", "RENDER", "HUMAN_REVIEW")
# Failure location → which repair lane owns the next question (Addendum 26 §3.5, §5 critical routing)
ROUTE_BY_STAGE = {
    "SOURCE_OBSERVATION": "S1_SOURCE_EVIDENCE", "CAUSE_INFERENCE": "S2_QUESTION", "STYLE_CONDITIONS": "S3_CONDITIONS",
    "OPERATION_DESIGN": "S4_OPERATION", "PROMPT_COMPILATION": "ENGINEERING_REPAIR_COMPILER",
    "PROVIDER_RESULT": "S4S5_PROVIDER_ROUTE", "ASSET_FAMILY": "S7_ASSET_FAMILY", "RENDER": "ENGINEERING_REPAIR_RENDER",
    "HUMAN_REVIEW": "AWAIT_USER",
}
REASONING_DIMENSIONS = ("Q0_result", "Q1_relations", "Q2_causal_importance", "Q3_contrast", "Q4_new_subject_decision",
                        "Q5_remaining_style_ambiguity", "Q6_operation", "Q7_proof")
# Literal Addendum 25 questionnaire stems: emitting these verbatim is questionnaire theatre (ADD26-Q01).
LITERAL_Q_STEMS = ("what is the observable high-impact result", "what visible relationships appear to create it",
                   "which details are causally important versus merely present", "what happens in different cases",
                   "what decisions would a producer make on a new subject", "what would still be left for the image model",
                   "what executable operation produces the decision", "what would prove it changed original art")
ANSWER_FIELDS = ("SOURCE_VISIBLE_FACTS", "IMPORTANT_LINKED_CHANGES", "CONSTRUCTION_EXPLANATION", "WHY_THE_DECISION_MATTERS",
                 "WHEN_APPLICABLE", "WHEN_NOT_APPLICABLE", "ACTUAL_PRODUCING_OPERATION", "WHERE_IT_ENTERS_COMPILED_REQUEST",
                 "REMAINING_UNKNOWN")
ANSWER_STATUSES = ("OBSERVED", "INFERRED", "UNKNOWN", "REFUTED")


@dataclass
class ActiveArtProblem:
    cluster_id: str
    version: int
    original_output_id_or_initial_reference_only: str
    reference_full_frame_ids: list
    affected_original_subject_classes: list
    high_impact_visible_difference: str
    whole_scene_consequence: str
    connected_artistic_relations: list
    current_explanation_and_support: list = field(default_factory=list)   # [{claim, witness_ids}]
    competing_explanations: list = field(default_factory=list)
    latest_confirmed_facts: list = field(default_factory=list)
    latest_unresolved_uncertainties: list = field(default_factory=list)
    expected_original_visual_improvement: str = ""
    next_required_producer_decision_id: str = ""
    owner_stage: str = "SOURCE_OBSERVATION"
    current_question_id_or_null: str | None = None
    source_evidence_version: str = ""
    selected_skill_version_or_null: str | None = None
    review_state: str = "NONE"
    next_action_and_exact_input: str = ""
    checkpoint_id: str | None = None
    required_conditions: dict = field(default_factory=dict)   # scope the decision must cover, e.g. {"view": "three_quarter"}
    output_findings: list = field(default_factory=list)       # latest original-output defects with attribution evidence
    history: list = field(default_factory=list)               # previous question ids / gaps

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProblemContext:
    """Everything the controller may consult. Each entry is a real persisted record, not prose."""
    bundles: dict = field(default_factory=dict)          # bundle_id -> WitnessBundle dict
    witnesses: dict = field(default_factory=dict)        # witness_id -> Witness dict
    decisions: dict = field(default_factory=dict)        # decision_id -> ConditionalVisualDecision dict
    registered_operators: dict = field(default_factory=dict)   # op_id -> {"capabilities": [...]}
    provider_capabilities: list = field(default_factory=list)  # supported op kinds
    compile_trace: dict | None = None                    # last compile result (trace or ticket)
    output_review: dict | None = None                    # last original output review
    asset_report: dict | None = None
    render_report: dict | None = None
    human_review: dict | None = None


def locate_earliest_missing_handoff(p: ActiveArtProblem, ctx: ProblemContext) -> dict:
    """Strict causal order: source fact → cause → condition → operation → compiled job → output → assets → render."""
    did = p.next_required_producer_decision_id
    full = [ctx.witnesses.get(w) for w in p.reference_full_frame_ids]
    full = [w for w in full if w]
    unseen = [u for u in p.latest_unresolved_uncertainties if u.get("kind") in ("NOT_SEEN", "RESOLUTION_INSUFFICIENT")]
    if not full or unseen:
        return {"stage": "SOURCE_OBSERVATION", "missing": did, "why": "no inspected whole-frame witness" if not full
                else f"source relation not actually visible: {unseen[0].get('what')}"}
    if not any(e.get("witness_ids") for e in p.current_explanation_and_support):
        return {"stage": "CAUSE_INFERENCE", "missing": did, "why": "no witness-supported explanation of the visible relation"}
    dec = ctx.decisions.get(did)
    if dec is None:
        return {"stage": "STYLE_CONDITIONS", "missing": did, "why": "required conditional decision does not exist"}
    # A single documented branch must satisfy the JOINT production context.
    # Two disjoint branches each matching one key are not evidence for the joint state.
    joint_supported = any(all(str(br.get("when", {}).get(k)) == str(v) for k, v in p.required_conditions.items())
                          for br in dec.get("branches", []))
    uncovered = {} if joint_supported else dict(p.required_conditions)
    if uncovered or dec.get("status") == "RESEARCH_ONLY" and dec.get("research_only_reason") in ("MISSING_CONDITIONS", "SINGLE_SOURCE"):
        return {"stage": "STYLE_CONDITIONS", "missing": did, "why": f"no branch for required conditions {uncovered or dec.get('research_only_reason')}",
                "uncovered_conditions": uncovered}
    ops = [o for br in dec.get("branches", []) for o in br.get("operation_node_ids", [])] or dec.get("operation_node_ids", [])
    unreg = [o for o in ops if o not in ctx.registered_operators]
    if not ops or unreg:
        return {"stage": "OPERATION_DESIGN", "missing": did, "why": f"operation not registered: {unreg or 'none declared'}"}
    unsupported = [o for o in ops if ctx.registered_operators[o].get("kind") not in ctx.provider_capabilities]
    if unsupported and ctx.provider_capabilities:
        return {"stage": "OPERATION_DESIGN", "missing": did, "why": f"provider cannot run {unsupported}"}
    ct = ctx.compile_trace
    if ct is None:
        return {"stage": "PROMPT_COMPILATION", "missing": did, "why": "no compiled job yet", "not_yet_run": True}
    if ct.get("blocked"):
        if ct.get("code") == "MISSING_STYLE_DECISION":
            return {"stage": "STYLE_CONDITIONS", "missing": ct.get("missing_decision", did), "why": "compiler ticket"}
        return {"stage": "PROMPT_COMPILATION", "missing": did, "why": f"compile blocked: {ct.get('code')}"}
    if did not in ct.get("selected_decisions", []) or ct.get("skill_present_but_not_compiled"):
        return {"stage": "PROMPT_COMPILATION", "missing": did,
                "why": f"decision selected by skill but absent from payload: {ct.get('skill_present_but_not_compiled')}"}
    rv = ctx.output_review
    if rv is None:
        return {"stage": "PROVIDER_RESULT", "missing": did, "why": "no real output yet", "not_yet_run": True}
    bad = [f for f in rv.get("findings", []) if f.get("attributed_stage") in ("PROVIDER_RESULT", "SOURCE_OBSERVATION",
                                                                            "STYLE_CONDITIONS", "CAUSE_INFERENCE")]
    if bad:
        f0 = sorted(bad, key=lambda f: HANDOFF_ORDER.index(f["attributed_stage"]))[0]
        return {"stage": f0["attributed_stage"], "missing": f0.get("decision_id") or did, "why": f0["symptom"], "finding": f0}
    if ctx.asset_report and not ctx.asset_report.get("ok"):
        return {"stage": "ASSET_FAMILY", "missing": did, "why": ctx.asset_report.get("problems", ["asset failure"])[0]}
    if ctx.render_report and not ctx.render_report.get("ok"):
        return {"stage": "RENDER", "missing": did, "why": ctx.render_report.get("problems", ["render failure"])[0]}
    return {"stage": "HUMAN_REVIEW", "missing": did, "why": "awaiting user verdict"}


def _witness_label(ctx: ProblemContext, wid: str) -> str:
    w = ctx.witnesses.get(wid, {})
    return f"{wid}[{w.get('evidence_kind', '?')} f{w.get('frame_start', '?')}-{w.get('frame_end', '?')} {w.get('subject_class') or ''}]".strip()


@dataclass
class NextQuestion:
    question_id: str
    cluster_id: str
    from_evidence_version: str
    gap_id: str
    missing_decision_id: str
    missing_producing_operation: str
    observed_contrast_with_witness_ids: list
    exact_artistic_unknown: str
    question_text: str
    planned_witness_or_input_ids: list
    possible_answer_consequences_for_operation: list
    route: str
    owner_stage: str
    reasoning_dimensions: dict
    uncovered_reasoning_dimensions: list
    answer_evidence_ids: list = field(default_factory=list)
    answer_visible_relations: list = field(default_factory=list)
    answer_status: str = "UNKNOWN"
    condition_applicability_and_exceptions: list = field(default_factory=list)
    effect_on_skill_version_and_compiled_job: str = ""
    next_action_if_unresolved: str = ""
    timestamp_and_checkpoint: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _alternatives_for(stage: str, p: ActiveArtProblem, ctx: ProblemContext, loc: dict) -> list[dict]:
    """How different plausible answers would change an actual operation (the usefulness test, §3.2 step 4d)."""
    did = loc["missing"]
    if stage == "SOURCE_OBSERVATION":
        return [{"if": "native crop shows the relation is a redrawn part state", "then": f"{did}: add whole-state redraw branch → guided_pose_edit"},
                {"if": "native crop shows a rigid transform of the same drawing", "then": f"{did}: keep layer transform → layer_extract + motion_render"}]
    if stage == "CAUSE_INFERENCE":
        alts = p.competing_explanations[:2] or [{"claim": "relation caused by part organisation"}, {"claim": "relation caused by value/colour grouping"}]
        return [{"if": f"evidence supports '{a.get('claim')}'", "then": f"{did}: construction_action targets {a.get('claim')}"} for a in alts]
    if stage == "STYLE_CONDITIONS":
        unc = loc.get("uncovered_conditions") or p.required_conditions
        k = next(iter(unc), "subject_kind")
        return [{"if": f"choice is invariant across {k}", "then": f"{did}: single branch, clause reused for {k}={unc.get(k)}"},
                {"if": f"choice adapts with {k}", "then": f"{did}: new branch when {k}={unc.get(k)} with its own clause + reference role"}]
    if stage == "OPERATION_DESIGN":
        caps = ctx.provider_capabilities or ["whole_scene", "guided_pose_edit"]
        return [{"if": f"route '{c}' preserves the decision", "then": f"{did}: operation_node={c}"} for c in caps[:2]] or \
               [{"if": "no supported route", "then": f"{did}: RESEARCH_ONLY until a provider route exists"}]
    if stage == "PROMPT_COMPILATION":
        return [{"if": "condition evaluation dropped the branch", "then": "fix resolver predicate; payload must then contain the clause"},
                {"if": "clause binding/precedence dropped the text", "then": "fix template rendering order; payload must then contain the clause"}]
    if stage == "PROVIDER_RESULT":
        return [{"if": "reference role allocation was insufficient", "then": f"{did}: stage a reference-guided edit with the identity/style anchor"},
                {"if": "model cannot follow even with correct conditioning", "then": "switch provider/model route (user-approved)"}]
    if stage == "ASSET_FAMILY":
        return [{"if": "variant drawn without canonical conditioning", "then": "regenerate variant via guided_pose_edit from approved canonical"},
                {"if": "segmentation destroyed the drawing", "then": "use whole-state drawings + state swap instead of layers"}]
    if stage == "RENDER":
        return [{"if": "pivot/anchor mismatch", "then": "fix ArtLayer anchor contract"},
                {"if": "wrong drawing-state timing", "then": "fix StateTransition timing"}]
    return [{"if": "user approves", "then": "freeze and proceed"}, {"if": "user rejects", "then": "derive next question from their critique"}]


def derive_next_question(p: ActiveArtProblem, ctx: ProblemContext, *, gap_id: str) -> NextQuestion:
    """Produce exactly ONE discriminating question for the earliest blocking dependency."""
    loc = locate_earliest_missing_handoff(p, ctx)
    stage = loc["stage"]
    did = loc["missing"]
    if not did:
        raise Blocked("NO_MISSING_DECISION_NAMED", "a question must be bound to a producer decision")
    full_ids = list(p.reference_full_frame_ids)
    contrast_ids = sorted({wid for b in ctx.bundles.values() for wid in b.get("contrasting_witness_ids", [])
                           if any(w.get("witness_id") in full_ids for w in b.get("witnesses", []))})
    witnesses = full_ids + [c for c in contrast_ids if c not in full_ids]
    relations = ", ".join(p.connected_artistic_relations[:3]) or "the linked relations"
    wl = "; ".join(_witness_label(ctx, w) for w in witnesses[:4]) or "NO WITNESS YET"
    finding = loc.get("finding") or {}
    alt = _alternatives_for(stage, p, ctx, loc)
    op_missing = {"OPERATION_DESIGN": "registered operation for " + did, "PROMPT_COMPILATION": "skill→payload binding of " + did,
                  "PROVIDER_RESULT": "conditioning/edit route honouring " + did,
                  "ASSET_FAMILY": "canonical-conditioned state drawing", "RENDER": "scene-graph state/timing"}.get(stage, did)
    if stage == "SOURCE_OBSERVATION":
        unknown = f"whether {relations} is actually constructed as claimed (current evidence: {loc['why']})"
        text = (f"In {wl}, {p.high_impact_visible_difference}; the deciding region was not inspected at sufficient resolution. "
                f"Which native-resolution crop of the focal region, viewed with its full frame and the adjacent frames, shows how "
                f"{relations} is constructed, so that decision {did} can choose between: "
                + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = [*full_ids, "NATIVE_CROP(focal region)", "TEMPORAL_COMPARE(±2 frames)"]
    elif stage == "CAUSE_INFERENCE":
        unknown = f"which visible relation among {relations} causes the difference"
        text = (f"Given {wl} where {p.high_impact_visible_difference}, which of the competing explanations ("
                + "; ".join(e.get("claim", "?") for e in p.competing_explanations[:2]) +
                f") is supported by the visible relations between {relations}, and which witness contradicts the other, so that "
                f"{did}'s construction action becomes: " + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = witnesses + ["CONTRASTING_WITNESS"]
    elif stage == "STYLE_CONDITIONS":
        unc = loc.get("uncovered_conditions") or p.required_conditions
        cond = ", ".join(f"{k}={v}" for k, v in unc.items()) or "the new subject conditions"
        unknown = f"how the {relations} decision behaves under {cond}"
        text = (f"Comparing {wl}: {p.high_impact_visible_difference}. Under {cond}, which parts of the {relations} "
                f"construction stay invariant and which adapt with the actor/world design, so that for a new original subject the "
                f"producer selects: " + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = witnesses + [f"UNLIKE_WITNESS({cond})"]
    elif stage == "OPERATION_DESIGN":
        unknown = f"which supported operation constructs {did}"
        text = (f"Decision {did} is supported by {wl} but {loc['why']}. Which provider-supported route among "
                f"{ctx.provider_capabilities or 'the verified capabilities'} produces {relations} for a new subject from typed inputs, and "
                f"what output asset contract results: " + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = [did, "PROVIDER_CAPABILITY_SNAPSHOT", "OPERATOR_REGISTRY"]
    elif stage == "PROMPT_COMPILATION":
        unknown = f"which dataflow step drops {did}"
        text = (f"Skill selects {did} for this brief but {loc['why']}. Which binding, precedence or condition-evaluation step in "
                f"the compiler drops it from the provider payload: " + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = ["COMPILE_TRACE", "PAYLOAD_BYTES_BEFORE_AFTER", did]
    elif stage == "PROVIDER_RESULT":
        unknown = f"which conditioning route makes the provider honour {did}"
        text = (f"The compiled job carried {did}, yet the output shows {finding.get('symptom', loc['why'])} compared with {wl}. "
                f"Which reference-role allocation, guided edit or provider route can construct {relations} within the verified "
                f"capabilities: " + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = [finding.get("output_id", "ORIGINAL_OUTPUT"), *witnesses[:2], "PROVIDER_CAPABILITY_SNAPSHOT"]
    elif stage == "ASSET_FAMILY":
        unknown = "which state drawing must be produced from the approved canonical"
        text = (f"The approved canonical art is sound but {loc['why']}. Which whole-pose/view/hand+prop drawing must be produced "
                f"from the canonical image to keep {relations}: " + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = ["APPROVED_CANONICAL", "ASSET_REPORT"]
    elif stage == "RENDER":
        unknown = "which scene-graph element breaks the motion"
        text = (f"Assets are approved but {loc['why']}. Which timing, pivot, mask or drawing-state selection fails: "
                + " / ".join(f"{a['if']} → {a['then']}" for a in alt) + "?")
        planned = ["SCENE_GRAPH", "RENDER_REPORT"]
    else:
        unknown = "user visual verdict"
        text = "Which important visual qualities are still missing or wrong?"
        planned = ["REVIEW_PACKET"]
    dims = {
        "Q0_result": p.high_impact_visible_difference or None,
        "Q1_relations": p.connected_artistic_relations or None,
        "Q2_causal_importance": [e.get("claim") for e in p.current_explanation_and_support] or None,
        "Q3_contrast": contrast_ids or None,
        "Q4_new_subject_decision": did,
        "Q5_remaining_style_ambiguity": [u.get("what") for u in p.latest_unresolved_uncertainties] or None,
        "Q6_operation": op_missing,
        "Q7_proof": p.expected_original_visual_improvement or None,
    }
    q = NextQuestion(
        question_id=new_id("q"), cluster_id=p.cluster_id, from_evidence_version=p.source_evidence_version, gap_id=gap_id,
        missing_decision_id=did, missing_producing_operation=op_missing,
        observed_contrast_with_witness_ids=witnesses, exact_artistic_unknown=unknown, question_text=text,
        planned_witness_or_input_ids=planned, possible_answer_consequences_for_operation=alt,
        route=ROUTE_BY_STAGE[stage], owner_stage=stage, reasoning_dimensions=dims,
        uncovered_reasoning_dimensions=[k for k, v in dims.items() if not v],
        next_action_if_unresolved=f"retrieve {planned[0] if planned else 'evidence'} and re-ask narrower; keep {did} BLOCKED",
        timestamp_and_checkpoint=now_iso())
    check_question_quality(q, ctx)
    return q


def check_question_quality(q: NextQuestion, ctx: ProblemContext) -> None:
    t = q.question_text.lower()
    if any(t.strip().startswith(s) or t.strip() == s + "?" for s in LITERAL_Q_STEMS):
        raise Blocked("FIXED_QUESTIONNAIRE_REJECTED", "literal Q0–Q7 wording is not a derived question")
    if q.owner_stage != "HUMAN_REVIEW":
        if q.missing_decision_id.lower() not in t:
            raise Blocked("QUESTION_NOT_BOUND_TO_DECISION")
        if len(q.possible_answer_consequences_for_operation) < 2:
            raise Blocked("QUESTION_HAS_NO_OPERATIONAL_CONSEQUENCE")
        if re.fullmatch(r".*(why (is it|are they) beautiful|what is the palette).*", t):
            raise Blocked("LOW_LEVERAGE_QUESTION")
        if q.owner_stage in ("SOURCE_OBSERVATION", "CAUSE_INFERENCE", "STYLE_CONDITIONS") and not q.observed_contrast_with_witness_ids:
            raise Blocked("QUESTION_WITHOUT_VISIBLE_CONTRAST")


def reject_question_list(candidates: list) -> None:
    """ADD26-Q02: one controlling question per bottleneck, never a brainstormed list."""
    if isinstance(candidates, list) and len(candidates) > 1:
        bottlenecks = {getattr(c, "missing_decision_id", None) or (c.get("missing_decision_id") if isinstance(c, dict) else None)
                       for c in candidates}
        if len(bottlenecks) <= 1:
            raise Blocked("QUESTION_LIST_THEATRE", f"{len(candidates)} questions for one bottleneck")


def select_evidence(q: NextQuestion, available: dict) -> list[str]:
    """Cheapest sufficient evidence for the question's stage (§3.2 step 5). Never film re-reads for code gaps."""
    stage = q.owner_stage
    if stage in ("PROMPT_COMPILATION", "RENDER"):
        return [k for k in available if available[k].get("kind") in ("COMPILE_TRACE", "PAYLOAD", "RENDER_REPORT", "SCENE_GRAPH")]
    if stage == "OPERATION_DESIGN":
        return [k for k in available if available[k].get("kind") in ("CAPABILITY", "OPERATOR")]
    if stage == "PROVIDER_RESULT":
        return [k for k in available if available[k].get("kind") in ("ORIGINAL_OUTPUT", "FULL_FRAME", "CAPABILITY")][:4]
    picked = [k for k in q.observed_contrast_with_witness_ids if k in available]
    if stage == "SOURCE_OBSERVATION":
        picked += [k for k in available if available[k].get("kind") in ("NATIVE_CROP", "TEMPORAL_COMPARE")
                   and available[k].get("parent") in q.observed_contrast_with_witness_ids]
    return list(dict.fromkeys(picked))


def validate_answer(q: NextQuestion, answer: dict, registered_ops: dict) -> dict:
    """§4.4 good-answer standard. Vague or unsupported answers keep the decision UNRESOLVED (ADD26-Q06)."""
    problems = []
    status = answer.get("answer_status", "UNKNOWN")
    if status not in ANSWER_STATUSES:
        problems.append("BAD_STATUS")
    for f in ANSWER_FIELDS:
        if f not in answer:
            problems.append(f"MISSING:{f}")
    if status in ("OBSERVED", "INFERRED"):
        facts = answer.get("SOURCE_VISIBLE_FACTS") or []
        if q.owner_stage in ("SOURCE_OBSERVATION", "CAUSE_INFERENCE", "STYLE_CONDITIONS"):
            if not facts or any(not f.get("witness_ids") for f in facts):
                problems.append("FACT_WITHOUT_WITNESS")
            # Only images selected by the controller and actually supplied to the
            # source question can authorize a fact. A model cannot self-add IDs.
            allowed = set(q.observed_contrast_with_witness_ids)
            if set(answer.get("answer_evidence_ids", [])) - allowed:
                problems.append("ANSWER_SELF_AUTHORIZED_UNSHOWN_WITNESS")
            for f in facts:
                if set(f.get("witness_ids", [])) - allowed:
                    problems.append("FACT_CITES_UNPLANNED_WITNESS")
        if is_vague_statement(str(answer.get("CONSTRUCTION_EXPLANATION", ""))):
            problems.append("VAGUE_CONSTRUCTION_EXPLANATION")
        op = answer.get("ACTUAL_PRODUCING_OPERATION") or {}
        if q.owner_stage not in ("PROMPT_COMPILATION", "RENDER") and op.get("operation_id") not in registered_ops:
            problems.append("NO_REGISTERED_PRODUCING_OPERATION")
        if not answer.get("WHERE_IT_ENTERS_COMPILED_REQUEST"):
            problems.append("NO_COMPILED_REQUEST_ENTRY")
    ok = not problems
    return {"ok": ok, "problems": problems, "effective_status": status if ok else "UNKNOWN"}


def record_answer(q: NextQuestion, answer: dict, registered_ops: dict) -> NextQuestion:
    v = validate_answer(q, answer, registered_ops)
    q.answer_status = v["effective_status"]
    q.answer_evidence_ids = answer.get("answer_evidence_ids", [])
    q.answer_visible_relations = [f.get("relation") for f in answer.get("SOURCE_VISIBLE_FACTS", []) or []]
    q.condition_applicability_and_exceptions = [{"when": answer.get("WHEN_APPLICABLE"), "not_when": answer.get("WHEN_NOT_APPLICABLE")}]
    q.effect_on_skill_version_and_compiled_job = (str(answer.get("WHERE_IT_ENTERS_COMPILED_REQUEST")) if v["ok"]
                                                  else f"NONE — unresolved: {v['problems']}")
    return q


class LoopController:
    """Owns the ActiveArtProblem lifecycle; persists every version (store record type 'ActiveArtProblem')."""

    def __init__(self, store, ctx: ProblemContext):
        self.store = store
        self.ctx = ctx

    def save(self, p: ActiveArtProblem) -> None:
        self.store.put("ActiveArtProblem", p.cluster_id, p.to_dict())

    def load(self, cluster_id: str) -> ActiveArtProblem:
        d = self.store.get("ActiveArtProblem", cluster_id)
        if d is None:
            raise Blocked("NO_ACTIVE_PROBLEM", cluster_id)
        return ActiveArtProblem(**d)

    def step_question(self, p: ActiveArtProblem, gap_id: str) -> NextQuestion:
        q = derive_next_question(p, self.ctx, gap_id=gap_id)
        p.version += 1
        p.owner_stage = q.owner_stage
        if p.current_question_id_or_null:
            p.history.append({"question_id": p.current_question_id_or_null, "gap_id": gap_id})
        p.current_question_id_or_null = q.question_id
        p.next_action_and_exact_input = f"answer {q.question_id} using {q.planned_witness_or_input_ids[:3]}"
        self.store.put("NextQuestion", q.question_id, q.to_dict())
        self.save(p)
        return q

    def apply_answer(self, p: ActiveArtProblem, q: NextQuestion, answer: dict,
                     decision_writer: Callable[[NextQuestion, dict], dict | None]) -> dict:
        """Update the producing decision ONLY when the answer changes a concrete choice (§3.2 step 7)."""
        record_answer(q, answer, self.ctx.registered_operators)
        self.store.put("NextQuestion", q.question_id, q.to_dict())
        effect = {"question_id": q.question_id, "status": q.answer_status, "decision_changed": False, "route": q.route}
        if q.answer_status in ("OBSERVED", "INFERRED"):
            p.latest_confirmed_facts += [f for f in answer.get("SOURCE_VISIBLE_FACTS", [])]
            p.latest_unresolved_uncertainties = [u for u in p.latest_unresolved_uncertainties
                                                 if u.get("what") not in str(answer.get("SOURCE_VISIBLE_FACTS"))]
            if q.owner_stage in ("SOURCE_OBSERVATION",):
                p.latest_unresolved_uncertainties = [u for u in p.latest_unresolved_uncertainties
                                                     if u.get("kind") not in ("NOT_SEEN", "RESOLUTION_INSUFFICIENT")]
            if q.owner_stage == "CAUSE_INFERENCE":
                p.current_explanation_and_support.append({"claim": answer["CONSTRUCTION_EXPLANATION"],
                                                          "witness_ids": sorted({w for f in answer["SOURCE_VISIBLE_FACTS"] for w in f["witness_ids"]})})
            new_dec = decision_writer(q, answer) if q.route.startswith(("S2", "S3", "S4", "S1")) else None
            if new_dec is not None:
                self.ctx.decisions[new_dec["decision_id"]] = new_dec
                effect["decision_changed"] = True
                effect["decision_id"] = new_dec["decision_id"]
                effect["decision_version"] = new_dec.get("version")
            elif q.route.startswith("ENGINEERING"):
                effect["engineering_repair"] = answer.get("ACTUAL_PRODUCING_OPERATION")
        else:
            effect["unresolved"] = True
            effect["next_action"] = q.next_action_if_unresolved
            p.latest_unresolved_uncertainties.append({"kind": "UNANSWERED", "what": q.exact_artistic_unknown,
                                                      "question_id": q.question_id})
        p.version += 1
        self.save(p)
        self.store.put("AnswerEffect", q.question_id, effect)
        return effect

    def observe_new_output(self, p: ActiveArtProblem, review: dict) -> None:
        """A changed real/fixture output resets the evidence version; the next question derives from it (ADD26-Q05)."""
        p.original_output_id_or_initial_reference_only = review["output_id"]
        p.output_findings = review.get("findings", [])
        top = sorted(p.output_findings, key=lambda f: HANDOFF_ORDER.index(f.get("attributed_stage", "HUMAN_REVIEW")))
        if top:
            p.high_impact_visible_difference = top[0]["symptom"]
            if top[0].get("decision_id"):
                p.next_required_producer_decision_id = top[0]["decision_id"]
            if top[0].get("required_conditions"):
                p.required_conditions = top[0]["required_conditions"]
        p.source_evidence_version = digest({"prev": p.source_evidence_version, "output": review["output_id"]})[:16]
        self.ctx.output_review = review
        p.version += 1
        self.save(p)
