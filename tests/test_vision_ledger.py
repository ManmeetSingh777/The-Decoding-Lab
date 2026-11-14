"""Per-frame VLM packet ledger, validation, crash/resume and coverage truth
(A19, A27, A28, A61–A66, B03–B08, C03, C05, C35, ADD25-F01..F08, ADD25-R01, ADD26-F01/F02)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT
from vme.util import Blocked


def _runner(store, ws, indexed, mode="correct", max_images=8, queryable=True, remote=None):
    from vme.vision.providers import MockVisionProvider
    from vme.vision.runner import PacketRunner, plan_packets
    clip, idx, loader = indexed
    prov = MockVisionProvider(remote or (ws.root / f"remote_{mode}"), mode=mode, max_images=max_images, queryable=queryable)
    plans = plan_packets(idx, 0, len(idx) - 1, film_sha=idx[0]["film_sha256"], pass_id=f"p_{mode}", cluster_id="CL",
                         model_version="mock", max_images=max_images, target_per_packet=8)
    return PacketRunner(store, ws.vision_dir, idx, loader, prov, source_is_synthetic=True,
                        active_questions=[{"question_id": "Q1", "text": "SYNTHETIC"}]), plans, prov


@pytest.mark.req("ADD25-F01", "ADD25-F07", "A61")
def test_plan_exact_targets_and_provider_image_limit(indexed24):
    from vme.vision.runner import plan_packets
    _, idx, _ = indexed24
    plans = plan_packets(idx, 3, 20, film_sha="f", pass_id="p", cluster_id="c", model_version="m", max_images=12, target_per_packet=8)
    assert [k for p in plans for k in p.target_indices] == list(range(3, 21))
    small = plan_packets(idx, 0, 23, film_sha="f", pass_id="p", cluster_id="c", model_version="m", max_images=2)
    assert all(len(p.target_indices) + len(p.context_before) + len(p.context_after) <= 2 for p in small)
    assert [k for p in small for k in p.target_indices] == list(range(24))


@pytest.mark.req("A27", "A61", "A62", "C03", "B03")
def test_full_mock_pass_commits_every_frame_but_never_real_vlm(store, ws, indexed24):
    from vme.vision.runner import coverage_for_range
    pr, plans, prov = _runner(store, ws, indexed24)
    pr.register(plans)
    res = pr.resume(plans)
    assert set(res["results"].values()) == {"SEMANTIC_COMMITTED"}
    cov = coverage_for_range(store, plans[0].film_sha256, "p_correct", 0, 23)
    assert cov["complete"] and cov["verified"] == 24
    assert not cov["real_vlm"] and cov["statuses"] == ["MOCK_VERIFIED_SYNTHETIC"]


@pytest.mark.req("C03", "ADD26-F01")
def test_mock_provider_on_real_source_forbidden(store, ws, indexed24):
    from vme.vision.providers import MockVisionProvider
    from vme.vision.runner import PacketRunner
    _, idx, loader = indexed24
    with pytest.raises(Blocked) as e:
        PacketRunner(store, ws.vision_dir, idx, loader, MockVisionProvider(ws.root / "r"), source_is_synthetic=False)
    assert e.value.code == "MOCK_PROVIDER_ON_REAL_SOURCE_FORBIDDEN"


@pytest.mark.parametrize("mode,expected,req", [
    ("omit_one", "NEEDS_REINSPECTION", "ADD25-F03"), ("summary_only", "NEEDS_REINSPECTION", "A62"),
    ("subsample", "NEEDS_REINSPECTION", "A61"), ("hash_mismatch", "QUARANTINED", "B05"),
    ("received_fewer", "NEEDS_REINSPECTION", "ADD25-F07"), ("corrupt_json", "NEEDS_REINSPECTION", "C35")])
def test_bad_vlm_responses_never_advance_coverage(store, ws, indexed24, mode, expected, req):
    from vme.vision.runner import coverage_for_range
    pr, plans, _ = _runner(store, ws, indexed24, mode=mode)
    st = pr.run(plans[0])
    assert st == expected
    cov = coverage_for_range(store, plans[0].film_sha256, f"p_{mode}", plans[0].target_indices[0], plans[0].target_indices[-1])
    assert cov["verified"] == 0 and not cov["complete"]


test_bad_vlm_responses_never_advance_coverage = pytest.mark.req("ADD25-F03", "A62", "A61", "B04", "B05", "ADD25-F07", "ADD26-F02")(
    test_bad_vlm_responses_never_advance_coverage)


@pytest.mark.req("ADD25-F05")
def test_vague_entries_flagged_weak_not_artistic(store, ws, indexed24):
    pr, plans, _ = _runner(store, ws, indexed24, mode="vague")
    st = pr.run(plans[0])
    assert st == "NEEDS_REINSPECTION"  # identical generic text across frames = undifferentiated


@pytest.mark.req("A63", "C05")
def test_boundary_event_must_be_reconciled(store, ws, indexed24, tmp_path):
    from vme.util import atomic_write_json
    pr, plans, _ = _runner(store, ws, indexed24, mode="no_reconcile")
    # commit packet 0 with a correct provider, then plant an open event (head turn crossing the boundary)
    from vme.vision.providers import MockVisionProvider
    pr.provider = MockVisionProvider(ws.root / "remote_ok_b")
    assert pr.run(plans[0]) == "SEMANTIC_COMMITTED"
    bp = ws.vision_dir / plans[0].pass_id / plans[0].packet_id / "boundary.json"
    b = json.loads(bp.read_text())
    b["open_events"] = [{"event_id": "head_turn_1", "kind": "head_turn", "started_frame": 7, "actors": ["actor_a"]},
                        {"event_id": "grip_1", "kind": "hand_prop_contact", "started_frame": 6, "actors": ["actor_a", "prop_b"]}]
    atomic_write_json(bp, b)
    pr.provider = MockVisionProvider(ws.root / "remote_noreconcile", mode="no_reconcile")
    assert pr.run(plans[1]) == "NEEDS_REINSPECTION"
    pr.provider = MockVisionProvider(ws.root / "remote_ok_c")
    assert pr.run(plans[1]) == "SEMANTIC_COMMITTED"  # correct provider reconciles both open events


def _crash_child(ws_root: Path, clip: Path, point: str, remote: Path, extra_env=None):
    code = f"""
import sys; sys.path.insert(0, r'{ROOT}')
from pathlib import Path
from vme.state.workspace import Workspace
from vme.fixtures.loop_fixtures import index_and_loader
from vme.vision.providers import MockVisionProvider
from vme.vision.runner import PacketRunner, plan_packets
ws = Workspace(Path(r'{ws_root}')).ensure(); st = ws.store()
idx, loader = index_and_loader(Path(r'{clip}'), Path(r'{ws_root}') / 'idx')
prov = MockVisionProvider(Path(r'{remote}'), max_images=8)
plans = plan_packets(idx, 0, len(idx)-1, film_sha=idx[0]['film_sha256'], pass_id='crash', cluster_id='CL', model_version='mock', max_images=8)
pr = PacketRunner(st, ws.vision_dir, idx, loader, prov, source_is_synthetic=True, active_questions=[{{'question_id':'Q1','text':'S'}}])
pr.register(plans)
print(pr.resume(plans))
"""
    env = {**os.environ, "VME_CRASH_AT": point, "VME_CRASH_HARD": "1", **(extra_env or {})}
    if point == "NONE":
        env.pop("VME_CRASH_AT")
    return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=300)


@pytest.mark.parametrize("point", ["after_inputs_ready", "after_inflight_commit", "after_submit_before_save",
                                   "after_raw_response", "mid_semantic_commit", "after_semantic_commit"])
def test_hard_kill_at_every_boundary_then_resume_new_process(tmp_path, clip24, point):
    ws_root, remote = tmp_path / "w", tmp_path / "remote"
    r1 = _crash_child(ws_root, clip24, point, remote)
    assert r1.returncode == 97, r1.stderr[-800:]
    r2 = _crash_child(ws_root, clip24, "NONE", remote)
    assert r2.returncode == 0, r2.stderr[-800:]
    import sqlite3
    con = sqlite3.connect(str(ws_root / "store" / "vme.sqlite"))
    states = [r[0] for r in con.execute("SELECT state FROM packets WHERE pass_id='crash'")]
    seen = con.execute("SELECT COUNT(DISTINCT frame_index) FROM frame_vision WHERE pass_id='crash'").fetchone()[0]
    con.close()
    assert set(states) == {"SEMANTIC_COMMITTED"} and seen == 24
    from vme.util import read_json
    subs = [read_json(p)["submissions"] for p in remote.glob("*.json")]
    billed = [read_json(p)["billed"] for p in remote.glob("*.json")]
    assert len(billed) == len(states)  # exactly one billed task per packet, never two
    assert all(s <= 2 for s in subs)


test_hard_kill_at_every_boundary_then_resume_new_process = pytest.mark.req(
    "A19", "A64", "A65", "B06", "B07", "C35", "ADD25-F08", "ADD24-D4-1")(test_hard_kill_at_every_boundary_then_resume_new_process)


@pytest.mark.req("A65", "B06", "ADD26-R02")
def test_unqueryable_pending_task_is_unknown_billing_not_resubmitted(store, ws, indexed24, monkeypatch):
    from vme.vision.runner import SimulatedCrash
    pr, plans, prov = _runner(store, ws, indexed24, queryable=False)
    monkeypatch.setenv("VME_CRASH_AT", "after_submit_before_save")
    with pytest.raises(SimulatedCrash):
        pr.run(plans[0])
    monkeypatch.delenv("VME_CRASH_AT")
    assert pr.run(plans[0]) == "UNKNOWN_BILLING"
    assert prov.billed_count() == 1


@pytest.mark.req("A64", "B08", "ADD25-R01")
def test_semantic_checkpoint_records_questions_boundary_and_next(store, ws, indexed24):
    pr, plans, _ = _runner(store, ws, indexed24)
    pr.register(plans)
    pr.run(plans[0])
    ck = store.get("SemanticPacketCheckpoint", plans[0].packet_id)
    assert ck["next_frame_index"] == plans[0].target_indices[-1] + 1
    assert ck["unresolved_questions"] == ["Q1"] and Path(ck["boundary_state_path"]).exists()
    assert "run packet starting at frame" in ck["exact_next_action"]
    from vme.state.handoff import exact_next_operation
    nxt = exact_next_operation(ws)
    assert nxt["kind"] == "RUN_VISION_PACKET" and nxt["start_frame"] == plans[1].target_indices[0]


@pytest.mark.req("C35", "A64")
def test_committed_artifact_tamper_quarantined_on_verify(store, ws, indexed24):
    pr, plans, _ = _runner(store, ws, indexed24)
    pr.run(plans[0])
    f = ws.vision_dir / plans[0].pass_id / plans[0].packet_id / "frames.jsonl"
    f.write_text(f.read_text() + "{}\n")
    assert plans[0].packet_id in pr.verify_committed()


@pytest.mark.req("A28", "A05", phase="PAID")
def test_all_frame_vlm_estimate_blocks_without_verified_price():
    from vme.vision.providers import estimate_vision_cost
    assert estimate_vision_cost(None, 255676)["status"] == "BLOCKED_FOR_PRICE_VERIFICATION"


@pytest.mark.req("A28", "C38", "B24", phase="PAID")
def test_real_vision_adapter_refuses_without_network_consent(tmp_path, monkeypatch):
    from vme.vision.providers import HttpVisionAdapter, VisionCapabilities
    from vme.providers.authorization import AuthorizationRegistry
    caps = VisionCapabilities("vlm-x", "model-1", 8, 2048, True, False, 0.001, True, "TEST")
    ad = HttpVisionAdapter(caps, AuthorizationRegistry(tmp_path))
    req = {"target_frames": [{"frame_id": "a" * 16 + ":0"}], "context_frames": []}
    monkeypatch.delenv("VME_ALLOW_NETWORK", raising=False)
    with pytest.raises(Blocked) as e:
        ad.submit("t", req, [b"x"])
    assert e.value.code == "NETWORK_DISABLED"
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    with pytest.raises(Blocked) as e:
        ad.submit("t", req, [b"x"])
    assert e.value.code == "NO_PROVIDER_AUTHORIZATION"


@pytest.mark.req("A66")
def test_two_film_first_vs_five_reporting():
    from vme.reference.frame_index import validate_claimed_coverage
    films = {f"f{i}": 100 for i in range(5)}
    studied = {"f0": list(range(100)), "f1": list(range(100))}
    rep = {f: validate_claimed_coverage([{"presentation_index": i} for i in range(n)], studied.get(f, []))["complete"] for f, n in films.items()}
    assert sum(rep.values()) == 2 and not all(rep.values())


@pytest.mark.req("ADD25-F04")
def test_duplicate_frame_identity_distinct_presentation_indices(tmp_path):
    from vme.fixtures.synthetic import make_sixth_clip
    from vme.fixtures.loop_fixtures import index_and_loader
    c = make_sixth_clip(tmp_path / "dup.mp4", segments=[("gray", 6)])
    idx, _ = index_and_loader(c, tmp_path / "i")
    assert len({r["frame_content_sha256"] for r in idx}) == 1  # identical pixels
    assert [r["presentation_index"] for r in idx] == list(range(6))  # but distinct verified source frames
