"""CLI for the REAL path and the human decisions it waits for (no paid call happens without `vme authorize`)."""
from __future__ import annotations

import json
from pathlib import Path

from .util import read_json


def _p(o):
    print(json.dumps(o, indent=2, sort_keys=True, ensure_ascii=False, default=str))


def run_real(ws, run_id: str, until: str = "S9") -> dict:
    from .loop.real import RealLoopRunner, RealProviders
    return RealLoopRunner(ws, run_id=run_id, providers=RealProviders.production(ws)).run(until=until)


def register(sub, wsf):
    def add(name, fn, *args):
        s = sub.add_parser(name)
        for a in args:
            s.add_argument(*a[0], **a[1])
        s.set_defaults(f=lambda a: fn(wsf(a), a))
        return s

    def real_run(ws, a):
        _p(run_real(ws, a.run_id, a.until))
    add("real", real_run, (["action"], {"choices": ["run"]}), (["--run-id"], {"default": "REAL-001"}), (["--until"], {"default": "S9"}))

    def confirm_role(ws, a):
        from .reference.roles import confirm_role as cr, write_role_report
        _p(cr(ws, sha256=a.sha, role=a.role, confirmed_by=a.by, statement=a.statement or "confirmed via CLI"))
        write_role_report(ws, ws.reports_dir / "SOURCE_ROLE_CONFIRMATION_REPORT.md")
    add("confirm-role", confirm_role, (["--sha"], {"required": True}), (["--role"], {"required": True}), (["--by"], {"required": True}),
        (["--statement"], {}))

    def approve_sel(ws, a):
        from .loop.human import approve_selection
        _p(approve_selection(ws, manifest_sha=a.manifest_sha, approved_by=a.by))
    add("approve-selection", approve_sel, (["--manifest-sha"], {"required": True}), (["--by"], {"required": True}))

    def brief_add(ws, a):
        from .loop.human import add_brief
        _p(add_brief(ws, read_json(a.file), added_by=a.by, holdout=a.holdout))
    add("brief", brief_add, (["action"], {"choices": ["add"]}), (["--file"], {"required": True}), (["--by"], {"required": True}),
        (["--holdout"], {"action": "store_true"}))

    def provider(ws, a):
        from .loop.human import confirm_runware_model, confirm_vision_model
        if a.action == "confirm-runware":
            _p(confirm_runware_model(ws, model_air_id=a.model, confirmed_by=a.by, est_cost_per_image_usd=a.est_cost_usd))
        else:
            _p(confirm_vision_model(ws, model_id=a.model, confirmed_by=a.by, max_images_per_request=a.max_images))
    add("provider", provider, (["action"], {"choices": ["confirm-runware", "confirm-vision"]}), (["--model"], {"required": True}),
        (["--by"], {"required": True}), (["--est-cost-usd"], {"type": float, "default": None}), (["--max-images"], {"type": int, "default": 20}))

    def freeze(ws, a):
        from .loop.human import freeze_real_skill
        _p(freeze_real_skill(ws, Path(a.folder), approved_by=a.by))
    add("freeze-skill", freeze, (["--folder"], {"required": True}), (["--by"], {"required": True}))

    def ref_consent(ws, a):
        from .loop.human import consent_reference_exemplars
        _p(consent_reference_exemplars(ws, film_sha=a.film_sha, by=a.by, statement=a.statement))
    add("reference-consent", ref_consent, (["--film-sha"], {"required": True}), (["--by"], {"required": True}),
        (["--statement"], {"required": True}))

    def assets(ws, a):
        from .review.approvals import GateKeeper
        st = ws.store()
        try:
            out = st.get("LoopTransition", f"{a.run}:S7")["outputs"]
            _p(GateKeeper(st).submit_asset_verdict(a.run, pack_manifest={"files": out["files"]}, verdict="APPROVED" if a.action == "approve" else "REJECTED",
                                                   signed_by=a.by, character_family_ids=[]))
        finally:
            st.close()
    add("assets", assets, (["action"], {"choices": ["approve", "reject"]}), (["--run"], {"required": True}), (["--by"], {"required": True}))

    def video(ws, a):
        from .review.approvals import save_user_review
        st = ws.store()
        try:
            gaps = [g for g in (a.gaps or "").split(";") if g.strip()]
            _p(save_user_review(st, run_id=a.run, verdict=a.verdict, top_remaining_gaps=gaps, preferred_next_focus=a.focus or "",
                                submitted_by=a.by, linked_image_hashes=[], stage="video",
                                findings=[{"symptom": g, "attributed_stage": a.stage or "HUMAN_REVIEW"} for g in gaps]))
        finally:
            st.close()
    add("video", video, (["action"], {"choices": ["verdict"]}), (["--run"], {"required": True}), (["--verdict"], {"required": True}),
        (["--gaps"], {}), (["--focus"], {}), (["--stage"], {}), (["--by"], {"required": True}))
