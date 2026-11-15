"""REAL-path S0–S9: production handlers driven through SIMULATED transports (labelled). path="REAL" marks
tests that exercise vme.loop.real; their evidence is wiring evidence only (never real learning or art)."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT
from vme.util import Blocked, read_json, atomic_write_json

REAL_MODULES = ["vme/loop/real.py", "vme/style/authoring.py", "vme/vision/claude_adapter.py", "vme/skills/runtime.py", "vme/loop/human.py",
                "vme/reference/roles.py"]


@pytest.mark.req("ADD26-S0S9", "C13", path="REAL")
def test_real_modules_never_import_fixtures_or_testing():
    import ast
    for m in REAL_MODULES:
        tree = ast.parse((ROOT / m).read_text(encoding="utf-8"))
        mods = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + \
               [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert not [x for x in mods if "fixtures" in x or "testing" in x], (m, mods)
    assert not re.search(r'mode == "REAL"', (ROOT / "vme/loop/stages.py").read_text(encoding="utf-8").replace(
        'if mode == "REAL":\n            raise Blocked("REAL_MODE_MOVED"', ""))


@pytest.fixture(scope="module")
def drill(tmp_path_factory):
    from vme.testing.drill import build_drill_workspace, drill_providers, drive, enable_network_flag
    root = tmp_path_factory.mktemp("realdrill")
    enable_network_flag()
    d = build_drill_workspace(root)
    prov, client = drill_providers(root)
    res = drive(d["ws"], prov, run_id="REAL-DRILL")
    os.environ.pop("VME_ALLOW_NETWORK", None)
    return d["ws"], res, client, root


@pytest.mark.req("ADD26-S0S9", "ADD24-S0S4-REAL", "ADD25-L0-REAL", "A11", "A52", "C12", "C13", path="REAL")
def test_full_real_path_drill_completes_s0_to_s9(drill):
    ws, res, client, _ = drill
    assert res["result"].get("completed_through") == "S9", res
    st = ws.store()
    T = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == "REAL-DRILL"}
    assert all(T[s]["status"] == "COMPLETED" and T[s]["evidence_origin"] == "SIMULATED_VLM_TRANSPORT" for s in T)
    assert T["S1"]["outputs"]["statuses"] == ["SIMULATED_TRANSPORT_FIXTURE"] and T["S1"]["outputs"]["sixth_included"]
    st.close()
    assert client.duplicate_creates() == 0


@pytest.mark.req("A61", "A62", "C03", "C05", "A10", path="REAL")
def test_every_selected_frame_has_anchored_observation_and_witnesses(drill):
    ws, *_ = drill
    st = ws.store()
    man = st.get("SelectedSequenceManifest", "REAL:15")
    assert man["selected_count"] == 15 and all(s["observer"] == "VLM" for s in man["selected"])
    rows = st.conn.execute("SELECT film_sha256, frame_index, status FROM frame_vision WHERE pass_id='REAL-DRILL-L0'").fetchall()
    want = sum(s["actual_frame_count"] for s in man["selected"]) + (lambda x: x["frame_count"])(st.get("SpecialIntroSelection", "REAL"))
    assert len(rows) == want and {r[2] for r in rows} == {"SIMULATED_TRANSPORT_FIXTURE"}
    from vme.reference.frame_index import read_index
    for w in st.list("Witness")[:40]:
        idx = read_index(ws.frames_dir / w["film_sha256"] / "index.jsonl.gz")
        if w["evidence_kind"] == "FULL_FRAME":
            assert w["image_sha256"] == idx[w["frame_start"]]["frame_content_sha256"] and w["observer"] == "VLM"
    assert any(w["evidence_kind"] == "NATIVE_CROP" for w in st.list("Witness"))
    st.close()


@pytest.mark.req("C08", "ADD26-Q05", "B13", "ADD27-3", path="REAL")
def test_multiple_questions_close_multiple_gaps(drill):
    ws, *_ = drill
    st = ws.store()
    t = st.get("RealInvestigationTrace", "REAL-DRILL")
    closed = {s["gap_signature"] for s in t["steps"] if s["decision_changed"] and s["stage"] == "STYLE_CONDITIONS"}
    assert len(closed) >= 5 and {s["stage"] for s in t["steps"]} >= {"CAUSE_INFERENCE", "STYLE_CONDITIONS"}
    assert len({s["question"] for s in t["steps"]}) == len(t["steps"])   # never the same question text twice
    rev = st.get("CoverageReview", "REAL-DRILL")
    assert rev["review"]["state"] == "READY_FOR_ORIGINAL_IMAGE_TRIAL"
    st.close()


@pytest.mark.req("ADD27-6", "ADD27-11", "ADD27-13", "C29", path="REAL")
def test_source_to_skill_to_payload_trace(drill):
    ws, *_ = drill
    from vme.style.authoring import verify_structural_derivation
    from vme.skills.skill import load_skill
    st = ws.store()
    s4 = st.get("LoopTransition", "REAL-DRILL:S4")["outputs"]
    assert verify_structural_derivation(s4["skill_folder"])["ok"]
    sk = load_skill(s4["skill_folder"])
    assert sk["status"] == "FROZEN" and not sk["synthetic"] and sk["manifest"]["evidence_origin"] == "SIMULATED_VLM_TRANSPORT"
    jobs = st.list("CompiledImageJob")
    clause_by = {c["id"]: c for c in sk["clauses"]}
    for j in jobs:
        for seg in j["trace"]["segments"]:
            if seg["authority"] == "STYLE":
                c = clause_by[seg["clause_id"]]
                d = next(x for x in sk["decisions"] if x["decision_id"] == c["derivation"]["decision_id"])
                assert d["evidence_frame_ids"] and d["observed_relation_ids"]       # clause → decision → witnesses/relations
                assert seg["text"] in j["payload"]["positivePrompt"]
    st.close()


@pytest.mark.req("A59", "C20", "A57", path="REAL")
def test_states_are_conditioned_on_approved_canonical_bytes(drill):
    ws, *_ = drill
    st = ws.store()
    s5 = st.get("LoopTransition", "REAL-DRILL:S5")["outputs"]
    pack = read_json(st.get("LoopTransition", "REAL-DRILL:S7")["outputs"]["pack"])
    assert pack["method"] == "WHOLE_STATE_SWAP" and set(pack["states"]) == {"view:front", "grip:chamber_handle"}
    for v in pack["states"].values():
        assert s5["n_canonical_character"]["sha"] in v["reference_shas"]
    s8 = st.get("LoopTransition", "REAL-DRILL:S8")["outputs"]
    assert s8["motion"] == "INDEPENDENT_MOTION_PRESENT" and s8["state_swaps"] == 2
    st.close()


@pytest.mark.req("A36", "B17", "ADD25-P03", path="REAL")
def test_ablating_an_authored_decision_changes_or_blocks_payload(drill, tmp_path):
    ws, *_ = drill
    from vme.experiments.experiments import causal_mutation_test
    from vme.loop.human import provider_state
    st = ws.store()
    s4 = st.get("LoopTransition", "REAL-DRILL:S4")["outputs"]
    brief = st.get("OriginalBrief", "BRIEF-DRILL-ANCHOR")["brief"]
    st.close()
    folder = tmp_path / "skillcopy"
    shutil.copytree(s4["skill_folder"], folder)
    (folder / "FROZEN.json").unlink()
    caps = provider_state(ws)["runware"]

    def drop_first(f):
        d = read_json(f / "decisions.json")
        atomic_write_json(f / "decisions.json", d[1:])
    r = causal_mutation_test(folder, brief, caps, recipe_id="main", node_id="n_whole_scene", mutate=drop_first, label="ablate decision")
    assert r["request_changed_or_blocked"]


@pytest.mark.req("A04", "A28", "C17", "C18", "C38", path="REAL")
def test_production_providers_stop_only_at_authorization(drill, tmp_path, monkeypatch):
    """Same handlers with PRODUCTION providers: no unconditional block — the first external call is refused by the
    network/authorization barrier, before any client is constructed."""
    ws, _, _, root = drill
    from vme.loop.real import RealLoopRunner, RealProviders
    built = []
    prov = RealProviders(vision_client_factory=lambda: built.append(1), vision_transport_kind="NETWORK",
                         image_transport=lambda b, h: built.append(2), image_transport_kind="NETWORK")
    monkeypatch.delenv("VME_ALLOW_NETWORK", raising=False)
    st = ws.store()
    for c in list(st.list("CandidateSequence"))[:1]:
        pass
    st.close()
    new = RealLoopRunner(ws, run_id="REAL-PROD-CHECK", providers=prov)
    # force S0 to need a fresh rationale: new window config
    from vme.loop.real import RealLoopConfig
    new.cfg = RealLoopConfig(max_window_s=0.2, min_window_s=0.1, max_windows_per_film=4)
    out = new.run(until="S0")
    assert out["stopped_at"] == "S0" and out["reason"] == "NETWORK_DISABLED" and built == []


@pytest.mark.req("A19", "A64", "ADD26-R01", "ADD24-D4-3", "C35", path="REAL")
def test_crash_after_every_stage_commit_resumes(tmp_path):
    from vme.testing.drill import build_drill_workspace, drill_providers, drive, enable_network_flag
    enable_network_flag()
    d = build_drill_workspace(tmp_path)
    prov, client = drill_providers(tmp_path)
    res = drive(d["ws"], prov, run_id="REAL-CRASH", crash_at=[f"S{i}" for i in range(10)], max_rounds=60)
    os.environ.pop("VME_ALLOW_NETWORK", None)
    crashes = [x for x in res["log"] if "crash" in x]
    assert res["result"].get("completed_through") == "S9", res["log"][-3:]
    assert len(crashes) == 10 and client.duplicate_creates() == 0


@pytest.mark.req("A65", "B06", "ADD24-D4-1", "ADD24-D4-2", path="REAL")
def test_hard_kill_mid_packet_reconciles_batches(tmp_path):
    code = f"""
import sys, os, json; sys.path.insert(0, r'{ROOT}')
from pathlib import Path
from vme.testing.drill import build_drill_workspace, drill_providers, drive, enable_network_flag
from vme.state.workspace import Workspace
root = Path(r'{tmp_path}')
enable_network_flag()
if not (root / 'ws' / 'state' / 'SOURCE_LOCK.json').exists():
    build_drill_workspace(root)
ws = Workspace(root / 'ws').ensure()
prov, client = drill_providers(root)
out = drive(ws, prov, run_id='REAL-KILL', max_rounds=4)
print(json.dumps({{'out': out['result'].get('stopped_at') or out['result'].get('completed_through'), 'billed': client.billed_requests(), 'dups': client.duplicate_creates()}}))
"""
    env = {**os.environ, "VME_CRASH_AT": "after_submit_before_save", "VME_CRASH_HARD": "1"}
    r1 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=900)
    assert r1.returncode == 97, r1.stderr[-800:]
    env.pop("VME_CRASH_AT")
    r2 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=900)
    assert r2.returncode == 0, r2.stderr[-800:]
    o = json.loads(r2.stdout.strip().splitlines()[-1])
    assert o["dups"] == 0


@pytest.mark.req("B20", "A56", path="REAL")
def test_real_brief_rejects_style_smuggling_and_requires_human(tmp_path):
    from vme.state.workspace import Workspace
    from vme.loop.human import add_brief
    from vme.testing.drill import drill_brief
    ws = Workspace(tmp_path / "w").ensure()
    b = drill_brief()
    b["slots"]["subject"] = "explorer with thick outlines"
    with pytest.raises(Blocked):
        add_brief(ws, b, added_by="user")
    with pytest.raises(Blocked):
        add_brief(ws, drill_brief(), added_by="claude")


@pytest.mark.req("B23", "C17", path="REAL")
def test_runware_model_must_be_typed_by_user(tmp_path):
    from vme.state.workspace import Workspace
    from vme.loop.human import confirm_runware_model
    ws = Workspace(tmp_path / "w").ensure()
    with pytest.raises(Blocked):
        confirm_runware_model(ws, model_air_id="FLUX Klein 7B", confirmed_by="user", est_cost_per_image_usd=0.01)
    s = confirm_runware_model(ws, model_air_id="runware:400@4", confirmed_by="user", est_cost_per_image_usd=0.01)
    assert s["user_confirmed_model"] and not s["verified_by_probe"]


@pytest.mark.req("AUDIT-P0-5", path="REAL")
def test_source_roles_unconfirmed_quarantine_real_s0(tmp_path):
    from vme.state.workspace import Workspace
    from vme.loop.real import RealLoopRunner, RealProviders
    ws = Workspace(tmp_path / "w").ensure()
    atomic_write_json(ws.state_dir / "SOURCE_LOCK.json", {"sources": [{"sha256": c * 64, "file_name": c, "role": "BASE_FILM", "basis": "DEFAULT_NON_SIXTH",
                                                                         "width": 1280, "height": 720} for c in "abcde"]})
    out = RealLoopRunner(ws, run_id="REAL-Q", providers=RealProviders.production(ws)).run()
    assert out["stopped_at"] == "S0" and out["reason"] == "SOURCE_ROLES_UNCONFIRMED"
