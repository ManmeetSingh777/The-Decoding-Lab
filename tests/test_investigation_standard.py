"""Addendum 28 investigation standard: versioned protocol, every-frame temporal records, sufficiency for a producing choice,
model-drift calibration and the portable Investigation Capsule (ST28-01, 05..08, 12, 17..20, 23). SYNTHETIC data only."""
from __future__ import annotations

import json
import shutil
import zipfile

import pytest

from vme.util import Blocked

HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"


@pytest.mark.req("ST28-18", "A28-PROTOCOL")
def test_protocol_is_versioned_hashed_and_bound():
    from vme.vision.protocol import PROTOCOL_SHA, PROTOCOL_VERSION, pass_instructions, bind, verify_protocol, PASS_ORDER, protocol_payload
    from vme.util import digest
    assert PROTOCOL_VERSION == "VME-A28-1" and PROTOCOL_SHA == digest(protocol_payload())
    for p in PASS_ORDER:
        t = pass_instructions(p)
        assert f"PROTOCOL VME-A28-1 sha={PROTOCOL_SHA}" in t and f"pass={p}" in t and "WHOLE -> PARTS -> WHOLE" in t
    with pytest.raises(Blocked) as e:
        bind(protocol={"version": PROTOCOL_VERSION, "sha": PROTOCOL_SHA}, source={})
    assert e.value.code == "PROTOCOL_BINDING_MISSING"
    with pytest.raises(Blocked) as e:
        verify_protocol("VME-A28-1", "0" * 64)
    assert e.value.code == "PROTOCOL_DRIFT"
    mig = {"from_sha": "0" * 64, "to_sha": PROTOCOL_SHA, "calibration_report": "SYNTHETIC calibration on fixed witness set"}
    assert verify_protocol("VME-A28-1", "0" * 64, migration=mig)["status"] == "EXPLICIT_MIGRATION"


def _manifest(n=3):
    return [{"frame_id": f"{'a' * 16}:{i}", "source_sha": "a" * 16, "pts": i, "pts_time": i / 30, "image_sha": f"{i:064x}",
             "width": 64, "height": 36} for i in range(n)]


def _obs(m, **over):
    o = {f: [] for f in ("active_question_ids", "actually_visible_actor_and_object_ids", "visible_design_relations",
                         "character_face_limb_contact_state", "simultaneous_event_links", "material_finish_or_colour_change",
                         "native_detail_followups", "source_fact_statements", "hypothesis_or_uncertainty", "confidence_limitations",
                         "unexplained_phenomena")}
    o.update(frame_id=m["frame_id"], source_sha=m["source_sha"], pts_time=m["pts_time"], request_id="p", submitted_image_sha=m["image_sha"],
             scene_and_world_state="SYNTHETIC world", focal_whole_artwork_state=f"SYNTHETIC: focal form at {m['frame_id']} stays in front of the far layer",
             visible_layer_depth_attention_state="UNKNOWN", camera_vs_actor_vs_drawing_state="UNKNOWN",
             changed_since_prior_frame=[{"kind": "OBSERVED_DIFF", "what": "SYNTHETIC: near hand moves toward the handle"}],
             persistent_state_ids=["actor_1"],
             visible_design_relations=[{"relation": f"SYNTHETIC: at {m['frame_id']} the near hand overlaps the far handle edge while the "
                                                    "background layer stays behind", "dimensions": ["CHARACTER_BODY_HAND_CONTACT"]}])
    o.update(over)
    return o


def _resp(obs):
    return {"frame_observations": obs, "packet_transition_graph": {"edges": []},
            "boundary_state": {"active_objects": ["actor_1"], "open_events": []}, "reconciled_events": []}


@pytest.mark.req("ST28-01", "ST28-06")
def test_every_frame_records_empty_generic_and_lost_identity_are_rejected():
    from vme.vision.contracts import validate_packet_response
    m = _manifest()
    assert validate_packet_response(_resp([_obs(x) for x in m]), m, None, images_actually_sent=3)["ok"]
    bad = [_obs(x) for x in m]
    bad[1]["focal_whole_artwork_state"] = " "
    v = validate_packet_response(_resp(bad), m, None, images_actually_sent=3)
    assert not v["ok"] and any(p.startswith("EMPTY_FRAME_ENTRY") for p in v["problems"])
    same = [_obs(x, focal_whole_artwork_state="SYNTHETIC: identical text", changed_since_prior_frame=[{"kind": "OBSERVED_DIFF", "what": "x"}])
            for x in m]
    assert "GENERIC_UNDIFFERENTIATED_ENTRIES" in validate_packet_response(_resp(same), m, None, images_actually_sent=3)["problems"]
    prior = {"active_objects": ["actor_1", "prop_7"], "open_events": []}
    v = validate_packet_response(_resp([_obs(x) for x in m]), m, prior, images_actually_sent=3)
    assert any(p.startswith("BOUNDARY_IDENTITY_NOT_RECONCILED") and "prop_7" in p for p in v["problems"])
    ok = [_obs(x) for x in m]
    ok[0]["ended_state_ids"] = ["prop_7"]
    assert validate_packet_response(_resp(ok), m, prior, images_actually_sent=3)["ok"]
    missing = [_obs(x) for x in m]
    del missing[2]["persistent_state_ids"]
    assert any("persistent_state_ids" in p for p in validate_packet_response(_resp(missing), m, None, images_actually_sent=3)["problems"])


@pytest.mark.req("ST28-05", "A28-PROTOCOL")
def test_packet_request_carries_protocol_binding_and_real_images():
    from vme.vision.prompt import build_vision_request
    from vme.vision.protocol import PROTOCOL_SHA
    m = _manifest()
    r = build_vision_request("pkt", m, [], [{"question_id": "Q", "text": "t"}], None)
    assert r["protocol"] == {"version": "VME-A28-1", "sha": PROTOCOL_SHA, "pass_id": "P1"}
    assert [t["bytes_sha"] for t in r["binding"]["target_images"]] == [x["image_sha"] for x in m]
    assert "alternatives until discriminated" in r["instructions"]          # camera/redraw/object motion are not assumed facts


def _good_answer(wids):
    return {"answer_status": "INFERRED", "REMAINING_UNKNOWN": ["SYNTHETIC: profile view unseen"],
            "SOURCE_VISIBLE_FACTS": [{"relation": f"SYNTHETIC: in {w} the near hand overlaps the handle edge while the sleeve stays behind the prop",
                                      "witness_ids": [w]} for w in wids],
            "CONSTRUCTION_EXPLANATION": "SYNTHETIC: hand and prop are drawn as one contact state rather than a transformed arm",
            "BRANCHES": [{"when": {"action": "grip"}, "operation_id": "op.hand_prop_contact",
                          "construction_action": "SYNTHETIC: draw the {subject}'s near hand wrapped over the {original_prop} edge in one drawing"}]}


@pytest.mark.req("ST28-08", "ST28-12", "MODEL_STANDARD_DRIFT")
def test_shallow_structurally_valid_answer_is_insufficient_and_alternative_is_kept_as_competitor():
    from vme.vision.protocol import assess_sufficiency, competing_hypothesis
    wids = {"W-1", "W-2"}
    shallow = {"answer_status": "INFERRED", "REMAINING_UNKNOWN": ["x"],
               "SOURCE_VISIBLE_FACTS": [{"relation": "SYNTHETIC: vibrant polished premium look", "witness_ids": ["W-1"]}],
               "CONSTRUCTION_EXPLANATION": "great lighting",
               "BRANCHES": [{"when": {"action": "grip"}, "operation_id": "op.hand_prop_contact", "construction_action": "make it dynamic and fluid"}]}
    a = assess_sufficiency(shallow, producing_operator="op.hand_prop_contact", known_witness_ids=wids)
    assert a["verdict"] == "INSUFFICIENT_FOR_PRODUCING_CHOICE"
    assert {"FACTS_ARE_NOT_RELATIONAL_OR_ARE_ADJECTIVE_ONLY", "MECHANISM_HYPOTHESIS_ABSENT_OR_VAGUE"} <= set(a["reasons"])
    uncited = _good_answer(["W-9"])
    assert "NO_FACT_CITES_A_REAL_WITNESS" in assess_sufficiency(uncited, producing_operator="op.hand_prop_contact", known_witness_ids=wids)["reasons"]
    good = _good_answer(["W-1"])
    g = assess_sufficiency(good, producing_operator="op.hand_prop_contact", known_witness_ids=wids)
    assert g["verdict"] == "SUFFICIENT_FOR_PRODUCING_CHOICE"
    accepted = {"decision_id": "PC-1", "version": 3, "branches": [{"construction_action": "SYNTHETIC: draw the arm transformed toward the prop"}]}
    c = competing_hypothesis(accepted, good, g)
    assert c["status"] == "COMPETING_HYPOTHESIS_UNVERIFIED" and c["against_version"] == 3 and "NOT overwritten" in c["resolution_needed"]
    assert competing_hypothesis(accepted, shallow, a) is None


@pytest.mark.req("ST28-23")
def test_simulated_origin_never_becomes_real_source_qualified(tmp_path):
    from vme.state.capsule import validate_capsule
    cap = {"origin": "REAL_SOURCE_QUALIFIED"}
    assert any("origin" in e for e in validate_capsule(cap))


@pytest.mark.req("ST28-17", "ST28-19", "ST28-20", "R12", path="REAL")
def test_capsule_cold_start_resumes_first_uncommitted_operation_without_rebilling(tmp_path, monkeypatch):
    """Kill after a question's raw answer arrives but before its decision is published, export the capsule, import it into a fresh
    destination under a different executor process, verify, resume; then a second capsule reproduces the pinned compile byte-for-byte."""
    from vme.testing.drill import build_drill_workspace, drill_providers, drill_config, drive, enable_network_flag
    from vme.loop.real import RealLoopRunner
    from vme.loop.human import approve_selection
    from vme.state.capsule import export_capsule, import_and_verify
    from vme.state.workspace import Workspace
    from vme.vision.runner import SimulatedCrash
    enable_network_flag()
    src_root = tmp_path / "envA"
    ws = build_drill_workspace(src_root)["ws"]
    prov, client = drill_providers(src_root)
    R = lambda w: RealLoopRunner(w, run_id="REAL-CAP", providers=prov, config=drill_config()).run()
    assert R(ws)["reason"] == "AWAITING_SELECTION_APPROVAL"
    st = ws.store()
    m = st.get("SelectedSequenceManifest", "REAL:15")
    st.close()
    approve_selection(ws, manifest_sha=m["manifest_sha"], approved_by=HUMAN)
    monkeypatch.setenv("VME_CRASH_AT", "real_s2_after_answer_before_decision")
    with pytest.raises(SimulatedCrash):
        R(ws)
    monkeypatch.delenv("VME_CRASH_AT")
    billed_at_crash = client.billed_requests()
    raws = sorted((ws.root / "providers" / "anthropic").glob("raw_*.json"))
    assert raws
    e1 = export_capsule(ws, "REAL-CAP", tmp_path / "capsule_A.zip")
    with zipfile.ZipFile(tmp_path / "capsule_A.zip") as z:
        names = z.namelist()
    assert "state/INVESTIGATION_CAPSULE.json" in names and not any(n.endswith(".mp4") for n in names)
    cap = e1["capsule"]
    assert cap["coverage"]["first_uncommitted_frame"] is None and cap["coverage"]["verified_vision_frames"]
    assert cap["active_problem"]["controlling_question"]["status"] == "OPEN"
    # fresh destination, different executor: verify before resuming
    v = import_and_verify(tmp_path / "capsule_A.zip", tmp_path / "envB", sources_folder=src_root / "drill_sources")
    assert v["status"] == "VERIFIED_READY_TO_RESUME", v
    assert v["protocol"]["status"] == "IDENTICAL_PROTOCOL" and v["committed_frames"] == len(cap["coverage"]["verified_vision_frames"])
    wsB = Workspace(tmp_path / "envB")
    out = drive(wsB, prov, run_id="REAL-CAP", max_rounds=40)
    assert out["result"].get("completed_through") == "S9", out["log"]
    stB = wsB.store()
    tB = {t["stage"]: t for t in stB.list("LoopTransition") if t["run_id"] == "REAL-CAP"}
    assert tB["S1"]["status"] == "COMPLETED"
    stB.close()
    # the journaled answer was reused: no question re-billed for the crashed step (the frame study was not redone)
    assert client.duplicate_creates() == 0
    assert client.billed_requests() >= billed_at_crash
    e2 = export_capsule(wsB, "REAL-CAP", tmp_path / "capsule_B.zip")
    assert e2["capsule"]["pinned_rehearsal"]["reference_shas"]
    v2 = import_and_verify(tmp_path / "capsule_B.zip", tmp_path / "envC", sources_folder=src_root / "drill_sources")
    assert v2["rehearsal"]["byte_identical_logical_payload"] is True and v2["status"] == "VERIFIED_READY_TO_RESUME", v2
    (tmp_path / "envC_report.json").write_text(json.dumps(v2, default=str), encoding="utf-8")
    # corrupt/missing artifact → exact blocker
    shutil.copy(tmp_path / "capsule_B.zip", tmp_path / "capsule_C.zip")
    with zipfile.ZipFile(tmp_path / "capsule_B.zip") as zin, zipfile.ZipFile(tmp_path / "capsule_D.zip", "w") as zout:
        for n in zin.namelist():
            if "/references/" in n and n.endswith(".png"):
                continue
            zout.writestr(n, zin.read(n))
    vd = import_and_verify(tmp_path / "capsule_D.zip", tmp_path / "envD", sources_folder=src_root / "drill_sources")
    assert vd["status"] == "BLOCKED_MISSING_EVIDENCE"
    assert {m["sha256"] for m in vd["missing_capsule_artifacts"] if m["artifact"] == "reference_image"} ==         set(e2["capsule"]["provenance"]["reference_image_sha256s"])
    assert vd["rehearsal"]["recomputed"]["error"] == "REFERENCE_BYTES_MISSING"
