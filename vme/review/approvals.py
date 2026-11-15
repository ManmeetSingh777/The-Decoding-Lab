"""Immutable hash-bound approvals and the visual gate state machine (07 §4, 04, A07/A42–A44/A47, B30, C33).

ARTWORK approval → ASSET-family approval → (only then) integrated video. Approvals are
bound to the exact bytes; any byte change invalidates them. Only a named human can sign;
fixture simulations are labelled and can never authorise a non-synthetic run.
"""
from __future__ import annotations

from pathlib import Path

from ..util import Blocked, digest, new_id, now_iso, sha256_file

GATE_STATES = ("AWAITING_PROVIDER_OR_SOURCE", "ART_GENERATING", "ART_FAILED_INTERNAL", "AWAITING_ARTWORK_REVIEW",
               "ARTWORK_REJECTED", "ARTWORK_APPROVED", "ASSET_PREPARING", "AWAITING_ASSET_REVIEW", "ASSETS_REJECTED",
               "ASSETS_APPROVED", "VIDEO_RENDERING", "AWAITING_VIDEO_REVIEW", "TRANSFER_PENDING", "TRANSFER_QUALIFIED")
TRANSITIONS = {
    "AWAITING_PROVIDER_OR_SOURCE": {"ART_GENERATING"},
    "ART_GENERATING": {"ART_FAILED_INTERNAL", "AWAITING_ARTWORK_REVIEW"},
    "ART_FAILED_INTERNAL": {"ART_GENERATING"},
    "AWAITING_ARTWORK_REVIEW": {"ARTWORK_REJECTED", "ARTWORK_APPROVED"},
    "ARTWORK_REJECTED": {"ART_GENERATING"},
    "ARTWORK_APPROVED": {"ASSET_PREPARING", "ART_GENERATING"},
    "ASSET_PREPARING": {"AWAITING_ASSET_REVIEW"},
    "AWAITING_ASSET_REVIEW": {"ASSETS_REJECTED", "ASSETS_APPROVED"},
    "ASSETS_REJECTED": {"ASSET_PREPARING"},
    "ASSETS_APPROVED": {"VIDEO_RENDERING", "ASSET_PREPARING"},
    "VIDEO_RENDERING": {"AWAITING_VIDEO_REVIEW"},
    "AWAITING_VIDEO_REVIEW": {"TRANSFER_PENDING", "ASSET_PREPARING", "ART_GENERATING"},
    "TRANSFER_PENDING": {"TRANSFER_QUALIFIED", "ART_GENERATING"},
    "TRANSFER_QUALIFIED": set(),
}
REVIEW_VERDICTS = ("APPROVED_IMPROVEMENT", "PARTIAL", "REJECTED", "NEEDS_EVIDENCE")
_NON_HUMAN = ("agent", "claude", "codex", "model", "auto", "system", "")
FIXTURE_SIGNER = "TEST_FIXTURE_HUMAN_SIMULATION"


class GateKeeper:
    def __init__(self, store):
        self.store = store

    def state(self, run_id: str) -> dict:
        return self.store.get("VisualGateState", run_id) or {"run_id": run_id, "state": "AWAITING_PROVIDER_OR_SOURCE",
                                                              "required_art_approval_ids": [], "required_asset_approval_ids": [],
                                                              "authorized_render_art_hashes": [], "authorized_render_asset_hashes": [],
                                                              "blocked_reasons": [], "synthetic": False}

    def transition(self, run_id: str, to: str, *, reason: str = "", synthetic: bool | None = None) -> dict:
        st = self.state(run_id)
        if to not in TRANSITIONS[st["state"]]:
            raise Blocked("ILLEGAL_GATE_TRANSITION", f"{st['state']} → {to}")
        st["state"] = to
        if synthetic is not None:
            st["synthetic"] = synthetic
        st.setdefault("history", []).append({"to": to, "reason": reason, "at": now_iso()})
        self.store.put("VisualGateState", run_id, st)
        self.store.event("GATE", run_id, {"to": to, "reason": reason})
        return st

    def _sign(self, signed_by: str, synthetic: bool) -> None:
        if (signed_by or "").strip().lower() in _NON_HUMAN:
            raise Blocked("HUMAN_SIGNATURE_REQUIRED", "approvals cannot be issued by the agent")
        if signed_by == FIXTURE_SIGNER and not synthetic:
            raise Blocked("FIXTURE_SIGNATURE_ON_REAL_RUN")

    def submit_art_verdict(self, run_id: str, *, image_paths: list[str], brief_id: str, skill_versions: list[str],
                           verdict: str, defects: list, signed_by: str) -> dict:
        st = self.state(run_id)
        if st["state"] != "AWAITING_ARTWORK_REVIEW":
            raise Blocked("NOT_AWAITING_ARTWORK_REVIEW", st["state"])
        if verdict not in ("APPROVED", "REJECTED"):
            raise Blocked("BAD_VERDICT", verdict)
        self._sign(signed_by, st.get("synthetic", False))
        hashes = sorted(sha256_file(p) for p in image_paths)
        a = {"approval_id": new_id("artapp"), "run_id": run_id, "original_brief_id": brief_id, "image_hashes": hashes,
             "image_paths": image_paths, "skill_versions": skill_versions, "verdict": verdict, "defects": defects,
             "signed_at": now_iso(), "signed_by": signed_by, "synthetic_fixture": st.get("synthetic", False)}
        a["approval_sha"] = digest(a)
        self.store.put("ArtApproval", a["approval_id"], a)
        self.store.event("ART_VERDICT", run_id, {"approval_id": a["approval_id"], "approval_sha": a["approval_sha"], "verdict": verdict})
        st = self.transition(run_id, "ARTWORK_APPROVED" if verdict == "APPROVED" else "ARTWORK_REJECTED", reason=verdict)
        if verdict == "APPROVED":
            st["required_art_approval_ids"] = [a["approval_id"]]
            st["authorized_render_art_hashes"] = hashes
            self.store.put("VisualGateState", run_id, st)
        return a

    def submit_asset_verdict(self, run_id: str, *, pack_manifest: dict, verdict: str, signed_by: str,
                             character_family_ids: list) -> dict:
        st = self.state(run_id)
        if st["state"] != "AWAITING_ASSET_REVIEW":
            raise Blocked("NOT_AWAITING_ASSET_REVIEW", st["state"])
        self._sign(signed_by, st.get("synthetic", False))
        self.verify_art_still_valid(run_id)
        pack_hashes = sorted(sha256_file(p) for p in pack_manifest["files"])
        a = {"approval_id": new_id("assetapp"), "run_id": run_id, "approved_art_ids": st["required_art_approval_ids"],
             "asset_manifest_sha256": digest(pack_hashes), "asset_files": pack_manifest["files"], "character_family_ids": character_family_ids,
             "verdict": verdict, "signed_at": now_iso(), "signed_by": signed_by, "synthetic_fixture": st.get("synthetic", False)}
        a["approval_sha"] = digest(a)
        self.store.put("AssetApproval", a["approval_id"], a)
        self.store.event("ASSET_VERDICT", run_id, {"approval_id": a["approval_id"], "approval_sha": a["approval_sha"], "verdict": verdict})
        st = self.transition(run_id, "ASSETS_APPROVED" if verdict == "APPROVED" else "ASSETS_REJECTED", reason=verdict)
        if verdict == "APPROVED":
            st["required_asset_approval_ids"] = [a["approval_id"]]
            st["authorized_render_asset_hashes"] = pack_hashes
            self.store.put("VisualGateState", run_id, st)
        return a

    def _approval_genuine(self, rtype: str, approval_id: str) -> dict:
        a = self.store.get(rtype, approval_id)
        if a is None:
            raise Blocked("APPROVAL_NOT_FOUND_OR_FORGED", approval_id)
        ev = [e for e in self.store.events("ART_VERDICT" if rtype == "ArtApproval" else "ASSET_VERDICT")
              if e["body"].get("approval_id") == approval_id]
        body = {k: v for k, v in a.items() if k != "approval_sha"}
        if not ev or ev[-1]["body"]["approval_sha"] != a["approval_sha"] or digest(body) != a["approval_sha"]:
            raise Blocked("APPROVAL_TAMPERED_OR_FORGED", approval_id)
        return a

    def verify_art_still_valid(self, run_id: str) -> None:
        st = self.state(run_id)
        for aid in st["required_art_approval_ids"]:
            a = self._approval_genuine("ArtApproval", aid)
            if a["verdict"] != "APPROVED":
                raise Blocked("ART_NOT_APPROVED", aid)
            now = sorted(sha256_file(p) if Path(p).exists() else "MISSING" for p in a["image_paths"])
            if now != a["image_hashes"]:
                self._invalidate(run_id, "APPROVED_ART_BYTES_CHANGED")
                raise Blocked("APPROVED_ART_BYTES_CHANGED", "art changed after approval: reapproval required")

    def reopen(self, run_id: str, level: str, *, reason: str) -> dict:
        """Deterministic downstream invalidation (R12): ART clears art+asset approvals and returns to ART_GENERATING;
        ASSET clears asset approvals and returns to ASSET_PREPARING. Approvals stay in the store (append-only), unusable."""
        st = self.state(run_id)
        if level == "ART":
            if st["state"] in ("AWAITING_PROVIDER_OR_SOURCE", "ART_GENERATING"):
                return st
            st.update(state="ART_GENERATING", required_art_approval_ids=[], required_asset_approval_ids=[],
                      authorized_render_art_hashes=[], authorized_render_asset_hashes=[])
        elif level == "ASSET":
            if st["state"] in ("ASSET_PREPARING",):
                return st
            st.update(state="ASSET_PREPARING", required_asset_approval_ids=[], authorized_render_asset_hashes=[])
        else:
            raise Blocked("UNKNOWN_REOPEN_LEVEL", level)
        st.setdefault("history", []).append({"to": st["state"], "reason": f"REOPEN_{level}: {reason}", "at": now_iso()})
        self.store.put("VisualGateState", run_id, st)
        self.store.event("GATE_REOPENED", run_id, {"level": level, "reason": reason})
        return st

    def _invalidate(self, run_id: str, reason: str) -> None:
        st = self.state(run_id)
        st["authorized_render_art_hashes"] = []
        st["authorized_render_asset_hashes"] = []
        st["blocked_reasons"].append(reason)
        st["state"] = "AWAITING_ARTWORK_REVIEW" if "ART" in reason else "AWAITING_ASSET_REVIEW"
        self.store.put("VisualGateState", run_id, st)
        self.store.event("APPROVAL_INVALIDATED", run_id, {"reason": reason})

    def authorize_render(self, run_id: str, *, scene_asset_paths: list[str]) -> dict:
        """The renderer's ONLY door for an integrated video: both approvals, genuine, bytes unchanged."""
        st = self.state(run_id)
        if st["state"] not in ("ASSETS_APPROVED",):
            raise Blocked("RENDER_REFUSED_GATE", f"state {st['state']} (needs ARTWORK_APPROVED then ASSETS_APPROVED)")
        if not st["required_art_approval_ids"] or not st["required_asset_approval_ids"]:
            raise Blocked("RENDER_REFUSED_MISSING_APPROVAL")
        self.verify_art_still_valid(run_id)
        for aid in st["required_asset_approval_ids"]:
            a = self._approval_genuine("AssetApproval", aid)
            if a["verdict"] != "APPROVED":
                raise Blocked("ASSETS_NOT_APPROVED", aid)
            now = sorted(sha256_file(p) if Path(p).exists() else "MISSING" for p in a["asset_files"])
            if digest(now) != a["asset_manifest_sha256"]:
                self._invalidate(run_id, "APPROVED_ASSET_BYTES_CHANGED")
                raise Blocked("APPROVED_ASSET_BYTES_CHANGED")
        allowed = set(st["authorized_render_asset_hashes"]) | set(st["authorized_render_art_hashes"])
        for p in scene_asset_paths:
            if sha256_file(p) not in allowed:
                raise Blocked("RENDER_USES_UNAPPROVED_ASSET", p)
        self.transition(run_id, "VIDEO_RENDERING", reason="approvals verified")
        return {"authorized": True, "run_id": run_id, "synthetic": st.get("synthetic", False)}


def save_user_review(store, *, run_id: str, verdict: str, top_remaining_gaps: list, preferred_next_focus: str,
                     submitted_by: str, linked_image_hashes: list, stage: str = "art", findings: list | None = None) -> dict:
    """04 feedback form: persistent, timestamped, immutable review record."""
    if verdict not in REVIEW_VERDICTS:
        raise Blocked("BAD_REVIEW_VERDICT", verdict)
    if (submitted_by or "").strip().lower() in _NON_HUMAN:
        raise Blocked("HUMAN_SIGNATURE_REQUIRED")
    r = {"review_id": new_id("rev"), "run_id": run_id, "verdict": verdict, "top_remaining_gaps": top_remaining_gaps,
         "preferred_next_focus": preferred_next_focus, "timestamp": now_iso(), "submitted_by": submitted_by,
         "linked_image_hashes": linked_image_hashes, "stage": stage,
         # findings: [{symptom, attributed_stage, decision_id?, required_conditions?}] — the human's attribution drives the next question
         "findings": findings or [{"symptom": g, "attributed_stage": "HUMAN_REVIEW"} for g in top_remaining_gaps]}
    store.put("VisualReview", r["review_id"], r)
    store.event("USER_REVIEW", run_id, {"review_id": r["review_id"], "verdict": verdict})
    return r
