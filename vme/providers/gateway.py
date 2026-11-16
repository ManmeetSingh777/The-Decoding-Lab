"""StyleImageGateway — the SOLE image-provider entry point (spec 15 §1/§6, C14, B19, A53, ADD25-P01, ADD26-P01).

`submit(job)` accepts only a CompiledImageJob issued by StyleProgramCompiler. There is no method that accepts
prompt text. Every job is re-derived from its pinned inputs and must be byte-identical.

Provider safety (repair R04–R07):
  * each NEW logical job mints a Runware taskUUID with uuid4() ONCE, persists it with the exact request-body hash
    (state INTENT_PERSISTED) BEFORE any network call, and reuses it only for getResponse reconciliation;
  * a paid job reserves its worst-case cost in the transactional SpendLedger BEFORE sending; it is settled once on
    receipt, released only when the provider DEFINITELY rejected it, and kept as an unknown liability otherwise;
  * an interrupted task is polled (processing / success / error / not-found); any uncertain acceptance stops in
    UNKNOWN_BILLING for human reconciliation — never a blind resend;
  * a COMMITTED job returns its exact saved bytes + receipt without another request.
"""
from __future__ import annotations

import base64
import io
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw

from ..util import Blocked, atomic_write_bytes, atomic_write_json, canonical_json, now_iso, read_json, sha256_bytes
from ..artwork.raster import decode_raster
from ..compiler.compiler import CompiledImageJob, issued_by_compiler, payload_diff, recompile
from ..style.provenance import interface_two_audit
from ..vision.runner import maybe_crash
from .authorization import AuthorizationRegistry
from .capabilities import assert_paid_ready
from .ids import new_task_uuid4, validate_uuid4
from .runware import RunwareAdapter

JOB_STATES = ("INTENT_PERSISTED", "IN_FLIGHT", "RESPONSE_SAVED", "COMMITTED", "UNKNOWN_BILLING", "REJECTED", "FAILED")


class StyleImageGateway:
    def __init__(self, store, artifacts_dir: str | Path, adapter: RunwareAdapter, registry: AuthorizationRegistry):
        self.store = store
        self.art = Path(artifacts_dir)
        self.adapter = adapter
        self.registry = registry
        self._reservation: dict | None = None

    # -- the only public submission method ------------------------------------------------
    def submit(self, job: CompiledImageJob, *, task_category: str = "image_generation", probe: bool = False) -> dict:
        if not issued_by_compiler(job):
            raise Blocked("RAW_PROMPT_GATEWAY_BYPASS", "gateway accepts only issued CompiledImageJob objects")
        fresh = recompile(job)
        if fresh.trace.get("stage_plan") and int(job.trace.get("stage_index", 1)) == 1:
            return self._submit_staged(job, fresh, task_category=task_category, probe=probe)
        return self._submit_one(job, fresh, task_category=task_category, probe=probe)

    # -- R3-C01: staged multi-reference execution -------------------------------------------------
    def _stages_to_run(self, plan: list[dict]) -> list[dict]:
        return list(plan)

    def _submit_staged(self, job: CompiledImageJob, fresh: CompiledImageJob, *, task_category: str, probe: bool) -> dict:
        """Execute EVERY stage of a staged job as its own compiled request (own journal row, uuid4, reservation, receipt).
        Stage k binds the exact bytes stage k-1 returned. Coverage is checked against an INDEPENDENT recompilation, so a stage
        that silently disappears is REQUIRED_STAGE_NOT_EXECUTED, and stage 1's image is never returned as the finished asset."""
        from ..compiler.compiler import StyleProgramCompiler
        plan = fresh.trace["stage_plan"]
        required = list(fresh.trace["required_reference_shas"])
        r = self._submit_one(job, fresh, task_category=task_category, probe=probe)
        receipts = [{"stage": 1, "job_id": job.job_id, "task_uuid": r["task_uuid"], "request_body_sha256": r["request_body_sha256"],
                     "reference_shas": list(job.trace["stage_ref_shas"]), "output_sha256": r["outputs"][0]["sha256"]}]
        covered = list(job.trace["stage_ref_shas"])
        i = job.inputs
        for sp in self._stages_to_run(plan)[1:]:
            maybe_crash(f"gateway_before_stage_{sp['index']}")
            prior = r["outputs"][0]
            sj = StyleProgramCompiler().compile(i["brief"], i["skill_folder"], pinned_skill_hash=i["pinned_skill_hash"], recipe_id=i["recipe_id"],
                                                node_id=i["node_id"], caps=i["caps"], identity_assets=i["identity_assets"],
                                                output_contract=i["output_contract"], actor_scope=i.get("actor_scope"),
                                                stage={"index": sp["index"], "prior_output": {"sha256": prior["sha256"], "path": prior["path"]}})
            if sj.trace["stage_prior_output_sha"] != prior["sha256"]:
                raise Blocked("STAGE_NOT_BOUND_TO_PRIOR_OUTPUT", str(sp["index"]))
            r = self._submit_one(sj, recompile(sj), task_category=task_category, probe=probe)
            receipts.append({"stage": sp["index"], "job_id": sj.job_id, "task_uuid": r["task_uuid"], "request_body_sha256": r["request_body_sha256"],
                             "prior_output_sha256": prior["sha256"], "reference_shas": list(sj.trace["stage_ref_shas"]),
                             "output_sha256": r["outputs"][0]["sha256"]})
            covered += [s for s in sj.trace["stage_ref_shas"] if s not in covered]
        if len(receipts) != len(plan) or sorted(set(covered)) != sorted(set(required)):
            raise Blocked("REQUIRED_STAGE_NOT_EXECUTED", f"executed {len(receipts)}/{len(plan)} stages; references never submitted: "
                                                         f"{sorted(set(required) - set(covered))[:4]}")
        final = {**r, "job_id": job.job_id, "staged": True, "stage_count": len(plan), "stage_receipts": receipts,
                 "final_stage_job_id": receipts[-1]["job_id"], "reference_shas": required, "intermediate": False}
        atomic_write_json(self.art / "provider" / job.job_id / "staged_result.json", final)
        self.store.put("StagedImageResult", job.job_id, final)
        return final

    def _submit_one(self, job: CompiledImageJob, fresh: CompiledImageJob, *, task_category: str, probe: bool) -> dict:
        if fresh.logical_sha256 != job.logical_sha256 or fresh.logical_payload != job.logical_payload:
            raise Blocked("COMPILED_JOB_MUTATED", "payload differs from deterministic recompilation",
                          diff=payload_diff(fresh.logical_payload, job.logical_payload))
        if not job.baseline_only:
            audit = interface_two_audit(job.logical_payload, job.trace["field_ownership"], job.trace["segments"])
            if not audit["ok"]:
                raise Blocked("UNAUTHORIZED_STYLE_TEXT", str(audit["problems"][:3]))
        self._reservation = None
        row = self._row(job.logical_sha256)
        if row and row[0] == "COMMITTED":        # exact saved bytes + receipt; no request, no new reservation
            return dict(read_json(self.art / "provider" / job.job_id / "result.json"))
        if self.adapter.kind == "REAL":
            if job.synthetic:
                raise Blocked("SYNTHETIC_SKILL_TO_REAL_PROVIDER", "fixture skills never reach a paid provider")
            origin = job.trace.get("skill_evidence_origin", "REAL_VLM")
            if getattr(self.adapter, "transport_kind", "NETWORK") == "NETWORK" and origin not in ("REAL_VLM", None) and not job.baseline_only:
                raise Blocked("SIMULATED_EVIDENCE_SKILL_TO_NETWORK", f"skill evidence origin {origin} cannot drive a paid call")
            if row and row[0] == "UNKNOWN_BILLING":
                raise Blocked("UNKNOWN_BILLING", "pending provider task needs human reconciliation")
            assert_paid_ready(self.adapter.snapshot, probe=probe)
            est = self.adapter.snapshot.get("cost_per_image_usd")
            self._auth, self._reservation = self.registry.reserve(
                provider="runware", model_id=job.logical_payload["model"], task=task_category, estimated_cost_usd=est,
                logical_job_id=job.logical_sha256, source_shas=job.trace.get("requires_source_upload_consent_for") or None)
        return self._run(job)

    # -- journal ------------------------------------------------------------------------------
    def _row(self, key: str):
        return self.store.conn.execute("SELECT state, task_uuid, response_path, body FROM jobs WHERE job_key=?", (key,)).fetchone()

    def _set(self, key: str, state: str, **cols) -> None:
        with self.store.tx() as c:
            row = c.execute("SELECT body FROM jobs WHERE job_key=?", (key,)).fetchone()
            body = json.loads(row[0]) if row else {}
            body.update({k: v for k, v in cols.items() if k not in ("task_uuid", "response_path", "payload_sha", "cost_usd")})
            if row is None:
                c.execute("INSERT INTO jobs(job_key,kind,state,provider,task_uuid,payload_sha,response_path,cost_usd,updated_at,body) "
                          "VALUES(?,?,?,?,?,?,?,?,?,?)", (key, "image", state, "runware", cols.get("task_uuid"),
                                                          cols.get("payload_sha"), cols.get("response_path"), cols.get("cost_usd"),
                                                          now_iso(), canonical_json(body)))
            else:
                sets = ["state=?", "updated_at=?", "body=?"]
                vals = [state, now_iso(), canonical_json(body)]
                for k in ("task_uuid", "payload_sha", "response_path", "cost_usd"):
                    if k in cols:
                        sets.append(f"{k}=?")
                        vals.append(cols[k])
                c.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE job_key=?", vals + [key])
            self.store.event("IMAGE_JOB_STATE", key, {"state": state}, conn=c)

    def _ledger_call(self, what: str, **kw) -> None:
        if self._reservation is None:
            return
        led = self.registry.ledger
        rid = self._reservation["reservation_id"]
        {"settle": led.settle, "release": led.release, "liability": led.mark_liability}[what](rid, **kw)

    def _query(self, task_uuid: str, d: Path) -> tuple[str, bytes | None]:
        """getResponse polling for an interrupted task until a terminal status or the deadline (R06)."""
        deadline = time.time() + float(getattr(self.adapter, "poll_deadline_s", 0.0))
        polls: list[dict] = []
        while True:
            try:
                raw = self.adapter.send(self.adapter.query_body(task_uuid))
            except Blocked as b:
                polls.append({"at": now_iso(), "status": f"QUERY_FAILED:{b.code}"})
                atomic_write_json(d / "poll_log.json", polls)
                return "UNKNOWN", None
            c = RunwareAdapter.classify(raw, task_uuid)
            polls.append({"at": now_iso(), "status": c["status"]})
            atomic_write_json(d / "poll_log.json", polls)
            if c["status"] in ("SUCCESS", "ERROR", "NOT_FOUND"):
                return c["status"], raw
            if time.time() >= deadline:
                return ("PROCESSING" if c["status"] == "PROCESSING" else "UNKNOWN"), raw
            time.sleep(float(getattr(self.adapter, "poll_interval", 2.0)))

    def _run(self, job: CompiledImageJob) -> dict:
        key = job.logical_sha256
        d = self.art / "provider" / job.job_id
        row = self._row(key)
        if row and row[0] == "COMMITTED":
            return read_json(d / "result.json")
        if row and row[0] == "UNKNOWN_BILLING":
            raise Blocked("UNKNOWN_BILLING", "pending provider task needs human reconciliation")
        if row and row[0] in ("FAILED", "REJECTED"):
            raise Blocked("IMAGE_JOB_" + row[0], (json.loads(row[3]) if row[3] else {}).get("error", ""))
        if row is None or not row[1]:
            # NEW logical job: UUIDv4 minted ONCE, persisted with the exact body hash BEFORE any network call (R04)
            task_uuid = new_task_uuid4()
            body = self.adapter.build_body(job.logical_payload, task_uuid)
            atomic_write_bytes(d / "request_body.json", body)
            self._set(key, "INTENT_PERSISTED", task_uuid=task_uuid, payload_sha=sha256_bytes(body), job_id=job.job_id,
                      reservation_id=(self._reservation or {}).get("reservation_id"))
            maybe_crash("gateway_after_intent")
            row = self._row(key)
        task_uuid = validate_uuid4(row[1])
        body = (d / "request_body.json").read_bytes()
        if sha256_bytes(body) != self.store.conn.execute("SELECT payload_sha FROM jobs WHERE job_key=?", (key,)).fetchone()[0]:
            raise Blocked("REQUEST_BODY_CHANGED", "persisted request body no longer matches its journaled hash")
        state = row[0]
        resp: bytes | None = None
        if state == "INTENT_PERSISTED":
            # definitely never sent: mark IN_FLIGHT first, then send exactly once
            self._set(key, "IN_FLIGHT")
            maybe_crash("gateway_after_inflight")
            try:
                resp = self.adapter.send(body)
            except Blocked as b:
                if b.code == "PROVIDER_REJECTED":            # documented 4xx: request definitely not accepted
                    atomic_write_json(d / "rejection.json", b.to_dict())
                    self._set(key, "REJECTED", error=str(b))
                    self._ledger_call("release", reason=str(b)[:200])
                    raise
                state = "IN_FLIGHT"                            # acceptance unknown → reconcile, never resend
            else:
                maybe_crash("gateway_after_send_before_save")
                c = RunwareAdapter.classify(resp, task_uuid)
                if c["status"] == "ERROR":
                    atomic_write_bytes(d / "response.json", resp)
                    self._set(key, "REJECTED", error=str(c["error"])[:300], response_path=str(d / "response.json"))
                    self._ledger_call("release", reason="provider error response")
                    raise Blocked("PROVIDER_EXECUTION", str(c["error"])[:300])
                if c["status"] != "SUCCESS":
                    resp, state = None, "IN_FLIGHT"
        if state == "IN_FLIGHT" and resp is None:
            status, raw = self._query(task_uuid, d)
            if status == "SUCCESS":
                resp = raw
            elif status == "ERROR":
                atomic_write_bytes(d / "response.json", raw or b"")
                self._set(key, "FAILED", error="provider reported task error")
                self._ledger_call("release", reason="provider task error")
                raise Blocked("PROVIDER_EXECUTION", "task reported error on getResponse")
            elif status == "PROCESSING":
                raise Blocked("PROVIDER_PENDING", f"task {task_uuid} still processing; poll again later (no resend)")
            else:   # NOT_FOUND after a possible send, unqueryable or unparseable → acceptance uncertain
                self._set(key, "UNKNOWN_BILLING", error=f"reconciliation status {status}")
                self._ledger_call("liability", reason=f"acceptance uncertain ({status})")
                raise Blocked("UNKNOWN_BILLING", f"task {task_uuid} acceptance uncertain ({status}); refusing blind resubmit")
        if resp is not None:
            atomic_write_bytes(d / "response.json", resp)
            self._set(key, "RESPONSE_SAVED", response_path=str(d / "response.json"))
            maybe_crash("gateway_after_response_saved")
        resp = (d / "response.json").read_bytes()
        try:
            imgs = RunwareAdapter.parse_images(resp, task_uuid, fetch_url=getattr(self.adapter, "fetch_url", None))
        except Blocked as b:
            self._set(key, "FAILED", error=b.code)
            self._ledger_call("liability", reason=f"response saved but unusable ({b.code})")
            raise
        outs = []
        for i, im in enumerate(imgs):
            try:
                ra = decode_raster(im["bytes"], asset_id=f"{job.job_id}_img{i}", owner=job.trace.get("brief_id", "baseline"),
                                   skill_version=job.trace.get("skill_hash", "BASELINE_ONLY"),
                                   expected_size=(job.logical_payload["width"], job.logical_payload["height"]))
            except Blocked as b:
                self._set(key, "FAILED", error=b.code)
                self._ledger_call("liability", reason=f"image invalid ({b.code})")
                raise
            p = self.art / "images" / f"{ra.sha256}.png"
            atomic_write_bytes(p, im["bytes"])
            ra.path = str(p)
            outs.append({**ra.to_dict(), "imageUUID": im.get("imageUUID"), "provider_cost": im.get("cost"), "delivery": im.get("delivery")})
        cost = sum(float(o["provider_cost"] or 0) for o in outs) if all(o["provider_cost"] is not None for o in outs) else None
        result = {"job_id": job.job_id, "logical_sha256": key, "task_uuid": task_uuid, "task_uuid_version": 4,
                  "request_body_sha256": sha256_bytes(body),
                  "adapter_kind": self.adapter.kind, "synthetic_skill": job.synthetic, "baseline_only": job.baseline_only,
                  "skill_hash": job.trace.get("skill_hash"), "selected_decisions": job.trace.get("selected_decisions"),
                  "clause_ids": job.trace.get("clause_ids"), "reference_shas": [r[1] for r in job.reference_images],
                  "stage_index": int(job.trace.get("stage_index", 1)), "stage_count": len(job.trace.get("stage_plan") or [1]),
                  "intermediate": int(job.trace.get("stage_index", 1)) < len(job.trace.get("stage_plan") or [1]),
                  "outputs": outs, "cost_usd": cost, "cost_status": "REPORTED" if cost is not None else "UNKNOWN",
                  "reservation_id": (self._reservation or {}).get("reservation_id"),
                  "label": ("OFFLINE_FIXTURE_NOT_LEARNED_ART" if self.adapter.kind != "REAL" else
                            "REAL_PROVIDER_OUTPUT" if getattr(self.adapter, "transport_kind", "NETWORK") == "NETWORK"
                            else "SIMULATED_TRANSPORT_FIXTURE_IMAGE"),
                  "committed_at": now_iso()}
        self._ledger_call("settle", actual_cost=cost, receipt={"task_uuid": task_uuid, "response_sha256": sha256_bytes(resp)})
        atomic_write_json(d / "result.json", result)
        self.store.put("GeneratedRaster", job.job_id, result)
        self._set(key, "COMMITTED", cost_usd=cost)
        return result

    # -- human reconciliation of an uncertain task ------------------------------------------------
    def reconcile_unknown(self, job_key: str, *, resolution: str, by: str, evidence: str) -> dict:
        """Only a named human may resolve UNKNOWN_BILLING: CONFIRMED_NOT_ACCEPTED (release + allow a NEW uuid4) or
        CONFIRMED_BILLED (liability stays; job FAILED, never resent)."""
        if not by or by.lower() in ("agent", "claude", "codex", "model", "auto"):
            raise Blocked("HUMAN_ISSUER_REQUIRED")
        row = self._row(job_key)
        if not row or row[0] != "UNKNOWN_BILLING":
            raise Blocked("NOT_UNKNOWN_BILLING", job_key)
        body = json.loads(row[3]) if row[3] else {}
        rid = body.get("reservation_id")
        if resolution == "CONFIRMED_NOT_ACCEPTED":
            if rid:
                self.registry.ledger.release(rid, reason=f"human {by}: {evidence}")
            with self.store.tx() as c:
                c.execute("DELETE FROM jobs WHERE job_key=?", (job_key,))
                self.store.event("IMAGE_JOB_RECONCILED", job_key, {"resolution": resolution, "by": by, "evidence": evidence,
                                                                   "old_task_uuid": row[1]}, conn=c)
        elif resolution == "CONFIRMED_BILLED":
            self._set(job_key, "FAILED", error=f"human-confirmed billed without usable result ({by})")
        else:
            raise Blocked("UNKNOWN_RESOLUTION", resolution)
        return {"job_key": job_key, "resolution": resolution, "by": by}


IMAGE_TASK_FIELDS = {"taskType", "taskUUID", "model", "positivePrompt", "negativePrompt", "width", "height", "numberResults",
                     "outputType", "outputFormat", "includeCost", "inputs", "seed", "steps", "CFGScale"}


class OfflineRecordingTransport:
    """STRICT simulated Runware transport (no network). Contract per runware.ai docs for `runware:400@4`:
    UUIDv4 taskUUID, numberResults=1, outputType base64Data|dataURI|URL, outputFormat PNG|WEBP|JPG, includeCost=true,
    inputs.referenceImages 1..4, no unknown fields. Violations are REJECTED (HTTP-400 equivalent, not billed).
    Every accepted imageInference is billed — a second send of the same taskUUID is recorded as a DUPLICATE bill
    (the fake does not assume server-side idempotency). Returns a locally drawn, labelled FIXTURE PNG.

    modes: ok | wrong_size | invalid_bytes | http_error | url_only | data_uri | no_image | accept_then_drop
           | drop_before_accept | processing (getResponse reports processing `processing_polls` times first)
    """

    def __init__(self, state_dir: str | Path, *, mode: str = "ok", queryable: bool = True, cost: float | None = 0.0,
                 processing_polls: int = 1):
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.queryable = queryable
        self.cost = cost
        self.processing_polls = processing_polls

    def sent_bodies(self) -> list[dict]:
        return [read_json(p) for p in sorted(self.dir.glob("req_*.json"))]

    def billed(self) -> int:
        return len(list(self.dir.glob("bill_*.json")))

    def duplicate_bills(self) -> int:
        return len(list(self.dir.glob("bill_*_dup*.json")))

    def rejected(self) -> list[dict]:
        return [read_json(p) for p in sorted(self.dir.glob("rejected_*.json"))]

    @staticmethod
    def contract_problems(t: dict) -> list[str]:
        from .ids import validate_uuid4
        probs = []
        unknown = sorted(set(t) - IMAGE_TASK_FIELDS)
        if unknown:
            probs.append(f"unknown fields {unknown}")
        try:
            validate_uuid4(t.get("taskUUID", ""))
        except Blocked as b:
            probs.append(str(b))
        if t.get("taskType") != "imageInference":
            probs.append("taskType must be imageInference")
        for k in ("model", "positivePrompt", "width", "height"):
            if k not in t:
                probs.append(f"missing {k}")
        if t.get("numberResults") != 1:
            probs.append("numberResults must be 1")
        if t.get("outputType") not in ("base64Data", "dataURI", "URL"):
            probs.append("outputType invalid")
        if t.get("outputFormat") not in ("PNG", "WEBP", "JPG"):
            probs.append("outputFormat invalid")
        if t.get("includeCost") is not True:
            probs.append("includeCost must be true")
        refs = (t.get("inputs") or {}).get("referenceImages")
        if "inputs" in t and (not isinstance(refs, list) or not 1 <= len(refs) <= 4 or set(t["inputs"]) - {"referenceImages"}):
            probs.append("inputs.referenceImages must be a list of 1..4 images")
        for k in ("width", "height"):
            if isinstance(t.get(k), int) and (t[k] % 16 or not 128 <= t[k] <= 2048):
                probs.append(f"{k} must be a multiple of 16 in [128,2048]")
        return probs

    def fetcher(self):
        """Fixture URL fetcher (only for url_only mode): serves the stored bytes for https://im.runware.ai/fx/<uuid>.png."""
        def fetch(url: str) -> tuple[bytes, str]:
            from urllib.parse import urlparse
            u = urlparse(url)
            if u.scheme != "https" or u.hostname != "im.runware.ai":
                raise Blocked("PROVIDER_URL_HOST_NOT_ALLOWED", url)
            p = self.dir / f"img_{Path(u.path).stem}.png"
            if not p.exists():
                raise Blocked("PROVIDER_URL_EXPIRED_OR_UNFETCHED", url)
            return p.read_bytes(), "image/png"
        return fetch

    def _image(self, body: bytes, w: int, h: int) -> bytes:
        # Derived from the LOGICAL request only (the per-run random taskUUID is excluded): the same request always yields the
        # same bytes, and different requests differ VISIBLY (full-RGB fill + a hash-placed block). Hashing the raw body made
        # the colour random per run, so two drawing states sometimes came out near-identical and the motion gate (correctly)
        # judged the swap STATIC — a fixture flake, not an engine fault.
        try:
            tasks = json.loads(body)
            logical = canonical_json([{k: v for k, v in t.items() if k != "taskUUID"} for t in tasks]).encode("utf-8")
        except (ValueError, TypeError, AttributeError):
            logical = body
        hx = sha256_bytes(logical)
        fill = tuple(40 + int(hx[i:i + 2], 16) * 175 // 255 for i in (0, 2, 4))
        im = Image.new("RGB", (w, h), fill)
        dr = ImageDraw.Draw(im)
        bx, by = int(hx[6:8], 16) * max(1, w - w // 3) // 255, int(hx[8:10], 16) * max(1, h - h // 3) // 255
        dr.rectangle([bx, by, bx + w // 3, by + h // 3], fill=tuple(255 - c for c in fill))
        dr.rectangle([8, 8, w - 9, h - 9], outline=(255, 255, 255), width=3)
        dr.text((20, 20), "OFFLINE FIXTURE - NOT LEARNED ART", fill=(255, 255, 255))
        dr.text((20, 40), f"payload {hx[:16]}", fill=(255, 255, 255))
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue()

    def __call__(self, body: bytes, headers: dict) -> bytes:
        tasks = json.loads(body)
        t = tasks[0]
        if t.get("taskType") == "getResponse":
            if not self.queryable:
                raise Blocked("PROVIDER_QUERY_UNSUPPORTED")
            uid = t["taskUUID"]
            p = self.dir / f"resp_{uid}.json"
            if not p.exists():
                return json.dumps({"errors": [{"code": "taskNotFound", "taskUUID": uid, "message": "fixture: unknown task"}]}).encode()
            qp = self.dir / f"polls_{uid}.json"
            n = read_json(qp)["n"] + 1 if qp.exists() else 1
            atomic_write_json(qp, {"n": n})
            if self.mode == "processing" and n <= self.processing_polls:
                return json.dumps({"data": [{"taskType": "imageInference", "taskUUID": uid, "status": "processing"}]}).encode()
            return p.read_bytes()
        probs = self.contract_problems(t)
        uid = str(t.get("taskUUID"))
        if probs:
            atomic_write_json(self.dir / f"rejected_{sha256_bytes(body)[:16]}.json", {"problems": probs, "taskUUID": uid})
            raise Blocked("PROVIDER_REJECTED", "; ".join(probs)[:500], http_status=400)
        if self.mode == "http_error":
            raise Blocked("PROVIDER_REJECTED", "invalidModel (fixture)", http_status=400)
        if self.mode == "drop_before_accept":
            raise Blocked("TRANSPORT_UNCERTAIN", "fixture: connection reset before the provider accepted")
        bill = self.dir / f"bill_{uid}.json"
        if bill.exists():
            k = len(list(self.dir.glob(f"bill_{uid}_dup*.json")))
            atomic_write_json(self.dir / f"bill_{uid}_dup{k}.json", {"at": now_iso()})
        else:
            atomic_write_json(bill, {"at": now_iso()})
        atomic_write_json(self.dir / f"req_{uid}.json", {"body_sha256": sha256_bytes(body), "task": {k: (v if k != "inputs" else
                          {"referenceImages_count": len(v.get("referenceImages", [])),
                           "referenceImages_sha256": [sha256_bytes(x.encode()) for x in v.get("referenceImages", [])]})
                          for k, v in t.items()}})
        w, h = int(t["width"]), int(t["height"])
        if self.mode == "wrong_size":
            w, h = w + 16, h
        data = self._image(body, w, h)
        if self.mode == "invalid_bytes":
            data = b"\x89PNG\r\n\x1a\nGARBAGE"
        item: dict = {"taskType": "imageInference", "taskUUID": uid, "imageUUID": "fx-" + uid[:8], "status": "success", "seed": 0}
        if self.cost is not None:
            item["cost"] = self.cost
        if self.mode == "url_only":
            atomic_write_bytes(self.dir / f"img_{uid}.png", data)
            item["imageURL"] = f"https://im.runware.ai/fx/{uid}.png"
        elif self.mode == "data_uri":
            item["imageDataURI"] = "data:image/png;base64," + base64.b64encode(data).decode()
        elif self.mode != "no_image":
            item["imageBase64Data"] = base64.b64encode(data).decode()
        raw = json.dumps({"data": [item]}).encode()
        atomic_write_bytes(self.dir / f"resp_{uid}.json", raw)
        if self.mode == "accept_then_drop":
            raise Blocked("TRANSPORT_UNCERTAIN", "fixture: provider accepted and billed, response lost")
        return raw
