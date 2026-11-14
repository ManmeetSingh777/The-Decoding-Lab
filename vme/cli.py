"""`vme` command-line interface (01 §10, 07 §5, 24 D3, 25 §5.2). Every command calls real module code;
paid/external actions refuse truthfully unless network + human authorization + consent exist."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .util import Blocked, read_json, atomic_write_json
from .state.workspace import Workspace, write_continue_here

ROOT = Path(__file__).resolve().parents[1]


def _ws(a) -> Workspace:
    return Workspace(Path(a.workspace or os.environ.get("VME_WORKSPACE") or ROOT / "workspace")).ensure()


def _p(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, default=str))


def cmd_doctor(a):
    from .reference.probe import which
    rem = ROOT / "render" / "remotion" / "node_modules" / "remotion"
    out = {"python": sys.version.split()[0], "ffmpeg": which("ffmpeg"), "ffprobe": which("ffprobe"), "node": which("node"),
           "remotion_installed": rem.exists(), "network_allowed": os.environ.get("VME_ALLOW_NETWORK") == "1",
           "runware_key_present_in_env": bool(os.environ.get("RUNWARE_API_KEY")), "runware_key_value": "NEVER_PRINTED",
           "prior_animationlab_artifacts_found": [str(p) for p in ROOT.rglob("*") if "animationlab" in p.name.lower()][:5]}
    ws = _ws(a)
    if (ws.state_dir / "SOURCE_LOCK.json").exists():
        lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
        out["sources"] = [{k: s[k] for k in ("file_name", "sha256", "role", "basis")} for s in lock["sources"]]
        out["sixth_status"] = lock["sixth_status"]
    _p(out)


def cmd_sources(a):
    from .reference.ingest import ingest, index_all
    ws = _ws(a)
    if a.action in ("probe", "ingest"):
        lock = ingest(ws, a.folder)
        _p({"sources": [{k: s[k] for k in ("file_name", "sha256", "role", "basis", "format_duration_s")} for s in lock["sources"]],
            "sixth_status": lock["sixth_status"], "note": lock["contract_title_note"]})
        if a.action == "ingest" and a.index_every_frame:
            a.action = "index"
    if a.action == "index":
        res = index_all(ws, a.folder, workers=a.workers)
        _p([{k: r[k] for k in ("file_name", "frame_count_decoded", "complete_frame_index", "vfr_observed", "end_gap_s", "problems")} for r in res])
    if a.action == "vision":
        from .vision.providers import estimate_vision_cost
        summ = read_json(ws.state_dir / "FRAME_INDEX_SUMMARY.json")
        _p({"all_frames": summ["total_frames_decoded"], "estimate": estimate_vision_cost(None, summ["total_frames_decoded"]),
            "dry_run": True, "submitted": 0})


def cmd_survey(a):
    from .reference.frame_index import read_index
    from .reference.survey import survey_film
    ws = _ws(a)
    lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
    out = []
    for s in lock["sources"]:
        if a.film and not s["sha256"].startswith(a.film):
            continue
        idx = read_index(ws.frames_dir / s["sha256"] / "index.jsonl.gz")
        sv = survey_film(Path(lock["folder"]) / s["relative_path"], s["sha256"], idx, ws.frames_dir / s["sha256"], threshold=a.threshold)
        st = ws.store()
        st.put("FilmSurvey", s["sha256"], sv.to_dict())
        st.close()
        out.append({"file": s["file_name"], "shots": len(sv.shots), "status": sv.status})
    _p(out)


def cmd_selection(a):
    from .selection.first15 import propose_selection, navigation_candidates_from_survey
    ws = _ws(a)
    st = ws.store()
    try:
        lock = read_json(ws.state_dir / "SOURCE_LOCK.json")
        if a.action == "candidates":
            out = []
            for s in lock["sources"]:
                if s["role"] != "BASE_FILM" or (a.film and not s["sha256"].startswith(a.film)):
                    continue
                sv = st.get("FilmSurvey", s["sha256"])
                if not sv:
                    raise Blocked("NO_SURVEY", s["file_name"])
                nav = navigation_candidates_from_survey(s["sha256"], sv)
                atomic_write_json(ws.frames_dir / s["sha256"] / "navigation_candidates.json", nav)
                out.append({"film": s["file_name"], "navigation_windows": len(nav), "status": "AWAITING_VISUAL_RATIONALE"})
            if a.import_rationales:
                for c in read_json(a.import_rationales):
                    st.put("CandidateSequence", c["candidate_id"], c)
            _p(out)
        elif a.action == "propose":
            base = [s["sha256"] for s in lock["sources"] if s["role"] == "BASE_FILM"]
            man = propose_selection(st.list("CandidateSequence"), base, per_film=a.per_film)
            st.put("SelectedSequenceManifest", "current", man)
            _p({k: man.get(k) for k in ("status", "selected_count", "target", "substitutions", "reason")} | {"rejected": len(man.get("rejected", []))})
        elif a.action == "explain":
            _p(st.get("SelectedSequenceManifest", a.manifest or "current"))
        elif a.action == "sixth-locate":
            st.close()
            from .reference.real_local import run_real_sixth_locator
            r = run_real_sixth_locator(ws)
            _p({k: r.get(k) for k in ("status", "clip_file", "search_window_frames", "witness_packet_sha", "human_next_step", "notes")}
               | {"candidate_cut_boundaries": len(r.get("candidate_starts", []))})
            st = ws.store()
        elif a.action == "sixth-lock":
            from .selection.sixth import lock_sixth_interval
            from .reference.frame_index import read_index
            res = st.get("SixthIntroLocatorResult", "REAL")
            six = next(s for s in lock["sources"] if s["role"] == "SIXTH_SPECIAL")
            idx = read_index(ws.frames_dir / six["sha256"] / "index.jsonl.gz")
            rec = lock_sixth_interval(res, start_frame_index=a.start, end_frame_index_inclusive=a.end, confirmed_by=a.confirmed_by,
                                      index=idx, witness_packet_sha=a.witness_sha)
            st.put("SpecialIntroSelection", "REAL", rec)
            _p(rec)
    finally:
        st.close()


def cmd_vision(a):
    from .vision.providers import estimate_vision_cost
    ws = _ws(a)
    st = ws.store()
    try:
        if a.action == "estimate":
            man = st.get("SelectedSequenceManifest", a.selection or "current") or {"selected": []}
            n = sum(s["actual_frame_count"] for s in man.get("selected", []))
            _p({"selected_frames": n, "estimate": estimate_vision_cost(None, n)})
        elif a.action == "coverage":
            rows = st.conn.execute("SELECT pass_id, status, COUNT(*) FROM frame_vision GROUP BY pass_id, status").fetchall()
            summ = read_json(ws.state_dir / "FRAME_INDEX_SUMMARY.json") if (ws.state_dir / "FRAME_INDEX_SUMMARY.json").exists() else {}
            _p({"indexed_total": summ.get("total_frames_decoded"), "vision_rows": rows,
                "real_vlm_seen": sum(r[2] for r in rows if r[1] == "VISION_OUTPUT_VERIFIED")})
        elif a.action in ("run", "plan", "resume"):
            raise Blocked("BLOCKED_CONSENT", "real per-frame VLM needs a chosen provider, verified capabilities/price, "
                                             "source-upload consent and a spend cap (vme authorize ...)")
    finally:
        st.close()


def cmd_investigate(a):
    ws = _ws(a)
    st = ws.store()
    try:
        if a.action == "questions":
            p = st.get("ActiveArtProblem", a.cluster)
            qs = [q for q in st.list("NextQuestion") if q["cluster_id"] == a.cluster]
            _p({"active_problem": p, "questions": qs})
        elif a.action == "explain":
            _p({"question": st.get("NextQuestion", a.question), "effect": st.get("AnswerEffect", a.question)})
    finally:
        st.close()


def cmd_skill(a):
    from .skills.skill import load_skill
    ws = _ws(a)
    if a.action == "trace":
        st = ws.store()
        _p({"decision": next((d for d in st.list("ConditionalVisualDecision") if d["decision_id"] == a.decision), None),
            "compiled_job": st.get("CompiledImageJob", a.compiled_job) if a.compiled_job else None})
        st.close()
    elif a.action == "show":
        sk = load_skill(a.folder)
        _p({k: sk[k] for k in ("skill_id", "version", "status", "claim_state", "synthetic", "skill_hash")})
    elif a.action == "freeze":
        raise Blocked("FREEZE_NEEDS_OBSERVED_RELATIONS", "use the S4 loop stage (freeze is gated by Interface I provenance)")


def cmd_art(a):
    from .compiler.compiler import StyleProgramCompiler
    from .providers.capabilities import resolve_model
    from .skills.skill import skill_hash
    ws = _ws(a)
    if a.action == "compile":
        caps = resolve_model(a.model)
        job = StyleProgramCompiler().compile(read_json(a.brief), a.skill, pinned_skill_hash=a.pin or skill_hash(a.skill),
                                             recipe_id=a.recipe, node_id=a.node, caps=caps)
        _p({"job_id": job.job_id, "payload": {k: (v if k != "inputs" else {"referenceImages": len(v["referenceImages"])})
                                               for k, v in job.logical_payload.items()},
            "coverage": job.trace["interface_two_audit"], "selected_decisions": job.trace["selected_decisions"],
            "clause_ids": job.trace["clause_ids"], "synthetic": job.synthetic, "allow_paid_call": False})
    elif a.action == "generate":
        raise Blocked("PAID_GENERATION_NOT_AUTHORIZED", "offline build: no Runware calls (needs vme authorize + VME_ALLOW_NETWORK=1 + probe)")
    elif a.action in ("approve", "reject"):
        from .review.approvals import GateKeeper
        st = ws.store()
        try:
            r = GateKeeper(st).submit_art_verdict(a.run, image_paths=a.images, brief_id=a.brief_id or "?", skill_versions=[],
                                                  verdict="APPROVED" if a.action == "approve" else "REJECTED",
                                                  defects=json.loads(a.issues or "[]"), signed_by=a.signed_by)
            _p(r)
        finally:
            st.close()


def cmd_render(a):
    from .review.approvals import GateKeeper
    ws = _ws(a)
    st = ws.store()
    try:
        GateKeeper(st).authorize_render(a.run, scene_asset_paths=[])
    finally:
        st.close()


def cmd_review(a):
    from .review.server import serve
    ws = _ws(a)
    st = ws.store()
    imgs = [{"path": g["outputs"][0]["path"], "sha256": g["outputs"][0]["sha256"], "label": g["label"], "caption": g["job_id"]}
            for g in st.list("GeneratedRaster")]
    print(f"Serving http://127.0.0.1:{a.port}/  (Ctrl+C to stop)")
    serve(st, a.run, images=imgs, packet={"gate": st.get("VisualGateState", a.run)}, port=a.port)


def cmd_authorize(a):
    from .providers.authorization import AuthorizationRegistry
    ws = _ws(a)
    auth = AuthorizationRegistry(ws.state_dir).issue(provider=a.provider, model_id=a.model, task_categories=a.tasks.split(","),
                                                     spend_cap_usd=a.cap_usd, issued_by=a.issued_by, confirm_phrase=a.confirm,
                                                     source_upload_consent=a.source_upload_consent,
                                                     allowed_source_shas=(a.allowed_sources or "").split(",") if a.allowed_sources else [])
    _p(auth.to_dict())


def cmd_status(a):
    from .state.handoff import exact_next_operation
    ws = _ws(a)
    st = ws.read_state()
    nxt = exact_next_operation(ws)
    out = {"state": st, "next_operation": nxt, "claims": {
        "ENGINE_READY": "see TEST_RESULTS.json", "ALL_FRAME_DECODER_READY": True, "PAID_VLM_FRAMES_SEEN": st.get("paid_vlm_frames_seen", 0),
        "RUNWARE_REAL_CALLS": st.get("runware_real_calls", 0), "ART_QUALITY_NOT_EVALUATED": True, "ANIMATION_FIXTURE_ONLY": True,
        "TRANSFER_NOT_EVALUATED": True}}
    if a.detailed:
        s = ws.store()
        out["record_types"] = {t: len(s.list(t)) for t in s.list_types()}
        s.close()
    _p(out)


def cmd_checkpoint(a):
    ws = _ws(a)
    from .state.handoff import exact_next_operation
    nxt = exact_next_operation(ws)
    write_continue_here(ws, next_command=nxt["command"], details={"reason": a.reason, "next_operation": json.dumps(nxt)})
    s = ws.store()
    s.event("CHECKPOINT", None, {"reason": a.reason})
    s.close()
    _p({"checkpointed": True, "next": nxt})


def cmd_export(a):
    from .state.handoff import export_handoff
    _p(export_handoff(_ws(a), a.output, reason=a.reason))


def cmd_import(a):
    from .state.handoff import import_handoff
    _p(import_handoff(a.zip, a.workspace_out, sources_folder=a.sources))


def cmd_resume(a):
    from .state.handoff import exact_next_operation
    ws = _ws(a)
    nxt = exact_next_operation(ws)
    rep = {"verified_store": ws.store().integrity_ok(), "next_operation": nxt}
    if (ws.state_dir / "IMPORT_REPORT.json").exists():
        rep["import_report"] = read_json(ws.state_dir / "IMPORT_REPORT.json")
    _p(rep)


def cmd_loop(a):
    from .loop.stages import LoopRunner
    ws = _ws(a)
    _p(LoopRunner(ws, run_id=a.run_id, mode=a.mode, simulate_human=a.simulate_human_fixture).run(until=a.until))


def cmd_audit(a):
    from .audit.export import build_audit_zip
    _p(build_audit_zip(Path(a.out), workspace=_ws(a)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vme")
    ap.add_argument("--workspace")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("doctor"); s.set_defaults(f=cmd_doctor)
    s = sub.add_parser("sources"); s.add_argument("action", choices=["probe", "ingest", "index", "vision"])
    s.add_argument("--folder", default=str(ROOT.parent / "source_clips")); s.add_argument("--index-every-frame", action="store_true")
    s.add_argument("--all", action="store_true"); s.add_argument("--verify", action="store_true"); s.add_argument("--workers", type=int, default=6)
    s.add_argument("--coverage"); s.add_argument("--estimate-cost", action="store_true"); s.add_argument("--dry-run", action="store_true")
    s.set_defaults(f=cmd_sources)
    s = sub.add_parser("survey"); s.add_argument("action", choices=["build"]); s.add_argument("--all", action="store_true")
    s.add_argument("--navigation-only", action="store_true"); s.add_argument("--film"); s.add_argument("--threshold", type=float, default=0.30)
    s.set_defaults(f=cmd_survey)
    s = sub.add_parser("selection"); s.add_argument("action", choices=["candidates", "propose", "explain", "sixth-locate", "sixth-lock"])
    s.add_argument("--film"); s.add_argument("--target", type=int, default=15); s.add_argument("--per-film", type=int, default=3)
    s.add_argument("--roles", default="W,C,T"); s.add_argument("--manifest"); s.add_argument("--import-rationales")
    s.add_argument("--start", type=int); s.add_argument("--end", type=int); s.add_argument("--confirmed-by"); s.add_argument("--witness-sha")
    s.set_defaults(f=cmd_selection)
    s = sub.add_parser("vision"); s.add_argument("action", choices=["estimate", "plan", "run", "coverage", "resume"])
    s.add_argument("--selection"); s.add_argument("--provider"); s.add_argument("--every-frame", action="store_true")
    s.add_argument("--authorization"); s.add_argument("--by-frame", action="store_true"); s.add_argument("--pass")
    s.set_defaults(f=cmd_vision)
    s = sub.add_parser("investigate"); s.add_argument("action", choices=["questions", "explain"]); s.add_argument("--cluster")
    s.add_argument("--question"); s.add_argument("--evidence"); s.set_defaults(f=cmd_investigate)
    s = sub.add_parser("skill"); s.add_argument("action", choices=["trace", "show", "freeze"]); s.add_argument("--decision")
    s.add_argument("--compiled-job"); s.add_argument("--folder"); s.set_defaults(f=cmd_skill)
    s = sub.add_parser("art"); s.add_argument("action", choices=["compile", "generate", "approve", "reject"])
    s.add_argument("--brief"); s.add_argument("--skill"); s.add_argument("--pin"); s.add_argument("--recipe", default="character_world")
    s.add_argument("--node", default="n1_scene"); s.add_argument("--model", default="runware:400@4"); s.add_argument("--run")
    s.add_argument("--images", nargs="*"); s.add_argument("--issues"); s.add_argument("--signed-by"); s.add_argument("--brief-id")
    s.set_defaults(f=cmd_art)
    s = sub.add_parser("render"); s.add_argument("--run", required=True); s.set_defaults(f=cmd_render)
    s = sub.add_parser("review"); s.add_argument("action", choices=["serve"]); s.add_argument("--run", required=True)
    s.add_argument("--port", type=int, default=8765); s.set_defaults(f=cmd_review)
    s = sub.add_parser("authorize"); s.add_argument("--provider", required=True); s.add_argument("--model", required=True)
    s.add_argument("--tasks", required=True); s.add_argument("--cap-usd", type=float, required=True); s.add_argument("--issued-by", required=True)
    s.add_argument("--confirm", required=True); s.add_argument("--source-upload-consent", action="store_true"); s.add_argument("--allowed-sources")
    s.set_defaults(f=cmd_authorize)
    s = sub.add_parser("status"); s.add_argument("--detailed", action="store_true"); s.set_defaults(f=cmd_status)
    s = sub.add_parser("checkpoint"); s.add_argument("--reason", default="manual"); s.set_defaults(f=cmd_checkpoint)
    s = sub.add_parser("export-handoff"); s.add_argument("--output", required=True); s.add_argument("--reason", default="switch-coding-agent")
    s.set_defaults(f=cmd_export)
    s = sub.add_parser("import-handoff"); s.add_argument("zip"); s.add_argument("--workspace-out", required=True); s.add_argument("--sources")
    s.set_defaults(f=cmd_import)
    s = sub.add_parser("resume"); s.add_argument("--verify", action="store_true"); s.set_defaults(f=cmd_resume)
    s = sub.add_parser("loop"); s.add_argument("action", choices=["run"]); s.add_argument("--run-id", required=True)
    s.add_argument("--mode", choices=["SYNTHETIC_FIXTURE", "REAL"], default="SYNTHETIC_FIXTURE"); s.add_argument("--until", default="S9")
    s.add_argument("--simulate-human-fixture", action="store_true"); s.set_defaults(f=cmd_loop)
    s = sub.add_parser("audit"); s.add_argument("action", choices=["export"]); s.add_argument("--offline", action="store_true")
    s.add_argument("--out", required=True); s.set_defaults(f=cmd_audit)
    a = ap.parse_args(argv)
    try:
        a.f(a)
    except Blocked as b:
        _p({"BLOCKED": b.to_dict()})
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
