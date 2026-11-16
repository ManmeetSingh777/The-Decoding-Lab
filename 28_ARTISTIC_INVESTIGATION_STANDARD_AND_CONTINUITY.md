# VME v1.3 — Addendum 28: Operational artistic-investigation standard, knowledge fidelity and cross-model continuity

**Authority and purpose.** This is an ADDITIVE, mandatory operational protocol for the existing Visual Mastery Engine, implementing the original 13-part system, v1.3, Addenda 24–27, and the 24-item Comprehensive Root-Cause Repair Contract. It does not substitute for the repair contract, source films, or actual human artistic review. It sets **how to investigate**, **what counts as a construction-level finding**, **how to produce the next question**, **how to preserve the result**, and **how to resume without lowering that standard**. Apply this standard to the real S0–S9 path and code, not only documents or synthetic drills. It is a replacement for any weaker vague observation quality rule where those rules conflict. Do not replace the requirement to process every actual frame in the 15+1 selected intervals with representative frames.

## 0. The standard is an operating method, not a checklist of art adjectives

**Purpose:** produce trustworthy, reusable methods that cause high-quality *original* illustrated images, related character states and well-directed animation. The primary objective is **accurate, source-evidenced construction decisions with an actual production consequence**, not maximum words, geometric measurements, aesthetic praise, or the number of questions answered.

We can control documented software behavior, durable evidence, prompts, references, and operation inputs. We **cannot guarantee** a vision model interpreted artistic intent correctly, know the source studio's hidden construction files, reproduce the image model's internal choices, or ensure professional results from syntax alone. Represent these limits explicitly. Accuracy > unsupported specificity. Where no observed cause is distinguishable from an alternative, record both and a discriminating evidence/production experiment.

**Seven invariants that every investigator invocation must be taught and obey:**

1. **Whole result first.** Begin with the complete frame/shot and its role in the illustrated world, focal hierarchy, motion and attention. Zoom into parts only to explain a consequential whole-result quality; always return to full-frame consequences.
2. **All actual source frames within selected intervals.** Each has exact original source/stream/PTS/frame/hash, verified image submission, and a distinct semantic observation; packet overlap/context is not counted as a target observation. Use small bounded packets and explicit previous/next boundary states. No skipping quiet frames; record what persists.
3. **Visible fact ≠ possible cause ≠ transferable rule.** Store these as separate typed items with source witnesses, uncertainty, counterevidence and condition ranges. Do not infer proprietary software or exact studio intent from pixels.
4. **Interacting decisions, not isolated categories.** Observe how silhouette, face, material, light, world, camera, action, sound, and attention work together, including how those relationships change through time. Add a new dimension if the film exhibits one not in the initial atlas.
5. **High-impact question is born from missing producing knowledge.** Ask the one decision-discriminating question for the active dependency; record many live gaps across a 2–5-related-problem cluster. Resolve connected questions within the same iteration; there is no fixed Q0–Q7 questionnaire, quota, or fixed number of questions.
6. **An answer is not a skill until it controls an executable creation choice.** Specify conditional applicability, exceptions, visual exemplar roles/bytes, the producing/editing/render operation, required character/scene assets, failure modes and exact skill-owned prompt clauses. If any consequential choice is unexplained, reopen the correct source investigation rather than add freewritten aesthetic instructions.
7. **Continuity belongs to durable evidence.** Preserve the complete committed observations, competing interpretations, open question and next input, operation/provenance graph, actual images and job state. No model may infer from a summary that it inherits the prior model's private thought process.

### Audit observation from actual repaired code (what must change)

In the inspected repair archive, `vme/vision/prompt.py::_TEMPLATE` instructs the vision model to inspect the whole picture and changes, but still allows free-text fields such as `focal_whole_artwork_state` to substitute for serious construction-level visual analysis. `vme/vision/contracts.py::validate_packet_response` validates field presence/hash and weak phrase filters but cannot establish deep accuracy. `vme/style/coverage.py::reverse_plan` starts from a finite set of predeclared needs. `vme/investigation/controller.py` provides the useful active-problem structure, but does not by itself teach a model to make expert artistic distinctions. The Comprehensive Repair Contract already targets missing references, over-broad completeness, dynamic reinspection and source→skill losses. **Repair the producing and reasoning paths together**, not by appending 100 more boolean gates.

---

## 1. Standardized source-analysis sequence: mandatory multiscale passes

**A film-vision unit** is an actual selected contiguous sequence and its preceding/following context. The system must run the passes below over a durable sequence investigation—not by calling one VLM prompt and assuming that it mastered everything. Passes may share an API request when the provider genuinely permits the images/context without truncation. Record which pass has been performed and source data actually seen.

**Pass 0 — establish source truth and context.** SHA256/stream ID, true PTS/decode-order versus presentation-order, frame count, resolution, source role, sequence start/end inclusive and adjacent context; verify no altered/decimated/substituted footage. Identify source shot and whether subtitles, narration/audio, other source elements are actually present and whether their content is accessible; UNKNOWN if no actual audio analysis. Keep film survey (`SURVEY`) distinct from deep study (`VISION_SEEN`) and art knowledge (`EXPLAINED`). The sixth volcano→Earth logo must be explicitly visually locked; do not guess its boundaries.

**Pass 1 — whole-shot perceptual structure.** At natural viewing size, identify every visually consequential focal subject/world/graphic, changes in meaning/attention, scale/depth order, whole-scene complexity, principal large masses and colour-role grouping. Identify entry/exit context and the most salient visual moments. Record *observed effects*, not a style conclusion. Do not let a camera movement be named just because two frames differ; distinguish possible layer motion, object movement, redrawing and camera transformation.

**Pass 2 — exhaustive actual frame and temporal continuity.** Send each target frame to an actual VLM (with correct image count/cost), not only a hash or embedding. For each frame, reconcile actor/object/drawing-state identities and open events from previous committed boundary. Describe what appeared, disappeared, moved, changed geometry, changed role or persisted. Preserve *co-occurrence*: actor gesture while background moves, light changes while head turns, one asset passing behind another, etc. Include comparisons to actual neighbor images, and note why unchanged details remain relevant. For first/last frame of packet, reconcile ongoing phenomena across boundary. Do not claim per-frame source inspection from generated text alone: store provider request image manifest, receipt and raw response. If provider downscales, native-detail remains separately pending where needed.

**Pass 3 — whole-artwork decomposition for specific observed events.** For high-impact moments, inspect **whole result → coherent large shapes/subject identity → medium-level part relationships → fine visual finish → back to whole-result**. Follow contours, negative space, head/torso/limb/hand/prop relationships, costume surface panels, eye/mouth anatomy, edge treatment, environmental structure, colour roles, material and lighting regions. Decompose only until the visible aesthetic difference can be specified as a **choice a production method could make**; don't use tiny arbitrary coordinates as a substitute for learning. Source-native crops maintain full-scene witness parent IDs and orientation/scale; a crop alone cannot prove global hierarchy.

**Pass 4 — temporal mechanism and meaningful movement.** Track stable drawing components versus newly appearing/disappearing/redrawn artwork; measure actual visible relative timing/order, contact, anticipation, body-weight cues, changes in eye/facial/head orientation, foreground/world motion, focus and transitions. Separate **OBSERVED CHANGE** from **possible implementation** (`camera`, `transform`, `pose replacement`, `deform`, `new drawn layer`) when ambiguity exists. Derive what alternate illustration states an original actor/world would need to animate an equivalent effect. Audio-dependent observations require real audio or transcript evidence; no invented sync.

**Pass 5 — cross-character/cross-world and contrast.** For each consequential candidate design decision, select at least one unlike original reference subject/scene and a meaningful exception or evidence gap. Compare at the **relationship level**: what stays stable, what changes under view/material/role/scale/acting, why a naive universal ratio/palette/pose would fail. Do not use exact source actor appearance as a brand rule. If evidence only applies to one class, scope decision to that class and keep other classes UNKNOWN.

**Pass 6 — reverse-construction and unanswered-decision search.** Pretend a new, unrelated scene must be produced *today* with only the documented skills. Decompose required original assets and states; for each significant appearance/motion choice ask whether a skill and producing operator actually decide it. Search for absent pairwise/cross-system interactions (not just missing categories), unsupported art assumptions, unknown environmental changes, missing expressions, masks, anchors, depth and character/world integration. Where a choice remains, construct the next focused investigation. A coverage cell saying `SUPPORTED` because one item in the category was studied is insufficient.

**Pass 7 — evidence-to-operation synthesis.** Create source fact → candidate explanation → conditional visual decision → executable recipe → frozen skill clause/reference → actual provider-visible operation. A single observation cannot claim causal truth just because the explanation sounds plausible. Preserve alternative hypotheses or a user-visible uncertainty. Propose an exact observable visual difference in unrelated output if this skill decision is used vs ablated. This synthesis is not qualified until genuine original outputs are reviewed.

**Pass 8 — whole-art coherence inspection before candidate skill freeze.** Review the entire proposed original visual-construction program for scene, characters, worlds and moving relationships: which high-impact visual choices are delegated to a model improvisation? Which clauses contradict or overpower others? Which required reference images or animation states have no actual producer? Resolve those source/skill/operation holes *before* releasing an image job. Stop honestly if required evidence/capability cannot be obtained, rather than auto-completing a checklist.

### Exact VLM instruction discipline

- Each invocation includes `protocol_version`, `pass_id`, `source/sequence/target frame manifest`, real submitted image(s), adjacent boundary/scene memory, `active connected quality cluster`, `one controlling unknown`, `relevant coverage gaps`, typed output schema, and examples of *weak vs construction-useful reasoning* labeled synthetic. Never append a generic independent styling request.
- Small packets (chosen against real provider limits) are consecutive and overlap only in context. Dynamically allocate extra native-resolution crops and cross-film contrast for the unanswered **production decision**. There is **no arbitrary three-crop ceiling**.
- For each target, output its identity, entities/drawing states, visible shape+layer/material+attention relations, precise delta to previous, linked simultaneous events, uncertain interpretation, quality-relevant observation and source witness region. An unchanged frame can have an unchanged record tied to earlier state—not a fabricated change.
- Every API response is stored raw. The parser must preserve unknown/unparseable responses and retry within an approved budget rather than invent content; a structure-valid answer is not automatically semantically sufficient.
- If packets become long or context degradation is detected, split work into committed micro-packets, not sparse sampling. Never spend or upload source data without explicit approval. In a model switch, require identical protocol version or an explicit migrated version with calibrated comparison.

---

## 2. Complete visual-phenomenon atlas: where to look (not prewritten answers)

The atlas is a **search map**, never a permanent exhaustive ontology, not a checklist whose nonempty cells prove mastery. Apply at **whole frame, focal object/actor, relevant parts, successive frames and cross-film contrasts**, then investigate relations among discovered phenomena. Mark each entry `VISIBLE_RELEVANT / VISIBLE_LOW_IMPACT / NOT_VISIBLE_WITH_WITNESS / UNKNOWN_NEEDS_INSPECTION / CONTRADICTED`, and cite actual frames or the specific scope exclusion. `NOT_VISIBLE` is per witnessed interval, never a claim of global absence. Add new entries when real source artwork exhibits something else.

**A — Whole-scene visual language:** information hierarchy, composition and negative space, focal contrast, clarity at viewing size, image-wide rhythm/complexity, foreground-midground-background grouping, coordinated detailing versus deliberate simplification, global art finish, illustrative density and graphic metaphor as actually visible.

**B — Characters and living actors:** overall silhouette and legibility, shape-mass organization, varying anatomical proportions, personality encoded in relative shape and gesture, skull and face contours, eyes/eyelids/gaze/brows/mouth/ears/hair, expression as whole pose, costume geometry, part junctions, materials, hand shape, grip, foot-ground contact, weight and balance, alternate viewpoint redraw, identity through acting/scale, and texture/detail hierarchy.

**C — Non-character objects:** designed object topology, silhouette, readable functional shape, material separation, paneling/edges/contours, structure/scale, prop affordances, seams, in-world labels/graphics, relation to actor hands, material/lighting adaptation, and complexity matched to focal role.

**D — Environments and illustrated worlds:** environment type, world depth logic, near/far detail, overlapping artwork, architecture/nature/space/biology conventions as present, ambient elements, atmospheric separation, world response to motion, colour/light continuity, clean world plate requirements, background states, parallax support.

**E — Shape and image construction:** contour curvature, intentional irregularity, negative space, overlap order, silhouette hierarchy, relative ratios *conditional on actor/material/view*, internal shape segmentation, boundary softness, edge/no-outline/outline choices, anti-aliasing, masks and visual hierarchy of big/medium/small detail.

**F — Colour and material design:** palette *roles* rather than copied hex values, hue/value/chroma relations, warm/cool/focal/background adaptation, material-specific colour changes, repeated accent roles, local/global contrast, reflected/bounce effects where visibly justified, form-shadow planes, gradients, gloss/matte differences, physically plausible versus graphically stylized choices.

**G — Light, atmosphere and finishing:** directionality versus decorative drawn light, rim/edge highlights, cast versus form shadows, light-shape boundaries, occlusion, background glow, atmospheric effects, outline/softness/noise/texture hierarchy, visual polish and how finish changes through a viewpoint or focal shift.

**H — Spatial system and camera:** projection or perspective cues, scale/depth hierarchy, parallax, apparent focal length only when justified, screen-space/world-space distinction, framing transitions, object vs camera motion, redraw/view-state requirements, hidden/revealed geometry, focus/attention change with motion.

**I — Character motion and acting:** gait/weight support, anticipation/reaction/follow-through, pose-to-pose silhouettes, asymmetry, contact constraints, gesture staging, relation of gaze and prop contact, face/body linked changes, grip release and catch, pose interpolation versus redraw, simultaneous acts.

**J — Motion/world choreography:** multiple moving entities, interactions, event dependencies, temporal layering, concurrent narrative beats, rhythm and intervals, static-vs-active world, intentionally held frames, synchronized motion, response and after-effects, clarity under complexity.

**K — Transitions, editing and visual attention:** cut meaning, cut placement, speed/hold, match transitions, metamorphoses, wipes, drawn effects, viewpoint continuity, reveal timing, attention hand-off, motif recurrence, foreground-to-world bridging, visual vs audio-led editing.

**L — Explanatory visual grammar and audio:** symbols/diagrams/labels, visual metaphors, how text is integrated with illustration, visual density matched to explanation, narration and audible effects when actually accessible, music-to-beat relations when observed, causal explanation through simultaneous change.

**M — Output-specific craftsmanship:** resolution/edge treatment, how fine detail survives final display size, crop/headroom, readable framing, cohesive scene-to-scene design, character identity at different shot sizes, compositing errors, source-dependent limitations due to 720p/1080p.

**Cross-dimension relationship probes (not a fixed exhaustive list):** `character×world`, `silhouette×gesture`, `face×head turn×light`, `hand×prop×sleeve×body support`, `colour×material×lighting`, `scale×detail`, `viewpoint×redrawn art×depth`, `camera×attention×scene complexity`, `transition×world continuity`, `audio×cut×visual event`, `foreground×mask×occlusion`, `character identity×alternate pose`, `multiple actors×contact×choreography`, `whole-frame readability×fine detail`. For every observed simultaneous change, ask which linked choices are necessary and which are merely co-occurring; do not invent causality.

**Atlas search algorithm:** (i) record what is visibly salient and relevant in the sequence; (ii) enumerate all relevant component phenomena at meaningful scale; (iii) trace actual dependencies and changes; (iv) discover uncovered aspects *including outside this atlas*; (v) form the next missing production choice. Do not run an expensive fixed 13-category essay on every frame. Store each frame's compact evidence record linked to rich scene/actor/relationship dossiers and native crops where causal decisions depend on them.

---

## 3. Teaching the investigator to ask *the right* question

### 3.1 The exact decision-driven question algorithm

The `ActiveArtProblem` owns **multiple connected missing decisions**, not a single category. For each unsatisfied producer dependency:

1. **Start from outcome:** state the visible quality the original-output skill needs to create, including its effect on whole character/world or scene. If no original output yet, define the intended construction capability from real source witnesses and a typed first-iteration brief.
2. **Find the earliest broken handoff:** source visible fact → explanatory visual relation → conditional new-subject choice → producing operation → skill/reference → compiled provider request → actual asset/animation. Do not investigate source again for a known compiler bug.
3. **Precisely identify unknown:** name the missing *choice a producer would otherwise improvise*, not a general artistic category. Examples: which head contour must redraw when gaze shifts; which prop/hand boundaries must be drawn together at a grip; which foreground layer can cover the focal actor during an apparent camera move.
4. **Bind strongest available real contrasts:** whole shot, exact state-changing frame span/crop, unlike actor/environment or exception. List what those frames could and could not establish. Prefer **minimal sufficient but high-information evidence**, then expand if ambiguous.
5. **Form one discriminating question:** `For [new-brief situation + condition], which [specific linked artistic construction decision] best creates [observable quality] across [source witnesses/contrasts], and what evidence would distinguish [plausible alternative A] from [plausible alternative B]?` Must identify the expected `OperationNode`, which actual source detail could answer, and why the answer matters. Do not emit a generic Q0–Q7 or invent a random list of candidate questions.
6. **Answer with observed relationships first:** enumerate visible evidence **and contrasts**, explicit counterexamples and uncertainty; then proposed conditional method, exceptions, reference roles, concrete function/model edit, expected visual effect and failure case. If evidence doesn't discriminate, return `UNKNOWN + next exact frame/contrast request`, not a polished false answer.
7. **Update the shared model:** store decision independent of broad category, relationship edges and revision; mark what was *actually* learned vs hypothesized; recompute affected completeness dependencies. Multiple significant gaps remain in the queue; continue through the connected cluster before image-job compilation.
8. **Predict observable effect:** show how adopting the answer changes frozen skill inputs and the image/asset operation. If no specific downstream change is possible, classify it as `SOURCE_DESCRIPTION` or `UNACTIONABLE` and investigate another consequence.

### 3.2 Answer standard — construction-grade, not adjective-grade

For every important conditional decision, provide all of:

- `VISIBLE_EFFECT`: source-based meaningful whole-result quality, with real witnesses and region; never just "premium" or "pretty".
- `LINKED_OBSERVATIONS`: minimum relevant whole-frame, part, temporal and cross-subject comparisons; identify which was directly seen vs inferred.
- `ARTISTIC_MECHANISM_HYPOTHESIS`: the particular visible relationship likely causing the quality; uncertainty and alternatives.
- `NEW_SUBJECT_CONDITIONS`: for what classes, scale, viewpoint, action, material, light and focus role it applies; not an indiscriminate brand formula.
- `PRODUCER_DECISION`: the exact choice to make, with branches, dependencies and exceptions; state what cannot be inferred from film alone.
- `ACTUAL_CREATION_RECIPE`: registered operator, real inputs, visual-reference roles, masks/anchors, output dimensional/identity constraints, animation states and downstream consumer.
- `SKILL_AUTHORITY`: exact frozen decision/clauses plus evidence lineage; no freehand stylistic prompt invention.
- `EXPECTED_CAUSAL_CHANGE`: predicted visible difference between using and withholding the decision in a new original output; if weak, investigate before qualification.
- `CONFLICTS_AND_UNKNOWNS`: counterevidence, alternative explanations and exact source/production gap, with one next question if needed.

The question engine must **not** pad answers by inventing detail. A short answer with all essential discriminating information can be sufficient; a 10,000-word inaccurate guess is worse than UNKNOWN.

### 3.3 Paired synthetic calibration example (NOT source-derived facts)

**Weak observation:** "The space explorer has expressive eyes, nice shadows and smooth limbs." Fails: no frame, no viewpoint, no linked design relationships, no contrast, no new-character production action.

**Useful *hypothesis* example (synthetic):** "At the fictional hero's three-quarter head turn, the near cheek contour grows in visible prominence, far eye is partially hidden, helmet rim moves in front of the far brow, and neck connection shifts under the near shoulder. The world illumination stays fixed while the character's illustrated shadow planes are redrawn; the gaze moves before the hand reaches the prop. Witnesses: synthetic full frames F10–F26, head/hand crops, a contrasting differently proportioned fictional character. Hypotheses: authored alternate drawings vs deformable mesh; the pixels alone do not establish which technique the source studio used. New original action requires (i) an approved canonical drawing, (ii) front/three-quarter head states and expression variants made through skill-selected guided edits, (iii) a hand+prop contact state and (iv) coherent world lighting. The prompt skill must choose reference roles and exact rendering operations based on view and action. A flattened head rotation without redrawing would fail the intended contour/occlusion quality." **Do not carry fictional contour specifics into genuine Kurzgesagt knowledge; this only teaches the answer structure.**

---

## 4. Prevent quality loss during observation → skill → prompt → artwork → animation

**Source evidence is never compressed into ungrounded prose.** Preserve the raw source frame identities, byte-hashed visual exemplars when consent permits, actual VLM raw answers, explicit visible facts, competing mechanisms, chosen condition branches, constraints, exception/negative cases, and named operations. Summary is a navigation aid, not authoritative knowledge.

At each transformation record a lineage DAG with typed edges:

`frame/crop → observation → contrast/relationship → candidate mechanism → conditional decision → operator recipe → immutable skill version/reference/clauses → compiled image/edit job → provider result → approved asset/state → animation event/composition → actual rendered frame/video review`.

**Do not let a model-owned prompt fill a missing decision.** A determined compiler chooses skill-owned clause bytes and references; a content-only brief supplies original subject/action/world. Exempt engineering fields like PNG size and transport identifiers are labeled explicitly, not artistic evidence. Style-provenance claims describe *instructions given to the provider*, not the model's private pixel-generation process. Save unsupported output appearance as an unresolved defect/uncertainty.

**Source→skill preservation:** Never collapse two distinct facial or shading observations because they share the same coverage category. Preserve identity by phenomenon, context, conditions, witness set and revision lineage, not `dimension_tag` alone. Pair every style hypothesis with what it would change in actual creation. If a conflict remains, restrict scope or defer; do not silently merge. If a critical decision has no real operator, report `MISSING_OPERATION` and stop capability promotion.

**Skill→art preservation:** The exact *provider-visible* request includes every required relevant skill clause and required visual reference under real provider limits. A reference is an actual hashed image byte or approved resource, not a filename in prose. If max reference count is exceeded, choose a planned skill-owned sequence of supported edits; never silently drop a mandatory reference. Maintain approved canonical character identity in subsequent head/hand/pose states. Record actual reference consent and source restrictions.

**Art→animation preservation:** Plan actor/world clean separation, layer dependency, hidden surfaces, full-pose drawing states, contact, alpha/mask, anchor, stage position and view/camera changes *before* asset generation. Do not pretend one complete raster character is an articulated rig. When movements demand genuinely different silhouette/occlusion, use redrawn approved states or an actually implemented alternative method. When the exact operation is missing, do not render a generic sprite-pan as a substitute.

**Learning progress:** Track `OBSERVED / CANDIDATE / EXECUTABLE / ORIGINAL_ART_TRIAL / TRANSFER_QUALIFIED` per **actual capability**, never per top-level category. Human-art rejection may reopen previously supported decisions, update source questions and invalidate only downstream stage hashes. Qualified still images do not imply qualified character acting or multi-shot animated transfer.

---

## 5. Standard-preserving model/environment handoff

### 5.1 The portable 'Investigation Capsule' (additional to existing Addendum 24 state)

For each active sequence, connected cluster and current question, commit these objects transactionally:

1. `protocol_id/version/hash` of this standard, source set and acknowledged model-specific limitations; not just a title saying "deep analysis".
2. Full `SOURCE_LOCK`: film/stream SHA, correct filenames, resolution/PTS/frame hashes, selected interval and sixth boundary lock state; actual source files remain externally rebound by matching bytes.
3. `FRAME_COVERAGE`: each target's real sent/verified/unknown/native-detail state, request/receipt, target manifest and any missing ranges; packets with open event boundary states and exact first uncommitted frame.
4. `VISUAL_EVIDENCE`: raw model responses, verbatim source facts, relative whole-image/detailed observations, event/part identities, native crop coordinates/bytes or immutable hashes+rebind instructions, contrasting witnesses, and uncertainty.
5. `ACTIVE_ART_PROBLEM`: complete current 2–5 linked deficiencies, salience/order reasoning, competing causes, single controlling question, prior answered questions, rejected explanations, source evidence needed next, exact affected operator.
6. `STYLE_MODEL`: complete conditional decisions with individual IDs, relations, applicability/exception/negative cases, outstanding conflicts and original-output review notes; frozen skill versions, prompt clauses, reference roles+bytes and actual provider job hashes.
7. `SCENE/CHARACTER`: original subject and action plans, approved canonical art, view/face/hand/grip state plans, masks/clean plates/layer coordinates, rendered evidence and human approvals, if any.
8. `EXTERNAL_JOBS`: paid/nonpaid, provider/model/version, actual request/remote ID, consent, budget reservation, response bytes/receipt or uncertain state. Never replay uncertain charged requests automatically.
9. `CAUSAL_AND_QUALITY_LOG`: prior output errors and root-cause attribution, changed rule/operator, effect observed or not, rejected patches, and exact remaining unknowns.
10. `CONTINUE_HERE`: one **exact executable next operation** with input hashes, prerequisites, named stage, expected artifact, bounded cost/consent status and how it will be verified; plus a map to all above objects. No vague 'keep investigating'.

**Atomicity:** commit each bounded frame packet, question answer, branch decision, skill revision, provider job, image asset, user verdict and stage transition as a transaction; store raw evidence before summary and publish a versioned content manifest. A switch may lose an uncommitted response, but cannot truthfully claim it was preserved. If the source bytes or required artifact are unavailable in the new environment, stop with the exact missing SHA and relink path instead of producing imaginary evidence.

### 5.2 Cold-start algorithm for a new Claude Code/Codex/other model session

1. Import coherent SQLite snapshot + artifact manifest; hash-verify project code, protocol version, source indexes, crucial images/crops and skill versions. Source videos rebind by SHA; no false 'same film' from title alone.
2. Read the **actual protocol** (this file) and the effective spec precedence list; acknowledge which prior standards apply. Do not inherit the previous coding agent's guesses or resume from a terminal chat summary alone.
3. Load full active sequence/cluster/question plus all cited source facts, comparisons and counterevidence; inspect the last actual source full-frame/crops and prior original art if present. Rebuild open event, actor identity and art-state relations from committed structured records.
4. Produce a short **reconstruction of current artistic state**, not new artistic speculation: what is observed, inferred, contradicted and unknown; which decisions/skills are frozen, what is blocked, which one decision should be resolved next and why. Store this account as a handoff checkpoint; do **not** auto-author a new style rule merely from the recap.
5. Reconcile external pending jobs, authorization version and spending liabilities. Any unqueryable/uncertain paid submission blocks reissue pending user reconciliation.
6. Run a deterministic dry rehearsal on a *frozen synthetic fixture* through the same question→skill→compiler path, comparing actual input/output hashes to the previous environment. If different because of runtime/tool/model version, investigate the difference before modifying real knowledge.
7. Resume exactly one committed pending operation, or reopen the first incomplete packet/question using its stored actual inputs. Do not redo already committed frame spans or replace prior source observations with the new model's reinterpretation unless a targeted contradictory-evidence task requests it.

### 5.3 Provider/model drift controls

- Preserve the vision model ID, provider API request settings, image resizing policy, protocol hash and parser version for each completed batch; switching models **must not silently rewrite old observations**.
- New provider capabilities, context/image limits and pricing can change packet size and context method; these changes create a new `execution_profile`, not permission to skip frames.
- New model must work under the same investigation standard, type schema and decision logic. If the new model's understanding is noticeably shallower on a **small fixed witness set** with known human-reviewed observations, flag `MODEL_CAPABILITY_REGRESSION` and stop, rather than lower the standard; this calibration is about consistency and ability to cite evidence, not agreeing on aesthetic opinions without proof.
- For differences in artistic interpretation, retain both provenance-linked hypotheses and seek discriminating visual evidence. Do not overwrite an earlier accepted style decision just because the new model asserts something else. Decisions remain revisable with appropriate evidence.
- If a third-party model's API cannot accept the required image detail, task quantity or preservation constraints, adapt bounded packet size or use local native crops; if still inadequate, `BLOCKED_MODEL_CAPABILITY`, not pretend equivalent analysis.

### 5.4 Handoff drills before full film study

- Kill mid-per-frame packet, import elsewhere; committed frame count and active question unchanged, next target exact. Never duplicate already charged uncertain work.
- Kill after a complicated question's raw answer arrives but before its conditional decision is published; the raw answer, evidence and next T-step persist without inventing the unpublished decision.
- Change coding model with only handoff capsule+film bytes, then reproduce a pinned skill compiled request byte-for-byte, including reference hashes; compare recent witness interpretation on calibration frame set.
- Restart while significant `face×view×light` or `hand×prop×actor pose` relation remains UNKNOWN; it must remain visible and actively unresolved, not disappear because category says complete.
- Reject art, export/import, resume, and show same defect→question→revised-skill invalidation path.
- Corrupt/missing source image/reference/skill artifact → exact blocker instead of speculative continuation.

---

## 6. Mandatory modifications to actual modules, tied to the previous 24-item repair

Implement this protocol in production paths and consumers **in addition to all R01–R24**:

| Existing area | Required code change |
|---|---|
| `vme/vision/prompt.py` | Versioned multi-pass requests. Distinct whole-frame, temporal, relationship, candidate-mechanism and reinspection instructions; include active scope/question and relevant evidence. Use *actual image inputs*; no static questionnaire disguised as prompts. |
| `vme/vision/contracts.py` | Rich evidence/lineage fields, per-frame semantic+temporal state, source-vs-inference distinction, answer-to-production link; validate source identity without claiming accuracy from field presence. |
| `vme/vision/runner.py`, `vme/vision/claude_adapter.py` | Bounded every-frame packets, correct provider SDK/limits/IDs, native crops, cross-packet continuity and real receipt state; offline fakes strict. Preserve high-resolution work where available without pretending 720p is 1080p. |
| `vme/investigation/controller.py`, `vme/investigation/evidence.py` | Dynamic highest-impact producer-choice question, linked gaps, explicit counterevidence, requested source followups; no question-count maximization. |
| `vme/style/coverage.py`, `vme/style/decisions.py`, `vme/style/authoring.py` | Phenomenon/joint-decision ledger rather than category checkbox, complete per-decision source→conditional branch→operation→skill reference; distinct same-category findings never collide. |
| `vme/skills/`, `vme/compiler/`, `vme/providers/gateway.py` | Skill-owned art instructions and actual visual reference bytes reaching Runware; do not rewrite style independently. Real asset/edit outputs or explicit missing operator. |
| `vme/loop/real.py` | Run all passes/targeted revisits, dependency-hash invalidation and human-feedback-driven revision through real stages; no silent S0–S9 fast-forward. |
| `vme/state/`, handoff CLI | Save protocol hash, raw evidence and capsule, coherent SQLite/artifacts/receipts and cold-start verification; maintain true external spend state. |
| audit exporter/tests | Log actual real path, new standard→code crosswalk, negative/dynamic tests and handoff drills, real provider constraints, no claim of artistic success from simulations. |

**Dependency order:** restore provider/job/billing safety first (R01–R07), source identity and coverage (R13–R14, R22), implement this investigation teaching and semantic fidelity (R08–R12, R15–R16), then true asset manufacturing (R17–R20), stage invalidation and portability (R12/R21/R23), finally full clean audit (R24). The training examples here are fictional **format demonstrations**, not source findings. Do not spend tokens on polishing synthetic art as a substitute for real investigation once authorized.

---

## 7. Evidence required before calling the repair complete

These are proof of **software behavior**, not certification of artistic mastery:

1. A real code invocation (with explicitly SIMULATED images/vision outputs during offline tests) generates a source observation record that contains a precise actor/world/temporal relationship and named unknown; a weak but structurally complete generic answer is diagnosed as insufficient *for the intended producing choice*. Do not mistake a keyword test for artistic understanding.
2. Contrasting witnesses for two different character types yield two conditional branches or appropriately scoped unknowns, not a copied subject-specific template. Show the difference in a skill-owned output clause and real operator selection.
3. Two distinct source findings in the SAME category survive into skill and prompt as separate decisions and reference roles, with no dimension-ID collision.
4. A visual relation missing between otherwise supported face, view and light dimensions creates one exact targeted source question and source reinspection request; the other already-closed gap decisions remain committed.
5. A precise question answer with an `UNKNOWN` material aspect fails to become an invented aesthetic prompt; source or producer study continues, with all important connected gaps still queued.
6. A decoded target sequence with one missing actual vision response remains incomplete, regardless of surrounding responses or survey thumbnail status.
7. The same detailed visual evidence, question, skill, reference hash and next operation survive a clean-directory export/import and restart under a different executor; an incompletely saved question cannot be silently completed by summary.
8. Actual provider-visible Runware payload contains exact skill-owned clauses and authorized reference image bytes, original content slots only, with realistic provider limits. No compulsory paid request during this offline repair.
9. A rejected output reopens the affected interpretation, branch, operation or provider route; the revised compiled output must change for a predicted reason. Not simply "more adjectives" or a noncausal check.
10. The complete remaining R01–R24 tests, strict provider contract tests, crash and cap tests, character/asset plan consumers and fresh-extraction suite run without hidden skips/deleted tests. Export actual changed source, logs, hashes, requirement map and explicit unproven artistic results.

**Named status:** `OFFLINE_ENGINEERING_REPAIRED` can only mean production logic and safety are connected in code and pass executable evidence. It does NOT mean real selected frames have been studied, a human has approved the style, or professional output has been demonstrated. `READY_FOR_AUTHORIZED_CANARY` requires exact source/volcano boundary lock, correct provider accounts/caps/consent, verified artifact references and independent audit; never automatic full six-film spend.

**External constraints:** We intentionally do not authorize paid Anthropic or Runware calls and do not upload user films to external services during this repair. Source frames may be inspected locally. Preserve exact five local source hashes and real 720p resolution; unconfirmed roles stay unresolved.
