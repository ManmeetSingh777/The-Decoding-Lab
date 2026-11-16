"""Iteration invalidation, rejection→revised skill, asset-demand manufacturing and the directed renderer
(repair R12, R17–R21, R23; ST28-15/16/21). Drills use SIMULATED transports; outputs are labelled fixtures, not art."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vme.util import Blocked

HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"


def _runner(ws, prov, run_id):
    from vme.loop.real import RealLoopRunner
    from vme.testing.drill import drill_config
    return RealLoopRunner(ws, run_id=run_id, providers=prov, config=drill_config())


def _to_art_review(tmp_path, run_id):
    from vme.testing.drill import build_drill_workspace, drill_providers, enable_network_flag
    from vme.loop.human import approve_selection
    enable_network_flag()
    ws = build_drill_workspace(tmp_path)["ws"]
    prov, client = drill_providers(tmp_path)
    o = _runner(ws, prov, run_id).run()
    assert o["reason"] == "AWAITING_SELECTION_APPROVAL"
    st = ws.store()
    m = st.get("SelectedSequenceManifest", "REAL:15")
    st.close()
    approve_selection(ws, manifest_sha=m["manifest_sha"], approved_by=HUMAN)
    o = _runner(ws, prov, run_id).run()
    assert o["stopped_at"] == "S6" and o["reason"] == "AWAITING_ARTWORK_REVIEW", o
    return ws, prov, client


@pytest.mark.req("R12", "R21", "ST28-21", path="REAL")
def test_art_rejection_reopens_decision_new_skill_new_request_only_dependants_rerun(tmp_path):
    from vme.review.approvals import GateKeeper
    from vme.skills.skill import load_skill, skill_hash
    ws, prov, client = _to_art_review(tmp_path, "REAL-REJ")
    st = ws.store()
    s4 = st.get("LoopTransition", "REAL-REJ:S4")["outputs"]
    s5 = st.get("LoopTransition", "REAL-REJ:S5")["outputs"]
    old_result = Path(tmp_path / "ws" / "artifacts" / "provider")
    old_results = sorted(p.read_bytes() for p in old_result.rglob("result.json"))
    did = next(n for n in load_skill(s4["skill_folder"])["recipes"]["main"]["nodes"] if n["id"] == "n_canonical_character")["decisions"][0]
    imgs = st.get("LoopTransition", "REAL-REJ:S6")["outputs"]["images"]
    GateKeeper(st).submit_art_verdict("REAL-REJ", image_paths=imgs, brief_id="BRIEF-DRILL-ANCHOR", skill_versions=[s4["skill_hash"]],
                                      verdict="REJECTED", signed_by=HUMAN,
                                      defects=[{"symptom": "TEST: near arm merges into the torso silhouette", "attributed_stage": "STYLE_DECISION",
                                                "decision_id": did}])
    st.close()
    o1 = _runner(ws, prov, "REAL-REJ").run()
    assert o1["reason"] == "ARTWORK_REJECTED_REVISION_OPEN"
    o2 = _runner(ws, prov, "REAL-REJ").run()
    tr = {t["stage"]: t for t in o2["trace"]}
    assert tr["S0"].get("resumed_from_store") and tr["S1"].get("resumed_from_store")          # source work never redone
    assert all(tr[s].get("rerun_due_to_invalidation") for s in ("S2", "S3", "S4", "S5"))
    assert o2["stopped_at"] == "S6" and o2["reason"] == "AWAITING_ARTWORK_REVIEW"
    st = ws.store()
    s4b = st.get("LoopTransition", "REAL-REJ:S4")["outputs"]
    s5b = st.get("LoopTransition", "REAL-REJ:S5")["outputs"]
    assert s4b["skill_hash"] != s4["skill_hash"] and Path(s4["skill_folder"]).exists()
    assert skill_hash(s4["skill_folder"]) == s4["skill_hash"]                                    # old version immutable
    assert s5b["n_canonical_character"]["request_body_sha256"] != s5["n_canonical_character"]["request_body_sha256"]
    d = st.get("ConditionalVisualDecision", did)
    assert d["status"] != "RESEARCH_ONLY" and d["superseded_branches"] and d["revision_of"].startswith("REOPENED_BY_HUMAN")
    assert all(b in sorted(p.read_bytes() for p in old_result.rglob("result.json")) for b in old_results)   # receipts not overwritten
    inv = [i for i in st.list("StageInvalidation") if i["run_id"] == "REAL-REJ"]
    assert {i["stage"] for i in inv} == {"S2", "S3", "S4", "S5"}
    assert next(i for i in inv if i["stage"] == "S2")["changed_inputs"] == ["revisions"]
    st.close()


@pytest.mark.req("R12", "R17", "R19", "ST28-15", "ST28-16", path="REAL")
def test_shot_plan_change_reruns_only_asset_stage_and_blocks_unproducible_demands(tmp_path):
    from vme.testing.drill import drill_brief, drive
    from vme.loop.human import add_brief
    from vme.testing.drill import build_drill_workspace, drill_providers, enable_network_flag
    enable_network_flag()
    ws = build_drill_workspace(tmp_path)["ws"]
    prov, client = drill_providers(tmp_path)
    out = drive(ws, prov, run_id="REAL-SP", max_rounds=40)
    assert out["result"].get("completed_through") == "S9", out["log"]
    st = ws.store()
    s7 = st.get("LoopTransition", "REAL-SP:S7")["outputs"]
    assert {x["status"] for x in s7["demands"]} <= {"PRODUCED", "PRODUCED_IN_S5"} and s7["blocked"] == []
    pack = json.loads(Path(s7["pack"]).read_text(encoding="utf-8"))
    assert pack["world_plate"]["contains_actor"] is False and pack["world_plate"]["depth"] == 0
    for k, a in pack["states"].items():
        assert a["identity_source_sha256"] == pack["canonical"]["sha256"] and a["coordinate_frame"]["origin"] and a["consumers"]
    s8 = st.get("LoopTransition", "REAL-SP:S8")["outputs"]
    assert s8["background"].startswith("WORLD_PLATE") and s8["actors"] == ["explorer"] and len(s8["event_trace"]) == 2
    st.close()
    b = drill_brief()
    b["shot_plan"]["actions"].append({"actor": "explorer", "event_id": "e3", "expression": "surprised"})
    b["shot_plan"]["actions"].append({"actor": "explorer", "event_id": "e4", "moves_part": "near_arm"})
    add_brief(ws, b, added_by=HUMAN)
    o = _runner(ws, prov, "REAL-SP").run()
    tr = {t["stage"]: t for t in o["trace"]}
    assert all(tr[s].get("resumed_from_store") for s in ("S0", "S1", "S2", "S3", "S4", "S5", "S6"))
    assert o["stopped_at"] == "S7" and o["reason"] == "ASSET_DEMAND_BLOCKED"
    st = ws.store()
    s7b = st.get("LoopTransition", "REAL-SP:S7")["outputs"]
    blocked = {x["step"]: x["status"] for x in s7b["blocked"]}
    assert blocked == {"expr:surprised": "BLOCKED_NO_DECISION_OR_OPERATOR", "layer:near_arm": "BLOCKED_ROUTE_NOT_IMPLEMENTED",
                       "clean_plate:near_arm": "BLOCKED_ROUTE_NOT_IMPLEMENTED"}
    from vme.review.approvals import GateKeeper
    assert GateKeeper(st).state("REAL-SP")["state"] == "ASSET_PREPARING"          # old asset approval no longer authorizes a render
    st.close()


def _man(st, ids):
    return {"submitted_witness_ids": sorted(ids), "byte_manifest": [{"witness_id": w, "source_sha256": st.get("Witness", w)["film_sha256"],
                                                                     "frame_index": st.get("Witness", w)["frame_start"], "region": None}
                                                                    for w in ids]}


def _s8_runner(ws, sp, pack):
    from vme.loop.real import RealLoopRunner, RealProviders
    prov = RealProviders(vision_client_factory=lambda: None, vision_transport_kind="SIMULATED", image_transport=None,
                         image_transport_kind="SIMULATED")
    r = RealLoopRunner(ws, run_id="REAL-S8", providers=prov)
    pp = ws.root / "pack.json"
    pp.write_text(json.dumps(pack), encoding="utf-8")
    st = ws.store()
    st.put("LoopTransition", "REAL-S8:S7", {"run_id": "REAL-S8", "stage": "S7", "status": "COMPLETED", "outputs": {"pack": str(pp)}})
    r._brief = lambda _st: {"shot_plan": sp}
    return r, st


@pytest.mark.req("R20", "ST28-16")
def test_renderer_refuses_undirected_actor_and_missing_event_state(ws):
    canon = {"actor_id": "hero", "path": "c.png", "sha256": "0" * 64}
    pack = {"world_plate": {"path": "x.png"}, "canonical": canon, "canonical_by_actor": {"hero": canon}, "states": {}}
    r, st = _s8_runner(ws, {"frames": 60, "events": []}, pack)
    status, out = r._s8(st)
    assert status == "STOPPED" and out["stop_reason"] == "SHOT_PLAN_NOT_DIRECTED"          # never a default x=55% actor
    r, st = _s8_runner(ws, {"frames": 60, "actors": [{"id": "hero", "x": 1, "y": 1, "w": 10, "h": 10, "z": 1}],
                            "events": [{"actor": "hero", "from": 0, "to": 9, "state": "view:profile"}]}, pack)
    status, out = r._s8(st)
    assert status == "STOPPED" and out["stop_reason"] == "EVENT_STATE_NOT_PRODUCED"          # no transform substitute for a drawing
    st.close()


@pytest.mark.req("R18")
def test_world_plate_operation_sends_setting_only(tmp_path, store):
    from vme.style.authoring import author_decision, production_choice_id, publish_skill_version
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.testing.drill import drill_brief
    from vme.fixtures.synthetic import fixture_caps
    from vme.skills.operators import registered
    store.put("Witness", "W-w", {"witness_id": "W-w", "film_sha256": "c" * 64, "sequence_id": "s", "frame_start": 3, "frame_end": 3,
                                 "evidence_kind": "FULL_FRAME", "observer": "VLM", "visible_relation": "SYNTHETIC: far layers recede behind near ones",
                                 "dimensions": ["WORLD_ASSEMBLY"], "scene_specific_facts": [], "observation_ids": [], "limits": "t",
                                 "subject_class": "landscape", "evidence_origin": "SIMULATED_VLM_TRANSPORT"})
    ans = {"answer_status": "INFERRED", "SOURCE_VISIBLE_FACTS": [{"relation": "SYNTHETIC: near and far layers separate by value steps while the focal area stays open", "witness_ids": ["W-w"]}],
           "CONSTRUCTION_EXPLANATION": "SYNTHETIC: depth planes are separated by value", "WHEN_NOT_APPLICABLE": ["diagrams"], "ADAPTS_WITH": ["scale"],
           "REMAINING_UNKNOWN": ["x"], "BRANCHES": [{"when": {"environment": "underwater"}, "operation_id": "op.world_plate",
                                                     "construction_action": "SYNTHETIC: paint the {setting} as an empty plate whose near layers separate from far layers by value steps",
                                                     "reference_policy": {"mode": "NOT_APPLICABLE", "reason": "SYNTHETIC: plate decision carried by clause"}}]}
    did = production_choice_id("world:clean_plate", "plate")
    d = author_decision(store, {"question_id": "Q", "exact_artistic_unknown": "t", "observed_contrast_with_witness_ids": [],
                                "owner_stage": "STYLE_CONDITIONS"}, ans, authorized_submission_manifest=_man(store, ["W-w"]),
                        dims=["WORLD_ASSEMBLY"], registered_ops=registered(), required_branches=[], decision_id=did,
                        owned_choice_ids=["world:clean_plate"], phenomenon="plate")
    oc = {"op.world_plate": {"width": 1536, "height": 864, "format": "PNG", "asset_kind": "WORLD_PLATE"}}
    res = publish_skill_version(tmp_path / "sk", [d], skill_id="t", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT", output_contracts=oc,
                                exemplar_loader=None)
    job = StyleProgramCompiler().compile(drill_brief(), res["folder"], pinned_skill_hash=res["skill_hash"], recipe_id="main",
                                         node_id="n_world_plate", caps=fixture_caps())
    p = job.logical_payload["positivePrompt"]
    assert "Original setting" in p and "Original subject" not in p and "deep-sea research explorer" not in p
    bad = dict(ans, BRANCHES=[{"when": {"environment": "underwater"}, "operation_id": "op.world_plate",
                               "construction_action": "SYNTHETIC: paint the {setting} with near layers in front of the {subject} and far layers behind",
                               "reference_policy": {"mode": "NOT_APPLICABLE", "reason": "SYNTHETIC"}}])
    d2 = author_decision(store, {"question_id": "Q2", "exact_artistic_unknown": "t", "observed_contrast_with_witness_ids": [],
                                 "owner_stage": "STYLE_CONDITIONS"}, bad, authorized_submission_manifest=_man(store, ["W-w"]),
                         dims=["WORLD_ASSEMBLY"], registered_ops=registered(), required_branches=[], decision_id=production_choice_id("world:p2", "p2"),
                         owned_choice_ids=["world:p2"], phenomenon="p2")
    res2 = publish_skill_version(tmp_path / "sk2", [d2], skill_id="t", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT",
                                 output_contracts=oc, exemplar_loader=None)
    with pytest.raises(Blocked) as e:
        StyleProgramCompiler().compile(drill_brief(), res2["folder"], pinned_skill_hash=res2["skill_hash"], recipe_id="main",
                                       node_id="n_world_plate", caps=fixture_caps())
    assert e.value.code == "CLAUSE_USES_SLOT_OUTSIDE_OPERATION"
