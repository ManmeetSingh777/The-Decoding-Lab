"""StyleImageGateway — the SOLE image-provider entry point (spec 15 §1/§6, C14, B19, A53, ADD25-P01, ADD26-P01).

`submit(job)` accepts only a CompiledImageJob issued by StyleProgramCompiler. There is no
method that accepts prompt text. Every job is re-derived from its pinned inputs and must be
byte-identical (any appended adjective / dropped clause / swapped reference is refused).
Paid sends additionally need network + authorization + spend cap + (for source pixels)
upload consent, and a capability snapshot verified by a consented probe.
"""
from __future__ import annotations

import base64
import io
import json
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

from ..util import Blocked, atomic_write_bytes, atomic_write_json, canonical_json, now_iso, read_json, sha256_bytes
from ..artwork.raster import decode_raster
from ..compiler.compiler import CompiledImageJob, issued_by_compiler, payload_diff, recompile
from ..style.provenance import interface_two_audit
from ..vision.runner import maybe_crash
from .authorization import AuthorizationRegistry
from .capabilities import assert_paid_ready
from .runware import RunwareAdapter

JOB_STATES = ("PENDING", "IN_FLIGHT", "RESPONSE_SAVED", "COMMITTED", "UNKNOWN_BILLING", "FAILED")


class StyleImageGateway:
    def __init__(self, store, artifacts_dir: str | Path, adapter: RunwareAdapter, registry: AuthorizationRegistry):
        self.store = store
        self.art = Path(artifacts_dir)
        self.adapter = adapter
        self.registry = registry

    # -- the only public submission method ------------------------------------------------
    def submit(self, job: CompiledImageJob, *, task_category: str = "image_generation", probe: bool = False) -> dict:
        if not issued_by_compiler(job):
            raise Blocked("RAW_PROMPT_GATEWAY_BYPASS", "gateway accepts only issued CompiledImageJob objects")
        fresh = recompile(job)
        if fresh.logical_sha256 != job.logical_sha256 or fresh.logical_payload != job.logical_payload:
            raise Blocked("COMPILED_JOB_MUTATED", "payload differs from deterministic recompilation",
                          diff=payload_diff(fresh.logical_payload, job.logical_payload))
        if not job.baseline_only:
            audit = interface_two_audit(job.logical_payload, job.trace["field_ownership"], job.trace["segments"])
            if not audit["ok"]:
                raise Blocked("UNAUTHORIZED_STYLE_TEXT", str(audit["problems"][:3]))
        if self.adapter.kind == "REAL":
            if job.synthetic:
                raise Blocked("SYNTHETIC_SKILL_TO_REAL_PROVIDER", "fixture skills never reach a paid provider")
            origin = job.trace.get("skill_evidence_origin", "REAL_VLM")
            if getattr(self.adapter, "transport_kind", "NETWORK") == "NETWORK" and origin not in ("REAL_VLM", None) and not job.baseline_only:
                raise Blocked("SIMULATED_EVIDENCE_SKILL_TO_NETWORK", f"skill evidence origin {origin} cannot drive a paid call")
            assert_paid_ready(self.adapter.snapshot, probe=probe)
            est = self.adapter.snapshot.get("cost_per_image_usd")
            self._auth = self.registry.check(provider="runware", model_id=job.logical_payload["model"], task=task_category,
                                             estimated_cost_usd=est,
                                             source_shas=job.trace.get("requires_source_upload_consent_for") or None)
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

    def _run(self, job: CompiledImageJob) -> dict:
        key = job.logical_sha256
        d = self.art / "provider" / job.job_id
        row = self._row(key)
        if row and row[0] == "COMMITTED":
            return read_json(d / "result.json")
        if row and row[0] == "UNKNOWN_BILLING":
            raise Blocked("UNKNOWN_BILLING", "pending provider task needs human reconciliation")
        task_uuid = row[1] if row and row[1] else str(uuid.uuid5(uuid.NAMESPACE_URL, key))
        body = self.adapter.build_body(job.logical_payload, task_uuid)
        resp = None
        if row is None or row[0] == "PENDING":
            atomic_write_bytes(d / "request_body.json", body)
            self._set(key, "IN_FLIGHT", task_uuid=task_uuid, payload_sha=sha256_bytes(body), job_id=job.job_id)
            maybe_crash("gateway_after_inflight")
            resp = self.adapter.send(body)
            maybe_crash("gateway_after_send_before_save")
        elif row[0] == "IN_FLIGHT":
            try:
                resp = self.adapter.send(self.adapter.query_body(task_uuid))
                RunwareAdapter.parse_images(resp, task_uuid)
            except Blocked:
                self._set(key, "UNKNOWN_BILLING", error="cannot reconcile pending task")
                raise Blocked("UNKNOWN_BILLING", f"task {task_uuid} not reconcilable; refusing blind resubmit")
        if resp is not None:
            atomic_write_bytes(d / "response.json", resp)
            self._set(key, "RESPONSE_SAVED", response_path=str(d / "response.json"))
            maybe_crash("gateway_after_response_saved")
        resp = (d / "response.json").read_bytes()
        try:
            imgs = RunwareAdapter.parse_images(resp, task_uuid)
        except Blocked as b:
            self._set(key, "FAILED", error=b.code)
            raise
        outs = []
        for i, im in enumerate(imgs):
            if "bytes" not in im:
                self._set(key, "FAILED", error="PROVIDER_URL_NOT_FETCHED")
                raise Blocked("PROVIDER_URL_EXPIRED_OR_UNFETCHED", "URL outputs must be fetched immediately under authorization")
            try:
                ra = decode_raster(im["bytes"], asset_id=f"{job.job_id}_img{i}", owner=job.trace.get("brief_id", "baseline"),
                                   skill_version=job.trace.get("skill_hash", "BASELINE_ONLY"),
                                   expected_size=(job.logical_payload["width"], job.logical_payload["height"]))
            except Blocked as b:
                self._set(key, "FAILED", error=b.code)
                raise
            p = self.art / "images" / f"{ra.sha256}.png"
            atomic_write_bytes(p, im["bytes"])
            ra.path = str(p)
            outs.append({**ra.to_dict(), "imageUUID": im.get("imageUUID"), "provider_cost": im.get("cost")})
        cost = sum(float(o["provider_cost"] or 0) for o in outs) if all(o["provider_cost"] is not None for o in outs) else None
        result = {"job_id": job.job_id, "logical_sha256": key, "task_uuid": task_uuid, "request_body_sha256": sha256_bytes(body),
                  "adapter_kind": self.adapter.kind, "synthetic_skill": job.synthetic, "baseline_only": job.baseline_only,
                  "skill_hash": job.trace.get("skill_hash"), "selected_decisions": job.trace.get("selected_decisions"),
                  "clause_ids": job.trace.get("clause_ids"), "reference_shas": [r[1] for r in job.reference_images],
                  "outputs": outs, "cost_usd": cost, "cost_status": "REPORTED" if cost is not None else "UNKNOWN",
                  "label": ("OFFLINE_FIXTURE_NOT_LEARNED_ART" if self.adapter.kind != "REAL" else
                            "REAL_PROVIDER_OUTPUT" if getattr(self.adapter, "transport_kind", "NETWORK") == "NETWORK"
                            else "SIMULATED_TRANSPORT_FIXTURE_IMAGE"),
                  "committed_at": now_iso()}
        atomic_write_json(d / "result.json", result)
        self.store.put("GeneratedRaster", job.job_id, result)
        self._set(key, "COMMITTED", cost_usd=cost)
        if self.adapter.kind == "REAL" and cost is not None:
            self.registry.record_spend(self._auth.auth_id, cost)
        return result


class OfflineRecordingTransport:
    """No network. Records exact request bodies; returns a locally drawn, clearly labelled FIXTURE PNG.

    State persists on disk so getResponse reconciliation works across process kills.
    """

    def __init__(self, state_dir: str | Path, *, mode: str = "ok", queryable: bool = True):
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.queryable = queryable

    def sent_bodies(self) -> list[dict]:
        return [read_json(p) for p in sorted(self.dir.glob("req_*.json"))]

    def billed(self) -> int:
        return len(list(self.dir.glob("bill_*.json")))

    def __call__(self, body: bytes, headers: dict) -> bytes:
        tasks = json.loads(body)
        t = tasks[0]
        if t.get("taskType") == "getResponse":
            if not self.queryable:
                raise Blocked("PROVIDER_QUERY_UNSUPPORTED")
            p = self.dir / f"resp_{t['taskUUID']}.json"
            if not p.exists():
                return json.dumps({"errors": [{"code": "taskNotFound"}]}).encode()
            return p.read_bytes()
        uid = t["taskUUID"]
        resp_p = self.dir / f"resp_{uid}.json"
        if resp_p.exists():  # idempotent by taskUUID: never billed twice
            return resp_p.read_bytes()
        atomic_write_json(self.dir / f"req_{uid}.json", {"body_sha256": sha256_bytes(body), "task": {k: (v if k != "inputs" else
                          {"referenceImages_count": len(v.get("referenceImages", [])),
                           "referenceImages_sha256": [sha256_bytes(x.encode()) for x in v.get("referenceImages", [])]})
                          for k, v in t.items()}})
        atomic_write_json(self.dir / f"bill_{uid}.json", {"at": now_iso()})
        w, h = int(t["width"]), int(t["height"])
        if self.mode == "wrong_size":
            w, h = w + 16, h
        im = Image.new("RGB", (w, h), (int(sha256_bytes(body)[:2], 16), 90, 120))
        dr = ImageDraw.Draw(im)
        dr.rectangle([8, 8, w - 9, h - 9], outline=(255, 255, 255), width=3)
        dr.text((20, 20), "OFFLINE FIXTURE - NOT LEARNED ART", fill=(255, 255, 255))
        dr.text((20, 40), f"payload {sha256_bytes(body)[:16]}", fill=(255, 255, 255))
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        data = buf.getvalue()
        if self.mode == "invalid_bytes":
            data = b"\x89PNG\r\n\x1a\nGARBAGE"
        resp: dict
        if self.mode == "http_error":
            resp = {"errors": [{"code": "invalidModel", "message": "fixture provider error"}]}
        elif self.mode == "url_only":
            resp = {"data": [{"taskUUID": uid, "imageUUID": "fx-" + uid[:8], "imageURL": "https://expired.invalid/img.png", "cost": 0.0}]}
        elif self.mode == "no_image":
            resp = {"data": [{"taskUUID": uid}]}
        else:
            resp = {"data": [{"taskUUID": uid, "imageUUID": "fx-" + uid[:8], "imageBase64Data": base64.b64encode(data).decode(),
                              "cost": 0.0, "seed": 0}]}
        raw = json.dumps(resp).encode()
        atomic_write_bytes(resp_p, raw)
        return raw
