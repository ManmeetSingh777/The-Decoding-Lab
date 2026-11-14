"""Addendum 27: coverage ledger, completeness investigator, reverse planner, provenance interfaces I/II/III
(ADD27-1..ADD27-14)."""
import copy
import json
import os
import subprocess
import sys

import pytest

from conftest import ROOT, compile_job
from vme.util import Blocked, read_json
from vme.fixtures import loop_fixtures as fx
from vme.skills.operators import registered
from vme.style.coverage import (review_visual_model_completeness, OriginalScope, set_dimension, new_ledger, DIMENSIONS)
from vme.style.provenance import interface_one_gate, interface_three_attribution, ProvenanceGraph, ProvenanceNode


def _decisions(**kw):
    return fx.synthetic_decisions(**{"face_light_joint": True, "grip_light_joint": True, **kw})


@pytest.mark.req("ADD27-1", "ADD27-2")
def test_complete_fixture_ready_for_trial_with_honest_labels():
    L, scope = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, scope, _decisions(), registered())
    assert r["review"]["state"] == "READY_FOR_ORIGINAL_IMAGE_TRIAL" and r["review"]["image_trial_ready"]
    assert r["artistic_quality"] == "ARTISTIC_QUALITY_UNPROVEN" and r["scope_claim"] == "SCOPE_COVERED_WITH_KNOWN_LIMITS"


@pytest.mark.req("ADD27-3", "ADD27-4")
def test_missing_face_viewpoint_rule_found_and_one_question_routed():
    L, scope = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, scope, _decisions(include_face=False), registered())
    assert r["review"]["state"] == "BLOCKED_MISSING_STYLE_DECISION"
    assert any("CHARACTER_FACE_ACTING" in g["dimensions"] for g in r["gap_details"])
    assert len(r["gap_details"]) > 1 and r["question_ticket"] and r["question_ticket"]["blocking_gap_id"] == r["controlling_gap"]["gap_id"]


@pytest.mark.req("ADD27-5")
def test_individually_supported_but_missing_face_view_light_link_rejected():
    """27_WORKED_EXAMPLE C: face, viewpoint and light each supported, but no joint decision → materially incomplete."""
    L, scope = fx.complete_ledger_and_scope(lighting="directional")
    r = review_visual_model_completeness(L, scope, _decisions(face_light_joint=False), registered())
    joint = [g for g in r["gap_details"] if g["kind"] == "MISSING_JOINT_DECISION" and "face+view+light" in g.get("joint_id", "")]
    assert joint and joint[0]["individually_supported"] and r["review"]["state"] == "BLOCKED_MISSING_STYLE_DECISION"
    t = r["question_ticket"]
    assert "TOGETHER" in t["actual_question"] and "CHARACTER_FACE_ACTING" in t["actual_question"]


@pytest.mark.req("ADD27-5")
def test_character_pose_contact_and_lighting_world_unlinked_rejected():
    L, scope = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, scope, _decisions(grip_light_joint=False), registered())
    assert any(g.get("joint_id", "").endswith("contact+light") for g in r["gap_details"])
    assert not r["review"]["image_trial_ready"]


@pytest.mark.req("ADD27-4")
def test_colour_present_but_world_light_link_missing_and_disconnected_world_camera():
    L, scope = fx.complete_ledger_and_scope()
    L["relations"] = [x for x in L["relations"] if x["relation_id"] != "world_layers+viewpoint"]
    r = review_visual_model_completeness(L, scope, _decisions(), registered())
    assert any(g.get("joint_id") == "world_layers+viewpoint" for g in r["gap_details"])
    scope2 = OriginalScope("S2", subjects=scope.subjects, world=scope.world, camera={"moves": ["push"], "scale_change": True})
    L2, _ = fx.complete_ledger_and_scope()
    r2 = review_visual_model_completeness(L2, scope2, _decisions(), registered())
    assert any(g.get("joint_id") == "camera+art_states" for g in r2["gap_details"])


@pytest.mark.req("ADD27-10")
def test_unexpected_phenomenon_becomes_dynamic_extension():
    L, scope = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, scope, _decisions(), registered(), unexplained_phenomena=[
        {"phenomenon": "ink-bleed reveal transition", "why": "frames show a wipe drawn as spreading ink", "connected": ["TRANSITIONS_VISUAL_GRAMMAR"]}])
    ext = [e["dimension"] for e in L["extensions"]]
    assert "EXT_INK_BLEED_REVEAL_TRANSITION" in ext and not r["review"]["image_trial_ready"]
    assert all(e not in DIMENSIONS for e in ext)


@pytest.mark.req("ADD27-5")
def test_all_eighteen_not_applicable_contradicts_scope():
    L = new_ledger("S", ["x"])
    L["frame_coverage_state"] = "ALL_TARGET_FRAMES_SEEN"
    for d in DIMENSIONS:
        set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=[], why_relevant="none", inapplicability_reason="claimed absent")
    _, scope = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, scope, _decisions(), registered())
    assert r["review"]["state"] == "BLOCKED_MISSING_SOURCE" and any(g["kind"] == "CONTRADICTED" for g in r["gap_details"])
    with pytest.raises(Blocked):
        set_dimension(L, "WORLD_ASSEMBLY", "NOT_APPLICABLE_WITH_REASON", evidence=[], why_relevant="x")


@pytest.mark.req("ADD27-3")
def test_fixing_one_gap_uncovers_next_review_repeats():
    L, scope = fx.complete_ledger_and_scope()
    decs = _decisions(include_face=False, grip_light_joint=False)
    r1 = review_visual_model_completeness(L, scope, decs, registered())
    first = r1["controlling_gap"]
    decs2 = _decisions(grip_light_joint=False)  # face decision added
    r2 = review_visual_model_completeness(L, scope, decs2, registered())
    assert not r2["review"]["image_trial_ready"] and r2["controlling_gap"]["what"] != first["what"]
    r3 = review_visual_model_completeness(L, scope, _decisions(), registered())
    assert r3["review"]["image_trial_ready"]


@pytest.mark.req("ADD27-6", "ADD27-11")
def test_model_authored_clause_blocked_at_observation_to_skill_boundary(tmp_path):
    from vme.fixtures.synthetic import build_synthetic_skill
    from vme.skills.skill import freeze_skill
    bad = {"id": "K-SYN-EYES-99", "decision_id": "D-SYN-FACE-VIEW", "priority": 5,
           "template": "metallic teal eyes with tiny diamond-shaped sparkles", "allowed_content_slots": [], "reference_roles": [],
           "operation_id": "op.face_view_state", "origin_type": "CROSS_SOURCE_INFERRED"}   # falsely claims inference
    f = tmp_path / "sk"
    build_synthetic_skill(f, extra_clause=bad)
    with pytest.raises(Blocked) as e:
        freeze_skill(f, observed_relations=fx.OBSERVED_RELATIONS, approved_by="reviewer")
    rep = e.value.data["report"]
    a = next(x for x in rep["clause_audits"] if x["clause_id"].startswith("K-SYN-EYES-99"))
    assert a["verdict"] == "RESEARCH_ONLY" and a["classified_origin"] == "MODEL_SUGGESTED_UNVERIFIED"
    assert "CLAUSE_TERMS_NOT_DERIVED_FROM_OBSERVATION" in a["reasons"]
    assert (f / "FREEZE_REFUSAL.json").exists() and not (f / "FROZEN.json").exists()


@pytest.mark.req("ADD27-6")
def test_declared_model_suggested_origin_never_freezable():
    c = {"id": "k", "decision_id": "D", "template": "near and far facial features redrawn together", "origin_type": "MODEL_SUGGESTED_UNVERIFIED"}
    d = {"decision_id": "D", "observed_relation_ids": ["R-SYN-02"], "branches": []}
    assert interface_one_gate(c, d, fx.OBSERVED_RELATIONS)["verdict"] == "RESEARCH_ONLY"


@pytest.mark.req("ADD27-7", "ADD27-9")
def test_skill_to_payload_authority_every_field_classified(skill, brief, caps):
    from vme.style.provenance import interface_two_audit
    j = compile_job(skill, brief, caps)
    ok = interface_two_audit(j.logical_payload, j.trace["field_ownership"], j.trace["segments"])
    assert ok["ok"]
    p2 = dict(j.logical_payload, CFGScale=9)  # unowned appearance-affecting field
    bad = interface_two_audit(p2, j.trace["field_ownership"], j.trace["segments"])
    assert any(x["code"] == "UNOWNED_PROVIDER_FIELD" for x in bad["problems"])
    p3 = dict(j.logical_payload, positivePrompt=j.logical_payload["positivePrompt"] + "\nmasterpiece, trending")
    bad3 = interface_two_audit(p3, j.trace["field_ownership"], j.trace["segments"])
    assert any(x["code"] == "UNAUTHORIZED_STYLE_TEXT" for x in bad3["problems"])


@pytest.mark.req("ADD27-12")
def test_ungoverned_output_appearance_not_credited_to_skill():
    regions = [{"region_id": "face", "description": "redrawn 3/4 face", "claimed_decision_ids": ["D-SYN-FACE-VIEW"], "salience": "HIGH"},
               {"region_id": "coat", "description": "red coat", "content_fields": ["slots.subject"], "salience": "MEDIUM"},
               {"region_id": "glint", "description": "beautiful unexpected rim highlight", "salience": "HIGH"}]
    r = interface_three_attribution(regions, {"decision_ids": ["D-SYN-FACE-VIEW"], "content_fields": ["slots.subject"]})
    by = {x["region_id"]: x for x in r["regions"]}
    assert by["glint"]["origin"] == "PROVIDER_GENERATED_UNDETERMINED" and not by["glint"]["credited_to_skill"]
    assert r["status"] == "UNGOVERNED_OUTPUT_APPEARANCE" and r["skill_success_credit"] is False
    assert "cannot be exhaustively attributed" in r["notice"]


@pytest.mark.req("ADD27-13")
def test_provenance_graph_lineage_and_dangling_parent_refused():
    g = ProvenanceGraph()
    g.add(ProvenanceNode("w", "SOURCE_WITNESS", "SOURCE_OBSERVED", "W-SYN-A01", []))
    g.add(ProvenanceNode("r", "SOURCE_OBSERVATION", "SOURCE_OBSERVED", "R-SYN-02", ["w"]))
    g.add(ProvenanceNode("i", "STYLE_INFERENCE", "CROSS_SOURCE_INFERRED", "I", ["r"]))
    g.add(ProvenanceNode("d", "STYLE_DECISION", "CROSS_SOURCE_INFERRED", "D-SYN-FACE-VIEW", ["i"]))
    g.add(ProvenanceNode("k", "SKILL_CLAUSE", "CROSS_SOURCE_INFERRED", "K-SYN-FACE-01", ["d"]))
    g.add(ProvenanceNode("f", "COMPILED_FIELD", "PRODUCER_ENGINEERING_CHOICE", "positivePrompt[5]", ["k"]))
    assert g.roots_of_type("f", "SOURCE_WITNESS") == ["w"]
    with pytest.raises(Blocked):
        g.add(ProvenanceNode("x", "COMPILED_FIELD", "UNKNOWN_ORIGIN", "?", ["missing"]))


@pytest.mark.req("ADD27-14")
def test_crash_during_completeness_commit_recovers_ledger_and_next_question(tmp_path):
    code = f"""
import sys, json; sys.path.insert(0, r'{ROOT}')
from pathlib import Path
from vme.state.workspace import Workspace
from vme.fixtures import loop_fixtures as fx
from vme.skills.operators import registered
from vme.style.coverage import review_visual_model_completeness
from vme.vision.runner import maybe_crash
ws = Workspace(Path(r'{tmp_path / "w"}')).ensure(); st = ws.store()
L, scope = fx.complete_ledger_and_scope()
r = review_visual_model_completeness(L, scope, fx.synthetic_decisions(face_light_joint=False, grip_light_joint=True), registered())
with st.tx() as c:
    st.put('VisualModelCoverageLedger', 'SCOPE-SYN-01', L, conn=c)
    maybe_crash('mid_coverage_commit')
    st.put('CoverageReview', 'SCOPE-SYN-01', r, conn=c)
print(json.dumps(r['question_ticket']['actual_question']))
"""
    env = {**os.environ, "VME_CRASH_AT": "mid_coverage_commit", "VME_CRASH_HARD": "1"}
    r1 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
    assert r1.returncode == 97
    import sqlite3
    con = sqlite3.connect(str(tmp_path / "w" / "store" / "vme.sqlite"))
    assert con.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0   # torn transaction rolled back, nothing half-written
    con.close()
    env.pop("VME_CRASH_AT")
    r2 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0, r2.stderr[-500:]
    from vme.state.workspace import Workspace
    st = Workspace(tmp_path / "w").ensure().store()
    rev = st.get("CoverageReview", "SCOPE-SYN-01")
    assert rev["review"]["state"] == "BLOCKED_MISSING_STYLE_DECISION" and json.loads(r2.stdout.strip()) == rev["question_ticket"]["actual_question"]
    st.close()


@pytest.mark.req("ADD27-1")
def test_ledger_and_review_validate_against_addendum27_schema():
    import jsonschema
    schema = read_json(ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3" / "27_TYPED_COVERAGE_AND_PROVENANCE.schema.json")
    L, scope = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, scope, _decisions(include_face=False), registered())
    jsonschema.validate(L, schema)
    jsonschema.validate(r["review"], schema)
    for k in ("question_ticket",):
        jsonschema.validate(r[k], {**schema["$defs"]["DynamicQuestionTicket"], "$defs": schema["$defs"]})
    bad = copy.deepcopy(L)
    del bad["open_gaps"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
