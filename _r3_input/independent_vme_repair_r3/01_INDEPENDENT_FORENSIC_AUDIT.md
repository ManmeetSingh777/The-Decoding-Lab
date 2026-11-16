# VME v1.3 — Independent code-path audit and non-negotiable correction boundary

Audit input: `VME_V13_COMPREHENSIVE_REPAIR_AUDIT.zip` (SHA256
`0e49e93bfc9f2f696fc816957406b46d87f15af58e73467851a8f7fe06ad939c`).
Date: 2026-11-15. Scope: the actual archived Python/Remotion sources, test claims, metadata and Addendum 28 inputs;
**NOT** the user's live `G:` checkout or actual source MP4s.

## Independent verdict

**REJECTED FOR 15+1 REAL SOURCE INVESTIGATION.** Archive integrity is sound, but the running code
still permits invalid observations, unsent witness self-citations, incorrect conditional
coverage, and unresolved production limitations. The existing 227-repo-pass / 225-fresh-pass,
2-skipped figures are claims in the archive; this audit did not rerun the ~90-minute suite.
Actual source frames, audio and paid provider calls were not present/performed; real artistic
perception, photographic accuracy, original art and professional animated transfer are unproven.

**Direct independent proof:** `INDEPENDENT_REDTEAM.py` failed all five acceptance cases against
the unmodified extracted ZIP (four assertion failures, one unhandled exception). A *limited
working-copy correction* to the three implicated modules passes all five tests and Python
`compileall`. It is NOT an end-to-end repair and does not replace the remaining work.

## A. Confirmed executable faults (must fix before canary)

| ID | Actual location | Reproduced defect | Required fail-closed correction and test |
|---|---|---|---|
| F01 | `vme/vision/contracts.py:121-122` | A record saying `nice beautiful premium artwork` with empty visible relations and source facts returns `ok=True, VALIDATED` (only `weak_frames`). | Promote weak content to `NEEDS_REINSPECTION`, maintain precise target ids. Separate structural frame coverage from artistic sufficiency; false-generic, unchanged-frame and counterexample tests. |
| F02 | `vme/vision/contracts.py:145-146` | Boundary `active_objects:[{"id":"actor_1",...}]` throws `TypeError: unhashable type: 'dict'`. Tests had only strings. | Normalize and validate structured IDs, reconcile continued/ended/open events, reject malformed identities, test real shape. |
| F03 | `vme/style/coverage.py:194` | A branch requiring `action=grip` falsely covers `view=profile` because unknown keys are filtered away, allowing `all([])`. | Reject unmatched predicates. Require exact applicability or an explicit evidence-backed invariant/wildcard. Test unrelated, partially matching and multi-condition cases. |
| F04 | `vme/investigation/controller.py:351` | A model may add `W-never-sent` to its own `answer_evidence_ids` and then cite it as observed, passing `validate_answer`. | Evidence authorization must come from immutable **actual image manifest**, not model output. Reject self-authorized, unseen, wrong-film, wrong-region and wrong-version citations. |
| F05 | `vme/investigation/controller.py:110-114` | One branch for `view=profile` plus another for `action=grip` counts as coverage of `view=profile AND action=grip`; no joint branch exists. | Check joint applicability on one coherent rule, or prove documented condition independence; test wrong combined camera/grip/lighting. |

These five defects were **independently reproduced** using the attached executable test file.

## B. Additional code-path deficiencies confirmed by inspection (require integration tests)

| ID | Actual location | Why the old suite is insufficient | Required correction |
|---|---|---|---|
| F06 | `vme/loop/real.py:43-51,697-699`; `vme/vision/protocol.py` | Detailed P2/P3/P4 pass instructions exist, yet the central source question-answer request sends `QA_SYSTEM` rather than `pass_instructions("P4")`; rationale and native follow-ups likewise use short bespoke text. Only P1 and one P5 route have visible protocol injection. | One versioned, tested protocol dispatcher for **every** source-analysis request; P0 context and typed binding, active cluster, counterexamples and required output; record exact sent text/hash in request journal. Wire P2/P3/P4 in their actual causal stages, not just static constants. |
| F07 | `vme/vision/runner.py:84-87,148-170`; `vme/loop/real.py:103-135` | Packet IDs and the S1 stage-cache external key use a `VISION_PROMPT_VERSION` label/model, not actual `PROTOCOL_SHA`. Changing instructions while retaining the version string risks reusing old semantic commits without rerunning calibration or invalidating evidence. | Hash exact protocol, response schema/parser, execution profile, image preprocessing and relevant source/selection into packet/stage fingerprints; on change, migrate explicitly or invalidate dependent semantic claims (never blindly rebill). Cold-start negative tests. |
| F08 | `vme/style/authoring.py:79,85,171-193`; `vme/loop/real.py:43-51` | `REFERENCE_REQUIRED` defaults false when the answer omits it; `QA_SYSTEM` does not ask for this field. Branch references can be optional and silently omitted from provider conditioning. Only the alphabetically first witness image is packaged per role. | A skill-owned **required conditioning plan** based on the actual construction task, provider limitations, human rights/consent and linked source exemplars. Missing/UNKNOWN requiredness fails closed; preserve multiple distinct contrast roles when necessary; block if provider cannot realize them. Never automatically upload third-party frames. |
| F09 | `vme/vision/claude_adapter.py:268-285` | The adapter itself sets `receipt.images_received = images_sent`—not a provider-observed acknowledgement. A copied frame SHA and valid JSON prove correspondence of text to input labels, not that the model studied or correctly understood pixels. | Correct the status label to **response identity validated**, record actual request image bytes, provider receipt, and independent artistic calibration separately. Do not conflate SENT, ANSWERED, GROUNDED, EXPLAINED. |
| F10 | `vme/investigation/controller.py:400-426`; `vme/loop/real.py:703-711` | The strict `assess_sufficiency` check is invoked only when owner stage is STYLE_CONDITIONS; `apply_answer` can call the decision writer for S1/S2 causal stages too. | Central mandatory sufficiency/provenance gate inside the decision writer itself, before **any** path can publish a usable decision; negative tests for every caller and stage. |
| F11 | `vme/style/coverage.py:91-177`; `vme/loop/real.py:482-555` | The reverse construction plan primarily uses a typed **original brief** and generic categories like face, body, world, not an exhaustive source-observed scene/character-event design inventory. A populated dimension is not proof every relevant art treatment in all 15+1 scenes was understood. | Maintain two independent ledgers: **source-grounded investigation completeness across all selected scenes** and **new-production construction coverage**. Native witnesses per discovered element/state/relation, source-led novel dimensions, separate joint constraints, explicit unknowns. Both gate skill promotion. |
| F12 | `vme/loop/real.py:1076-1121,1182-1200` | S7 reuses one `n_canonical_character` output for all actors; S8 has one `pack.canonical` and refuses other actor IDs. | Per-actor canonical/identity/state graph keyed by stable ID, distinct jobs/cost/consent/approval, asset ownership and cross-actor contact; multi-actor drill must pass without identity aliasing. |
| F13 | `render/remotion/src/SceneGraph.jsx:4-55`; `vme/loop/real.py:1202-1214` | Whole-state swaps and fixed linear position/rotation/opacity interpolation are the actual motion engine. The skill-derived image clauses do **not** govern shot choreography, acting, easing, environment response, attention or simultaneous motion. | Typed source-derived **motion/scene grammar** compiled into art-state timelines, event graph, camera/world/actor tracks and verified contacts; editable motion decisions must affect actual render; tests with ablation, temporal comparisons and multi-actor counterfactuals. Do not call sprite movement professional animation. |
| F14 | `vme/reference/probe.py`; `vme/style/coverage.py:165-166`; no substantive source-audio path under `vme/loop`, `vme/vision`, `vme/render` | Audio count is probed and `VISUAL_AUDIO_TIMING` is a potential coverage label; there is no evidenced waveform, transcript, narration, SFX, music, timing alignment or audio-mux implementation in the audited production loop. | Add real, consented source-audio inspection: stream decode/timebase, transcript when available, temporal events with uncertainty, music/SFX beats, synchronized scene decisions, output audio tracks, playback and AV validation. If absent, mark AUDIO_UNSTUDIED and AV_PRODUCTION_UNAVAILABLE. |
| F15 | `vme/render/renderer.py:157-170`; `vme/loop/real.py:1208-1214` | `render_video` returns and transitions to video review even if `ffprobe_verify.ok` or `motion_evidence.ok` is false; S8 logs these as output values, not strict blockers. | Enforce `TECHNICAL_RENDER_FAILED` for essential mismatches, with a separate explicit diagnostic-only route; artistic motion-quality must be reviewed independently. |
| F16 | `vme/style/decisions.py:108-117`, `vme/style/authoring.py:64-146` | REAL path sets `substitutes=None`, so the textual cross-subject substitution challenge is NOT_RUN; supporting facts are only checked for presence/witness IDs/rough relational wording. No automated proof that proposed artistic details match those pixels. | Preserve limited-scope candidate status; implement cross-subject discriminating evidence selection, independent calibrated visual reviewer, hard negative counterexamples, human review of sampled high-impact claims and unambiguous candidate→qualified transitions. |
| F17 | `vme/loop/real.py:1217-1243` | S9 conducts one **still** holdout and explicitly states animated transfer NOT_ATTEMPTED. | Freeze skills, then run multi-subject/multi-scene animated unseen scripts including 2-minute contiguous film, human review + causal ablations before any qualification label. |
| F18 | `vme/vision/claude_adapter.py:35-65` | 8 target frames plus contexts share a 16k-token response ceiling. This can encourage terse, nonspecific output even when structurally complete; no real-model quality calibration exists. | Adaptive packet size, per-target observation budgeting and staged scene/actor/state dossiers; reinspection for precise open gaps, prevent token-driven omissions without skipping any target frame. Use measured provider capabilities and bounded budgets. |

## C. The intended artistic learning method (source first, especially characters)

**Do NOT begin from a generic human skeleton that dictates tube limbs/hands.** Class names are indexes,
not geometry generators. First inspect how the ACTUAL source illustration is designed and changes:

1. **Whole drawn entity:** readable silhouette and negative space, aspect ratios, line of action, major part-group silhouettes, focal hierarchy; surrounding world and viewpoint. Every claim has exact frame/region/PTS.
2. **Source-specific art-treatment map:** which pieces merge into one continuous colored region versus separate outlined shapes; upper/lower width profile and taper; curvature changes; fill, edge, gradient, highlight/shadow topology and material; intentional simplification and stylization. Say where evidence is ambiguous.
3. **State-conditioned drawings:** inspect the same identity across poses, turns, expressions, contacts and scale; what outer contour, part relationship, occlusion, light, color/edge and negative space actually **redraws**, and what persists. No generic bone solver may invent visible anatomy not present in evidence.
4. **Contact/interactions:** hands represented as actual visually designed forms; overlap/order between sleeve, hand, prop, torso, other actor and ground; where pivots/contact anchors lie and whether view-specific whole drawings are required. Validate against impossible reach, sliding feet, swallowed props, and false limb continuity.
5. **Cross-reference conditional grammar:** contrast unlike characters/worlds/roles, focus size, lighting, material and action. Record invariants, adaptations, exceptions, and contrary witnesses. Never turn one character's head/eye dimensions or palette into a global recipe.
6. **Art-method recipe:** for each qualified state and operation specify original content slots, required visual inputs, layered/whole-state/region-edit route, explicit geometry/occlusion/color/light constraints, output asset, animation consumer and negative constraints. If actual provider capability cannot implement, mark `MISSING_OPERATION`; never substitute low-quality tubes/shapes.
7. **Whole-look validation:** inspect resulting character at natural size, including temporal identity and integration into scene. The user's previously approved concept-sheet aesthetic can be used as a *quality comparator*, not a universal design template or source evidence.

Every high-impact design assertion must be stored in a **source hash → frame/region → observation → alternative → branch-condition → skill clause/reference → real operator → generated asset/state → rendered-frame witness** lineage path.
No single descriptive paragraph may substitute for that graph. Separate human-observed facts from VLM inferences, and preserve `UNKNOWN` without promoting rules.

## D. Qualification gates—these are not optional

**Gate 0 — source authority.** Exact five source identity/role confirmations and sixth volcano→Earth-logo boundary lock; 15+1 selected intervals and native PTS; source bytes available, explicit paid/source-upload consent if external. Existing archive has five roles `confirmed_by=null`, sixth start/end unlocked and zero real source frame records.

**Gate 1 — protocol/calibration.** Every live source call uses versioned P0..P6 with exact sent hash and typed bindings. Test weak-but-valid frame, false positive, discontinuity, changing model, wrong source and unseen witness. Human/artistic witness calibration at native source detail before full run.

**Gate 2 — scene/character evidence.** Every target frame actually sent; every visual feature of meaningful artistic consequence investigated across time and native-crop evidence; source/interpretation/unknown separate. Coverage is per source sequence, event, actor, drawing state and relationship, not just 18 category flags.

**Gate 3 — skill and reference authority.** Only source-grounded conditional candidate decisions with matching conditions, no contradictions, genuine relevant contrasts and exact consumers. A skill is *not* qualified by being executable. All mandatory references/identity/masks/state assets are present, authorized and within provider limits.

**Gate 4 — compiled output causality.** For each production capability: concrete output operation and actual payload/scene code are altered by the rule; ablation changes predicted local visual behavior. No side-channel style text in content, scene plan or provider parameters. Reject unsupported motion/audio choices.

**Gate 5 — professional qualification.** Original unrelated stills and character art, then actual moving held-out film, multi-actor/scene, AV and independent human review. Keep still, motion, audio and audiovisual qualification separate. Do not widen evidence beyond tested domains.

**Gate 6 — cold-start replay.** Protocol/parser/runtime/compiler/provider-profile/source SHA changes invalidate or explicitly migrate semantic evidence; a new model/executor verifies full capsule and resumes first uncommitted operation without replacing raw witness judgments or duplicating uncertain paid calls.

### Minimum test strategy

Use `INDEPENDENT_REDTEAM.py` **unaltered** as external five-case acceptance baseline; retain the existing 227/225 suites; add full negative/mutation tests: citation forgery, same-category distinct cases, incompatible partial branches, misleading art wording, mismatched frame hashes, actor identity swaps, source identity mismatch, protocol SHA change without version bump, missing mandatory exemplar, missing reference consent, aborted provider batch, multi-actor draw-state crossing, renderer no-audio and failed ffprobe. Each must independently fail when its guard is disabled. Re-run from a clean extraction/checkout, retain all failures/logs and evidence. Paid tests require a new explicit user authorization.

## E. Critical reality checks

- Correct code cannot *guarantee* a VLM inferred the right artistic cause from pixels. Human-reviewed source calibration and adversarial cross-reference tests are unavoidable for a credible claim.
- The provided ZIP contains code and synthetic tests but no actual MP4 frames/audio, so I cannot perform the proposed real six-minute artistic investigation in this audit. It must be separately supplied or accessed from the user's checkout once authorized.
- A fully exact model-controlled pixel realization is impossible to promise from text prompts alone; a model can deviate. Required conditioning, causal ablations and image approval quantify/control that risk, but never eliminate it by declaration.
- The source video rights/source-upload consent and real API keys/caps are explicit stop conditions, not defects to bypass. Claude Code subscription is not the Anthropic API billing account.
- `OFFLINE_ENGINEERING_TESTS_GREEN` means wiring/safety tests passed, NOT artistic learning qualified, not all 15+1 scenes understood, and not production-ready professional audiovisual animation.
