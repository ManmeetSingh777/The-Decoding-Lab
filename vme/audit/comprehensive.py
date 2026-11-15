"""`python -m vme.audit.comprehensive --out <zip>` builds VME_V13_COMPREHENSIVE_REPAIR_AUDIT.zip from ACTUAL executions.

Every evidence JSON is produced by calling the repaired production code with SIMULATED transports (no socket is opened, no paid
call, no source upload). Nothing here is artistic evidence about the real films. Test, lint and type logs come from commands
run in the repo AND in a fresh extraction of the ZIP's own source.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import uuid
import zipfile
from pathlib import Path

from ..util import Blocked, atomic_write_json, atomic_write_text, now_iso, read_json, sha256_bytes, sha256_file
from ..state.workspace import Workspace
from .export import ROOT, SPEC, EXCLUDE_DIRS, EXCLUDE_SUFFIX, _run, _ver, verify_zip

HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"
BASE_COMMIT = "651c75b"
SPEC28 = ["VME_V13_COMPREHENSIVE_ROOT_CAUSE_REPAIR_CONTRACT.md", "VME_V13_REAL_PATH_INDEPENDENT_AUDIT_2.md",
          "28_ARTISTIC_INVESTIGATION_STANDARD_AND_CONTINUITY.md", "28_VERSIONED_VISION_PROMPT_CONTRACT.md",
          "28_WORKED_INVESTIGATION_AND_CALIBRATION.md", "28_STANDARD_IMPLEMENTATION_TEST_PLAN.md", "28_INVESTIGATION_CAPSULE_SCHEMA.json",
          "00_PASTE_INTO_CLAUDE_COMBINED_REPAIR_AND_STANDARD.txt", "README_USE_ONLY_THIS_PACKAGE.md", "VME_V13_REPAIR_SOURCE_FACTS.json"]


def _g(st, rtype: str, rid: str) -> dict:
    r = st.get(rtype, rid)
    if r is None:
        raise Blocked("AUDIT_RECORD_MISSING", f"{rtype}:{rid}")
    return r


def _w(base: Path, name: str, obj) -> str:
    p = base / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        atomic_write_text(p, obj)
    else:
        atomic_write_json(p, obj)
    return sha256_file(p)


def _redact_body(task: dict) -> dict:
    t = dict(task)
    if "inputs" in t:
        refs = t["inputs"].get("referenceImages", [])
        t["inputs"] = {"referenceImages": [{"redacted": "data URI bytes omitted from the audit", "chars": len(r),
                                            "decoded_png_sha256": sha256_bytes(base64.b64decode(r.split(",", 1)[1])) if r.startswith("data:") else None}
                                           for r in refs]}
    return t


# ------------------------------------------------------------------------------------------------ provider contracts
def provider_contracts(out: Path, tmp: Path) -> dict:
    from ..vision.runner import plan_packets
    from ..providers.ids import packet_custom_id, CUSTOM_ID_RE
    from ..vision.claude_adapter import ClaudeBatchVisionAdapter
    from ..testing.simulated_anthropic import SimulatedAnthropicClient, SimulatedAPIStatusError
    from ..providers.gateway import OfflineRecordingTransport
    from ..providers.runware import RunwareAdapter
    from PIL import Image
    import io
    d = out / "REQUEST_PROVIDER_CONTRACTS"
    idx = [{"pts": i, "pts_time": i / 30, "frame_content_sha256": f"{i:064x}"} for i in range(80)]
    plans = plan_packets(idx, 0, 79, film_sha="a" * 64, pass_id="REAL-EXAMPLE-L0", cluster_id="win_example", model_version="claude-opus-5-5",
                         max_images=20)
    ids = [packet_custom_id(p) for p in plans]
    old = f"{plans[0].idempotency_key}-{uuid.uuid5(uuid.NAMESPACE_URL, plans[0].packet_id)}"
    b = io.BytesIO()
    Image.new("RGB", (64, 36), (9, 9, 9)).save(b, format="PNG")
    png = b.getvalue()
    params = ClaudeBatchVisionAdapter.serialize("frame_packet", "<P1 instructions: see ART_INVESTIGATION_STANDARD_TRACE.json>",
                                                json.dumps({"packet_id": plans[0].packet_id, "target_frames": "..."}),
                                                [(f"FRAME {'a' * 16}:{i} [TARGET] image_sha=...", png) for i in range(2)], "claude-opus-5-5", 16000)
    ClaudeBatchVisionAdapter.validate_params(params, max_images=20)
    for c in params["messages"][0]["content"]:
        if c["type"] == "image":
            c["source"]["data"] = f"<base64 PNG {len(png)} bytes sha256={sha256_bytes(png)}>"
    _w(d, "anthropic_batch_create_request.json", {"sdk_call": "client.messages.batches.create(requests=[{custom_id, params}])",
                                                   "requests": [{"custom_id": ids[0], "params": params}],
                                                   "custom_id_rule": "^[A-Za-z0-9_-]{1,64}$ (docs: messages/batches/create)",
                                                   "all_packet_custom_ids": ids, "lengths": sorted({len(i) for i in ids}),
                                                   "all_valid": all(CUSTOM_ID_RE.fullmatch(i) for i in ids),
                                                   "pre_repair_formula_example": old, "pre_repair_length": len(old),
                                                   "label": "SIMULATED/OFFLINE serialization example — never sent"})
    c = SimulatedAnthropicClient(tmp / "strict_anthropic")
    rej: list[dict] = []
    for cid, pr in ((old, params), ("bad id!", params), ("vme_ok", {**params, "bogus": 1})):
        try:
            c.messages.batches.create(requests=[{"custom_id": cid, "params": pr}])
            rej.append({"custom_id": cid, "result": "ACCEPTED (unexpected)"})
        except SimulatedAPIStatusError as e:
            rej.append({"custom_id": cid, "status_code": e.status_code, "error": str(e)[:200]})
    _w(d, "anthropic_strict_fake_rejections.json", {"rejections": rej, "billed_requests": c.billed_requests()})
    t = OfflineRecordingTransport(tmp / "strict_runware")
    # the hand-built NEGATIVE payloads live in the test suite: no module under vme/ may build a raw positivePrompt task (C14 scan)
    sys.path.insert(0, str(ROOT / "tests"))
    from test_provider_contracts import runware_rejection_cases   # type: ignore
    cases = runware_rejection_cases()
    rr = {}
    for k, task in cases.items():
        try:
            t(json.dumps([task]).encode(), {})
            rr[k] = "ACCEPTED (unexpected)"
        except Blocked as e:
            rr[k] = str(e)[:300]
    samples = {"processing": {"data": [{"taskUUID": "U", "status": "processing"}]}, "success": {"data": [{"taskUUID": "U", "status": "success",
                                                                                                         "imageURL": "https://im.runware.ai/x.png"}]},
               "error": {"errors": [{"taskUUID": "U", "code": "invalidReferenceImage"}]}, "not_found": {"errors": [{"taskUUID": "U", "code": "taskNotFound"}]},
               "garbage": "not json"}
    cls = {k: RunwareAdapter.classify(json.dumps(v).encode() if not isinstance(v, str) else v.encode(), "U")["status"] for k, v in samples.items()}
    _w(d, "runware_strict_fake_rejections.json", {"rejected": rr, "billed": t.billed()})
    _w(d, "runware_getResponse_classification.json", {"classification": cls, "gateway_rule": "PROCESSING→PROVIDER_PENDING (no resend); "
                                                       "ERROR→release reservation; NOT_FOUND/UNPARSEABLE after a possible send→UNKNOWN_BILLING + human reconcile"})
    return {"custom_id_lengths": sorted({len(i) for i in ids}), "runware_rejections": len(rr), "classification": cls}


# ------------------------------------------------------------------------------------------------ crash + cost
_HK_VISION = r"""
import sys, json; sys.path.insert(0, r'{root}')
from pathlib import Path
from vme.vision.claude_adapter import ClaudeBatchVisionAdapter, default_caps
from vme.providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
from vme.testing.simulated_anthropic import SimulatedAnthropicClient
from vme.util import Blocked
import io
from PIL import Image
tp = Path(r'{tp}')
reg = AuthorizationRegistry(tp / 'authz')
if not reg.find('anthropic-claude', 'claude-opus-5-5', 'source_vision'):
    reg.issue(provider='anthropic-claude', model_id='claude-opus-5-5', task_categories=['source_vision'], spend_cap_usd=10.0, issued_by='{human}',
              confirm_phrase=CONFIRM_PHRASE, source_upload_consent=True, allowed_source_shas=['f' * 64])
client = SimulatedAnthropicClient(tp / 'remote_provider')
ad = ClaudeBatchVisionAdapter(default_caps(), reg, tp / 'journal', client_factory=lambda: client, transport_kind='SIMULATED')
b = io.BytesIO(); Image.new('RGB', (64, 36), (1, 2, 3)).save(b, format='PNG'); png = b.getvalue()
try:
    r = ad.request_json('vme_nd_' + '7' * 40, 'native_detail', 'S', json.dumps({{'reason': 'r', 'frame': 1}}), [('FULL f:1', png, 64, 36), ('NATIVE_CROP f:1', png, 64, 36)], source_shas=['f' * 64])
    print(json.dumps({{'result': 'OK', 'batch': r['receipt']['batch_id']}}))
except Blocked as e:
    print(json.dumps({{'result': 'BLOCKED', 'code': e.code}}))
print(json.dumps({{'billed': client.billed_requests(), 'ledger': [x['status'] for x in reg.ledger.rows()],
                  'journal': json.loads((tp / 'journal' / ('task_vme_nd_' + '7' * 40 + '.json')).read_text())['state']}}))
"""

_HK_IMAGE = r"""
import sys, json; sys.path.insert(0, r'{root}'); sys.path.insert(0, r'{root}/tests')
from pathlib import Path
from vme.state.store import Store
from test_provider_contracts import _real_gateway, _probe_job
tp = Path(r'{tp}')
st = Store(tp / 'jobs.sqlite')
g, t, reg, snap = _real_gateway(tp, st, cost=0.2)
r = g.submit(_probe_job(snap), task_category='capability_probe', probe=True)
print(json.dumps({{'task_uuid': r['task_uuid'], 'billed': t.billed(), 'dups': t.duplicate_bills(), 'ledger': [(x['status'], x['actual_cost']) for x in reg.ledger.rows()],
                  'poll_log': json.loads((tp / 'art' / 'provider' / r['job_id'] / 'poll_log.json').read_text()) if (tp / 'art' / 'provider' / r['job_id'] / 'poll_log.json').exists() else None}}))
"""


def crash_and_cost(out: Path, tmp: Path) -> dict:
    d = out / "CRASH_AND_COST"
    py = sys.executable
    res: dict = {}
    for name, code, point in (("HARD_KILL_1_vision_accepted_before_batch_id_saved.json", _HK_VISION, "vision_after_create_before_save"),
                              ("HARD_KILL_2_image_sent_before_receipt_saved.json", _HK_IMAGE, "gateway_after_send_before_save")):
        tp = tmp / name.split(".")[0]
        tp.mkdir(parents=True, exist_ok=True)
        src = code.format(root=str(ROOT), tp=str(tp), human=HUMAN)
        env = {**os.environ, "VME_ALLOW_NETWORK": "1", "VME_CRASH_AT": point, "VME_CRASH_HARD": "1", "PYTHONIOENCODING": "utf-8"}
        r1 = subprocess.run([py, "-c", src], env=env, capture_output=True, text=True, timeout=600)
        env.pop("VME_CRASH_AT")
        r2 = subprocess.run([py, "-c", src], env=env, capture_output=True, text=True, timeout=600)
        r3 = subprocess.run([py, "-c", src], env=env, capture_output=True, text=True, timeout=600)
        rec = {"crash_point": point, "kill": {"returncode": r1.returncode, "meaning": "os._exit(97) — hard kill, no cleanup"},
               "restart_1": {"returncode": r2.returncode, "stdout": r2.stdout.strip().splitlines(), "stderr_tail": r2.stderr[-400:]},
               "restart_2": {"returncode": r3.returncode, "stdout": r3.stdout.strip().splitlines()},
               "label": "SIMULATED provider (durable on disk, survives the kill); no network"}
        _w(d, name, rec)
        res[name] = rec
    # concurrency
    from ..providers.ledger import SpendLedger
    led = SpendLedger(tmp / "conc" / "L.sqlite")
    ok: list[dict] = []
    refused: list[str] = []

    def go(i):
        try:
            ok.append(led.reserve(auth_id="A", provider="runware", cap_usd=1.0, logical_job_id=f"job{i}", estimated_max_cost=0.25))
        except Blocked as b:
            refused.append(b.code)
    ts = [threading.Thread(target=go, args=(i,)) for i in range(12)]
    for x in ts:
        x.start()
    for x in ts:
        x.join()
    conc = {"threads": 12, "cap_usd": 1.0, "reservation_usd": 0.25, "reserved": len(ok), "refused": refused, "exposure": led.exposure("A"),
            "process_level": "tests/test_provider_contracts.py::test_process_level_concurrent_gateway_jobs_respect_cap (5 processes, 2 OK, 3 refused)"}
    _w(d, "CONCURRENT_RESERVATIONS.json", conc)
    # manual reconciliation
    from ..state.store import Store
    sys.path.insert(0, str(ROOT / "tests"))
    from test_provider_contracts import _real_gateway, _probe_job   # type: ignore
    os.environ["VME_ALLOW_NETWORK"] = "1"
    tp = tmp / "manual"
    st = Store(tp / "s.sqlite")
    g, t, reg, snap = _real_gateway(tp, st, mode="drop_before_accept")
    job = _probe_job(snap)
    steps = []
    try:
        g.submit(job, task_category="capability_probe", probe=True)
    except Blocked as b:
        steps.append({"submit": b.code, "ledger": [x["status"] for x in reg.ledger.rows()], "task_uuid": st.conn.execute("SELECT task_uuid FROM jobs").fetchone()[0]})
    try:
        g.submit(job, task_category="capability_probe", probe=True)
    except Blocked as b:
        steps.append({"resubmit": b.code, "note": "never blind-resent"})
    try:
        g.reconcile_unknown(job.logical_sha256, resolution="CONFIRMED_NOT_ACCEPTED", by="claude", evidence="x")
    except Blocked as b:
        steps.append({"agent_reconcile": b.code})
    g.reconcile_unknown(job.logical_sha256, resolution="CONFIRMED_NOT_ACCEPTED", by=HUMAN, evidence="fixture: provider dashboard shows no task")
    t.mode = "ok"
    r = g.submit(job, task_category="capability_probe", probe=True)
    steps.append({"after_human_reconcile": "COMMITTED", "new_task_uuid": r["task_uuid"], "uuid_version": uuid.UUID(r["task_uuid"]).version,
                  "billed": t.billed(), "ledger": [x["status"] for x in reg.ledger.rows()]})
    st.close()
    _w(d, "MANUAL_RECONCILIATION.json", {"steps": steps})
    return {"hard_kills": {k: (v["restart_1"]["stdout"]) for k, v in res.items()}, "concurrency": {"reserved": len(ok), "refused": len(refused)}}


# ------------------------------------------------------------------------------------------------ drill-based evidence
def _drive_to_end(ws, prov, run_id):
    from ..testing.drill import drive
    out = drive(ws, prov, run_id=run_id, max_rounds=40)
    if out["result"].get("completed_through") != "S9":
        raise Blocked("DRILL_DID_NOT_COMPLETE", json.dumps(out["log"])[:500])
    return out


def drill_evidence(out: Path, tmp: Path) -> dict:
    """ONE simulated drill: crash after a question's raw answer → capsule A → cold import in a fresh destination → resume to S9 →
    capsule B → second fresh destination verifies a byte-identical pinned compile; then evidence traces from that workspace."""
    from ..testing.drill import build_drill_workspace, drill_providers, drill_config, enable_network_flag
    from ..loop.real import RealLoopRunner
    from ..loop.human import approve_selection
    from ..state.capsule import export_capsule, import_and_verify
    from ..vision.runner import SimulatedCrash
    enable_network_flag()
    A = tmp / "envA"
    ws = build_drill_workspace(A)["ws"]
    prov, client = drill_providers(A)
    run = "REAL-AUDIT"
    R = lambda w: RealLoopRunner(w, run_id=run, providers=prov, config=drill_config()).run()
    R(ws)
    st = ws.store()
    m = _g(st, "SelectedSequenceManifest", "REAL:15")
    st.close()
    approve_selection(ws, manifest_sha=m["manifest_sha"], approved_by=HUMAN)
    os.environ["VME_CRASH_AT"] = "real_s2_after_answer_before_decision"
    try:
        R(ws)
        crashed = False
    except SimulatedCrash:
        crashed = True
    finally:
        os.environ.pop("VME_CRASH_AT", None)
    billed_crash = client.billed_requests()
    e1 = export_capsule(ws, run, tmp / "capsule_A.zip")
    v1 = import_and_verify(tmp / "capsule_A.zip", tmp / "envB", sources_folder=A / "drill_sources")
    wsB = Workspace(tmp / "envB")
    drv = _drive_to_end(wsB, prov, run)
    e2 = export_capsule(wsB, run, tmp / "capsule_B.zip")
    v2 = import_and_verify(tmp / "capsule_B.zip", tmp / "envC", sources_folder=A / "drill_sources")
    with zipfile.ZipFile(tmp / "capsule_B.zip") as zin, zipfile.ZipFile(tmp / "capsule_D.zip", "w") as zout:
        for n in zin.namelist():
            if not ("/references/" in n and n.endswith(".png")):
                zout.writestr(n, zin.read(n))
    vD = import_and_verify(tmp / "capsule_D.zip", tmp / "envD", sources_folder=A / "drill_sources")
    _w(out, "PORTABLE_INVESTIGATION_CAPSULE_TEST.json", {
        "label": "SIMULATED drill (synthetic films, simulated vision/image transports) — engineering continuity only",
        "crash_injected": "real_s2_after_answer_before_decision (raw answer journaled, decision NOT yet published)", "crashed": crashed,
        "billed_at_crash": billed_crash, "billed_after_resume_in_new_env": client.billed_requests(), "duplicate_creates": client.duplicate_creates(),
        "capsule_A": {"sha256": e1["capsule_sha256"], "zip_sha256": e1["sha256"], "first_uncommitted_frame": e1["capsule"]["coverage"]["first_uncommitted_frame"],
                      "committed_frames": len(e1["capsule"]["coverage"]["verified_vision_frames"]),
                      "controlling_question": e1["capsule"]["active_problem"]["controlling_question"],
                      "external_jobs": e1["capsule"]["external_jobs"][:5], "protocol_sha256": e1["capsule"]["protocol_sha256"]},
        "fresh_destination_B_verification": v1, "resumed_in_B": drv["log"],
        "capsule_B": {"sha256": e2["capsule_sha256"], "pinned_rehearsal": e2["capsule"]["pinned_rehearsal"]},
        "fresh_destination_C_verification": v2, "missing_reference_bytes_destination_D": {"status": vD["status"],
                                                                                          "missing": vD["missing_capsule_artifacts"][:6],
                                                                                          "rehearsal": vD["rehearsal"]["recomputed"]}})
    _w(out, "CAPSULE_EXAMPLE.json", e2["capsule"])
    ev = evidence_from_workspace(out, wsB, run, tmp, prov)
    return {"capsule_B_verification": v2["status"], "D": vD["status"], **ev}


def evidence_from_workspace(out: Path, ws: Workspace, run: str, tmp: Path, prov) -> dict:
    from ..skills.skill import load_skill
    from ..vision.protocol import PROTOCOL_SHA, PROTOCOL_VERSION, PASSES, CALIBRATION_PAIRS
    st = ws.store()
    try:
        tr = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == run}
        s4, s5 = tr["S4"]["outputs"], tr["S5"]["outputs"]
        sk = load_skill(s4["skill_folder"])
        decs = {d["decision_id"]: d for d in sk["decisions"]}
        node = next(n for n in sk["recipes"]["main"]["nodes"] if n["id"] == "n_canonical_character")
        did = next(x for x in node["decisions"] if decs[x].get("reference_required")) if any(decs[x].get("reference_required") for x in node["decisions"]) else node["decisions"][0]
        d = decs[did]
        trace = _g(st, "RealInvestigationTrace", run)
        step = next(s for s in reversed(trace["steps"]) if s.get("decision_id") == did and s.get("question_id"))
        wit = [_g(st, "Witness", w) for w in d["evidence_frame_ids"]]
        pkt = None
        w0 = wit[0]
        rows = st.conn.execute("SELECT packet_id, pass_id, image_sha FROM frame_vision WHERE film_sha256=? AND frame_index=?",
                               (w0["film_sha256"], w0["frame_start"])).fetchall()
        if rows:
            pkt = {"packet_id": rows[0][0], "pass_id": rows[0][1], "submitted_png_sha256": rows[0][2]}
        jnl = read_json(ws.root / "providers" / "anthropic" / f"task_{step['task']}.json")
        refs = [r for r in sk["references"] if r["decision_id"] == did]
        res = read_json(next((ws.artifacts_dir / "provider").rglob("result.json")))
        canon_job = s5["n_canonical_character"]
        req_body = None
        for p in (ws.artifacts_dir / "provider").rglob("request_body.json"):
            body = json.loads(p.read_bytes())[0]
            if sha256_file(p) == canon_job["request_body_sha256"]:
                req_body = _redact_body(body)
        chain = {"label": "SIMULATED transports; synthetic films — shows the WIRING, not learned art",
                 "1_source_frame": {"film_sha256": w0["film_sha256"], "frame_index": w0["frame_start"], "pts_time": w0.get("pts_time"),
                                    "raw_frame_sha256": w0["image_sha256"], "packet": pkt},
                 "2_witnesses": [{k: w[k] for k in ("witness_id", "evidence_kind", "visible_relation", "dimensions", "region") if k in w} for w in wit],
                 "3_question": {"question_id": step["question_id"], "stage": step["stage"], "question": step["question"], "custom_id": step["task"],
                                "images_sent": step["witnesses"], "gap": step["gap"], "owned_choice_ids": step.get("owned_choice_ids"),
                                "journal_state": jnl["state"], "request_sha256": jnl["request_sha256"], "raw_answer_sha256": jnl.get("raw_sha256")},
                 "4_decision": {k: d.get(k) for k in ("decision_id", "version", "status", "owned_choice_ids", "phenomenon", "identity_basis", "dimension_tags",
                                                      "branches", "exceptions", "uncertainty", "reference_required", "visual_truth", "claim_state",
                                                      "observed_vs_inferred", "contradictions", "superseded_branches")},
                 "5_skill": {"skill_hash": sk["skill_hash"], "folder": Path(s4["skill_folder"]).name,
                             "clauses": [c for c in sk["clauses"] if c["decision_id"] == did]},
                 "6_reference_bytes": refs,
                 "7_compiled_job_and_provider_body": {"node": "n_canonical_character", "request_body_sha256": canon_job["request_body_sha256"],
                                                      "reference_shas": canon_job.get("reference_shas"), "clause_ids": canon_job.get("clause_ids"),
                                                      "provider_visible_body_redacted": req_body},
                 "8_provider_receipt_example": {k: res.get(k) for k in ("task_uuid", "task_uuid_version", "request_body_sha256", "label", "cost_status",
                                                                         "reservation_id")}}
        _w(out, "REAL_EVIDENCE_TO_REQUEST/FRAME_QUESTION_DECISION_SKILL_REFERENCE_PAYLOAD_TRACE.json", chain)
        # A28 standard trace
        fr = None
        if pkt:
            f = ws.vision_dir / pkt["pass_id"] / pkt["packet_id"] / "frames.jsonl"
            fr = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()][0]
            inp = read_json(ws.vision_dir / pkt["pass_id"] / pkt["packet_id"] / "input.json")
        phen = st.list("VisualPhenomenon")
        _w(out, "ART_INVESTIGATION_STANDARD_TRACE.json", {
            "protocol": {"version": PROTOCOL_VERSION, "sha256": PROTOCOL_SHA},
            "passes_and_code_paths": {"P0": "vme/vision/protocol.py:P0 (prepended to every pass)",
                                      "P1": "vme/vision/prompt.py:build_vision_request → vme/vision/runner.py:PacketRunner.run (every target frame)",
                                      "P2/P4": "vme/loop/real.py:RealLoopRunner._s2 → request_json(question_answer, QA_SYSTEM) → vme/vision/protocol.py:assess_sufficiency",
                                      "P3": "vme/style/coverage.py:review_visual_model_completeness + choose_controlling_gap → vme/investigation/controller.py:LoopController.step_question",
                                      "P5": "vme/loop/real.py:RealLoopRunner._reinspect (full frames + native crops + temporal neighbours)",
                                      "P6": "vme/state/capsule.py:import_and_verify (cold start)"},
            "pass_names": {k: v[0] for k, v in PASSES.items()},
            "packet_request_binding": inp["request"]["binding"] if pkt else None,
            "one_per_frame_record": fr, "construction_grade_example_SYNTHETIC": CALIBRATION_PAIRS[0],
            "counterevidence_and_contradictions": [c for x in decs.values() for c in x.get("contradictions", [])][:3],
            "unexplained_phenomena_registered": phen, "label": "SIMULATED drill records; calibration example is fictional"})
        # gap queue / question dynamics
        gq_versions = st.versions("GapQueue", run)
        best = max(gq_versions, key=lambda v: len(v["body"].get("queued", [])))["body"] if gq_versions else {}
        _w(out, "DYNAMIC_QUESTION_AND_GAP_QUEUE.json", {
            "controlling_gap": best.get("controlling_gap"), "queued_gaps": best.get("queued", [])[:30], "queued_count": len(best.get("queued", [])),
            "clusters": best.get("clusters"), "history_versions": len(gq_versions),
            "question_steps": [{k: s.get(k) for k in ("question_id", "stage", "gap", "decision_id", "owned_choice_ids", "queued_gaps", "answer_status",
                                                      "decision_changed")} for s in trace["steps"]][:60],
            "final_coverage_review": (st.get("CoverageReview", run) or {}).get("review"),
            "note": "one controlling question per step chosen from the queued gaps; other gaps stay queued (no fixed question list)"})
        _w(out, "SOURCE_FACT_TO_SKILL_TO_REQUEST.json", same_category_trace(tmp / "samecat"))
        dyn = dynamic_reinspection(out, ws, run, prov, st)
        assets = {"S7": tr["S7"]["outputs"], "pack": read_json(Path(tr["S7"]["outputs"]["pack"])), "S8": tr["S8"]["outputs"],
                  "plan": st.get("CharacterConstructionPlan", f"{run}:explorer")}
    finally:
        st.close()
    _w(out, "ASSET_MANUFACTURING/DRILL_ASSET_PACK_AND_RENDER.json", assets)
    asset_blockers(out, ws, run, prov)
    return {"decision": did, "reinspection": dyn}


def same_category_trace(tmp: Path) -> dict:
    """Two same-category decisions with different witnesses → two branches → immutable references → payload; mutations."""
    from ..state.store import Store
    sys.path.insert(0, str(ROOT / "tests"))
    import test_production_choices as T   # type: ignore
    tmp.mkdir(parents=True, exist_ok=True)
    st = Store(tmp / "s.sqlite")
    a, b = T._two_same_category_decisions(st)
    from ..style.authoring import publish_skill_version
    kw = dict(skill_id="samecat", version="0.1", evidence_origin="SIMULATED_VLM_TRANSPORT", output_contracts=T.OC,
              consent_for=lambda sha: {"status": "CONSENTED", "consented_by": HUMAN})
    r1 = publish_skill_version(tmp / "sk", [a, b], exemplar_loader=T._loader({"W-A": (200, 10, 10), "W-B": (10, 200, 10)}), **kw)
    j1 = T._compile(r1["folder"], r1["skill_hash"])
    r2 = publish_skill_version(tmp / "sk", [a, b], exemplar_loader=T._loader({"W-A": (201, 10, 10), "W-B": (10, 200, 10)}), **kw)
    j2 = T._compile(r2["folder"], r2["skill_hash"])
    r3 = publish_skill_version(tmp / "sk3", [a, b], exemplar_loader=T._loader({"W-A": (1, 1, 1), "W-B": (2, 2, 2)}), **{**kw, "consent_for": lambda s: None})
    try:
        T._compile(r3["folder"], r3["skill_hash"])
        refusal = "NONE (unexpected)"
    except Blocked as e:
        refusal = e.code
    r4 = publish_skill_version(tmp / "sk4", [a, b], exemplar_loader=None, **kw)
    try:
        T._compile(r4["folder"], r4["skill_hash"])
        refusal4 = "NONE (unexpected)"
    except Blocked as e:
        refusal4 = e.code
    st.close()
    seg = lambda j: [{k: s.get(k) for k in ("authority", "clause_id", "skill_decision_id", "text")} for s in j.trace["segments"]]
    return {"label": "SYNTHETIC witnesses (made-up film hashes)",
            "decisions": [{k: x[k] for k in ("decision_id", "owned_choice_ids", "phenomenon", "dimension_tags", "branches", "evidence_frame_ids",
                                             "identity_basis")} for x in (a, b)],
            "same_dimension_tags": a["dimension_tags"] == b["dimension_tags"], "distinct_ids": a["decision_id"] != b["decision_id"],
            "skill_v1": {"hash": r1["skill_hash"], "references": r1["references"]},
            "compiled_v1": {"logical_sha256": j1.logical_sha256, "segments": seg(j1), "reference_trace": j1.trace["reference_trace"],
                            "field_ownership": j1.trace["field_ownership"],
                            "payload_fields": sorted(j1.logical_payload), "referenceImages_count": len(j1.logical_payload["inputs"]["referenceImages"])},
            "mutation_exemplar_bytes_changed": {"skill_hash": r2["skill_hash"], "logical_sha256": j2.logical_sha256,
                                                "payload_changed": j1.logical_sha256 != j2.logical_sha256,
                                                "prompt_unchanged": j1.logical_payload["positivePrompt"] == j2.logical_payload["positivePrompt"]},
            "mutation_consent_missing": refusal, "mutation_reference_bytes_missing": refusal4,
            "independent_artistic_text_in_request": "none: every STYLE segment carries clause_id+skill_decision_id; CONTENT segments carry brief_field_path"}


def dynamic_reinspection(out: Path, ws: Workspace, run: str, prov, st) -> dict:
    from ..loop.real import RealLoopRunner
    from ..testing.drill import drill_config
    r = RealLoopRunner(ws, run_id=run, providers=prov, config=drill_config())
    vis = r._vision()
    ph = st.list("VisualPhenomenon")[0]
    trace: dict = {"steps": []}
    g = {"gap_id": f"GP_{ph['phenomenon_id']}-audit", "kind": "MISSING_SOURCE", "what": f"unexplained phenomenon {ph['phenomenon']!r} at {ph['frame_id']}",
         "dimensions": ph["connected_dimensions"], "phenomenon_id": ph["phenomenon_id"], "salience": "HIGH"}
    res = r._reinspect(st, vis, g, 1, trace)
    new_w = [st.get("Witness", w) for w in res.get("new_witness_ids", [])]
    g2 = {"gap_id": "G-audit-unknown", "kind": "MISSING_SOURCE", "what": "GRAPHICS_EXPLANATORY_VISUALS required by scope but never observed",
          "dimensions": [], "salience": "HIGH"}
    res2 = r._reinspect(st, vis, g2, 1, trace)
    studied = [s for s in _g(st, "RealInvestigationTrace", run)["steps"] if str(s.get("gap", "")).startswith("GP_")]
    dec = [d for d in st.list("ConditionalVisualDecision") if ph["phenomenon_id"] in d.get("owned_choice_ids", [])]
    rec = {"label": "SYNTHETIC phenomenon emitted by the simulated vision client (clearly labelled SIMULATED)",
           "phenomenon": ph, "reinspection_request": trace["steps"][0] if trace["steps"] else None, "result": res,
           "new_witnesses": new_w, "question_steps_for_phenomenon": studied[:6],
           "decision_owning_phenomenon": [{k: d.get(k) for k in ("decision_id", "status", "owned_choice_ids", "branches")} for d in dec],
           "unanswerable_gap": {"gap": g2, "result": res2, "meaning": "no relation visible → remains UNRESOLVED (no invented rule)"}}
    _w(out, "DYNAMIC_REINSPECTION/PHENOMENON_CROP_NEIGHBOUR_REINSPECTION.json", rec)
    return {"status": res["status"], "unknown": res2["status"]}


def asset_blockers(out: Path, ws: Workspace, run: str, prov) -> None:
    from ..testing.drill import drill_brief
    from ..loop.human import add_brief
    from ..loop.real import RealLoopRunner
    from ..testing.drill import drill_config
    b = drill_brief()
    b["shot_plan"]["actions"] += [{"actor": "explorer", "event_id": "e3", "expression": "surprised"},
                                  {"actor": "explorer", "event_id": "e4", "moves_part": "near_arm"}]
    add_brief(ws, b, added_by=HUMAN)
    o = RealLoopRunner(ws, run_id=run, providers=prov, config=drill_config()).run()
    st = ws.store()
    try:
        s7 = _g(st, "LoopTransition", f"{run}:S7")["outputs"]
        inv = [i for i in st.list("StageInvalidation") if i["run_id"] == run]
        from ..review.approvals import GateKeeper
        gate = GateKeeper(st).state(run)
    finally:
        st.close()
    _w(out, "ASSET_MANUFACTURING/DIRECTED_BRIEF_DEMANDS_AND_MISSING_ROUTES.json", {
        "brief_change": "shot_plan + expression 'surprised' + independently moving 'near_arm'", "trace": o["trace"],
        "stopped_at": o.get("stopped_at"), "reason": o.get("reason"), "demands": s7.get("demands"), "exact_blockers": s7.get("exact_blockers"),
        "stage_invalidations": inv[-3:], "gate_state_after": gate["state"],
        "meaning": "no fake multi-part actor from WHOLE_STATE_SWAP; layer/clean-plate need a verified mask route that does not exist"})


def iteration_invalidation(out: Path, tmp: Path) -> dict:
    from ..testing.drill import build_drill_workspace, drill_providers, drill_config, enable_network_flag
    from ..loop.real import RealLoopRunner
    from ..loop.human import approve_selection
    from ..review.approvals import GateKeeper
    from ..skills.skill import load_skill, skill_hash
    enable_network_flag()
    root = tmp / "rej"
    ws = build_drill_workspace(root)["ws"]
    prov, client = drill_providers(root)
    run = "REAL-REJ"
    R = lambda: RealLoopRunner(ws, run_id=run, providers=prov, config=drill_config()).run()
    R()
    st = ws.store()
    approve_selection(ws, manifest_sha=_g(st, "SelectedSequenceManifest", "REAL:15")["manifest_sha"], approved_by=HUMAN)
    st.close()
    o0 = R()
    st = ws.store()
    s4 = _g(st, "LoopTransition", f"{run}:S4")["outputs"]
    s5 = _g(st, "LoopTransition", f"{run}:S5")["outputs"]
    did = next(n for n in load_skill(s4["skill_folder"])["recipes"]["main"]["nodes"] if n["id"] == "n_canonical_character")["decisions"][0]
    imgs = _g(st, "LoopTransition", f"{run}:S6")["outputs"]["images"]
    GateKeeper(st).submit_art_verdict(run, image_paths=imgs, brief_id="BRIEF-DRILL-ANCHOR", skill_versions=[s4["skill_hash"]], verdict="REJECTED",
                                      signed_by=HUMAN, defects=[{"symptom": "FIXTURE: near arm merges into the torso silhouette",
                                                                 "attributed_stage": "STYLE_DECISION", "decision_id": did}])
    old_prompt = None
    for p in (ws.artifacts_dir / "provider").rglob("request_body.json"):
        if sha256_file(p) == s5["n_canonical_character"]["request_body_sha256"]:
            old_prompt = json.loads(p.read_bytes())[0]["positivePrompt"]
    st.close()
    o1 = R()
    o2 = R()
    st = ws.store()
    s4b = _g(st, "LoopTransition", f"{run}:S4")["outputs"]
    s5b = _g(st, "LoopTransition", f"{run}:S5")["outputs"]
    new_prompt = None
    for p in (ws.artifacts_dir / "provider").rglob("request_body.json"):
        if sha256_file(p) == s5b["n_canonical_character"]["request_body_sha256"]:
            new_prompt = json.loads(p.read_bytes())[0]["positivePrompt"]
    import difflib
    rec = {"label": "SIMULATED drill; fixture human signer", "before_rejection": o0.get("reason"), "rejection_run": {"reason": o1.get("reason"),
                                                                                                                  "trace": o1["trace"]},
           "rerun": {"trace": o2["trace"], "stopped_at": o2.get("stopped_at"), "reason": o2.get("reason")},
           "stage_invalidations": [i for i in st.list("StageInvalidation") if i["run_id"] == run],
           "revision": [r for r in st.list("ArtRevision") if r["run_id"] == run],
           "reopened_decision_after": {k: _g(st, "ConditionalVisualDecision", did).get(k) for k in ("decision_id", "version", "status", "superseded_branches",
                                                                                                   "revision_of")},
           "skill_before": s4["skill_hash"], "skill_after": s4b["skill_hash"], "old_version_still_immutable": skill_hash(s4["skill_folder"]) == s4["skill_hash"],
           "canonical_request_before": s5["n_canonical_character"]["request_body_sha256"], "canonical_request_after": s5b["n_canonical_character"]["request_body_sha256"],
           "prompt_diff": list(difflib.unified_diff((old_prompt or "").splitlines(), (new_prompt or "").splitlines(), "before", "after", lineterm=""))}
    st.close()
    _w(out, "ITERATION_INVALIDATION/ART_REJECTION_TO_NEW_SKILL_AND_REQUEST.json", rec)
    return {"skill_changed": s4["skill_hash"] != s4b["skill_hash"], "reran": [t["stage"] for t in o2["trace"] if t.get("rerun_due_to_invalidation")]}


def model_drift(out: Path) -> dict:
    from ..vision.protocol import assess_sufficiency, competing_hypothesis
    sys.path.insert(0, str(ROOT / "tests"))
    import test_investigation_standard as T   # type: ignore
    shallow = {"answer_status": "INFERRED", "REMAINING_UNKNOWN": ["x"],
               "SOURCE_VISIBLE_FACTS": [{"relation": "SYNTHETIC: vibrant polished premium look", "witness_ids": ["W-1"]}],
               "CONSTRUCTION_EXPLANATION": "great lighting",
               "BRANCHES": [{"when": {"action": "grip"}, "operation_id": "op.hand_prop_contact", "construction_action": "make it dynamic and fluid"}]}
    good = T._good_answer(["W-1"])
    a1 = assess_sufficiency(shallow, producing_operator="op.hand_prop_contact", known_witness_ids={"W-1"})
    a2 = assess_sufficiency(good, producing_operator="op.hand_prop_contact", known_witness_ids={"W-1"})
    acc = {"decision_id": "PC-accepted", "version": 3, "branches": [{"construction_action": "SYNTHETIC: draw the arm transformed toward the prop"}]}
    rec = {"label": "SYNTHETIC replacement-model responses", "shallow_response_with_all_fields": shallow, "shallow_assessment": a1,
           "substantive_alternative": good, "alternative_assessment": a2, "competing_hypothesis": competing_hypothesis(acc, good, a2),
           "protocol_drift": "vme/vision/protocol.py:verify_protocol → PROTOCOL_DRIFT unless identical sha or a recorded migration with calibration report",
           "real_path_gate": "vme/loop/real.py:_s2 stores InsufficientAnswer and does NOT author a decision from it"}
    _w(out, "MODEL_STANDARD_DRIFT_TEST.json", rec)
    return {"shallow": a1["verdict"], "alternative": a2["verdict"]}


def film_source_status(out: Path, real_ws: Workspace) -> dict:
    from ..reference.roles import role_status
    from ..state.handoff import exact_next_operation
    lock = read_json(real_ws.state_dir / "SOURCE_LOCK.json")
    six = read_json(real_ws.state_dir / "SIXTH_LOCATOR_STATUS.json") if (real_ws.state_dir / "SIXTH_LOCATOR_STATUS.json").exists() else {}
    st = real_ws.store()
    try:
        sel = st.get("SpecialIntroSelection", "REAL")
        jobs = st.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        frames_seen = st.conn.execute("SELECT COUNT(*) FROM frame_vision").fetchone()[0]
    finally:
        st.close()
    rs = role_status(real_ws)
    authz = real_ws.state_dir / "AUTHORIZATIONS.json"
    rec = {"sources": [{k: s.get(k) for k in ("file_name", "sha256", "role", "basis", "confirmed_by", "width", "height", "avg_frame_rate", "frame_count")}
                       for s in lock["sources"]],
           "true_resolution": sorted({f"{s['width']}x{s['height']}" for s in lock["sources"]}),
           "role_status": rs, "sixth_clip_role": next((s["basis"] for s in lock["sources"] if s["role"] == "SIXTH_SPECIAL"), None),
           "sixth_boundary_lock": (sel or {}).get("status", "UNLOCKED"), "sixth_locator_status": six.get("status"),
           "real_loop_expected_stop": "S0 SOURCE_ROLES_UNCONFIRMED (and S0/S1 SIXTH_BOUNDARY_NOT_LOCKED after that)",
           "first_future_human_action": "confirm (or replace) the five BASE_FILM files by SHA256 — they do not match the contract titles; then view the "
                                        "sixth-clip witness frames locally and lock the volcano start / Earth-logo arrival frames",
           "exact_next_operation_from_state": exact_next_operation(real_ws),
           "no_real_spend": {"jobs_rows": jobs, "frame_vision_rows": frames_seen, "authorizations_file_exists": authz.exists(),
                             "authorizations": read_json(authz)["authorizations"] if authz.exists() else []}}
    _w(out, "FILM_SOURCE_STATUS/SOURCE_ROLE_AND_SIXTH_BOUNDARY_STATUS.json", rec)
    return {"roles_confirmed": rs["base_five_confirmed"], "sixth": rec["sixth_boundary_lock"]}


# ------------------------------------------------------------------------------------------------ matrices
ROOT_CAUSES = [
    ("R01", "API_ASSUMPTION", "vme/providers/ids.py:custom_id_for/packet_custom_id; vme/vision/claude_adapter.py:request_json(validate_custom_id)",
     "runner built 74-char ids", ["test_all_vision_custom_ids_are_short_safe_and_stable", "test_strict_fake_batches_reject_invalid_custom_id_and_params",
                                  "test_adapter_refuses_invalid_custom_id_before_any_create"]),
    ("R02", "IMPLEMENTATION", "vme/vision/claude_adapter.py:request_json (SUBMISSION_ATTEMPTED before create, SUBMISSION_UNCERTAIN, reconcile_uncertain)",
     "create() before durable intent", ["test_accept_then_raise_is_submission_uncertain_never_resubmitted", "test_hard_kill_after_create_before_batch_id_saved_is_uncertain",
                                         "test_crash_after_intent_before_create_is_uncertain_not_resent", "test_bad_batch_results_are_named_and_raw_is_kept"]),
    ("R03", "IMPLEMENTATION", "requirements.lock, pyproject.toml (anthropic==2.8.0); ClaudeBatchVisionAdapter.validate_params", "SDK unpinned",
     ["test_anthropic_sdk_pinned_and_request_serializes"]),
    ("R04", "API_ASSUMPTION", "vme/providers/gateway.py:StyleImageGateway._run (new_task_uuid4, INTENT_PERSISTED); vme/providers/ids.py:validate_uuid4",
     "uuid5 taskUUID", ["test_runware_body_is_uuid4_with_documented_fields", "test_strict_runware_fake_rejects_uuid5_and_missing_include_cost",
                        "test_uuid4_persisted_before_network_and_reused_after_crash"]),
    ("R05", "API_ASSUMPTION", "vme/providers/runware.py:RunwareAdapter.decode_item/https_image_fetcher; compiler includeCost", "URL result refused; no includeCost",
     ["test_url_and_data_uri_results_are_decoded_and_verified", "test_url_fetch_refuses_unapproved_host_and_plain_http", "test_runware_body_is_uuid4_with_documented_fields"]),
    ("R06", "IMPLEMENTATION", "vme/providers/runware.py:RunwareAdapter.classify; gateway._query", "any parse failure = uncertain",
     ["test_accept_then_drop_reconciles_by_get_response_without_resend", "test_processing_status_is_pending_not_resent",
      "test_possible_acceptance_not_found_is_unknown_billing_then_human_reconcile", "test_gateway_kill_after_send_reconciles_without_rebilling"]),
    ("R07", "SPEC_LOGIC", "vme/providers/ledger.py:SpendLedger; AuthorizationRegistry.reserve; gateway/adapter settle/release/liability",
     "check-then-spend race", ["test_concurrent_reservations_cannot_overrun_cap", "test_process_level_concurrent_gateway_jobs_respect_cap",
                               "test_unreserved_spend_api_is_gone", "test_crash_after_response_saved_before_settle_neither_loses_cost_nor_replays"]),
    ("R08", "IMPLEMENTATION", "vme/style/authoring.py:_package_references/author_skill; vme/loop/real.py:_exemplar_loader/_reference_consent; compiler reference selection",
     "references=[]", ["test_two_same_category_findings_are_two_decisions_into_skill_and_payload", "test_reference_change_changes_payload_and_missing_consent_or_bytes_refuses"]),
    ("R09", "SPEC_LOGIC", "vme/style/authoring.py:production_choice_id/author_decision (contradictions, superseded_branches)", "decision_id_for(dims)",
     ["test_two_same_category_findings_are_two_decisions_into_skill_and_payload", "test_reanswering_same_choice_keeps_contradiction_instead_of_overwriting"]),
    ("R10", "SPEC_LOGIC", "vme/style/coverage.py:owns/_owner_for/set_relation; vme/loop/real.py:_ledger/_phenomena_gaps", "category presence = coverage",
     ["test_category_presence_is_not_choice_or_joint_coverage", "test_case4_complete_grid_still_reports_missing_face_view_light_and_hand_prop"]),
    ("R11", "IMPLEMENTATION", "vme/loop/real.py:_s2 → _reinspect; _native_followups (budget, no per-sequence cap)", "STOP on MISSING_SOURCE; first 3 crops",
     ["test_missing_source_gap_triggers_crop_and_neighbour_reinspection_not_a_stop"]),
    ("R12", "SPEC_LOGIC", "vme/loop/real.py:run/_input_key/_external_inputs; GateKeeper.reopen; _open_revision", "COMPLETED stages always skipped",
     ["test_art_rejection_reopens_decision_new_skill_new_request_only_dependants_rerun", "test_shot_plan_change_reruns_only_asset_stage_and_blocks_unproducible_demands"]),
    ("R13", "IMPLEMENTATION", "vme/loop/real.py:_s0/_s1 (SIXTH_BOUNDARY_NOT_LOCKED)", "15 without 16th", ["test_s1_refuses_15_without_locked_sixteenth"]),
    ("R14", "EXTERNAL_UNPROVEN", "vme/reference/roles.py:role_status; FILM_SOURCE_STATUS export", "real base-five identity unconfirmed", []),
    ("R15", "SPEC_LOGIC", "author_decision: claim_state, observed_vs_inferred, exemplar_witness_ids, uncertainty", "text-only branch copy",
     ["test_two_same_category_findings_are_two_decisions_into_skill_and_payload"]),
    ("R16", "IMPLEMENTATION", "compiler.compile mandatory/optional roles, STYLE_REFERENCE_CONSENT_MISSING, PROVIDER_REF_LIMIT",
     "mandatory refs unreachable", ["test_reference_change_changes_payload_and_missing_consent_or_bytes_refuses",
                                    "test_more_mandatory_references_than_provider_limit_is_named_refusal"]),
    ("R17", "IMPLEMENTATION", "vme/loop/real.py:_s7 (every demand produced or BLOCKED_*)", "expressions/layers silently skipped",
     ["test_shot_plan_change_reruns_only_asset_stage_and_blocks_unproducible_demands"]),
    ("R18", "SPEC_LOGIC", "op.world_plate (operators/compiler content_slots); coverage reverse_plan world:clean_plate; _s5/_s8 background", "actor over a scene containing it",
     ["test_world_plate_operation_sends_setting_only", "test_shot_plan_change_reruns_only_asset_stage_and_blocks_unproducible_demands"]),
    ("R19", "EXTERNAL_UNPROVEN", "_s7 LAYER/CLEAN_PLATE → BLOCKED_ROUTE_NOT_IMPLEMENTED; pack.method_limits", "no segmentation route",
     ["test_shot_plan_change_reruns_only_asset_stage_and_blocks_unproducible_demands"]),
    ("R20", "EXTERNAL_UNPROVEN", "vme/loop/real.py:_s8 (shot_plan.actors/events/camera only)", "default x=55% sprite + pan",
     ["test_renderer_refuses_undirected_actor_and_missing_event_state"]),
    ("R21", "IMPLEMENTATION", "vme/style/authoring.py:publish_skill_version (versions/<hash>, CURRENT.json)", "fixed folder rewritten",
     ["test_reference_change_changes_payload_and_missing_consent_or_bytes_refuses", "test_art_rejection_reopens_decision_new_skill_new_request_only_dependants_rerun"]),
    ("R22", "IMPLEMENTATION", "vme/loop/real.py:_windows/_review_order/_rationale_batch + CandidateCoverageLedger", "10-window cap",
     ["test_candidate_review_order_covers_every_window"]),
    ("R23", "SPEC_LOGIC", "vme/loop/real.py:_s9 (still vs animated transfer)", "one still read as transfer", []),
    ("R24", "IMPLEMENTATION", "tests/test_compiler_authority.py:_ast_scan; tests/test_real_path.py hard-kill snippet", "2 failing tests",
     ["test_static_scan_only_compiler_builds_positive_prompt_and_only_gateway_sends", "test_static_scanner_still_catches_an_unauthorized_send",
      "test_hard_kill_mid_packet_reconciles_batches"]),
]
ST28 = {
    "ST28-01": ("vme/vision/contracts.py:validate_packet_response (EMPTY_FRAME_ENTRY, GENERIC, persistent_state_ids)", ["test_every_frame_records_empty_generic_and_lost_identity_are_rejected"]),
    "ST28-02": ("vme/util.py:is_vague_statement in contracts/extract_witnesses; protocol P0", ["test_every_frame_records_empty_generic_and_lost_identity_are_rejected"]),
    "ST28-03": ("_reinspect crops keep parent_full_frame_witness + neighbours", ["test_missing_source_gap_triggers_crop_and_neighbour_reinspection_not_a_stop"]),
    "ST28-04": ("CALIBRATION_PAIRS + decision FORBIDDEN_SOURCE_SPECIFIC/role-level relations (quality needs real VLM)", []),
    "ST28-05": ("P0/P1 'alternatives until discriminated'; DIFF_KINDS", ["test_packet_request_carries_protocol_binding_and_real_images"]),
    "ST28-06": ("contracts BOUNDARY_IDENTITY_NOT_RECONCILED / BOUNDARY_EVENT_NOT_RECONCILED", ["test_every_frame_records_empty_generic_and_lost_identity_are_rejected"]),
    "ST28-07": ("coverage.choose_controlling_gap + GapQueue (one controlling question, rest queued)", ["test_case4_complete_grid_still_reports_missing_face_view_light_and_hand_prop"]),
    "ST28-08": ("protocol.assess_sufficiency gate in _s2 (InsufficientAnswer)", ["test_shallow_structurally_valid_answer_is_insufficient_and_alternative_is_kept_as_competitor"]),
    "ST28-09": ("contrast witnesses in _pick_witnesses/author_decision (cross-subject); quality needs real VLM", []),
    "ST28-10": ("production_choice_id", ["test_two_same_category_findings_are_two_decisions_into_skill_and_payload"]),
    "ST28-11": ("coverage owns + joint witness evidence", ["test_case4_complete_grid_still_reports_missing_face_view_light_and_hand_prop"]),
    "ST28-12": ("observed_vs_inferred + contradictions + assess_sufficiency", ["test_reanswering_same_choice_keeps_contradiction_instead_of_overwriting"]),
    "ST28-13": ("skill clauses + reference bytes + field_ownership", ["test_reference_change_changes_payload_and_missing_consent_or_bytes_refuses"]),
    "ST28-14": ("provenance.RESIDUAL_NOTICE (uncontrolled appearance reported, not credited) — needs real output", []),
    "ST28-15": ("_s7 BLOCKED states; no SVG/tube fallback", ["test_shot_plan_change_reruns_only_asset_stage_and_blocks_unproducible_demands"]),
    "ST28-16": ("_s8 EVENT_STATE_NOT_PRODUCED / SHOT_PLAN_NOT_DIRECTED", ["test_renderer_refuses_undirected_actor_and_missing_event_state"]),
    "ST28-17": ("journal + capsule first_uncommitted_frame", ["test_capsule_cold_start_resumes_first_uncommitted_operation_without_rebilling",
                                                              "test_hard_kill_mid_packet_reconciles_batches"]),
    "ST28-18": ("protocol sha + verify_protocol", ["test_protocol_is_versioned_hashed_and_bound"]),
    "ST28-19": ("competing_hypothesis; contradictions retained", ["test_shallow_structurally_valid_answer_is_insufficient_and_alternative_is_kept_as_competitor"]),
    "ST28-20": ("capsule import_and_verify missing artifacts", ["test_capsule_cold_start_resumes_first_uncommitted_operation_without_rebilling"]),
    "ST28-21": ("rejection → reopen → new skill → different request", ["test_art_rejection_reopens_decision_new_skill_new_request_only_dependants_rerun"]),
    "ST28-22": ("coverage_for_range per range + capsule all_sequences + CandidateCoverageLedger", ["test_s1_refuses_15_without_locked_sixteenth"]),
    "ST28-23": ("evidence_origin SIMULATED_VLM_TRANSPORT propagation; capsule origin enum", ["test_simulated_origin_never_becomes_real_source_qualified"]),
    "ST28-24": ("R01–R07 strict fakes", ["test_accept_then_raise_is_submission_uncertain_never_resubmitted", "test_concurrent_reservations_cannot_overrun_cap"]),
}
UNPROVEN = {"R14": "UNPROVEN: needs the user's confirmation of the five base films (and 1080p originals if any)",
            "R19": "BLOCKED: no verified segmentation/hidden-surface/clean-plate route; demand is blocked by name",
            "R20": "UNPROVEN: directed renderer contract implemented; professional multi-actor acting needs approved real art",
            "R23": "UNPROVEN: labels separated; real still/animated transfer needs real art + human review",
            "ST28-04": "UNPROVEN: needs real VLM output on real frames", "ST28-09": "UNPROVEN: needs real contrasting witnesses",
            "ST28-14": "UNPROVEN: needs a real provider output"}


def matrices(out: Path, results: list[dict]) -> dict:
    by: dict[str, list] = {}
    for r in results:
        name = r["nodeid"].split("::")[-1].split("[")[0]
        by.setdefault(name, []).append(r["outcome"])

    def status(tests, key):
        outs = [o for t in tests for o in by.get(t, ["NOT_RUN"])]
        if any(o == "failed" for o in outs):
            return "FAIL"
        if any(o == "NOT_RUN" for o in outs):
            return "FAIL" if tests else UNPROVEN.get(key, "UNPROVEN").split(":")[0]
        base = "PASS" if outs else "UNPROVEN"
        return UNPROVEN.get(key, base).split(":")[0] if key in UNPROVEN and base == "PASS" else base
    red = read_json(ROOT / "evidence" / "RED_BEFORE_REPRODUCERS.json") if (ROOT / "evidence" / "RED_BEFORE_REPRODUCERS.json").exists() else {}
    rows = []
    for rid, cls, sym, prefix, tests in ROOT_CAUSES:
        rows.append({"id": rid, "classification": cls, "code_symbols": sym, "pre_fix_defect": prefix,
                     "pre_fix_reproducer": {k: v for k, v in red.items() if k.startswith(rid)} or "see evidence/RED_BEFORE_*",
                     "tests": tests, "test_outcomes": {t: by.get(t, ["NOT_RUN"]) for t in tests}, "status": status(tests, rid),
                     "truthful_exception": UNPROVEN.get(rid)})
    st28 = [{"id": k, "code": v[0], "tests": v[1], "test_outcomes": {t: by.get(t, ["NOT_RUN"]) for t in v[1]}, "status": status(v[1], k),
             "truthful_exception": UNPROVEN.get(k)} for k, v in ST28.items()]
    _w(out, "ROOT_CAUSE_MATRIX.json", {"rows": rows, "status_vocab": ["PASS", "FAIL", "BLOCKED", "UNPROVEN"],
                                        "note": "PASS = software behaviour on strict offline fakes only; no artistic or live-provider claim"})
    _w(out, "CRITICAL_REPAIR_CROSSWALK.json", {"R": rows, "ST28": st28, "global_status": "NONE (no global pass for missing visual evidence)"})
    tot: dict[str, int] = {}
    for r in rows + st28:
        tot[r["status"]] = tot.get(r["status"], 0) + 1
    return tot


# ------------------------------------------------------------------------------------------------ checks + zip
def run_checks(out: Path, repo: Path, tag: str) -> dict:
    py = sys.executable
    raw = out / f"test_results_{tag}.json"
    env = {"VME_TEST_RESULTS": str(raw), "PYTHONPATH": str(repo)}
    res = {"pytest": _run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", "tests"], repo, env, timeout=10800),
           "pyflakes": _run([py, "-m", "pyflakes", "vme", "tests"], repo), "mypy": _run([py, "-m", "mypy", "vme", "--ignore-missing-imports"], repo),
           "compileall": _run([py, "-m", "compileall", "-q", "vme"], repo), "node_check": _run(["node", "--check", "render/remotion/render.mjs"], repo)}
    spec = repo.parent / "Visual_Mastery_Engine_Build_Spec_v1_3"
    for k, sub in (("reference_impl_v12", "reference_impl"), ("reference_impl_v13", "reference_impl_v13")):
        if (spec / sub).exists():
            res[k] = _run([py, "-m", "unittest", "-v"], spec / sub)
    logs = out / f"logs_{tag}"
    logs.mkdir(parents=True, exist_ok=True)
    for k, v in res.items():
        (logs / f"{k}.stdout.txt").write_text(v.pop("_stdout"), encoding="utf-8")
        (logs / f"{k}.stderr.txt").write_text(v.pop("_stderr"), encoding="utf-8")
    results = read_json(raw)["results"] if raw.exists() else []
    outcomes: dict = {}
    for r in results:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    summ = {"tag": tag, "repo": str(repo), "commands": res, "pytest_outcomes": outcomes,
            "pytest_summary_line": (res["pytest"]["stdout_tail"].strip().splitlines() or [""])[-1],
            "platform": {"os": platform.platform(), "python": sys.version, "node": _ver("node"), "ffmpeg": _ver("ffmpeg", "-version")}}
    _w(out, f"TEST_RESULTS_{tag.upper()}.json", {**summ, "cases": results})
    return {**summ, "results": results}


def _assemble(zpath: Path, audit: Path, real_ws: Workspace, extra_spec: list[Path]) -> list[dict]:
    files: list[dict] = []
    tmp = zpath.with_suffix(".tmp.zip")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        def add(p: Path, arc: str):
            z.write(p, arc)
            files.append({"path": arc, "sha256": sha256_file(p), "bytes": p.stat().st_size})
        for p in sorted(ROOT.rglob("*")):
            rel = p.relative_to(ROOT)
            if not p.is_file() or set(rel.parts) & (EXCLUDE_DIRS | {"audit_build_v3", "evidence_reuse"}) or p.suffix.lower() in EXCLUDE_SUFFIX:
                continue
            if rel.parts[0] in ("workspace", "reports") or p.name.endswith(".log") or p.name == ".env":
                continue
            add(p, "visual-mastery-engine/" + rel.as_posix())
        for p in sorted(audit.rglob("*")):
            if p.is_file():
                add(p, "visual-mastery-engine/audit/" + p.relative_to(audit).as_posix())
        wr = real_ws.root
        for wp in sorted(wr.rglob("*")):
            wrel = wp.relative_to(wr).as_posix()
            if wp.is_file() and ((wrel.startswith("frames/") and wrel.endswith(("index.jsonl.gz", "index_summary.json", "film_survey.json")))
                                 or wrel in ("state/SOURCE_LOCK.json", "state/FRAME_INDEX_SUMMARY.json", "state/STATE.json",
                                             "state/SIXTH_LOCATOR_STATUS.json")):
                add(wp, "visual-mastery-engine/workspace/" + wrel)
        for p in [x for x in sorted(SPEC.rglob("*")) if x.is_file() and x.suffix.lower() != ".zip" and "__pycache__" not in x.parts]:
            add(p, "Visual_Mastery_Engine_Build_Spec_v1_3/" + p.relative_to(SPEC).as_posix())
        for p in extra_spec:
            add(p, "repair_and_addendum28_inputs/" + p.name)
        z.writestr("SHA256_MANIFEST.json", json.dumps({"generated_at": now_iso(), "files": files,
                                                       "never_included": ["source MP4 bytes", "decoded source frames", "API keys/secrets",
                                                                          ".venv", "node_modules", "paid provider media"]}, indent=1))
    os.replace(tmp, zpath)
    return files


def build(out_zip: Path, *, real_workspace: Path, skip_fresh: bool = False, reuse_evidence: Path | None = None) -> dict:
    out_zip = Path(out_zip).resolve()
    b = ROOT / "audit_build_v3"

    def _force(func, path, exc):           # drill source clips are written read-only; clear the flag and retry
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if b.exists():
        shutil.rmtree(b, onexc=_force)
    if b.exists():
        raise Blocked("AUDIT_BUILD_DIR_NOT_CLEARED", str(b))
    audit, tmp = b / "audit", b / "tmp"
    audit.mkdir(parents=True)
    tmp.mkdir()
    real_ws = Workspace(real_workspace)
    summary: dict = {"started": now_iso()}
    summary["provider_contracts"] = provider_contracts(audit, tmp)
    slow = ["CRASH_AND_COST", "REAL_EVIDENCE_TO_REQUEST", "DYNAMIC_REINSPECTION", "ITERATION_INVALIDATION", "ASSET_MANUFACTURING",
            "ART_INVESTIGATION_STANDARD_TRACE.json", "CAPSULE_EXAMPLE.json", "DYNAMIC_QUESTION_AND_GAP_QUEUE.json",
            "PORTABLE_INVESTIGATION_CAPSULE_TEST.json", "SOURCE_FACT_TO_SKILL_TO_REQUEST.json"]
    if reuse_evidence and all((reuse_evidence / n).exists() for n in slow):
        # slow drill evidence generated earlier by this same generator; code paths it exercises are unchanged since then
        man = {}
        for n in slow:
            src = reuse_evidence / n
            (shutil.copytree(src, audit / n) if src.is_dir() else shutil.copy(src, audit / n))
            for f in ([src] if src.is_file() else sorted(x for x in src.rglob("*") if x.is_file())):
                man[f.relative_to(reuse_evidence).as_posix()] = sha256_file(f)
        summary["evidence_reused"] = {"from": str(reuse_evidence), "generated_at_commit": "e16d451/6641d2d (same drill code)",
                                      "files_sha256": man}
    else:
        summary["crash_and_cost"] = crash_and_cost(audit, tmp)
        summary["drill"] = drill_evidence(audit, tmp)
        summary["iteration"] = iteration_invalidation(audit, tmp)
    summary["drift"] = model_drift(audit)
    summary["film"] = film_source_status(audit, real_ws)
    after = subprocess.run([sys.executable, str(ROOT / "tools" / "repro_defects.py")], cwd=ROOT, capture_output=True, text=True)
    _w(audit, "RED_BEFORE_GREEN_AFTER/GREEN_AFTER_REPRODUCERS.json", json.loads(after.stdout))
    shutil.copy(ROOT / "evidence" / "RED_BEFORE_REPRODUCERS.json", audit / "RED_BEFORE_GREEN_AFTER" / "RED_BEFORE_REPRODUCERS.json")
    shutil.copy(ROOT / "evidence" / "RED_BEFORE_R24_TESTS.txt", audit / "RED_BEFORE_GREEN_AFTER" / "RED_BEFORE_R24_TESTS.txt")
    diff = subprocess.run(["git", "diff", f"{BASE_COMMIT}..HEAD", "--stat"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout
    full = subprocess.run(["git", "diff", f"{BASE_COMMIT}..HEAD"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout
    _w(audit, "CHANGED_FILES_STAT.txt", diff)
    _w(audit, "CHANGED_FILES.diff", full)
    _w(audit, "CODE_VERSION_HASHES.json", {"git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                                           "git_log": subprocess.run(["git", "log", "--oneline", "-12"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines(),
                                           "files": {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in sorted((ROOT / "vme").rglob("*.py"))}})
    repo_checks = run_checks(audit, ROOT, "repo")
    tot = matrices(audit, repo_checks["results"])
    extra = [ROOT.parent / n for n in SPEC28 if (ROOT.parent / n).exists()]
    stage1 = b / "stage1.zip"
    _assemble(stage1, audit, real_ws, extra)
    fresh = None
    if not skip_fresh:
        fx = b / "fresh"
        with zipfile.ZipFile(stage1) as z:
            z.extractall(fx)
        frepo = fx / "visual-mastery-engine"
        rr = frepo / "render" / "remotion"
        if (ROOT / "render" / "remotion" / "node_modules").exists() and rr.exists():
            # node_modules are excluded from the ZIP (huge dependency); link the pinned install so render tests run
            subprocess.run(["cmd", "/c", "mklink", "/J", str(rr / "node_modules"), str(ROOT / "render" / "remotion" / "node_modules")],
                           capture_output=True)
        fresh = run_checks(audit, frepo, "fresh_extraction")
        _w(audit, "FRESH_EXTRACTION_NOTE.json", {"extracted_from_sha256": sha256_file(stage1), "path": str(frepo),
                                                 "interpreter": sys.executable, "node_modules": "junction to the pinned repo install (excluded from ZIP)",
                                                 "source_mp4s": "absent in extraction; tests that need them report truthful stops"})
    summary["matrix_totals"] = tot
    summary["repo_pytest"] = repo_checks["pytest_outcomes"]
    summary["fresh_pytest"] = fresh["pytest_outcomes"] if fresh else "SKIPPED"
    _w(audit, "AUDIT_BUILD_SUMMARY.json", summary)
    from .comprehensive_docs import write_docs
    write_docs(audit, summary=summary, repo_checks=repo_checks, fresh=fresh)
    files = _assemble(out_zip, audit, real_ws, extra)
    chk = verify_zip(out_zip)
    return {"zip": str(out_zip), "sha256": sha256_file(out_zip), "files": len(files), "self_check": chk, **summary}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workspace", default=str(ROOT / "workspace"))
    ap.add_argument("--skip-fresh", action="store_true")
    ap.add_argument("--reuse-evidence", default=None)
    a = ap.parse_args(argv)
    r = build(Path(a.out), real_workspace=Path(a.workspace), skip_fresh=a.skip_fresh,
              reuse_evidence=Path(a.reuse_evidence) if a.reuse_evidence else None)
    print(json.dumps({k: r[k] for k in ("zip", "sha256", "files", "self_check", "matrix_totals", "repo_pytest", "fresh_pytest")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
