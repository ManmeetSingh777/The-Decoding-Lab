"""S0–S9 loop with real handlers, crash at stage boundaries, cross-environment handoff
(ADD26 §5, ADD26-R01, ADD24-D1..D4, ADD25-R01, ADD25-A01, B08, B35, A47, C35, C36)."""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from conftest import ROOT
from vme.util import Blocked, read_json


def _loop_code(ws_root, run_id, until, sim=True):
    return f"""
import sys, json; sys.path.insert(0, r'{ROOT}')
from pathlib import Path
from vme.state.workspace import Workspace
from vme.loop.stages import LoopRunner
ws = Workspace(Path(r'{ws_root}')).ensure()
print(json.dumps(LoopRunner(ws, run_id='{run_id}', simulate_human={sim}).run(until='{until}')))
"""


@pytest.fixture(scope="module")
def e2e(tmp_path_factory):
    root = tmp_path_factory.mktemp("e2e") / "ws"
    r = subprocess.run([sys.executable, "-c", _loop_code(root, "RUN-E2E", "S9")], capture_output=True, text=True, timeout=900,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-1500:]
    return root, json.loads(r.stdout.strip().splitlines()[-1])


@pytest.mark.req("ADD26-A01", "ADD26-S0S9", "ADD24-E2", "C13")
def test_e2e_all_stages_real_consumers(e2e):
    root, out = e2e
    from vme.render.renderer import REMOTION_DIR
    if not (REMOTION_DIR / "node_modules" / "remotion").exists():
        # truthful stop when the render engine is absent (e.g. fresh ZIP extraction before `npm ci`)
        assert out.get("stopped_at") == "S8" and out.get("reason") == "RENDER_ENGINE_NOT_INSTALLED", out
        pytest.skip("Remotion not installed: loop stopped truthfully at S8 (run `npm ci` in render/remotion)")
    assert out.get("completed_through") == "S9", out
    from vme.state.workspace import Workspace
    st = Workspace(root).ensure().store()
    ts = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == "RUN-E2E"}
    assert set(ts) == {f"S{i}" for i in range(10)} and all(t["consumer"].startswith("vme.") for t in ts.values())
    assert ts["S1"]["outputs"]["coverage"]["complete"] and "MOCK" in ts["S1"]["outputs"]["coverage_label"]
    assert ts["S2"]["outputs"]["stages"] == ["SOURCE_OBSERVATION", "CAUSE_INFERENCE", "STYLE_CONDITIONS"]
    assert ts["S4"]["outputs"]["coverage_state"] == "READY_FOR_ORIGINAL_IMAGE_TRIAL"
    assert ts["S8"]["outputs"]["motion"] == "INDEPENDENT_MOTION_PRESENT" and ts["S8"]["outputs"]["label"] == "ANIMATION_FIXTURE_ONLY"
    assert ts["S9"]["outputs"]["question_changed"] and ts["S9"]["outputs"]["transfer"] == "TRANSFER_PENDING_AWAITING_REVIEW"
    st.close()


@pytest.mark.req("ADD26-Q05", "ADD24-E2")
def test_s3_decision_is_what_the_skill_compiles(e2e):
    """answer → ConditionalVisualDecision (S3) → skill decisions.json (S4) → compiled payload (S5)."""
    root, _ = e2e
    from vme.state.workspace import Workspace
    st = Workspace(root).ensure().store()
    d3 = next(d for d in st.list("ConditionalVisualDecision") if d["decision_id"] == "D-SYN-FACE-VIEW")
    s4 = st.get("LoopTransition", "RUN-E2E:S4")["outputs"]
    dj = {d["decision_id"]: d for d in read_json(Path(s4["skill_folder"]) / "decisions.json")}
    assert dj["D-SYN-FACE-VIEW"]["version"] == d3["version"] == 2 and dj["D-SYN-FACE-VIEW"]["evidence_scope"] == d3["evidence_scope"]
    job = next(j for j in st.list("CompiledImageJob") if j["trace"]["node_id"] == "n2_canonical")
    assert "D-SYN-FACE-VIEW" in job["trace"]["selected_decisions"]
    assert any(c.startswith("K-SYN-FACE-01") for c in job["trace"]["clause_ids"])
    st.close()


@pytest.mark.req("ADD26-I02")
def test_loop_without_human_stops_at_artwork_review(tmp_path):
    r = subprocess.run([sys.executable, "-c", _loop_code(tmp_path / "w", "RUN-NOHUMAN", "S9", sim=False)], capture_output=True, text=True,
                       timeout=600)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["stopped_at"] == "S6" and out["reason"] == "AWAITING_ARTWORK_REVIEW"


@pytest.mark.parametrize("stage", ["S1", "S2", "S3", "S4", "S5"])
def test_hard_kill_after_stage_then_resume_completes_without_redoing(tmp_path, stage):
    w = tmp_path / "w"
    env = {**os.environ, "VME_CRASH_AT": f"loop_after_{stage}", "VME_CRASH_HARD": "1"}
    r1 = subprocess.run([sys.executable, "-c", _loop_code(w, "RUN-K", "S5")], env=env, capture_output=True, text=True, timeout=600)
    assert r1.returncode == 97, r1.stderr[-800:]
    env.pop("VME_CRASH_AT")
    r2 = subprocess.run([sys.executable, "-c", _loop_code(w, "RUN-K", "S5")], env=env, capture_output=True, text=True, timeout=600)
    assert r2.returncode == 0, r2.stderr[-800:]
    out = json.loads(r2.stdout.strip().splitlines()[-1])
    resumed = [t["stage"] for t in out["trace"] if t.get("resumed_from_store")]
    assert stage in resumed and out["completed_through"] == "S5"


test_hard_kill_after_stage_then_resume_completes_without_redoing = pytest.mark.req(
    "ADD26-R01", "ADD24-D4-3", "ADD24-D4-4", "C35")(test_hard_kill_after_stage_then_resume_completes_without_redoing)


@pytest.mark.req("ADD24-D3", "ADD24-D4-6", "ADD25-R01", "B08", "ADD24-D1", "ADD24-D2", "ADD24-E3")
def test_export_import_handoff_new_workspace_reproduces_compile_and_next_op(e2e, tmp_path):
    root, _ = e2e
    from vme.state.workspace import Workspace
    from vme.state.handoff import export_handoff, import_handoff, exact_next_operation
    ws = Workspace(root).ensure()
    ex = export_handoff(ws, tmp_path / "VME_PORTABLE_HANDOFF.zip")
    with zipfile.ZipFile(ex["zip"]) as z:
        names = z.namelist()
    assert "store/vme.sqlite" in names and "HANDOFF_MANIFEST.json" in names
    assert not any(n.endswith(".mp4") for n in names)
    new = tmp_path / "other_env"
    rep = import_handoff(ex["zip"], new)
    assert rep["sqlite_integrity"] == "ok" and not rep["hash_mismatches"]
    ws2 = Workspace(new).ensure()
    assert exact_next_operation(ws2) == exact_next_operation(ws)
    # deterministic recompilation of a frozen job from imported state (different folder path → rebind skill folder)
    st = ws2.store()
    j = next(x for x in st.list("CompiledImageJob") if x["trace"]["node_id"] == "n1_scene")
    s4 = st.get("LoopTransition", "RUN-E2E:S4")["outputs"]
    st.close()
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.fixtures.loop_fixtures import synthetic_brief, fixture_caps
    moved = new / "skills" / Path(s4["skill_folder"]).name
    re = StyleProgramCompiler().compile(synthetic_brief(), moved, pinned_skill_hash=s4["skill_hash"], recipe_id="character_world",
                                        node_id="n1_scene", caps=fixture_caps())
    assert re.logical_payload["positivePrompt"] == j["payload"]["positivePrompt"]


@pytest.mark.req("ADD24-D4-5", "ADD25-R02")
def test_import_refuses_corrupt_and_reports_missing_sources(e2e, tmp_path):
    root, _ = e2e
    from vme.state.workspace import Workspace
    from vme.state.handoff import export_handoff, import_handoff
    ex = export_handoff(Workspace(root).ensure(), tmp_path / "h.zip")
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(ex["zip"]) as zin, zipfile.ZipFile(bad, "w") as zout:
        for n in zin.namelist():
            data = zin.read(n)
            if n.startswith("artifacts/images/") and n.endswith(".png"):
                data = data + b"tamper"
            zout.writestr(n, data)
    with pytest.raises(Blocked) as e:
        import_handoff(bad, tmp_path / "x")
    assert e.value.code == "HANDOFF_CORRUPT"
    # sources required but not supplied → INCOMPLETE, never COMPLETE
    lock_ws = tmp_path / "wl"
    from vme.state.workspace import Workspace as W
    w = W(lock_ws).ensure()
    from vme.util import atomic_write_json
    atomic_write_json(w.state_dir / "SOURCE_LOCK.json", {"sources": [{"file_name": "f.mp4", "sha256": "a" * 64, "role": "BASE_FILM"}]})
    ex2 = export_handoff(w, tmp_path / "h2.zip")
    rep = import_handoff(ex2["zip"], tmp_path / "y", sources_folder=tmp_path)
    assert rep["status"] == "INCOMPLETE" and rep["sources_unbound"]


@pytest.mark.req("ADD24-D4-7", "A47")
def test_review_rejection_survives_handoff(tmp_path):
    from vme.state.workspace import Workspace
    from vme.state.handoff import export_handoff, import_handoff
    from vme.review.approvals import GateKeeper, FIXTURE_SIGNER
    from PIL import Image
    w = Workspace(tmp_path / "w").ensure()
    st = w.store()
    gk = GateKeeper(st)
    gk.transition("R", "ART_GENERATING", synthetic=True)
    gk.transition("R", "AWAITING_ARTWORK_REVIEW")
    img = w.artifacts_dir / "x.png"
    Image.new("RGB", (8, 8)).save(img)
    gk.submit_art_verdict("R", image_paths=[str(img)], brief_id="b", skill_versions=[], verdict="REJECTED", defects=["face"], signed_by=FIXTURE_SIGNER)
    st.close()
    ex = export_handoff(w, tmp_path / "h.zip")
    import_handoff(ex["zip"], tmp_path / "n")
    st2 = Workspace(tmp_path / "n").ensure().store()
    assert GateKeeper(st2).state("R")["state"] == "ARTWORK_REJECTED"
    with pytest.raises(Blocked):
        GateKeeper(st2).authorize_render("R", scene_asset_paths=[])
    st2.close()


@pytest.mark.req("ADD25-A01", "B35")
def test_handoff_excludes_mp4_and_secrets(tmp_path):
    from vme.state.workspace import Workspace
    from vme.state.handoff import export_handoff
    w = Workspace(tmp_path / "w").ensure()
    (w.artifacts_dir / "film.mp4").write_bytes(b"\x00" * 10)
    fake = "rk_" + "live_" + "abcdefghijklmnop"          # built at runtime: no key-shaped literal in source
    (w.state_dir / "notes.txt").write_text("RUNWARE_API_KEY" + "=" + fake, encoding="utf-8")
    ex = export_handoff(w, tmp_path / "h.zip")
    with zipfile.ZipFile(ex["zip"]) as z:
        names = z.namelist()
        blob = b"".join(z.read(n) for n in names)
    assert not any(n.endswith(".mp4") for n in names) and fake.encode() not in blob
    reasons = {o["path"]: o["reason"] for o in ex["omitted"]}
    assert reasons["state/notes.txt"] == "SECRET_PATTERN_DETECTED"


@pytest.mark.req("ADD26-S0S9")
def test_real_mode_loop_stops_truthfully_at_selection(tmp_path):
    """REAL mode on a workspace with real-like sources but no visual rationales → STOPPED at S0 (no fabricated selection)."""
    from vme.state.workspace import Workspace
    from vme.util import atomic_write_json
    from vme.loop.stages import LoopRunner
    w = Workspace(tmp_path / "w").ensure()
    atomic_write_json(w.state_dir / "SOURCE_LOCK.json", {"sources": [{"sha256": c * 64, "role": "BASE_FILM"} for c in "abcde"]})
    out = LoopRunner(w, run_id="REAL1", mode="REAL").run()
    assert out["stopped_at"] == "S0" and "NO_VISUAL_RATIONALE" in out["reason"]
    with pytest.raises(Blocked):
        LoopRunner(w, run_id="REAL2", mode="REAL", simulate_human=True)


@pytest.mark.req("ADD24-D4-4", "A47", "A19")
def test_kill_during_character_pose_generation_preserves_canonical_and_reconciles(tmp_path):
    w = tmp_path / "w"
    env = {**os.environ}
    r0 = subprocess.run([sys.executable, "-c", _loop_code(w, "RUN-P", "S6")], env=env, capture_output=True, text=True, timeout=600)
    assert r0.returncode == 0, r0.stderr[-600:]
    from vme.state.workspace import Workspace
    st = Workspace(w).ensure().store()
    canon_sha = st.get("LoopTransition", "RUN-P:S5")["outputs"]["n2_canonical"]["sha"]
    st.close()
    env.update(VME_CRASH_AT="gateway_after_send_before_save", VME_CRASH_HARD="1")
    r1 = subprocess.run([sys.executable, "-c", _loop_code(w, "RUN-P", "S7")], env=env, capture_output=True, text=True, timeout=600)
    assert r1.returncode == 97, r1.stderr[-600:]
    env.pop("VME_CRASH_AT")
    r2 = subprocess.run([sys.executable, "-c", _loop_code(w, "RUN-P", "S7")], env=env, capture_output=True, text=True, timeout=600)
    assert r2.returncode == 0, r2.stderr[-800:]
    st = Workspace(w).ensure().store()
    s7 = st.get("LoopTransition", "RUN-P:S7")
    assert s7["status"] == "COMPLETED" and s7["outputs"]["states"]["n3_view"]["identity_ref"] == canon_sha
    bills = list((w / "runs" / "RUN-P" / "offline_runware").glob("bill_*.json"))
    reqs = list((w / "runs" / "RUN-P" / "offline_runware").glob("req_*.json"))
    assert len(bills) == len(reqs) == 4  # n1,n2 (S5) + n3,n4 (S7): each billed exactly once despite the kill
    st.close()
