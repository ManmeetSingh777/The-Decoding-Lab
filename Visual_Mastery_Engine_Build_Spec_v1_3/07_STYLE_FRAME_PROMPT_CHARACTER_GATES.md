# 07 — VME v1.2: STYLE-FIRST OBSERVATION, FRAME COVERAGE, PROMPT COMPILER, CHARACTER ART, APPROVAL GATES

**Status:** Preserved v1.1 requirements, supplemented by authoritative v1.2 algorithms in 09–12; v1.2 controls runtime style prompting, semantic frame resumption and character manufacturing. Original v1.1 requirements to be IMPLEMENTED and VERIFIED by the coding agent; none of these components is claimed to exist today. This addendum **amends**, rather than deletes, the user-approved 13 sections. In any conflict with v1.0, use this addendum, the revised launch prompt and amended acceptance tests. Keep original planning text unchanged as provenance only. Source evidence for the new project remains exactly the five MP4s and new project outputs, never previous AnimationLab research.

## 0. Governing correction: produce style knowledge, not scene descriptions

The original observation model may produce detailed, accurate, completely useless object descriptions. The new model MUST start from a **visual capability that remains useful when the original topic, subjects, script, location and individual artwork are swapped out**. This is not merely a frequency/pattern test and is not proven by holdout tests alone. A style is a conditional system of *design decisions, relationships, execution habits and exclusions*; it is NOT a library of source-specific objects, copied curves or RGB values.

For each high-impact investigation keep FOUR separate records:

1. `SOURCE_FACT`: what is actually visible, frame IDs and neighboring context; e.g. multiple internal graphic masses are arranged inside a larger subject, with a coherent edge/material treatment.
2. `STYLE_MECHANISM`: what artwork-producing decisions explain the visual treatment, subject-independent when possible; which decisions are held invariant, which adapt by material/viewpoint/role, and how those choices combine. State empirical status `INFERRED` until verified by original output. Not a slogan, not just a list of repeats across films.
3. `ORIGINAL_CREATIVE_INPUT`: design choices that the original brief should supply or that a trained image model may invent *within the learned art constraints*. Do not smuggle specific source characters, original metaphors, colour codes or scenes into the style mechanism.
4. `PRODUCTION_METHOD`: exact executable route for producing the outcome with an image model, image-edit model, background/subject/variant generator, mask/layer tool and/or renderer; actual inputs, provider options, prompts, references, outputs and corrections. A written rule without a producing mechanism is not a skill.

### Mandatory STYLE-MECHANISM questions (apply to selected connected quality cluster)
- Which **design decisions** create the distinctive professional treatment, not merely the depicted content?
- If we replace the fly with an unfamiliar mechanical robot, or the forest with a different original world, **which relationships must stay**, and what must change because the subject, material and scale changed?
- How are large shape masses, designed internal structures, detail hierarchy and art finish coordinated at whole-subject and whole-frame levels? What is deliberately excluded?
- Which features depend on **subject class, focus, camera distance, illumination, pose or movement**? What does the reference show about those dependencies?
- If a generator follows the current style contract but is allowed to invent an original subject, where could it still choose a generic or visually incompatible treatment? Name and close those high-impact degrees of freedom, not every pixel.
- How will this method give the same strong design language to different original people, organisms, cities, diagrams and celestial worlds without forcing them into one subject template?
- Can the same style mechanism produce aesthetically coherent but **distinct** creative results, rather than selecting one source frame and changing labels?
- What new original artwork proves the mechanism, and how does that method compare against the identical model without the mechanism?

### The style record MUST contain
`style_mechanism_id; source_witness_ids; dominant_visible_quality; subject_independent_decisions; conditional_variations; relationships_with_other_mechanisms; scene_specific_facts_to_exclude; examples_and_contrasts; independent_source_checks; original_content_freedom; compatible_production_tools; exact_prompt_rule_ids; output_tests; source_claim_status; transfer_status; rejected_interpretations`.

**Evidence discipline:** one source example is permitted as a lead but may NOT be called a general style rule. Cross-film examples help but repeated motifs alone are not sufficient. Require an abstraction argument: *what remains after removing topic, character, exact object and script?* Challenge by counterfactual content substitutions and original generation. If the rule generates clones or is applicable only to the source example, classify `SCENE_SPECIFIC`, not `STYLE`. Preserve contradictions and conditional branches. Never claim to know the studio's private implementation from final video alone.

### High-impact, connected observation cluster
Begin with **3–6 connected significant qualities** when justified, not a fixed number. The initial cluster MUST include: coherent, sophisticated world artwork; original character design (including compelling face and silhouette); subject-specific colour/material/lighting finish; at least one potential viewpoint/drawing-state relationship. Investigate these together from real frames and link the causes; don't let a character researcher ignore the complete world or vice versa. Every observation needs a source witness, a precise claim, why it changes actual image generation, what other elements it depends on, and a planned production operation. Keep other material gaps in the queue. Avoid huge superficial checklists and low-impact micro-details.

**No automatic graduation from observation:** the actual production method must yield visibly better original art on more than the source subject. Save stylistic *decisions and conditions* instead of attempting to freeze all content, artist choices or pixels.

---
## 1. Every-frame coverage: exact claims, no theatrical 'saw every pixel'

The five MP4 files supplied for this project have been independently probed as approximately **242,095 video frames**, mostly 60 fps across roughly 67.25 minutes. The implementer MUST independently re-probe the user's local originals; don't hard-code counts or assume constant FPS. Video can be VFR. Index using decoded frame order and actual presentation timestamp (PTS), not `round(second * fps)`.

A. **ALL-FRAME DECODE + TIMELINE:** decode/count every original displayed frame, record source hash + decoded frame index + PTS + frame dimensions + frame image or reproducible decoder offset + normalized thumbnail perceptual fingerprint; detect and record failures and gaps. Streaming decode is permitted, but no unaccounted index ranges. Compute motion/change/shot/occlusion indicators and cross-frame context. Use storage-efficient frame indexes, not millions of redundant full-res JPEGs. Prove coverage: count/index/PTS range, contiguous frame IDs, last frame, missing/corrupt frame list, source identity, re-run spot checks.

B. **VISION COVERAGE LEDGER:** every frame gets an explicit status: `INDEXED_ONLY`, `AUTOMATED_VISUAL_FEATURES`, `SENT_TO_VISION`, `VISION_OUTPUT_VERIFIED`, `NATIVE_DETAIL_REVIEWED`, `UNKNOWN_OR_FAILED`. Machine metrics are NOT LLM artistic understanding. A contact sheet that omits frames, a video provider that resamples internally, or a 10 fps sample cannot be marked as every frame seen. Track input group, frame IDs, image resolution/crop scale, model/provider/version, actual image artifacts passed, response, output quality, failures and source timestamp. The tool MUST be able to request **every decoded frame** for vision review in contiguous non-dropping batches (`--vision-coverage all-frames`), including moving/near-identical frame relationships. The agent must discover image/video API limits and verify if the provider actually saw every supplied frame, not assume that it did.

C. **ARTISTIC DEPTH:** seeing all frames at low resolution does NOT mean learning every small feature. For visual qualities that drive production, pull native-resolution stills and crops; for acting, transitions, pose/limb swaps, contact, lighting, camera and multiple events, pull adjacent original frames densely. Complete source understanding claims require the necessary native-detail and temporal evidence, not a coverage count.

D. **COST/TRUTH:** do not launch ~242k separate expensive vision calls automatically. Implement a budget-estimated all-frame VLM mode with bounded batching and checkpointed coverage; seek explicit authorization before any paid large-scale analysis or third-party source upload. If vision video APIs silently sub-sample, use a provider/method that truly accepts frame images or mark `NOT_VISION_VERIFIED`. If budget stops early, record exact percentages and ranges, and continue source-driven visual method investigation with honest *partial* coverage. **The user wants frame-by-frame analysis; support it, but never pretend a 60-fps artistic study is complete when it wasn't performed.**

E. **MINIMUM for any production skill:** source shot context + enough near-native evidence + required temporal observations for its claim, documented as above. Full 242k-frame VLM completion is NOT a prerequisite for the first useful skill unless a user-approved stage specifically requests it; otherwise we risk spending all the budget before making any artwork. This does not waive the full-frame coverage requirement or the ability to complete its VLM pass later.

F. **Tests:** inject skipped frame, wrong PTS, missing final frame, VFR clip, provider that samples one in ten, incomplete vision response, and interrupted batch; coverage gate must flag them. A claim `ALL_FRAMES_VISUALLY_UNDERSTOOD` is disallowed: a ledger can prove frames were presented, not perfection of subjective understanding.

---
## 2. The STYLE → ORIGINAL ART → PROMPT compilation bridge (MOST CRITICAL)

**Mandatory rule:** no image API call may be authored as a free-form last-minute prompt by a general-purpose agent. Calls must be produced by `PromptCompiler` from frozen or candidate **style skills**, an independent **original subject brief**, explicit scene/character asset requirements, and the real provider's capabilities.

The style contract is the ONLY authority for the *targeted artistic style*, not necessarily for the original subject/content. The original brief supplies what to depict and the required story-driven action; scene context supplies composition and functional focus; an identity/asset bible supplies persistent character details; provider capability specifies technical limits. No undocumented aesthetic instructions may be silently invented outside the style contract. Claude must flag missing high-impact style decisions and ask the investigator for evidence or mark them as a tracked creative/default decision; don't fill it using source-specific imitation.

### Typed inputs
`OriginalSceneBrief`: new subject/topic, key objects, world, required actions, focal subject(s), originality constraints, aspect/resolution.
`StyleContract`: conditional professional art decisions from qualified/candidate skill with provenance, *high-impact visual construction clauses*, negatives and applicability.
`SceneArtPlan`: desired whole composition, relative depth, visible object/part relationships, silhouette and density intentions, focal hierarchy, art layer responsibilities, planned motion, viewpoint/state requests; this is a constrained plan, not a vague list of nouns.
`CharacterBible`: approved character identity and art-family requirements (see section 3).
`ReferenceRoles`: separately selected source stills/crops with role `overall-design-language`, `subject-construction`, `material`, `whole-world-coherence`, `viewpoint`, `motion-state` or `negative-contrast`; include hashes, regions, permissions and strength/priority. Do not imply the provider can ingest more images than it can.
`ProviderCapabilities`: model ID, prompt limits, native size, supported reference/edit/mask modes, seed, transparency, permitted upload and financial budget. Unsupported features require a named failure or validated alternate path.

### Internal multi-stage procedure (keep detailed specification separate from provider text prompt)
1. **Choose route first**: whole-scene concept, canonical character, character variation, object/prop, world expansion, mask/clean-plate, local corrective edit. Never use one giant prompt for every operation.
2. **Build a high-fidelity original image design plan**: concrete visual structure, subject function, hierarchy, object relationships, depth, overall richness, lighting/material cohesion, facial/silhouette treatment and requested alternate states. Distinguish mandatory decisions, conditional choices and freedom for the illustrator.
3. **Compile prioritized prompts**: [A] original scene and intended visible result; [B] style-driven shape/finish/world design; [C] focal composition, spatial/object/character relations; [D] approved design identity; [E] exact changes to make for edit/variant; [F] prohibited failures/copying; [G] provider-specific technical settings. Concise, visually concrete, unambiguous language; do not stuff thousands of marginal rules. More detailed information belongs in referenced example images, structured plans and separately executed edits.
4. **Constraint trace**: for every HIGH-IMPACT style clause required by this task, record which part of the provider request implements it: prompt span, named reference image, edit region/mask, linked dependent function or named deferred action. `UNREPRESENTED` high-impact clause => **BLOCK**. `DEFERRED` is permitted only when an actual next operation with a concrete dependency is recorded, not a hand-waving promise.
5. **Contradiction, context and identity audit**: resolve instruction conflicts and emphasis; detect references/clauses that demand source-specific characters, incompatible palettes/materials, inconsistent viewpoints, impossible limb contact or competing focal subjects. Reject overly generic template text, unverified prompt clauses, missing mandatory state variants and oversized requests. Check actual prompt *character/length limits* of chosen provider. For Runware FLUX.2 [klein] 4B docs `positivePrompt` supports up to 10,000 characters, width/height 128–2048 step 16, up to four reference images for supported tasks; verify model settings per route at runtime, not assume all calls share a limit.
6. **Generate + verify REAL images**: persist the exact provider request and response (and output bytes), prompt/source/skill/scene hashes, reference roles, model settings, seed where supported, cost, provider errors, output dimensions and image format. No mock artistic quality.
7. **Prompt-to-pixel visual audit**: independent model/human checks actual images, not prompt text, for (i) high-impact style contract, (ii) original brief, (iii) complete designed illustration, (iv) character identity/anatomy, (v) coherently rendered whole world, (vi) significant missing/wrong elements. Attribute failures to one of `STYLE_OBSERVATION`, `STYLE_ABSTRACTION`, `IMAGE_DESIGN_PLAN`, `PROMPT_COMPILATION`, `PROVIDER_MODEL`, `REFERENCE_CONDITIONING`, `MODEL_EXECUTION`, `ASSET_EXTRACTION`, or `REVIEW_ERROR` with discriminating evidence.
8. **Targeted correction**: if text conditioning was ambiguous, fix the plan/compiler and regenerate; if visually correct except one region, use controlled inpainting/edit with protected identity regions; if the model repeatedly fails a complex operation, use a tested stronger provider or route. Record which method changed and which visible defect improved. Never bypass user approval by editing after signoff without an additional approval.

### Prompt length and completeness
**Do NOT confuse long with complete.** The image prompt should cover the few major characteristics that control large amounts of visual quality, followed by needed conditional specifics; use real visual references and staged edit calls for dense craft rather than dumping every observation into a 1,000-line prompt. A promise of exact pixel control from text is false. Promote only results that actually look good. Use a deterministic compiler and test that *removing a key style clause removes or changes the intended guidance*; then verify whether its inclusion improves actual generated images.

### Contract examples (not a predefined Kurzgesagt formula)
- BAD: `Make a stunning Kurzgesagt-ish laboratory with detailed vector art, rich colors, beautiful lighting.`
- BETTER: original subject and composition are defined explicitly; actual project-derived `STYLE_MECHANISM` clauses specify how subjects should be organized as coherent designed forms, how environmental substructures cohere, which scene elements carry visual complexity, how colour/material treatment differs by material/attention, which expressions/views to construct, and which negative outcomes must be avoided. The prompt compiler should assemble these **from demonstrated source-grounded skills**, not generic examples copied from this document.

### Tests
Unknown skills, no source-witness trace, missing original brief, contradicting art clauses, missing mandatory face/limb art state, source character leakage, provider prompt-length overflow, unsupported references, no prompt coverage for top clauses, unsupported alpha, unchanged actual provider request after high-impact skill change, model success without valid image bytes, and rendering after unapproved art must all be caught. Need real examples of compiled request differences AND output visual differences; byte changes alone do not certify artistic improvement.

---
## 3. Character artwork is a FIRST-CLASS primary capability, not a minor layer issue

Characters must be addressed in the first connected learning cluster along with world artwork and art finish, as the user explicitly prioritizes faces, silhouettes and limbs. The character investigator must start from source examples of *fully appealing designed characters* across varied subjects, states and contexts, not line-segment length alone. Investigate the visually dominant **style mechanisms** of:

- **Identity + appeal:** designed major silhouette, proportions and intentional exaggeration, head/hair/body/costume masses, distinctive facial construction, colour-role and detail distribution. Why the whole character is a coherent illustration, not flat tube limbs or disconnected icons.
- **Face:** front/three-quarter/profile structural changes; eye construction and near/far eye, brow, mouth, cheek, hairline, ear relations; expressions must change the integrated face rather than just scaling eyes/mouth primitives.
- **Pose and acting:** whole-body line of action, meaningful pose silhouette, weight, torso/pelvis relationship, gesture, hands and fingertips, stance, contacts, costume response and secondary parts. Measurements only where they enforce a visible relationship.
- **Changing drawings:** image/edited drawing families for necessary views, gestures, gripping states, expression changes and unusual poses. Track which parts can transform and which require replacement illustrations. Don't presume rigging a single raster cutout can produce all motions.
- **Whole-scene fit:** proportions and perspective relative to room/ground/prop/camera, shadow, contact, occlusion, visual role in an environment, lighting/material match with nearby world art.

### CharacterBible / CharacterAssetFamily MUST specify
`character_id; original_brief; canonical approved full art; identity invariant map; silhouette/shape design notes; relative proportions by view/state; visible face topology; material/color identity; intended acting/viewpoint list; state gallery; limb connection/attachment map; hands/feet alternatives; head/hair/clothing layer groups; foreground/background part ordering; held prop constraints; motion pivot/anchors; any necessary occluded artwork; clean-plate/masks/alpha; image generation lineage; review evidence; user approval version; defects & exclusions`.

The canonical art comes FIRST. Generate the meaningful alternate artwork using reference-guided editing from the canonical image where supported. **Do not call an unrelated text-to-image prompt for each pose** and pretend identity will be stable. Maintain coherent full-body silhouettes and facial appeal across all needed views. Use masked part images or independent pose drawings where they work best; never force all motion into one limb rig.

### Layer and limb preparation
- A scene-level visual design and upcoming motions must exist BEFORE drawing assets. Decide which parts truly must separate, and where whole-pose redraws preserve quality better.
- For each moving part, record geometry anchor and relative owner, render ordering, visible/occluded contours and alternate state requirements. Use masks or layered generation/segmentation with clean plate; test actual recomposition against canonical image. An API returning PNG **does not** mean true transparency.
- Validate joint attachment / allowed extent / silhouette / perspective / hand-to-prop contact and ground support against the *visible artwork*, not just skeleton numbers. Avoid invented joints detached from raster parts and stretchy forearms.
- Facial expressions must have complete coherent visual states, including eyes, brows, mouth, cheeks, hair and face contour as required. A floating eyebrow/mouth transition or lost character identity blocks art-family approval.
- For key poses, compare full composite and original art side-by-side; flag choppy shape swaps, unstable outline, garment clipping, wrong overlap and changed facial design.
- Use code for the positions, timing, camera and controlled transforms of validated assets; **never require code to invent the full professional illustration through generic SVG body parts**. SVG is permitted for simple diagrams/masks/motion paths or provider-vetted vector assets, not as the primary artistic construction method.

### Character-specific review gate
Show user: canonical full-art design, character in one scene, face crops, full-body silhouette sheet, major alternate views/expressions, hand/grip poses, separated layer overlays and recomposed hero image; show any critical missing required states. User can reject character while approving environment, or vice versa. `APPROVED_ARTWORK` never implies `APPROVED_CHARACTER_FAMILY`; separate statuses. No automatic render using rejected/corrupt characters. Request visual improvements before animation.

**User expectation:** prioritize visible major improvement within the first one or two learning rounds; provide side-by-side evidence each round. Never guarantee that a particular image model will achieve expert character art in exactly two iterations. If output remains poor, diagnose provider/approach and stop costly multiplication of variants.

---
## 4. Artwork-first stage gates (supersedes unconditional video requirement)

The previous rule "every major learning iteration MUST render 12–20s MP4" is **REPLACED** by an art-quality-dependent progression:

`REFERENCE/BASELINE -> CONNECTED STYLE STUDY -> PROMPT COMPILE -> ORIGINAL STILL PRODUCE -> INTERNAL ART AUDIT -> USER ARTWORK REVIEW -> (if approved) CHARACTER/LAYER/STATE ART PACKAGE -> INTERNAL ASSET AUDIT -> USER ASSET REVIEW -> (if approved) MOVING PREVIEW -> VIDEO REVIEW -> TRANSFER`.

**State machine**:
- `AWAITING_PROVIDER_OR_SOURCE`: missing reference or paid permission. No fake art.
- `ART_GENERATING`: source/style/prompt workflow running; no render approval.
- `ART_FAILED_INTERNAL`: obvious invalid or poor art; record defects and revise art; notify/show user when meaningful. Do not force a video.
- `AWAITING_ARTWORK_REVIEW`: save original still gallery + design-plan/prompt coverage + honest review; pause for user decision.
- `ARTWORK_REJECTED`: freeze failure evidence and return to high-impact investigation/prompt/provider changes. A rejected still cannot be used for an integrated finished animation.
- `ARTWORK_APPROVED`: immutable user-signed image/skill/brief hash, exact image revision, approved expected visual quality.
- `ASSET_PREPARING`: create canonical character variants/layers/masks/state families from approved artwork.
- `AWAITING_ASSET_REVIEW`: show character and other animation-ready assets, recomposition consistency and layered proof; pause for user decision when applicable.
- `ASSETS_REJECTED` / `ASSETS_APPROVED`.
- `VIDEO_RENDERING`: only reachable with matching `ARTWORK_APPROVED` and necessary `ASSETS_APPROVED` for all essential assets.
- `AWAITING_VIDEO_REVIEW`: actual MP4, original frames, time-coded defects, comparisons and your verdict.
- `TRANSFER_PENDING` and `TRANSFER_QUALIFIED`: only after freeze and unseen tests.

**No automatic promotion** based on objective metric, generic aesthetic evaluator or a different user's feedback. A user-accepted still can require reapproval if key artwork changes. Renderer may create inexpensive internal diagnostic previews (clearly named `DIAGNOSTIC_NOT_APPROVED`) when essential to discover problems, but may not emit or qualify a "finished major iteration video" from rejected art. No downstream render job may bypass gate by missing or substituting hashes.

**Iteration endpoint:** stage-dependent: an *art-learning iteration* ends with full-resolution original stills + user judgment. An *integrated animation iteration*, after approved art/asset gates, ends with 12–20s moving MP4 + user judgment. Later 20–30s integrated milestone unchanged. The first build should deliver first live original-image review ASAP, not burn time rendering bad characters. All outcomes and user decisions remain versioned.

### Tests
Simulate rejected hero art, rejected face, unapproved mask pack, forged approval, art replacement after approval, wrong scene hash, provider failure and skipped review; full render must refuse. Then approve a valid art/asset set and verify actual motion MP4 can be produced by existing primary Remotion+FFmpeg route. Coverage of existing v1.0 milestone code must remain, with conditional gate logic.

---
## 5. Engine interfaces and concrete execution commands

Required functions (exact module names may vary; behaviors must not):

```
index_every_frame(original_mp4) -> FrameCoverageLedger
request_frame_vision(ledger, frame_ranges, coverage_mode, model, budget) -> VerifiedVisionCoverage
observe_style_cluster(source_evidence, active_gap_cluster) -> StyleMechanism[]
compile_scene_art_plan(original_brief, skills, character_bibles, scene_requirements) -> SceneArtPlan
compile_image_request(scene_art_plan, style_contract, model_capabilities, refs, route) -> PromptCompilation
validate_prompt_coverage(prompt_compilation) -> CoverageReport | BLOCK
create_original_art(prompt_compilation, approved_provider) -> ImageOutput + ProviderTrace
review_art(original_art, style_contract, original_brief, independent_reviewer) -> VisualFindings
submit_user_art_verdict(run_id, asset_hashes, verdict, defects) -> ImmutableArtApproval
prepare_animation_assets(approved_art, actions, art_family_method) -> Layer/StatePack
verify_asset_pack(pack, artwork_approval, character_bible) -> AssetReport | BLOCK
submit_user_asset_verdict(run_id, pack_hashes, verdict) -> ImmutableAssetApproval
render_video(approved_art, approved_assets, scene_spec) -> ActualMp4 | BLOCK
```

Required CLI flow (paths/names can change if documented):
```
vme sources ingest --all --index-every-frame
vme sources vision --coverage all-frames --estimate-cost --dry-run
vme sources vision --coverage all-frames --budget-usd <approved> --submit-to <approved-provider>
vme investigate --cluster <cluster-id> --mode style-mechanisms
vme art plan --original-brief <path> --skills <version-lock>
vme art compile --plan <path> --provider <model-id> --show-coverage
vme art generate --compiled-request <path> --budget-usd <approved>
vme art review --run <id> --serve
vme art approve|reject --run <id> --hash <art-hash> --issues <json>
vme assets build --run <id>
vme assets review --run <id> --serve
vme assets approve|reject --run <id> --hash <pack-hash>
vme render --run <id>   # must refuse before both required approvals
vme review --run <id> --serve
vme continue --run <id>
```

Save `FrameCoverageLedger`, `StyleMechanism`, `SceneArtPlan`, `PromptCompilation`, `CharacterAssetFamily`, `ArtApproval`, `AssetApproval`, `VisualGateState`, `ProviderTrace`, and per-run `CONTINUE_HERE.md`. Use typed schemas, immutable audit logs and atomic checkpoint writes; test interruption/resume after provider submission, artwork approval and asset approval; never repeat paid calls silently.

---
## 6. Independent acceptance and honest claim language

A data-schema test passing means **structure** passes; it does not mean `style mastered`. A prompt containing all expected words means **coverage** passes, not visually good art. A frame ledger spanning 242,095 frames means **indexed**, not deeply inspected. A generated single beautiful hero illustration means **art demonstration**, not all-view/limb skill. A short MP4 encoded means **rendered**, not compelling motion. A single scene improving means **local improvement**, not a transferable style mechanism.

For each run report independent columns: `SOURCE_FULL_FRAME_INDEX`; `SOURCE_VISION_COVERAGE`; `STYLE_OBSERVATION_EVIDENCE`; `SKILL_TO_PROMPT_COVERAGE`; `PROVIDER_REAL_OUTPUT`; `ART_QUALITY_REVIEW`; `CHARACTER_FAMILY_REVIEW`; `ANIMATION_ASSET_READINESS`; `VIDEO_QUALITY_REVIEW`; `UNSEEN_STYLE_TRANSFER`; `USER_VERDICT`. Each has `PASS | FAIL | PARTIAL | UNTESTED | BLOCKED` with paths and next concrete action.

The engineering specification is correct **only when** a test can disable an essential observation, style rule, prompt clause, character state, layer or approval gate and cause the appropriate output/test to fail. An integrated prototype becomes artistically valuable only with actual images and human review. We cannot guarantee exact proprietary style fidelity or perfect error-free prompts; the system must expose unsolved limits and use actual provider results to decide.
