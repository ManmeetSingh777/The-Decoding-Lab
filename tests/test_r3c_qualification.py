"""R3-C10 sufficiency + visual qualification, R3-C11 separate readiness stages."""
from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from vme.util import Blocked


@pytest.mark.req("R3-C10")
def test_one_witnessed_overlap_is_not_a_whole_illustration_specification():
    from vme.vision.protocol import assess_sufficiency
    one = {"answer_status": "OBSERVED", "SOURCE_VISIBLE_FACTS": [{"relation": "Red body is in front of blue body near the lower left", "witness_ids": ["W1"]}],
           "CONSTRUCTION_EXPLANATION": "The visible overlap indicates one drawing occludes another here",
           "BRANCHES": [{"operation_id": "op.whole_scene", "construction_action": "Draw red in front of blue to express the overlap"}]}
    v = assess_sufficiency(one, producing_operator="op.whole_scene", known_witness_ids={"W1"})
    assert v["verdict"] == "INSUFFICIENT_FOR_PRODUCING_CHOICE"
    assert {"WHOLE_ILLUSTRATION_NEEDS_MULTIPLE_WITNESSED_RELATIONS", "NO_APPLICABILITY_LIMITS_OR_EXCEPTIONS",
            "CONSTRUCTION_ACTION_NOT_CONSTRUCTION_GRADE"} <= set(v["reasons"])
    # the same single fact may still be an authentic NARROW rule for a local operator
    narrow = dict(one, BRANCHES=[{"operation_id": "op.region_edit", "construction_action": "Draw red in front of blue to express the overlap"}])
    assert assess_sufficiency(narrow, producing_operator="op.region_edit", known_witness_ids={"W1"})["verdict"] == "SUFFICIENT_FOR_PRODUCING_CHOICE"
    full = dict(one, SOURCE_VISIBLE_FACTS=one["SOURCE_VISIBLE_FACTS"] + [{"relation": "in W2 the blue body stays behind the red contour while the floor recedes",
                                                                           "witness_ids": ["W2"]}],
                WHEN_NOT_APPLICABLE=["diagram frames with flat labels"],
                BRANCHES=[{"operation_id": "op.whole_scene", "construction_action":
                           "draw the {subject} as the near mass overlapping the far mass with its contour unbroken and the floor receding behind both"}])
    assert assess_sufficiency(full, producing_operator="op.whole_scene", known_witness_ids={"W1", "W2"})["verdict"] == "SUFFICIENT_FOR_PRODUCING_CHOICE"


def _img(box=None, col=(200, 40, 40)):
    im = Image.new("RGB", (200, 120), (30, 30, 60))
    if box:
        ImageDraw.Draw(im).rectangle(box, fill=col)
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


@pytest.mark.req("R3-C10")
def test_ablation_must_change_the_declared_region_and_leave_the_rest_stable(store):
    from vme.review.visual_qualification import qualify_branch_output
    region = {"x": 40, "y": 30, "w": 60, "h": 50}
    q = qualify_branch_output(store, decision_id="PC-1", branch_when={"view": "front"}, region=region, output_png=_img((50, 40, 90, 70)),
                              ablated_png=_img(), output_label="SIMULATED_TRANSPORT_FIXTURE_IMAGE", evidence_origin="SIMULATED_VLM_TRANSPORT",
                              expected_change="the near hand mass appears over the handle inside the grip region")
    assert q["status"] == "VISUAL_EFFECT_EXHIBITED" and not q["transfer_eligible"]
    leak = qualify_branch_output(store, decision_id="PC-1", branch_when={"view": "front"}, region=region, output_png=_img((0, 0, 199, 119)),
                                 ablated_png=_img(), output_label="REAL_PROVIDER_OUTPUT", evidence_origin="REAL_VLM",
                                 expected_change="the near hand mass appears over the handle inside the grip region")
    assert leak["status"] == "EFFECT_LEAKS_OUTSIDE_REGION"
    none = qualify_branch_output(store, decision_id="PC-1", branch_when={}, region=region, output_png=_img(), ablated_png=_img(),
                                 output_label="REAL_PROVIDER_OUTPUT", evidence_origin="REAL_VLM",
                                 expected_change="the near hand mass appears over the handle")
    assert none["status"] == "NO_VISIBLE_EFFECT"


@pytest.mark.req("R3-C10")
def test_human_approval_needs_a_measured_effect_on_real_output_and_a_human(store):
    from vme.review.visual_qualification import qualify_branch_output, human_visual_verdict
    region = {"x": 40, "y": 30, "w": 60, "h": 50}
    sim = qualify_branch_output(store, decision_id="PC-1", branch_when={}, region=region, output_png=_img((50, 40, 90, 70)), ablated_png=_img(),
                                output_label="SIMULATED_TRANSPORT_FIXTURE_IMAGE", evidence_origin="SIMULATED_VLM_TRANSPORT",
                                expected_change="the near hand mass appears over the handle")
    with pytest.raises(Blocked) as e:
        human_visual_verdict(store, sim["qualification_id"], verdict="APPROVED", by="Reviewer A", statement="looks right")
    assert e.value.code == "SIMULATED_OUTPUT_CANNOT_QUALIFY"
    real = qualify_branch_output(store, decision_id="PC-2", branch_when={}, region=region, output_png=_img((50, 40, 90, 70)), ablated_png=_img(),
                                 output_label="REAL_PROVIDER_OUTPUT", evidence_origin="REAL_VLM", expected_change="the near hand mass appears over the handle")
    with pytest.raises(Blocked) as e:
        human_visual_verdict(store, real["qualification_id"], verdict="APPROVED", by="claude", statement="self-attested")
    assert e.value.code == "HUMAN_SIGNER_REQUIRED"
    ok = human_visual_verdict(store, real["qualification_id"], verdict="APPROVED", by="Reviewer A", statement="grip reads as designed")
    assert ok["status"] == "HUMAN_VISUALLY_APPROVED"
    with pytest.raises(Blocked) as e:
        qualify_branch_output(store, decision_id="PC-3", branch_when={}, region=region, output_png=_img(), ablated_png=_img(),
                              output_label="REAL_PROVIDER_OUTPUT", evidence_origin="REAL_VLM", expected_change="")
    assert e.value.code == "EXPECTED_VISIBLE_CHANGE_NOT_PREDICTED"


@pytest.mark.req("R3-C11")
def test_readiness_stages_are_separate_and_never_inferred(store):
    from vme.review.qualification import readiness_report, READINESS_STAGES
    eng = {"repo_suite_failed": 0, "fresh_suite_failed": 0, "mutants_survived": 0, "red_before_closed": True, "static_clean": True}
    r = readiness_report(store, engineering=eng)
    assert list(r["stages"]) == list(READINESS_STAGES)
    assert r["stages"]["ENGINEERING_READY_FOR_SOURCE_CALIBRATION"] == "PASS"
    assert r["stages"]["SOURCE_INVESTIGATION_COMPLETED_AND_REVIEWED"] == "BLOCKED:AWAITING_AUTHORIZED_SOURCE_TRANSFER"
    assert r["stages"]["SKILLS_ORIGINAL_TRIAL_PROVEN"] == "NOT_MET" and r["stages"]["HELDOUT_ORIGINAL_AV_QUALIFIED"] == "NOT_MET"
    assert r["ready_for_15_plus_1"] is False
    store.put("SourceArtLedger", "REAL-CANARY", {"run_id": "REAL-CANARY", "scenes": [{"source_art_truth": "SOURCE_ART_REVIEWED"}],
                                                 "complete_for_promotion": True})
    assert readiness_report(store, engineering=eng)["stages"]["SOURCE_INVESTIGATION_COMPLETED_AND_REVIEWED"] != "PASS"   # drills never count
    bad = readiness_report(store, engineering={**eng, "fresh_suite_failed": 1})
    assert bad["stages"]["ENGINEERING_READY_FOR_SOURCE_CALIBRATION"] == "FAIL"
