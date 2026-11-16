# 20 — Worked end-to-end example of RIGHT observation→skill→prompt→art operations

**EVERY visual statement below is a fabricated educational fixture, NOT an observation about Kurzgesagt's five films.** Actual source-specific values must be extracted from the five provided original MP4s in the later authorized run. This document exists because the user explicitly rejects a loose instruction such as 'turn observations into skills' and wants an actual worked example whose process can be implemented.

## The active connected quality cluster

New original content: a curious research explorer in a giant deep-sea observatory reaches toward a floating biological organism; camera later changes scale to reveal an organism's inner world. The cluster addresses three interdependent quality targets: (Q1) whole illustrated world versus generic scattered props; (Q2) attractive actor with expressive, coherent full-body/hand+prop design; (Q3) spatial and visual finish consistency between focal actor, translucent organism and surrounding environment. Nothing here commits to these exact objects as learned style.

### STEP 1: Contrast on source visuals (future real input)

The *required observation format*, not a prefilled claim:

`WITNESS_A: film_sha, frame_idx, original full-image hash, native crop, visible treatment (what shape/color/layer relationships are actually present), source-specific object facts NOT transferable`.

`WITNESS_B: DIFFERENT film/scene/subject supporting an analogous design relationship, actual whole image and relevant detail`.

`WITNESS_C: contrasting scene/exception (a simplified diagram or background subject where the rule changes), or `UNKNOWN` if evidence is absent`.

`TEMPORAL_WITNESS: consecutive source frame IDs where perspective, gesture, light or composition meaningfully changes; actual changes distinguished from static appearance`.

A correct observation does NOT write 'beautiful detailed observatory'. It says which visible *construction decision* is reflected by the image, how its parts relate, what adapts with focal roles and distance, and which of these are observations versus inferred production methods.

### STEP 2: Ask exact questions

Q-001: 'On two unlike original film subjects, what picture-level relationships make focal objects look purpose-illustrated rather than independent icons?' Evidence: actual images + internal shape/part and environmental relations. Expected output: concrete visual design decisions.

Q-002: 'When the same art language is used for supporting/distant objects, which characteristics simplify and which remain recognizable?' Evidence: contrasting supporting case. Output: conditional detail and silhouette decision.

Q-003: 'When full-body actors reach or turn, which face/body/hand/prop drawings change, what physical/overlap relations remain, and what is newly illustrated rather than transformed?' Evidence: consecutive source frames + unlike characters. Output: canonical+whole-pose+identity edit plan.

Q-004: 'Which art direction is a reusable rule and which belongs only to the particular original scene or subject?' Evidence: replacement thought-experiment with unlike original worlds and character types. Output: conditions/exceptions/creative freedom, NOT copied objects.

Q-005: 'What actual image operation and references will construct these decisions in a different original subject?' Evidence: provider capability and source-based reference roles. Output: typed `OperationNode`s, prompting rules and expected image-state family.

Q-006: 'Which artistic decisions would the model still be forced to invent because our skill is silent?' Output: focused missing research tickets, not untracked prompt adjectives.

### STEP 3: Source facts separated from style decisions

**Synthetic example of a scene fact (must never become universal):** 'Source creature A is orange and has five visible plates.' Object-specific. A rule 'draw every new creature orange with five plates' is explicitly REJECTED.

**Synthetic example of a possible style mechanism:** `IF focal_role AND multi-part illustrated subject AND medium-view THEN create a coherent readable outer silhouette whose larger internal masses are intentionally connected; coordinate surface finish with material and local environment; decrease internal articulation on distant supporting subjects while preserving recognizability; DO NOT copy particular source anatomy or palette. EXCEPTION: explanatory diagram uses simpler parts. ADAPTS: body type, material, viewpoint, scene role. EXPECTED: new original subjects look designed and coherent, not a bag of generic icons.` This must be replaced by actual, justified source-learned artwork relationships, never simply accepted as Kurzgesagt truth.

**Synthetic acting mechanism:** `IF stylized biped AND reaches across body to prop AND three-quarter view THEN define whole pose incl. weight/support, chosen hand side, prop space, facial attention and silhouette; create canonical-conditioned whole-state illustration; preserve whole actor identity; derive independent sprite pieces only for actions that benefit.` The real observing agent must establish what the five films support, including exceptions.

### STEP 4: Convert into executable operations (example only)

```
O-001 WHOLE_SCENE_ART:
  inputs: original world+visual focus, selected skill decisions, style reference roles
  function: provider.generate_original_scene(compiled_job)
  outputs: original composite PNG, provider response, dimensions/hash
  dependencies: none

O-002 CHARACTER_CANONICAL:
  inputs: original character identity/parts, scene/scale/light roles, selected skill reference images
  function: provider.generate_canonical_character(compiled_job)
  outputs: native whole-body actor art + identity anchor hash
  dependencies: O-001 scene art plan

O-003 CHARACTER_REACH_STATE:
  inputs: O-002 original canonical image, approved prop art, hand side, whole-body pose spec
  function: provider.guided_character_edit(compiled_job)
  outputs: whole character with actual designed hand+prop contact, same identity
  dependencies: O-002, prop art

O-004 LAYER_PREP:
  inputs: approved original scene/character states, intended actor-part motion
  function: asset_pipeline.extract_mask_and_clean_plate(...)
  outputs: verified RGBA pieces, masks, cleaned backgrounds, origins/anchors/owner refs
  dependencies: O-001/O-002/O-003 user approval

O-005 MOTION_SCENE:
  inputs: approved asset pack, movement events, camera states, contact relation
  function: remotion_renderer.render_scene(...)
  outputs: FFmpeg-verified MP4 + actual frame evidence
  dependencies: user-approved O-004
```

Each operator above is a CONTRACT for an actual callable implementation. A coding agent must not count this document as working code. If `guided_character_edit` isn't supported by the actual selected Runware model, it has to implement a truthful supported alternate route or mark the operation BLOCKED; cannot fake reference guidance.

### STEP 5: What goes into a real style-owned prompt

The **original brief** supplies: 'original explorer', 'deep-sea observatory', 'reaches toward translucent organism', 'three-quarter view', etc. The skill supplies all style/rendering text, reference crop roles, image/edit operation and conditional treatment. The `StyleProgramCompiler` binds only allowlisted content variables to frozen style clauses and returns a traceable provider payload.

A synthetic style clause such as:

`C-ART-F01`: 'Construct the original focal ${subject} as a unified intentional silhouette with internally coordinated major visual masses; preserve its relation to the ${setting} and clear foreground/background separation. Apply the approved material-specific treatment in style reference [ROLE=ART_TREATMENT_01].'

is **not acceptable to promote** until (a) grounded in actual source witness images with enough specific construction decisions; (b) the referred visual conditioning image actually exists and is included in the provider job or staged edit; and (c) actual generation of unrelated subject looks excellent. The text itself is only one part of the skill. A prompt that mentions a visual reference while the real request omits it has NO causal implementation.

An original actor pose-edit clause should reference **the approved original canonical actor image**; it must preserve identity and specify actual guided edit route and intended new whole-body drawing. It must not draw the body from text afresh in each shot.

### STEP 6: The FIRST success/failure diagnosis

If original explorer is unattractive BEFORE animation, don't investigate Remotion, sprite anchor placement or change a `quality_gate`. Reopen actual source character art, revise character construction+conditioning method, recompile a real new image job, and inspect output.

If explorer is beautiful but next pose has a different face, don't rewrite a generic 'same face please' prompt alone; change original-image guidance/edit strategy, crop/mask coverage, state dependency or provider.

If scene looks excellent but splitting layers creates seams, change the separation+hidden-surface generation method or render approved whole-pose states instead.

If all stills are excellent but held prop floats in motion, investigate contact/event timeline/anchors in the renderer. Do not reanalyze character colours for a motion bug.

If one revised image looks excellent but different original subject fails, freeze technique as narrowly conditional or change learning method; do not label generally mastered.

### STEP 7: Exact learning packet for human review

Show actual source evidence when used with permissions, original full-res world+character, before/after original images, selected source-linked decision IDs, selected prompt clause strings and actual provider request, previous vs current skill operations, real image/reference hashes, meaningful remaining gaps, root causes, what has and hasn't improved and what is pending. User can reject art before generating any full video. Don't present any synthetic fixture in this manual as a genuine result.
