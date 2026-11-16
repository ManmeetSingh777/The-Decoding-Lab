"""Vision providers: an offline MOCK with a durable simulated remote, and a real HTTP adapter shape.

The mock is for engineering drills only (crash/resume, omission, subsampling, hash
mismatch, summary-only, image limits). Its "observations" are crude pixel statistics
explicitly labelled MOCK; they are never artistic understanding, and the runner refuses to
run the mock on real (non-synthetic) source films.
"""
from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from PIL import Image, ImageStat

from ..util import Blocked, atomic_write_json, read_json, sha256_bytes, now_iso
from ..providers.authorization import AuthorizationRegistry


@dataclass
class VisionCapabilities:
    provider_id: str
    model_id: str
    max_images_per_request: int
    max_image_side: int
    supports_image_id_mapping: bool
    supports_task_query: bool
    cost_per_image_usd: float | None
    verified: bool
    source: str  # where the limits come from (doc URL + date, or FIXTURE)


class VisionProvider(Protocol):
    kind: str  # "MOCK" | "REAL"
    caps: VisionCapabilities

    def submit(self, task_id: str, request: dict, images: list[bytes]) -> dict: ...
    def query(self, task_id: str) -> dict | None: ...   # None => cannot determine


class MockVisionProvider:
    """Deterministic offline simulator with a durable 'remote' (survives process kills)."""

    kind = "MOCK"

    def __init__(self, remote_dir: str | Path, *, mode: str = "correct", max_images: int = 12,
                 queryable: bool = True):
        self.remote = Path(remote_dir)
        self.remote.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.queryable = queryable
        self.caps = VisionCapabilities("mock-vision", "mock-vlm-1", max_images, 4096, True, queryable, 0.0, True,
                                       "FIXTURE_ONLY")

    # simulated remote billing ledger ------------------------------------------------
    def _rp(self, task_id: str) -> Path:
        return self.remote / f"{task_id}.json"

    def billed_count(self) -> int:
        return sum(1 for p in self.remote.glob("*.json") if read_json(p).get("billed"))

    def submissions(self, task_id: str) -> int:
        p = self._rp(task_id)
        return read_json(p).get("submissions", 0) if p.exists() else 0

    def submit(self, task_id: str, request: dict, images: list[bytes]) -> dict:
        p = self._rp(task_id)
        if p.exists():  # idempotent: same task id never billed twice
            rec = read_json(p)
            rec["submissions"] = rec.get("submissions", 1) + 1
            atomic_write_json(p, rec)
            return rec["response"]
        if len(images) > self.caps.max_images_per_request:
            raise Blocked("PROVIDER_IMAGE_LIMIT", f"{len(images)} > {self.caps.max_images_per_request}")
        resp = self._respond(request, images)
        atomic_write_json(p, {"task_id": task_id, "billed": True, "submissions": 1, "response": resp, "at": now_iso()})
        return resp

    def query(self, task_id: str) -> dict | None:
        if not self.queryable:
            return None
        p = self._rp(task_id)
        if not p.exists():
            return {"status": "NOT_FOUND"}
        return {"status": "COMPLETED", "response": read_json(p)["response"]}

    def _respond(self, request: dict, images: list[bytes]) -> dict:
        targets = request["target_frames"]
        obs: list[dict] = []
        prev_mean: list | None = None
        for i, t in enumerate(targets):
            img_bytes = images[i]
            im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            mean = [round(x, 2) for x in ImageStat.Stat(im).mean]
            delta: float | None = None if prev_mean is None else round(sum(abs(a - b) for a, b in zip(mean, prev_mean)), 2)
            changed = [] if (delta is not None and delta < 0.5) else [
                {"kind": "OBSERVED_DIFF", "what": f"MOCK mean-colour shift {delta} relative to prior frame"}]
            obs.append({
                "frame_id": t["frame_id"], "source_sha": t["frame_id"].split(":")[0], "pts_time": t["pts_time"],
                "request_id": request["packet_id"], "submitted_image_sha": sha256_bytes(img_bytes),
                "active_question_ids": [q.get("question_id") for q in request["active_questions"]],
                "scene_and_world_state": f"MOCK_ONLY frame {t['frame_id']} mean RGB {mean}",
                "actually_visible_actor_and_object_ids": [],
                "focal_whole_artwork_state": f"MOCK_ONLY: pixel statistics for frame {t['order']} compared to neighbouring frames; not artistic vision",
                "visible_design_relations": [], "character_face_limb_contact_state": [],
                "visible_layer_depth_attention_state": "UNKNOWN (mock)", "changed_since_prior_frame": changed,
                "no_significant_change_reason": None if changed else f"MOCK: mean colour unchanged vs prior frame (delta {delta})",
                "simultaneous_event_links": [], "camera_vs_actor_vs_drawing_state": "UNKNOWN",
                "material_finish_or_colour_change": [], "native_detail_followups": [],
                "source_fact_statements": [f"MOCK_ONLY measured mean RGB {mean} compared with the prior frame (delta {delta})"],
                "hypothesis_or_uncertainty": ["MOCK provider: no perception claims"], "confidence_limitations": ["MOCK"],
                "persistent_state_ids": [], "unexplained_phenomena": [],
            })
            prev_mean = mean
        resp: Any = {"receipt": {"images_received": len(images)}, "frame_observations": obs,
                "packet_transition_graph": {"edges": [[obs[i]["frame_id"], obs[i + 1]["frame_id"]] for i in range(len(obs) - 1)]},
                "boundary_state": {"scene_world": "MOCK", "active_objects": [], "open_events": [], "attention": "UNKNOWN",
                                   "hypotheses": [], "open_questions": [q.get("question_id") for q in request["active_questions"]],
                                   "last_frame_index": None},
                "reconciled_events": [{"event_id": e.get("event_id"), "resolution": "CONTINUES"}
                                      for e in (request.get("prior_boundary_state") or {}).get("open_events", [])],
                "question_update": None, "provider_kind": "MOCK"}
        m = self.mode
        if m == "omit_one" and len(obs) > 1:
            resp["frame_observations"] = obs[:2] + obs[3:] if len(obs) > 2 else obs[:1]
        elif m == "summary_only":
            resp = {"receipt": {"images_received": len(images)}, "summary": "colourful and dynamic scene"}
        elif m == "subsample":
            resp["frame_observations"] = obs[::10] or obs[:1]
        elif m == "hash_mismatch":
            resp["frame_observations"][0]["submitted_image_sha"] = "0" * 64
        elif m == "vague":
            for o in resp["frame_observations"]:
                o["focal_whole_artwork_state"] = "colourful and dynamic"
                o["changed_since_prior_frame"] = [{"kind": "OBSERVED_DIFF", "what": "dynamic"}]
        elif m == "received_fewer":
            resp["receipt"]["images_received"] = max(1, len(images) - 1)
        elif m == "corrupt_json":
            resp = "{not json"
        elif m == "no_reconcile":
            resp["reconciled_events"] = []
        return resp


class HttpVisionAdapter:
    """Real-provider adapter shape. Refuses unless network + authorization + source-upload consent hold.

    No specific commercial VLM is chosen in this build; `caps` must come from a dated,
    verified capability snapshot. Until then estimate() returns BLOCKED_FOR_PRICE_VERIFICATION.
    """

    kind = "REAL"

    def __init__(self, caps: VisionCapabilities, registry: AuthorizationRegistry, transport=None):
        self.caps = caps
        self.registry = registry
        self.transport = transport

    def build_payload(self, request: dict, images: list[bytes]) -> dict:
        return {"model": self.caps.model_id, "instructions": request["instructions"],
                "frames": [{"frame_id": t["frame_id"], "image_base64": base64.b64encode(b).decode()}
                           for t, b in zip(request["target_frames"] + request["context_frames"], images)],
                "questions": request["active_questions"], "prior_boundary_state": request["prior_boundary_state"]}

    def submit(self, task_id: str, request: dict, images: list[bytes]) -> dict:
        if not self.caps.verified:
            raise Blocked("PROVIDER_CAPABILITIES_UNVERIFIED")
        cost = None if self.caps.cost_per_image_usd is None else self.caps.cost_per_image_usd * len(images)
        source_shas = sorted({t["frame_id"].split(":")[0] for t in request["target_frames"]})
        self.registry.check(provider=self.caps.provider_id, model_id=self.caps.model_id, task="source_vision",
                            estimated_cost_usd=cost, source_shas=source_shas)
        if self.transport is None:
            raise Blocked("NO_TRANSPORT_CONFIGURED")
        raw = self.transport(self.build_payload(request, images), task_id)
        return json.loads(raw) if isinstance(raw, (str, bytes)) else raw

    def query(self, task_id: str) -> dict | None:
        return None  # unknown → runner records UNKNOWN_BILLING unless provider supports polling


def estimate_vision_cost(caps: VisionCapabilities | None, frame_count: int, context_per_packet: int = 2,
                         packet_size: int = 8) -> dict:
    if caps is None or caps.cost_per_image_usd is None or not caps.verified:
        return {"status": "BLOCKED_FOR_PRICE_VERIFICATION", "frames": frame_count,
                "note": "No verified vision provider price/limits; refusing to guess a cost."}
    packets = -(-frame_count // packet_size)
    images = frame_count + packets * context_per_packet
    return {"status": "ESTIMATED", "frames": frame_count, "packets": packets, "images": images,
            "usd": round(images * caps.cost_per_image_usd, 4), "provider": caps.provider_id, "model": caps.model_id}
