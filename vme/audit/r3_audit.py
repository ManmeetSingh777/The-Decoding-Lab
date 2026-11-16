"""R3 final independent-audit builder → G:\\The Decoding Lab\\VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip

Refuses to run on a dirty tree (every result must belong to ONE committed HEAD). Steps, all offline / simulated, no paid call,
no source upload, no source film bytes or decoded source frames in the ZIP:
  1. re-run the R3 package's INDEPENDENT_REDTEAM.py, 29 reference guards and 5 live-boundary tests (AFTER logs; baseline BEFORE logs
     are the committed evidence/r3_baseline/*);
  2. drive a fresh two-actor canary (S0→S9) and extract identity / state / motion / AV / capture / ledger / causality evidence;
  3. run the mutation suite against the final code (using that canary for the canary-bound mutants);
  4. run the FULL repo test suite and the FULL suite inside a fresh extraction of `git archive HEAD`, in parallel, separate basetemps;
  5. write IMPLEMENTATION_MAP / CAPABILITY_VERDICT / GAPS docs, DELTA.patch vs the pre-R3 base, SHA256 manifest, and zip.

    python -m vme.audit.r3_audit --out "G:/The Decoding Lab/VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip"
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R3_PKG = ROOT.parent / "_r3_input" / "independent_vme_repair_r3"
R3_ZIP = ROOT.parent / "VME_V13_ONE_PASS_END_TO_END_REPAIR_R3.zip"
PRE_R3_BASE = "516af70"
PY = sys.executable
MEDIA_OK = {"integrated.mp4", "integrated_video_only.mp4"}          # ORIGINAL synthetic canary renders, never source media
# assembled at runtime so this source (and DELTA.patch, which contains it) never matches its own secret scan
_SECRET_MARKERS = tuple("".join(x) for x in (("sk-", "ant-", "api"), ("RUNWARE_", "API_KEY", "="), ("x-", "api-", "key:")))
SPEC = ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3"


def _git(*a) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def _sha(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _w(base: Path, rel: str, obj) -> Path:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1, default=str), encoding="utf-8")
    return p


def _rm(p: Path) -> None:
    def force(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if p.exists():
        for link in p.rglob("node_modules"):
            if link.is_symlink() or os.path.isjunction(link):
                try:
                    link.unlink()
                except OSError:
                    os.rmdir(link)
        shutil.rmtree(p, onexc=force)


def _run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 900) -> dict:
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return {"cmd": cmd, "cwd": str(cwd), "returncode": p.returncode, "seconds": round(time.time() - t0, 1), "stdout": p.stdout, "stderr": p.stderr}


# --------------------------------------------------------------------------------------------- 1. independent / reference / live
def independent_logs(out: Path) -> dict:
    env = {"PYTHONPATH": str(ROOT)}
    res = {"redteam": _run([PY, str(R3_PKG / "INDEPENDENT_REDTEAM.py")], R3_PKG, env),
           "reference_guards": _run([PY, "-m", "unittest", "-v", "test_reference_guards"], R3_PKG, env),
           "live_boundary": _run([PY, "-m", "unittest", "-v", "test_archived_wiring"], R3_PKG, env)}
    for k, name in (("redteam", "INDEPENDENT_REDTEAM_ORIGINAL"), ("reference_guards", "REFERENCE_GUARDS"), ("live_boundary", "LIVE_BOUNDARY")):
        _w(out, f"REDTEAM_AND_GUARDS/{name}_AFTER.log", res[k]["stdout"] + res[k]["stderr"])
    for f in (ROOT / "evidence" / "r3_baseline").glob("*.log"):           # BEFORE = pre-patch code (committed baseline)
        shutil.copy(f, out / "REDTEAM_AND_GUARDS" / f"{f.stem.replace('_BASELINE', '')}_BEFORE.log")
    summ = {k: {"returncode": v["returncode"], "tail": (v["stdout"] + v["stderr"]).strip().splitlines()[-3:]} for k, v in res.items()}
    _w(out, "REDTEAM_AND_GUARDS/SUMMARY.json", {"after_on_final_commit": summ, "before": "evidence/r3_baseline (pre-patch code)",
                                               "r3_package_zip_sha256": _sha(R3_ZIP) if R3_ZIP.exists() else "ABSENT"})
    return summ


# --------------------------------------------------------------------------------------------- 2. two-actor canary
def drive_canary(root: Path) -> dict:
    from ..testing.drill import build_drill_workspace, drill_providers, drive, enable_network_flag, two_actor_brief, two_actor_unseen_brief, DRILL_HUMAN
    from ..loop.human import add_brief
    from ..state.workspace import Workspace
    enable_network_flag()
    build_drill_workspace(root)
    add_brief(Workspace(root / "ws").ensure(), two_actor_brief(), added_by=DRILL_HUMAN)
    ws = Workspace(root / "ws").ensure()
    prov, client = drill_providers(root)
    t0 = time.time()
    out = drive(ws, prov, run_id="REAL-CANARY", families=["keeper", "moth"], anchor_brief_id="BRIEF-CANARY-2ACTOR",
                unseen_brief=two_actor_unseen_brief, max_rounds=40)
    return {"ws": ws, "out": out, "seconds": round(time.time() - t0, 1), "billed_simulated": client.billed_requests(),
            "duplicate_creates": client.duplicate_creates()}


def _rel(obj, root: Path):
    s = json.dumps(obj, default=str)
    for r in {str(root), str(root).replace("\\", "\\\\"), root.as_posix()}:
        s = s.replace(r, "<canary_root>")
    return json.loads(s)


def canary_evidence(out: Path, root: Path, drv: dict) -> dict:
    from ..vision.protocol import P0, PROTOCOL_SHA
    from ..render.motion_program import compile_event_program
    from ..style.coverage import OriginalScope
    ws = drv["ws"]
    st = ws.store()
    o: dict = {s: (st.get("LoopTransition", f"REAL-CANARY:{s}") or {}).get("outputs") or {} for s in ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9")}
    prog = st.get("EventProgram", "REAL-CANARY")
    jobs = {r["job_id"]: r for r in st.list("CompiledImageJob")}
    brief = st.get("OriginalBrief", "BRIEF-CANARY-2ACTOR")["brief"]
    cap = st.get("CapabilityVerdict", "REAL-CANARY")
    sled, pled = st.get("SourceArtLedger", "REAL-CANARY"), st.get("ProductionCoverageLedger", "REAL-CANARY")
    dossiers = st.list("CharacterArtDossier")
    st.close()
    pack = json.loads(Path(o["S7"]["pack"]).read_text(encoding="utf-8"))
    C = "CHARACTER_AND_MULTIACTOR_TEST"
    M = "MOTION_CAMERA_AV_TEST"
    _w(out, f"{C}/BRIEF_CANARY_2ACTOR.json", brief)
    _w(out, f"{C}/RUN_LOG.json", _rel({"log": drv["out"]["log"], "result": drv["out"]["result"], "seconds": drv["seconds"],
                                        "simulated_billed_requests": drv["billed_simulated"], "duplicate_creates": drv["duplicate_creates"]}, root))
    per_actor = {}
    for a in ("keeper", "moth"):
        r = o["S5"][f"n_canonical_character@{a}"]
        j = jobs.get(r["job_id"], {})
        per_actor[a] = {"canonical_sha256": r["sha"], "job_id": r["job_id"], "identity_slots": r["identity_slots"],
                        "selected_decisions": r["selected_decisions"], "clause_ids": r["clause_ids"],
                        "excluded_other_actor_decisions": (j.get("trace") or {}).get("excluded_other_actor_decisions"),
                        "positive_prompt": (j.get("payload") or {}).get("positivePrompt"), "reference_shas": r.get("reference_shas")}
    _w(out, f"{C}/PER_ACTOR_CANONICAL_JOBS.json", per_actor)
    canon = {a: v["sha256"] for a, v in pack["canonical_by_actor"].items()}
    states = {k: {"actor_id": v["actor_id"], "sha256": v["sha256"], "identity_source_sha256": v["identity_source_sha256"],
                  "bound_to_own_canonical": v["identity_source_sha256"] == canon[v["actor_id"]], "clause_ids": v.get("clause_ids"),
                  "contact": v.get("contact")} for k, v in pack["states"].items()}
    _w(out, f"{C}/STATE_IDENTITY_AND_CONTACTS.json", {"canonical_by_actor": canon, "distinct": len(set(canon.values())) == len(canon),
                                                      "states": states, "contacts": o["S8"]["contacts"], "method": pack["method"],
                                                      "method_limits": pack["method_limits"], "dossiers": [d.get("dossier_id") for d in dossiers]})
    for v in list(pack["canonical_by_actor"].values()) + list(pack["states"].values()) + [pack["world_plate"]]:
        p = Path(v["path"])
        if p.exists():
            shutil.copy(p, out / C / f"{v.get('actor_id') or 'world'}_{v['kind']}_{v['sha256'][:12]}.png")
    _w(out, f"{M}/EVENT_PROGRAM.json", prog)
    _w(out, f"{M}/S8_RENDER_AND_AV.json", _rel(o["S8"], root))
    _w(out, f"{M}/S9_HELDOUT.json", _rel(o["S9"], root))
    mp4 = Path(o["S8"]["mp4"])
    if mp4.exists():
        shutil.copy(mp4, out / M / "integrated.mp4")
        pr = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4)], ROOT)
        _w(out, f"{M}/FFPROBE.json", pr["stdout"] or pr["stderr"])
    # capture index: what was ACTUALLY sent (local journal), never the model reply
    caps = []
    for p in sorted((ws.root / "providers" / "anthropic").rglob("task_*.json")):
        j = json.loads(p.read_text(encoding="utf-8"))
        m = j.get("manifest") or {}
        sysx = m.get("system") or ""
        caps.append({"task": p.stem, "pass_id": m.get("pass_id"), "kind": m.get("kind"), "request_sha": m.get("request_sha"),
                     "system_sha256": __import__("hashlib").sha256(sysx.encode()).hexdigest(), "carries_P0": P0[:80] in sysx,
                     "carries_protocol_sha": PROTOCOL_SHA in sysx, "carries_own_pass": f"pass={m.get('pass_id')}" in sysx,
                     "image_bytes_sha256": [b.get("image_bytes_sha256") for b in m.get("byte_manifest") or []],
                     "source_shas": m.get("source_shas"), "evidence_status": j.get("evidence_status")})
    img = [{"job_id": k, "node_id": v["node_id"], "payload_sha256": __import__("hashlib").sha256(json.dumps(v["payload"], sort_keys=True).encode()).hexdigest(),
            "clause_ids": (v.get("trace") or {}).get("clause_ids"), "selected_decisions": (v.get("trace") or {}).get("selected_decisions"),
            "actor_scope": (v.get("trace") or {}).get("actor_scope"), "ref_shas": v.get("ref_shas")} for k, v in jobs.items()]
    _w(out, "REAL_REQUEST_CAPTURE_INDEX.json", {"transport": "SIMULATED (no socket, no paid call)", "source_requests": caps,
                                                "all_carry_P0_and_own_pass": all(c["carries_P0"] and c["carries_own_pass"] for c in caps) and bool(caps),
                                                "image_requests": img, "motion_program_sha": prog["program_sha"]})
    _w(out, "SOURCE_AND_PRODUCTION_COVERAGE.json", {"note": "two SEPARATE ledgers; never unioned. Source ledger here is over SYNTHETIC drill films.",
                                                    "SourceArtObservation": _rel(sled, root), "ProductionDecisionCoverage": pled})
    _w(out, "CAPABILITY_STATUSES_CANARY.json", cap)

    # causal checks on the frozen canary skill + program (pure, local)
    decs = json.loads((Path(o["S4"]["skill_folder"]) / "decisions.json").read_text(encoding="utf-8"))
    scope = OriginalScope(scope_id=brief["brief_id"], **brief["scope"])

    def prog_of(dd, b=brief):
        return compile_event_program(decisions=dd, scope=scope, brief=b, pack=pack, width=320, height=180, scale=0.25)
    base = prog_of(decs)
    rows = [{"check": "baseline reproduces rendered program", "ok": base["program_sha"] == prog["program_sha"]}]
    from ..util import Blocked
    for t in base["tracks"]:
        if t["kind"] == "ACTOR_DRAWING_STATE":
            continue
        owners = {t["owner_decision_id"], *t.get("co_owner_decision_ids", [])}
        try:
            prog_of([d for d in decs if d["decision_id"] not in owners])
            rows.append({"check": f"ablate all owners of {t['kind']}/{t.get('actor_id')}", "ok": False, "result": "NO_BLOCK"})
        except Blocked as e:
            rows.append({"check": f"ablate all owners of {t['kind']}/{t.get('actor_id')}", "ok": e.code == "MOTION_TRACK_UNOWNED", "result": e.code,
                         "owners": sorted(owners)})
    import copy
    moth = next(t for t in base["tracks"] if t["kind"] == "ACTOR_ACTING" and t["actor_id"] == "moth")
    d2 = copy.deepcopy(decs)
    for d in d2:
        if d["decision_id"] == moth["owner_decision_id"]:
            for b in d["branches"]:
                if (b.get("motion_program") or {}).get("track_kind") == "ACTOR_ACTING":
                    b["motion_program"]["method"] = "HOLD_THEN_MOVE"
    try:
        p2 = prog_of(d2)
        k2 = {(t["kind"], t.get("actor_id")): t["keyframes"] for t in p2["tracks"] if "keyframes" in t}
        k1 = {(t["kind"], t.get("actor_id")): t["keyframes"] for t in base["tracks"] if "keyframes" in t}
        rows.append({"check": "counterfactual: moth acting method → HOLD_THEN_MOVE changes only moth keyframes",
                     "ok": k2[("ACTOR_ACTING", "moth")] != k1[("ACTOR_ACTING", "moth")] and k2[("ACTOR_ACTING", "keeper")] == k1[("ACTOR_ACTING", "keeper")]})
    except Blocked as e:                 # co-owner disagreement is itself the correct refusal
        rows.append({"check": "counterfactual: moth acting method change", "ok": e.code == "CONFLICTING_MOTION_OWNERS", "result": e.code})
    b3 = copy.deepcopy(brief)
    b3["shot_plan"]["events"][1]["from"] = 35
    p3 = prog_of(decs, b3)
    rows.append({"check": "counterfactual: moth event moved 25→35 moves its cue and redraw", "ok": 35 in [c["frame"] for c in p3["audio_cues"]]
                 and next(t for t in p3["tracks"] if t["kind"] == "ACTOR_DRAWING_STATE" and t["actor_id"] == "moth")["start_frame"] == 35})
    rows.append({"check": "image: per-actor jobs select disjoint actor-only decisions",
                 "ok": not (set(per_actor["keeper"]["selected_decisions"]) & set(per_actor["keeper"]["excluded_other_actor_decisions"] or []))
                 and bool(set(per_actor["keeper"]["excluded_other_actor_decisions"] or []) & set(per_actor["moth"]["selected_decisions"]))})
    _w(out, "CONDITIONED_SKILL_CAUSALITY.json", {"scope": "canary skill + event program, local pure functions; artistic quality UNPROVEN",
                                                 "checks": rows, "all_ok": all(r["ok"] for r in rows)})
    return {"completed": drv["out"]["result"].get("completed_through"), "causality_ok": all(r["ok"] for r in rows),
            "capture_ok": all(c["carries_P0"] and c["carries_own_pass"] for c in caps) and bool(caps), "n_source_requests": len(caps),
            "av": o["S8"]["av"]["status"], "motion": o["S8"]["motion"], "tracks": [(t["kind"], t["actor_id"], t["method"]) for t in o["S8"]["tracks"]],
            "canonical_distinct": len(set(canon.values())) == 2, "states_bound": all(s["bound_to_own_canonical"] for s in states.values()),
            "capability": cap}


# --------------------------------------------------------------------------------------------- 4. suites
def _suite(repo: Path, tag: str, work: Path) -> subprocess.Popen:
    raw = work / f"raw_{tag}.json"
    env = {**os.environ, "VME_TEST_RESULTS": str(raw), "PYTHONPATH": str(repo), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("VME_CANARY_REUSE_ROOT", None)
    env.pop("VME_ALLOW_NETWORK", None)
    log = open(work / f"pytest_{tag}.log", "w", encoding="utf-8")
    return subprocess.Popen([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", "--basetemp", str(work / f"bt_{tag}"), "tests"],
                            cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)


def _suite_summary(work: Path, tag: str, seconds: float, rc: int) -> dict:
    raw = work / f"raw_{tag}.json"
    res = json.loads(raw.read_text(encoding="utf-8"))["results"] if raw.exists() else []
    oc: dict = {}
    for r in res:
        oc[r["outcome"]] = oc.get(r["outcome"], 0) + 1
    tail = (work / f"pytest_{tag}.log").read_text(encoding="utf-8", errors="replace").strip().splitlines()
    return {"tag": tag, "returncode": rc, "seconds": round(seconds, 1), "outcomes": oc, "summary_line": tail[-1] if tail else "",
            "failures": [{"nodeid": r["nodeid"], "longrepr": r["longrepr"]} for r in res if r["outcome"] == "failed"],
            "skipped": [r["nodeid"] for r in res if r["outcome"] == "skipped"], "cases": res}


def static_checks(repo: Path) -> dict:
    return {k: {kk: v[kk] for kk in ("returncode", "seconds")} | {"tail": (v["stdout"] + v["stderr"])[-1500:]} for k, v in {
        "pyflakes": _run([PY, "-m", "pyflakes", "vme", "tests"], repo), "compileall": _run([PY, "-m", "compileall", "-q", "vme"], repo),
        "mypy": _run([PY, "-m", "mypy", "vme", "--ignore-missing-imports"], repo, timeout=1800),
        "node_check": _run(["node", "--check", "render/remotion/render.mjs"], repo)}.items()}


def _ver(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.splitlines()[0]
    except Exception as e:                # noqa: BLE001
        return f"UNAVAILABLE ({e.__class__.__name__})"


# --------------------------------------------------------------------------------------------- 5. docs
F_MAP = [
    ("F01", "vision/contracts.py:validate_packet_response (NO_TYPED_SOURCE_VISUAL_FACTS, ARTISTIC_FRAME_OBSERVATIONS_INSUFFICIENT); runner keeps NEEDS_REINSPECTION",
     "test_r3_contract::test_f01_*; M11,M12"),
    ("F02", "vision/contracts.py boundary reconciliation of structured active_objects / open_events", "test_f02_*; M13"),
    ("F03", "style/coverage.py:_owner_for — branch must match the choice's conditions", "test_f03_*"),
    ("F04", "style/authoring.py:authorize_answer — cited ⊆ submitted manifest; source/PTS/region checks; controller refuses self-authorized ids",
     "test_f04_f10_* (9 causes), test_f04_controller_*; M01–M03"),
    ("F05", "authoring.author_decision covers() joint tuple + human INVARIANCE_REVIEW; CONFLICTING_EQUALLY_APPLICABLE_BRANCHES; motion CONFLICTING_MOTION_OWNERS",
     "test_f05_*, test_f13_conflicting_*; M04,M05,M19,M25"),
    ("F06", "vision/dispatch.py:prepare_verified_request/submit_source_request — P0+Pn system, typed byte manifest; adapter refuses unverified/different/bytes",
     "test_f06_*, provider_contracts manifest tests, canary capture index; M15,M16"),
    ("F07", "request_sha over system/user/images/provider/parser/preprocess; runner STALE_SEMANTIC_PACKET_REQUIRES_NEW_ID; stage keys carry protocol hashes",
     "test_f07_*; M14"),
    ("F08", "authoring._reference_policy REQUIRED/TEXT_ONLY_DEMONSTRATED/NOT_APPLICABLE/UNKNOWN; compiler PROVIDER_REF_LIMIT; distinct role bytes",
     "test_f08_* (6 causes + distinct roles); M06"),
    ("F09", "runner status RESPONSE_IDENTITY_BOUND (identity, not understanding); coverage artistic_status ARTISTIC_CLAIM_UNVERIFIED", "test_f09_*"),
    ("F10", "author_decision owner_stage must be STYLE_CONDITIONS + sufficiency for every caller", "test_f04_f10_*"),
    ("F11", "style/source_ledger.py validate_character_art_study (A29), SourceArtObservation ledger, S4 SOURCE_ART_LEDGER_OPEN gate; dossier gate",
     "test_f11_* (3); M08,M09,M10"),
    ("F12", "S5 per-actor canonical jobs with compiler actor_scope (decisions owned only by other actors excluded, recompile keeps scope); "
            "ACTOR_IDENTITY_COLLISION; S8 STATE_IDENTITY_ALIASES_ANOTHER_ACTOR; capsule rehearsal replays every actor",
     "test_f12_*, canary identity/continuity/recompile/capsule; M17,M27,M28"),
    ("F13", "render/motion_program.py compile_event_program: skill-owned ACTOR_ACTING/CAMERA/ATTENTION/WORLD/AUDIO/DRAWING_STATE tracks, no default",
     "test_f13_* (3), canary motion/ablation/counterfactual; M18,M19"),
    ("F14", "reference/audio.py local source-audio study → AUDIO_SIGNAL witnesses bound to aligned full-frame parent; approved original sound; mux; AV gate",
     "test_f14_* (3), canary AV; M07,M21–M23"),
    ("F15", "render/renderer.py TECHNICAL_RENDER_FAILED fatal; diagnostic scope separate", "test_f15_*; M20"),
    ("F16", "review/qualification.py review_source_claim — native refutation never promotes", "test_f16_*"),
    ("F17", "qualification.capability_verdict — 16 independent statuses; still-only never qualifies motion/AV", "test_f17_*, canary held-out; M26"),
    ("F18", "real.py _budgeted_targets / _split_truncated (SUPERSEDED_BY_SPLIT), no lost targets", "test_f18_*; M24"),
]
BLOCKERS = [
    ("1 native frames indexed ≠ interpreted", "status vocabulary INDEXED / RESPONSE_IDENTITY_BOUND / SOURCE_ART_REVIEWED; ledger counts typed observations only",
     "OPEN for real films (no real frame was sent)"),
    ("2 overview-level events", "SourceArtObservation per frame/PTS/relation; NEEDS_SOURCE_REINSPECTION while gaps open", "OPEN (needs real investigation)"),
    ("3 shallow reports stay candidate", "claim_state METHOD_CANDIDATE / UNRESOLVED; source_art_truth UNREVIEWED without human SOURCE_ART_REVIEW", "ENFORCED"),
    ("4 no executable high-end method", "decisions → clauses/motion programs → compiler/event program consumers with ablation", "WIRED offline; quality UNPROVEN"),
    ("5 hypotheses never auto-qualified", "skill_status SKILL_CANDIDATE; qualification separate", "ENFORCED"),
    ("6 AV unlearned", "local energy-onset study + AV gate; meaning/narration BLOCKED:AUDIO_MEANING_UNSTUDIED", "PARTIAL (timing only)"),
    ("7 camera vs actor vs redraw / choreography", "separate tracks with owners; CAMERA_VS_REDRAW_UNRESOLVED; conflicting owners refused", "WIRED offline"),
    ("8 conditional grammar", "joint condition coverage, contrast witnesses, invariance only by human review", "ENFORCED; real contrasts OPEN"),
    ("9 per-part/state coverage", "two separate ledgers (source-art vs production)", "ENFORCED"),
    ("10 semantic continuity/source identity", "content-addressed requests, stale-semantic refusal, capsule cold restore incl. per-actor jobs", "OFFLINE_VERIFIED"),
    ("11 certification ≠ proof", "independent capability statuses; artistic gates need humans", "ENFORCED"),
    ("12 no qualified original AV film", "ORIGINAL_AUDIOVISUAL_QUALIFIED unreachable offline", "OPEN"),
]


def write_docs(out: Path, ctx: dict) -> None:
    head, mut, can = ctx["head"], ctx["mutation"]["summary"], ctx["canary"]
    rp, fr = ctx["repo"], ctx["fresh"]
    lines = ["# IMPLEMENTATION_MAP — R3 F01–F18 and 12 recurring blockers", "", f"Commit `{head}` (branch r3-repair). Every row is "
             "backed by tests in the repo suite and, where listed, a mutant that the tests kill (`MUTATION_RESULTS.json`).", "",
             "| ID | Implementation (file:function) | Tests / mutants |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in F_MAP]
    lines += ["", "## 12 recurring blockers", "", "| Blocker | Mechanism | Status |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in BLOCKERS]
    _w(out, "IMPLEMENTATION_MAP.md", "\n".join(lines) + "\n")
    eng = (rp["outcomes"].get("failed", 0) == 0 and fr["outcomes"].get("failed", 0) == 0 and mut.get("SURVIVED", 1) == 0
           and can["causality_ok"] and can["capture_ok"] and can["completed"] == "S9")
    yn = lambda b: "YES" if b else "NO"
    v = ["# CAPABILITY_VERDICT", "", f"Commit `{head}`. Independent answers; nothing is averaged.", "",
         "| Question | Answer | Basis |", "|---|---|---|",
         f"| Engineering wired (offline, simulated transports) | {yn(eng)} | repo {rp['outcomes']}, fresh {fr['outcomes']}, mutants {mut}, canary S9 + causality |",
         "| Source evidence ready (15+1 real films investigated) | NO | no real frame/audio was sent; 15+1 files and sixth boundaries not confirmed in this run |",
         "| Visual truth confirmed (human SOURCE_ART_REVIEW) | NO | source_art_truth UNREVIEWED |",
         "| Skill qualified (SKILL_TRANSFER_QUALIFIED) | NO | canary skill is SKILL_CANDIDATE from SIMULATED answers |",
         "| Original still art (real provider, human-approved) | NO | Runware transport simulated; images are placeholders |",
         "| Character animation (professional quality) | NO | WHOLE_STATE_SWAP over approved states; quality UNPROVEN |",
         "| Sound (meaningful source-learned AV) | NO | onset timing only; AUDIO_MEANING_UNSTUDIED; cue is a locally synthesized original tone |",
         "| 2-minute held-out original AV film | NO | still-only held-out; animated transfer NOT_ATTEMPTED |", "",
         "## 16 individual capability statuses (canary run)", "", "```json", json.dumps(can["capability"], indent=1, default=str), "```", ""]
    _w(out, "CAPABILITY_VERDICT.md", "\n".join(v))
    g = ["# HONEST GAPS AND UNRESOLVED RESOURCES", "",
         "## External resources / human decisions (true stops)",
         "1. The actual 15 base + 1 special source video files must be confirmed by the user (SHA256s in `SOURCE_FILMS_NOT_INCLUDED.md`); not re-confirmed here.",
         "2. Exact sixth-film special-interval boundaries need human confirmation (drill uses synthetic boundaries only).",
         "3. Paid-call approval: none given. Anthropic vision and Runware image calls require `vme authorize` with the phrase and a spend cap.",
         "4. Third-party source image upload authorization (SOURCE_UPLOAD_CONSENT per film) not granted; no source frame was uploaded.",
         "5. Runware model `runware:400@4` must be user-confirmed with a real probe (`vme provider confirm-runware`).", "",
         "## What this audit does NOT prove",
         "* Any real perception of source art: all VLM answers are SIMULATED deterministic text; they prove routing, refusal and provenance only.",
         "* Artistic quality of any image, character state, motion or sound (UNPROVEN everywhere).",
         "* Audio meaning (narration/music/effects semantics): BLOCKED:AUDIO_MEANING_UNSTUDIED — only local energy onsets are studied.",
         "* Separated-part animation (arms/IK/hidden surfaces): method is WHOLE_STATE_SWAP; no verified segmentation/inpainting capability.",
         "* Held-out animated transfer: NOT_ATTEMPTED; ORIGINAL_AUDIOVISUAL_QUALIFIED is unreachable offline.",
         "* The co-owned motion tracks in the canary are corroborated only by agreeing SIMULATED decisions.", "",
         "## Known engineering limits", "* Simulated transports cannot detect provider-side behaviour changes; a bounded real canary is the next validation.",
         "* Mutation suite covers 28 named guards; it is not exhaustive mutation testing of every line.", ""]
    if rp["failures"] or fr["failures"]:
        g += ["## Test failures on the final commit", ""] + [f"* {f['nodeid']}" for f in rp["failures"] + fr["failures"]]
    _w(out, "GAPS_AND_UNRESOLVED.md", "\n".join(g) + "\n")


# --------------------------------------------------------------------------------------------- build
def build(out_zip: Path, keep: bool = False) -> dict:
    if _git("status", "--porcelain").strip():
        raise SystemExit("REFUSED: working tree is dirty; commit first so every result belongs to one HEAD\n" + _git("status", "--short"))
    head = _git("rev-parse", "HEAD").strip()
    # the build directory lives OUTSIDE the repo: the repo suite scans ROOT and must never see the fresh suite's temp files
    b = ROOT.parent / "_vme_r3_audit_build"
    _rm(b)
    _rm(ROOT / "audit_build_r3")
    out, work = b / "audit", b / "work"
    out.mkdir(parents=True)
    work.mkdir()
    ctx: dict = {"head": head, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    print("independent/reference/live logs", flush=True)
    ctx["independent"] = independent_logs(out)
    # fresh extraction of the committed tree
    arch = work / "source_HEAD.zip"
    subprocess.run(["git", "archive", "--format=zip", "-o", str(arch), "HEAD"], cwd=ROOT, check=True)
    fx = work / "fresh" / "visual-mastery-engine"
    with zipfile.ZipFile(arch) as z:
        z.extractall(fx)
    # the authoritative spec is a SIBLING of the repo (not in git); the fresh environment gets the same sibling copy (no ZIPs)
    if SPEC.exists():
        shutil.copytree(SPEC, fx.parent / SPEC.name, ignore=shutil.ignore_patterns("*.zip", "__pycache__"))
    nm = ROOT / "render" / "remotion" / "node_modules"
    if nm.exists() and (fx / "render" / "remotion").exists():
        subprocess.run(["cmd", "/c", "mklink", "/J", str(fx / "render" / "remotion" / "node_modules"), str(nm)], capture_output=True)
    print("suites started (repo + fresh, parallel)", flush=True)
    t0 = time.time()
    procs = {"repo": _suite(ROOT, "repo", work), "fresh": _suite(fx, "fresh", work)}
    print("canary", flush=True)
    croot = work / "canary"
    drv = drive_canary(croot)
    ctx["canary"] = canary_evidence(out, croot, drv)
    print("mutations", flush=True)
    from .mutation import run as run_mut
    ctx["mutation"] = run_mut(out / "MUTATION_RESULTS.json", canary_root=str(croot))
    done = {}
    for tag, p in procs.items():
        rc = p.wait()
        done[tag] = _suite_summary(work, tag, time.time() - t0, rc)
        shutil.copy(work / f"pytest_{tag}.log", out / f"PYTEST_{tag.upper()}.log")
        _w(out, f"TEST_RESULTS_{tag.upper()}.json", done[tag])
    ctx["repo"], ctx["fresh"] = done["repo"], done["fresh"]
    ctx["static"] = static_checks(ROOT)
    _w(out, "STATIC_CHECKS.json", ctx["static"])
    plat = {"os": platform.platform(), "python": sys.version, "node": _ver(["node", "--version"]), "ffmpeg": _ver(["ffmpeg", "-version"]),
            "pip_freeze": _run([PY, "-m", "pip", "freeze"], ROOT)["stdout"].splitlines()}
    tests_txt = [f"commit: {head}", f"branch: {_git('rev-parse', '--abbrev-ref', 'HEAD').strip()}",
                 f"fresh extraction: git archive HEAD (sha256 {_sha(arch)}) extracted to a new directory; node_modules junction (excluded)",
                 f"repo suite:  {done['repo']['summary_line']}  outcomes={done['repo']['outcomes']}  rc={done['repo']['returncode']}",
                 f"fresh suite: {done['fresh']['summary_line']}  outcomes={done['fresh']['outcomes']}  rc={done['fresh']['returncode']}",
                 f"mutations: {ctx['mutation']['summary']}", "independent red-team / reference guards / live boundary (after): "
                 + json.dumps({k: v["returncode"] for k, v in ctx["independent"].items()}),
                 "static: " + json.dumps({k: v["returncode"] for k, v in ctx["static"].items()}),
                 f"canary: completed_through={ctx['canary']['completed']} av={ctx['canary']['av']} motion={ctx['canary']['motion']} "
                 f"causality_ok={ctx['canary']['causality_ok']} capture_ok={ctx['canary']['capture_ok']}",
                 "", "failures:"] + [f"  {f['nodeid']}" for f in done["repo"]["failures"] + done["fresh"]["failures"]] + \
                ["", "skipped:"] + [f"  {s}" for s in done["repo"]["skipped"] + done["fresh"]["skipped"]]
    _w(out, "TESTS_FINAL_COMMIT.txt", "\n".join(tests_txt) + "\n")
    _w(out, "PLATFORM.json", plat)
    _w(out, "SOURCE_REVISION.json", {"head": head, "log": _git("log", "--oneline", "-15").splitlines(), "pre_r3_base": PRE_R3_BASE,
                                     "files_sha256": {p.relative_to(ROOT).as_posix(): _sha(p) for p in sorted((ROOT / "vme").rglob("*.py"))}})
    _w(out, "DELTA.patch", _git("diff", f"{PRE_R3_BASE}..HEAD"))
    _w(out, "DELTA_STAT.txt", _git("diff", "--stat", f"{PRE_R3_BASE}..HEAD"))
    shutil.copy(arch, out / "SOURCE_AT_HEAD.zip")
    write_docs(out, ctx)
    for f in ("R3_PROMPT_VERBATIM.txt", "R3_LINEAGE_GRAPH_PRE_PATCH.md", "R3_WORK_IN_PROGRESS_STATUS.md"):
        if (ROOT / "docs" / f).exists():
            shutil.copy(ROOT / "docs" / f, out / f)
    # assemble with a self-check: no source films, no decoded source frames, no secrets
    files: list[dict] = []
    bad: list[str] = []
    tmp = out_zip.with_suffix(".tmp.zip")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for fp in sorted(out.rglob("*")):
            if not fp.is_file():
                continue
            arc = fp.relative_to(out).as_posix()
            if fp.suffix.lower() in (".mp4", ".mov", ".mkv", ".wav") and fp.name not in MEDIA_OK:
                bad.append(arc)
                continue
            z.write(fp, arc)
            files.append({"path": arc, "sha256": _sha(fp), "bytes": fp.stat().st_size})
        z.writestr("SHA256_MANIFEST.json", json.dumps({"commit": head, "files": files, "never_included": [
            "source film bytes", "decoded source frames", "API keys / secrets", ".venv", "node_modules", "paid provider media"],
            "excluded_media": bad}, indent=1))
    secret_hits = []
    with zipfile.ZipFile(tmp) as z:
        for n in z.namelist():
            if n.endswith((".json", ".md", ".txt", ".log", ".patch")):
                t = z.read(n).decode("utf-8", "replace")
                if any(k in t for k in _SECRET_MARKERS):
                    secret_hits.append(n)
    if secret_hits:
        tmp.unlink()
        raise SystemExit(f"REFUSED: secret-like strings in {secret_hits}")
    os.replace(tmp, out_zip)
    res = {"zip": str(out_zip), "sha256": _sha(out_zip), "files": len(files), "head": head, "repo": done["repo"]["outcomes"],
           "fresh": done["fresh"]["outcomes"], "mutation": ctx["mutation"]["summary"], "canary": {k: v for k, v in ctx["canary"].items() if k != "capability"},
           "independent": {k: v["returncode"] for k, v in ctx["independent"].items()}, "static": {k: v["returncode"] for k, v in ctx["static"].items()}}
    _w(b, "BUILD_RESULT.json", res)
    if not keep:
        _rm(work)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT.parent / "VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip"))
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    print(json.dumps(build(Path(a.out), a.keep), indent=1, default=str))
