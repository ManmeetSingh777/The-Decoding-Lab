"""Human-owned decisions the REAL loop waits for. Every function requires a named human; none is called by handlers.

Selection approval, original briefs (anchor / sealed unseen holdout), user-confirmed provider models and price
estimates, provider probe results, and real-skill freeze. (Art/asset/video verdicts live in vme.review.approvals.)
"""
from __future__ import annotations

from ..util import Blocked, atomic_write_json, digest, now_iso, read_json
from ..state.workspace import Workspace
from ..compiler.brief import validate_brief

_NON_HUMAN = ("agent", "claude", "codex", "model", "auto", "system", "")


def _human(by: str) -> None:
    if (by or "").strip().lower() in _NON_HUMAN:
        raise Blocked("HUMAN_REQUIRED", "this decision must be made by a named person")


def approve_selection(ws: Workspace, *, manifest_sha: str, approved_by: str, note: str = "") -> dict:
    _human(approved_by)
    st = ws.store()
    try:
        man = st.get("SelectedSequenceManifest", "REAL:15")
        if not man or man.get("manifest_sha") != manifest_sha:
            raise Blocked("SELECTION_MANIFEST_MISMATCH", "approve the manifest that was presented")
        rec = {"manifest_sha": manifest_sha, "approved_by": approved_by, "at": now_iso(), "note": note}
        st.put("SelectionApproval", manifest_sha, rec)
        return rec
    finally:
        st.close()


def add_brief(ws: Workspace, raw: dict, *, added_by: str, holdout: bool = False) -> dict:
    _human(added_by)
    b = validate_brief(raw)
    st = ws.store()
    try:
        if holdout:
            from ..experiments.experiments import HoldoutRegistry
            HoldoutRegistry(ws.state_dir / "HOLDOUTS.json").seal(raw)
            st.event("HOLDOUT_SEALED", b.brief_id, {"by": added_by, "sha": digest(raw)})
            return {"sealed": b.brief_id}
        rec = {"brief": raw, "added_by": added_by, "at": now_iso(), "brief_sha": digest(raw)}
        st.put("OriginalBrief", b.brief_id, rec)
        st.put("ActiveBrief", "anchor", {"brief_id": b.brief_id})
        return rec
    finally:
        st.close()


def _ps(ws: Workspace) -> dict:
    p = ws.state_dir / "PROVIDER_STATE.json"
    return read_json(p) if p.exists() else {}


def confirm_runware_model(ws: Workspace, *, model_air_id: str, confirmed_by: str, est_cost_per_image_usd: float) -> dict:
    """The AIR id is never guessed: it must be typed by the user and exist in the capability snapshots."""
    _human(confirmed_by)
    from ..providers.capabilities import resolve_model
    snap = resolve_model(model_air_id)
    snap.update(user_confirmed_model=True, confirmed_by=confirmed_by, confirmed_at=now_iso(), cost_per_image_usd=float(est_cost_per_image_usd),
                cost_basis="USER_SUPPLIED_ESTIMATE")
    d = _ps(ws)
    d["runware"] = snap
    atomic_write_json(ws.state_dir / "PROVIDER_STATE.json", d)
    return snap


def confirm_vision_model(ws: Workspace, *, model_id: str, confirmed_by: str, max_images_per_request: int = 20) -> dict:
    _human(confirmed_by)
    d = _ps(ws)
    d["vision"] = {"provider": "anthropic-claude", "model_id": model_id, "max_images_per_request": int(max_images_per_request),
                   "confirmed_by": confirmed_by, "confirmed_at": now_iso(), "discovered": None}
    atomic_write_json(ws.state_dir / "PROVIDER_STATE.json", d)
    return d["vision"]


def provider_state(ws: Workspace) -> dict:
    return _ps(ws)


def record_runware_probe(ws: Workspace, observed: dict) -> dict:
    d = _ps(ws)
    if "runware" not in d:
        raise Blocked("MODEL_NOT_CONFIRMED")
    d["runware"].update(verified_by_probe=True, probe_observed=observed, probe_at=now_iso())
    atomic_write_json(ws.state_dir / "PROVIDER_STATE.json", d)
    return d["runware"]


def freeze_real_skill(ws: Workspace, folder, *, approved_by: str) -> dict:
    """REAL freeze: structural derivation of every clause from evidenced decisions + named human approval."""
    _human(approved_by)
    from ..style.authoring import verify_structural_derivation
    v = verify_structural_derivation(folder)
    if not v["ok"]:
        raise Blocked("FREEZE_REFUSED", str(v["problems"][:3]), report=v)
    rep = {"skill_hash": v["skill_hash"], "approved_by": approved_by, "at": now_iso(), "result": "FROZEN",
           "basis": "structural derivation verified; artistic quality UNPROVEN"}
    from pathlib import Path
    atomic_write_json(Path(folder) / "FROZEN.json", rep)
    return rep


def consent_reference_exemplars(ws: Workspace, *, film_sha: str, by: str, statement: str) -> dict:
    """Human consent to package exemplar bytes from this source film as skill references AND to send those bytes to the
    image provider (third-party upload). Without it mandatory references block compilation (R08/R16)."""
    _human(by)
    st = ws.store()
    try:
        rec = {"film_sha256": film_sha, "status": "CONSENTED", "consented_by": by, "statement": statement, "at": now_iso(),
               "scope": "skill reference exemplars (full frames / native crops) for provider upload under a separate spend authorization"}
        st.put("ReferenceExemplarConsent", film_sha, rec)
        return rec
    finally:
        st.close()
