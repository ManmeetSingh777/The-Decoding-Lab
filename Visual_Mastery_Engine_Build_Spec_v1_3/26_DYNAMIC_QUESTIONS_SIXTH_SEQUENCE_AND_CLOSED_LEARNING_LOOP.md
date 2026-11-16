# VME v1.3 — ADDENDUM 26
## Dynamic Artistic Question Selection, Exact 15+1 Source Coverage, and the Closed Observation→Skill→Output Learning Loop

**MANDATORY ADDITIVE ENGINEERING CONTRACT.** Preserve the entire original v1.3 archive and Addenda 24 and 25 unchanged. This document corrects their only remaining source-selection and question-control ambiguities. Do **not** copy earlier AnimationLab artistic findings. The first coding-agent execution is still **OFFLINE ENGINEERING → ACTUAL IMPLEMENTATION-AUDIT ZIP → STOP**. No external source-frame upload, provider billing, or real art-learning claims without the later user authorization and audit.

**Precedence (narrow):** Addendum 26 governs (a) treating Q0–Q7 as *inquiry functions* rather than fixed questions, (b) discovering the single next high-impact missing question from current evidence, (c) the sixth special source interval, (d) the complete active learning-loop controller, and (e) the associated audit evidence. All 13 original objectives, all A01–A68 tests, B01–B36, C01–C38, Addendum 24 continuity, Addendum 25 per-frame study and skill-only prompt authority stay binding. This file does not establish any actual Kurzgesagt style fact.

---

## 1. WHAT WAS CONFIRMED ABOUT THE OLD PACKAGES

- Original Full Build Spec → v1.1: artwork/asset user approval superseded compulsory early MP4; character, per-frame coverage and prompt compiler added.
- v1.1 → v1.2: observation-to-skill algorithm, exhaustive-frame VLM and durable resume, prevention-first art generation, launch progression and mini compiler added.
- v1.2 → v1.3: byte-identical `01_IMPLEMENTATION_CONTRACT.md`, `02_DATA_SCHEMAS.json`, `03_ACCEPTANCE_TEST_PLAN.md`, `04_USER_REVIEW_PACKET.md`, `05_APPROVED_13_PART_REFERENCE.txt`, `06_BUILD_AUDIT_MAP.md`, `07_STYLE_FRAME_PROMPT_CHARACTER_GATES.md`, `08_PROMPT_PIPELINE_EXAMPLE.md`, `09_STYLE_OBSERVATION_TO_PRODUCTION_ALGORITHM.md`, `10_EXHAUSTIVE_FRAME_VISION_AND_CRASH_RESUME.md`, `11_CONCRETE_SKILL_CONTROLLED_IMAGE_PRODUCTION.md`, and `12_EXACT_LAUNCH_AND_PROGRESS_CONTRACT.md`. Old A01–A68 still present. The old v1.2 first launch instruction remains only as `00_PREVIOUS_V12_LAUNCH_REFERENCE_DO_NOT_PASTE.md`.
- No dropped *substantive* predecessor obligation was discovered; inherited early launch instructions must not be pasted as authoritative because the first-run mode changed to OFFLINE BUILD + AUDIT.

The above is provenance, **not** permission to reuse old AnimationLab artistic observations as evidence.

---

## 2. EXACT FIRST SOURCE STUDY: FIFTEEN + ONE EXTRA, NOT A SIXTH REPLACEMENT

**First five original films**: Follow Addendum 25 exactly. Build a navigation survey of all five, select **three nonredundant contiguous sequences per film** = **15 selected sequences**, focusing on whole illustrated worlds, cross-character design/acting, and coordinated viewpoint/motion changes. Examine **every actually decoded presentation frame within each selected interval** in the genuine vision phase. Do not claim a selected interval studied if even one frame has not received a source-mapped real visual analysis entry. Use native-resolution targeted followups, including interactions between art, background and movement. These are fifteen **learning windows**, not fifteen isolated keyframes.

**One additional special sixth source clip** (approximately six minutes, user supplied): Treat it as **source 6, a separately preselected high-value event, not one of the original 15**. It has an especially strong opening starting where **the volcano scene begins** and ending where **the brand Earth logo comes in**. Its exact video filename, SHA256, first frame, end frame, and PTS **must be discovered from the actual supplied clip**. Never guess '2–3 seconds' or assume that the logo's entrance lasts a particular number of frames. Identify the actual opening and closing boundaries by whole-frame visual review plus neighboring frames. Preserve enough adjacent frames to distinguish a volcano start from a preceding dissolve and to distinguish the logo's entrance from a later hold. Present the selected start/end thumbnails and frame indices for review, then lock the interval. If source 6 does not exist in `source_films/`, mark `SIXTH_SOURCE_NOT_AVAILABLE`, keep this requirement pending, **do not invent filename/timestamps**, and continue offline engineering. When real study is authorized, study every frame of the locked opening interval, plus the necessary adjacent context. If the rest of the six-minute clip shows important complementary techniques, index it and add evidence later based on observed relevance rather than automatically treating the entire clip as an intro.

Study the sixth event as an interconnected **artwork→perspective→temporal transformation→attention** sequence. Observe how source art states, environmental design, moving objects, layers, camera movement, focal subject, scale and image complexity change together; then investigate exactly which *transferable* visual design and transition decisions would create a comparable new original event. **The original Earth brand logo and exact volcanic composition are source-specific evidence—not objects to copy into a new film.** Do not add a universal 'always put a volcano before a logo' rule.

A 6th source does NOT invalidate the current five-film full-coverage eventual requirement; it extends the corpus. Maintain separate `base_five_film_coverage` and `special_sixth_clip_coverage` statuses. The first study set is **15 + one mandatory special interval = 16 source windows** once source 6 is available. No need to deeply study the entire six-minute sixth clip before the initial image iteration unless the active artistic question requires it.

**Selection crosswalk:** For the initial 15, preserve candidate comparisons, actor/world/viewpoint diversity, entry/exit context, and per-film selection reasons from Addendum 25. Then append the sixth preselected event with separate status and clear reasons. If there is a source mismatch, stop only that clip, not unrelated five-film work. Paid work requires explicit cost/third-party upload authorization per source and provider.

---

## 3. THE MOST IMPORTANT NEW RULE: Q0–Q7 ARE NOT FIXED QUESTIONS

The Q0–Q7 procedure from Addendum 25 describes **what the investigation must be able to resolve**: quality, cause, impact, contrast, conditional production decision, remaining missing knowledge, operation, and proof. It is **NOT** an instruction to ask the same eight questions as a questionnaire during every iteration. Nor should the agent brainstorm four generic questions and choose one for appearance's sake.

The agent must derive **one next question per active unresolved bottleneck** directly from real evidence and the currently blocked producing decision. When the learned ability spans 2–5 linked artistic relationships, the system retains them as ONE coordinated cluster and uses one controlling question at a time. More than one truly independent bottleneck can be recorded, but only the highest-leverage currently actionable question drives the next investigation operation. If a decisive answer entails one narrowly targeted follow-up, ask it. Do not spray generic prompts across every category.

### 3.1 Maintain an evidence-owned active problem, not a title-only category

For each active learning cluster persist:

```
ActiveArtProblem {
  cluster_id, version, original_output_id_or_initial_reference_only,
  reference_full_frame_ids, affected_original_subject_classes,
  high_impact_visible_difference, whole_scene_consequence,
  connected_artistic_relations[],
  current_explanation_and_support[], competing_explanations[],
  latest_confirmed_facts[], latest_unresolved_uncertainties[],
  expected_original_visual_improvement,
  next_required_producer_decision_id,
  owner_stage: SOURCE_OBSERVATION | CAUSE_INFERENCE | STYLE_CONDITIONS |
               OPERATION_DESIGN | PROMPT_COMPILATION | PROVIDER_RESULT |
               ASSET_FAMILY | RENDER | HUMAN_REVIEW,
  current_question_id_or_null, source_evidence_version,
  selected_skill_version_or_null, review_state,
  next_action_and_exact_input, checkpoint_id
}
```

**Question creation must consume the actual `ActiveArtProblem` and latest source observations/output failures.** It cannot be a detached 'question generator' using only a generic system prompt.

### 3.2 Exact next-question derivation algorithm (no arbitrary list of choices)

1. **Locate the first incomplete causal handoff for the current problem**, in this strict order: source visible fact → proposed cause → conditional decision → producing operation → compiled image job → actual generated artwork/character family → animation result. If source perception is weak, do not pretend an operation can solve it; if source analysis is adequate but image requests are wrong, do not waste time reanalyzing the film.
2. **Read the specific missing piece** from the producer decision that would be required to make the next original output better. For example, the missing piece might be 'the condition under which a face outline changes during a turn', not 'study character design'. Name what concrete art operation cannot yet be chosen.
3. **Ground the uncertainty in one actual visible contrast**: source frames and different actors/worlds, or reference versus the current original output. Which visible relationship is clear, and what exactly is not yet explained?
4. **Form ONE discriminating question** that can change the producing decision. It must contain: *(a) a real observed art difference, (b) the particular unknown choice or conditional rule, (c) the source evidence that can settle it, (d) how different plausible answers would change an actual generation/edit/animation operation).* It may be a longer question if the linked artistic relations require it. It must not ask only 'why beautiful?' or 'what is the palette?'.
5. **Identify the cheapest sufficient real evidence**: native crop plus full frame, neighboring exact frames, unlike case from the current corpus, a verified original image comparison, or a specific provider/asset result. Do not blindly request more film vision if the missing piece is in code or image-model support.
6. **Answer with the actual evidence**, separating observed relations from possible causes; record which conditional producer decision is now enabled, refuted, or still blocked.
7. **Update the skill/manufacturing operation only if the answer changes a concrete artwork-producing choice.** If it doesn't, classify this question as low leverage or incorrectly targeted; choose the next uncovered causal handoff, not another long artistic essay.
8. **Repeat** using the revised evidence and the largest remaining gap. A useful question after a pose failure will be different from a useful question after a rich-world failure, even when they share a reference film.

### 3.3 Required question record, bound to a decision and an action

```
NextQuestion {
  question_id, cluster_id, from_evidence_version, gap_id,
  missing_decision_id, missing_producing_operation,
  observed_contrast_with_witness_ids,
  exact_artistic_unknown,
  question_text,
  planned_witness_or_input_ids[],
  possible_answer_consequences_for_operation[],
  answer_evidence_ids[], answer_visible_relations[],
  answer_status: OBSERVED|INFERRED|UNKNOWN|REFUTED,
  condition_applicability_and_exceptions[],
  effect_on_skill_version_and_compiled_job,
  next_action_if_unresolved,
  timestamp_and_checkpoint
}
```

**Example, SYNTHETIC, NOT a finding from the films:** Initial weak prompt: 'What makes characters expressive?' The active missing decision is the production of a different 3/4 head drawing during a specific reaction. The *derived* question becomes: 'Comparing the actual face-turn states in these source frames and unlike actor examples, which visible changes in head contour, near/far facial parts, gaze and supporting shoulder silhouette are jointly necessary to preserve whole-character expression, and which adjustments depend on actor head design? Which new canonical-conditioned artwork state should our generator produce?' A correct answer connects whole-character source evidence → conditions for a new actor → reference-guided new head/body state → image job. A forehead-coordinate inventory does not.

### 3.4 How to decide that a proposed question is HIGH IMPACT (prevention, not checkbox)

A proposed question is the right next one **only when answering it will change a high-salience visual part of the original result or remove the earliest blocker to producing that part**. For example:

- Does the affected visual result dominate the viewer's attention, character identity, world cohesion, or a crucial perspective transformation? Explain from actual images; don't pretend an arbitrary percentage is measured.
- Does the answer govern several connected output elements (actor + clothing + face, or foreground + world + light, or source world + destination world + camera)? That has higher leverage than an isolated minor detail.
- Does the unknown change an actual pending producer operation or provider request? If not, it is not the next question.
- Can the necessary evidence resolve the uncertainty with a usable answer at reasonable cost? If not, preserve UNKNOWN and find a more actionable high-impact bottleneck rather than fabricate certainty.
- Are we asking about a transferable condition or merely one source object's exact detail? Reframe if source-specific.

Do not compute an invented 'impact 92/100'. Do not perform exhaustive brainstorming of candidate questions. Do not use the arbitrary order of broad skill categories to pick the next investigation. **Ask what is preventing the desired ART from being produced next.**

### 3.5 Different question triggers depending on failure location

| Provenance of failure | Next question MUST target | What it must NOT do |
|---|---|---|
| Source artwork not actually seen, or full-resolution region too small | Which exact source image/scale/motion comparison is needed to see the missing relationship? | Infer shapes from a thumbnail or write long generic explanation |
| Source witness understood; transfer condition unclear | Under what actor/world/material/view/action condition does the art decision vary? Which unlike witness resolves it? | Copy a reference character ratio or palette universally |
| Conditional decision exists; no art-producing method | Which supported real generation/edit/layer/animation operation can construct it on a new subject? | Add more adjectives or style-check gates |
| Skill recipe exists; compiled request omits it | Which actual dataflow/binding/precedence bug dropped the skill-owned clause/reference/operation? | Reanalyze frames without evidence it's an observation gap |
| Correct request; image model ignores reference/ruins art | Which input-conditioning/editing or provider route can produce the intended art with this model's capabilities? | Pretend tighter prompt text guarantees pixels |
| Canonical actor beautiful; variants wrong | Which coherent whole-pose/view/face/hand+prop original drawings must be produced from approved canonical artwork? | Modify just a joint coordinate or use tube limbs |
| Layers/assets correct; motion breaks contact | Which actual scene-graph timing, pivot, mask or drawing-state selection fails? | Rewrite the general character style skill |
| Output attractive but source visual identity missing | Which visible cross-film art construction decision is absent from the compiled original art? | Label all attractive imagery 'Kurzgesagt style' |

---

## 4. HOW TO OBSERVE: TIGHTEN THE EXISTING ADDENDUM 25 PROCEDURE

### 4.1 Three linked forms of evidence, always start from the whole image

For each selected source window, the vision implementation shall keep:

1. **WHOLE-FRAME**: what the complete illustrated world and characters look like at presentation scale; which visual relations are simultaneously present; what is the focal treatment and what supports it.
2. **CONSECUTIVE-TIME**: how the art changes in real successive frames—subject/limb/face/world states, camera/world separation, foreground vs background and simultaneous events; what remains the same across time.
3. **NATIVE-DETAIL**: actual full-resolution source (not enlarged thumbnail) and chosen crops for unresolved high-impact art construction: face/eyes/limbs/proportions, part overlaps, material finish, complex objects and transition states.

Do not run these as three disconnected reports. Every observation is attached to the same source entity/event and active `ActiveArtProblem`. A native crop is contextualized with its full frame; a changing part is contextualized with the whole actor; a whole scene is contextualized with its neighboring states. A still frame is not sufficient evidence for how a complicated movement was constructed.

### 4.2 Exactly what every-frame study must mean

- The full source file is locally decoded with every presented video frame having identity (stream, index, PTS, hash). Selected windows use inclusive exact frame ranges, not time-based sparse sampling.
- A `FrameVisionTask` must contain the actual image bytes/reference to immutable local decoded bytes, associated exact frame identity, and at least the immediately relevant temporal context. When the vision provider supports limited images, use smaller packets; the full selected target set still must be covered.
- The model must provide an individual `FrameObservation` for each target **real frame**, with specific image facts and meaningful changes/persisting states relative to adjacent frames. An unchanged image can have a concise factual 'holds state', not fabricated novelty.
- A source frame's ledger cannot enter `VLM_SEEN` unless a real provider response identifies that exact submitted frame and there is evidence it actually received the image. A decoded thumbnail or automatic colour/shape calculation cannot count as deep vision.
- A true `ARTISTICALLY_EXPLAINED` status is higher than `VLM_SEEN`: it requires applicable evidence answering the construction question in linked full-frame + temporal + native-detail context. No full-frame count can stand in for this qualitative claim.
- Framewise accumulation must preserve **cross-frame dependencies and whole shot art decisions**. Do not conclude that a source actor 'changed personality' based on a one-frame mouth difference without neighboring context.
- Each selected sequence must have a completed expected-frame-set versus seen-frame-set comparison, independent evidence mapping, and a record of unresolved difficult intervals. Frame inclusion is strict; artistic conclusions can remain explicitly incomplete, even if every frame was seen.

### 4.3 How to use visual comparison to answer the missing question

For each question, show the model a **witness set chosen to discriminate**:

- At least one full frame in its context; exact relevant consecutive frames or their immutable IDs; native crop when a small region affects artwork quality.
- An unlike example from a different actor/world/material or a visibly different viewpoint to determine what can vary without losing visual identity.
- If the current issue concerns produced quality, the actual original output and professional source witness in comparable viewing roles. Do not confuse differences of subject with differences of artistic treatment.
- State one specific unresolved decision, not 'analyze everything'. Ask what evidence supports answer A vs B and what resulting construction operation would differ; do not force the model to invent two answers if evidence already resolves the question.
- An observed property (e.g. a certain local shadow) is source-specific until supported as a conditional production choice; do not automatically copy its exact colour/angle to another scene.

### 4.4 Good answer standard: what must be emitted

A completed `QuestionAnswer` must say precisely:

```
SOURCE_VISIBLE_FACTS: exact source-frame-backed relationships
IMPORTANT_LINKED_CHANGES: art + subject/world/pose/view/attention relationships
CONSTRUCTION_EXPLANATION: best source-supported transferable art decision(s)
WHY_THE_DECISION_MATTERS: specific difference it should create in new art
WHEN_APPLICABLE: relevant new-subject conditions
WHEN_NOT_APPLICABLE: exceptions / known limits
ACTUAL_PRODUCING_OPERATION: typed image/edit/pose/layer/motion action and inputs
WHERE_IT_ENTERS_COMPILED_REQUEST: concrete skill clause/reference/operation ID
REMAINING_UNKNOWN: evidence still required; no invented completion
```

A frame observation itself may be concise; the *answer to the artistic construction question* must be as detailed as its producing operation needs. Avoid thousands of low-impact micro-observations, but do not let a model answer 'detailed harmonious palette' with no concrete constructible art instruction.

---

## 5. FULL CLOSED LEARNING LOOP — OPERATING INSTRUCTIONS (AFTER OFFLINE AUDIT AND CONSENT)

The lead controller must actually implement these persisted phases and transitions. Each phase has a named artifact and an explicit consumer; no silent jump from analysis prose to image production.

### S0 — Source survey and coverage planning

**Inputs:** verified six-source manifest when sixth available, otherwise five-source manifest plus `SIXTH_SOURCE_NOT_AVAILABLE` blocker. **Action:** index all 5 base sources, navigation survey, propose 3x5 deep intervals; locate and lock separate volcano→Earth-logo event from source 6 if present; budget authorized cloud operations. **Output:** `FilmSurvey`, `CandidateSequences`, `SelectionManifest15`, `SpecialIntroSelection`, `CoverageLedger`, `VisionPlan`. **Consumer:** frame reader and investigator. **Stops:** no authentic selected frame evidence, wrong source hashes, no paid authorization.

### S1 — Every-frame deep visual witness construction

**Inputs:** selected 15+1 intervals, real decoded frames + PTS and active question/state. **Action:** submit each selected actual frame in bounded vision packets, maintain temporal context; native-resolution inspection of important connected art questions; cross-sequence witness comparisons; persist observations and unknowns. **Output:** immutable `FrameObservation`, `TemporalGraph`, `WitnessBundle`, `SourceArtifactState`. **Consumer:** question controller. **Stops:** incomplete frame coverage is not marked complete; blocked provider or limits honest.

### S2 — Evidence-driven high-impact problem and next one question

**Inputs:** witnesses, latest original-art output if exists, current cluster and skill gaps. **Action:** identify 2–5 connected high-impact artistic relations; locate earliest unresolved causal handoff; derive **ONE next high-leverage, discriminating question** using §3.2; retrieve sufficient real evidence; answer at production-decision specificity. **Output:** `ActiveArtProblem`, `NextQuestion`, `QuestionAnswer`, `EvidenceGraph`, `Uncertainties`. **Consumer:** conditional-style-decision builder. **Stops:** unresolved witness/unsupported explanation remains open, not asserted solved.

### S3 — Transferable conditional artistic decisions

**Inputs:** source facts and cross-case answers. **Action:** separate source object facts from style choices; derive when the artistic decision holds, adapts, or is exceptional across unlike subjects; connect all dominant visible relations that must work together. **Output:** versioned `ConditionalVisualDecision` with evidence+counterexamples, allowed new-subject variables, intended visible difference. **Consumer:** skill-operation builder. **Stops:** source example copy or aesthetic adjective with no conditional operation is not promoted.

### S4 — Skill-owned production method (real manufacturing)

**Inputs:** decisions + actual image/animation provider capabilities. **Action:** construct SkillVersion with machine-readable decisions, frozen prompt clauses/templates, role-specific real reference images and hashes, canonical actor identity slots, operation DAG (whole-image generate/edit, multi-view/pose, masks/clean plates, layers, animation), output contracts. **Output:** `SkillVersion`, `SkillOperationRecipe`, `ProviderCapabilityRoute`. **Consumer:** compiler. **Stops:** missing real operation or unresolved critical style clause → RESEARCH_ONLY / BLOCKED.

### S5 — Original image production (skill authority is causal)

**Inputs:** typed original brief; frozen skills; scene/actor plans. **Action:** compile deterministic image job with no free-text style writer, submit through restricted image gateway, save request/ref hashes/response/actual raster; prepare complete whole-actor and world art. **Output:** `CompiledImageJob`, `GeneratedRaster`, `CharacterCanonical`, `WorldArtPlan`. **Consumer:** visual reviewer and later asset maker. **Stops:** no selected skill, wrong provider capability, missing required ref/image bytes, rejected artwork.

### S6 — Artwork review and source-attributed improvement

**Inputs:** actual full-resolution original art, baseline same original brief, rotated original subject and professional witness comparisons. **Action:** show the user the actual images and multiple biggest visual gaps, attribute each to observation, conditional rule, compiler, provider artwork or integration; maintain one connected repair cluster and identify the earliest failing handoff. **Output:** `ArtworkReviewPacket`, `UserVerdict`, `GapAttribution`, `NextActiveArtProblem`. **Consumer:** next S2 inquiry or S4/S5 repair as appropriate. **Stops:** user rejects art → do not promote and do not animate.

### S7 — Animation-state and moving-world preparation

**Inputs:** approved original canonical art and intended actions. **Action:** construct and inspect full actor pose families, whole hand/prop contact drawings, views/expressions, masks and clean plates, scene graph, camera/world relationships and transformations. Refuse generic tube-limb stand-ins. Show user actual asset family and recomposition before rendering. **Output:** `CharacterPack`, `SceneGraph`, `AnimationDemandPlan`, `AssetReviewPacket`. **Consumer:** video renderer. **Stops:** unapproved or incomplete assets; missing required image drawing state.

### S8 — Animation rendering and movement review

**Inputs:** approved art + asset family + locked motion plan and real Remotion/FFmpeg path. **Action:** render actual original moving MP4; compare visual quality over time, perspective travel, character weight/contact, interacting objects and coherent world changes. **Output:** `RenderedVideo`, `MotionEvidence`, `VideoReviewPacket`, `UserVerdict`. **Consumer:** failure attribution and skills revision. **Stops:** rejected motion → return to earliest proven failing stage, not automatically 'study more style'.

### S9 — Transfer, learning state and next iteration

**Inputs:** approved versioned skill, fixed baseline original brief, rotating original brief, new frozen unseen original challenge; meaningful visual comparisons. **Action:** evaluate whether the same unchanged skill produces comparable artistic quality on different content. Record failure cause and applicability scope. Freeze truly transferable successes; retain failed attempts for investigation, no fake mastery. **Output:** `TransferRecord`, `SkillRevisionHistory`, `NewActiveArtProblem`, durable checkpoint. **Consumer:** subsequent S2/S3/S4/S5, as failure diagnosis dictates. **Stops:** cannot call a single attractive reference imitation transferable.

**Critical routing:** A coding bug in the compiler or renderer routes directly to a targeted engineering repair; a weak observation returns to S1/S2; missing style conditions return to S3; image-model inability returns to S4/S5 provider-route correction. Always fix the *earliest actual broken step* and keep unaffected skills intact. A loop need not restart all ten stages on every correction.

---

## 6. OFFLINE AUDIT: PROVE THE OPERATING LOOP IS IMPLEMENTED, NOT MERELY DESCRIBED

The coding agent MUST implement real typed stage handlers, callers, persisted transitions, source→question→decision→skill→prompt dataflow, resumability and internal review/approval state. Mock actual paid providers only; do not mock away the stage logic. The audit must exercise synthetic fixtures through connected stages and preserve the artifacts that each real consumer reads.

### Required new acceptance/failure injections (additive to all A/B/C/ADD25 tests)

| ID | Injected situation | Required observed behavior |
|---|---|---|
| ADD26-D01 | Legacy full/1.1/1.2 source instructions present beside v1.3 | Build reads authoritative v1.3+24+25+26 only; no contradictory obsolete prompt used |
| ADD26-D02 | Sixth user clip absent | Status `SIXTH_SOURCE_NOT_AVAILABLE`; no fabricated timecode or opening event; original five-film offline build continues |
| ADD26-D03 | Sixth clip present with volcano start and logo at different/nonround PTS | Locate event from actual frames, capture true inclusive range and adjacent context, not guessed duration |
| ADD26-D04 | Local clip has several volcano scenes or several Earth-logo states | Preserve candidates with witness images; resolve correct opening boundaries from actual visual sequence or request review; no arbitrary automatic lock |
| ADD26-D05 | Sixth intro logo interpreted as a universal design motif | Refuse source-specific branding as a transferable art skill; keep causal transition qualities |
| ADD26-Q01 | Question engine simply emits literal Q0–Q7 wording every iteration | Reject fixed-question behavior; derive next one question from `ActiveArtProblem` and earliest missing production decision |
| ADD26-Q02 | Question engine generates many plausible questions without source gaps | Refuse question-list theatre; require single highest-impact actionable missing decision and its discriminating evidence |
| ADD26-Q03 | Current gap is broken compiled prompt, not source understanding | Route to compiler/dataflow repair, not irrelevant source film reanalysis |
| ADD26-Q04 | Problem is unqualified face-turn condition across actors | Ask source-backed actor/view-specific question connected to canonical-conditioned draw state, not a generic eyebrow/color description |
| ADD26-Q05 | Original art result changes and creates a new high-impact deficiency | Next question is derived from this NEW output gap, not reused from last iteration's template |
| ADD26-Q06 | Question answer says 'more details and vibrant colours' with no operation | Keep unresolved; ask exact missing art decision; never silently compile prose as learned style |
| ADD26-F01 | Selection survey incorrectly treats sparse overview as every-frame vision | Ledger preserves SURVEY_ONLY vs VLM_SEEN; no false completion |
| ADD26-F02 | One actual frame in a selected 16-window interval missing provider receipt | Cannot call selected-sequence frame-coverage complete; queue exact missing frame |
| ADD26-F03 | Native crop shown without full-frame or temporal context | Cannot use crop alone to assert whole-character/motion style decision |
| ADD26-F04 | Significant movement attributed to camera when source artwork is redrawn | Require distinction/uncertainty and appropriate connected follow-up before constructing motion skill |
| ADD26-S01 | Source face proportion rule transferred unchanged to unlike original character | Reject scene-specific fixed ratio; require actor-conditional design decision |
| ADD26-S02 | Source visual observation exists but chosen skill lacks producing operation | RESEARCH_ONLY; no qualified style job and no arbitrary art improvisation |
| ADD26-P01 | Runtime LLM tries to append its own aesthetic sentence to compiled prompt | Gateway rejects or it is impossible through production API; record causal style-authority trace |
| ADD26-P02 | Skill instruction changed; compiled image job unchanged despite selection | Fail causal mutation test and identify disconnected skill consumer |
| ADD26-P03 | Character scene brief changes actor species/view/prop | Compiler selects relevant skill branches and identity references, with no copying of source character |
| ADD26-I01 | Art looks weak but the image prompt is correctly compiled | Route to actual provider/art conditioning or missing decision as supported; don't declare compiler fix sufficient |
| ADD26-I02 | User rejects first art | Stop BEFORE animation-state/full video work; persist specific critique and next question |
| ADD26-I03 | User approves art but pose/layer family is poor | Hold at asset-review stage, repair canonical-conditioned variants, do not animate |
| ADD26-R01 | Agent switches environment after frame packet/answer but before skill compilation | Restore active problem, last question/answer/evidence, exact next operation, never restart source review |
| ADD26-R02 | Pending provider request unknown after interruption | Reconcile idempotency/remote task ID before retry or mark BLOCKED, never silently double-charge |
| ADD26-A01 | Audit only presents schemas/traces rather than real code consumers | Audit FAIL; require module:function and rerunnable test for each stage transition |
| ADD26-A02 | Agent claims 'style mastered' after mocked tests | Reject; label ENGINEERING_ONLY / ART_QUALITY_UNPROVEN |

### Audit ZIP MUST include (in addition to v1.3/24/25 evidence)

```
ADD26_PRESERVATION_COMPARISON.md        # v1.0→v1.1→v1.2→v1.3 preserved documents and only legitimate supersessions
ADD26_SIXTH_INTRO_LOCATOR_CONTRACT.json # source identity, visual boundary criteria, candidate frame sets, review-needed state
ADD26_QUESTION_DERIVATION_TRACE.json     # synthetic evidence -> actual current gap -> ONE question -> producing decision -> next question after changed output
ADD26_ACTIVE_ART_PROBLEM.schema.json     # persisted record, question/answer/evidence/skill/operation version linkage
ADD26_END_TO_END_LOOP_TRACE.json         # synthetic S0→S9 stage transitions and code-consumer references
ADD26_STAGE_IMPL_MAP.md                 # exact module:function, input/output schema, test and first/next consumer for every S0–S9
ADD26_TEST_RESULTS.json                 # true observed pass/fail/blocked, include console logs
ADD26_UNRESOLVED_AND_CONTINUE.md          # exact blockers, source6 state, next operation after audit authorization
```

If source 6 is present, the offline phase may perform local decoded-frame boundary location at no external cost, but must not claim a film-understanding VLM pass or perform paid operations. If absent, demonstrate locator behavior with a clearly **synthetic** clip fixture and preserve the blocker. Do not zip any MP4, private provider key, or huge generated cache into implementation audit. Include hash manifest and reproducible commands for independent inspection.

---

## 7. WHAT IS AND IS NOT PROVEN

The offline code audit can confirm runtime coupling and failure prevention, not that a model has correctly inferred all artistic design decisions. The actual learning phase proves its value through real source frames, specific conditional artistic decisions, skill-controlled Runware jobs, original art, user visual inspection and transferable results. The claim of 100% style fidelity is not warranted by a finite set of questions, a good specification or an automated test count.

**STOP FIRST RUN with marker:** `STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT`.
