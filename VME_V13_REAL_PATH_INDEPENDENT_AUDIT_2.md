# Visual Mastery Engine v1.3 — independent audit of REAL PATH REPAIR

Source archive: `VME_V13_REAL_PATH_REPAIR_AUDIT.zip` uploaded November 15, 2026.

## Integrity and execution

- ZIP SHA-256: `8aaf3d51a878bb3c3670bfe31d8e81fc0023186e7f7e53f3aa00fbb6fa8ad2c8` (matches developer report).
- 259 ZIP entries; `ZipFile.testzip()` clean; all 258 entries in `SHA256_MANIFEST.json` match their hashes and sizes.
- Reported machine run: 180 pass, 2 fail, 182 tests. Independently reproduced both failures in a separate Linux extraction. Additionally, 20 tests passed in style/question suite and 59 passed in gateway/completeness/asset/selection suites. A larger combined run was interrupted by the execution timeout, so no claim of an independent full-suite pass.
- No source MP4s, real image generations or production vision results included. The reported REAL S0–S9 run uses simulated vision and Runware transports.

## Strong improvements over prior audit

- `vme/loop/real.py` provides real stage handlers S0–S9 that invoke production modules and accept injected providers, rather than the previous unconditional stop placeholders. The input and output gates are stateful and distinguish simulation from genuine learning.
- `vme/skills/runtime.py` now exists. `vme/style/authoring.py` writes source-linked decisions, skill branches and provider clauses; `vme/compiler/compiler.py` and `vme/providers/gateway.py` enforce deterministic pinned-skill payloads and reject several raw-prompt bypasses.
- `vme/vision/runner.py` has per-frame coverage, source hashes and per-packet semantic checkpoints. An updated image gallery and approval interfaces are present.
- `vme/artwork/character.py` expresses canonical-character-first manufacturing and the real loop labels WHOLE_STATE_SWAP honestly instead of pretending to have segmented parts.

## Verified blockers / important weaknesses

### P0-1 — Real Anthropic Message Batches requests violate the 64-character custom_id limit

- Code: `vme/vision/runner.py` (~178) constructs `f"{p.idempotency_key}-{uuid.uuid5(...)}"`, where `p.idempotency_key` is `idem_` plus 32 hex characters. The resulting ID has length **74**. `vme/vision/claude_adapter.py` (~109) forwards this unchanged as `custom_id`.
- Reproduced by invoking the archived `plan_packets()` on a 32-frame synthetic index: `74` characters.
- Anthropic Message Batches API requires `custom_id` length 1–64 and matching `[A-Za-z0-9_-]+`. Real frame analysis will fail at submission.
- Fix: canonical short <=64-character safe task id; validate before any request; add a strict simulated-API contract that rejects invalid IDs (not a permissive mock).

### P0-2 — Vision billing/resume has a crash window after API acceptance but before journal persistence

- Code: `vme/vision/claude_adapter.py::request_json` calls `messages.batches.create()` then writes `task_*.json` containing batch ID. A hard kill in between leaves an accepted remote batch unrecorded. `custom_id` is unique within a batch; it is not an across-batches idempotency guarantee. Retrying can create a second billable batch.
- Existing hard-kill drills simulate a durable remote but do NOT prove this particular real API failure mode safe.
- Fix: journal `SUBMISSION_ATTEMPTED` with stable payload hash and custom id *before* submission. On restart with missing remote batch ID mark `SUBMISSION_UNCERTAIN`, look for reliable remote reconciliation or require explicit human resolution; never blindly resubmit. Prove with a strict simulated client that accepts the batch then raises before returning its ID.

### P0-3 — The REAL skill builder currently emits zero style reference image bytes

- Code: `vme/style/authoring.py::author_skill`: writes `reference_roles: []`, `reference_role_ids: []`, and passes `references=[]` into `write_skill`. `vme/compiler/compiler.py` supports approved visual references but never receives any from these real-authored skills.
- Audit trace `audit/SOURCE_TO_SKILL_TO_PAYLOAD_TRACE.json` shows `reference_byte_shas: []` on generated skill-owned jobs. Thus textual construction rules are connected, but source-derived visual conditioning remains absent.
- Fix: source-witness → selected, role-labelled, suitably cropped/full artwork exemplar → byte hash → immutable versioned skill reference manifest → explicit clause/branch reference role → compiled job `referenceImages` → provider payload. Condition references on applicability, subject diversity and user authorization; do not send copyrighted/reference frames without explicit permission. Prove both requests change when reference selection changes and missing references block compilation.

### P0-4 — Independent artistic decisions can be silently merged or overwritten

- Code: `vme/style/authoring.py::decision_id_for(dims)` hashes only sorted dimension tags. Two different findings about eyes, head contour or gesture under the same dimensions get the same decision ID. `author_decision` merges by `when` and operation; later findings may replace earlier ones.
- Fix: canonical artistic phenomenon/producer-choice ID separate from category tags; stable reuse only on explicitly equivalent decision/branch keys. Keep versioned evidence, previous conditions and contradictions; add regression of two same-category, same-condition but different, simultaneously necessary decisions both reaching the skill and provider request.

### P0-5 — Visual completeness can be overstated by category presence rather than actual construction coverage

- Code: `vme/loop/real.py::_ledger` marks each dimension RELEVANT_SUPPORTED whenever any non-research decision has that tag. The corresponding `set_relation` call marks SUPPORT with `evidence=[]` if a witnessed relation merely carries all tags. `vme/style/coverage.py` requires a joint owner for required dimensions but doesn't verify all distinct artistic phenomena within those tags.
- Risk: one satisfactory FACE_ACTING or COLOUR decision can hide several missing face/colour construction choices; required but unknown source phenomena not in the original typed scope may be classified not applicable.
- Fix: coverage keyed to specific observed phenomena, necessary producing choices and interdependencies—not only one of 18 dimension names. Carry an explicit unresolved-question register, counterexamples, scope exceptions and documented reasons. Reopen “supported” items when new contradictory visual evidence or bad output appears. Require real evidence for joint relationships (not empty evidence arrays).

### P0-6 — First 15+1 source study can silently omit the mandatory sixth clip

- Code: `vme/loop/real.py::_s0` records `PENDING_HUMAN_BOUNDARY_LOCK` for sixth selection but still returns COMPLETED, and `_s1` includes the sixth only if already LOCKED. This permits a successful 15-sequence run without the sixteenth mandatory volcano→Earth-logo sequence.
- Fix: explicit hard-stop before L0 if sixth is not locked; no invented timestamps. Preserve user confirmation for the clip role separately from visual confirmation of exact boundaries.

### P0-7 — Real native-resolution deep investigation and gap-driven rereading are too shallow/rigid

- Code: `RealLoopConfig.native_followups_per_sequence=3`; `_native_followups` follows the first three provider suggestions per sequence. `_s2` asks follow-up questions using full frame images of existing witnesses, but does not request new gap-selected crops or temporal re-observations when a high-impact question remains unresolved.
- Fix: for EACH high-impact gap, choose the minimum sufficient relevant source views/crops/neighbor frames, perform deliberate adaptive reinspection, and persist their relationships to the question/answer/skill. Keep exhaustive initial per-frame submission for every selected sequence; don't substitute 3 crops for in-depth vision. Preserve strict spend budgets and checkpoint/reconcile on all passes.

### P0-8 — Anthropic SDK isn't in the pinned install requirements

- `vme/vision/claude_adapter.py::production_client_factory()` imports `anthropic`, but neither `pyproject.toml` nor `requirements.lock` includes that dependency. Local environment happens to have it, but clean installation won't prepare for the real model path. Pin the SDK (and test offline import and serialization in an isolated environment).
- Important: Claude Code Pro/Max subscription usage does NOT include API calls made by the external `anthropic` SDK. Explicit separate API-key/account/spending authorization required. Price table and max-images planning assumptions remain unverified.

### P0-9 — Live image provider still needs a small authorised actual-response contract test

- `vme/providers/gateway.py::_run` rejects `imageURL` results as `PROVIDER_URL_NOT_FETCHED`; the requested `base64Data` path is assumed. Transport, model ID, output mode, credit cost, and supported edit/reference capabilities were never tested live.
- Fix provider adapter with explicit grounded capability negotiation and supported modes. Paid tiny probe only after an additional user authorization, and do not infer it works from fixture tests.

### P1 (not an excuse to bypass art approval) — Character/world animation path is still narrow

- `vme/loop/real.py::_s7` uses WHOLE_STATE_SWAP, and does not generate some expression states because no conditional rule exists; `_s8` builds a one-actor / one-background scene with default positions, basic keyframes and camera. It is not yet a reusable multi-character layered artwork/acting/choreography renderer.
- The image-first approval sequence is appropriate. Do not block all progress on complex motion, but before claiming integrated professional animation, implement genuine compositional multi-layer/multi-actor states, depth, attention, contacts, suitable masks/clean plates and no fake fallback pan when motion is missing. Never use unapproved artwork or primitive SVG substitutes to hide missing capability.

### P1 — Initial candidate coverage favors convenience over expressive diversity

- `_windows` uses 2–12s shots and caps VLM rationale candidates to 10 windows per film, sampled evenly. That is an efficient first survey but not proof every important artistic technique was offered for selection. Keep 3/film selection with a coverage and visual-novelty challenge, including additional candidates where important events may be missed.

### P1 — Skill versioning/freeze must not allow stale clause files

- `author_skill` writes to a fixed `skills/real-<run_id>` folder; `write_skill` overwrites named files but doesn't purge obsolete prompt-template files. Require version-specific immutable folders or safe replacement; test multiple revisions retain independent hashes and no old clauses leak into the current compiled request.

## Two reported tests independently reproduced

1. `tests/test_compiler_authority.py::test_static_scan_only_compiler_builds_positive_prompt_and_only_gateway_sends`: regex flags `loop/real.py` for mentioning `http_transport` and `runware`. It does not show an unauthorized image *send*; use AST/call-target checks.
2. `tests/test_real_path.py::test_hard_kill_mid_packet_reconciles_batches`: embedded child process calls `Path()` without `from pathlib import Path`. Fix the subprocess snippet; retain a genuine crash-after-remote-acceptance test for P0-2 above.

## Recommendation and go/no-go

- **NO** to starting paid L0 vision of 15+1 sequences, providing keys, or allowing automated Runware runs in this code version.
- **YES** to continuing the existing repo with a focused P0 repair; preserve working frame indexes, prompt compiler, gateway, S0–S9 stages and approved specs. Do **not** switch to HyperFrames, REA-Video, OmniSVG or Rive now.
- After P0 repair and independent repeat audit, ask the user to confirm correct five source films and the sixth start/end frames, choose a vision provider and verified model and cost, then do a *small* explicitly authorised real provider probe before full L0.
- Governing success question: professional, transferable source-learned visual construction on unfamiliar original scripts? **NO — unproven**. Major verified gap: real artistic learning and image quality not yet demonstrated; important LIVE API and source-to-style-reference construction issues remain.
