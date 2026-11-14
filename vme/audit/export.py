"""`vme audit export --offline`: builds VME_V13_IMPLEMENTATION_AUDIT.zip from ACTUAL executions.

Every JSON trace is produced by calling the implementation (never hand-written). Test/lint/type
results come from commands run here. Excludes source MP4s, decoded source pixels, secrets, venv,
node_modules and caches. Synthetic artefacts are labelled SYNTHETIC throughout.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from ..util import Blocked, atomic_write_json, atomic_write_text, digest, now_iso, read_json, sha256_bytes, sha256_file
from ..state.workspace import Workspace
from .requirements import all_requirements, ORIGINAL_13

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3"
TEST_OWNERS = {
    "test_sources": "vme.reference.probe, vme.reference.frame_index, vme.reference.frames",
    "test_frames_native": "vme.reference.frames",
    "test_vision_ledger": "vme.vision.runner, vme.vision.contracts, vme.vision.providers",
    "test_questions": "vme.investigation.controller, vme.investigation.gaps",
    "test_style_decisions": "vme.style.decisions, vme.investigation.evidence",
    "test_compiler_authority": "vme.compiler.compiler, vme.compiler.brief, vme.skills.skill, vme.providers.gateway",
    "test_gateway": "vme.providers.gateway, vme.providers.runware, vme.providers.authorization, vme.providers.capabilities",
    "test_assets_character": "vme.artwork.raster, vme.artwork.assets, vme.artwork.character",
    "test_gates_render": "vme.review.approvals, vme.review.server, vme.render.renderer",
    "test_experiments_diagnosis": "vme.experiments.experiments, vme.diagnose.diagnose",
    "test_selection_sixth": "vme.selection.first15, vme.selection.sixth, vme.spec_registry",
    "test_completeness_provenance": "vme.style.coverage, vme.style.provenance, vme.skills.skill",
    "test_loop_handoff": "vme.loop.stages, vme.state.handoff",
    "test_schemas": "vme.audit.contracts",
}
EXCLUDE_DIRS = {".venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".git", "public", "audit_build"}
EXCLUDE_SUFFIX = (".mp4", ".mov", ".mkv", ".pyc", ".sqlite-wal", ".sqlite-shm")


def _run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 3600) -> dict:
    t0 = now_iso()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})})
    return {"cmd": " ".join(cmd), "returncode": r.returncode, "started": t0, "finished": now_iso(),
            "stdout_sha256": sha256_bytes(r.stdout.encode()), "stderr_sha256": sha256_bytes(r.stderr.encode()),
            "stdout_tail": r.stdout[-4000:], "stderr_tail": r.stderr[-2000:], "_stdout": r.stdout, "_stderr": r.stderr}


def run_checks(out: Path) -> dict:
    py = sys.executable
    raw = out / "test_results_raw.json"
    res = {"pytest": _run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], ROOT, {"VME_TEST_RESULTS": str(raw)}),
           "pyflakes": _run([py, "-m", "pyflakes", "vme", "tests"], ROOT),
           "mypy": _run([py, "-m", "mypy", "vme", "--ignore-missing-imports"], ROOT),
           "compileall": _run([py, "-m", "compileall", "-q", "vme"], ROOT),
           "node_check": _run(["node", "--check", "render/remotion/render.mjs"], ROOT),
           "reference_impl_v12": _run([py, "-m", "unittest", "-v"], SPEC / "reference_impl"),
           "reference_impl_v13": _run([py, "-m", "unittest", "-v"], SPEC / "reference_impl_v13")}
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for k, v in res.items():
        (logs / f"{k}.stdout.txt").write_text(v.pop("_stdout"), encoding="utf-8")
        (logs / f"{k}.stderr.txt").write_text(v.pop("_stderr"), encoding="utf-8")
    res["raw"] = read_json(raw) if raw.exists() else {"results": []}
    return res


def requirement_matrix(raw_results: list[dict]) -> dict:
    reqs = all_requirements()
    by: dict[str, list] = {k: [] for k in reqs}
    unknown = set()
    for r in raw_results:
        for rid in r["req_ids"]:
            if rid in by:
                by[rid].append(r)
            else:
                unknown.add(rid)
    rows = []
    for rid, meta in reqs.items():
        tests = by[rid]
        outcomes = [t["outcome"] for t in tests]
        if not tests:
            eng = "NOT_TESTED"
        elif any(o == "failed" for o in outcomes):
            eng = "FAIL"
        elif all(o == "skipped" for o in outcomes):
            eng = "SKIPPED"
        else:
            eng = "PASS"
        needs = meta["needs"]
        if eng == "FAIL":
            status = "FAIL"
        elif needs:
            status = "BLOCKED"
        elif eng == "PASS":
            status = "PASS"
        else:
            status = "NOT_BUILT" if eng == "NOT_TESTED" else "BLOCKED"
        files = sorted({t["nodeid"].split("::")[0].split("/")[-1].replace(".py", "") for t in tests})
        rows.append({"id": rid, "group": meta["group"], "requirement": meta["text"], "needs_for_positive_proof": needs or None,
                     "engineering_status": eng, "status": status,
                     "module": "; ".join(TEST_OWNERS.get(f, "?") for f in files) or None,
                     "tests": [t["nodeid"] for t in tests], "test_outcomes": outcomes,
                     "blocker": ({"PAID": "needs explicit provider authorization + spend cap (+ source-upload consent)",
                                  "ART": "needs real original artwork from an authorized provider",
                                  "HUMAN": "needs the user's visual verdict"}.get(needs.split("+")[0]) if needs else None),
                     "evidence_kind": "OFFLINE_ENGINEERING (synthetic fixtures and/or real local source decode)"})
    totals: dict[str, int] = {}
    for r in rows:
        totals[r["status"]] = totals.get(r["status"], 0) + 1
    return {"generated_at": now_iso(), "rows": rows, "totals": totals, "unknown_ids_in_tests": sorted(unknown),
            "note": "BLOCKED = offline wiring/refusal tests pass but positive proof needs PAID/ART/HUMAN; never counted as PASS."}


def _strip(o):
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items() if k not in ("referenceImages",)}
    if isinstance(o, list):
        return [_strip(x) for x in o]
    if isinstance(o, str) and o.startswith("data:image/"):
        return f"<data-uri sha256={sha256_bytes(o.encode())}>"
    return o


def generate_traces(out: Path, real_ws: Workspace) -> dict:
    """Run the actual code paths in a fresh temp workspace and write every required trace."""
    from ..fixtures import loop_fixtures as fx
    from ..loop.stages import LoopRunner
    from ..compiler.compiler import StyleProgramCompiler, CompiledImageJob
    from ..experiments.experiments import causal_mutation_test
    from ..providers.gateway import StyleImageGateway, OfflineRecordingTransport
    from ..providers.runware import RunwareAdapter
    from ..providers.authorization import AuthorizationRegistry
    from ..style.coverage import review_visual_model_completeness
    from ..style.provenance import interface_two_audit, interface_three_attribution
    from ..skills.operators import registered
    from ..skills.skill import freeze_skill, skill_hash
    from ..selection.first15 import propose_selection
    from ..vision.runner import plan_packets
    from ..state.handoff import export_handoff, import_handoff, exact_next_operation
    from ..artwork.assets import verify_pack
    from ..util import read_json as rj, atomic_write_json as aw
    from . import contracts as K
    written = {}

    def W(name, obj):
        p = out / name
        if name.endswith(".md"):
            atomic_write_text(p, obj)
        else:
            atomic_write_json(p, _strip(obj))
        written[name] = str(p)

    tmp = Path(tempfile.mkdtemp(prefix="vme_audit_"))
    ws = Workspace(tmp / "ws").ensure()
    loop = LoopRunner(ws, run_id="AUDIT-SYN-E2E", simulate_human=True).run()
    st = ws.store()
    T = {t["stage"]: t for t in st.list("LoopTransition") if t["run_id"] == "AUDIT-SYN-E2E"}
    s4 = T["S4"]["outputs"]
    folder, h = Path(s4["skill_folder"]), s4["skill_hash"]
    caps = fx.fixture_caps()
    brief = fx.synthetic_brief()
    c = StyleProgramCompiler()
    job = c.compile(brief, folder, pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene", caps=caps)
    # ---- 18 PROMPT_AUTHORITY_TRACE with bypass attempts --------------------------------------------
    g = StyleImageGateway(st, tmp / "art", RunwareAdapter(caps, OfflineRecordingTransport(tmp / "rt"), kind="OFFLINE_RECORDING"),
                          AuthorizationRegistry(tmp / "authz"))
    attempts = []
    for label, fn in [
        ("raw positivePrompt dict to gateway", lambda: g.submit({"positivePrompt": "draw a cute Kurzgesagt scientist"})),
        ("append 'add shiny Pixar-style lighting' after compile", lambda: (job.logical_payload.__setitem__("positivePrompt", job.logical_payload["positivePrompt"] + "\nadd shiny Pixar-style lighting"), g.submit(job))),
        ("construct CompiledImageJob directly", lambda: CompiledImageJob("x", {}, (), {}, {}, False, False, "0", object())),
        ("style words in brief", lambda: c.compile(fx.synthetic_brief(slots={"subject": "explorer with thick outlines and yellow highlights"}), folder,
                                                   pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene", caps=caps)),
        ("unverified model 'FLUX Klein 7B'", lambda: __import__("vme.providers.capabilities", fromlist=["x"]).resolve_model("FLUX Klein 7B")),
        ("pose edit without canonical identity", lambda: c.compile(brief, folder, pinned_skill_hash=h, recipe_id="character_world", node_id="n3_view", caps=caps)),
    ]:
        try:
            fn()
            attempts.append({"attempt": label, "result": "NOT_BLOCKED"})
        except Blocked as b:
            attempts.append({"attempt": label, "result": "BLOCKED", "code": b.code, "detail": b.detail[:200]})
    job = c.compile(brief, folder, pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene", caps=caps)
    W("PROMPT_AUTHORITY_TRACE.json", {"label": "SYNTHETIC FIXTURE skill — NOT learned style", "original_brief": brief, "skill_id": job.trace["skill_id"],
                                      "skill_hash": h, "selected_decisions": job.trace["selected_decisions"], "selected_branches": job.trace["selected_branches"],
                                      "clause_ids": job.trace["clause_ids"], "segments": job.trace["segments"], "provider_payload": job.logical_payload,
                                      "provider_payload_sha256": digest(job.logical_payload), "reference_roles": job.trace["reference_trace"],
                                      "operation_graph": job.trace["scene_art_plan"]["required_art_ops"],
                                      "gateway_call_path": "StyleProgramCompiler.compile → CompiledImageJob(issuer) → StyleImageGateway.submit → recompile check → interface_two_audit → RunwareAdapter.build_body → transport",
                                      "bypass_attempts": attempts, "contract_02": K.prompt_authority_trace(job.trace, job.logical_payload, [r[1] for r in job.reference_images]),
                                      "contract_21": K.prompt_trace(job.trace, job.logical_payload, [r[1] for r in job.reference_images])})
    # ---- causal mutations (B17/B18, ADD25-P03/P04, ADD27) -----------------------------------------
    def m_select(f):
        p = f / "prompt_templates" / "whole_scene.json"
        t = rj(p)
        for cl in t["clauses"]:
            if cl["id"].startswith("K-SYN-WORLD-01"):
                cl["template"] = cl["template"].replace("repeat one construction system", "repeat one construction system with clustered rhythm")
        aw(p, t)
        if (f / "FROZEN.json").exists():
            (f / "FROZEN.json").unlink()

    def m_prose(f):
        (f / "SKILL.md").write_text("cinematic glossy masterpiece prose", encoding="utf-8")

    def m_remove(f):
        aw(f / "decisions.json", [d for d in rj(f / "decisions.json") if d["decision_id"] != "D-SYN-WORLD"])
        if (f / "FROZEN.json").exists():
            (f / "FROZEN.json").unlink()
    mutations = [causal_mutation_test(folder, brief, caps, recipe_id="character_world", node_id="n1_scene", mutate=m, label=lab)
                 for m, lab in ((m_select, "selected clause edit"), (m_prose, "non-selected prose edit"), (m_remove, "remove required decision"))]
    W("SKILL_TO_PROVIDER_PAYLOAD_AUTHORITY.json", {
        "label": "SYNTHETIC", "interface_two_audit": job.trace["interface_two_audit"], "field_ownership": job.trace["field_ownership"],
        "segments": job.trace["segments"], "mutations": mutations,
        "unowned_field_injection": interface_two_audit(dict(job.logical_payload, CFGScale=9), job.trace["field_ownership"], job.trace["segments"]),
        "unauthorized_text_injection": interface_two_audit(dict(job.logical_payload, positivePrompt=job.logical_payload["positivePrompt"] + "\nmasterpiece"),
                                                           job.trace["field_ownership"], job.trace["segments"]),
        "lost_clause_compiler_bug": _lost_clause(c, brief, folder, h, caps)})
    W("STYLE_TO_COMPILED_IMAGE_JOB_TRACE.json", {"label": "SYNTHETIC", "jobs": [j for j in st.list("CompiledImageJob")], "mutations": mutations,
                                                  "bypass_attempts": attempts})
    # ---- construction / question / decision traces --------------------------------------------------
    qtrace = st.get("QuestionDerivationTrace", "AUDIT-SYN-E2E")
    d3 = [d for d in st.list("ConditionalVisualDecision")]
    W("CONSTRUCTION_TRACE.json", {"label": "SYNTHETIC fixture evidence — not a film observation",
                                  "witnesses": fx.synthetic_witnesses(), "observed_relations": fx.OBSERVED_RELATIONS,
                                  "questions": qtrace, "decisions": d3, "recipe": rj(folder / "recipes" / "character_world.json"),
                                  "compiled_prompt": job.logical_payload["positivePrompt"], "skill_hash": h})
    W("QUESTION_REFINEMENT_TRACE.json", {"label": "SYNTHETIC", "initial_problem": fx.synthetic_problem(), "derived_questions": qtrace,
                                         "note": "Q0–Q7 appear as reasoning_dimensions inside each NextQuestion, never as emitted questions"})
    tr = st.get("TransferRecord", "AUDIT-SYN-E2E")
    W("ADD26_QUESTION_DERIVATION_TRACE.json", {"label": "SYNTHETIC", "evidence_to_questions": qtrace,
                                               "after_changed_output": {"review": fx.synthetic_output_review(tr["output_sha"]), "next_question": tr["next_question"],
                                                                        "previous_question_text": tr["previous_question_text"], "changed": tr["question_changed"]},
                                               "active_problem_versions": st.versions("ActiveArtProblem", "CL-SYN-01")[-3:]})
    W("CROSS_FILM_STYLE_DECISION_TRACE.json", {"label": "SYNTHETIC", "decision": d3, "bundle": fx.synthetic_bundle().to_dict(),
                                               "scene_facts_excluded": [w.get("scene_specific_facts") for w in fx.synthetic_witnesses().values()],
                                               "substitution_challenge": d3[0]["substitution_challenge"] if d3 else None})
    W("CHARACTER_STYLE_WITNESS_DEMO.json", {"label": "SYNTHETIC", "cross_actor_group": __import__("vme.artwork.character", fromlist=["x"]).cross_actor_witness_group(
        list(fx.synthetic_witnesses().values()), "new actor three-quarter reach"), "witnesses": fx.synthetic_witnesses()})
    plan = st.get("CharacterConstructionPlan", "AUDIT-SYN-E2E:explorer")
    W("CHARACTER_STYLE_SKILL_TRACE.json", {"label": "SYNTHETIC", "C1_witness": "W-SYN-A01..A03,B01", "C3_relation": fx.OBSERVED_RELATIONS["R-SYN-02"],
                                           "C4_decision": d3, "C5_recipe_nodes": rj(folder / "recipes" / "character_world.json")["nodes"],
                                           "C6_compiled_pose_jobs": [j for j in st.list("CompiledImageJob") if j["trace"]["node_id"] in ("n3_view", "n4_grip")],
                                           "C7_output": "OFFLINE FIXTURE raster only — no real art; diagnosis BLOCKED until authorized", "construction_plan": plan})
    pack = rj(T["S7"]["outputs"]["pack"])
    W("CHARACTER_PACK_CONTRACT.json", {"label": "FIXTURE_ONLY_NOT_ART_QUALIFICATION", "construction_plan": plan, "pack": pack,
                                       "contract_02": K.character_construction_plan(plan), "contract_21": K.character_plan(plan, "explorer:canonical"),
                                       "verify": verify_pack(pack)})
    W("ASSET_ROUNDTRIP_REPORT.json", _asset_roundtrip(tmp, pack))
    # ---- selection / every-frame / crash ------------------------------------------------------------------
    man = st.get("SelectedSequenceManifest", "AUDIT-SYN-E2E:15")
    W("FIRST15_SELECTION_LOGIC_TRACE.json", {"label": "SYNTHETIC five-film candidate fixtures", "candidates": fx.synthetic_candidates(), "manifest": man,
                                             "four_film_block": propose_selection(fx.synthetic_candidates(), fx.SYNTHETIC_BASE_FILMS[:4])})
    W("FIRST15_SELECTION_CONTRACT.schema.json", _selection_schema())
    W("PER_FRAME_VISION_CONTRACT.schema.json", _per_frame_schema())
    idx = [{"presentation_index": i, "pts": 100 + i * 256, "frame_content_sha256": digest(i)} for i in range(200)]
    plans = plan_packets(idx, 100, 123, film_sha="SYNTHETIC", pass_id="p", cluster_id="c", model_version="m", max_images=12)
    pk = st.conn.execute("SELECT packet_id, state, start_frame, end_frame, provider_task_id, response_sha, semantic_manifest_sha FROM packets").fetchall()
    W("EVERY_FRAME_PLAN_AND_LEDGER.json", {"label": "SYNTHETIC", "range_100_123_plan": [p.to_dict() for p in plans],
                                           "target_frames": [k for p in plans for k in p.target_indices],
                                           "e2e_packets": [dict(zip(("packet_id", "state", "start", "end", "task", "response_sha", "semantic_sha"), r)) for r in pk],
                                           "e2e_coverage": T["S1"]["outputs"]["coverage"]})
    W("ADD26_END_TO_END_LOOP_TRACE.json", {"label": "SYNTHETIC_FIXTURE mode; simulated human signer TEST_FIXTURE_HUMAN_SIMULATION", "result": loop,
                                           "transitions": [T[s] for s in sorted(T)]})
    W("ADD26_SIXTH_INTRO_LOCATOR_CONTRACT.json", {"boundary_criteria": __import__("vme.selection.sixth", fromlist=["x"]).BOUNDARY_CRITERIA,
                                                  "synthetic_demo": st.get("SixthIntroLocatorResult", "AUDIT-SYN-E2E"),
                                                  "real_local_status": _real(real_ws, "SIXTH_LOCATOR_STATUS.json", drop=("witness_packet_files",)),
                                                  "statuses": __import__("vme.selection.sixth", fromlist=["x"]).STATUSES})
    W("ADD26_ACTIVE_ART_PROBLEM.schema.json", _problem_schema())
    # ---- Addendum 27 -----------------------------------------------------------------------------
    L, scope = fx.complete_ledger_and_scope()
    full = review_visual_model_completeness(L, scope, fx.synthetic_decisions(face_light_joint=True, grip_light_joint=True), registered())
    L2, _ = fx.complete_ledger_and_scope()
    gap = review_visual_model_completeness(L2, scope, fx.synthetic_decisions(face_light_joint=False, grip_light_joint=True), registered())
    W("COVERAGE_COMPLETENESS_DEMONSTRATION.json", {"label": "SYNTHETIC", "complete_scope": full, "missing_joint_face_view_light": gap})
    W("DYNAMIC_QUESTION_AFTER_COMPLETENESS_GAP.json", {"label": "SYNTHETIC", "controlling_gap": gap["controlling_gap"], "question_ticket": gap["question_ticket"],
                                                       "all_gaps": gap["gap_details"], "clusters": gap["clusters"]})
    W("VISUAL_MODEL_COMPLETENESS_NEGATIVE_TESTS.json", _neg27(fx, registered))
    W("SOURCE_TO_SKILL_PROVENANCE_AUDIT.json", _prov27(fx, tmp))
    W("SYNTHETIC_UNGOVERNED_OUTPUT_REVIEW.json", interface_three_attribution(
        [{"region_id": "face", "description": "3/4 face state", "claimed_decision_ids": ["D-SYN-FACE-VIEW"], "salience": "HIGH"},
         {"region_id": "coat", "description": "red laboratory coat", "content_fields": ["slots.subject"], "salience": "MEDIUM"},
         {"region_id": "rim", "description": "SYNTHETIC: unexpected rim highlight not requested by any clause", "salience": "HIGH"}],
        {"decision_ids": job.trace["selected_decisions"], "content_fields": ["slots.subject"]}))
    # ---- handoff / crash evidence -----------------------------------------------------------------
    ex = export_handoff(ws, tmp / "VME_PORTABLE_HANDOFF.zip")
    imp = import_handoff(ex["zip"], tmp / "other_env")
    W("CROSS_ENV_HANDOFF_TEST.json", {"export": ex, "import": imp, "next_op_source": exact_next_operation(ws),
                                      "next_op_imported": exact_next_operation(Workspace(tmp / "other_env").ensure()),
                                      "identical_next_operation": exact_next_operation(ws) == exact_next_operation(Workspace(tmp / "other_env").ensure())})
    st.close()
    shutil.rmtree(tmp, ignore_errors=True)
    return written


def _lost_clause(c, brief, folder, h, caps):
    from ..compiler.compiler import StyleProgramCompiler
    def buggy(t, s):
        return StyleProgramCompiler._default_render(t, s).replace("densest internal divisions", "")
    try:
        StyleProgramCompiler(clause_renderer=buggy).compile(brief, folder, pinned_skill_hash=h, recipe_id="character_world", node_id="n1_scene", caps=caps)
        return {"result": "NOT_DETECTED"}
    except Blocked as b:
        return {"result": "BLOCKED", "code": b.code, "payload_prompt_before": b.data.get("payload_prompt_before"),
                "payload_prompt_after": b.data.get("payload_prompt_after")}


def _asset_roundtrip(tmp: Path, pack: dict) -> dict:
    import copy
    from ..artwork.assets import verify_pack, recompose, recomposition_report, coordinate_map
    from ..artwork.raster import load_rgba, decode_raster
    from PIL import Image
    import io
    good = verify_pack(pack)
    canon = load_rgba(Path(pack["canonical"]["path"]).read_bytes())
    rec = recompose(pack["layers"], (pack["canonical"]["width"], pack["canonical"]["height"]))
    inj = {}
    for name, mut in {"opaque_claimed_transparent": lambda p: p["layers"][1].update(mode="RGBA", image_path=pack["layers"][0]["image_path"],
                                                                                         image_sha256=pack["layers"][0]["image_sha256"],
                                                                                         natural_size=pack["layers"][0]["natural_size"], local_origin=[0, 0]),
                      "mask_wrong_size": lambda p: p["layers"][1].update(mask_path=pack["layers"][0]["image_path"]),
                      "missing_clean_plate": lambda p: p["layers"][1].update(occluded_fill=None),
                      "z_order": lambda p: p["layers"][1].update(z=-5),
                      "contact_anchor": lambda p: p["contacts"][0].update(prop_anchor_world=[300, 300])}.items():
        q = copy.deepcopy(pack)
        mut(q)
        inj[name] = verify_pack(q)
    b = io.BytesIO()
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(b, format="PNG")
    opaque = decode_raster(b.getvalue(), asset_id="x", owner="o", skill_version="s").to_dict()
    return {"label": "FIXTURE rasters prove wiring only", "valid_pack": good, "recomposition": recomposition_report(rec, canon),
            "injected_failures": inj, "opaque_png_rgba_report": opaque,
            "coordinate_maps": {"1536x864": coordinate_map(1536, 864), "1920x1088": coordinate_map(1920, 1088)}}


def _neg27(fx, registered):
    from ..style.coverage import review_visual_model_completeness, OriginalScope, set_dimension, new_ledger, DIMENSIONS
    out = {}
    def rv(name, decs, ledger_mut=None, scope=None, **kw):
        L, sc = fx.complete_ledger_and_scope()
        if ledger_mut:
            ledger_mut(L)
        r = review_visual_model_completeness(L, scope or sc, decs, registered(), **kw)
        out[name] = {"state": r["review"]["state"], "controlling_gap": r["controlling_gap"], "gap_count": len(r["gap_details"]),
                     "question": (r["question_ticket"] or {}).get("actual_question")}
    rv("missing_facial_viewpoint_rule", fx.synthetic_decisions(include_face=False, face_light_joint=True, grip_light_joint=True))
    rv("pose_contact_without_lighting_link", fx.synthetic_decisions(face_light_joint=True, grip_light_joint=False))
    rv("face_view_light_individually_supported_no_joint", fx.synthetic_decisions(face_light_joint=False, grip_light_joint=True))
    rv("world_layers_camera_disconnected", fx.synthetic_decisions(face_light_joint=True, grip_light_joint=True),
       ledger_mut=lambda L: L["relations"].__setitem__(slice(None), [x for x in L["relations"] if x["relation_id"] != "world_layers+viewpoint"]))
    rv("unexpected_phenomenon", fx.synthetic_decisions(face_light_joint=True, grip_light_joint=True),
       unexplained_phenomena=[{"phenomenon": "ink-bleed reveal transition", "why": "fixture", "connected": ["TRANSITIONS_VISUAL_GRAMMAR"]}])
    L = new_ledger("S", ["x"])
    L["frame_coverage_state"] = "ALL_TARGET_FRAMES_SEEN"
    for d in DIMENSIONS:
        set_dimension(L, d, "NOT_APPLICABLE_WITH_REASON", evidence=[], why_relevant="x", inapplicability_reason="claimed absent")
    _, sc = fx.complete_ledger_and_scope()
    r = review_visual_model_completeness(L, sc, fx.synthetic_decisions(face_light_joint=True, grip_light_joint=True), registered())
    out["all_18_not_applicable"] = {"state": r["review"]["state"], "gap_count": len(r["gap_details"])}
    return {"label": "SYNTHETIC", "results": out}


def _prov27(fx, tmp: Path):
    from ..fixtures.synthetic import build_synthetic_skill
    from ..skills.skill import freeze_skill
    good = tmp / "prov_good"
    build_synthetic_skill(good)
    frozen = freeze_skill(good, observed_relations=fx.OBSERVED_RELATIONS, approved_by="audit-run")
    bad = tmp / "prov_bad"
    build_synthetic_skill(bad, extra_clause={"id": "K-SYN-EYES-99", "decision_id": "D-SYN-FACE-VIEW", "priority": 5,
                                             "template": "metallic teal eyes with tiny diamond-shaped sparkles", "allowed_content_slots": [],
                                             "reference_roles": [], "operation_id": "op.face_view_state", "origin_type": "CROSS_SOURCE_INFERRED"})
    try:
        freeze_skill(bad, observed_relations=fx.OBSERVED_RELATIONS, approved_by="audit-run")
        refused = None
    except Blocked as b:
        refused = b.data.get("report")
    return {"label": "SYNTHETIC", "interface_I_frozen_skill": frozen, "interface_I_model_authored_clause_refusal": refused,
            "origin_classes": __import__("vme.style.provenance", fromlist=["x"]).ORIGIN_TYPES}


def _selection_schema() -> dict:
    from ..selection.first15 import CANDIDATE_REQUIRED, ALL_OPPORTUNITIES, OBSERVERS
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "SelectedSequence (Addendum 25 §1.2–1.3)", "type": "object",
            "required": list(CANDIDATE_REQUIRED) + ["selection_role", "question_cluster_id"],
            "properties": {"selection_role": {"enum": ["W", "C", "T"]}, "observer": {"enum": list(OBSERVERS)},
                           "opportunities": {"type": "array", "items": {"enum": list(ALL_OPPORTUNITIES)}},
                           "start_frame_index": {"type": "integer", "minimum": 0}, "end_frame_index_inclusive": {"type": "integer", "minimum": 0},
                           "whole_visual_quality_statement": {"type": "string", "minLength": 25}}}


def _per_frame_schema() -> dict:
    from ..vision.contracts import FRAME_OBSERVATION_FIELDS, DIFF_KINDS, PACKET_STATES, COVERAGE_STATUSES
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "FrameObservation + packet (Addendum 25 §2.3)",
            "$defs": {"FrameObservation": {"type": "object", "required": [f for f in FRAME_OBSERVATION_FIELDS if f != "raw_response_path"],
                                           "properties": {"changed_since_prior_frame": {"type": "array", "items": {"type": "object", "properties": {"kind": {"enum": list(DIFF_KINDS)}}}}}},
                      "PacketState": {"enum": list(PACKET_STATES)}, "CoverageStatus": {"enum": list(COVERAGE_STATUSES)}}}


def _problem_schema() -> dict:
    from ..investigation.controller import ActiveArtProblem, NextQuestion, HANDOFF_ORDER
    import dataclasses
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "ActiveArtProblem + NextQuestion (Addendum 26 §3.1/3.3)",
            "$defs": {"ActiveArtProblem": {"type": "object", "required": [f.name for f in dataclasses.fields(ActiveArtProblem)
                                                                          if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING],
                                           "properties": {"owner_stage": {"enum": list(HANDOFF_ORDER)}}},
                      "NextQuestion": {"type": "object", "required": [f.name for f in dataclasses.fields(NextQuestion)
                                                                      if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING]}}}


def _real(ws: Workspace, name: str, drop=()):
    p = ws.state_dir / name
    if not p.exists():
        return {"status": "NOT_RUN"}
    d = read_json(p)
    return {k: v for k, v in d.items() if k not in drop}


def real_source_artifacts(out: Path, ws: Workspace) -> dict:
    lock = _real(ws, "SOURCE_LOCK.json")
    summ = _real(ws, "FRAME_INDEX_SUMMARY.json")
    st = ws.store()
    vis = st.conn.execute("SELECT status, COUNT(*) FROM frame_vision GROUP BY status").fetchall()
    surveys = {s["film_sha256"]: len(s["shots"]) for s in st.list("FilmSurvey")}
    st.close()
    atomic_write_json(out / "SOURCE_MANIFEST.json", {"source_lock": lock, "decoded": [{k: f[k] for k in ("file_name", "film_sha256", "role", "frame_count_decoded",
                                                                                                        "first_pts", "last_pts", "time_base", "vfr_observed",
                                                                                                        "complete_frame_index", "end_gap_s", "index_sha256", "problems")}
                                                                                       for f in summ.get("films", [])],
                                                     "total_frames_decoded": summ.get("total_frames_decoded"), "base_five_total": summ.get("base_five_total"),
                                                     "note": "Counts from actual decode (ffmpeg framehash, passthrough timing, -copyts); not fps×duration."})
    films = []
    for f in summ.get("films", []):
        films.append({"film": f["file_name"], "sha256": f["film_sha256"], "role": f["role"], "indexed": f["frame_count_decoded"],
                      "surveyed_navigation_shots": surveys.get(f["film_sha256"], 0), "vlm_seen": 0, "artistically_reviewed": 0,
                      "native_detail_reviewed": 0})
    cov = {"films": films, "vision_rows_by_status": vis, "PAID_VLM_FRAMES_SEEN": 0,
           "base_five_film_coverage": {"indexed": summ.get("base_five_total"), "vlm_seen": 0},
           "special_sixth_clip_coverage": {"indexed": next((f["indexed"] for f in films if f["role"] == "SIXTH_SPECIAL"), 0), "vlm_seen": 0,
                                           "locator": _real(ws, "SIXTH_LOCATOR_STATUS.json").get("status")},
           "first15_real_selection": "NOT_RUN (needs whole-artwork witness rationales from a HUMAN or authorized VLM)"}
    atomic_write_json(out / "FRAME_COVERAGE.json", cov)
    atomic_write_json(out / "SOURCE_COVERAGE_STATUS.json", cov)
    return cov


def build_audit_zip(out_zip: Path, *, workspace: Workspace) -> dict:
    out_zip = Path(out_zip).resolve()
    build = ROOT / "audit_build"
    shutil.rmtree(build, ignore_errors=True)
    audit = build / "audit"
    audit.mkdir(parents=True)
    checks = run_checks(audit)
    raw = checks.pop("raw")
    matrix = requirement_matrix(raw.get("results", []))
    atomic_write_json(audit / "REQUIREMENT_MATRIX.json", matrix)
    tr = {k: {kk: vv for kk, vv in v.items()} for k, v in checks.items()}
    outcomes: dict[str, int] = {}
    for r in raw.get("results", []):
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    atomic_write_json(audit / "TEST_RESULTS.json", {"platform": {"os": platform.platform(), "python": sys.version, "node": _ver("node"),
                                                                 "ffmpeg": _ver("ffmpeg", "-version")}, "commands": tr, "pytest_outcomes": outcomes,
                                                    "pytest_cases": raw.get("results", []), "generated_at": now_iso()})
    real = real_source_artifacts(audit, workspace)
    traces = generate_traces(audit, workspace)
    for g, prefix in (("ADD25", "ADD25-"), ("ADD26", "ADD26-")):
        rows = [r for r in matrix["rows"] if r["id"].startswith(prefix)]
        atomic_write_json(audit / ("ADDENDUM25_TEST_RESULTS.json" if g == "ADD25" else "ADD26_TEST_RESULTS.json"),
                          {"rows": rows, "pytest_log": "logs/pytest.stdout.txt"})
    from .docs import write_docs
    write_docs(audit, matrix=matrix, checks=checks, real=real, traces=traces, workspace=workspace)
    # assemble zip
    tmp_zip = out_zip.with_suffix(".tmp.zip")
    files = []
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
        def add(p: Path, arc: str):
            z.write(p, arc)
            files.append({"path": arc, "sha256": sha256_file(p), "bytes": p.stat().st_size})
        for p in sorted(ROOT.rglob("*")):
            rel = p.relative_to(ROOT)
            if not p.is_file() or set(rel.parts) & EXCLUDE_DIRS or p.suffix.lower() in EXCLUDE_SUFFIX:
                continue
            top = rel.parts[0]
            if top in ("workspace", "reports") or p.name.endswith(".log") or p.name in (".env",):
                continue
            add(p, "visual-mastery-engine/" + rel.as_posix())
        for p in sorted(audit.rglob("*")):
            if p.is_file():
                add(p, "visual-mastery-engine/audit/" + p.relative_to(audit).as_posix())
        # real-source evidence: hashes/PTS indexes and surveys only — NEVER decoded source pixels or MP4 bytes
        wr = workspace.root
        for p in sorted(wr.rglob("*")):
            rel = p.relative_to(wr).as_posix()
            if not p.is_file():
                continue
            keep = (rel.startswith("frames/") and (rel.endswith("index.jsonl.gz") or rel.endswith("index_summary.json") or rel.endswith("film_survey.json")
                                                     or rel.endswith("navigation_candidates.json"))) or \
                   rel in ("state/SOURCE_LOCK.json", "state/FRAME_INDEX_SUMMARY.json", "state/STATE.json")
            if keep:
                add(p, "visual-mastery-engine/workspace/" + rel)
        spec_files = [p for p in sorted(SPEC.rglob("*")) if p.is_file() and p.suffix.lower() != ".zip" and "__pycache__" not in p.parts]
        for p in spec_files:
            add(p, "Visual_Mastery_Engine_Build_Spec_v1_3/" + p.relative_to(SPEC).as_posix())
        man = {"generated_at": now_iso(), "files": files, "excluded_policy": {"dirs": sorted(EXCLUDE_DIRS), "suffixes": list(EXCLUDE_SUFFIX),
                                                                             "never_included": ["source MP4 bytes", "decoded source frame PNGs (sixth witness packet)",
                                                                                                "RUNWARE_API_KEY / any secret", ".venv", "node_modules"]}}
        z.writestr("SHA256_MANIFEST.json", json.dumps(man, indent=1))
    os.replace(tmp_zip, out_zip)
    check = verify_zip(out_zip)
    return {"zip": str(out_zip), "sha256": sha256_file(out_zip), "files": len(files), "zip_self_check": check,
            "requirement_totals": matrix["totals"], "pytest_outcomes": outcomes}


def verify_zip(p: Path) -> dict:
    """B35 / ADD25-A01: contains repo+tests+audit; no MP4/keys/decoded source frames."""
    import re
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        bad_media = [n for n in names if n.lower().endswith((".mp4", ".mov", ".mkv"))]
        witness = [n for n in names if "sixth_witness_packet" in n]
        secret = []
        for n in names:
            if z.getinfo(n).file_size < 5_000_000:
                b = z.read(n)
                if re.search(rb"RUNWARE_API_KEY\s*=\s*\S{8,}", b) or re.search(rb"Bearer\s+[A-Za-z0-9_\-]{24,}", b):
                    secret.append(n)
    required = ["visual-mastery-engine/vme/compiler/compiler.py", "visual-mastery-engine/tests/test_compiler_authority.py",
                "visual-mastery-engine/audit/REQUIREMENT_MATRIX.json", "visual-mastery-engine/audit/TEST_RESULTS.json", "SHA256_MANIFEST.json"]
    return {"media_files": bad_media, "decoded_source_frames": witness, "secret_hits": secret,
            "required_present": all(r in names for r in required), "ok": not bad_media and not witness and not secret and all(r in names for r in required)}


def _ver(tool: str, flag: str = "--version") -> str:
    try:
        return subprocess.run([tool, flag], capture_output=True, text=True, timeout=30).stdout.splitlines()[0]
    except Exception:
        return "unavailable"
