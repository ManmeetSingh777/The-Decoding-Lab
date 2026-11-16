"""Human-readable audit documents for the comprehensive repair ZIP, written from the measured build summary."""
from __future__ import annotations

import json
from pathlib import Path

from ..util import atomic_write_text, now_iso


def _counts(o) -> str:
    if not isinstance(o, dict):
        return str(o)
    return ", ".join(f"{k}={v}" for k, v in sorted(o.items()))


def write_docs(audit: Path, *, summary: dict, repo_checks: dict, fresh: dict | None) -> None:
    rp = repo_checks["pytest_outcomes"]
    fp = fresh["pytest_outcomes"] if fresh else "SKIPPED"
    rl = repo_checks["pytest_summary_line"]
    fl = fresh["pytest_summary_line"] if fresh else "SKIPPED"
    tot = summary["matrix_totals"]
    atomic_write_text(audit / "README_AUDIT.md", f"""# VME v1.3 — Comprehensive root-cause repair + Addendum 28 — audit index

Generated {now_iso()} by `python -m vme.audit.comprehensive` (every JSON below was produced by running the repaired code).
**No paid call, no source upload, no network request was made.** All drills use SIMULATED vision/image transports on SYNTHETIC
films; they prove software wiring only — not artistic learning, image quality or real provider behaviour.

* Tests in repo: `{rl}` ({_counts(rp)}) — logs `logs_repo/`, cases `TEST_RESULTS_REPO.json`.
* Tests in a fresh extraction of this ZIP's own source: `{fl}` ({_counts(fp)}) — `logs_fresh_extraction/`, `TEST_RESULTS_FRESH_EXTRACTION.json`.
* R01–R24 + ST28-01..24 status totals: {_counts(tot)} — `ROOT_CAUSE_MATRIX.json`, `CRITICAL_REPAIR_CROSSWALK.json`.

| Folder / file | What it proves (offline) |
|---|---|
| `REQUEST_PROVIDER_CONTRACTS/` | Anthropic batch payload with ≤64-char ids; strict fake rejections; Runware strict rejections (uuid5, no includeCost, 5 refs…); getResponse classification |
| `CRASH_AND_COST/` | 2 hard kills (vision accepted-before-batch-id; image sent-before-receipt), concurrent reservations, human reconciliation |
| `REAL_EVIDENCE_TO_REQUEST/` | frame → witness → question → decision → skill version → reference bytes → compiled provider body |
| `SOURCE_FACT_TO_SKILL_TO_REQUEST.json` | two same-category decisions survive as two decisions; exemplar-byte mutation changes payload; missing consent/bytes refuse |
| `DYNAMIC_REINSPECTION/` | SYNTHETIC unexplained phenomenon → crop + neighbour reinspection → new witnesses; an unanswerable gap stays unresolved |
| `DYNAMIC_QUESTION_AND_GAP_QUEUE.json` | one controlling question chosen from many queued gaps; question steps |
| `ITERATION_INVALIDATION/` | human art rejection → reopened decision → only S2–S5 rerun → new skill hash → different request (prompt diff) |
| `ASSET_MANUFACTURING/` | asset contracts (hash/size/alpha/coordinates/consumers), world plate without actor; expression/layer/clean-plate demands blocked by name |
| `FILM_SOURCE_STATUS/` | real six-file hashes, true 1280×720 resolution, unconfirmed base five, unlocked sixth boundary, first human action, no-spend evidence |
| `ART_INVESTIGATION_STANDARD_TRACE.json` | protocol VME-A28-1 + sha, pass→code map, packet binding, one per-frame record |
| `PORTABLE_INVESTIGATION_CAPSULE_TEST.json`, `CAPSULE_EXAMPLE.json` | crash before decision publish → capsule → fresh destination verify/resume → byte-identical pinned compile; missing reference bytes block |
| `MODEL_STANDARD_DRIFT_TEST.json` | shallow-but-valid answer rejected for the producing choice; substantive alternative kept as competing hypothesis |
| `RED_BEFORE_GREEN_AFTER/` | reproducers run on the unmodified code (red) and the repaired code (green); the 2 previously failing tests |
| `CHANGED_FILES.diff`, `CODE_VERSION_HASHES.json` | exact source change since 651c75b and per-file hashes |
| `WHAT_IS_NOT_YET_PROVEN.md`, `ANSWERS_A_TO_G.md`, `HUMAN_APPROVAL_HANDOFF.md` | limits, the A–G answers, the next human decisions |
""")
    atomic_write_text(audit / "WHAT_IS_NOT_YET_PROVEN.md", """# What is NOT yet proven (and NO REAL SPEND)

**No real spend.** This run made zero Anthropic or Runware calls, uploaded zero source frames and opened no provider socket. Every drill
used `vme/testing/simulated_anthropic.py:SimulatedAnthropicClient` and `vme/providers/gateway.py:OfflineRecordingTransport`
(labelled SIMULATED / OFFLINE FIXTURE). The real workspace has no authorizations, no jobs and no frame-vision rows
(`FILM_SOURCE_STATUS/SOURCE_ROLE_AND_SIXTH_BOUNDARY_STATUS.json:no_real_spend`). Claude Code subscription usage does NOT cover API
calls made through the `anthropic` SDK: a separate API account, key and spend authorization would be needed.

| Area | Status | Exact next action |
|---|---|---|
| Real vision perception of the 15+1 selected intervals | UNPROVEN — nothing real was seen | user confirms sources + 6th boundaries; authorize a SMALL canary with explicit model/price/cap and source-upload consent |
| Anthropic live API shape (`output_config.effort`, image limits, pricing $4/$20 per MTok from a cached table) | OFFLINE_CONTRACT_VALIDATED only | authorized `models.retrieve` + one tiny batch canary |
| Runware `runware:400@4` live behaviour (base64 vs URL, cost field, reference-image limit, getResponse states) | OFFLINE_CONTRACT_VALIDATED only (doc-cited, strict fake) | user confirms model/account; one authorized probe image |
| Artistic quality of any generated image | ART_QUALITY_UNPROVEN | real original art + human review |
| Correctness of a VLM's artistic interpretation | UNPROVEN; sufficiency gate checks structure/relations, not truth | calibration on a small real witness set with human review |
| Base five films' identity | BLOCKED_SOURCE_CONFIRMATION (titles differ from the contract; all 720p) | user confirms or supplies the intended films |
| Sixth clip volcano start / Earth-logo arrival | BLOCKED: boundaries unlocked (role confirmed by the user) | user views the local witness frames and locks both frames |
| Layers / masks / clean plates / hidden surfaces / IK | BLOCKED_ROUTE_NOT_IMPLEMENTED (named blocker per demand) | verified segmentation + clean-plate provider route |
| Expressions without an evidenced decision | BLOCKED_NO_DECISION_OR_OPERATOR | real source evidence for the expression choice |
| Professional multi-actor animation | UNPROVEN — WHOLE_STATE_SWAP only; directed graph consumer exists | approved real art + asset routes |
| Still transfer / animated transfer | still: pending human review; animated: NOT_ATTEMPTED | frozen skill + sealed unseen briefs + human review |
| Reference-exemplar upload of real source frames | BLOCKED without `ReferenceExemplarConsent` + Runware source-upload consent | explicit user consent per film SHA |
""")
    atomic_write_text(audit / "HUMAN_APPROVAL_HANDOFF.md", """# Human-approval handoff (what only the user can do next)

Nothing below was done by the agent. Exact current state: `FILM_SOURCE_STATUS/SOURCE_ROLE_AND_SIXTH_BOUNDARY_STATUS.json`.

1. **Confirm the five BASE_FILM files by SHA256** (or supply the intended films; 1080p originals would be NEW sources):
   `vme confirm-role --sha <sha256> --role BASE_FILM --by <your name>` — the REAL loop stops at `SOURCE_ROLES_UNCONFIRMED` until then.
2. **Lock the sixth interval** after viewing the local witness frames: volcano first frame and Earth-logo arrival frame
   (`vme selection sixth-lock --start <i> --end <j> --confirmed-by <name> --witness-sha <packet sha>`). The loop stops at `SIXTH_BOUNDARY_NOT_LOCKED`; 15 sequences alone never run.
3. **Approve the 15-window selection** (`vme approve-selection --manifest-sha <sha> --by <name>`) after reviewing the proposal.
4. **Choose/confirm the vision model and price**, then issue a capped authorization with the confirmation phrase
   `I AUTHORIZE PAID CALLS WITHIN THIS CAP` and explicit source-upload consent listing film SHAs — only for a small canary first:
   `vme provider confirm-vision --model <id> --by <name>`, then `vme authorize --provider anthropic-claude --model <id> --tasks source_vision
   --cap-usd <cap> --issued-by <name> --confirm "I AUTHORIZE PAID CALLS WITHIN THIS CAP" --source-upload-consent --allowed-sources <sha,...>`.
5. **Confirm the Runware account/model** `runware:400@4`, a cost estimate per image, and (separately) whether source-frame exemplars
   may be uploaded as reference images: `vme provider confirm-runware --model runware:400@4 --est-cost-usd <x> --by <name>` and
   `vme reference-consent --film-sha <sha> --by <name> --statement "..."`. Keys stay in your local environment only.
6. **Review real original art** (S6), **assets** (S7) and **video** (S9); attribute each defect to a decision id so the responsible
   production choice is reopened. Freeze the skill only after review.
7. **Reconcile any uncertain paid submission** shown by `exact_next_operation` (`RECONCILE_VISION_SUBMISSION` / `RECONCILE_PROVIDER_JOB`)
   before anything is retried.
""")
    p = summary
    atomic_write_text(audit / "ANSWERS_A_TO_G.md", f"""# Addendum 28 final non-regression answers (A–G)

All reproduction commands run from `visual-mastery-engine/` with the pinned venv. Outputs cited are in this audit folder.
Limitation common to all: the drills use SIMULATED transports and SYNTHETIC films — they prove routing, not perception.

## A. Every target frame, neighbours, byte identity; whole→details→whole, temporal, cross-film contrast
* Code: `vme/vision/runner.py:plan_packets` (contiguous target packets covering exactly [start..end], context frames separate) →
  `PacketRunner._inputs` (decodes every frame, checks `raw_sha == frame_content_sha256`, records PNG sha/PTS) →
  `vme/vision/prompt.py:build_vision_request` (typed binding: `target_images[{{frame_id, pts, bytes_sha}}]`, prior boundary, active cluster,
  controlling problem) → `vme/vision/claude_adapter.py:submit` (each image preceded by `FRAME <id> [TARGET|CONTEXT] image_sha=...`) →
  `vme/vision/contracts.py:validate_packet_response` (one record per target, echoed image hash, persistent/ended identities,
  boundary events reconciled; empty/generic entries rejected). Instructions: `vme/vision/protocol.py:P0` ("WHOLE -> PARTS -> WHOLE",
  temporal alternatives) + `PASSES['P1']`; cross-film contrast: `vme/loop/real.py:_pick_witnesses` (one witness per film + contrast
  witnesses from other films/subject classes) used by `_s2` questions; P2/P5 in `protocol.py`.
* Reproduce: `python -m pytest tests/test_investigation_standard.py -k "protocol or every_frame or packet_request" -q`
* Output: `ART_INVESTIGATION_STANDARD_TRACE.json` (`packet_request_binding`, `one_per_frame_record`).
* Limitation: a model may still perceive wrongly; packet image count (20) is a planning assumption until `models.retrieve` is authorized.

## B. A feature absent from the atlas
* Code: per-frame `unexplained_phenomena` (required field, `contracts.py`) → `vme/loop/real.py:_register_phenomena` (one
  `VisualPhenomenon` per distinct behaviour, sightings accumulated across sequences) → `_phenomena_gaps` (a gap owned by the phenomenon
  id, not a category) → `_s2` question / `_reinspect` (crops + neighbours) → decision whose `owned_choice_ids` contains the phenomenon id;
  it counts as explained only when that decision is executable.
* Reproduce: `python -m pytest tests/test_production_choices.py -k reinspection -q`; drill evidence `DYNAMIC_REINSPECTION/`.
* Limitation: discovery depends on the vision model flagging the phenomenon; the simulated client flags one synthetic case.

## C. Missing face×view×light / hand×prop×body relation in a filled grid
* Code: `vme/style/coverage.py:reverse_plan` emits joint choices (`<actor>:face+view+light`, `<actor>:contact+light`);
  `VisualModelCompletenessInvestigator.investigate` requires a SUPPORTED relation WITH witness evidence AND a decision that OWNS the joint id
  (`owns`); `set_relation` refuses SUPPORTED with empty evidence. `_s2` turns the controlling gap into one question
  (`LoopController.step_question`), sends the witnesses that show all joint dimensions (`_pick_witnesses`), and asks for branches whose
  operation is `op.face_view_state` / `op.hand_prop_contact` (`_required_branches`); the answer changes those operators' clauses/references.
* Reproduce: `python -m pytest tests/test_production_choices.py -k case4 -q` (filled grid still reports `hero:face+view+light`,
  `hero:contact+light`, `hero:face+view`).
* Output: `DYNAMIC_QUESTION_AND_GAP_QUEUE.json`.
* Limitation: the drill's simulated answers are deterministic text; real answers need real frames.

## D. Two same-category observations
* Code: `vme/style/authoring.py:production_choice_id(owned_key, phenomenon)` → `author_decision(decision_id=..., owned_choice_ids=...)`;
  same decision re-answered with a different action → `contradictions` (both witness sets, status OPEN → RESEARCH_ONLY); human rejection →
  `superseded_branches`. Each branch gets its own clause `K-<decision>-<i>@<op>` and reference role `exemplar:<decision>:<hash>`;
  `_package_references` stores the exemplar bytes by sha with witness/film/consent.
* Reproduce: `python -m pytest tests/test_production_choices.py -k "same_category or contradiction" -q`
* Output: `SOURCE_FACT_TO_SKILL_TO_REQUEST.json` (two decisions, identical dimension tags, distinct ids, two clauses, two reference shas).
* Limitation: identity quality depends on the reverse plan / phenomenon naming; equivalent phenomena described differently stay separate.

## E. Skill-owned instructions to Runware without a second LLM
* Code: `vme/compiler/compiler.py:StyleProgramCompiler.compile` (CONTENT segments from typed brief slots; STYLE segments only from skill
  clauses; references from the skill manifest; `includeCost`, `outputType`, `outputFormat` technical) → `vme/providers/gateway.py:StyleImageGateway.submit`
  (only accepts issued jobs, recompiles and refuses any mutation, `interface_two_audit` field ownership) → `RunwareAdapter.build_body` (UUIDv4).
  Character states use the same path with the approved canonical bytes as identity reference (`skills/runtime.execute`, `_s7`).
  Static AST scan: only `compiler.py` builds a `positivePrompt` dict; only gateway/runware call `send`.
* Reproduce: `python -m pytest tests/test_compiler_authority.py tests/test_provider_contracts.py -q`
* Output: `REAL_EVIDENCE_TO_REQUEST/...TRACE.json:7_compiled_job_and_provider_body` (redacted provider-visible body), `REQUEST_PROVIDER_CONTRACTS/`.
* Limitation: the provider's own pixel choices remain uncontrolled (`provenance.RESIDUAL_NOTICE`).

## F. A new coding model reading only CONTINUE_HERE
* Code: `vme/state/capsule.py:import_and_verify` — hash-verifies every file, `verify_protocol` (identical sha or recorded migration with
  calibration report, else `PROTOCOL_DRIFT`), rebinding films by SHA only, uncertain charges block, recompiles the pinned job and compares
  the logical hash + reference hashes byte-for-byte, writes a factual `HandoffReconstruction` (no new rules), returns the first uncommitted
  operation. Old decisions are versioned records; a different interpretation becomes a contradiction/competing hypothesis
  (`protocol.competing_hypothesis`), never an overwrite. `PacketRunner` refuses to recount committed frames; image resolution policy is in
  `model_profile`.
* Reproduce: `python -m pytest tests/test_investigation_standard.py -k capsule -q`
* Output: `PORTABLE_INVESTIGATION_CAPSULE_TEST.json` (destination C rehearsal `byte_identical_logical_payload`, destination D
  `BLOCKED_MISSING_EVIDENCE` when reference bytes are removed).
* Limitation: a new model's *perceptual* regression can only be detected on a real calibration witness set (not available offline).

## G. Status by capability (no relabelling)
* Engineering-complete on strict offline fakes: R01–R13, R15–R18, R21, R22, R24 and ST28 items with PASS in `CRITICAL_REPAIR_CROSSWALK.json`
  (totals {_counts(tot)}).
* Awaiting real vision/model proof: perception of the 15+1 intervals, VLM artistic interpretation quality (ST28-04/09), provider live
  behaviour, image quality (ST28-14), transfer (R23).
* Blocked: source confirmation (R14: base five unconfirmed, 720p), sixth boundary lock, layers/masks/clean plates (R19), expressions without
  evidenced decisions, professional multi-actor animation (R20), all human approvals and any paid call.
* Measured test results: repo `{rl}`; fresh extraction `{fl}`.
""")
    atomic_write_text(audit / "FINAL_STATUS.txt", "STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT\n")
    (audit / "build_summary_pretty.json").write_text(json.dumps(p, indent=1, default=str), encoding="utf-8")
