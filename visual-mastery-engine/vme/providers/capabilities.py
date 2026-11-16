"""Provider capability snapshots and exact-model verification (spec 19, B23, C17)."""
from __future__ import annotations

import re
from pathlib import Path

from ..util import Blocked, read_json, digest

_AIR = re.compile(r"^[a-z0-9_-]+:[0-9]+@[0-9]+$")
_DEFAULT = Path(__file__).resolve().parents[2] / "config" / "provider_capabilities.json"


def load_snapshots(path: str | Path | None = None) -> list[dict]:
    return read_json(path or _DEFAULT)["snapshots"]


def resolve_model(requested: str, *, path: str | Path | None = None) -> dict:
    """Return the snapshot for an EXACT AIR id. Names like 'FLUX Klein 7B' are refused, never mapped."""
    if not requested or not _AIR.match(requested):
        raise Blocked("UNVERIFIED_MODEL_ID", f"'{requested}' is not an exact AIR id (e.g. runware:400@4); no guessing")
    for s in load_snapshots(path):
        if s["model_air_id"] == requested:
            return {**s, "caps_sha": digest(s)}
    raise Blocked("MODEL_NOT_IN_CAPABILITY_SNAPSHOTS", requested)


def assert_paid_ready(snapshot: dict, *, probe: bool) -> None:
    """A non-probe paid job needs a capability snapshot verified by a consented probe."""
    if not snapshot.get("user_confirmed_model"):
        raise Blocked("MODEL_NOT_USER_CONFIRMED", snapshot["model_air_id"])
    if not probe and not snapshot.get("verified_by_probe"):
        raise Blocked("CAPABILITIES_NOT_VERIFIED_BY_PROBE", snapshot["snapshot_id"])
