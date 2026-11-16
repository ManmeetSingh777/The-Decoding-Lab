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
import re
import urllib.error
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
        try:
            with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (only after authorization checks)
                return r.read()
        except urllib.error.HTTPError as e:     # provider answered: body carries the documented `errors` list
            if 400 <= e.code < 500 and e.code not in (408, 409):
                raise Blocked("PROVIDER_REJECTED", f"HTTP {e.code}", http_status=e.code, body=e.read()[:2000].decode("utf-8", "replace"))
            raise Blocked("TRANSPORT_UNCERTAIN", f"HTTP {e.code}: acceptance unknown")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise Blocked("TRANSPORT_UNCERTAIN", f"{type(e).__name__}: request may or may not have been accepted")
    return send


class RunwareAdapter:
    provider_id = "runware"

    def __init__(self, snapshot: dict, transport: Transport, *, kind: str = "REAL", transport_kind: str = "NETWORK",
                 fetch_url=None, poll_interval: float = 2.0, poll_deadline_s: float = 0.0):
        self.snapshot = snapshot
        self.fetch_url = fetch_url if fetch_url is not None else (
            https_image_fetcher(snapshot.get("allowed_image_hosts", [])) if transport_kind == "NETWORK" else None)
        self.poll_interval = poll_interval
        self.poll_deadline_s = poll_deadline_s
        self.transport = transport
        self.kind = kind  # "REAL" (authorization-gated path) or "OFFLINE_RECORDING"
        self.transport_kind = transport_kind  # NETWORK | SIMULATED (labelled fixture transport behind the REAL path)

    def build_body(self, logical_payload: dict, task_uuid: str) -> bytes:
        from .ids import validate_uuid4
        validate_uuid4(task_uuid)
        task = dict(logical_payload)
        task["taskUUID"] = task_uuid
        return canonical_json([task]).encode("utf-8")

    def query_body(self, task_uuid: str) -> bytes:
        return canonical_json([{"taskType": "getResponse", "taskUUID": task_uuid}]).encode("utf-8")

    def send(self, body: bytes) -> bytes:
        return self.transport(body, {"X-VME-Body-SHA256": sha256_bytes(body)})

    # -- response classification (R05/R06) ------------------------------------------------------------
    @staticmethod
    def classify(resp_bytes: bytes, task_uuid: str) -> dict:
        """Classify an imageInference or getResponse reply for ONE taskUUID.

        Returns {"status": SUCCESS|PROCESSING|ERROR|NOT_FOUND|UNPARSEABLE, "items": [...], "error": ...}.
        Runware task polling (docs: models-api/task-polling) reports per-task `status` processing|success|error;
        errors arrive in a top-level `errors` list carrying the taskUUID and a code.
        """
        try:
            resp = json.loads(resp_bytes)
        except (ValueError, TypeError):
            return {"status": "UNPARSEABLE", "items": [], "error": "response is not JSON"}
        if not isinstance(resp, dict):
            return {"status": "UNPARSEABLE", "items": [], "error": "response is not an object"}
        errs = [e for e in (resp.get("errors") or []) if isinstance(e, dict) and e.get("taskUUID") in (None, task_uuid)]
        if errs:
            codes = " ".join(str(e.get("code", "")) for e in errs)
            if "notfound" in codes.lower().replace("_", ""):
                return {"status": "NOT_FOUND", "items": [], "error": errs}
            return {"status": "ERROR", "items": [], "error": errs}
        items = [d for d in (resp.get("data") or []) if isinstance(d, dict) and d.get("taskUUID") == task_uuid]
        if not items:
            return {"status": "UNPARSEABLE", "items": [], "error": "no data item for this taskUUID"}
        sts = {str(d.get("status", "success")).lower() for d in items}
        if "error" in sts:
            return {"status": "ERROR", "items": items, "error": [d for d in items if str(d.get("status")).lower() == "error"]}
        if "processing" in sts and not any(_has_image(d) for d in items):
            return {"status": "PROCESSING", "items": items, "error": None}
        return {"status": "SUCCESS", "items": items, "error": None}

    @staticmethod
    def decode_item(d: dict, *, fetch_url: "Callable[[str], tuple[bytes, str]] | None" = None) -> dict:
        """base64Data / dataURI decoded locally; URL fetched by the injected, host-restricted fetcher."""
        meta = {"imageUUID": d.get("imageUUID"), "cost": d.get("cost"), "seed": d.get("seed")}
        if "imageBase64Data" in d:
            try:
                return {**meta, "bytes": base64.b64decode(d["imageBase64Data"], validate=True), "delivery": "base64Data"}
            except ValueError:
                raise Blocked("PROVIDER_EXECUTION", "invalid base64 image data")
        if "imageDataURI" in d:
            m = re.fullmatch(r"data:(image/(?:png|webp|jpeg));base64,([A-Za-z0-9+/=]+)", str(d["imageDataURI"]))
            if not m:
                raise Blocked("PROVIDER_EXECUTION", "invalid image data URI")
            return {**meta, "bytes": base64.b64decode(m.group(2), validate=True), "delivery": "dataURI", "content_type": m.group(1)}
        if "imageURL" in d:
            if fetch_url is None:
                raise Blocked("PROVIDER_URL_FETCH_NOT_CONFIGURED", "URL output requires the approved fetcher")
            b, ctype = fetch_url(str(d["imageURL"]))
            return {**meta, "bytes": b, "delivery": "URL", "content_type": ctype}
        raise Blocked("PROVIDER_NO_IMAGE", "success item without image data")

    @staticmethod
    def parse_images(resp_bytes: bytes, task_uuid: str, *, fetch_url=None) -> list[dict]:
        c = RunwareAdapter.classify(resp_bytes, task_uuid)
        if c["status"] != "SUCCESS":
            raise Blocked("PROVIDER_EXECUTION" if c["status"] in ("ERROR", "UNPARSEABLE") else f"PROVIDER_{c['status']}",
                          str(c["error"])[:300])
        out = [RunwareAdapter.decode_item(d, fetch_url=fetch_url) for d in c["items"] if _has_image(d)]
        if not out:
            raise Blocked("PROVIDER_NO_IMAGE", "HTTP success without image data")
        return out


def _has_image(d: dict) -> bool:
    return any(k in d for k in ("imageBase64Data", "imageDataURI", "imageURL"))


def https_image_fetcher(allowed_hosts: list[str], *, max_bytes: int = 32 * 1024 * 1024, timeout: float = 60.0):
    """Controlled fetch of a provider-returned image URL: https only, exact allowed host, size/time/content-type limits."""
    from urllib.parse import urlparse
    from .authorization import network_allowed

    def fetch(url: str) -> tuple[bytes, str]:
        u = urlparse(url)
        if u.scheme != "https" or (u.hostname or "") not in allowed_hosts:
            raise Blocked("PROVIDER_URL_HOST_NOT_ALLOWED", f"{u.scheme}://{u.hostname}")
        if not network_allowed():
            raise Blocked("NETWORK_DISABLED", "image URL fetch needs VME_ALLOW_NETWORK=1")
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as r:  # noqa: S310
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
            if ctype not in ("image/png", "image/webp", "image/jpeg"):
                raise Blocked("PROVIDER_URL_CONTENT_TYPE", ctype)
            data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise Blocked("PROVIDER_URL_TOO_LARGE", str(len(data)))
        return data, ctype
    return fetch
