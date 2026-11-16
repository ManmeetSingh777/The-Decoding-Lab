"""Gap ranking, connected clusters and the dynamic ONE-next-question controller
(A08–A10, B09, B12, B13, B31, C06–C08, C30, ADD25-Q01, ADD25-Q05, ADD26-Q01..Q06, ADD26-I01)."""

import pytest

from vme.util import Blocked
from vme.fixtures import loop_fixtures as fx
from vme.investigation.controller import (ActiveArtProblem, LoopController, ProblemContext, derive_next_question,
                                          reject_question_list, validate_answer, select_evidence, LITERAL_Q_STEMS)
from vme.skills.operators import registered


def _ctx(decisions=None, **kw):
    return ProblemContext(bundles={"WB": fx.synthetic_bundle().to_dict()}, witnesses=fx.synthetic_witnesses(),
                          decisions=decisions or {}, registered_operators=registered(),
                          provider_capabilities=["whole_scene", "canonical_character", "guided_pose_edit"], **kw)


@pytest.mark.req("A08", "C06")
def test_multi_gap_ranking_with_written_pairwise_reasons():
    from vme.investigation.gaps import rank_gaps
    r = rank_gaps(fx.synthetic_gaps())
    assert r["status"] == "RANKED" and r["ranked_ids"][0] == "G-SYN-FACE" and r["ranked_ids"][-1] == "G-SYN-MICRO"
    assert all(p["because"] for p in r["pairwise"])
    g = fx.synthetic_gaps()[:1] + [dict(fx.synthetic_gaps()[1], visual_symptom="needs polish")]
    assert rank_gaps(g)["status"] == "INSUFFICIENT_GAPS"  # generic 'needs polish' rejected


@pytest.mark.req("A09", "B12", "C30")
def test_connected_cluster_first_iteration_character_world_view():
    from vme.investigation.gaps import rank_gaps, select_cluster
    gaps = fx.synthetic_gaps()
    c = select_cluster(gaps, rank_gaps(gaps)["ranked_ids"], first_iteration=True)
    assert c["status"] == "CLUSTER_SELECTED" and 2 <= len(c["cluster_gap_ids"]) <= 5
    assert "G-SYN-MICRO" in c["excluded_queue"] and c["dependency_links"]
    with pytest.raises(Blocked):
        select_cluster(gaps, rank_gaps(gaps)["ranked_ids"], first_iteration=True, user_override={"gap_id": "G-SYN-MICRO"})


@pytest.mark.req("ADD26-Q01", "ADD25-Q01", "B09", "C08")
def test_question_derived_from_problem_not_literal_questionnaire():
    p = ActiveArtProblem(**fx.synthetic_problem())
    q = derive_next_question(p, _ctx(), gap_id="G-SYN-FACE")
    low = q.question_text.lower()
    assert not any(low.startswith(s) for s in LITERAL_Q_STEMS)
    assert "d-syn-face-view" in low and "w-syn-a01" in low
    assert q.owner_stage == "SOURCE_OBSERVATION" and len(q.possible_answer_consequences_for_operation) >= 2
    assert set(q.reasoning_dimensions) == {"Q0_result", "Q1_relations", "Q2_causal_importance", "Q3_contrast",
                                           "Q4_new_subject_decision", "Q5_remaining_style_ambiguity", "Q6_operation", "Q7_proof"}


@pytest.mark.req("ADD26-Q02")
def test_question_list_theatre_refused():
    p = ActiveArtProblem(**fx.synthetic_problem())
    q1 = derive_next_question(p, _ctx(), gap_id="g")
    q2 = derive_next_question(p, _ctx(), gap_id="g")
    with pytest.raises(Blocked) as e:
        reject_question_list([q1, q2])
    assert e.value.code == "QUESTION_LIST_THEATRE"


@pytest.mark.req("ADD26-Q03")
def test_broken_compile_routes_to_compiler_repair_not_film_reanalysis():
    pd = fx.synthetic_problem()
    pd["latest_unresolved_uncertainties"] = []
    pd["current_explanation_and_support"] = [{"claim": "x", "witness_ids": ["W-SYN-A01"]}]
    dec = fx.face_view_proposal_from_answer({})
    dec["status"] = "EXECUTABLE_CANDIDATE"
    ctx = _ctx({"D-SYN-FACE-VIEW": dec}, compile_trace={"selected_decisions": ["D-SYN-WORLD"], "skill_present_but_not_compiled": ["D-SYN-FACE-VIEW"]})
    q = derive_next_question(ActiveArtProblem(**pd), ctx, gap_id="g")
    assert q.owner_stage == "PROMPT_COMPILATION" and q.route == "ENGINEERING_REPAIR_COMPILER"
    ev = select_evidence(q, {"film_frame": {"kind": "FULL_FRAME"}, "trace": {"kind": "COMPILE_TRACE"}})
    assert ev == ["trace"]


@pytest.mark.req("ADD26-Q04", "ADD26-P03")
def test_face_turn_condition_question_is_actor_view_specific():
    pd = fx.synthetic_problem()
    pd["latest_unresolved_uncertainties"] = []
    pd["current_explanation_and_support"] = [{"claim": "redraw", "witness_ids": ["W-SYN-A02"]}]
    pd["required_conditions"] = {"view": "profile"}
    dec = fx.face_view_proposal_from_answer({})
    q = derive_next_question(ActiveArtProblem(**pd), _ctx({"D-SYN-FACE-VIEW": dec}), gap_id="g")
    assert q.owner_stage == "STYLE_CONDITIONS" and "view=profile" in q.question_text
    assert "eyebrow" not in q.question_text.lower() and "palette" not in q.question_text.lower()


@pytest.mark.req("ADD26-Q05", "ADD26-I01")
def test_new_output_gap_yields_different_question(store):
    pd = fx.synthetic_problem()
    pd["latest_unresolved_uncertainties"] = []
    pd["current_explanation_and_support"] = [{"claim": "redraw", "witness_ids": ["W-SYN-A02"]}]
    dec = fx.face_view_proposal_from_answer({})
    dec["status"] = "EXECUTABLE_CANDIDATE"
    ctx = _ctx({"D-SYN-FACE-VIEW": dec}, compile_trace={"selected_decisions": ["D-SYN-FACE-VIEW"], "skill_present_but_not_compiled": []})
    lc = LoopController(store, ctx)
    p = ActiveArtProblem(**pd)
    q1 = lc.step_question(p, gap_id="g1")
    assert q1.owner_stage == "PROVIDER_RESULT"   # compiled correctly, no output yet
    lc.observe_new_output(p, {"output_id": "OUT-1", "findings": [
        {"symptom": "identity drifts: canonical face redrawn as a different actor in the 3/4 state",
         "attributed_stage": "PROVIDER_RESULT", "decision_id": "D-SYN-FACE-VIEW", "output_id": "OUT-1"}]})
    q2 = lc.step_question(p, gap_id="g2")
    assert q2.owner_stage == "PROVIDER_RESULT" and q2.question_text != q1.question_text
    assert "identity drifts" in q2.question_text and q2.route == "S4S5_PROVIDER_ROUTE"
    lc.observe_new_output(p, {"output_id": "OUT-2", "findings": [
        {"symptom": "hand floats beside handle", "attributed_stage": "STYLE_CONDITIONS", "decision_id": "D-SYN-GRIP",
         "required_conditions": {"action": "grip"}}]})
    q3 = lc.step_question(p, gap_id="g3")
    assert q3.missing_decision_id == "D-SYN-GRIP" and q3.question_text not in (q1.question_text, q2.question_text)


@pytest.mark.req("ADD26-Q06", "C07", "A10")
def test_vague_answer_keeps_decision_unresolved(store):
    p = ActiveArtProblem(**fx.synthetic_problem())
    lc = LoopController(store, _ctx())
    q = lc.step_question(p, gap_id="g")
    vague = {**fx.fixture_answer(q), "CONSTRUCTION_EXPLANATION": "more details and vibrant colours"}
    eff = lc.apply_answer(p, q, vague, decision_writer=lambda *_: None)
    assert eff["status"] == "UNKNOWN" and eff["unresolved"] and not eff["decision_changed"]
    good = fx.fixture_answer(q)
    v = validate_answer(q, good, registered())
    assert v["ok"]
    bad_op = {**good, "ACTUAL_PRODUCING_OPERATION": {"operation_id": "op.make_beautiful_art"}}
    assert "NO_REGISTERED_PRODUCING_OPERATION" in validate_answer(q, bad_op, registered())["problems"]


@pytest.mark.req("B13", "ADD25-Q05", "B31")
def test_sequential_questions_change_stage_as_handoffs_fill(store):
    """Each answer updates the problem; the next question targets the next missing handoff (no reuse)."""
    p = ActiveArtProblem(**fx.synthetic_problem())
    ctx = _ctx()
    lc = LoopController(store, ctx)
    stages, texts = [], []
    from vme.style.decisions import witness_to_decision

    def writer(q, a):
        if q.owner_stage != "STYLE_CONDITIONS":
            return None
        return witness_to_decision(fx.synthetic_bundle(), fx.face_view_proposal_from_answer(a), registered_operators=registered(),
                                   substitutes=[{"noun": "robot", "subject_kind": "machine"}, {"noun": "eel", "subject_kind": "creature"}]).to_dict()
    for _ in range(4):
        q = lc.step_question(p, gap_id="G")
        stages.append(q.owner_stage)
        texts.append(q.question_text)
        if q.owner_stage == "PROMPT_COMPILATION":
            break
        lc.apply_answer(p, q, fx.fixture_answer(q), decision_writer=writer)
    assert stages == ["SOURCE_OBSERVATION", "CAUSE_INFERENCE", "STYLE_CONDITIONS", "PROMPT_COMPILATION"]
    assert len(set(texts)) == 4
    stored = store.versions("ActiveArtProblem", "CL-SYN-01")
    assert len(stored) >= 5  # every step persisted


@pytest.mark.req("ADD26-Q01")
def test_literal_q_stem_question_rejected():
    from vme.investigation.controller import NextQuestion, check_question_quality
    q = NextQuestion("q", "c", "e", "g", "D", "op", ["W"], "u", "What is the observable high-impact result?", [], [{}, {}],
                     "S1", "SOURCE_OBSERVATION", {}, [])
    with pytest.raises(Blocked) as e:
        check_question_quality(q, _ctx())
    assert e.value.code == "FIXED_QUESTIONNAIRE_REJECTED"
