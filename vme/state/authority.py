"""R3 F08/F16 — separately stored, locally trusted authority registry.

Human approvals, source-upload consents, provider capability verifications, reviewed invariances, text-only transfer reviews and
source-art reviews live HERE, scoped to source SHA / witness / image-byte SHA / decision / condition. No code path copies a model reply
into this registry: an answer's `approved: true`, `qualification_proofs` or self-declared invariance is never consulted. Every record is
content-hashed, signed by a named human (agent/model names refused) and append-only (a later record supersedes, history stays).
"""
from __future__ import annotations

from ..util import Blocked, digest, now_iso

KINDS = ("SOURCE_UPLOAD_CONSENT", "PROVIDER_REFERENCE_CAPABILITY", "INVARIANCE_REVIEW", "TEXT_ONLY_TRANSFER_REVIEW", "SOURCE_ART_REVIEW",
         "ORIGINAL_ASSET_REVIEW", "SOUND_ASSET_APPROVAL", "INTENTIONAL_STILLNESS_REVIEW", "QUALIFICATION_REVIEW")
_NON_HUMAN = ("", "agent", "claude", "codex", "model", "auto", "system", "assistant", "gpt")
VERDICTS = ("APPROVED", "REFUTED", "NEEDS_EVIDENCE")


def _human(by: str) -> None:
    if not isinstance(by, str) or by.strip().lower() in _NON_HUMAN:
        raise Blocked("HUMAN_SIGNER_REQUIRED", f"{by!r} cannot sign an authority record")


class AuthorityRegistry:
    def __init__(self, store):
        self.store = store

    def issue(self, kind: str, *, scope: dict, verdict: str, by: str, statement: str, evidence: dict | None = None) -> dict:
        if kind not in KINDS:
            raise Blocked("UNKNOWN_AUTHORITY_KIND", kind)
        if verdict not in VERDICTS:
            raise Blocked("BAD_AUTHORITY_VERDICT", verdict)
        _human(by)
        if not statement or not statement.strip():
            raise Blocked("AUTHORITY_STATEMENT_REQUIRED")
        key = f"{kind}:{digest(scope)[:24]}"
        rec = {"authority_id": key, "kind": kind, "scope": scope, "scope_sha": digest(scope), "verdict": verdict, "by": by,
               "statement": statement, "evidence": evidence or {}, "issued_via": "LOCAL_HUMAN_AUTHORITY", "at": now_iso()}
        rec["record_sha"] = digest({k: v for k, v in rec.items() if k != "at"})
        self.store.put("AuthorityRecord", key, rec)
        self.store.event("AUTHORITY_ISSUED", key, {"kind": kind, "verdict": verdict, "by": by})
        return rec

    def get(self, kind: str, scope: dict) -> dict | None:
        r = self.store.get("AuthorityRecord", f"{kind}:{digest(scope)[:24]}")
        if r and r.get("issued_via") == "LOCAL_HUMAN_AUTHORITY" and r.get("record_sha") == digest({k: v for k, v in r.items()
                                                                                                    if k not in ("at", "record_sha")}):
            return r
        return None

    def approved(self, kind: str, scope: dict) -> bool:
        r = self.get(kind, scope)
        return bool(r and r["verdict"] == "APPROVED")

    # -- scoped lookups used by production code ------------------------------------------------------
    def upload_consent(self, film_sha: str, image_bytes_sha: str | None = None) -> dict | None:
        """Consent may name exact exemplar bytes, or (broader, explicitly stated by the human) a whole film."""
        if image_bytes_sha:
            r = self.get("SOURCE_UPLOAD_CONSENT", {"film_sha256": film_sha, "image_bytes_sha256": image_bytes_sha})
            if r and r["verdict"] == "APPROVED":
                return r
        r = self.get("SOURCE_UPLOAD_CONSENT", {"film_sha256": film_sha, "image_bytes_sha256": "ALL_EXEMPLARS_OF_THIS_FILM"})
        if r and r["verdict"] == "APPROVED":
            return r
        legacy = self.store.get("ReferenceExemplarConsent", film_sha)        # human CLI record from Phase 3 (film-wide)
        return legacy if legacy and legacy.get("status") == "CONSENTED" else None

    def invariance(self, decision_id: str, axis: str) -> dict | None:
        r = self.get("INVARIANCE_REVIEW", {"decision_id": decision_id, "axis": axis})
        return r if r and r["verdict"] == "APPROVED" and len(r["evidence"].get("witness_ids", [])) >= 2 else None

    def text_only_transfer(self, decision_id: str, when: dict, action: str) -> dict | None:
        r = self.get("TEXT_ONLY_TRANSFER_REVIEW", {"decision_id": decision_id, "condition_sha": digest(when), "action_sha": digest(action)})
        return r if r and r["verdict"] == "APPROVED" else None

    def source_art_review(self, decision_id: str, version: int) -> dict | None:
        return self.get("SOURCE_ART_REVIEW", {"decision_id": decision_id, "version": int(version)})

    def provider_reference_capability(self, provider: str, model: str) -> dict | None:
        r = self.get("PROVIDER_REFERENCE_CAPABILITY", {"provider": provider, "model": model})
        return r if r and r["verdict"] == "APPROVED" else None

    def sound_asset(self, asset_sha: str) -> dict | None:
        r = self.get("SOUND_ASSET_APPROVAL", {"asset_sha256": asset_sha})
        return r if r and r["verdict"] == "APPROVED" else None
