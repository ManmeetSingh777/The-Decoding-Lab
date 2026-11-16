# VISUAL MASTERY ENGINE — IMPLEMENTATION CONTRACT v1.2

**EARLIER v1.1 REQUIREMENTS (retained; v1.2 09–12 have highest priority):** Read `07_STYLE_FRAME_PROMPT_CHARACTER_GATES.md` and `08_PROMPT_PIPELINE_EXAMPLE.md` completely. They expand the approved 13 sections without replacing them. Specific overrides: visual observations MUST be abstracted into source-independent conditional **style mechanisms** before skill promotion; every decoded video frame MUST have a coverage status and all-frame model review must be supported with truthful cost/coverage claims; ALL image-provider requests MUST pass a skill-controlled `PromptCompiler`; **characters are first-priority** with facial, limb, silhouette and layered-state qualification; **ARTWORK and ASSET approval block integrated MP4 rendering**. The old unconditional video-at-every-iteration rule is superseded. Nothing in this contract authorizes claiming the capabilities implemented before they are executed and tested.

**Purpose:** Build a new, executable learning-to-production system that discovers the highest-impact visual properties of five original Kurzgesagt films, learns how to create comparable craftsmanship on unrelated original subjects, and progressively assembles convincing moving illustrated worlds. **This is a build instruction, not a claim that the system is already built or capable.**

**Non-negotiable governing principle:** Source observation -> evidence-backed, specific question -> tested production procedure -> original artwork/animation -> independent visual comparison -> multiple gap diagnoses -> user's review -> reusable versioned improvement. Repeat on newly chosen high-impact, connected clusters. The *creation and comparison* are the learning test; reports alone do not qualify anything.

**Scope boundary:** Visual mastery first. The new studio consumes a manually supplied, original scene brief describing the subjects, actions, viewpoint and intended visual focus. It does not yet autonomously invent the story, scientific explanation, voice-over or emotional arc. Narration/audio interfaces may exist for synchronization but the full Director is out of scope. Do not delete, merge or replace the 13 commitments in the user's approved specification. This contract details their execution and user-requested revisions.

**V1.2 IMPORTANT:** This file preserves the user-approved 13-part architecture. `09`–`12` are authoritative working-algorithm addenda and override any weaker wording about style abstraction, runtime prompt generation, mandatory source-frame vision and timeout/resume. The target is **working skill-owned image production**, not new gates as a substitute for artistic quality.

## 0. Absolute isolation, input consent, provenance

1. Create a **new repository and workspace** (e.g. `visual-mastery-engine/`). Do not import or inspect any prior AnimationLab reports, candidate skills, code, CMRs, screenshots, judgments, datasets, or historical renders. Treat the user-approved 13-point architecture as **requirements**, not evidence about style or artistic methods. Do not derive artistic rules from chat summaries.
2. Allowed learning sources: **only the five original user-supplied Kurzgesagt MP4s**, inspected directly; the newly built engine's own original outputs and user feedback; and independent, documented tool/runtime APIs. Preserve SHA-256, path, duration, dimensions, audio streams, and frame/time provenance. Do not copy original source frame pixels into generated original films or redistributable skill assets. Use reference images for analysis/conditioning only when the user authorizes third-party upload.
3. Original reference films expected (match actual files by the user's paths and hashes, NOT fuzzy names): AI Humanity's Final Invention; How Are Memories Stored Inside Your Brain; Why Your Brain Blinds You; How Nuclear Flies Protect You; Why Humanity Will Never Leave Solar System. Never substitute web copies silently.
4. Keep local sources read-only; generate all index/analysis products in fresh hashed working folders. No prior evidence imports by default, including 'helpful' old architectural or style files.
5. Before sending source frames to any third-party image or vision API, surface its destination, upload form and data handling and request user authorization. Original output images can be sent where authorized. Never assume user authorizes use of copyrighted references to fine-tune a model. Preserve exact input selection and terms compliance.
6. `.env` contains credentials, never commit. Run offline/dry mode without a key; mark **NOT VERIFIED**, never pretend placeholder/mock art satisfies a visual proof. Paid execution requires an explicit configured budget and approval.

## 1. The six permanently connected responsibilities (approved section 1)

**Reference Library**: ingest, decode, catalogue, individually account for every decoded frame, support full-frame vision coverage with honest model-coverage states, and select dense time spans and native crops. Only newly collected evidence from original 5 MP4s.

**Quality Gap Finder**: compare actual references with multiple original baselines or newest outputs, identify and rank **several** distinct high-impact visual deficiencies; group related differences into one or more causal clusters. Never reduce the first iteration to a single tiny issue.

**Question-Driven Investigator**: inspect source evidence and generated outputs, ask specific cause-discriminating questions for each cluster, investigate connections across artwork/world/visual perspective/motion. It may inspect full native frames and consecutive sequences; shall not emit hollow adjectives or arbitrary geometry.

**Skill Builder**: abstract observations into source-independent conditional style mechanisms and implement procedures that actually produce the visual result using image generation, editing, layering, code, motion and rendering. Create genuine SKILL.md + tooling + grounded visuals + proven examples, and do not promote a skill based on text alone.

**Visual Producer**: compiles every image request from original brief + scene requirements + approved/candidate style skill + validated references + provider capabilities; calls real configured providers; makes original illustrations and animation-ready versions; composites and renders original videos ONLY after required visual/artwork/asset user approval.

**Comparison + User Review**: independently examine original artwork and character families BEFORE animation, then examine rendered output and relevant stills with blinded where feasible A/B; diagnose observed deficits, show the user an intelligible review page, collect specific feedback and use that feedback to prioritize the next iteration. The loop is complete only after review is recorded, or paused awaiting review.

System stages share one scene model, one evidence register, one procedure registry and one outcome register. None may silently replace another's data or change a frozen test brief.

## 2. What counts as a useful high-impact question (approved section 2, expanded)

Do not let an LLM create 100 generic topics. It must first **look at** original source artwork and a baseline. Detect multiple observable differences affecting the finished result, then formulate specific questions that can discriminate causes and drive creation. Include obvious blind-spot checks: (a) identity and richness of entire illustrated world, (b) bespoke subject construction and finish, (c) coherence of all objects in one frame, (d) colour/material/light unity, (e) viewpoint and scene-state changes, (f) moving parts/interactions/secondary activity, (g) composition and what stays legible during movement. These are *coverage prompts*, not preassigned agent silos.

For each quality gap create a `gap` record with:
- **Visible symptom**: what is worse in actual image/clip, where, at what moment, with image URLs or local paths and coordinates when useful.
- **Importance explanation**: which portions/subjects/viewing moments the gap damages, why a viewer notices it, how severe it is. Do not confuse large pixel area with salience.
- **Reference contrast**: 2+ meaningful source visual witnesses if available, including different source subjects or film contexts. If only one, mark conditional evidence limited.
- **Affected dependent features**: artwork, lighting, layout, camera, movement etc. *as they interact*, not isolated boxes.
- **Competing causal explanations**: at least the plausible main causes, with one discriminating check for each; don't blindly blame source analysis.
- **Expected fix signature**: what observable output would change if the proposed method is right, and what would not change.
- **Implementation locus**: source extraction / diagnosis / skill input / model/provider / layer separation / animation code / integration / evaluation / unsupported capability.
- **Proposed effort/cost, reusable breadth, uncertainty and evidence**. No fake objective scores of artistic beauty.

**Ranking rubric**: Do qualitative pairwise comparison for the top 5-8 observed gaps, evaluating (1) salience and overall quality loss, (2) breadth across multiple visual situations, (3) causal upstream position: does it undermine other improvements?, (4) likelihood a specific working method can improve it, (5) leverage per time and paid model cost, and (6) interaction with other high-impact gaps. State why the highest ones beat the next ones. The user can override priority with a visible recorded reason.

**Select a connected cluster** of generally 2-5 linked gaps with a common original output goal. The size is flexible; choose only as many as can be investigated and causally assessed without losing attribution. Never select a low-impact micro-detail merely to fill a quota. Preserve unrelated high-impact gaps in ranked queue for the next cycle. If several severe gaps are independent, stage them as separate subchanges within the same major iteration rather than silently combining edits.

**First iteration special rule**: Put character visual identity, full-body silhouette, facial artwork, limb/hand relations and coherent rich world artwork in the initial cluster. Do not postpone character artistry as a minor issue. Make an **initial high-impact cluster**, not one local fix. Study a useful cross-section of original films before baseline comparison; then compare against several real original baseline outputs; refine the cluster. Initial work must cover integrated frame craftsmanship (designed subjects + coherent whole-world art + unified colour/material/lighting) **and at least one viewpoint/motion relationship** to prevent an image-only blind spot. Prioritize the specific defects actually observed, not an imagined universal list.

## 3. Question-driven investigation standard (approved section 3)

Investigator should construct a **question tree, not a topical encyclopedia**:

Q0: What visible quality is the generated result missing relative to appropriate professional examples? Evidence in frames.
Q1: What makes this quality visibly present in the sources? Describe *relationships and design choices*, not just labels like 'rich'.
Q2: Which specific feature of the source result is not explained by our current method? Compare alternatives with native visual evidence.
Q3: Which choices vary with subject, viewpoint, light, action or scene purpose? Find cross-subject examples and counterexamples to avoid copying one reference.
Q4: How could a verified image/editing/motion operation produce the relevant property on a novel original brief? Input, method, tool, output, corrections.
Q5: What result should our real output display if this method is correct? What falsifies it?
Q6: If the output falls short, did we observe incorrectly, infer incorrectly, fail to specify the procedure, fail to execute, or choose an inadequate provider?

Every question answer must include: (i) a precise claim, (ii) inspectable witness or actual output, (iii) its conditions and connected features, (iv) confidence label `OBSERVED/INFERRED/TESTED`, (v) an actionable next question/operation or explicit stop reason. A vague term without a visual example, causal relationship and a usable production decision fails review. **Specific does not mean narrow**: show surrounding context, changing frames, co-moving objects, scene-wide interactions and the implications of each local conclusion.

Efficient source reading: (a) scene/shot overview + full film context, (b) dense native sequence for selected changes, (c) deep native crops of affected objects/regions, (d) compare two+ contrasting cases across reference films, (e) inspect new source witnesses only when questions demand them. Do not mass-index pixels, universally sample one frame per second as proof of analysis, or repeatedly decode unrelated film portions.

No assumption from observations alone about proprietary production methods. Identify the **observable effect**, infer possible routes, then qualify whichever route actually produces it; original production technique is not required. Do not silently turn guessed reasons into facts.

**Cross-category co-observation**: For each selected source shot, store an integrated table: visible subject and world, their artistic identity and finish, composition and attention, state changes, camera/world relations, independently moving objects, temporal interaction and the specific proposed skill consumers. Several related questions and answers may be processed sequentially in a single bounded investigation pass, yielding one coherent cluster; not one unrelated page per category.

## 4. Working skill conversion, no missing magic step (approved section 4)

**Definition**: A skill is a *tested reusable production procedure* taking an unfamiliar original brief and required states as input and producing original art/motion by calling actual verified tools. A style essay or a single successful prompt is a candidate, not a skill.

One skill folder requires:
```
skills/<capability-id>/
  SKILL.md                 # concise when-to-use, inputs/outputs, conditional workflow, refusal cases
  manifest.json            # version, status, dependencies, model capabilities, witnesses, tests
  recipes/                 # exact prompts + conditioning roles + settings + branching decisions
  references/              # pointers to LOCAL original witnesses; don't redistribute source pixels
  scripts/                 # REAL callable generation/editing/composition methods where applicable
  examples/                # NEW original baseline, intervention, resulting outputs, masks, clip
  tests/                   # executable input/outputs, transfer checks, failure checks
```

`SKILL.md` must answer: **When** is the technique relevant? **What** must the caller provide? **How** are original composition, subject, materials, viewpoint and motion requirements translated into operations? **Which** model/tool and validated parameters are used? **What** images/layers/states are produced? **What** constraints/conditions are checked? **How** are failures corrected without manual per-scene coordinate edits? **What** other capabilities must be invoked to complete the scene? It may point to long reference/recipe files; avoid dumping all study text into model context.

**Operational recipe structure**: source-quality target -> original brief parse -> visual reference selection with roles (`design-language`, `material`, `compositional`, `motion`), not merely one style prompt -> generation plan -> provider call -> visual inspection -> high-impact corrective edit if needed -> asset packaging (layers, masks, depth, states) -> animation method -> render -> comparison/transfer test. Record exact provider model ID/version, prompt, reference image SHA, seed if supported, dimensions, cost returned, output SHA and masks. Model failures must be distinguished from orchestration bugs.

**Promote through explicit states**: `OBSERVATION`, `METHOD_CANDIDATE`, `EXECUTABLE`, `IMPROVING`, `TRANSFER_QUALIFIED`. Each transition references actual evidence. `EXECUTABLE` only means code runs. `IMPROVING` requires better original visual outcomes than controlled baseline. `TRANSFER_QUALIFIED` requires frozen methods, different subjects and independent review. A passing structure test is not art quality.

**Crucial source-to-operation trace**: each proposed visual principle needs concrete consuming tool/argument/operation -> produced asset/scene part -> changed visual result -> review verdict. A rule that only appears in logs is not a skill.

**Dependencies and integration**: Shared canonical `SceneSpec` and `AssetSpec` identify subject, identity, viewpoint, layer ownership, material, focus, pose/state, visibility, relation to other objects and time-based events. Skills may depend on one another; outputs must be compatible rather than independently inventing different objects. A world skill must know which character assets will animate; a character-view skill must preserve approved design; a camera skill must not presume static artwork can cover unseen geometry.

## 5. Agent orchestration: sequential decisions + bounded parallel support (approved section 5)

**Default: single sequential lead investigator**, not ten independent agents. One shared queue of quality gaps and scene-specific questions; one continuous artifact record. A temporary specialist is created only when a specific high-impact question needs expertise.

**Parallel work allowed**: independent mechanical extraction, reference checks on *different source witnesses with the same question schema*, competing model/provider trials, and blind visual reviews. No concurrent unfrozen edits to the same skill, shared scene or decision log. Parallel results merge through explicit reconciliation of contradictions, signed evidence pointers and one prioritized cluster.

**Roles** (logical tasks, not guaranteed separate continuously running agents):
- Lead/Orchestrator: maintain state, priorities, human review gates, cluster dependencies.
- Source Investigator: recover visual causes and cross-source conditions.
- Production Method Engineer: implement real image/editing/animation calls and skill recipes.
- Independent Visual Reviewer: directly inspect the outputs, not author claims; seek missing or worsened qualities.
- Integration/Diagnostic Engineer: classify code/provider/compositing/motion failures and run discriminating tests.
- Human (user): review meaningful visual iteration outputs; no automatic qualification in place of human judgment.

**Memory**: Do not rely on conversation context. Persist `project_state.json`, `source_index`, `gap_register`, `question_records`, `skill_versions`, `experiment_runs`, `reviews`, provider usage and checkpoint manifest. Atomic writes (temp -> fsync -> rename), hash critical artifacts, commit code+manifests on checkpoint, verify state and hashes on resume, run a crash/resume test with deliberate kill/restart. No “resume succeeded” without tested restoration.

## 6. Iteration protocol WITH USER review (approved section 6; cluster revision)

Each **major learning iteration** is a complete evidence-backed batch with multiple connected changes:

0. `START`: load state; choose a balanced mix of reference source witnesses and **at least two original briefs** (one fixed for A/B and one rotating). Record an additional unseen-challenge procedure, not exposed to the skill-editing agent until frozen.
1. `BASELINE`: use actual available art provider/renderer without newly proposed skill changes. Save original frames, original MP4 when motion is relevant, complete calls and costs. Baseline can be reused for exact same brief/model settings within the batch, not indefinitely after model changes.
2. `MULTI_GAP`: inspect **the top several high-impact problems**, rank them and select a causally connected cluster with a defined desired visible improvement, explicit related areas and excluded lower-priority distractions. User may correct priorities at review.
3. `INVESTIGATE`: in one coherent bounded pass, deeply inspect source frames and time sequences for all connected cluster problems, and answer discriminating questions in a graph; preserve confidence and contradictions.
4. `BUILD`: create/change *multiple necessary working skill components* in a versioned branch; ensure every proposed rule maps to a producing operation. Validate schemas, tool calls, frame/layer output, and runtime errors before expensive model generation.
5. `PRODUCE`: create revised full-res original stills and **wait for artwork + asset approvals before any full integrated moving MP4**; after approval, render an actual integrated moving MP4, not a still-camera move falsely presented as rich animation; show legitimate scene-state, foreground, object, camera or perspective actions as applicable. Create the same brief with no new skill and with the revised skill; preserve the rotating original brief too.
6. `DIAGNOSE`: find **multiple observed gaps** (not just the largest), test whether each arises from source reading, question/causal model, skill recipe, model quality, reference-conditioning failure, layer separation, geometry/contact/animation code, integration, or evaluator failure. Log evidence for each. Where linked subchanges were applied together, do small isolated toggles/ablations to determine which improved output and whether interactions matter. Avoid full factorial explosion: focus on highest-impact ambiguous contributors.
7. `REVIEW`: at the artwork stage publish before/after full-res stills + original character quality evidence and pause; at asset stage publish layers, poses, views and recomposition and pause; at video stage publish MP4 comparison and pause. Preserve rotating-scene evidence, prioritized gap differences, prompt compiler/skill patch diff, costs and reviewer objections. **Pause for user feedback at each applicable gate**. Review statuses `APPROVED_IMPROVEMENT`, `PARTIAL`, `REJECTED`, `NEEDS_EVIDENCE`; do not auto-approve.
8. `TRANSFER`: after method freeze and review, run an independent **new** related-but-different subject/scene challenge. If failed, keep as improving but do not mark transferable; route failure to queue. No manual repair of test subject's specific geometry or art followed by false qualification.
9. `COMMIT/RESUME`: preserve all outcomes, fixes and failures; recompute rank list, select next connected cluster based on largest unresolved quality loss; retry with different **active subjects**, not endless refinement on one scene. A final 20–30-second integrated original visual demonstration is the stronger milestone after first batch.

**User review frequency**: every major visual iteration and any claim of material skill improvement. Small internal renders needed to debug code or model options don't require a response each time. The review page must function locally without requiring that the user read source code. If the user is absent, persist `AWAITING_HUMAN_REVIEW` and stop before promotion; do not fabricate feedback or continue automatically as approved.

## 7. Fast learning without shallow learning (approved section 7)

- Build an initial scene/shot index once, then retrieve only source segments relevant to current high-impact questions. Deep inspect native images only where it changes the procedure; consecutive frames for motion/transformations.
- Never allocate large budgets to generic mass-reporting. Demand a testable method from each source-reasoning batch.
- A **visual cluster** can create multiple linked skill changes before rendering. But split the implementation into independently addressable toggles for diagnosis.
- Render internal diagnostic previews and selected full-res frames to check artwork/geometry fast; **do NOT require MP4 before approved artwork and asset-pack gates**. A major integrated motion-cycle checkpoint includes moving MP4 after both approvals; pre-render art cycles close with user-reviewed stills.
- Preserve provider request/response/cache hashes and seeds where available to avoid duplicate billing and separate prompt variability from actual method improvement.
- Use a preapproved maximum paid budget, per-task cost logging and hard stops. Do not guess a user's budget. Test actual provider behavior with cheap calls before costlier reference conditioning or many variants. If an image provider can't produce acceptable art despite appropriate conditioning, replace the provider/route rather than deepening geometry reports endlessly.
- Detect stalled progress: if repeated cluster experiments don't produce a visible improvement, stop that method branch, present evidence, consider source reasoning versus provider limitations, and seek user direction on paid alternatives.

## 8. Visual quality first; animation-aware from the start (approved section 8)

**Milestone A**: user-approved original professionally appealing whole frames from unrelated briefs, not icons or source clones. Retain scene-level coherent composition and designed assets.

**Milestone B**: user-approved coherent character/object/environment states, layers, correct occlusion, viewpoint variation, camera travel and transition artwork prepared without destroying the canonical design. Define first intended motion before art generation so hidden geometry and alternate states can be supplied.

**Milestone C**: genuinely animated, coordinated scenes: movement, changing drawings and perspective, interacting objects, background activity and visual coherence. No camera-only pan across a flat still as proof of full motion.

**Milestone D**: connected original 20–30s multi-shot visual production; after credible success, expand to 60–120s audiovisual production with a separate Director. Don't change this milestone ladder.

**Asset production routes**: raster image model (complex canonical artwork); image-edit/reference-conditioned model (related states); segmentation/masks and manual/automatic clean-plate generation (for separable animation); deterministic code (camera, layout, motion, event timing, diagrams, parallax); selective modeled redraws for complex gestures/turns or unsupported deformations. Do not assume a generative video model is available or reliable. No infinite handcrafted per-scene coordinates.

**Real render engine**: choose ONE primary verified, installable rendering path, recommended Remotion + FFmpeg/ffprobe. Use typed scene data and real loaded assets to construct original 1920x1080/30fps MP4 where feasible. Another renderer (e.g. HyperFrames) is a **verified plug-in adapter only if installed and tested**; do not build two engines or assume undocumented APIs. Render selected stills with same scene inputs. Refuse if no actual working engine. Proof clip must have visible multi-layer movement or meaningful drawing-state change; encode timestamps, action and focus events in trace.

**MANDATORY PromptCompiler + character module + frame ledger**: implement the preserved v1.1 typed data/contracts/approval gates in `07_STYLE_FRAME_PROMPT_CHARACTER_GATES.md` in addition to the modules below. Do not send open-ended image prompts invented outside style skill; do not qualify SVG primitive drawings as source-trained artwork; do not confuse 100% frame indexing with 100% vision-level understanding.

**Reference/model details**: Runware's official FLUX.2 [klein] 4B route `runware:400@4` supports text to image, reference images and editing. The developer must verify actual API model capability, dimensions, image upload and reference limits using current official docs; no hardwired unsupported transparency or LoRA assumption. This is a cost-oriented starting adapter **not an artistic quality guarantee**; create a provider interface that can swap to a stronger image/edit model after a real visual comparison. Never ship a mock as if it were art evidence. Model output format PNG does not guarantee alpha masks; test actual alpha and implement separate matting as needed.

## 9. Non-overfitting / anti-false-improvement (approved section 9; revised)

**Three distinct scene pools**:
A. `comparison_anchor`: a fixed brief within a given batch for controlled before/after A/B. It may be kept as a periodic regression test but not be the only training scene.
B. `rotating_development`: new briefs each major cycle (different subject classes, composition, palette, environmental structures, lighting conditions, and eventually motion types) exposed to skill builder.
C. `unseen_transfer`: independently generated/selected **after skill freeze**; keep hidden from method author until version lock; materially different original world, but same capability under test.

A/B: same base model and settings, same original brief; same reference access policy; seeded where supported; at least one paired replicate, more when stochastic variation masks conclusion. Measure blind human/independent visual comparison, not just pixel differences. Disable skill completely (baseline), apply full cluster (intervention) and inspect individual high-impact subchange toggles. Compare on both anchor and rotating original scene. Worsened dimensions must be recorded. Transfer runs must use frozen method; if corrected using holdout-specific prompting, it becomes training data, not a pass; replace with a new unseen challenge.

**Reference generalization**: do not treat recurring source patterns as style rules automatically; first identify style-making design decisions, conditions and original design freedom as in §07; then use cross-film witnesses, different subject types, counterexamples and conditional criteria; don't memorize source shapes, fixed palette values, characters or existing shot designs. Distinguish `original design choice` from learned `visual construction principle` and documented `source fact`.

## 10. Concrete engineering modules and interfaces (approved section 10)

Recommended repository:
```
visual-mastery-engine/
  README.md  .env.example  package.json  pyproject.toml
  config/project.yaml  config/provider_capabilities.json
  input/reference_mp4/           # user-owned original source videos, ignored by Git
  input/original_briefs/         # rotating development scenes
  src/reference/                 # ingest, hash, probe, shots, native frames, audio frame timing
  src/compare/                   # source selections, visual gap cards, ranking, condition checks
  src/questions/                 # question/cause graph + targeted source retrieval
  src/skills/                    # schema validator, execution, versions, ablation, freeze
  src/providers/                 # real image/edit provider adapters, cost and capability checks
  src/artwork/                   # canonical imagery, variants, layers, masks, clean plates
  src/scenes/                    # typed SceneSpec, AssetSpec, event graph, attention/focus
  src/render/                    # Remotion composition, still/MP4/frames, FFmpeg validation
  src/review/                    # independent evaluation, user-facing local gallery + feedback API
  src/experiments/               # baseline/intervention/ablations/rotating/unseen tests
  src/state/                     # atomic records, hashes, resume & checkpoint
  skills/                        # qualified and candidate skills, NOT only prose
  tests/                         # programmatic, integration, visual fixture, resume tests
  runs/                          # immutable per-iteration output manifests, ignored by Git if large
  reports/                       # human-review packets and audit logs
```

Suggested CLIs implemented and documented:
```
vme doctor                     # python/node/ffmpeg/provider/repo/source/renderer capability audit
vme ingest --sources <dir>      # source hashes, probe, read-only register
vme reference overview         # first cross-film source survey & scene index
vme baseline --briefs <dir>     # real provider original baselines (budget required)
vme gaps --run <id>             # ranked multiple visible gaps & clustered hypotheses
vme investigate --cluster <id> # grounded questions and native frame investigation
vme build-skills --cluster <id># executable recipes and tests, not fake skill status
vme produce --run <id>          # original stills and actual MP4
vme diagnose --run <id>         # multiple root causes + isolated toggles/ablations
vme review serve --run <id>     # local review gallery and feedback submission
vme transfer --skill <id>      # freeze then genuinely unseen original brief
vme resume                     # validate artifacts and continue without duplicate calls
vme status                     # truthful state, cost, next action, awaiting user
```
CLI may be `npm run vme -- ...` or Python, but these contract-level commands must exist as equivalent documented interfaces. CLI cannot silently succeed without artifacts.

**Core typed records**: `SourceWitness`, `SceneSpec`, `AssetSpec`, `GapCandidate`, `QuestionAnswer`, `CausalCluster`, `SkillManifest`, `ProviderCall`, `VisualExperiment`, `DiagnosticFinding`, `VisualReview`, `TransferChallenge`, `Checkpoint`. See `02_DATA_SCHEMAS.json` for minimal validation contracts. Separate `ObservedFact`, `Interpretation`, `ProductionMethod`, and `ReviewVerdict` fields. No logs-as-evidence substitution.

**Local review UX**: a browser gallery showing original reference comparison fragments, baseline original stills, intervention stills, synchronized before/after MP4s, annotated issue regions, material difference ranking, skill versions/diffs, paid cost, multiple diagnoses and your feedback fields. Feedback submission writes a timestamped immutable review record; final promotion requires explicit human signoff. Provide CLI fallback with same state updates; don't build an inert HTML mock UI.

## 11. First actual complete cycle (approved section 11, expanded)

A. Bootstrap new repo and tool adapters, `doctor` pass for source reading + Remotion/FFmpeg + authorized real art provider. Do not run full paid batch until budget approved.
B. Ingest exact five original MP4s (no prior reports). Build focused cross-film overview and useful source witness index only.
C. Choose **at least two original briefs with dissimilar subjects**, one anchor and one rotating development brief, supplied/generated without copying source subjects. Reserve another genuinely unseen challenge after skill freeze.
D. Generate untrained baselines with real art model; a preliminary short sequence establishing actual moving output. Save model and scene inputs, full resolution stills, motion results and provider costs.
E. Identify several salient visual defects and form first tightly connected cluster; investigate native film evidence across relevant subjects for **world-level artwork coherence, distinctive design/finish, integrated material/color/light and moving/perspective behavior**, adapting specificity to actual observed gaps. Multiple questions per cluster; inspect full context and temporal changes, not just isolated crops.
F. Write **several connected skill procedures** and real callable tools, with source-condition statements and provider-specific operations; instrument scene/asset dependencies.
G. Recreate **the same anchor brief** under frozen baseline vs changed skill; also generate a newly rotating original scene. **FIRST produce full-res original stills, genuine character art and user ARTWORK approval; THEN produce and approve animation-ready variants/layer pack. Only with both approvals** render a genuine moving **12–20 second integrated MP4** with at least two linked shots, a purposeful viewpoint change and multiple evolving scene elements (not obligatory 100 things). The entire film should use original art. Record what the viewer is meant to see as a visual focus path; do not add autonomous creative story direction.
H. Independent reviewer lists ALL material strengths, losses and remaining gaps, ranks top ones and diagnoses source vs skill vs model vs renderer, with subchange ablations where needed. Generate user-ready interactive review report, pause awaiting user review and don't claim qualified mastery.
I. After user feedback, freeze improved skill versions and run genuinely new related capability challenge brief. Preserve outcome and select next cluster; qualify only when demonstrated. At integrated milestone, after artwork and asset approval, make a 20–30-second original multi-shot visual film. Later qualify 60–120s audio-visual output when the Director exists.

**Important**: If the real provider cannot produce sufficient visual craftsmanship, **do not fabricate success**. Still finish runnable architecture, show its best actual outputs and quantified costs, diagnose actual reason and user-approve provider change. Likewise if no provider key is available, deliver verified mock-free offline code/tests and a `WAITING_FOR_PROVIDER` state; don't claim the first real iteration passed.

## 12. Failure diagnosis, refusals and provenance (approved section 12)

Errors are classified independently, with evidence:
- `SOURCE_ACCESS`: missing/invalid MP4 or decodable witness.
- `OBSERVATION_GAP`: important visible feature/relationship overlooked, source contradicted inference.
- `HYPOTHESIS_ERROR`: artistic explanation does not predict actual quality.
- `SKILL_SPEC_GAP`: missing decision, invalid recipe branch, wrong original-brief conditioning.
- `PROVIDER_LIMIT`: model quality/editing/ref consistency insufficient despite correct calls.
- `PROVIDER_EXECUTION`: authentication, parameter validation, rate limits, unexpected output/response.
- `ASSET_PREP`: holes, bad masks, inconsistent views, broken identity, unusable layers.
- `RENDER_ENGINE`: import/dependency, runtime, FPS, encoding, output corruption.
- `MOTION_LOGIC`: missing object action, poor contact/state continuity, wrong camera-vs-world movement.
- `INTEGRATION`: mismatch between assets, colour/light, depth, attention and camera; one specialist overwrites another.
- `EVALUATION_ERROR`: reviewer didn't look at frames, saw only metadata, confounded stochastic differences.
- `GENERALIZATION_FAIL`: heldout scene worse or needs individual fixes.

For each failure: actual symptom artifact, precise file/time/image or response, candidate causes, minimal discriminating test, observed result, correction location, new original proof, and regression. Multiple causes per run allowed; fix high-leverage upstream cause first. Refuse approval if evidence missing. Failed/partial work must be faithfully recorded.

**Stop policies**: Missing/invalid source, missing source-upload consent, no configured paid budget, provider unsupported, no actual generation output, corrupt render, missing user feedback, or invalid/contaminated holdout cause a named checkpoint and safe pause; never convert to success. The user chooses whether paid model/provider experiments continue. Do not run unbounded automatic retries.

## 13. Success gates and milestone verdict (approved section 13)

- `ARTISTIC`: multiple substantially different original frames are judged rich, coherent, distinctive, strongly finished, with evidence that learned procedures improve on raw model baseline. Do not use a single global aesthetic score.
- `TRANSFER`: frozen skills improve unfamiliar original subjects, including cases that differ in art subject/world and composition, without per-subject manual rescue.
- `ANIMATION`: moving scenes retain that art quality while camera/perspective, scene states and objects change coherently; genuine non-camera object animation required.
- `INTEGRATED`: approved 20–30s multi-shot original visual result with independent review and the user's feedback. Later full 60–120s audiovisual integration requires separate Director.

Any status `VERIFIED` must link to actual bytes, witness hashes, program test logs, source/skill versions, visual comparisons and user review. Tests passing do not imply artistic quality. Never label visual mastery achieved based only on a static image or toy moving logo. Conversely, never burn budget on full animation before a meaningful source-grounded still-art and character-state user approval gate.

## 14. Explicit technical dependencies and 3 interfaces

**Image adapter** `generate/edit(request) -> {images, seed?, cost?, provider_response, model_id, provider_version?, source_hashes}`; capability probe `textToImage`, `imageEdit`, `multiReference`, `maxDimensions`, `alphaOutputVerified`, `costAccounting`. Use supported true values, not advertised values as proof. Check online docs or installed SDK at build time and pin packages.

**Renderer adapter** `render(SceneSpec, AssetManifest, frameRange?, settings) -> {stillFrames?, mp4, ffprobe, timingTrace, manifest}`. Select Remotion primary; validate actual frame dimensions, fps, duration, audio if supplied, decoded frame inspection, moving-entity changes beyond static camera. FFmpeg/ffprobe metadata verified; metadata alone not quality proof.

**Skill runner** `execute(skillVersion, originalBrief, sourceRefRoles, providerCapabilities, outputDir, config) -> {originalAssets, executionTrace, imageVersions, layerManifest, outputVideo?, providerCosts, typedErrors}`. Reject invalid dependencies; no algorithm that only writes trace events without affecting production pixels. Methods should be reproducible to the extent the provider supports, recording non-determinism honestly.

## 15. Verification and independent acceptance requirements

Implement programmatic tests for file hashes, reference identity, frame crops, source/witness timing, state schema, atomic recovery, multi-gap ranking, cluster selection, question source evidence, exact skill-to-tool consumption, provider error handling and budget stops, render integrity, view/layer mismatches, freeze and holdout integrity, honest preview-vs-video status, human review persistence, version rollback and ablation experiments. **Intentionally inject failures**, including an inert skill, a copied reference image, a changed style rule that doesn't affect pixels, a broken layer, no actual movement, a contaminated holdout, failed API response and forced crash halfway through checkpoint. The system must refuse false promotion.

Acceptance demonstrations:
1. The user can run `doctor`, ingest 5 movies and inspect exact hashes; historical AnimationLab artifacts are absent.
2. A real non-mock image API generates an original baseline from an unrelated brief; cost and full-resolution image saved.
3. Source-dependent and generated-output-dependent gap register contains **several ranked gaps** with evidence, not generic sentences.
4. A connected cluster yields multiple specific, evidence-backed questions with cause discrimination and a trace to **actual executable methods**.
5. An original scene is generated with cluster method enabled and disabled, and a changed rule actually affects the intended output.
6. The same original brief can be A/B compared without seed/brief/provider confounds; rotating brief and unseen-transfer exist.
7. First artwork cycle stops at approved or rejected full-res original still evidence; AFTER user artwork and character/asset approval, at least 12–20s genuinely moving original MP4 exists for the first integrated animation iteration; motion and frame provenance tested.
8. Diagnostic report attributes multiple defects to actual responsible layers and distinguishes provider limitation vs artistic inference vs renderer bug.
9. User can inspect a local comparison report and save feedback; promotion awaits that feedback.
10. Skill freeze prevents edits during holdout; unseen transfer is not retrospectively customized, and regression status is truthful.
11. Deliberate kill/resume restores a stable checkpoint without billing twice or inventing completed work.
12. Automated tests and visual review outcomes remain distinctly reported. If source access, paid API or the user review are not provided, the system pauses truthfully rather than issuing a false success.

## 16. Preserving exactly the 13 user-approved points

| Approved part | Preserved invariant | Requested revision |
|---|---|---|
| 1: six connected responsibilities | Single continuous source-gap-question-skill-produce-review loop | Fresh source only; gaps plural; connected cluster |
| 2: high impact | Actual visual difference and concrete cause | Several ranked problems; integrated quality and upstream leverage |
| 3: question engine | Specific sourced questions until actionable | Clustered deep specificity across connected domains; no invention |
| 4: skills | Tested methods, not reports | Actual callable operations, original outputs, ablations and transfer |
| 5: agent organization | Sequential lead + on-demand specialists | Bounded parallel gathering allowed; sequential decisions and shared memory |
| 6: iterations + human review | Source->skills->original output->visual review->repeat | Several changes per batch; full-res artwork reviewed BEFORE necessary asset approval; then MP4 video after approval; user sees each major result |
| 7: speed and continuity | Focused inspections, checkpoints, costs | One coherent deep cluster pass, not a shallow one-gap cycle |
| 8: visual then motion | Art first, animate without losing quality | Motion-aware art from day one; first integrated output is MP4 |
| 9: no overfit | Frozen transfer; original subjects | Anchor A/B + rotating scenes + unseen challenge after skill freeze |
| 10: engineering components | Concrete real code/tools/UX | Provider checks, strict diagnosis, optional renderer adapter |
| 11: first learning cycle | Complete real loop with sources and original art | Multiple related questions+skills; early full-res art review; after art/asset approval, 12–20s clip; human gates |
| 12: failure handling | Evidence-based root-cause repair | Multiple simultaneous causes: observation/spec/provider/render/integration |
| 13: success | Art, transfer, motion independently verified | No success without multiple subjects, genuine MP4 and user review |

**END CONTRACT.** All sections are requirements for implementation; none are automatically satisfied by writing this file.


## 17. Mandatory v1.2 construction algorithms (must implement, not just read)

- Follow `09_STYLE_OBSERVATION_TO_PRODUCTION_ALGORITHM.md` for complete high-impact conditional style extraction, source-fact separation, skill-owned operation/prompt templates, source-independent art-production methods, and character art-family design.
- Follow `10_EXHAUSTIVE_FRAME_VISION_AND_CRASH_RESUME.md` for every decoded frame, genuine per-frame VLM receipts/semantic observations in bounded contiguous packets, native-detail followups, source/semantic checkpoint identity and atomic resume; two films first only if explicitly staged/authorized.
- Follow `11_CONCRETE_SKILL_CONTROLLED_IMAGE_PRODUCTION.md` and the runnable `reference_impl` for immutable skill→prompt authority; production LLM cannot insert unproven style adjectives or operate the image provider using free text.
- Follow `12_EXACT_LAUNCH_AND_PROGRESS_CONTRACT.md` for correct implementation order, spending consent, user checkpoints, and persistent proof.
- All output that fails visibly must trigger upstream producing-method diagnosis and correction; validation is secondary. Full original artwork must precede animation, and approved character artwork must be generated as identity-conditioned art families, not skeleton-only code.
