"""Consent, spend cap and network barrier for every external call (A05, B24, C34, C38, spec 19 step 5).

Three independent permissions are required for any paid/external action:
  1. `VME_ALLOW_NETWORK=1` in the process environment (default: network disabled);
  2. a persisted, human-issued `ProviderAuthorization` naming provider, exact model,
     task categories and a USD spend ceiling;
  3. for any SOURCE FILM pixels leaving the machine, a separate `source_upload_consent`
     listing the allowed source SHA256s.
Missing or uncertain cost estimates stop the call (no guessing).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from pathlib import Path

from ..util import Blocked, atomic_write_json, read_json, now_iso, new_id

CONFIRM_PHRASE = "I AUTHORIZE PAID CALLS WITHIN THIS CAP"


@dataclass
class ProviderAuthorization:
    auth_id: str
    provider: str
    model_id: str
    task_categories: list
    spend_cap_usd: float
    source_upload_consent: bool
    allowed_source_shas: list
    issued_by: str
    issued_at: str
    note: str = ""
    revoked: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def network_allowed() -> bool:
    return os.environ.get("VME_ALLOW_NETWORK") == "1"


class AuthorizationRegistry:
    def __init__(self, state_dir: str | Path):
        self.path = Path(state_dir) / "AUTHORIZATIONS.json"

    def _load(self) -> dict:
        if self.path.exists():
            return read_json(self.path)
        return {"authorizations": [], "spend": {}}

    def issue(self, *, provider: str, model_id: str, task_categories: list, spend_cap_usd: float,
              issued_by: str, confirm_phrase: str, source_upload_consent: bool = False,
              allowed_source_shas: list | None = None, note: str = "") -> ProviderAuthorization:
        if confirm_phrase != CONFIRM_PHRASE:
            raise Blocked("AUTHORIZATION_PHRASE_MISSING", "explicit human confirmation phrase required")
        if not issued_by or issued_by.lower() in ("agent", "claude", "codex", "model", "auto"):
            raise Blocked("HUMAN_ISSUER_REQUIRED")
        if spend_cap_usd is None or spend_cap_usd <= 0:
            raise Blocked("SPEND_CAP_REQUIRED")
        if not model_id or model_id.lower() in ("auto", "flux klein 7b", "klein 7b") or "7b" in model_id.lower():
            raise Blocked("UNVERIFIED_MODEL_ID", f"model '{model_id}' is not a verified exact AIR id")
        if source_upload_consent and not allowed_source_shas:
            raise Blocked("SOURCE_UPLOAD_SCOPE_REQUIRED", "consent must list allowed source SHA256s")
        a = ProviderAuthorization(new_id("auth"), provider, model_id, sorted(task_categories), float(spend_cap_usd),
                                  bool(source_upload_consent), sorted(allowed_source_shas or []), issued_by, now_iso(), note)
        d = self._load()
        d["authorizations"].append(a.to_dict())
        atomic_write_json(self.path, d)
        return a

    def find(self, provider: str, model_id: str, task: str) -> ProviderAuthorization | None:
        for a in self._load()["authorizations"]:
            if (a["provider"] == provider and a["model_id"] == model_id and task in a["task_categories"]
                    and not a.get("revoked")):
                return ProviderAuthorization(**a)
        return None

    @property
    def ledger(self):
        from .ledger import SpendLedger
        return SpendLedger(self.path.parent / "SPEND_LEDGER.sqlite")

    def spent(self, auth_id: str) -> float:
        """Total exposure: settled actual cost + every open reservation / unknown liability (R07)."""
        return float(self._load()["spend"].get(auth_id, 0.0)) + self.ledger.exposure(auth_id)

    def record_spend(self, auth_id: str, usd: float) -> None:
        raise Blocked("UNRESERVED_SPEND_FORBIDDEN", "spend is recorded only by settling a reservation (reserve-before-submit)")

    def reserve(self, *, provider: str, model_id: str, task: str, estimated_cost_usd: float | None, logical_job_id: str,
                source_shas: list | None = None) -> tuple[ProviderAuthorization, dict]:
        """Permission checks + atomic reservation BEFORE any network submission. Idempotent per logical job."""
        a = self.check(provider=provider, model_id=model_id, task=task, estimated_cost_usd=estimated_cost_usd,
                       source_shas=source_shas, _skip_cap=True)
        assert estimated_cost_usd is not None
        r = self.ledger.reserve(auth_id=a.auth_id, provider=provider, cap_usd=a.spend_cap_usd - float(self._load()["spend"].get(a.auth_id, 0.0)),
                                logical_job_id=logical_job_id, estimated_max_cost=float(estimated_cost_usd))
        return a, r

    def check(self, *, provider: str, model_id: str, task: str, estimated_cost_usd: float | None,
              source_shas: list | None = None, _skip_cap: bool = False) -> ProviderAuthorization:
        """Raise Blocked unless all three permissions hold. Returns the governing authorization."""
        if not network_allowed():
            raise Blocked("NETWORK_DISABLED", "VME_ALLOW_NETWORK is not set; offline build")
        a = self.find(provider, model_id, task)
        if a is None:
            raise Blocked("NO_PROVIDER_AUTHORIZATION", f"{provider}/{model_id}/{task}")
        if source_shas:
            if not a.source_upload_consent:
                raise Blocked("NO_SOURCE_UPLOAD_CONSENT", "third-party upload of source frames not consented")
            outside = sorted(set(source_shas) - set(a.allowed_source_shas))
            if outside:
                raise Blocked("SOURCE_NOT_IN_CONSENT_SCOPE", str([s[:12] for s in outside]))
        if estimated_cost_usd is None:
            raise Blocked("COST_UNKNOWN_STOP", "no verified cost estimate; refusing to guess")
        if not _skip_cap and self.spent(a.auth_id) + estimated_cost_usd > a.spend_cap_usd + 1e-9:
            raise Blocked("SPEND_CAP_EXCEEDED", f"spent {self.spent(a.auth_id):.4f} + {estimated_cost_usd:.4f} > cap {a.spend_cap_usd}")
        return a
