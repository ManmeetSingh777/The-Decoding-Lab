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

from ..util import Blocked, atomic_write_json, now_iso, read_json
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
    def _authorize(self, images: list[tuple[str, bytes, int, int]], source_shas: list[str], task: str) -> float:
        price = PRICE_TABLE_UNVERIFIED.get(self.caps.model_id) if self.caps.cost_per_image_usd is not None else None
        est = None
        if price:
            tok = sum(image_tokens_estimate(w, h) for _, _, w, h in images) + 4000
            est = tok * price["input_per_mtok"] / 1e6 + self.max_output_tokens * price["output_per_mtok"] / 1e6
        self.registry.check(provider=PROVIDER_ID, model_id=self.caps.model_id, task=task, estimated_cost_usd=est,
                            source_shas=source_shas or None)
        return est or 0.0

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
    def parse_json_text(message: Any) -> Any:
        stop = getattr(message, "stop_reason", None) if not isinstance(message, dict) else message.get("stop_reason")
        if stop == "refusal":
            raise Blocked("PROVIDER_REFUSAL", "model declined; packet stays NEEDS_REINSPECTION")
        blocks = message.content if not isinstance(message, dict) else message["content"]
        text = "".join((b.text if not isinstance(b, dict) else b.get("text", "")) for b in blocks
                       if (getattr(b, "type", None) if not isinstance(b, dict) else b.get("type")) == "text")
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if m:
            text = m.group(1)
        return json.loads(text)

    # -- generic JSON request with reconciliation --------------------------------------------------------
    def _map_path(self, task_id: str) -> Path:
        return self.state / f"task_{task_id}.json"

    def request_json(self, task_id: str, kind: str, system: str, user_text: str, labelled_images: list[tuple[str, bytes, int, int]],
                     *, source_shas: list[str], auth_task: str = "source_vision") -> dict:
        if kind not in REQUEST_KINDS:
            raise Blocked("UNKNOWN_REQUEST_KIND", kind)
        if len(labelled_images) > self.caps.max_images_per_request:
            raise Blocked("PROVIDER_IMAGE_LIMIT", f"{len(labelled_images)} > {self.caps.max_images_per_request}")
        mp = self._map_path(task_id)
        if mp.exists():                       # already submitted: never resubmit, reconcile instead
            return self._await(task_id)
        est = self._authorize(labelled_images, source_shas, auth_task)
        params = self.serialize(kind, system, user_text, [(l, b) for l, b, _, _ in labelled_images], self.caps.model_id,
                                self.max_output_tokens)
        batch = self.client().messages.batches.create(requests=[{"custom_id": task_id, "params": params}])
        atomic_write_json(mp, {"task_id": task_id, "batch_id": batch.id, "kind": kind, "submitted_at": now_iso(),
                               "estimated_cost_usd": est, "images": len(labelled_images), "transport_kind": self.transport_kind,
                               "auth_task": auth_task})
        return self._await(task_id)

    def _await(self, task_id: str) -> dict:
        info = read_json(self._map_path(task_id))
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
            if r.result.type != "succeeded":
                raise Blocked("PROVIDER_EXECUTION", f"batch result {r.result.type}")
            parsed = self.parse_json_text(r.result.message)
            usage = getattr(r.result.message, "usage", None)
            if not info.get("spend_recorded"):
                price = PRICE_TABLE_UNVERIFIED.get(self.caps.model_id)
                it, ot = getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)
                actual = (it * price["input_per_mtok"] + ot * price["output_per_mtok"]) / 1e6 if price and it is not None and ot is not None                     else info.get("estimated_cost_usd") or 0.0
                a = self.registry.find(PROVIDER_ID, self.caps.model_id, info.get("auth_task", "source_vision"))
                if a is not None:
                    self.registry.record_spend(a.auth_id, actual)
                info.update(spend_recorded=True, cost_usd=actual, cost_basis="usage_tokens×unverified_price" if price else "estimate")
                atomic_write_json(self._map_path(task_id), info)
            if isinstance(parsed, dict):
                parsed.setdefault("receipt", {})
                parsed["receipt"].update({"images_sent": info["images"], "batch_id": info["batch_id"],
                                          "input_tokens": getattr(usage, "input_tokens", None),
                                          "output_tokens": getattr(usage, "output_tokens", None),
                                          "transport_kind": self.transport_kind})
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
        user = json.dumps({k: request[k] for k in ("packet_id", "target_frames", "context_frames", "active_questions", "prior_boundary_state",
                                                   "required_output_schema")})
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
        self.registry.check(provider=PROVIDER_ID, model_id=self.caps.model_id, task="capability_probe", estimated_cost_usd=0.0)
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
