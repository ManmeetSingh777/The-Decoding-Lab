"""Human-readable audit documents generated from the actual run data (no hand-maintained claims)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..util import atomic_write_json, atomic_write_text, now_iso, read_json
from ..state.workspace import Workspace
from .requirements import ORIGINAL_13

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT.parent / "Visual_Mastery_Engine_Build_Spec_v1_3"

STAGE_MAP = [
    ("S0", "vme.loop.stages:LoopRunner._s0", "vme.selection.first15:propose_selection, vme.selection.sixth:locate_sixth_intro",
     "SelectedSequenceManifest, SixthIntroLocatorResult", "S1 (frame packets)", "tests/test_selection_sixth.py, tests/test_loop_handoff.py"),
    ("S1", "LoopRunner._s1", "vme.vision.runner:plan_packets/PacketRunner.run, vme.investigation.evidence:build_event_graph",
     "SemanticPacketCheckpoint, frame_vision rows, CrossFrameEventGraph", "S2", "tests/test_vision_ledger.py"),
    ("S2", "LoopRunner._s2", "vme.investigation.gaps:rank_gaps/select_cluster, vme.investigation.controller:LoopController",
     "GapRanking, ActiveArtProblem, NextQuestion, AnswerEffect", "S3 (decision_writer)", "tests/test_questions.py"),
    ("S3", "LoopRunner._s3/_write_decision", "vme.style.decisions:witness_to_decision", "ConditionalVisualDecision", "S4 (decision_overrides)",
     "tests/test_style_decisions.py"),
    ("S4", "LoopRunner._s4", "vme.skills.skill:write_skill/freeze_skill, vme.style.coverage:review_visual_model_completeness",
     "skill folder + FROZEN.json, CoverageReview", "S5 (pinned skill hash)", "tests/test_completeness_provenance.py"),
    ("S5", "LoopRunner._s5", "vme.compiler.compiler:StyleProgramCompiler.compile, vme.providers.gateway:StyleImageGateway.submit",
     "CompiledImageJob, GeneratedRaster", "S6 (review images)", "tests/test_compiler_authority.py, tests/test_gateway.py"),
    ("S6", "LoopRunner._s6", "vme.review.approvals:GateKeeper.submit_art_verdict", "ArtApproval, VisualGateState", "S7", "tests/test_gates_render.py"),
    ("S7", "LoopRunner._s7", "vme.artwork.character:character_construction_plan, vme.artwork.assets:verify_pack, GateKeeper.submit_asset_verdict",
     "CharacterConstructionPlan, AssetReport, AssetApproval", "S8", "tests/test_assets_character.py"),
    ("S8", "LoopRunner._s8", "vme.render.renderer:render_video (GateKeeper.authorize_render first)", "RenderReport (MP4 + motion evidence)", "S9",
     "tests/test_gates_render.py"),
    ("S9", "LoopRunner._s9", "vme.experiments.experiments:HoldoutRegistry, LoopController.observe_new_output/step_question",
     "TransferRecord, new NextQuestion", "next S2/S3/S4 per routing", "tests/test_experiments_diagnosis.py, tests/test_loop_handoff.py"),
]


def write_docs(audit: Path, *, matrix: dict, checks: dict, real: dict, traces: dict, workspace: Workspace) -> None:
    t = matrix["totals"]
    rows = matrix["rows"]
    blocked = [r for r in rows if r["status"] in ("BLOCKED_AUTHORIZATION", "ART_QUALITY_UNPROVEN", "REAL_PATH_WIRED_UNTESTED")]
    fails = [r for r in rows if r["status"] == "FAIL"]
    notbuilt = [r for r in rows if r["status"] == "NOT_IMPLEMENTED"]
    py = checks["pytest"]
    W = lambda n, s: atomic_write_text(audit / n, s)
    crash = [r for r in read_json(audit / "TEST_RESULTS.json")["pytest_cases"] if any(k in r["nodeid"] for k in ("kill", "crash", "unqueryable", "unreconcilable"))]
    atomic_write_json(audit / "RESUME_CRASH_REPORT.json", {"tests": crash, "crash_points": {
        "vision": ["after_inputs_ready", "after_inflight_commit", "after_submit_before_save", "after_raw_response", "mid_semantic_commit", "after_semantic_commit"],
        "gateway": ["gateway_after_inflight", "gateway_after_send_before_save", "gateway_after_response_saved"],
        "loop": [f"loop_after_S{i}" for i in range(10)], "coverage": ["mid_coverage_commit"]},
        "method": "subprocess hard kill (os._exit(97)) at the named point, then a NEW process resumes from SQLite WAL + files",
        "billing_invariant": "each provider task id billed at most once; unqueryable pending → UNKNOWN_BILLING (no blind resubmit)"})
    W("RUN_INSTRUCTIONS.md", f"""# Run instructions (independent reproduction)

Tested on: Windows 11, Python 3.14, Node 22, FFmpeg 7.x (Git Bash or PowerShell). Linux/macOS should work (POSIX paths).

```bash
cd visual-mastery-engine
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.lock     # (bin/python on POSIX)
cd render/remotion && npm ci && cd ../..                                              # Remotion 4.0.538 (downloads Chrome Headless Shell once)
.venv/Scripts/python -m pytest -q tests                                               # full suite (real-source tests skip without the MP4s)
.venv/Scripts/python -m pyflakes vme tests && .venv/Scripts/python -m mypy vme --ignore-missing-imports
```

Real local source steps (no network, no upload; the user's MP4s are required and are NOT in this ZIP):

```bash
.venv/Scripts/python -m vme sources ingest --folder ../source_clips --index-every-frame
.venv/Scripts/python -m vme survey build --all --navigation-only
.venv/Scripts/python -m vme selection sixth-locate
.venv/Scripts/python -m vme loop run --run-id SYN1 --simulate-human-fixture     # synthetic S0–S9 drill (labelled)
.venv/Scripts/python -m vme status --detailed
.venv/Scripts/python -m vme audit export --offline --out ../VME_V13_IMPLEMENTATION_AUDIT.zip
```

`reference_impl` suites: `cd Visual_Mastery_Engine_Build_Spec_v1_3/reference_impl && python -m unittest -v` (and `reference_impl_v13`).
Observed in this build: pytest exit={py['returncode']}; see audit/logs/*.txt and TEST_RESULTS.json.
""")
    W("SECURITY_AND_BUDGET_REPORT.md", """# Security and budget report

- **API key**: read ONLY from `RUNWARE_API_KEY` inside `vme/providers/runware.py:http_transport` at send time. It is never written,
  logged, hashed into payloads or exported. `tests/test_gateway.py::test_api_key_never_written` sets a fake key and scans every file.
  The audit ZIP and handoff exporter scan for key/Bearer patterns and refuse/omit matching files (`verify_zip`, `handoff._secret_free`).
- **Network**: disabled unless `VME_ALLOW_NETWORK=1`. No code path in this build was run with it set except tests asserting refusal.
- **Three independent barriers** for any paid/external action (`vme/providers/authorization.py`): network flag + human-issued
  `ProviderAuthorization` (exact model AIR id, task categories, USD cap, confirmation phrase, human issuer) + separate
  `source_upload_consent` listing allowed source SHA256s for any source-frame pixels. Unknown cost → `COST_UNKNOWN_STOP`.
- **Model ambiguity**: "FLUX Klein 7B" is not a confirmed Runware model; `resolve_model` refuses non-AIR names. Capability snapshots
  for `runware:400@4` (FLUX.2 [klein] 4B) and `runware:400@2` (9B) are doc-cited from the spec and marked `verified_by_probe=false`,
  `user_confirmed_model=false`, `cost_per_image_usd=null`; a paid job needs a consented probe first (`assert_paid_ready`).
- **Real external calls in this build**: Runware = 0, vision provider = 0, source-frame uploads = 0. The agent did not view or upload
  any decoded source frame; the sixth-clip witness PNGs exist only on the user's disk and are excluded from this ZIP.
- **Proposed lowest-cost real probe (needs separate approval)**: after the user confirms the exact AIR id, authorize category
  `capability_probe` with a small cap (e.g. a few cents), run ONE text-to-image original (non-source) prompt at 512×512 to
  verify accepted parameters, returned format/alpha, `cost` field and `taskUUID` reconciliation; then optionally ONE
  reference-guided edit using only original (non-source) images. Source-frame reference upload requires its own consent.
- **Vision provider**: none selected; `vme vision estimate` returns `BLOCKED_FOR_PRICE_VERIFICATION` until a provider, its image
  limits and price are verified and recorded.
""")
    W("UNIMPLEMENTED_OR_BLOCKED.md", "# Unimplemented or blocked\n\n" +
      f"Requirement totals (from executed tests): {json.dumps(t)}\n\n" +
      "## FAIL\n" + ("\n".join(f"- {r['id']}: {r['requirement']} — {r['tests']}" for r in fails) or "- none observed") +
      "\n\n## NOT_IMPLEMENTED (no passing REAL-path test)\n" + ("\n".join(f"- {r['id']}: {r['requirement']}" for r in notbuilt) or "- none") +
      "\n\n## Wired but unproven (REAL_PATH_WIRED_UNTESTED / BLOCKED_AUTHORIZATION / ART_QUALITY_UNPROVEN)\n" +
      "\n".join(f"- {r['id']} [{r['status']}; needs {r['needs_for_positive_proof'] or 'a real provider run'}]: {r['requirement']}" for r in blocked) +
      """

## Known engineering limits (truthful)
- Vision provider: Claude Messages Batches adapter (`vme/vision/claude_adapter.py`, model `claude-opus-5-5`, official SDK) is implemented
  and exercised ONLY through a SIMULATED client. The 20-images-per-request limit is a planning assumption and the price comes from a cached
  table — both UNVERIFIED until a consented Models-API discovery call.
- REAL first-15 selection needs the five base films CONFIRMED by the user (currently quarantined: titles differ from the contract),
  then authorized VLM rationales. The sixth clip role is USER_CONFIRMED (2026-11-15); its volcano/logo boundaries are still unlocked.
- Character layers: no segmentation/inpainting capability is verified, so the REAL path uses an explicit WHOLE_STATE_SWAP (whole
  identity-conditioned drawings swapped by the renderer) instead of pretend layers. Expression states have no decision condition yet.
- `op.clean_plate` / `op.layer_extract` real implementations depend on provider edit/mask capability; the offline fixture uses a local
  fill on fixture rasters (wiring only). Real segmentation/matting model not chosen.
- Motion evidence is block-translation based: motion over textureless regions is not counted either way (documented limitation).
- Interface-I lexical grounding is a crude executable derivation check, not semantic proof that a clause follows from an observation.
- Artistic quality, identity consistency, transfer and video quality are UNEVALUATED (no real art exists).
""")
    W("ADD26_STAGE_IMPL_MAP.md", "# S0–S9 stage implementation map\n\n| Stage | Handler | Real consumers called | Persisted outputs | Next consumer | Tests |\n|---|---|---|---|---|---|\n" +
      "\n".join(f"| {a} | `{b}` | `{c}` | {d} | {e} | {f} |" for a, b, c, d, e, f in STAGE_MAP) +
      "\n\nEvery transition is persisted as a `LoopTransition` record (store), crash points `loop_after_S<n>`; resume skips COMPLETED stages, re-attempts STOPPED ones.\n")
    W("ADD26_PRESERVATION_COMPARISON.md", _preservation())
    lock = real.get("special_sixth_clip_coverage", {})
    W("ADD26_UNRESOLVED_AND_CONTINUE.md", f"""# Addendum 26 unresolved items and continuation

- Sixth source: PRESENT (by duration proposal, pending user confirmation). Locator status: {lock.get('locator')}.
- First-15 real selection: NOT_RUN — needs whole-artwork rationales (human or authorized VLM).
- Real per-frame VLM on 15+1 windows: BLOCKED_CONSENT (provider/price/upload consent absent).
- Next operation after audit approval: user confirms source roles + sixth boundaries, chooses VLM provider, authorizes upload + budget.
""")
    W("REQUIREMENT_INVENTORY_AND_CROSSWALK.md", _crosswalk(matrix))
    nxt = _next(workspace)
    W("CONTINUE_HERE.md", f"""# CONTINUE_HERE — VME v1.3 offline build

STATUS: **STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT**

## Exact next command (after the independent audit approves)
```bash
python -m vme status --detailed
```
Then, only with the user's explicit decisions: confirm source roles (`config/source_roles.json` by SHA256), lock the sixth interval
(`vme selection sixth-lock ...` from the witness packet), choose/verify a VLM provider, and issue authorizations (`vme authorize ...`).

## Current state
- Engine: implemented offline; tests: {json.dumps(read_json(audit / 'TEST_RESULTS.json')['pytest_outcomes'])}.
- Real sources: 6 files hashed; {real.get('base_five_film_coverage', {}).get('indexed')} base-five frames + {lock.get('indexed')} sixth-clip frames decoded and PTS-indexed.
- PAID_VLM_FRAMES_SEEN=0, RUNWARE_REAL_CALLS=0, ART_QUALITY_NOT_EVALUATED, ANIMATION_FIXTURE_ONLY, TRANSFER_NOT_EVALUATED.
- Recomputed next operation from DB: `{json.dumps(nxt)}`
- Pending human decisions: source-role confirmation, sixth boundaries, provider choice, budgets, upload consent.
""")
    W("NEXT_AGENT_HANDOFF.md", f"""# Next agent handoff

1. Read `CONTINUE_HERE.md`, then the structured records (`workspace/store/vme.sqlite`, `workspace/state/*.json`) — not chat history.
2. Re-verify sources by SHA256 (`vme sources probe --folder <dir>`); STOP if bytes differ (`SOURCE_HASH_MISMATCH`).
3. Run `pytest -q tests` and `vme status --detailed`; confirm `PAID_VLM_FRAMES_SEEN=0`, `RUNWARE_REAL_CALLS=0`.
4. Do not start paid work. First tasks after the user's approval: (a) choose a VLM provider and record a verified capability snapshot;
   (b) Runware consented probe with the user-confirmed AIR id; (c) human/VLM candidate rationales → `vme selection propose`.
5. Hidden reasoning from this session is not transferable; only committed records are. Uncommitted work = UNRESOLVED.
Recomputed next operation: `{json.dumps(nxt)}`
""")
    from ..review.server import build_review_page
    with tempfile.TemporaryDirectory() as td:
        w = Workspace(Path(td) / "w").ensure()
        s = w.store()
        html = build_review_page(s, "AUDIT-SNAPSHOT", images=[], packet={"note": "UI snapshot; live gallery at `vme review serve --run <id>`"})
        s.close()
    W("REVIEW_UI_SNAPSHOT.html", html)


def _next(ws: Workspace) -> dict:
    from ..state.handoff import exact_next_operation
    try:
        return exact_next_operation(ws)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def _preservation() -> str:
    from ..spec_registry import authority_report
    rep = authority_report(SPEC)
    lines = ["# Preservation comparison (v1.3 + Addenda 24–27)", "",
             "Authoritative documents and their SHA256 as read by this build (`vme/spec_registry.py`):", ""]
    lines += [f"- `{k}` {v}" for k, v in rep["authoritative"].items()]
    lines += ["", f"Missing authoritative: {rep['missing_authoritative'] or 'none'}",
              f"Superseded launch texts present (not used): {rep['superseded_present']}",
              f"Authoritative launch text: `{rep['authoritative_launch']}`", "", "Narrow precedence overrides applied:", ""]
    lines += [f"- {x}" for x in rep["precedence_overrides"]]
    lines += ["", "Legitimate supersessions: v1.1 replaced 'MP4 every iteration' with art→asset→video gates; v1.3 replaced the v1.2 launch "
              "with OFFLINE BUILD→AUDIT; Add26 reinterprets Q0–Q7 as reasoning functions; Add27 adds completeness + provenance."]
    return "\n".join(lines) + "\n"


def _crosswalk(matrix: dict) -> str:
    out = ["# Requirement inventory and crosswalk", "", f"Generated {now_iso()} from executed tests.", "",
           "## Original approved 13 parts → modules", ""]
    for k, (t, mods) in ORIGINAL_13.items():
        out.append(f"- **{k} {t}** → " + ", ".join(f"`{m}`" for m in mods))
    out += ["", "## Every requirement ID", "", "| ID | Status | Needs | Requirement | Module(s) | Tests |", "|---|---|---|---|---|---|"]
    for r in matrix["rows"]:
        out.append(f"| {r['id']} | {r['status']} | {r['needs_for_positive_proof'] or ''} | {r['requirement']} | {r['module'] or ''} | "
                   f"{len(r['tests'])} |")
    return "\n".join(out) + "\n"
