"""Strict-fake provider contracts, crash ambiguity and spend reservations (repair R01–R07, ST28-24).

All fakes are SIMULATED (no socket is opened). They are strict: they reject what the documented APIs reject,
bill every accepted create/send, and never assume server-side idempotency.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import uuid
from pathlib import Path

import pytest

from vme.util import Blocked

ROOT = Path(__file__).resolve().parents[1]
HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"


# ---------------------------------------------------------------- Anthropic custom_id (R01)
@pytest.mark.req("R01", "ST28-24")
def test_all_vision_custom_ids_are_short_safe_and_stable():
    from vme.vision.runner import plan_packets
    from vme.providers.ids import packet_custom_id, custom_id_for, KIND_PREFIX, CUSTOM_ID_RE
    idx = [{"pts": i, "pts_time": i / 30, "frame_content_sha256": f"{i:064x}"} for i in range(64)]
    plans = plan_packets(idx, 0, 63, film_sha="a" * 64, pass_id="REAL-RUN-WITH-A-LONG-NAME-L0", cluster_id="win_" + "b" * 40,
                         model_version="claude-opus-5-5", max_images=20)
    ids = [packet_custom_id(p) for p in plans]
    assert all(CUSTOM_ID_RE.fullmatch(i) and len(i) <= 64 for i in ids)
    assert len(set(ids)) == len(ids)
    assert ids == [packet_custom_id(p) for p in plans]          # restart-stable
    for k in KIND_PREFIX:
        assert len(custom_id_for(k, {"x": "y" * 500})) <= 64
    old = f"{plans[0].idempotency_key}-{uuid.uuid5(uuid.NAMESPACE_URL, plans[0].packet_id)}"
    assert len(old) == 74 and not CUSTOM_ID_RE.fullmatch(old)  # the pre-repair formula is invalid


@pytest.mark.req("R01", "R03")
def test_strict_fake_batches_reject_invalid_custom_id_and_params(tmp_path):
    from vme.testing.simulated_anthropic import SimulatedAnthropicClient, SimulatedAPIStatusError
    c = SimulatedAnthropicClient(tmp_path)
    ok = {"model": "m", "max_tokens": 10, "messages": [{"role": "user", "content": [{"type": "text", "text": "{}"}]}], "system": "x"}
    with pytest.raises(SimulatedAPIStatusError) as e:
        c.messages.batches.create(requests=[{"custom_id": "x" * 65, "params": ok}])
    assert e.value.status_code == 400
    with pytest.raises(SimulatedAPIStatusError):
        c.messages.batches.create(requests=[{"custom_id": "bad id!", "params": ok}])
    with pytest.raises(SimulatedAPIStatusError):
        c.messages.batches.create(requests=[{"custom_id": "a", "params": {**ok, "bogus": 1}}])
    assert c.billed_requests() == 0


def _vision(tmp_path, mode="ok", cap=50.0):
    from vme.vision.claude_adapter import ClaudeBatchVisionAdapter, default_caps
    from vme.providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
    from vme.testing.simulated_anthropic import SimulatedAnthropicClient
    reg = AuthorizationRegistry(tmp_path / "authz")
    reg.issue(provider="anthropic-claude", model_id="claude-opus-5-5", task_categories=["source_vision"], spend_cap_usd=cap,
              issued_by=HUMAN, confirm_phrase=CONFIRM_PHRASE, source_upload_consent=True, allowed_source_shas=["f" * 64])
    client = SimulatedAnthropicClient(tmp_path / "sim", mode=mode)
    ad = ClaudeBatchVisionAdapter(default_caps(), reg, tmp_path / "vstate", client_factory=lambda: client, transport_kind="SIMULATED")
    return ad, client, reg


def _img():
    import io
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (64, 36), (10, 20, 30)).save(b, format="PNG")
    return b.getvalue()


def _ask(ad, tid="vme_nd_" + "0" * 40):
    payload = json.dumps({"reason": "r", "frame": 1})
    return ad.request_json(tid, "native_detail", "SYS", payload, [("FULL f:1", _img(), 64, 36), ("NATIVE_CROP f:1", _img(), 64, 36)],
                           source_shas=["f" * 64])


@pytest.mark.req("R01")
def test_adapter_refuses_invalid_custom_id_before_any_create(tmp_path, monkeypatch):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    ad, client, _ = _vision(tmp_path)
    with pytest.raises(Blocked) as e:
        _ask(ad, "idem_" + "a" * 32 + "-" + str(uuid.uuid4()))
    assert e.value.code == "INVALID_CUSTOM_ID" and client.billed_requests() == 0


# ---------------------------------------------------------------- accepted-before-batch-id ambiguity (R02)
@pytest.mark.req("R02", "R07", "ST28-24")
def test_accept_then_raise_is_submission_uncertain_never_resubmitted(tmp_path, monkeypatch):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    ad, client, reg = _vision(tmp_path, mode="accept_then_raise")
    with pytest.raises(Blocked) as e:
        _ask(ad)
    assert e.value.code == "SUBMISSION_UNCERTAIN"
    client.messages.batches.mode = "ok"        # even if the network recovers, the journal forbids a blind resend
    for _ in range(3):
        with pytest.raises(Blocked) as e2:
            _ask(ad)
        assert e2.value.code == "SUBMISSION_UNCERTAIN"
    assert client.billed_requests() == 1 and client.duplicate_creates() == 0
    rows = reg.ledger.rows()
    assert [r["status"] for r in rows] == ["LIABILITY_UNKNOWN"]       # uncertain charge stays counted against the cap
    bid = sorted(p.stem for p in (tmp_path / "sim").glob("msgbatch_*.json"))[0]
    with pytest.raises(Blocked):
        ad.reconcile_uncertain("vme_nd_" + "0" * 40, by="claude", batch_id=bid)
    ad.reconcile_uncertain("vme_nd_" + "0" * 40, by=HUMAN, batch_id=bid)
    r = _ask(ad)
    assert r["receipt"]["batch_id"] == bid and client.billed_requests() == 1
    assert [x["status"] for x in reg.ledger.rows()] == ["SETTLED"]


@pytest.mark.req("R02", "R24", "ST28-17")
def test_hard_kill_after_create_before_batch_id_saved_is_uncertain(tmp_path):
    code = f"""
import sys, os, json; sys.path.insert(0, r'{ROOT}'); sys.path.insert(0, r'{ROOT / "tests"}')
from pathlib import Path
from test_provider_contracts import _vision, _ask
from vme.util import Blocked
tp = Path(r'{tmp_path}')
ad, client, reg = _vision(tp)
try:
    _ask(ad); print('RESULT_OK')
except Blocked as b:
    print('BLOCKED', b.code)
print('BILLED', client.billed_requests())
"""
    env = {**os.environ, "VME_ALLOW_NETWORK": "1", "VME_CRASH_AT": "vision_after_create_before_save", "VME_CRASH_HARD": "1"}
    r1 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=300)
    assert r1.returncode == 97, r1.stderr[-800:]
    env.pop("VME_CRASH_AT")
    r2 = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=300)
    assert r2.returncode == 0, r2.stderr[-800:]
    assert "BLOCKED SUBMISSION_UNCERTAIN" in r2.stdout and "BILLED 1" in r2.stdout
    (tmp_path / "HARD_KILL_VISION_TRACE.json").write_text(json.dumps({"kill": r1.returncode, "restart_stdout": r2.stdout}), encoding="utf-8")


@pytest.mark.req("R02")
def test_crash_after_intent_before_create_is_uncertain_not_resent(tmp_path, monkeypatch):
    from vme.vision.runner import SimulatedCrash
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    ad, client, _ = _vision(tmp_path)
    monkeypatch.setenv("VME_CRASH_AT", "vision_after_intent_before_create")
    with pytest.raises(SimulatedCrash):
        _ask(ad)
    monkeypatch.delenv("VME_CRASH_AT")
    with pytest.raises(Blocked) as e:
        _ask(ad)
    assert e.value.code == "SUBMISSION_UNCERTAIN" and client.billed_requests() == 0
    ad.reconcile_uncertain("vme_nd_" + "0" * 40, by=HUMAN, not_submitted_evidence="console shows no batch")
    assert _ask(ad)["receipt"]["custom_id"] == "vme_nd_" + "0" * 40 and client.billed_requests() == 1


@pytest.mark.req("R02", "ST28-01")
@pytest.mark.parametrize("mode,code", [("truncated", "PROVIDER_OUTPUT_TRUNCATED"), ("non_json", "PROVIDER_NON_JSON"),
                                       ("errored", "PROVIDER_EXECUTION"), ("expired", "PROVIDER_EXECUTION")])
def test_bad_batch_results_are_named_and_raw_is_kept(tmp_path, monkeypatch, mode, code):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    ad, client, reg = _vision(tmp_path, mode=mode)
    with pytest.raises(Blocked) as e:
        _ask(ad)
    assert e.value.code == code
    if mode in ("truncated", "non_json"):
        assert list((tmp_path / "vstate").glob("raw_*.json"))           # raw stored before parse
        assert reg.ledger.rows()[0]["status"] in ("SETTLED", "SETTLED_COST_UNKNOWN")
    else:
        assert reg.ledger.rows()[0]["status"] == "RELEASED"


# ---------------------------------------------------------------- Runware (R04–R07)
def _real_gateway(tmp_path, store, *, mode="ok", cap=1.0, est=0.25, queryable=True, cost=0.25, issue=True, **kw):
    from vme.providers.gateway import StyleImageGateway, OfflineRecordingTransport
    from vme.providers.runware import RunwareAdapter
    from vme.providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
    from vme.fixtures.synthetic import fixture_caps
    snap = fixture_caps()
    snap.update(user_confirmed_model=True, cost_per_image_usd=est)
    reg = AuthorizationRegistry(tmp_path / "authz")
    if issue and not reg.find("runware", "runware:400@4", "capability_probe"):
        reg.issue(provider="runware", model_id="runware:400@4", task_categories=["capability_probe", "image_generation"], spend_cap_usd=cap,
                  issued_by=HUMAN, confirm_phrase=CONFIRM_PHRASE)
    t = OfflineRecordingTransport(tmp_path / f"rw_{mode}", mode=mode, queryable=queryable, cost=cost, **kw)
    ad = RunwareAdapter(snap, t, kind="REAL", transport_kind="SIMULATED", fetch_url=t.fetcher())
    return StyleImageGateway(store, tmp_path / "art", ad, reg), t, reg, snap


def _probe_job(snap, n=0):
    from vme.compiler.compiler import StyleProgramCompiler
    from vme.fixtures.synthetic import synthetic_brief
    b = synthetic_brief()
    b["slots"] = dict(b["slots"], subject=b["slots"]["subject"] + f" variant {n}")
    return StyleProgramCompiler().compile_baseline(b, caps=snap, output_contract={"width": 512, "height": 512, "format": "PNG", "asset_kind": "PROBE"})


@pytest.mark.req("R04", "R05", "ST28-24")
def test_runware_body_is_uuid4_with_documented_fields(tmp_path, store, monkeypatch):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store)
    r = g.submit(_probe_job(snap), task_category="capability_probe", probe=True)
    body = t.sent_bodies()[0]["task"]
    assert uuid.UUID(body["taskUUID"]).version == 4 and r["task_uuid_version"] == 4
    assert body["model"] == "runware:400@4" and body["outputType"] == "base64Data" and body["outputFormat"] == "PNG"
    assert body["numberResults"] == 1 and body["includeCost"] is True
    assert t.billed() == 1 and t.duplicate_bills() == 0
    assert [x["status"] for x in reg.ledger.rows()] == ["SETTLED"]
    r2 = g.submit(_probe_job(snap), task_category="capability_probe", probe=True)       # completed job: no request
    assert r2 == r and t.billed() == 1


@pytest.mark.req("R04")
def test_strict_runware_fake_rejects_uuid5_and_missing_include_cost(tmp_path):
    from vme.providers.gateway import OfflineRecordingTransport
    t = OfflineRecordingTransport(tmp_path)
    task = {"taskType": "imageInference", "taskUUID": str(uuid.uuid5(uuid.NAMESPACE_URL, "x")), "model": "runware:400@4",
            "positivePrompt": "p", "width": 512, "height": 512, "numberResults": 1, "outputType": "base64Data", "outputFormat": "PNG"}
    with pytest.raises(Blocked) as e:
        t(json.dumps([task]).encode(), {})
    assert e.value.code == "PROVIDER_REJECTED" and "version 5" in str(e.value) and "includeCost" in str(e.value)
    assert t.billed() == 0
    from vme.providers.ids import validate_uuid4
    with pytest.raises(Blocked):
        validate_uuid4(task["taskUUID"])


@pytest.mark.req("R04", "R06", "ST28-17")
def test_uuid4_persisted_before_network_and_reused_after_crash(tmp_path, store, monkeypatch):
    from vme.vision.runner import SimulatedCrash
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store)
    job = _probe_job(snap)
    monkeypatch.setenv("VME_CRASH_AT", "gateway_after_intent")
    with pytest.raises(SimulatedCrash):
        g.submit(job, task_category="capability_probe", probe=True)
    row = store.conn.execute("SELECT state, task_uuid, payload_sha FROM jobs").fetchone()
    assert row[0] == "INTENT_PERSISTED" and uuid.UUID(row[1]).version == 4 and t.billed() == 0
    monkeypatch.delenv("VME_CRASH_AT")
    r = g.submit(job, task_category="capability_probe", probe=True)
    assert r["task_uuid"] == row[1] and t.billed() == 1


@pytest.mark.req("R06", "R07")
def test_accept_then_drop_reconciles_by_get_response_without_resend(tmp_path, store, monkeypatch):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store, mode="accept_then_drop")
    r = g.submit(_probe_job(snap), task_category="capability_probe", probe=True)
    assert r["outputs"] and t.billed() == 1 and t.duplicate_bills() == 0
    assert [x["status"] for x in reg.ledger.rows()] == ["SETTLED"]


@pytest.mark.req("R06", "R07", "ST28-24")
def test_possible_acceptance_not_found_is_unknown_billing_then_human_reconcile(tmp_path, store, monkeypatch):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store, mode="drop_before_accept")
    job = _probe_job(snap)
    with pytest.raises(Blocked) as e:
        g.submit(job, task_category="capability_probe", probe=True)
    assert e.value.code == "UNKNOWN_BILLING"
    assert [x["status"] for x in reg.ledger.rows()] == ["LIABILITY_UNKNOWN"]
    with pytest.raises(Blocked):
        g.submit(job, task_category="capability_probe", probe=True)          # never blind-resent
    first_uuid = store.conn.execute("SELECT task_uuid FROM jobs").fetchone()[0]
    g.reconcile_unknown(job.logical_sha256, resolution="CONFIRMED_NOT_ACCEPTED", by=HUMAN, evidence="dashboard shows no task")
    t.mode = "ok"
    r = g.submit(job, task_category="capability_probe", probe=True)
    assert r["task_uuid"] != first_uuid and uuid.UUID(r["task_uuid"]).version == 4 and t.billed() == 1


@pytest.mark.req("R06")
def test_processing_status_is_pending_not_resent(tmp_path, store, monkeypatch):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store, mode="processing", processing_polls=1)
    job = _probe_job(snap)
    monkeypatch.setenv("VME_CRASH_AT", "gateway_after_send_before_save")
    from vme.vision.runner import SimulatedCrash
    with pytest.raises(SimulatedCrash):
        g.submit(job, task_category="capability_probe", probe=True)
    monkeypatch.delenv("VME_CRASH_AT")
    with pytest.raises(Blocked) as e:
        g.submit(job, task_category="capability_probe", probe=True)
    assert e.value.code == "PROVIDER_PENDING"
    r = g.submit(job, task_category="capability_probe", probe=True)
    assert r["outputs"] and t.billed() == 1 and t.duplicate_bills() == 0


@pytest.mark.req("R05")
@pytest.mark.parametrize("mode,delivery", [("url_only", "URL"), ("data_uri", "dataURI")])
def test_url_and_data_uri_results_are_decoded_and_verified(tmp_path, store, monkeypatch, mode, delivery):
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store, mode=mode)
    r = g.submit(_probe_job(snap), task_category="capability_probe", probe=True)
    assert r["outputs"][0]["delivery"] == delivery and r["outputs"][0]["width"] == 512


@pytest.mark.req("R05")
def test_url_fetch_refuses_unapproved_host_and_plain_http():
    from vme.providers.runware import https_image_fetcher
    f = https_image_fetcher(["im.runware.ai"])
    for u in ("http://im.runware.ai/x.png", "https://evil.example/x.png"):
        with pytest.raises(Blocked) as e:
            f(u)
        assert e.value.code == "PROVIDER_URL_HOST_NOT_ALLOWED"


@pytest.mark.req("R07", "ST28-24")
def test_concurrent_reservations_cannot_overrun_cap(tmp_path):
    from vme.providers.ledger import SpendLedger
    led = SpendLedger(tmp_path / "L.sqlite")
    ok, refused = [], []

    def go(i):
        try:
            ok.append(led.reserve(auth_id="A", provider="runware", cap_usd=1.0, logical_job_id=f"job{i}", estimated_max_cost=0.25))
        except Blocked as b:
            refused.append(b.code)
    ts = [threading.Thread(target=go, args=(i,)) for i in range(12)]
    [x.start() for x in ts]
    [x.join() for x in ts]
    assert len(ok) == 4 and refused == ["SPEND_CAP_EXCEEDED"] * 8
    assert led.exposure("A") == pytest.approx(1.0)
    rid = ok[0]["reservation_id"]
    led.settle(rid, actual_cost=0.1, receipt={"r": 1})
    led.settle(rid, actual_cost=0.1, receipt={"r": 1})              # idempotent: never double-counted
    assert led.exposure("A") == pytest.approx(0.85)
    assert led.reserve(auth_id="A", provider="runware", cap_usd=1.0, logical_job_id="job_new", estimated_max_cost=0.15)
    led.release(ok[1]["reservation_id"], reason="definitely rejected")
    assert led.exposure("A") == pytest.approx(0.75)


@pytest.mark.req("R07")
def test_process_level_concurrent_gateway_jobs_respect_cap(tmp_path):
    code = f"""
import sys, os; sys.path.insert(0, r'{ROOT}'); sys.path.insert(0, r'{ROOT / "tests"}')
from pathlib import Path
from vme.state.store import Store
from vme.util import Blocked
from test_provider_contracts import _real_gateway, _probe_job
tp = Path(r'{tmp_path}'); n = int(sys.argv[1])
st = Store(tp / f's{{n}}.sqlite')
g, t, reg, snap = _real_gateway(tp, st, cost=None, cap=1.0, est=0.4, issue=False)
try:
    g.submit(_probe_job(snap, n), task_category='capability_probe', probe=True); print('OK')
except Blocked as b:
    print('REFUSED', b.code)
"""
    env = {**os.environ, "VME_ALLOW_NETWORK": "1"}
    from vme.state.store import Store
    _real_gateway(tmp_path, Store(tmp_path / "parent.sqlite"), cap=1.0)       # ONE authorization shared by all processes
    procs = [subprocess.Popen([sys.executable, "-c", code, str(i)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
             for i in range(5)]
    outs = [p.communicate(timeout=300) for p in procs]
    res = [(o[0].strip().splitlines() or ["NO_OUTPUT: " + o[1][-600:]])[-1] for o in outs]
    assert res.count("OK") == 2, (res, [o[1][-400:] for o in outs])
    assert res.count("REFUSED SPEND_CAP_EXCEEDED") == 3
    from vme.providers.ledger import SpendLedger
    rows = SpendLedger(tmp_path / "authz" / "SPEND_LEDGER.sqlite").rows()
    assert sorted(r["status"] for r in rows) == ["SETTLED_COST_UNKNOWN"] * 2    # unknown provider cost stays a liability


@pytest.mark.req("R07")
def test_unreserved_spend_api_is_gone(tmp_path):
    from vme.providers.authorization import AuthorizationRegistry
    with pytest.raises(Blocked) as e:
        AuthorizationRegistry(tmp_path).record_spend("a", 1.0)
    assert e.value.code == "UNRESERVED_SPEND_FORBIDDEN"


@pytest.mark.req("R03")
def test_anthropic_sdk_pinned_and_request_serializes(tmp_path):
    lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    pin = re.search(r"^anthropic==([0-9.]+)$", lock, re.M)
    assert pin, "anthropic SDK must be pinned in requirements.lock"
    import anthropic
    assert anthropic.__version__ == pin.group(1)
    assert f'"anthropic=={pin.group(1)}"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    from vme.vision.claude_adapter import ClaudeBatchVisionAdapter
    params = ClaudeBatchVisionAdapter.serialize("frame_packet", "S", "{}", [("FRAME a:1 [TARGET]", _img())], "claude-opus-5-5", 1000)
    ClaudeBatchVisionAdapter.validate_params(params, max_images=20)
    from anthropic.types.messages.batch_create_params import Request   # SDK request TypedDict exists in the pinned version
    assert "custom_id" in Request.__annotations__ and "params" in Request.__annotations__


@pytest.mark.req("R07", "ST28-24")
def test_crash_after_response_saved_before_settle_neither_loses_cost_nor_replays(tmp_path, store, monkeypatch):
    from vme.vision.runner import SimulatedCrash
    monkeypatch.setenv("VME_ALLOW_NETWORK", "1")
    g, t, reg, snap = _real_gateway(tmp_path, store, cost=0.2)
    job = _probe_job(snap)
    monkeypatch.setenv("VME_CRASH_AT", "gateway_after_response_saved")
    with pytest.raises(SimulatedCrash):
        g.submit(job, task_category="capability_probe", probe=True)
    assert [x["status"] for x in reg.ledger.rows()] == ["RESERVED"]          # liability still counted against the cap
    monkeypatch.delenv("VME_CRASH_AT")
    r = g.submit(job, task_category="capability_probe", probe=True)
    rows = reg.ledger.rows()
    assert t.billed() == 1 and t.duplicate_bills() == 0 and len(rows) == 1
    assert rows[0]["status"] == "SETTLED" and rows[0]["actual_cost"] == pytest.approx(0.2) and r["cost_usd"] == pytest.approx(0.2)
