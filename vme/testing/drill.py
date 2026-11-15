"""REAL-path drill harness (TESTING ONLY). Builds a workspace from SYNTHETIC source clips and plays the human
through the same public APIs a person uses (role confirmation, model confirmation, authorization, brief, approvals).
The REAL handlers it drives are the production ones; only the transports are simulated.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..state.workspace import Workspace
from ..util import digest

DRILL_HUMAN = "TEST_FIXTURE_HUMAN_SIMULATION"


def drill_brief(brief_id: str = "BRIEF-DRILL-ANCHOR", subject: str = "deep-sea research explorer", kind: str = "biped",
                env: str = "underwater", setting: str = "giant underwater observatory") -> dict:
    return {"brief_id": brief_id, "shot_id": "drill-shot-1",
            "subjects": [{"id": "explorer", "noun": subject, "subject_kind": kind, "role": "focal", "content_attributes": []}],
            "actions": ["looks at a specimen chamber, turns to the viewer, grips the chamber handle"],
            "world": {"setting": setting, "environment": env}, "visual_focus": "explorer and chamber",
            "camera_or_view_requirement": "three_quarter then front", "novelty_constraints": ["no source characters or logos"],
            "animation_requirements": ["view change", "grip"], "content_provenance": "FIXTURE_DRILL",
            "slots": {"subject": subject, "setting": setting, "action": "examines a floating specimen chamber", "visual_role": "focal",
                      "view": "three_quarter", "subject_kind": kind, "environment": env, "original_prop": "specimen chamber handle"},
            "scope": {"subjects": [{"id": "explorer", "kind": "character", "subject_kind": kind, "role": "focal", "view": "three_quarter",
                                    "view_changes": ["front"], "face_visible": True, "contact_props": ["chamber_handle"], "lighting_changes": False}],
                      "world": {"kind": env, "layers": True, "lighting": "directional"}},
            "shot_plan": {"actions": [{"actor": "explorer", "event_id": "e1", "view": "front"},
                                      {"actor": "explorer", "event_id": "e2", "contact_prop": "chamber_handle", "hand_side": "right"}],
                          "events": [{"from": 20, "to": 39, "state": "view:front"}, {"from": 40, "to": 59, "state": "grip:chamber_handle"}],
                          "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1.0}, {"frame": 59, "x": 20, "y": 0, "scale": 1.05}],
                          "fps": 30, "frames": 60}}


def build_drill_workspace(root: Path) -> dict:
    from ..fixtures.synthetic import make_clip, make_sixth_clip
    from ..reference.ingest import ingest, index_all
    from ..reference.frame_index import read_index
    from ..reference.survey import survey_film
    from ..reference.roles import confirm_role
    from ..selection.sixth import locate_sixth_intro, lock_sixth_interval
    from ..loop.human import add_brief, confirm_runware_model, confirm_vision_model
    from ..providers.authorization import AuthorizationRegistry, CONFIRM_PHRASE
    src = root / "drill_sources"
    for i in range(5):
        make_clip(src / f"SYNTHETIC_DRILL_BASE_{i}.mp4", frames=30 + i, fps=30)   # distinct bytes per film
    make_sixth_clip(src / "SYNTHETIC_DRILL_SIXTH.mp4", segments=[("gray", 8), ("red", 14), ("blue", 10)], fps=30)
    ws = Workspace(root / "ws").ensure()
    lock = ingest(ws, src)
    index_all(ws, src, workers=3)
    st = ws.store()
    for s in lock["sources"]:
        idx = read_index(ws.frames_dir / s["sha256"] / "index.jsonl.gz")
        st.put("FilmSurvey", s["sha256"], survey_film(src / s["relative_path"], s["sha256"], idx, ws.frames_dir / s["sha256"]).to_dict())
    st.close()
    six = next(s for s in lock["sources"] if "SIXTH" in s["file_name"])
    for s in lock["sources"]:
        confirm_role(ws, sha256=s["sha256"], role="SIXTH_SPECIAL" if s is six else "BASE_FILM", confirmed_by=DRILL_HUMAN, statement="drill")
    idx6 = read_index(ws.frames_dir / six["sha256"] / "index.jsonl.gz")
    st = ws.store()
    cuts = [x["start_frame_index"] for x in (st.get("FilmSurvey", six["sha256"]) or {})["shots"]][1:]
    res = locate_sixth_intro(src / six["relative_path"], six["sha256"], idx6, cut_frames=cuts, search_window_s=(0, 5)).to_dict()
    st.put("SixthIntroLocatorResult", "REAL", res)
    st.put("SpecialIntroSelection", "REAL", lock_sixth_interval(res, start_frame_index=8, end_frame_index_inclusive=22, confirmed_by=DRILL_HUMAN,
                                                                  index=idx6, witness_packet_sha=digest(res["witness_packet"])))
    st.close()
    confirm_vision_model(ws, model_id="claude-opus-5-5", confirmed_by=DRILL_HUMAN, max_images_per_request=20)
    confirm_runware_model(ws, model_air_id="runware:400@4", confirmed_by=DRILL_HUMAN, est_cost_per_image_usd=0.002)
    reg = AuthorizationRegistry(ws.state_dir)
    shas = [s["sha256"] for s in lock["sources"]]
    reg.issue(provider="anthropic-claude", model_id="claude-opus-5-5", task_categories=["source_vision", "capability_probe"], spend_cap_usd=500.0,
              issued_by=DRILL_HUMAN, confirm_phrase=CONFIRM_PHRASE, source_upload_consent=True, allowed_source_shas=shas, note="DRILL — simulated transport")
    reg.issue(provider="runware", model_id="runware:400@4", task_categories=["image_generation", "capability_probe"], spend_cap_usd=5.0,
              issued_by=DRILL_HUMAN, confirm_phrase=CONFIRM_PHRASE, note="DRILL — simulated transport")
    add_brief(ws, drill_brief(), added_by=DRILL_HUMAN)
    return {"ws": ws, "sources": src}


def drill_providers(root: Path, *, vision_mode: str = "ok", image_mode: str = "ok"):
    from ..loop.real import RealProviders
    from .simulated_anthropic import SimulatedAnthropicClient
    from ..providers.gateway import OfflineRecordingTransport
    client = SimulatedAnthropicClient(root / "sim_anthropic", mode=vision_mode)
    return RealProviders(vision_client_factory=lambda: client, vision_transport_kind="SIMULATED",
                         image_transport=OfflineRecordingTransport(root / "sim_runware", mode=image_mode), image_transport_kind="SIMULATED"), client


def drill_config():
    from ..loop.real import RealLoopConfig
    return RealLoopConfig(max_window_s=0.34, min_window_s=0.2, max_windows_per_film=3, target_per_packet=8, native_followups_per_sequence=1,
                          max_questions=80, render={"width": 320, "height": 180, "fps": 30})


def enable_network_flag():
    os.environ["VME_ALLOW_NETWORK"] = "1"   # simulated transports only; no socket is opened by these adapters


def drive(ws: Workspace, providers, *, run_id: str = "REAL-DRILL", crash_at: list[str] | None = None, max_rounds: int = 40) -> dict:
    """Run the REAL loop, acting as the (fixture) human whenever it stops for a human decision.
    crash_at: stages after whose commit an in-process crash is injected once each (resume must continue)."""
    from ..loop.real import RealLoopRunner
    from ..loop.human import approve_selection, freeze_real_skill, add_brief
    from ..review.approvals import GateKeeper, save_user_review
    from ..vision.runner import SimulatedCrash
    pending = list(crash_at or [])
    log: list[dict] = []
    for _ in range(max_rounds):
        injected = bool(pending)
        if pending:
            os.environ["VME_CRASH_AT"] = f"real_after_{pending[0]}"
        try:
            out = RealLoopRunner(ws, run_id=run_id, providers=providers, config=drill_config()).run()
        except SimulatedCrash as c:
            log.append({"crash": str(c)})
            pending.pop(0)
            os.environ.pop("VME_CRASH_AT", None)
            continue
        finally:
            if injected and not pending:
                os.environ.pop("VME_CRASH_AT", None)
        log.append({"stopped_at": out.get("stopped_at"), "reason": out.get("reason"), "completed": out.get("completed_through")})
        if out.get("completed_through") == "S9":
            break
        reason = out.get("reason")
        st = ws.store()
        try:
            if reason == "AWAITING_SELECTION_APPROVAL":
                m = st.get("SelectedSequenceManifest", "REAL:15") or {}
                st.close()
                approve_selection(ws, manifest_sha=m["manifest_sha"], approved_by=DRILL_HUMAN)
                st = ws.store()
            elif reason == "AWAITING_ARTWORK_REVIEW":
                imgs = (st.get("LoopTransition", f"{run_id}:S6") or {})["outputs"]["images"]
                GateKeeper(st).submit_art_verdict(run_id, image_paths=imgs, brief_id="BRIEF-DRILL-ANCHOR", skill_versions=[], verdict="APPROVED",
                                                  defects=[], signed_by=DRILL_HUMAN)
            elif reason == "AWAITING_ASSET_REVIEW":
                s7 = (st.get("LoopTransition", f"{run_id}:S7") or {})["outputs"]
                GateKeeper(st).submit_asset_verdict(run_id, pack_manifest={"files": s7["files"]}, verdict="APPROVED", signed_by=DRILL_HUMAN,
                                                    character_family_ids=["explorer"])
            elif reason == "AWAITING_VIDEO_REVIEW":
                save_user_review(st, run_id=run_id, verdict="PARTIAL", top_remaining_gaps=["grip hand does not overlap the handle"],
                                 preferred_next_focus="grip", submitted_by=DRILL_HUMAN, linked_image_hashes=[], stage="video",
                                 findings=[{"symptom": "DRILL: grip state hand does not overlap the handle", "attributed_stage": "PROVIDER_RESULT"}])
            elif reason == "AWAITING_SKILL_FREEZE":
                f = (st.get("LoopTransition", f"{run_id}:S4") or {})["outputs"]["skill_folder"]
                st.close()
                freeze_real_skill(ws, f, approved_by=DRILL_HUMAN)
                st = ws.store()
            elif reason == "AWAITING_UNSEEN_BRIEF":
                st.close()
                add_brief(ws, drill_brief(brief_id=f"BRIEF-DRILL-UNSEEN-{len(log)}", subject="tidal survey diver"), added_by=DRILL_HUMAN, holdout=True)
                st = ws.store()
            else:
                return {"result": out, "log": log}
        finally:
            st.close()
    return {"result": out, "log": log}
