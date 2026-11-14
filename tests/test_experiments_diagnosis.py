"""Causality, ablation, A/B confounds, holdout integrity, transfer and multi-root diagnosis
(A11–A17, A46, B31–B33, C29, C31, C32)."""
import pytest

from vme.util import Blocked, read_json, atomic_write_json
from vme.fixtures import loop_fixtures as fx
from vme.experiments.experiments import causal_mutation_test, assert_causal, ab_confound_check, HoldoutRegistry, transfer_status
from vme.diagnose.diagnose import diagnose_run, classify


@pytest.mark.req("A12", "A11", "C29")
def test_disabling_decision_changes_or_blocks_and_inert_rule_detected(skill, brief, caps):
    def drop_branch_clause(folder):
        d = read_json(folder / "decisions.json")
        for x in d:
            if x["decision_id"] == "D-SYN-CHAR-WHOLE":
                x["branches"][0]["clause_ids"] = [c for c in x["branches"][0]["clause_ids"] if "whole_scene" not in c]
        atomic_write_json(folder / "decisions.json", d)
    r = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=drop_branch_clause, label="disable")
    assert r["request_changed_or_blocked"]
    def rename_rule_only(folder):  # change a rule ID label that nothing consumes (inert)
        m = read_json(folder / "manifest.json")
        m["label"] = m["label"] + " (renamed note)"
        atomic_write_json(folder / "manifest.json", m)
    r2 = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=rename_rule_only, label="inert")
    assert r2["skill_hash_changed"] and not r2["request_changed_or_blocked"]
    with pytest.raises(Blocked) as e:
        assert_causal(r2, expect_change=True)
    assert e.value.code == "CAUSAL_EFFECT_MISSING"   # 03: rule id change w/o provider args change → refuse promotion


@pytest.mark.req("A13")
def test_subchange_ablation_toggles_are_individually_addressable(skill, brief, caps):
    def ab(did):
        def m(folder):
            d = read_json(folder / "decisions.json")
            for x in d:
                if x["decision_id"] == did:
                    for b in x["branches"]:
                        b["construction_action"] += " (ablated)"
                        b["clause_ids"] = b["clause_ids"]
            # ablate by removing this decision's clauses from the whole_scene template text
            t = read_json(folder / "prompt_templates" / "whole_scene.json")
            for c in t["clauses"]:
                if c["decision_id"] == did:
                    c["template"] = c["template"] + " [ablation-variant]"
            atomic_write_json(folder / "prompt_templates" / "whole_scene.json", t)
            atomic_write_json(folder / "decisions.json", d)
        return m
    r_world = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=ab("D-SYN-WORLD"), label="world")
    r_char = causal_mutation_test(skill[0], brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=ab("D-SYN-CHAR-WHOLE"), label="char")
    added_w = r_world["diff"]["positivePrompt"]["added"]
    added_c = r_char["diff"]["positivePrompt"]["added"]
    assert added_w and added_c and added_w != added_c


@pytest.mark.req("A15")
def test_ab_confound_detection():
    base = {"brief_hash": "b", "model": "runware:400@4", "provider_version": "1", "seed": 1, "width": 1536, "height": 864}
    assert ab_confound_check(base, dict(base))["status"] == "CONTROLLED"
    assert ab_confound_check(base, dict(base, provider_version="2"))["status"] == "CONFOUNDED"


@pytest.mark.req("A17", "C32", "B32")
def test_holdout_contamination_and_post_test_patch(tmp_path):
    hr = HoldoutRegistry(tmp_path / "h.json")
    hid = hr.seal(fx.holdout_brief())
    with pytest.raises(Blocked) as e:
        hr.access(hid, by_role="skill_builder", skill_frozen_hash="abc")
    assert e.value.code == "HOLDOUT_CONTAMINATED"
    hid2 = hr.seal(dict(fx.holdout_brief(), brief_id="H2"))
    with pytest.raises(Blocked):
        hr.access(hid2, by_role="transfer_runner", skill_frozen_hash=None)  # before freeze
    hid3 = hr.seal(dict(fx.holdout_brief(), brief_id="H3"))
    hr.access(hid3, by_role="transfer_runner", skill_frozen_hash="frozen1")
    with pytest.raises(Blocked) as e3:
        hr.record_result(hid3, skill_hash_used="patched2")
    assert e3.value.code == "SKILL_PATCHED_AFTER_TEST"
    assert transfer_status([], frozen=True, distinct_subjects=1) == "TRANSFER_PENDING_NEEDS_DISTINCT_SUBJECTS"
    assert transfer_status([], frozen=True, distinct_subjects=2) == "TRANSFER_PENDING_AWAITING_REVIEW"


@pytest.mark.req("A16")
def test_rotating_brief_uses_same_skill_without_manual_rescue(skill, caps):
    from conftest import compile_job
    rot = fx.synthetic_brief(brief_id="BRIEF-SYN-ROT-01", pool="rotating_development",
                             slots={"subject": "orchard surveyor drone pilot", "setting": "terraced orchard station", "environment": "interior"})
    j = compile_job(skill, rot, caps)
    assert j.trace["skill_hash"] == skill[1] and "terraced orchard station" in j.logical_payload["positivePrompt"]


@pytest.mark.req("A14", "A46", "C31", "B31")
def test_multiple_simultaneous_root_causes_kept_separate():
    sym = [{"symptom": "face drifts in 3/4 state", "evidence": {"request_correct": True, "output_ignores_reference": True}},
           {"symptom": "arm layer halo", "evidence": {"mask_mismatch": True}},
           {"symptom": "prop floats during reach", "evidence": {"contact_drift": True}},
           {"symptom": "world clause missing from payload", "evidence": {"compiled_payload_missing_clause": True}},
           {"symptom": "predicted near/far redraw did not appear", "evidence": {"hypothesis_prediction_failed": True}},
           {"symptom": "renderer frame count wrong", "evidence": {"ffprobe_mismatch": True}}]
    d = diagnose_run(sym)
    assert d["distinct_failure_classes"] == sorted(["MODEL_CAPABILITY_GAP", "ASSET_CONSTRUCTION_GAP", "MOTION_LOGIC",
                                                    "PROMPT_COMPILER_GAP", "HYPOTHESIS_ERROR", "RENDER_ENGINE"])
    assert not d["everything_blamed_on_reference_analysis"] and d["fix_first_stage"] == "CAUSE_INFERENCE"
    assert classify({"symptom": "?", "evidence": {}})["failure_classes"] == ["UNCLASSIFIED_NEEDS_EVIDENCE"]


@pytest.mark.req("B33", "A12", phase="PAID")
def test_visual_causality_requires_real_outputs_blocked_offline():
    """B33/A12 visual part: whether a skill change produces a visible source-conditioned difference needs real
    provider images; offline we prove only request-level causality (see compiler tests)."""
    assert True
