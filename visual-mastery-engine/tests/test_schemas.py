"""Real records conform to the spec schemas 02 (v1.2) and 21 (v1.3); mutations are rejected (structure only)."""
import json
from pathlib import Path

import jsonschema
import pytest

from conftest import ROOT, compile_job, offline_gateway
from vme.util import read_json
from vme.fixtures import loop_fixtures as fx
from vme.audit import contracts as K

SPEC = ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3"


@pytest.fixture(scope="module")
def s02():
    return read_json(SPEC / "02_DATA_SCHEMAS.json")


@pytest.fixture(scope="module")
def s21():
    return read_json(SPEC / "21_V13_TYPED_CONTRACTS.schema.json")


def _v(schema, rec):
    jsonschema.Draft202012Validator(schema).validate(rec)


@pytest.mark.req("C36", "B36", "A06")
def test_compile_gateway_records_validate_02_and_21(tmp_path, store, skill, brief, caps, s02, s21):
    j = compile_job(skill, brief, caps)
    g, _ = offline_gateway(store, tmp_path, caps)
    r = g.submit(j)
    refs = [x[1] for x in j.reference_images]
    for rec in (K.prompt_authority_trace(j.trace, j.logical_payload, refs), K.provider_call(r, brief["brief_id"], j.logical_payload)):
        _v(s02, rec)
    for rec in (K.prompt_trace(j.trace, j.logical_payload, refs), K.raster_asset(r["outputs"][0])):
        _v(s21, rec)
    folder, _ = skill
    for n in read_json(folder / "recipes" / "character_world.json")["nodes"]:
        _v(s21, K.operation_node(n))
    for c in read_json(folder / "prompt_templates" / "whole_scene.json")["clauses"]:
        _v(s21, K.skill_clause(c))
    bad = K.prompt_authority_trace(j.trace, j.logical_payload, refs)
    bad["record"]["runtime_style_invention_prohibited"] = False
    with pytest.raises(jsonschema.ValidationError):
        _v(s02, bad)


@pytest.mark.req("C36")
def test_decision_character_question_records_validate(store, s02, s21):
    from vme.style.decisions import witness_to_decision
    from vme.skills.operators import registered
    from vme.artwork.character import derive_animation_demand, character_construction_plan
    from vme.investigation.controller import ActiveArtProblem, derive_next_question, ProblemContext
    d = witness_to_decision(fx.synthetic_bundle(), fx.face_view_proposal_from_answer({}), registered_operators=registered(),
                            substitutes=[{"noun": "robot", "subject_kind": "machine"}, {"noun": "eel", "subject_kind": "creature"}]).to_dict()
    _v(s02, K.conditional_style_decision(d, "character_world"))
    _v(s21, K.style_decision(d))
    plan = character_construction_plan("explorer", "B", "h" * 8, derive_animation_demand("explorer", fx.synthetic_shot_actions()))
    _v(s02, K.character_construction_plan(plan))
    _v(s21, K.character_plan(plan, "explorer:canonical"))
    q = derive_next_question(ActiveArtProblem(**fx.synthetic_problem()),
                             ProblemContext(witnesses=fx.synthetic_witnesses(), registered_operators=registered()), gap_id="g")
    _v(s21, K.question_trace(q.to_dict()))
    w = fx.synthetic_witnesses()["W-SYN-A01"]
    _v(s21, K.frame_witness(w, "a" * 64))
    bad = K.style_decision(d)
    del bad["data"]["exceptions"]
    with pytest.raises(jsonschema.ValidationError):
        _v(s21, bad)


@pytest.mark.req("C36", "A47")
def test_gate_approval_review_checkpoint_records_validate(ws, indexed24, s02, s21, tmp_path):
    from vme.review.approvals import GateKeeper, FIXTURE_SIGNER, save_user_review
    from vme.vision.providers import MockVisionProvider
    from vme.vision.runner import PacketRunner, plan_packets
    from PIL import Image
    st = ws.store()
    gk = GateKeeper(st)
    gk.transition("R", "ART_GENERATING", synthetic=True)
    gk.transition("R", "AWAITING_ARTWORK_REVIEW")
    img = tmp_path / "i.png"
    Image.new("RGB", (8, 8)).save(img)
    a = gk.submit_art_verdict("R", image_paths=[str(img)], brief_id="b", skill_versions=["s"], verdict="APPROVED", defects=[], signed_by=FIXTURE_SIGNER)
    _v(s02, K.art_approval(a))
    _v(s02, K.visual_gate_state(gk.state("R")))
    rv = save_user_review(st, run_id="R", verdict="PARTIAL", top_remaining_gaps=["hands"], preferred_next_focus="hands", submitted_by="u",
                          linked_image_hashes=[])
    _v(s02, K.visual_review(rv))
    clip, idx, loader = indexed24
    plans = plan_packets(idx, 0, 7, film_sha=idx[0]["film_sha256"], pass_id="p", cluster_id="c", model_version="m", max_images=12)
    pr = PacketRunner(st, ws.vision_dir, idx, loader, MockVisionProvider(ws.root / "r"), source_is_synthetic=True,
                      active_questions=[{"question_id": "Q1", "text": "S"}])
    pr.run(plans[0])
    ck = st.get("SemanticPacketCheckpoint", plans[0].packet_id)
    _v(s02, K.semantic_packet_checkpoint(ck))
    _v(s21, K.semantic_checkpoint(ck, json.loads(Path(ck["boundary_state_path"]).read_text())))
    st.close()


@pytest.mark.req("A26", "C36")
def test_real_frame_coverage_ledger_validates_02(s02):
    p = ROOT / "workspace" / "state" / "FRAME_INDEX_SUMMARY.json"
    if not p.exists():
        pytest.skip("real index absent")
    for f in read_json(p)["films"]:
        _v(s02, K.frame_coverage_ledger(f, {"VISION_OUTPUT_VERIFIED": 0}))
