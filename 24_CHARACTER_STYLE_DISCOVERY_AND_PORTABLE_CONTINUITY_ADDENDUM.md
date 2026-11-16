# VME v1.3 — ADDENDUM 24: Character Visual Identity, Cross-Film First Study, and Loss-Minimized Cross-Model Continuity

**Status:** IMPLEMENTATION REQUIREMENTS, not a claim that source films have already been fully studied or that professional-quality image generation has been proved.

**Use alongside the unchanged `Visual_Mastery_Engine_v1_3_COMPLETE_PREBUILD_AUDIT_SPEC.zip`.** This is a **narrow, additive amendment** to v1.3, not a replacement spec or a second implementation. Preserve the original approved 13-part system and all v1.1–v1.3 requirements. Where this document is more precise, it takes precedence ONLY for (1) initial reference-study order, (2) character-specific observation→skill→image production, and (3) portable semantic continuation between coding environments. All existing offline-build/audit-first, paid-call authorization, image approval before animation, full-frame-accountability, and style-owned prompt constraints remain binding.

## A. Decision FIRST: how much do we analyze before the first meaningful artistic iteration?

**Do NOT analyze all 242k-ish frames of all five films before the first original image. Do NOT learn the style from one film alone.** Use a broad five-film map followed by a targeted, truly deep, cross-film initial study, then first original artwork. Exhaustive full-frame processing remains an eventual objective, not a precondition to testing whether the image-production learning chain works.

**The first coding-agent session remains OFFLINE ENGINEERING ONLY:** read v1.3+this addendum → implement actual software → test it → deliver `VME_V13_IMPLEMENTATION_AUDIT.zip` → STOP for independent audit. The following real reference-study steps occur only after code audit and explicit vision-provider/source-upload/budget authorization.

### First real learning iteration: source selection and depth

**S0 — Map all five original films.** Verify bytes/sha/fps/PTS, build a complete frame index and overview of shots/visual events/actor occurrences without claiming automated indexing equals artistic vision. Survey the five films for major illustration families, distinct character classes, character closeups, expressive acts, hand/object interactions, turns, figure-in-world relationships, and complex scene-to-scene changes. Do not import old AnimationLab analyses.

**S1 — Select an initial connected evidence set from ALL FIVE films.** Begin with approximately **three distinct short contiguous sequences per film** (roughly 15 total; a planning target, not a rigid quota): (i) the most revealing character-design or face/expression sequence where present; (ii) a character acting, changing view, moving, or interacting sequence where present; (iii) a rich world/perspective/visual-finish sequence, including character integration where relevant. If a film lacks a suitable human/mascot actor in a particular portion, choose another genuine visual subject and document why. Favor contrasting actor types, roles, detail scales, viewpoints, expressive states and environments rather than choosing similar shots repeatedly.

**S2 — Study the selected sequences deeply.** For each selected CONTIGUOUS sequence, send its **actual consecutive frames** for verified VLM inspection within provider limits, with persistent per-frame semantic records. Inspect important states and source-native-resolution crops to resolve significant art decisions; preserve full scene context. Compare entire illustrations, actor identity, face design, limb relationships, expressive motion, environmental treatment and camera interactions AS A CONNECTED SYSTEM. Do not just label RGB, shapes or coordinates. Each high-impact claim must link to visual witnesses and appropriate contrasting cases. If budget forbids the planned consecutive-frame study, stop for a user choice; do not silently replace it with sparse sampling or declare it complete.

**S3 — Construct the first conditional character+world style skill cluster.** Use multiple characters from different films and contrasting source shots, not a single favorite character. Define what carries across different actors, what adapts to species/role/view/action and which differences are source-specific. Make actual producing recipes with real reference-image roles, style-owned prompt clauses, and the character/scene operations described below. Unknowns remain explicit and blocked where they control a high-impact style decision.

**S4 — Make first actual original outputs.** Produce at least one *unfamiliar original* fully illustrated character in a rich new scene, plus character state/pose planning, using a skill-selected model route. Show full-resolution visual proof and compilation/source influence; **STOP AT ART REVIEW if the artwork is weak**. No forced video. After acceptable art: derive matching pose/view and hand/prop art, inspect actual layers, get approval, then render moving proof. Later iterations rotate to unrelated original subjects and continue frame-level analysis across the entire five-film set.

**Do not call S3 a complete global model of Kurzgesagt style.** It is a cross-film, source-grounded candidate basis that earns trust through different original subjects. Source coverage and skill/art competence must be reported separately. The full five-film vision goal remains tracked to individual authentic frames.

## B. Character investigation: how to observe the *artistic decisions* that create a visual identity

A list of character parts is not adequate. Every selected character investigation starts from an **actual whole character in actual scene context**, and asks which deliberately coordinated drawing decisions make the character visually compelling *and* recognizable as a member of the films' broader illustration language. Its answer must teach the new-character producer how to make the equivalent **artistic choices for an unrelated subject**, not to reproduce the original character.

### B1. Build cross-actor witness groups, not one-character dossiers

For each significant candidate character-style mechanism, collect and bind: (a) an authentic character drawing at its normal display size and surrounding scene, (b) native-size face/hand/torso crops if materially needed, (c) relevant consecutive alternate poses/views or a clear UNKNOWN where absent, (d) one DIFFERENT actor or subject class from another source film, (e) one contrasting treatment/exception or documented absence, and (f) the original production problem this mechanism is supposed to solve. **Never pretend that all five films contain the same actor state.** One strong character witness + one unlike witness is an investigation starting point, not automatic proof of a universal rule. Expand witnesses until the proposed decision's scope is supported.

Review the whole visual effect BEFORE dissecting individual parts. Keep drawing and motion together whenever movement changes the drawing.

### B2. Exact high-impact artistic questions; pursue the branches that actually control the result

The investigator MUST generate and answer these **question families**, connecting them where relevant. They are prompts for intelligent visual investigation, not hardcoded supposed answers or a requirement to record hundreds of low-value measurements.

1. **Whole design identity:** What visible relations among head/body mass, outer silhouette, gesture, costume/skin/hair regions, facial emphasis and surrounding artwork make the complete actor feel deliberately designed? Which decisions persist across unrelated character types, and which change? What would a generic AI actor get wrong if it ignored these decisions?
2. **Silhouette at meaningful states:** For the same actor across neutral/acting/turning frames, what changes the externally visible shape, which parts overlap or disappear, and which design motifs remain recognizable? Does the pose read BEFORE seeing tiny facial details? Does the character remain attractive at scene scale? Distinguish motion by transformation from newly illustrated states.
3. **Character-specific proportions:** How are head/torso/limb/hand/foot features proportioned RELATIVE to character type, personality, current gesture and viewing distance? Which apparent 'proportion rules' are actually variations or exceptions? Do not copy one source actor's ratios as brand constants.
4. **Shape organization and art finish:** How do outer masses, internal region divisions, appendage junctions, contour/edge language, large versus fine details, colour/material blocks and highlights reinforce one coherent design? Which finishing decisions change with material or focal importance? Do NOT simply say 'flat vector', 'no outlines', or 'rich details' without genuine contrasting visual evidence.
5. **Face construction and identity:** What visible decisions about skull/head contour, eyes, gaze, brows, cheeks, mouth, nose/ear visibility, hair masses and negative spaces make the face recognizable? For the specific viewpoint and acting state, which marks move, which volumes redraw, which relationships change together? What must be retained across different expressions, and what may intentionally exaggerate?
6. **Expression as a WHOLE actor:** What is the coupled change in facial artwork, head direction, neck/shoulder/torso gesture, arms/hands and the position of nearby props? When does a face-only edit fail because the entire pose carries the expression? What is the actual sequence of anticipation, peak and settle in consecutive frames?
7. **Hands, arms, and contact:** In observed grasp/reach/pointing states, how do shoulders, visible upper/lower arms, sleeve/hand transitions, near/far occlusion, finger/prop boundaries, hand size and body support work as **one designed silhouette**? Which parts are separate moving artwork and which are newly drawn combined hand+prop art? What makes the grip credible without relying on generic tube rigs or numerical elbow fixes?
8. **Views, scale and environmental integration:** On front/three-quarter/profile turns, zooms, changes of screen size, or entry into a different world, what must be REDRAWN or simplified? How does the character's palette, material/lighting response, perspective, detail density and focus remain compatible with the whole scene? Which identity anchors remain despite changing geometry?
9. **Illustration diversity without style collapse:** Why do two DIFFERENT source actors, organisms or mascots look intentionally different yet feel like they belong in one visual production? What are the shared *methods of visual decision-making*, not shared objects, clothing, facial arrangements or fixed colour tokens? Find deliberate exceptions and encode the conditions.
10. **Construction-to-tool translation:** What original whole-actor image should be produced first, which actual reference images and edit route should influence it, what later views/poses must be created, and where will independent layer animation destroy the artistic silhouette? What visual specification must be known BEFORE a model call?

For every question actually pursued, record: `observed_whole_visual_effect`, `source_witnesses`, `contrasting_witnesses`, `artistic_relationships`, `candidate_cause`, `what_is_actor_specific`, `what_transfers`, `condition_of_use`, `expected_new_art_change`, `actual_art_operation`, `unresolved_production_ambiguity`. Reject answers that give only 'bold eyes', 'rounded body', 'appealing character' or bare ratios. Reject source claims without exact frame witnesses. Dig further ONLY where the missing answer would alter a high-impact artistic decision or creation operation.

### B3. How to convert character artistic decisions into a working skill, step by step

**Each candidate mechanism MUST traverse all transformations below and point to actual producing operations; do not skip from description straight to a prompt.**

- **C1 — Source visual witness:** record real whole actor + linked frame(s) + acting interval + crop(s) + scene context; separate `SOURCE_FACT` from inference; explicitly list `SOURCE_ACTOR_FEATURES_NOT_TO_COPY`.
- **C2 — Target visual capability:** express the result independent of source subject. Example: 'a novel stylized actor whose whole-body silhouette, face, gesture and material treatment remain cohesive through a three-quarter reaching pose'; NOT 'recreate the source scientist'.
- **C3 — Candidate relationship:** from the source witness pair/contrast, specify exactly which COUPLED design decisions appear to cause that quality; state counterevidence and any conditions under which the treatment differs. If evidence insufficient, keep the decision `CANDIDATE/UNKNOWN` and ask the next production-relevant question.
- **C4 — Conditional artistic decision:** encode an explicit condition over actor class, focal/background role, view, movement, interaction, material, intended emotional state and surrounding world; attach the resulting construction action, adaptation/exception rules, and what is permitted to vary for an original design. A successful style mechanism is NOT one fixed face template.
- **C5 — Art manufacturing recipe:** translate each selected choice to an existing or implementable operator: `PLAN_ACTOR_DESIGN` (typed content+skill decisions) → `GENERATE_CANONICAL_WHOLE_ACTOR` (actual model+style witness references) → `GUIDED_WHOLE_POSE_VIEW_EDIT` (canonical image+role-specific reference and change request) → `GUIDED_FACE_HAND_CONTACT_STATE` (when needed) → `PREPARE_LAYER_OR_FULL_DRAWING_STATES` → `RECOMPOSE_OR_ILLUSTRATED_FRAME_OUTPUT` → `ANIMATE_COORDINATED_STATES`. Each operation has exact input slots, selected frozen skill clause IDs, reference hashes, image dimensions, output asset contract, explicit capability, provider limits and a real error/fallback path. A step with no supported image-model capability stays unimplemented, not 'working'.
- **C6 — Frozen style-owned prompt production:** the style skill stores the actual visually specific *template clauses*, selected references and **the decisions that choose them**. At runtime the Director supplies only original subject, action and other typed content. The renderer/producer compiles a prompt using the selected skill decisions and approved original identity; it must NOT invent additional artwork aesthetics, proportion/face/style clauses or replace learned reference images on its own. Prompt rules must specify whole-art quality and inter-part relationships before local details, rather than exhausting the context with irrelevant parts.
- **C7 — Real original image + diagnosis:** produce novel actor/scene; compare art at whole-actor, face, hand/prop, actor-in-world and pose-family levels. If weak, fix the **source observation, conditional decision, style-owned template, image-conditioning/edit route or provider** responsible, not a generic validation message. Only successful unchanged transfer to other novel actors upgrades transfer claim.

### B4. Example of the transformation (ILLUSTRATIVE ONLY; not a finding from actual source footage)

**Bad scene-bound note:** 'Character X in film Y has two big blue eyes and a small body. Use big blue eyes.' This copies a subject and does not specify how to design new actors.

**Better source question:** 'Across different actor designs and views, which choices preserve readable facial expression and character-specific personality while allowing different eye shapes, head masses and body proportions? What changes together when the actor looks toward a prop or turns?'

**Candidate evidence description, ONLY after actual viewing:** `WITNESS_A`: source actor A's focal three-quarter head/torso/hand silhouette in consecutive states; `WITNESS_B`: unrelated source actor B with different proportions but similar *conditional coordination* of face, gaze, pose and action; `CONTRAST`: more simplified distant actor or different acting state. Record exact source frame IDs, role, appearance and actual visual differences in real work; placeholders are NOT evidence.

**Skill decision SHAPE (must be filled with real source-derived detail later):** `IF actor_is_focal AND action=look_then_reach AND view=three_quarter, choose the complete whole-character gesture composition before local facial/hand details; preserve the approved character's distinctive identity-bearing shape masses; design gaze and hand/object relationship jointly; generate the reach state as a guided full-character illustration rather than unconstrained independent limb parts; vary exact proportions, face and clothing with the original identity and source-supported actor-class decisions.` This illustrates conditional transfer logic, not an already proven Kurzgesagt rule.

**Actual compiled job:** `content = new_actor_id + new_prop_id + action + viewpoint + environment`; `style = selected_immutable_character_skill_version + conditional clause IDs`; `references = authenticated allowed STYLE_CHARACTER witnesses + APPROVED_CANONICAL_ORIGINAL_ACTOR image for subsequent states`; `operation = authorized image_generate/edit`; `outputs = 1080p-compatible original whole-actor PNG/WEBP + pose/state metadata`; `trace = selected decision IDs → actual prompt bytes and image-reference hashes → image output hashes`. Use actual provider caps; never pretend source references were sent if they were not.

**Prompt authority check, independent of quality judgment:** remove or alter ONE active skill clause → real compiled request changes, and the changed clause is actually sent; altering only an unrelated observation note must not alter the request; directly supplying custom ad-hoc 'Kurzgesagt style' text must be refused by the provider gateway. The test proves control flow, NOT picture quality. The real images determine quality.

## C. Building a character that remains appealing when it moves: upstream artwork production

1. **Decide the visual acting states before generation.** The original content supplies action needs; the style skill determines whole-design, expression and view-dependent illustration methods. Produce the minimum state plan sufficient to convey the actual action and camera moves, without generating unrelated variants.
2. **Canonical whole-body art first.** Produce the approved original character with a coherent design, good hands/head and desired viewpoint, visual identity and environment treatment. Do not begin from raw separated limbs or generic vector stick rigs.
3. **Build related whole-pose/view drawings from the same approved original identity.** Use canonical image reference and directed edits, not a fresh unrelated text-to-image each time. A changed head contour, hands, garment silhouette, limb overlap or contact requires suitable new drawing states. Preserve art finish across each state.
4. **Design hand and prop together** when there is contact. The hand, forearm, sleeve, held object, near/far-side visibility, shoulder relation and whole-body support should read as a single coherent acting pose before any segment is isolated.
5. **Use the minimum necessary separable layers** from real artwork; preserve each layer's pixel coordinates, alpha, masks, hidden artwork and anchors. If segmentation worsens the art, prefer approved whole-state drawings over destructive limb splitting. SVG may be used for simple motion guides, diagrams or masks but not as the default illustration engine for sophisticated characters.
6. **Only then animate the approved drawings** using the established renderer and contact/pose timing. Stop before full video if the actual original art or related character state family is poor.

## D. Portable continuation across Claude Code, Codex, Antigravity or other LLM environments

**Truthful promise:** it is possible to preserve all *explicitly committed* source evidence, observations, decisions, prompts, code, assets, question state and exact next operation across coding tools. It is **NOT** possible to export another model's hidden chain-of-thought, unfinished uncommitted tokens, or identical subjective cognition. Design for deterministic task-state reconstruction, not 'copying the model's brain'. A failure can lose only the current uncommitted packet/transaction; it must not silently lose already committed semantic work.

### D1. All project state is disk-owned, not chat-owned

Define a portable workspace relative to the project root, with at minimum:

```
state/STATE.json                       # schema, last completed unit, current run/stage
state/ACTIVE_QUESTIONS.jsonl          # precise unanswered and answered artistic questions
state/ARTISTIC_DECISIONS.jsonl        # witness-linked proposals, conditions, exceptions
state/SESSION_NOTES.md               # explicit semantic recap incl. strongest counterevidence
state/CONTINUE_HERE.md               # one exact next action and exact current state
state/SOURCE_LOCK.json               # film SHA256, relative paths, indexed PTS/timebase
state/PENDING_JOBS.json               # provider job IDs, reconciliation, spend, permissions
state/REVIEW_STATE.json               # user approval and held blockers
store/vme.sqlite                      # transactional witness/frame/job/iteration records
skills/                               # full pinned skill folders, recipes, refs, examples
artifacts/                            # original generated images, masks, layers, sample clips
logs/                                 # append-only events, raw model observations, errors
```

The exact names may be mapped to existing v1.3 components, but each content class MUST be preserved in durable files. Never replace original detailed frame observations with a compressed summary; summaries are indexes pointing to real source-linked records. Keep produced image bytes, reference image bytes, generated prompt/job payloads and identity anchors where required to continue. Keep original film files separately on the user's disk; use SHA256 to rebind them on another computer, and STOP if bytes differ.

### D2. Atomic persistence at each reasoning boundary

Each small unit of artistic work is: `frame packet` OR `one unanswered question → supported answer/UNKNOWN` OR `one candidate style decision` OR `one skill revision` OR `one provider image/edit job` OR `one user approval` OR `one render/asset operation`.

- **BEFORE an operation:** persist exactly its input refs, IDs, active question, current competing explanations, expected outputs, dependencies, selected frozen skill version, planned tool/provider call and idempotency/task ID as `PENDING`; ensure prior committed work is untouched.
- **DURING a long operation:** write useful explicit partial observations/decisions to durable progress events at bounded intervals; don't rely on a model keeping a long internal unsaved reasoning chain. Full raw model response and essential image/text results must be stored when returned.
- **AFTER a step:** validate that source hashes/IDs match; write artifact and semantic result to a temporary file; fsync and atomically rename; transactionally advance the SQLite ledger (WAL with correct checkpoint/export handling) to `COMMITTED`. Only then schedule next work.
- **On failure:** recognize `PENDING/IN_FLIGHT/RESPONSE_SAVED/COMMITTED`, replay only uncommitted bounded work; never discard committed observations or blindly repeat an already paid provider call. If provider cannot query a pending job and a repeat may be billable, STOP for human reconciliation instead of silently duplicate charging.

Never claim exact semantic continuation if the unresolved reasoning was not written. Preserve it as explicitly `UNRESOLVED`, reopen its actual visual witnesses and continue fresh instead of inventing its answer.

### D3. Cross-environment handoff that works without the previous chat

Required user-visible commands in the implemented engine (names may be adapted but must exist and be documented):

```
vme status --detailed
vme checkpoint --reason "switch-coding-agent"
vme export-handoff --output VME_PORTABLE_HANDOFF.zip
vme import-handoff VME_PORTABLE_HANDOFF.zip --workspace NEW_WORKSPACE
vme resume --verify
```

The export must include versioned code/contracts/tests, all committed substantive evidence and learning data, original-content briefs, source hashes/PTS ledgers, exact current skill versions, compiled prompts/references, generated artwork/layers, unresolved questions, failure diagnosis, audit logs, human-review status, pending provider-task identifiers, and `CONTINUE_HERE.md` with a **single executable next step**. Exclude secrets, paid tokens, caches and enormous original MP4s; require user to place/rebind originals separately using exact SHA256. Export from a coherent SQLite snapshot (not a naked WAL database copy) and a hash-verified file manifest. If an artifact is omitted because of size, declare its content hash, required path and `MISSING_ARTIFACT` until restored—never imply complete continuation.

**Cold-start protocol in any new tool/model:** open repository and `CONTINUE_HERE.md` → run import and hash/dependency verification → read the *full active evidence and question records*, not only summary → inspect the last relevant actual source frames/art and current source–skill–provider trace → check pending external job statuses and authorizations → run a tiny resume fixture → continue the single stored next operation. No rerun from film start, no switch to an unqualified alternative model/skill version, no silently lost artistic constraints.

### D4. Required cross-tool failure drills BEFORE full paid analysis

- Force-kill mid-frame sequence; start in a fresh coding-agent chat without the old transcript, verify identical committed frame and question records and the exact next PTS.
- Force-kill after vision/image provider submission but before receipt; import on different environment and verify same job is reconciled instead of charged twice (or correctly BLOCKED if not reconcilable).
- Force-kill between a source observation and skill conversion; verify original evidence, open question, candidate alternatives and next T-stage survive without fabricated conclusions.
- Force-kill during character pose or mask generation; verify canonical actor SHA, state dependencies, original assets and pending edit request survive.
- Corrupt/drop an asset or original MP4; verify import refuses to claim a complete workspace.
- Switch from Claude Code to a separate model using ONLY the handoff ZIP and source MP4s; reproduce skill-owned compiled prompt bytes for a frozen fixture and resume exactly from the declared step.
- Reproduce an independent visual review packet after import and verify user rejection/approval cannot disappear or be silently bypassed.

**Success measure:** identical committed artifacts, evidence, skill versions and deterministic next compilation; no duplicate paid work and no lost explicit semantic decisions. Exact private thought-state preservation is NOT a meaningful or achievable success measure.

## E. What the coding agent must add during its FIRST OFFLINE BUILD (before paid analysis)

This addendum is mandatory alongside v1.3 and is **not permission to start the paid artistic-learning run**.

- Implement initial five-film mapping and the planned cross-film contiguous-sequence selection mechanism as *code/data contracts*, not real paid source conclusions.
- Implement the above character witness grouping, question traces, character-conditional style decision schema, skill-owned prompt clauses, and character art/pair-view/hand-contact producing routes with fixtures. Exercise `C1→C7` on explicitly fake synthetic examples; never call that proof of learned Kurzgesagt style.
- Implement persistent semantic work units, transactional resume and real `export-handoff`/`import-handoff` cold-start with complete file manifests and database consistency, including interruption drills. Do not just write a generic README saying 'resume supported'.
- Add requirements and tests for this addendum to the implementation matrix; show source modules, tests and actual run logs. If unable to meet any requirement, mark BLOCKED and do not say the handoff is complete.
- In the implementation audit ZIP, add `CHARACTER_STYLE_WITNESS_DEMO.json`, `CHARACTER_STYLE_SKILL_TRACE.json`, `CROSS_ENV_HANDOFF_TEST.json` (or equivalent real evidence) and describe first real-learning phase as S0–S4 above.
- **STOP** after offline build+audit ZIP; have the user upload it for independent code review. Do not automatically upload source film frames to a third-party provider or spend Runware credits.

## F. Hard-stop mistakes

- Observing single-source actor proportions as immutable general style constants.
- Calling a style paragraph a production skill without actual prompt clauses, reference bytes and callable operations.
- Allowing the runtime LLM to add any untracked artistic prompt text after the skill is frozen.
- Independently redrawing every pose from text without original canonical actor image conditioning.
- Declaring separate limb sprites correct merely because individual sprite images look attractive.
- Mistaking 100% frame indexing for 100% vision-model artistic inspection.
- Processing only one film and asserting global style identity is learned.
- Claiming model-to-model transfer of private hidden reasoning, or exporting only a short summary and calling that lossless resume.
- Resuming from an incomplete/mismatched source/asset/skill version without an explicit warning and repair.
- Charging twice because a pending provider task was not reconciled after a restart.
- Starting paid image/VLM generation or an automatic full render during offline build.

**Acceptance principle:** The learned character skill must eventually produce **different attractive original characters** that share the *source-supported visual decision language* while retaining distinct silhouettes, faces and personalities; remain coherent in viewpoint, expression, whole-body pose, hand/prop interaction and their illustrated worlds; and be proven by actual images/animation. The coding agent's first build must implement the causal path that can support that test, but cannot claim this artistic result before real provider experiments.
