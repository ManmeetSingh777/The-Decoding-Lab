"""R3 no-waiver acceptance tests (01_INDEPENDENT_FORENSIC_AUDIT F01–F18 + 03_NO_WAIVER_ACCEPTANCE_MATRIX).

Every negative asserts the EXACT intended root-cause code through the real production function, and a matching positive proves the
guard is not simply refusing everything. All data is SYNTHETIC; nothing here is evidence about the real films.
"""
from __future__ import annotations

import io
import json

import pytest
from PIL import Image

from vme.util import Blocked, digest
from vme.skills.operators import registered

FA, FB = "a" * 64, "b" * 64
HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"


def _png(rgb=(10, 20, 30), size=(64, 36)) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", size, rgb).save(b, format="PNG")
    return b.getvalue()


def _w(st, wid, film, k, dims, rel="SYNTHETIC: the near contour overlaps the far edge while the background stays behind", kind="FULL_FRAME",
       region=None, observer="VLM", parent=None, cls="biped"):
    st.put("Witness", wid, {"witness_id": wid, "film_sha256": film, "sequence_id": f"seq-{film[:4]}", "frame_start": k, "frame_end": k,
                            "evidence_kind": kind, "observer": observer, "visible_relation": rel, "image_sha256": f"{k:064x}",
                            "region": region, "subject_class": cls, "scene_specific_facts": [], "observation_ids": [f"{film[:16]}:{k}"],
                            "limits": "SYNTHETIC", "dimensions": dims, "evidence_origin": "SIMULATED_VLM_TRANSPORT",
                            "parent_full_frame_witness": parent})


def _man(st, ids, **override):
    ms = []
    for w in ids:
        r = st.get("Witness", w)
        m = {"witness_id": w, "source_sha256": r["film_sha256"], "frame_index": r["frame_start"], "region": r.get("region"),
             "role": "WITNESS", "image_bytes_sha256": "0" * 64}
        m.update(override.get(w, {}))
        ms.append(m)
    return {"submitted_witness_ids": sorted(ids), "byte_manifest": ms}


def _ans(wids, action="SYNTHETIC: draw the {subject} with the near limb overlapping the {original_prop} edge while the far limb stays behind",
         *, op="op.whole_scene", when=None, policy=None, extra=None):
    a = {"answer_status": "INFERRED", "REMAINING_UNKNOWN": ["SYNTHETIC: profile view"],
         "SOURCE_VISIBLE_FACTS": [{"relation": f"SYNTHETIC: in {w} the near hand overlaps the handle edge while the sleeve stays behind",
                                   "witness_ids": [w]} for w in wids],
         "CONSTRUCTION_EXPLANATION": "SYNTHETIC: hand and prop are drawn as one contact state rather than a transformed arm",
         "WHY_THE_DECISION_MATTERS": "SYNTHETIC: contact reads", "WHEN_NOT_APPLICABLE": ["diagram frames"], "ADAPTS_WITH": ["anatomy"],
         "BRANCHES": [{"when": when or {"environment": "underwater"}, "operation_id": op, "construction_action": action,
                       "reference_policy": policy or {"mode": "NOT_APPLICABLE", "reason": "SYNTHETIC: carried by the clause"}}]}
    a.update(extra or {})
    return a


def _q(stage="STYLE_CONDITIONS", qid="Q", contrast=()):
    return {"question_id": qid, "exact_artistic_unknown": "SYNTHETIC", "observed_contrast_with_witness_ids": list(contrast), "owner_stage": stage}


def _author(st, q, a, man, *, req=None, did="PC-TEST", dims=("WORLD_ASSEMBLY",)):
    from vme.style.authoring import author_decision
    return author_decision(st, q, a, dims=list(dims), registered_ops=registered(), required_branches=req or [], decision_id=did,
                           owned_choice_ids=["choice:test"], phenomenon="test", authorized_submission_manifest=man)


# ======================================================================== F01 / F02 — frame observations
def _frame_obs(m, **over):
    from vme.vision.contracts import FRAME_OBSERVATION_FIELDS
    o = {f: [] for f in FRAME_OBSERVATION_FIELDS}
    o.update(frame_id=m["frame_id"], source_sha=m["source_sha"], pts_time=m["pts_time"], request_id="r", submitted_image_sha=m["image_sha"],
             scene_and_world_state="SYNTHETIC", focal_whole_artwork_state=f"SYNTHETIC: at {m['frame_id']} the near figure overlaps the far wall while the floor recedes",
             visible_layer_depth_attention_state="UNKNOWN", camera_vs_actor_vs_drawing_state="UNKNOWN",
             changed_since_prior_frame=[{"kind": "OBSERVED_DIFF", "what": "SYNTHETIC: hand moves"}], persistent_state_ids=["actor_1"],
             visible_design_relations=[{"relation": "SYNTHETIC: the near hand overlaps the handle edge while the sleeve stays behind",
                                        "dimensions": ["CHARACTER_BODY_HAND_CONTACT"]}])
    o.update(over)
    return o


def _resp(obs, active=None):
    return {"frame_observations": obs, "packet_transition_graph": {"edges": []},
            "boundary_state": {"active_objects": active or [{"id": "actor_1"}], "open_events": []}, "reconciled_events": []}


M = [{"frame_id": f"{'a' * 16}:{i}", "source_sha": "a" * 16, "pts_time": i / 30, "image_sha": f"{i:064x}"} for i in range(2)]


@pytest.mark.req("R3-F01")
def test_f01_generic_or_relationless_frame_record_is_never_validated():
    from vme.vision.contracts import validate_packet_response
    assert validate_packet_response(_resp([_frame_obs(m) for m in M]), M, None, images_actually_sent=2)["ok"]
    vague = [_frame_obs(m, focal_whole_artwork_state="nice beautiful premium artwork", visible_design_relations=[]) for m in M]
    v = validate_packet_response(_resp(vague), M, None, images_actually_sent=2)
    assert not v["ok"] and v["status"] == "NEEDS_REINSPECTION"
    assert any(p.startswith("NO_TYPED_SOURCE_VISUAL_FACTS") for p in v["problems"])
    assert any(p.startswith("ARTISTIC_FRAME_OBSERVATIONS_INSUFFICIENT") for p in v["problems"])
    fluent = [_frame_obs(m, visible_design_relations=[], source_fact_statements=[]) for m in M]
    assert any(p.startswith("NO_TYPED_SOURCE_VISUAL_FACTS") for p in validate_packet_response(_resp(fluent), M, None, images_actually_sent=2)["problems"])


@pytest.mark.req("R3-F01")
def test_f01_through_the_actual_packet_runner(ws, indexed24):
    from vme.vision.runner import PacketRunner, plan_packets
    from vme.vision.providers import MockVisionProvider
    clip, idx, loader = indexed24
    st = ws.store()
    plans = plan_packets(idx, 0, 3, film_sha=idx[0]["film_sha256"], pass_id="pv", cluster_id="c", model_version="m", max_images=12)
    pr = PacketRunner(st, ws.vision_dir, idx, loader, MockVisionProvider(ws.root / "rv", mode="vague"), source_is_synthetic=True,
                      active_questions=[{"question_id": "Q", "text": "t"}])
    assert pr.run(plans[0]) == "NEEDS_REINSPECTION"
    err = st.conn.execute("SELECT error FROM packets WHERE packet_id=?", (plans[0].packet_id,)).fetchone()[0]
    assert "ARTISTIC_FRAME_OBSERVATIONS_INSUFFICIENT" in err
    assert st.conn.execute("SELECT COUNT(*) FROM frame_vision").fetchone()[0] == 0
    st.close()


@pytest.mark.req("R3-F02")
def test_f02_structured_boundary_ids_reconcile_and_loss_or_malformed_ids_fail():
    from vme.vision.contracts import validate_packet_response
    prior = {"active_objects": [{"id": "actor_1", "identity": "x", "drawing_state": "front"}, {"id": "prop_7"}], "open_events": [{"event_id": "e1"}]}
    ok = [_frame_obs(M[0], persistent_state_ids=["actor_1", "prop_7"]), _frame_obs(M[1])]
    r = _resp(ok)
    r["reconciled_events"] = [{"event_id": "e1", "resolution": "CONTINUES"}]
    assert validate_packet_response(r, M, prior, images_actually_sent=2)["ok"]
    lost = _resp([_frame_obs(M[0]), _frame_obs(M[1])])
    lost["reconciled_events"] = [{"event_id": "e1", "resolution": "CONTINUES"}]
    assert any("BOUNDARY_IDENTITY_NOT_RECONCILED" in p and "prop_7" in p for p in validate_packet_response(lost, M, prior, images_actually_sent=2)["problems"])
    no_ev = _resp(ok)
    assert any(p.startswith("BOUNDARY_EVENT_NOT_RECONCILED") for p in validate_packet_response(no_ev, M, prior, images_actually_sent=2)["problems"])
    bad = {"active_objects": [{"identity": "no id"}], "open_events": []}
    assert "BOUNDARY_OBJECT_WITHOUT_STABLE_ID" in validate_packet_response(_resp(ok), M, bad, images_actually_sent=2)["problems"]


# ======================================================================== F03 / F05 — applicability
@pytest.mark.req("R3-F03")
def test_f03_unrelated_branch_never_covers_a_choice():
    from vme.style.coverage import _owner_for
    c = {"choice_id": "a:face", "dimensions": ["CHARACTER_FACE_ACTING"], "conditions": {"view": "profile"}}
    mk = lambda when: {"decision_id": "D", "status": "EXECUTABLE_CANDIDATE", "owned_choice_ids": ["a:face"], "dimension_tags": ["CHARACTER_FACE_ACTING"],
                       "branches": [{"when": when, "operation_node_ids": ["op.whole_scene"]}]}
    assert _owner_for(c, [mk({"action": "grip"})], registered())[1] == "MISSING_DECISION"
    assert _owner_for(c, [mk({})], registered())[1] == "MISSING_DECISION"
    assert _owner_for(c, [mk({"view": "profile"})], registered()) == ("D", None)


@pytest.mark.req("R3-F05")
def test_f05_disjoint_branches_do_not_own_a_joint_condition_unless_invariance_is_reviewed(store):
    from vme.state.authority import AuthorityRegistry
    _w(store, "W-1", FA, 3, ["CHARACTER_BODY_HAND_CONTACT"])
    _w(store, "W-2", FB, 5, ["CHARACTER_BODY_HAND_CONTACT"], cls="creature")
    req = [{"conditions": {"view": "profile", "action": "grip"}, "operation_ids": ["op.whole_scene"], "choice_id": "choice:test"}]
    a = _ans(["W-1"])
    a["BRANCHES"] = [dict(a["BRANCHES"][0], when={"view": "profile"}),
                     dict(a["BRANCHES"][0], when={"action": "grip"}, construction_action="SYNTHETIC: draw the grip with the near hand over the edge")]
    d = _author(store, _q(contrast=["W-2"]), a, _man(store, ["W-1", "W-2"]), req=req, did="PC-J1")
    assert d["status"] == "RESEARCH_ONLY" and d["research_only_reason"].startswith("BRANCHES_MISSING_FOR")
    joint = _ans(["W-1"], when={"view": "profile", "action": "grip"})
    assert _author(store, _q(contrast=["W-2"]), joint, _man(store, ["W-1", "W-2"]), req=req, did="PC-J2")["status"] == "EXECUTABLE_CANDIDATE"
    # an omitted axis is acceptable ONLY with a human-reviewed invariance in the trusted authority registry
    AuthorityRegistry(store).issue("INVARIANCE_REVIEW", scope={"decision_id": "PC-J3", "axis": "action"}, verdict="APPROVED", by=HUMAN,
                                   statement="SYNTHETIC test invariance", evidence={"witness_ids": ["W-1", "W-2"]})
    part = _ans(["W-1"], when={"view": "profile"})
    assert _author(store, _q(contrast=["W-2"]), part, _man(store, ["W-1", "W-2"]), req=req, did="PC-J3")["status"] == "EXECUTABLE_CANDIDATE"
    with pytest.raises(Blocked) as e:
        AuthorityRegistry(store).issue("INVARIANCE_REVIEW", scope={"decision_id": "X", "axis": "a"}, verdict="APPROVED", by="claude", statement="s")
    assert e.value.code == "HUMAN_SIGNER_REQUIRED"


@pytest.mark.req("R3-F05")
def test_f05_conflicting_equally_applicable_branches_are_refused(store):
    _w(store, "W-1", FA, 3, ["WORLD_ASSEMBLY"])
    a = _ans(["W-1"])
    a["BRANCHES"].append(dict(a["BRANCHES"][0], construction_action="SYNTHETIC: draw the {subject} with the far limb in front of the edge instead"))
    with pytest.raises(Blocked) as e:
        _author(store, _q(), a, _man(store, ["W-1"]))
    assert e.value.code == "CONFLICTING_EQUALLY_APPLICABLE_BRANCHES"


@pytest.mark.req("R3-F05")
def test_f05_controller_requires_one_joint_branch():
    from vme.investigation.controller import ActiveArtProblem, ProblemContext, locate_earliest_missing_handoff
    p = ActiveArtProblem(cluster_id="c", version=1, original_output_id_or_initial_reference_only="r", reference_full_frame_ids=["w"],
                         affected_original_subject_classes=[], high_impact_visible_difference="x", whole_scene_consequence="x",
                         connected_artistic_relations=[], current_explanation_and_support=[{"claim": "x", "witness_ids": ["w"]}],
                         next_required_producer_decision_id="D", required_conditions={"view": "profile", "action": "grip"})
    mk = lambda brs: ProblemContext(witnesses={"w": {"witness_id": "w"}}, decisions={"D": {"status": "EXECUTABLE_CANDIDATE", "branches": brs}},
                                    registered_operators={"op": {"kind": "whole_scene"}}, provider_capabilities=["whole_scene"])
    disjoint = [{"when": {"view": "profile"}, "operation_node_ids": ["op"]}, {"when": {"action": "grip"}, "operation_node_ids": ["op"]}]
    assert locate_earliest_missing_handoff(p, mk(disjoint))["stage"] == "STYLE_CONDITIONS"
    assert locate_earliest_missing_handoff(p, mk([{"when": {"view": "profile", "action": "grip"}, "operation_node_ids": ["op"]}]))["stage"] != "STYLE_CONDITIONS"


# ======================================================================== F04 / F10 — authority at the write site
@pytest.mark.req("R3-F04", "R3-F10")
@pytest.mark.parametrize("case,code", [("unsent", "UNSENT_WITNESS_CITATION"), ("wrong_source", "WRONG_SOURCE_WITNESS"),
                                       ("wrong_pts", "WRONG_PTS_WITNESS"), ("unseen_crop", "UNSEEN_CROP_OR_WRONG_REGION"),
                                       ("early_stage", "EARLY_STAGE_CANNOT_PUBLISH_SKILL"), ("no_manifest", "NO_ACTUAL_SUBMISSION_MANIFEST"),
                                       ("uncited", "UNCITED_ARTISTIC_CLAIM"), ("vague", "INSUFFICIENT_FOR_PRODUCING_CHOICE"),
                                       ("bad_op", "UNREGISTERED_OPERATOR")])
def test_f04_f10_decision_writer_fails_closed_with_exact_cause(store, case, code):
    _w(store, "W-1", FA, 3, ["WORLD_ASSEMBLY"])
    _w(store, "W-C", FA, 4, ["WORLD_ASSEMBLY"], kind="NATIVE_CROP", region={"x": 1, "y": 1, "w": 8, "h": 8}, parent="W-1")
    man = _man(store, ["W-1"])
    a, q = _ans(["W-1"]), _q()
    if case == "unsent":
        a = _ans(["W-never-sent"])
    elif case == "wrong_source":
        man = _man(store, ["W-1"], **{"W-1": {"source_sha256": FB}})
    elif case == "wrong_pts":
        man = _man(store, ["W-1"], **{"W-1": {"frame_index": 9}})
    elif case == "unseen_crop":
        a, man = _ans(["W-C"]), _man(store, ["W-C"], **{"W-C": {"region": None}})
    elif case == "early_stage":
        q = _q("SOURCE_OBSERVATION")
    elif case == "no_manifest":
        man = {}
    elif case == "uncited":
        a["SOURCE_VISIBLE_FACTS"] = [{"relation": "SYNTHETIC: the near edge overlaps the far one", "witness_ids": []}]
    elif case == "vague":
        a["SOURCE_VISIBLE_FACTS"] = [{"relation": "SYNTHETIC vibrant polished premium look", "witness_ids": ["W-1"]}]
        a["CONSTRUCTION_EXPLANATION"] = "great lighting"
    elif case == "bad_op":
        a["BRANCHES"][0]["operation_id"] = "op.make_beautiful_art"
    with pytest.raises(Blocked) as e:
        _author(store, q, a, man)
    assert e.value.code == code
    assert store.get("ConditionalVisualDecision", "PC-TEST") is None          # nothing published


@pytest.mark.req("R3-F04")
def test_f04_controller_refuses_self_authorized_answer_ids():
    from vme.investigation.controller import NextQuestion, validate_answer
    q = NextQuestion(question_id="q", cluster_id="c", from_evidence_version="x", gap_id="g", missing_decision_id="D",
                     missing_producing_operation="op.whole_scene", observed_contrast_with_witness_ids=["W-sent"], exact_artistic_unknown="x",
                     question_text="?", planned_witness_or_input_ids=[], possible_answer_consequences_for_operation=[], route="S3_CONDITIONS",
                     owner_stage="STYLE_CONDITIONS", reasoning_dimensions={}, uncovered_reasoning_dimensions=[])
    a = {"answer_status": "INFERRED", "SOURCE_VISIBLE_FACTS": [{"relation": "x overlaps y", "witness_ids": ["W-sent"]}],
         "answer_evidence_ids": ["W-sent", "W-never-sent"], "CONSTRUCTION_EXPLANATION": "the near shape occludes the far shape",
         "ACTUAL_PRODUCING_OPERATION": {"operation_id": "op.whole_scene"}, "WHERE_IT_ENTERS_COMPILED_REQUEST": {"operator": "op.whole_scene"},
         "IMPORTANT_LINKED_CHANGES": [], "WHY_THE_DECISION_MATTERS": "x", "WHEN_APPLICABLE": {}, "WHEN_NOT_APPLICABLE": ["z"], "REMAINING_UNKNOWN": ["a"]}
    v = validate_answer(q, a, registered())
    assert "ANSWER_SELF_AUTHORIZED_UNSHOWN_WITNESS" in v["problems"]


# ======================================================================== F06 / F07 / F09 — dispatch, hashing, receipt
@pytest.mark.req("R3-F06")
def test_f06_every_source_pass_constant_and_dispatch_carries_p0_and_its_pass():
    from vme.loop.real import QA_SYSTEM, RATIONALE_SYSTEM, NATIVE_SYSTEM, CHARACTER_DOSSIER_SYSTEM
    from vme.vision.prompt import P1_SYSTEM
    from vme.vision.protocol import P0, PROTOCOL_SHA
    from vme.vision.dispatch import prepare_verified_request, image_entry, PASS_FOR_KIND
    for txt, pid in ((P1_SYSTEM, "P1"), (RATIONALE_SYSTEM, "P2"), (CHARACTER_DOSSIER_SYSTEM, "P2"), (QA_SYSTEM, "P4"), (NATIVE_SYSTEM, "P5")):
        assert P0[:80] in txt and PROTOCOL_SHA in txt and f"pass={pid}" in txt
    img = image_entry(role="TARGET", png=_png(), witness_id="w", source_sha256=FA, frame_index=1, pts=0.1, width=64, height=36)
    with pytest.raises(Blocked) as e:
        prepare_verified_request(pass_id="P1", kind="question_answer", shape="s", source_shas=[FA], selection={}, images=[img], prior_boundary=None,
                                 active_cluster=None, controlling_problem=None, competing_explanations=None, required_response={},
                                 provider_profile={}, payload={})
    assert e.value.code == "PROTOCOL_PASS_MISMATCH" and PASS_FOR_KIND["question_answer"] == "P4"
    img2 = dict(img, _bytes=b"tampered")
    with pytest.raises(Blocked) as e:
        prepare_verified_request(pass_id="P4", kind="question_answer", shape="s", source_shas=[FA], selection={}, images=[img2],
                                 prior_boundary=None, active_cluster=None, controlling_problem=None, competing_explanations=None,
                                 required_response={}, provider_profile={}, payload={})
    assert e.value.code == "LOCAL_IMAGE_BYTES_CHANGED"


@pytest.mark.req("R3-F07")
def test_f07_request_identity_changes_with_text_parser_bytes_or_profile_and_stale_commit_is_refused(ws, indexed24, monkeypatch):
    from vme.vision import dispatch
    from vme.vision.dispatch import prepare_verified_request, image_entry
    img = image_entry(role="TARGET", png=_png(), witness_id="w", source_sha256=FA, frame_index=1, pts=0.1, width=64, height=36)
    kw = dict(pass_id="P4", kind="question_answer", source_shas=[FA], selection={}, images=[img], prior_boundary=None, active_cluster=None,
              controlling_problem=None, competing_explanations=None, required_response={}, payload={"q": 1})
    base = prepare_verified_request(shape="s", provider_profile={"m": 1}, **kw)["request_sha"]
    assert prepare_verified_request(shape="s.", provider_profile={"m": 1}, **kw)["request_sha"] != base
    assert prepare_verified_request(shape="s", provider_profile={"m": 2}, **kw)["request_sha"] != base
    monkeypatch.setattr(dispatch, "PARSER_CONTRACT_SHA", "changed-parser")
    assert prepare_verified_request(shape="s", provider_profile={"m": 1}, **kw)["request_sha"] != base
    # a committed packet is never reused once its instructions/questions differ
    from vme.vision.runner import PacketRunner, plan_packets
    from vme.vision.providers import MockVisionProvider
    clip, idx, loader = indexed24
    st = ws.store()
    plans = plan_packets(idx, 0, 3, film_sha=idx[0]["film_sha256"], pass_id="ps", cluster_id="c", model_version="m", max_images=12)
    prov = MockVisionProvider(ws.root / "rs")
    assert PacketRunner(st, ws.vision_dir, idx, loader, prov, source_is_synthetic=True, active_questions=[{"question_id": "Q", "text": "a"}]).run(plans[0]) \
        == "SEMANTIC_COMMITTED"
    with pytest.raises(Blocked) as e:
        PacketRunner(st, ws.vision_dir, idx, loader, prov, source_is_synthetic=True,
                     active_questions=[{"question_id": "Q", "text": "a CHANGED question"}]).run(plans[0])
    assert e.value.code == "STALE_SEMANTIC_PACKET_REQUIRES_NEW_ID"
    st.close()


@pytest.mark.req("R3-F07")
def test_f07_stage_keys_carry_protocol_and_system_text_hashes(ws, monkeypatch):
    from vme.loop import real
    prov = real.RealProviders(vision_client_factory=lambda: None, vision_transport_kind="SIMULATED", image_transport=None, image_transport_kind="SIMULATED")
    r = real.RealLoopRunner(ws, run_id="REAL-K", providers=prov)
    st = ws.store()
    k1 = {s: r._input_key(st, s)["key"] for s in ("S1", "S2")}
    monkeypatch.setattr(real, "QA_SYSTEM", real.QA_SYSTEM + " (one sentence changed, same version label)")
    monkeypatch.setattr(real, "PROTOCOL_SHA", "0" * 64)
    k2 = {s: r._input_key(st, s)["key"] for s in ("S1", "S2")}
    assert k1["S1"] != k2["S1"] and k1["S2"] != k2["S2"]
    st.close()


@pytest.mark.req("R3-F09")
def test_f09_receipt_is_local_manifest_not_a_provider_acknowledgement(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from test_provider_contracts import _vision, _ask
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    ad, client, _ = _vision(tmp_path)
    r = _ask(ad)
    j = json.loads((tmp_path / "vstate" / f"task_{r['receipt']['custom_id']}.json").read_text(encoding="utf-8"))
    assert j["evidence_status"] == ["LOCAL_BYTES_VERIFIED", "SUBMITTED", "RESPONSE_RECEIVED"]
    assert "SOURCE_ARTISTICALLY_REVIEWED" not in j["evidence_status"] and "images_received" not in r["receipt"]
    assert r["receipt"]["provider_reported_image_count"] is None if "provider_reported_image_count" in r["receipt"] else True
    from vme.vision.runner import coverage_for_range
    from vme.state.store import Store
    st = Store(tmp_path / "s.sqlite")
    cov = coverage_for_range(st, FA, "p", 0, 0)
    assert cov["artistic_status"].startswith("ARTISTIC_CLAIM_UNVERIFIED") and not cov["real_vlm"]
    st.close()


# ======================================================================== F08 — reference policy
@pytest.mark.req("R3-F08")
@pytest.mark.parametrize("policy,reason", [(None, "REFERENCE_POLICY_UNKNOWN"), ({"mode": "REQUIRED", "roles": []}, "REQUIRED_REF_WITHOUT_ROLES"),
                                           ({"mode": "REQUIRED", "roles": [{"role": "positive_view", "witness_id": "W-unseen"}]}, "REQUIRED_REF_UNSEEN"),
                                           ({"mode": "TEXT_ONLY_DEMONSTRATED"}, "TEXT_ONLY_NOT_PROVEN"),
                                           ({"mode": "NOT_APPLICABLE"}, "NOT_APPLICABLE_UNJUSTIFIED"),
                                           ({"mode": "REQUIRED", "roles": [{"role": "positive_view", "witness_id": "W-1"},
                                                                           {"role": "positive_view", "witness_id": "W-2"}]}, "AMBIGUOUS_REFERENCE_ROLES")])
def test_f08_missing_or_unqualified_reference_requirement_blocks_the_skill(store, policy, reason):
    _w(store, "W-1", FA, 3, ["WORLD_ASSEMBLY"])
    _w(store, "W-2", FB, 5, ["WORLD_ASSEMBLY"])
    a = _ans(["W-1", "W-2"])
    if policy is None:
        a["BRANCHES"][0].pop("reference_policy")
    else:
        a["BRANCHES"][0]["reference_policy"] = policy
    d = _author(store, _q(), a, _man(store, ["W-1", "W-2"]))
    assert d["status"] == "RESEARCH_ONLY" and d["research_only_reason"] == f"REFERENCE_POLICY:{reason}"


@pytest.mark.req("R3-F08")
def test_f08_distinct_roles_keep_distinct_witness_bytes_and_text_only_needs_human_review(store, tmp_path):
    from vme.style.authoring import publish_skill_version
    from vme.state.authority import AuthorityRegistry
    _w(store, "W-1", FA, 3, ["WORLD_ASSEMBLY"])
    _w(store, "W-2", FB, 5, ["WORLD_ASSEMBLY"])
    pol = {"mode": "REQUIRED", "roles": [{"role": "positive_view", "witness_id": "W-1"}, {"role": "contrast", "witness_id": "W-2"}]}
    d = _author(store, _q(), _ans(["W-1", "W-2"], policy=pol), _man(store, ["W-1", "W-2"]))
    assert d["status"] == "EXECUTABLE_CANDIDATE" and len(d["branches"][0]["mandatory_reference_role_ids"]) == 2
    cols = {"W-1": (200, 0, 0), "W-2": (0, 200, 0)}
    res = publish_skill_version(tmp_path / "sk", [d], skill_id="t", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT",
                                output_contracts={"op.whole_scene": {"width": 1536, "height": 864, "format": "PNG", "asset_kind": "WHOLE_SCENE"}},
                                exemplar_loader=lambda w: (_png(cols[w]), {"film_sha256": FA if w == "W-1" else FB, "frame_index": 1}),
                                consent_for=lambda f, s=None: {"status": "CONSENTED"})
    refs = {r["source_witness_id"]: r["sha256"] for r in res["references"]}
    assert set(refs) == {"W-1", "W-2"} and len(set(refs.values())) == 2           # never sorted(wids)[0] for every role
    t = _ans(["W-1"], policy={"mode": "TEXT_ONLY_DEMONSTRATED"})
    assert _author(store, _q(), t, _man(store, ["W-1"]), did="PC-T")["research_only_reason"] == "REFERENCE_POLICY:TEXT_ONLY_NOT_PROVEN"
    b = t["BRANCHES"][0]
    AuthorityRegistry(store).issue("TEXT_ONLY_TRANSFER_REVIEW", scope={"decision_id": "PC-T2", "condition_sha": digest({k: str(v) for k, v in b["when"].items()}),
                                                                      "action_sha": digest(b["construction_action"])}, verdict="APPROVED", by=HUMAN,
                                   statement="SYNTHETIC reviewed text-only transfer")
    assert _author(store, _q(), t, _man(store, ["W-1"]), did="PC-T2")["status"] == "EXECUTABLE_CANDIDATE"


# ======================================================================== F11 + Addendum 29 — source-first character study / ledgers
def _dossier(states, crop, con, **over):
    f = lambda rel: {"state": "OBSERVED", "visible_relation": f"SYNTHETIC: {rel} relative to the setting edge", "reconstruction_impact": "redraw",
                     "witness_ids": states[:1]}
    from vme.style.source_ledger import CHAR_FIELDS
    d = {"study_basis": "SOURCE_FIRST_DRAWN_ENTITY", "fields": {k: f(f"{k} contour narrows while the near mass overlaps") for k in CHAR_FIELDS},
         "identity_across_drawings": [{"witness_ids": states[:2]}], "contrasting_examples": [{"witness_ids": con}], "scope_class": "CONDITIONAL_STYLE_RULE"}
    d.update(over)
    return d


@pytest.mark.req("R3-F11", "A29")
def test_f11_a29_character_study_is_source_first_and_witnessed():
    from vme.style.source_ledger import validate_character_art_study
    auth = {"s1", "s2", "c1", "x1"}
    assert validate_character_art_study(_dossier(["s1", "s2"], ["x1"], ["c1"]), auth) == []
    assert "GENERIC_ANATOMY_TEMPLATE_FORBIDDEN" in validate_character_art_study(_dossier(["s1", "s2"], [], ["c1"], study_basis="HUMAN_SKELETON"), auth)
    tube = _dossier(["s1", "s2"], [], ["c1"])
    tube["fields"]["outer_contour_and_taper"]["visible_relation"] = "SYNTHETIC: arms are tubes attached at the shoulder while the torso stays still"
    assert "GENERIC_ANATOMY_SUBSTITUTED_FOR_DRAWN_FORM:outer_contour_and_taper" in validate_character_art_study(tube, auth)
    assert any(p.startswith("CHARACTER_ART_WITHOUT_SUBMITTED_WITNESS") for p in validate_character_art_study(_dossier(["zz", "s2"], [], ["c1"]), auth))
    assert "NO_MULTI_STATE_IDENTITY_PROOF" in validate_character_art_study(_dossier(["s1"], [], ["c1"]), auth)
    assert "NO_CHARACTER_CONTRAST" in validate_character_art_study(_dossier(["s1", "s2"], [], []), auth)
    unk = _dossier(["s1", "s2"], [], ["c1"])
    unk["fields"]["view_and_pose_redraws"] = {"state": "UNKNOWN", "witness_ids": ["s1"], "precise_next_witness": ""}
    assert "CHARACTER_ART_UNKNOWN_WITHOUT_TARGET:view_and_pose_redraws" in validate_character_art_study(unk, auth)


@pytest.mark.req("R3-F11", "A29")
def test_f11_character_rule_without_validated_dossier_is_research_only(store):
    _w(store, "W-1", FA, 3, ["CHARACTER_WHOLE_DESIGN"])
    a = _ans(["W-1"], op="op.canonical_character", when={"subject_kind": "biped"},
             action="SYNTHETIC: draw the {subject} with the upper mass wider than the lower mass while the outline stays continuous")
    d = _author(store, _q(), a, _man(store, ["W-1"]), dims=("CHARACTER_WHOLE_DESIGN",), did="PC-CH")
    assert d["status"] == "RESEARCH_ONLY" and d["research_only_reason"] == "CHARACTER_SOURCE_STUDY_MISSING"
    store.put("CharacterArtDossier", "CD-1", {"dossier_id": "CD-1", "entity_id": "e", "films": [FA], "status": "VALIDATED"})
    d2 = _author(store, _q(), a, _man(store, ["W-1"]), dims=("CHARACTER_WHOLE_DESIGN",), did="PC-CH2")
    assert d2["status"] == "EXECUTABLE_CANDIDATE" and d2["character_dossier_ids"] == ["CD-1"]


@pytest.mark.req("R3-F11", "R3-B9")
def test_f11_filled_categories_do_not_close_a_scene_with_an_unexplained_character_state(ws):
    from vme.style.source_ledger import source_art_ledger
    st = ws.store()
    film = "c" * 64
    pdir = ws.vision_dir / "REAL-L-L0" / "pkt_x"
    pdir.mkdir(parents=True)
    (pdir / "frames.jsonl").write_text(json.dumps({"frame_id": f"{film[:16]}:0", "pts_time": 0.0, "actually_visible_actor_and_object_ids": ["hero"],
                                                   "visible_design_relations": [{"relation": "r", "dimensions": d} for d in
                                                                                ("WHOLE_FRAME_LANGUAGE", "CHARACTER_FACE_ACTING", "COLOUR_RELATIONS")]}) + "\n",
                                       encoding="utf-8")
    st.conn.execute("INSERT INTO frame_vision(film_sha256,frame_index,pass_id,status,packet_id,image_sha,observation_sha,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (film, 0, "REAL-L-L0", "SIMULATED_TRANSPORT_FIXTURE", "pkt_x", "i", "o", "t"))
    st.conn.commit()
    dos = _dossier(["s1", "s2"], [], ["c1"])
    dos["fields"]["view_and_pose_redraws"] = {"state": "UNKNOWN", "witness_ids": ["s1"], "precise_next_witness": "a profile drawing of hero"}
    st.put("CharacterArtDossier", "CD-h", {"dossier_id": "CD-h", "entity_id": "hero", "films": [film], "status": "VALIDATED", "study": dos})
    led = source_art_ledger(st, ws, "REAL-L", [(film, 0, 0, "seq")], "REAL-L-L0")
    sc = led["scenes"][0]
    assert sc["status"] == "NEEDS_SOURCE_REINSPECTION" and not led["complete_for_promotion"]
    g = next(x for x in sc["open_gaps"] if x["kind"] == "CHARACTER_STATE_UNEXPLAINED")
    assert g["fields"] == ["view_and_pose_redraws"] and g["next"] == ["a profile drawing of hero"]
    assert sc["source_art_truth"] == "UNREVIEWED"
    st.close()


# ======================================================================== F12 / F13 / F14 / F15 — production
@pytest.mark.req("R3-F12")
def test_f12_a_state_drawn_from_another_actors_canonical_is_refused(ws):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from test_iteration_assets import _s8_runner
    ca = {"actor_id": "a", "path": "a.png", "sha256": "1" * 64}
    cb = {"actor_id": "b", "path": "b.png", "sha256": "2" * 64}
    pack = {"world_plate": {"path": "w.png"}, "canonical_by_actor": {"a": ca, "b": cb},
            "states": {"b:view:front": {"path": "s.png", "sha256": "3" * 64, "identity_source_sha256": "1" * 64}}}
    sp = {"frames": 30, "actors": [{"id": "a", "x": 1, "y": 1, "w": 5, "h": 5, "z": 1}, {"id": "b", "x": 9, "y": 1, "w": 5, "h": 5, "z": 2}],
          "events": [{"actor": "b", "from": 0, "to": 9, "state": "view:front"}]}
    r, st = _s8_runner(ws, sp, pack)
    with pytest.raises(Blocked) as e:
        r._s8(st)
    assert e.value.code == "STATE_IDENTITY_ALIASES_ANOTHER_ACTOR"
    sp2 = dict(sp, actors=sp["actors"] + [{"id": "c", "x": 1, "y": 1, "w": 5, "h": 5, "z": 3}], events=[])
    r, st = _s8_runner(ws, sp2, pack)
    status, out = r._s8(st)
    assert status == "STOPPED" and out["stop_reason"] == "ACTOR_ASSET_NOT_APPROVED" and out["actor"] == "c"
    st.close()


def _motion_fixture(method="ANTICIPATE_OVERSHOOT", drop=None):
    from vme.style.coverage import OriginalScope
    scope = OriginalScope(scope_id="S", subjects=[{"id": "hero", "kind": "character", "subject_kind": "biped", "actions": ["walk"]}],
                          world={"kind": "space", "layers": True}, camera={"moves": True}, audio_cues=[{"event_id": "e1"}])
    from vme.render.motion_program import TRACK_METHOD_PARAMS
    vals = {"hold_ratio": 0.2, "anticipation_ratio": 0.1, "anticipation_span": 0.2, "overshoot_ratio": 0.1, "overshoot_span": 0.15,
            "cue_offset_frames": 0, "layer_coefficients": {"far": 0.4}}
    mk = lambda did, owns, op, kind, when, m: {"decision_id": did, "status": "EXECUTABLE_CANDIDATE", "owned_choice_ids": [owns],
                                               "dimension_tags": [], "branches": [{"when": when, "operation_node_ids": [op],
                                                                                   "motion_program": {"track_kind": kind, "method": m,
                                                                                                      **{p: vals[p] for p in TRACK_METHOD_PARAMS[kind][m]}}}]}
    from vme.style.coverage import reverse_plan
    plan = reverse_plan(scope)
    cond = {c["choice_id"]: c["conditions"] for c in plan["choices"]}
    dims = {c["choice_id"]: c["dimensions"] for c in plan["choices"]}
    decs = [mk("PC-act", "hero:acting", "op.motion_actor_track", "ACTOR_ACTING", cond["hero:acting"], method),
            mk("PC-cam", "camera:depth", "op.camera_attention", "CAMERA", cond["camera:depth"], "EASE_IN_OUT"),
            mk("PC-wld", "world:motion", "op.world_motion", "WORLD", cond["world:motion"], "PARALLAX_LAYERS"),
            mk("PC-aud", "audio_timing", "op.audio_cue", "AUDIO", cond["audio_timing"], "CUE_ON_EVENT")]
    for d in decs:
        d["dimension_tags"] = dims[d["owned_choice_ids"][0]]
    decs = [d for d in decs if d["decision_id"] != drop]
    brief = {"shot_plan": {"frames": 60, "plan_width": 100, "plan_height": 100, "world_layers": [{"id": "world", "depth": "far"}],
                           "actors": [{"id": "hero", "x": 0, "y": 0, "w": 10, "h": 10, "z": 1,
                                                     "keyframes": [{"frame": 0, "x": 0}, {"frame": 59, "x": 80}]}],
                           "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1}, {"frame": 59, "x": 20, "y": 0, "scale": 1}],
                           "events": [{"event_id": "e1", "actor": "hero", "from": 20, "to": 30}], "audio": {"required": True, "cues": []}}}
    return decs, scope, brief


@pytest.mark.req("R3-F13")
def test_f13_motion_is_owned_by_source_decisions_and_ablation_changes_or_blocks_output():
    from vme.render.motion_program import compile_event_program
    decs, scope, brief = _motion_fixture()
    p = compile_event_program(decisions=decs, scope=scope, brief=brief, pack={"states": {}}, width=100, height=100, scale=1.0)
    owners = {t["kind"]: t["owner_decision_id"] for t in p["tracks"]}
    assert owners == {"ACTOR_ACTING": "PC-act", "CAMERA": "PC-cam", "WORLD": "PC-wld", "AUDIO": "PC-aud"}
    kf = {k["frame"]: k for k in next(t for t in p["tracks"] if t["kind"] == "ACTOR_ACTING")["keyframes"]}
    assert min(v["x"] for v in kf.values()) < 0 and max(v["x"] for v in kf.values()) > 80         # learned anticipation + overshoot
    d2, s2, b2 = _motion_fixture(method="HOLD_THEN_MOVE")
    p2 = compile_event_program(decisions=d2, scope=s2, brief=b2, pack={"states": {}}, width=100, height=100, scale=1.0)
    kf2 = next(t for t in p2["tracks"] if t["kind"] == "ACTOR_ACTING")["keyframes"]
    assert kf2 != list(kf.values()) and p2["program_sha"] != p["program_sha"]                    # counterfactual changes timing
    for drop, track in (("PC-act", "ACTOR_ACTING"), ("PC-cam", "CAMERA"), ("PC-aud", "AUDIO")):
        d3, s3, b3 = _motion_fixture(drop=drop)
        with pytest.raises(Blocked) as e:
            compile_event_program(decisions=d3, scope=s3, brief=b3, pack={"states": {}}, width=100, height=100, scale=1.0)
        assert e.value.code == "MOTION_TRACK_UNOWNED" and track in e.value.detail                  # never a default linear track
    assert all(t["interpolation_or_redraw_method"] not in (None, "DEFAULT_LINEAR", "WHOLE_STATE_SWAP_ONLY") for t in p["tracks"])


@pytest.mark.req("R3-F07")
def test_atomic_write_survives_a_transient_windows_lock_but_not_a_persistent_one(tmp_path, monkeypatch):
    import os as _os
    from vme import util
    real = _os.replace
    calls = {"n": 0}

    def flaky(a, b):
        calls["n"] += 1
        if calls["n"] <= 3:
            raise PermissionError(5, "Access is denied")
        return real(a, b)
    monkeypatch.setattr(util.os, "replace", flaky)
    monkeypatch.setattr(util.os, "name", "nt")
    util.atomic_write_json(tmp_path / "x.json", {"a": 1})
    assert json.loads((tmp_path / "x.json").read_text(encoding="utf-8")) == {"a": 1} and calls["n"] == 4
    monkeypatch.setattr(util.os, "replace", lambda a, b: (_ for _ in ()).throw(PermissionError(5, "Access is denied")))
    with pytest.raises(PermissionError):
        util.atomic_write_json(tmp_path / "y.json", {"a": 2})
    assert not (tmp_path / "y.json").exists() and not list(tmp_path.glob(".y.json.*.tmp"))   # no partial file, temp removed


@pytest.mark.req("R3-F14", "R3-F04")
def test_f14_audio_witness_is_evidence_only_with_its_aligned_full_frame_parent():
    """S2 blocker fix: the audio observer is registered, but only for AUDIO_SIGNAL with a same-film full frame within ±1 frame."""
    from vme.investigation.evidence import Witness, WitnessBundle, validate_bundle
    rel_f = "the frame stays unchanged relative to the previous frame while the lamp remains lit"
    rel_a = "an audio energy onset occurs while the frame stays unchanged relative to the previous frame"
    full = lambda wid, film=FA, f=10: Witness(wid, film, "seq", f, f, "FULL_FRAME", "VLM", rel_f)
    aud = lambda parent, observer="LOCAL_SIGNAL_ANALYSIS": Witness("A1", FA, "seq", 10, 10, "AUDIO_SIGNAL", observer, rel_a,
                                                                   parent_full_frame_witness=parent)
    ok = lambda *ws: validate_bundle(WitnessBundle("b", None, "x", list(ws)))
    assert ok(full("F1"), aud("F1"))["ok"]
    assert any(p.startswith("AUDIO_WITHOUT_FULL_FRAME_CONTEXT") for p in ok(full("F1"), aud(None))["problems"])
    assert any(p.startswith("AUDIO_WITHOUT_FULL_FRAME_CONTEXT") for p in ok(full("F1"), aud("F-missing"))["problems"])
    assert any(p.startswith("AUDIO_PARENT_MISALIGNED") for p in ok(full("F2", f=14), aud("F2"))["problems"])
    assert any(p.startswith("AUDIO_PARENT_MISALIGNED") for p in ok(full("F3", film=FB), aud("F3"))["problems"])
    assert any(p.startswith("AUDIO_SIGNAL_WRONG_OBSERVER") for p in ok(full("F1"), aud("F1", observer="VLM"))["problems"])
    vis = Witness("V1", FA, "seq", 10, 10, "FULL_FRAME", "LOCAL_SIGNAL_ANALYSIS", rel_f)
    assert any(p.startswith("LOCAL_SIGNAL_OBSERVER_ON_VISUAL_EVIDENCE") for p in ok(vis)["problems"])


@pytest.mark.req("R3-F13", "R3-F05")
def test_f13_conflicting_motion_owners_refuse_and_agreeing_owners_corroborate():
    import copy
    from vme.render.motion_program import compile_event_program
    decs, scope, brief = _motion_fixture()
    twin = copy.deepcopy(next(d for d in decs if d["decision_id"] == "PC-act"))
    twin["decision_id"] = "PC-act2"
    p = compile_event_program(decisions=decs + [twin], scope=scope, brief=brief, pack={"states": {}}, width=100, height=100, scale=1.0)
    t = next(t for t in p["tracks"] if t["kind"] == "ACTOR_ACTING")
    assert t["owner_decision_id"] == "PC-act" and t["co_owner_decision_ids"] == ["PC-act2"]
    twin["branches"][0]["motion_program"]["method"] = "HOLD_THEN_MOVE"
    with pytest.raises(Blocked) as e:                     # list order must never decide between disagreeing source decisions
        compile_event_program(decisions=decs + [twin], scope=scope, brief=brief, pack={"states": {}}, width=100, height=100, scale=1.0)
    assert e.value.code == "CONFLICTING_MOTION_OWNERS" and "PC-act2=HOLD_THEN_MOVE" in e.value.detail


@pytest.mark.req("R3-F13")
def test_f13_camera_only_motion_cannot_stand_in_for_actor_acting():
    from vme.render.motion_program import compile_event_program
    decs, scope, brief = _motion_fixture(drop="PC-act")
    with pytest.raises(Blocked) as e:
        compile_event_program(decisions=decs, scope=scope, brief=brief, pack={"states": {}}, width=100, height=100, scale=1.0)
    assert e.value.code == "MOTION_TRACK_UNOWNED"


@pytest.mark.req("R3-F14")
def test_f14_av_gate_fails_on_missing_static_or_off_sync_audio(tmp_path):
    from vme.reference.audio import build_cue_track, make_original_cue_asset, mux, verify_av, study_interval
    from vme.fixtures.synthetic import make_clip
    v = make_clip(tmp_path / "v.mp4", frames=60, fps=30)
    asset = make_original_cue_asset(tmp_path / "cue.wav")
    good = mux(v, build_cue_track(asset, [10, 30], fps=30, frames=60, out_wav=tmp_path / "a.wav"), tmp_path / "good.mp4")
    assert verify_av(good, cue_frames=[10, 30], fps=30, frames=60)["ok"]
    off = mux(v, build_cue_track(asset, [16, 30], fps=30, frames=60, out_wav=tmp_path / "b.wav"), tmp_path / "off.mp4")
    r = verify_av(off, cue_frames=[10, 30], fps=30, frames=60)
    assert not r["ok"] and "CUE_NOT_HEARD_AT_FRAME:10" in r["problems"] and any(p.startswith("UNSCHEDULED_ONSET") for p in r["problems"])
    assert verify_av(v, cue_frames=[10], fps=30, frames=60)["problems"] == ["AUDIO_STREAM_MISSING"]
    import subprocess
    from vme.reference.probe import require_tool
    silent = tmp_path / "silent.mp4"
    subprocess.run([require_tool("ffmpeg"), "-v", "error", "-y", "-i", str(v), "-f", "lavfi", "-t", "2", "-i", "anullsrc=r=16000:cl=mono",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(silent)], check=True, capture_output=True)
    rs = verify_av(silent, cue_frames=[10], fps=30, frames=60)
    assert "AUDIO_SILENT" in rs["problems"] and "CUE_NOT_HEARD_AT_FRAME:10" in rs["problems"]
    assert study_interval(v, start_pts=0, end_pts=1, fps=30, film_sha256=FA, sequence_id="s")["status"] == "AUDIO_STREAM_ABSENT"


@pytest.mark.req("R3-F14")
def test_f14_audio_decision_needs_a_local_source_audio_witness_and_sound_needs_approval(store, ws, tmp_path):
    _w(store, "W-1", FA, 3, ["VISUAL_AUDIO_TIMING"])
    a = _ans(["W-1"], op="op.audio_cue", action="SYNTHETIC: place the cue at the frame where the near form overlaps the edge")
    a["BRANCHES"][0]["MOTION_PROGRAM"] = {"track_kind": "AUDIO", "method": "CUE_ON_EVENT", "cue_offset_frames": 0, "witness_ids": ["W-1"]}
    d = _author(store, _q(), a, _man(store, ["W-1"]), dims=("VISUAL_AUDIO_TIMING",), did="PC-AU")
    assert d["status"] == "RESEARCH_ONLY" and d["research_only_reason"].startswith("AUDIO_UNSTUDIED")
    from vme.loop.real import RealLoopRunner, RealProviders
    from vme.reference.audio import make_original_cue_asset
    from vme.util import sha256_file
    snd = make_original_cue_asset(tmp_path / "c.wav")
    r = RealLoopRunner(ws, run_id="REAL-A", providers=RealProviders(vision_client_factory=lambda: None, vision_transport_kind="SIMULATED",
                                                                   image_transport=None, image_transport_kind="SIMULATED"))
    with pytest.raises(Blocked) as e:
        r._mux_audio(store, tmp_path / "x.mp4", {"audio_cues": [{"frame": 1}]}, {"approved_asset_sha256": sha256_file(snd), "asset_path": str(snd)},
                     fps=30, frames=30)
    assert e.value.code == "NO_APPROVED_SOUND_ASSET"


@pytest.mark.req("R3-F15")
def test_f15_render_gate_failures_are_fatal_and_diagnostic_scope_is_separate(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import patch
    from vme.render import renderer
    calls = []
    gate = SimpleNamespace(authorize_render=lambda *a, **k: None, transition=lambda *a, **k: calls.append(a))
    scene = {"width": 16, "height": 16, "fps": 30, "durationInFrames": 2, "camera": {}, "layers": [], "motion_contract": {"expected_independent_motion": True}}
    root = tmp_path / "remotion"
    (root / "node_modules" / "remotion").mkdir(parents=True)

    def run(ff, mo, **kw):
        with patch.object(renderer, "REMOTION_DIR", root), patch.object(renderer, "require_tool", return_value="node"), \
                patch.object(renderer.subprocess, "run", return_value=SimpleNamespace(returncode=0, stderr="", stdout="")), \
                patch.object(renderer, "ffprobe_verify", return_value={"ok": ff, "problems": ["FRAME_COUNT_MISMATCH"]}), \
                patch.object(renderer, "motion_evidence", return_value={"ok": mo, "verdict": "STATIC"}), \
                patch.object(renderer, "sha256_file", return_value="S"):
            return renderer.render_video(dict(scene, **kw.pop("scene_over", {})), {}, tmp_path / "c.mp4", gate=gate, run_id="R", **kw)
    for ff, mo, code in ((False, True, "TECHNICAL_RENDER_FAILED"), (True, False, "TECHNICAL_MOTION_FAILED")):
        with pytest.raises(Blocked) as e:
            run(ff, mo)
        assert e.value.code == code
    assert calls and calls[-1][1] == "ASSETS_APPROVED"                 # nothing released for review
    with pytest.raises(Blocked) as e:
        run(True, True, scene_over={"motion_contract": {"expected_independent_motion": False}})
    assert e.value.code == "UNAPPROVED_STATIC_FILM"
    assert run(True, False, diagnostic_label="DIAGNOSTIC_NOT_APPROVED")["label"] == "DIAGNOSTIC_NOT_APPROVED"


# ======================================================================== F16 / F17 / F18
@pytest.mark.req("R3-F16")
def test_f16_pixel_false_claim_refuted_by_native_review_never_promotes(store):
    from vme.review.qualification import review_source_claim
    _w(store, "W-1", FA, 3, ["WORLD_ASSEMBLY"])
    d = _author(store, _q(), _ans(["W-1"]), _man(store, ["W-1"]), did="PC-R")
    assert d["status"] == "EXECUTABLE_CANDIDATE" and d["source_art_review"].startswith("UNREVIEWED")
    with pytest.raises(Blocked) as e:
        review_source_claim(store, "PC-R", verdict="REFUTED", by=HUMAN, statement="x", checked_witness_ids=["W-other"])
    assert e.value.code == "REVIEW_MUST_CHECK_THE_CITED_NATIVE_WITNESSES"
    review_source_claim(store, "PC-R", verdict="REFUTED", by=HUMAN, statement="SYNTHETIC: the pixels show no overlap", checked_witness_ids=["W-1"])
    d2 = store.get("ConditionalVisualDecision", "PC-R")
    assert d2["status"] == "RESEARCH_ONLY" and d2["claim_state"] == "REFUTED_BY_SOURCE_REVIEW" and d2["version"] == d["version"] + 1
    with pytest.raises(Blocked):
        review_source_claim(store, "PC-R", verdict="APPROVED", by="model", statement="x", checked_witness_ids=["W-1"])


@pytest.mark.req("R3-F17")
def test_f17_still_only_transfer_never_qualifies_motion_or_av(store):
    from vme.review.qualification import capability_verdict, STATUS
    store.put("LoopTransition", "REAL-Q:S9", {"run_id": "REAL-Q", "stage": "S9", "status": "COMPLETED", "evidence_origin": "SIMULATED_VLM_TRANSPORT",
                                              "outputs": {"transfer": "STILL_TRANSFER_PENDING_AWAITING_REVIEW"}})
    v = capability_verdict(store, "REAL-Q")
    assert v["capabilities"]["HELDOUT_TRANSFER"].startswith("BLOCKED") and v["ready_for_15_plus_1"] is False
    assert v["capabilities"]["SOURCE_ART_TRUTH"].startswith("BLOCKED") and "ORIGINAL_AUDIOVISUAL_QUALIFIED" not in v["capabilities"].values()
    assert len(v["capabilities"]) == 16 and "ORIGINAL_AUDIOVISUAL_QUALIFIED" in STATUS


@pytest.mark.req("R3-F18")
def test_f18_output_budget_caps_packets_and_truncation_splits_without_losing_targets(ws, indexed24, tmp_path, monkeypatch):
    from vme.loop.real import RealLoopRunner, RealProviders, RealLoopConfig
    from vme.vision.claude_adapter import ClaudeBatchVisionAdapter, default_caps
    from vme.vision.runner import PacketRunner, plan_packets, coverage_for_range
    from vme.providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
    from vme.testing.simulated_anthropic import SimulatedAnthropicClient
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    clip, idx, loader = indexed24
    film = idx[0]["film_sha256"]
    reg = AuthorizationRegistry(tmp_path / "authz")
    reg.issue(provider="anthropic-claude", model_id="claude-opus-5-5", task_categories=["source_vision"], spend_cap_usd=50, issued_by=HUMAN,
              confirm_phrase=CONFIRM_PHRASE, source_upload_consent=True, allowed_source_shas=[film])
    client = SimulatedAnthropicClient(tmp_path / "sim", mode="truncate_over_4")
    vis = ClaudeBatchVisionAdapter(default_caps(), reg, tmp_path / "vs", client_factory=lambda: client, transport_kind="SIMULATED")
    r = RealLoopRunner(ws, run_id="REAL-F18", providers=RealProviders(vision_client_factory=lambda: client, vision_transport_kind="SIMULATED",
                                                                       image_transport=None, image_transport_kind="SIMULATED"),
                       config=RealLoopConfig(target_per_packet=8, per_target_output_tokens=4000))
    assert r._budgeted_targets(vis) == 3                                        # (16000-2000)//4000
    r.cfg.per_target_output_tokens = 1400
    st = ws.store()
    plans = plan_packets(idx, 0, 7, film_sha=film, pass_id="REAL-F18-L0", cluster_id="seq", model_version=vis.caps.model_id,
                         max_images=vis.caps.max_images_per_request, target_per_packet=8)
    pr = PacketRunner(st, ws.vision_dir, idx, loader, vis, source_is_synthetic=False, active_questions=[{"question_id": "Q", "text": "t"}])
    res = pr.resume(plans)
    assert list(res["results"].values()) == ["NEEDS_REINSPECTION"]
    res = r._split_truncated(st, pr, plans, res, idx, film, "REAL-F18-L0", "seq", vis)
    assert set(res["results"].values()) == {"SEMANTIC_COMMITTED"} and len(res["results"]) == 2
    assert coverage_for_range(st, film, "REAL-F18-L0", 0, 7)["complete"]
    assert st.conn.execute("SELECT state FROM packets WHERE packet_id=?", (plans[0].packet_id,)).fetchone()[0] == "SUPERSEDED_BY_SPLIT"
    st.close()
