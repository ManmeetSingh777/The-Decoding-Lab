"""Source fact vs transferable conditional style decision (A30–A32, A49–A52, B10, B11, B14, B15, C09–C12,
ADD25-Q02..Q04, ADD26-S01/S02, ADD26-D05, ADD26-F03/F04)."""

import pytest

from vme.util import Blocked
from vme.fixtures import loop_fixtures as fx
from vme.skills.operators import registered
from vme.style.decisions import witness_to_decision, classify_statement, transfer_status

SUBS = [{"noun": "robot engineer", "subject_kind": "machine"}, {"noun": "tidal creature", "subject_kind": "creature"}]


def _prop(**over):
    p = fx.face_view_proposal_from_answer({})
    p.update(over)
    return p


@pytest.mark.req("A49", "A30", "B10", "C09", "ADD25-Q03", "ADD26-S01")
def test_source_specific_facts_demoted_to_scene_fact():
    assert classify_statement("every new actor wears an orange jacket with five buttons", ["source actor wears an orange jacket with five buttons"]) == "SCENE_FACT"
    assert classify_statement("head to body ratio 1:2.5 for all actors", []) == "SCENE_FACT"
    p = _prop(invariant_visual_relation="draw every new creature with exactly six legs like the source creature")
    with pytest.raises(Blocked) as e:
        witness_to_decision(fx.synthetic_bundle(), p, registered_operators=registered(), substitutes=SUBS)
    assert e.value.code == "SCENE_FACT_NOT_STYLE"


@pytest.mark.req("ADD26-D05")
def test_brand_logo_never_a_transferable_rule():
    p = _prop(invariant_visual_relation="always reveal the brand Earth logo after a volcano scene")
    with pytest.raises(Blocked) as e:
        witness_to_decision(fx.synthetic_bundle(), p, registered_operators=registered(), substitutes=SUBS)
    assert e.value.code == "SCENE_FACT_NOT_STYLE"


@pytest.mark.req("A50", "C07", "B09")
def test_adjective_only_decision_is_vague():
    p = _prop(invariant_visual_relation="polished rich beautiful vibrant", branches=[dict(_prop()["branches"][0], construction_action="nice")],
              expected_visible_effect="stunning")
    with pytest.raises(Blocked) as e:
        witness_to_decision(fx.synthetic_bundle(), p, registered_operators=registered(), substitutes=SUBS)
    assert e.value.code == "VAGUE_STYLE_DECISION"


@pytest.mark.req("A51", "A31", "C10", "B14")
def test_conditions_exceptions_adaptations_required():
    d = witness_to_decision(fx.synthetic_bundle(), _prop(), registered_operators=registered(), substitutes=SUBS)
    assert d.status == "EXECUTABLE_CANDIDATE" and d.evidence_scope == "CROSS_FILM_CROSS_SUBJECT"
    assert all(b["when"] for b in d.branches) and d.exceptions and d.adaptive_visual_choices
    assert "orange jacket" in " ".join(d.forbidden_source_specific_copies)
    d2 = witness_to_decision(fx.synthetic_bundle(), _prop(exceptions=[]), registered_operators=registered(), substitutes=SUBS)
    assert d2.status == "RESEARCH_ONLY" and d2.research_only_reason == "MISSING_EXCEPTIONS_OR_ADAPTATIONS"
    br = [dict(b, when={}) for b in _prop()["branches"]]
    d3 = witness_to_decision(fx.synthetic_bundle(), _prop(branches=br), registered_operators=registered(), substitutes=SUBS)
    assert d3.research_only_reason == "MISSING_CONDITIONS"


@pytest.mark.req("B15", "ADD25-Q04", "ADD26-S02", "C12")
def test_no_registered_operation_stays_research_only():
    br = [dict(b, operation_node_ids=["op.make_kz_style"]) for b in _prop()["branches"]]
    d = witness_to_decision(fx.synthetic_bundle(), _prop(branches=br), registered_operators=registered(), substitutes=SUBS)
    assert d.status == "RESEARCH_ONLY" and d.research_only_reason == "NO_REGISTERED_PRODUCING_OPERATION"


@pytest.mark.req("B11", "ADD25-Q02")
def test_single_source_example_stays_conditional_candidate():
    from vme.investigation.evidence import WitnessBundle
    w = fx.synthetic_witnesses()
    b = WitnessBundle("WB1", None, "x", [w["W-SYN-A01"], w["W-SYN-A02"], w["W-SYN-A03"]])
    d = witness_to_decision(b, _prop(), registered_operators=registered(), substitutes=SUBS).to_dict()
    assert d["evidence_scope"] == "SINGLE_SOURCE_LEAD"
    assert transfer_status(d) == "CONDITIONAL_CANDIDATE_LIMITED_SCOPE"


@pytest.mark.req("A52", "C11")
def test_substitution_challenge_requires_two_unlike_subjects():
    with pytest.raises(Blocked) as e:
        witness_to_decision(fx.synthetic_bundle(), _prop(), registered_operators=registered(),
                            substitutes=[{"noun": "a", "subject_kind": "biped"}, {"noun": "b", "subject_kind": "biped"}])
    assert e.value.code == "SUBSTITUTION_CHALLENGE_NEEDS_TWO_UNLIKE_SUBJECTS"
    d = witness_to_decision(fx.synthetic_bundle(), _prop(), registered_operators=registered(), substitutes=SUBS)
    assert len(d.substitution_challenge) == 2 and all(c["verdict"] == "STYLE_CANDIDATE" for c in d.substitution_challenge)


@pytest.mark.req("ADD26-F03")
def test_native_crop_without_full_frame_context_invalid():
    from vme.investigation.evidence import WitnessBundle, validate_bundle
    w = fx.synthetic_witnesses()
    crop = dict(w["W-SYN-A03"], parent_full_frame_witness=None, temporal_neighbor_witnesses=[])
    v = validate_bundle(WitnessBundle("b", None, "x", [crop]))
    assert not v["ok"] and any(p.startswith("CROP_WITHOUT_FULL_FRAME_CONTEXT") for p in v["problems"])
    assert "NO_WHOLE_FRAME_WITNESS" in v["problems"]


@pytest.mark.req("ADD26-F04")
def test_camera_vs_redraw_ambiguity_blocks_motion_skill():
    from vme.investigation.evidence import camera_attribution_guard
    with pytest.raises(Blocked):
        camera_attribution_guard({"changes": [{"kind": "INFERRED_CAMERA"}, {"kind": "INFERRED_NEW_DRAWING"}]})
    with pytest.raises(Blocked):
        camera_attribution_guard({"asserted_cause": "CAMERA_ONLY", "changes": [{"kind": "INFERRED_NEW_DRAWING"}]})


@pytest.mark.req("A32", phase="ART")
def test_originality_requires_real_distinct_outputs_blocked_offline(skill, caps):
    """Two unlike briefs compile to different content with the same governed grammar; visual originality
    vs. cloning can only be judged on real provider outputs (ART phase)."""
    from conftest import compile_job
    a = compile_job(skill, fx.synthetic_brief(), caps)
    b = compile_job(skill, fx.holdout_brief(), caps)
    assert a.logical_payload["positivePrompt"] != b.logical_payload["positivePrompt"]
    assert set(a.trace["selected_decisions"]) == set(b.trace["selected_decisions"])
    assert a.trace["selected_branches"]["D-SYN-CHAR-WHOLE"] != b.trace["selected_branches"]["D-SYN-CHAR-WHOLE"]
