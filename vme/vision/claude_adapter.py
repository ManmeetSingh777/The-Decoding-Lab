"""Concrete REAL vision provider: Claude Messages API via Message Batches (official `anthropic` SDK).

Why batches: each request carries a `custom_id` (= our idempotent task id), results are retrievable
later by batch id, so a process killed after submission reconciles instead of re-billing.
Serialization: each frame image is preceded by a text label `FRAME <frame_id> [TARGET|CONTEXT]` so
the model can map images to frame ids; the response must be strict JSON (validated by the runner).

The client is injected. Production builds `anthropic.Anthropic()` lazily ONLY after the authorization
check passes. Offline drills inject a simulated client with the same `.messages.batches` / `.models`
surface (vme/testing) — the adapter code below is identical in both cases.
"""
from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path
from typing import Any, Callable

from ..util import Blocked, atomic_write_json, digest, now_iso, read_json, sha256_bytes, sha256_file
from ..providers.ids import validate_custom_id
from .runner import maybe_crash
from ..providers.authorization import AuthorizationRegistry
from .providers import VisionCapabilities

PROVIDER_ID = "anthropic-claude"
DEFAULT_MODEL = "claude-opus-5-5"
# Pricing as listed in the claude-api skill model table (cached 2026-11-03): $4 / $20 per MTok for claude-opus-5-5.
# Recorded as UNVERIFIED until the user confirms; batch discount is NOT assumed.
PRICE_TABLE_UNVERIFIED: dict[str, dict[str, Any]] = {"claude-opus-5-5": {"input_per_mtok": 4.0, "output_per_mtok": 20.0, "source": "claude-api skill table cached 2026-11-03"}}
REQUEST_KINDS = ("frame_packet", "window_rationale", "question_answer", "native_detail")


def image_tokens_estimate(w: int, h: int) -> int:
    """Conservative estimate (~w*h/750 tokens per image), used only for a pre-call spend ceiling check."""
    return max(1, (w * h) // 750)


class ClaudeBatchVisionAdapter:
    kind = "REAL"

    def __init__(self, caps: VisionCapabilities, registry: AuthorizationRegistry, state_dir: str | Path, *,
                 client_factory: Callable[[], Any], transport_kind: str = "NETWORK", poll_seconds: float = 0.0,
                 poll_interval: float = 5.0, max_output_tokens: int = 16000):
        self.caps = caps
        self.registry = registry
        self.state = Path(state_dir)
        self.state.mkdir(parents=True, exist_ok=True)
        self.client_factory = client_factory
        self.transport_kind = transport_kind          # NETWORK | SIMULATED (labelled fixture)
        self.poll_seconds = poll_seconds
        self.poll_interval = poll_interval
        self.max_output_tokens = max_output_tokens
        self._client = None

    # -- authorization + spend ---------------------------------------------------------------
    def _estimate(self, images: list[tuple[str, bytes, int, int]]) -> float | None:
        price = PRICE_TABLE_UNVERIFIED.get(self.caps.model_id) if self.caps.cost_per_image_usd is not None else None
        if not price:
            return None
        tok = sum(image_tokens_estimate(w, h) for _, _, w, h in images) + 4000
        return tok * price["input_per_mtok"] / 1e6 + self.max_output_tokens * price["output_per_mtok"] / 1e6

    def client(self):
        if self._client is None:
            self._client = self.client_factory()
        return self._client

    # -- serialization -------------------------------------------------------------------------------
    @staticmethod
    def serialize(kind: str, system: str, user_text: str, labelled_images: list[tuple[str, bytes]], model: str, max_tokens: int) -> dict:
        content: list[dict] = [{"type": "text", "text": user_text}]
        for label, png in labelled_images:
            content.append({"type": "text", "text": label})
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.b64encode(png).decode()}})
        return {"model": model, "max_tokens": max_tokens, "output_config": {"effort": "high"},
                "system": f"VME_REQUEST_KIND: {kind}\n{system}", "messages": [{"role": "user", "content": content}]}

    @staticmethod
    def validate_params(params: dict, *, max_images: int) -> None:
        """Local request-schema check before any create (R03): fields the Messages API accepts, sane types, image count."""
        allowed = {"model", "max_tokens", "messages", "system", "output_config", "temperature", "thinking", "metadata", "stop_sequences"}
        extra = set(params) - allowed
        if extra:
            raise Blocked("REQUEST_SCHEMA_INVALID", f"unknown params {sorted(extra)}")
        if not isinstance(params.get("model"), str) or not isinstance(params.get("max_tokens"), int) or params["max_tokens"] < 1:
            raise Blocked("REQUEST_SCHEMA_INVALID", "model/max_tokens")
        msgs = params.get("messages")
        if not isinstance(msgs, list) or not msgs or msgs[0].get("role") != "user":
            raise Blocked("REQUEST_SCHEMA_INVALID", "messages")
        n_img = sum(1 for m in msgs for c in m["content"] if c.get("type") == "image")
        if n_img > max_images:
            raise Blocked("PROVIDER_IMAGE_LIMIT", f"{n_img} > {max_images}")
        for m in msgs:
            for c in m["content"]:
                if c.get("type") == "image" and (c["source"].get("type") != "base64" or c["source"].get("media_type") != "image/png"):
                    raise Blocked("REQUEST_SCHEMA_INVALID", "image source")

    @staticmethod
    def parse_json_text(message: Any) -> Any:
        """Strict parse: refusal, max_tokens truncation, empty or non-JSON output are named failures (never invented content)."""
        stop = getattr(message, "stop_reason", None) if not isinstance(message, dict) else message.get("stop_reason")
        if stop == "refusal":
            raise Blocked("PROVIDER_REFUSAL", "model declined; packet stays NEEDS_REINSPECTION")
        if stop == "max_tokens":
            raise Blocked("PROVIDER_OUTPUT_TRUNCATED", "max_tokens reached; output incomplete, re-run as smaller packets")
        blocks = message.content if not isinstance(message, dict) else message["content"]
        text = "".join((b.text if not isinstance(b, dict) else b.get("text", "")) for b in blocks
                       if (getattr(b, "type", None) if not isinstance(b, dict) else b.get("type")) == "text")
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if m:
            text = m.group(1)
        if not text.strip():
            raise Blocked("PROVIDER_NON_JSON", "empty text output")
        try:
            return json.loads(text)
        except ValueError as e:
            raise Blocked("PROVIDER_NON_JSON", f"unparseable JSON output ({e})")

    # -- durable intent journal + reconciliation (R01/R02/R07) --------------------------------------------
    def _map_path(self, task_id: str) -> Path:
        return self.state / f"task_{task_id}.json"

    def _jw(self, task_id: str, info: dict) -> None:
        atomic_write_json(self._map_path(task_id), info)

    def request_json(self, task_id: str, kind: str, system: str, user_text: str, labelled_images: list[tuple[str, bytes, int, int]],
                     *, source_shas: list[str], auth_task: str = "source_vision") -> dict:
        if kind not in REQUEST_KINDS:
            raise Blocked("UNKNOWN_REQUEST_KIND", kind)
        validate_custom_id(task_id)
        if len(labelled_images) > self.caps.max_images_per_request:
            raise Blocked("PROVIDER_IMAGE_LIMIT", f"{len(labelled_images)} > {self.caps.max_images_per_request}")
        mp = self._map_path(task_id)
        if mp.exists():                       # journaled: never resubmit, reconcile instead
            info = read_json(mp)
            st = info.get("state", "SUBMITTED" if info.get("batch_id") else "SUBMISSION_ATTEMPTED")
            if st == "SUBMISSION_ATTEMPTED":   # crashed between intent and saving the batch id
                info.update(state="SUBMISSION_UNCERTAIN", uncertain_since=now_iso())
                self._jw(task_id, info)
                self._liability(info, "accepted-before-batch-id ambiguity")
                st = "SUBMISSION_UNCERTAIN"
            if st == "SUBMISSION_UNCERTAIN":
                raise Blocked("SUBMISSION_UNCERTAIN", f"{task_id}: create() may have been accepted; human reconciliation required "
                                                      "(custom_id is not an across-batch idempotency key)", task_id=task_id)
            if st in ("REJECTED", "RECONCILED_NOT_SUBMITTED"):
                mp.unlink()
            else:
                return self._await(task_id)
        params = self.serialize(kind, system, user_text, [(l, b) for l, b, _, _ in labelled_images], self.caps.model_id,
                                self.max_output_tokens)
        self.validate_params(params, max_images=self.caps.max_images_per_request)
        est = self._estimate(labelled_images)
        a, res = self.registry.reserve(provider=PROVIDER_ID, model_id=self.caps.model_id, task=auth_task, estimated_cost_usd=est,
                                       logical_job_id=task_id, source_shas=source_shas or None)
        info = {"task_id": task_id, "state": "SUBMISSION_ATTEMPTED", "kind": kind, "request_sha256": digest(params),
                "image_shas": [sha256_bytes(b) for _, b, _, _ in labelled_images], "images": len(labelled_images),
                "estimated_cost_usd": est, "auth_id": a.auth_id, "authorization_version": a.issued_at,
                "consent_scope": sorted(source_shas or []), "reservation_id": res["reservation_id"],
                "transport_kind": self.transport_kind, "auth_task": auth_task, "attempted_at": now_iso(), "batch_id": None}
        self._jw(task_id, info)                         # durable intent BEFORE create
        maybe_crash("vision_after_intent_before_create")
        try:
            batch = self.client().messages.batches.create(requests=[{"custom_id": task_id, "params": params}])
        except Blocked:
            raise
        except Exception as e:                           # SDK / transport error
            status = getattr(e, "status_code", None)
            if isinstance(status, int) and 400 <= status < 500 and status not in (408, 409):
                info.update(state="REJECTED", error=f"HTTP {status}: {str(e)[:200]}")
                self._jw(task_id, info)
                self.registry.ledger.release(res["reservation_id"], reason=f"HTTP {status} rejection")
                raise Blocked("PROVIDER_REJECTED_REQUEST", f"HTTP {status}")
            info.update(state="SUBMISSION_UNCERTAIN", error=f"{type(e).__name__}: {str(e)[:200]}")
            self._jw(task_id, info)
            self._liability(info, "create() raised after possible acceptance")
            raise Blocked("SUBMISSION_UNCERTAIN", f"{task_id}: create() raised {type(e).__name__}; acceptance unknown", task_id=task_id)
        maybe_crash("vision_after_create_before_save")
        info.update(state="SUBMITTED", batch_id=batch.id, submitted_at=now_iso())
        self._jw(task_id, info)
        return self._await(task_id)

    def _liability(self, info: dict, why: str) -> None:
        if info.get("reservation_id"):
            self.registry.ledger.mark_liability(info["reservation_id"], reason=why)

    def reconcile_uncertain(self, task_id: str, *, by: str, batch_id: str | None = None, not_submitted_evidence: str | None = None) -> dict:
        """Human-only resolution of SUBMISSION_UNCERTAIN: attach the batch id found in the console, or confirm no batch exists."""
        if not by or by.lower() in ("agent", "claude", "codex", "model", "auto"):
            raise Blocked("HUMAN_ISSUER_REQUIRED")
        info = read_json(self._map_path(task_id))
        if info.get("state") not in ("SUBMISSION_UNCERTAIN", "SUBMISSION_ATTEMPTED"):
            raise Blocked("NOT_UNCERTAIN", info.get("state", "?"))
        if batch_id:
            info.update(state="SUBMITTED", batch_id=batch_id, reconciled_by=by, reconciled_at=now_iso())
        elif not_submitted_evidence:
            info.update(state="RECONCILED_NOT_SUBMITTED", reconciled_by=by, evidence=not_submitted_evidence, reconciled_at=now_iso())
            if info.get("reservation_id"):
                self.registry.ledger.release(info["reservation_id"], reason=f"human {by}: {not_submitted_evidence}")
        else:
            raise Blocked("RECONCILIATION_EVIDENCE_REQUIRED")
        self._jw(task_id, info)
        return info

    def _await(self, task_id: str) -> dict:
        info = read_json(self._map_path(task_id))
        if info.get("state") == "RESULT_INVALID":
            raise Blocked(info["error_code"], info.get("error", ""))
        deadline = time.time() + self.poll_seconds
        while True:
            b = self.client().messages.batches.retrieve(info["batch_id"])
            if b.processing_status == "ended":
                break
            if time.time() >= deadline:
                raise Blocked("PROVIDER_PENDING", f"batch {info['batch_id']} still {b.processing_status}")
            time.sleep(self.poll_interval)
        for r in self.client().messages.batches.results(info["batch_id"]):
            if r.custom_id != task_id:
                continue
            rtype = r.result.type
            if rtype != "succeeded":            # errored / expired / canceled: not billed per batch docs → release
                info.update(state="RESULT_" + rtype.upper(), error=str(getattr(r.result, "error", ""))[:300])
                self._jw(task_id, info)
                if info.get("reservation_id"):
                    self.registry.ledger.release(info["reservation_id"], reason=f"batch result {rtype}")
                raise Blocked("PROVIDER_EXECUTION", f"batch result {rtype}")
            msg = r.result.message
            usage = getattr(msg, "usage", None)
            raw: dict[str, Any] = {"stop_reason": getattr(msg, "stop_reason", None), "model": getattr(msg, "model", None),
                   "content": [{"type": getattr(c, "type", None), "text": getattr(c, "text", None)} for c in msg.content],
                   "usage": {"input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None)}}
            rp = self.state / f"raw_{task_id}.json"
            atomic_write_json(rp, raw)               # raw response stored BEFORE parsing
            price = PRICE_TABLE_UNVERIFIED.get(self.caps.model_id)
            it, ot = raw["usage"]["input_tokens"], raw["usage"]["output_tokens"]
            actual = (it * price["input_per_mtok"] + ot * price["output_per_mtok"]) / 1e6 if price and it is not None and ot is not None else None
            if info.get("reservation_id") and not info.get("settled"):
                self.registry.ledger.settle(info["reservation_id"], actual_cost=actual,
                                            receipt={"batch_id": info["batch_id"], "custom_id": task_id, "raw_sha256": sha256_file(rp)})
                info.update(settled=True, cost_usd=actual, cost_basis="usage_tokens x unverified_price" if actual is not None else "UNKNOWN")
            info.update(state="RESULT_RECEIVED", raw_path=str(rp), raw_sha256=sha256_file(rp))
            self._jw(task_id, info)
            try:
                parsed = self.parse_json_text(msg)
            except Blocked as e:
                info.update(state="RESULT_INVALID", error_code=e.code, error=e.detail)
                self._jw(task_id, info)
                raise
            if isinstance(parsed, dict):
                parsed.setdefault("receipt", {})
                parsed["receipt"].update({"images_sent": info["images"], "batch_id": info["batch_id"], "custom_id": task_id,
                                          "input_tokens": it, "output_tokens": ot, "raw_sha256": info["raw_sha256"],
                                          "request_sha256": info.get("request_sha256"), "transport_kind": self.transport_kind})
            return parsed
        raise Blocked("PROVIDER_RESULT_MISSING", task_id)

    # -- VisionProvider protocol (PacketRunner) ------------------------------------------------------
    def submit(self, task_id: str, request: dict, images: list[bytes]) -> dict:
        from PIL import Image
        import io
        frames = request["target_frames"] + request["context_frames"]
        labelled = []
        for f, b in zip(frames, images):
            im = Image.open(io.BytesIO(b))
            role = "TARGET" if f in request["target_frames"] else "CONTEXT"
            labelled.append((f"FRAME {f['frame_id']} [{role}] image_sha={f['image_sha']}", b, im.width, im.height))
        source_shas = sorted({request["film_sha256"]}) if request.get("film_sha256") else []
        user = json.dumps({k: request[k] for k in ("packet_id", "protocol", "binding", "target_frames", "context_frames", "active_questions",
                                                   "prior_boundary_state", "required_output_schema") if k in request})
        resp = self.request_json(task_id, "frame_packet", request["instructions"], user, labelled, source_shas=source_shas)
        if isinstance(resp, dict):
            resp.setdefault("receipt", {})["images_received"] = resp["receipt"].get("images_sent")
        return resp

    def query(self, task_id: str) -> dict | None:
        if not self._map_path(task_id).exists():
            return {"status": "NOT_FOUND"}
        try:
            return {"status": "COMPLETED", "response": self._await(task_id)}
        except Blocked as b:
            if b.code == "PROVIDER_PENDING":
                return {"status": "PENDING"}
            raise

    def discover(self) -> dict:
        """Live capability discovery via Models API (counts as an authorized capability_probe call)."""
        self.registry.check(provider=PROVIDER_ID, model_id=self.caps.model_id, task="capability_probe", estimated_cost_usd=0.0)  # models.retrieve is not billed
        m = self.client().models.retrieve(self.caps.model_id)
        return {"model": getattr(m, "id", self.caps.model_id), "max_input_tokens": getattr(m, "max_input_tokens", None),
                "max_tokens": getattr(m, "max_tokens", None), "capabilities": getattr(m, "capabilities", None), "at": now_iso()}


def default_caps(model_id: str = DEFAULT_MODEL, *, max_images: int = 20, verified: bool = False) -> VisionCapabilities:
    """max_images is a conservative per-request planning limit (not a documented maximum); verified=False until discovery."""
    return VisionCapabilities(PROVIDER_ID, model_id, max_images, 1568, True, True,
                              0.0 if model_id in PRICE_TABLE_UNVERIFIED else None, verified,
                              "claude-api skill model table (cached 2026-11-03); Models API discovery pending")


def production_client_factory():
    import anthropic  # official SDK; credentials resolved by the SDK (ANTHROPIC_API_KEY or `ant auth login` profile)
    return anthropic.Anthropic()
