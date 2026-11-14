"""Sole image gateway: consent, spend, idempotency, raster truth, model identity
(A04, A05, A19, A20, A22, A47, B23, B24, C17, C18, C34, C38, spec 17 §7 provider injections)."""
import os
import subprocess
import sys

import pytest

from conftest import ROOT, compile_job, offline_gateway
from vme.util import Blocked


@pytest.mark.req("B23", "C17")
def test_unverified_7b_model_name_refused():
    from vme.providers.capabilities import resolve_model
    from vme.providers.authorization import AuthorizationRegistry
    for name in ("FLUX Klein 7B", "flux-klein-7b", "auto", ""):
        with pytest.raises(Blocked) as e:
            resolve_model(name)
        assert e.value.code == "UNVERIFIED_MODEL_ID"
    with pytest.raises(Blocked):
        AuthorizationRegistry("x").issue(provider="runware", model_id="runware:klein-7B", task_categories=["image_generation"],
                                         spend_cap_usd=1, issued_by="user", confirm_phrase="I AUTHORIZE PAID CALLS WITHIN THIS CAP")
    assert resolve_model("runware:400@4")["verified_by_probe"] is False


@pytest.mark.req("A04", "A05", "B24", "C34", "C38", phase="PAID")
def test_real_adapter_refuses_without_network_authorization_cap(tmp_path, store, skill, brief, caps, monkeypatch):
    from vme.providers.gateway import StyleImageGateway
    from vme.providers.runware import RunwareAdapter
    from vme.providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
    sent = []
    snap = dict(caps, user_confirmed_model=True, verified_by_probe=True, cost_per_image_usd=0.01)
    reg = AuthorizationRegistry(tmp_path)
    g = StyleImageGateway(store, tmp_path / "a", RunwareAdapter(snap, lambda b, h: sent.append(b) or b"{}", kind="REAL"), reg)
    from vme.fixtures.synthetic import build_synthetic_skill
    real_like = tmp_path / "real_like"
    build_synthetic_skill(real_like)
    import json
    m = json.loads((real_like / "manifest.json").read_text())
    m["synthetic"] = False
    (real_like / "manifest.json").write_text(json.dumps(m))
    from vme.skills.skill import skill_hash
    from vme.compiler.compiler import StyleProgramCompiler
    job = StyleProgramCompiler().compile(brief, real_like, pinned_skill_hash=skill_hash(real_like), recipe_id="character_world",
                                         node_id="n1_scene", caps=snap)
    monkeypatch.delenv("VME_ALLOW_NETWORK", raising=False)
    with pytest.raises(Blocked) as e:
        g.submit(job)
    assert e.value.code == "NETWORK_DISABLED"
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    with pytest.raises(Blocked) as e:
        g.submit(job)
    assert e.value.code == "NO_PROVIDER_AUTHORIZATION"
    reg.issue(provider="runware", model_id="runware:400@4", task_categories=["image_generation"], spend_cap_usd=0.005,
                  issued_by="test-user", confirm_phrase=CONFIRM_PHRASE)
    with pytest.raises(Blocked) as e:
        g.submit(job)
    assert e.value.code == "SPEND_CAP_EXCEEDED"
    assert sent == []  # zero bytes ever reached the transport


@pytest.mark.req("C38", "B24", phase="PAID")
def test_source_frame_reference_requires_separate_upload_consent(tmp_path):
    from vme.providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
    reg = AuthorizationRegistry(tmp_path)
    reg.issue(provider="runware", model_id="runware:400@4", task_categories=["image_generation"], spend_cap_usd=5, issued_by="u",
              confirm_phrase=CONFIRM_PHRASE)
    os.environ["VME_ALLOW_NETWORK"] = "1"
    try:
        with pytest.raises(Blocked) as e:
            reg.check(provider="runware", model_id="runware:400@4", task="image_generation", estimated_cost_usd=0.01, source_shas=["a" * 64])
        assert e.value.code == "NO_SOURCE_UPLOAD_CONSENT"
        with pytest.raises(Blocked) as e2:
            reg.check(provider="runware", model_id="runware:400@4", task="image_generation", estimated_cost_usd=None)
        assert e2.value.code == "COST_UNKNOWN_STOP"
    finally:
        os.environ.pop("VME_ALLOW_NETWORK")


@pytest.mark.req("C18", "A20")
def test_offline_output_is_decoded_real_raster_with_honest_cost(tmp_path, store, skill, brief, caps):
    g, t = offline_gateway(store, tmp_path, caps)
    r = g.submit(compile_job(skill, brief, caps))
    o = r["outputs"][0]
    assert (o["width"], o["height"]) == (1536, 864) and o["pixel_mode"] == "RGB" and not o["has_nonopaque_alpha"]
    assert r["label"] == "OFFLINE_FIXTURE_NOT_LEARNED_ART" and r["cost_status"] in ("REPORTED", "UNKNOWN")
    body = t.sent_bodies()[0]["task"]
    assert body["positivePrompt"] == compile_job(skill, brief, caps).logical_payload["positivePrompt"]
    assert body["inputs"]["referenceImages_count"] == 2  # actual bytes were sent, not just IDs


@pytest.mark.parametrize("mode,code", [("invalid_bytes", "INVALID_IMAGE_BYTES"), ("http_error", "PROVIDER_EXECUTION"),
                                       ("url_only", "PROVIDER_URL_EXPIRED_OR_UNFETCHED"), ("wrong_size", "OUTPUT_DIMENSION_MISMATCH"),
                                       ("no_image", "PROVIDER_NO_IMAGE")])
def test_provider_failures_never_reported_as_art(tmp_path, store, skill, brief, caps, mode, code):
    g, _ = offline_gateway(store, tmp_path, caps, mode=mode)
    with pytest.raises(Blocked) as e:
        g.submit(compile_job(skill, brief, caps))
    assert e.value.code == code
    assert store.list("GeneratedRaster") == []


test_provider_failures_never_reported_as_art = pytest.mark.req("A22", "C18")(test_provider_failures_never_reported_as_art)


@pytest.mark.req("A19", "A47", "B06", "ADD24-D4-2")
def test_gateway_kill_after_send_reconciles_without_rebilling(tmp_path):
    code = f"""
import sys; sys.path.insert(0, r'{ROOT}'); sys.path.insert(0, r'{ROOT / "tests"}')
from pathlib import Path
from vme.state.store import Store
from vme.fixtures.synthetic import build_synthetic_skill, synthetic_brief, fixture_caps
from conftest import compile_job, offline_gateway
tp = Path(r'{tmp_path}')
f = tp / 'sk'
h = build_synthetic_skill(f) if not (f / 'manifest.json').exists() else __import__('vme.skills.skill', fromlist=['x']).skill_hash(f)
st = Store(tp / 's.sqlite'); caps = fixture_caps()
g, t = offline_gateway(st, tp, caps)
r = g.submit(compile_job((f, h), synthetic_brief(), caps))
print('BILLED', t.billed(), r['outputs'][0]['sha256'])
"""
    env = {**os.environ, "VME_CRASH_AT": "gateway_after_send_before_save", "VME_CRASH_HARD": "1"}
    r1 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=300)
    assert r1.returncode == 97, r1.stderr[-600:]
    env.pop("VME_CRASH_AT")
    r2 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=300)
    assert r2.returncode == 0, r2.stderr[-600:]
    assert "BILLED 1 " in r2.stdout


@pytest.mark.req("A65", "ADD26-R02")
def test_gateway_unreconcilable_pending_is_unknown_billing(tmp_path, store, skill, brief, caps, monkeypatch):
    from vme.vision.runner import SimulatedCrash
    g, t = offline_gateway(store, tmp_path, caps, queryable=False)
    job = compile_job(skill, brief, caps)
    monkeypatch.setenv("VME_CRASH_AT", "gateway_after_send_before_save")
    with pytest.raises(SimulatedCrash):
        g.submit(job)
    monkeypatch.delenv("VME_CRASH_AT")
    with pytest.raises(Blocked) as e:
        g.submit(job)
    assert e.value.code == "UNKNOWN_BILLING" and t.billed() == 1


@pytest.mark.req("C34")
def test_synthetic_skill_never_reaches_real_provider(tmp_path, store, skill, brief, caps, monkeypatch):
    from vme.providers.gateway import StyleImageGateway
    from vme.providers.runware import RunwareAdapter
    from vme.providers.authorization import AuthorizationRegistry
    g = StyleImageGateway(store, tmp_path / "a", RunwareAdapter(caps, lambda b, h: b"{}", kind="REAL"), AuthorizationRegistry(tmp_path))
    with pytest.raises(Blocked) as e:
        g.submit(compile_job(skill, brief, caps))
    assert e.value.code == "SYNTHETIC_SKILL_TO_REAL_PROVIDER"


@pytest.mark.req("C34")
def test_api_key_never_written(tmp_path, store, skill, brief, caps, monkeypatch):
    monkeypatch.setenv("RUNWARE_API_KEY", "rk_TESTSECRET_1234567890abcdef")
    g, t = offline_gateway(store, tmp_path, caps)
    g.submit(compile_job(skill, brief, caps))
    for p in tmp_path.rglob("*"):
        if p.is_file():
            assert b"rk_TESTSECRET" not in p.read_bytes(), p
