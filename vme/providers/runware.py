"""Runware imageInference adapter (spec 15 §5, 19). Reachable ONLY from StyleImageGateway.

The adapter turns an issued job's logical payload into the exact HTTP task body and
decodes responses. The API key is read from `RUNWARE_API_KEY` at send time only and is
never stored, logged or exported. Transport is injectable: the offline build uses a
recording transport that never touches the network.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
from typing import Callable

from ..util import Blocked, canonical_json, sha256_bytes

Transport = Callable[[bytes, dict], bytes]   # (body_bytes, headers_without_secret) -> response bytes


def http_transport(api_base: str) -> Transport:
    def send(body: bytes, headers: dict) -> bytes:
        key = os.environ.get("RUNWARE_API_KEY")
        if not key:
            raise Blocked("RUNWARE_API_KEY_MISSING")
        req = urllib.request.Request(api_base, data=body, method="POST",
                                     headers={**headers, "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (only after authorization checks)
            return r.read()
    return send


class RunwareAdapter:
    provider_id = "runware"

    def __init__(self, snapshot: dict, transport: Transport, *, kind: str = "REAL", transport_kind: str = "NETWORK"):
        self.snapshot = snapshot
        self.transport = transport
        self.kind = kind  # "REAL" (authorization-gated path) or "OFFLINE_RECORDING"
        self.transport_kind = transport_kind  # NETWORK | SIMULATED (labelled fixture transport behind the REAL path)

    def build_body(self, logical_payload: dict, task_uuid: str) -> bytes:
        task = dict(logical_payload)
        task["taskUUID"] = task_uuid
        return canonical_json([task]).encode("utf-8")

    def query_body(self, task_uuid: str) -> bytes:
        return canonical_json([{"taskType": "getResponse", "taskUUID": task_uuid}]).encode("utf-8")

    def send(self, body: bytes) -> bytes:
        return self.transport(body, {"X-VME-Body-SHA256": sha256_bytes(body)})

    @staticmethod
    def parse_images(resp_bytes: bytes, task_uuid: str) -> list[dict]:
        try:
            resp = json.loads(resp_bytes)
        except (ValueError, TypeError):
            raise Blocked("PROVIDER_EXECUTION", "response is not JSON")
        if resp.get("errors"):
            raise Blocked("PROVIDER_EXECUTION", str(resp["errors"])[:300])
        out = []
        for d in resp.get("data", []):
            if d.get("taskUUID") != task_uuid:
                continue
            if "imageBase64Data" in d:
                try:
                    b = base64.b64decode(d["imageBase64Data"], validate=True)
                except ValueError:
                    raise Blocked("PROVIDER_EXECUTION", "invalid base64 image data")
                out.append({"bytes": b, "imageUUID": d.get("imageUUID"), "cost": d.get("cost"), "seed": d.get("seed")})
            elif "imageURL" in d:
                out.append({"url": d["imageURL"], "imageUUID": d.get("imageUUID"), "cost": d.get("cost"), "seed": d.get("seed")})
        if not out:
            raise Blocked("PROVIDER_NO_IMAGE", "HTTP success without image data")
        return out
