# 08 — PROMPT AND VISUAL SKILL: ACTUAL EXECUTION EXAMPLE & REFUSAL CONTRACT

**Status:** engineering example, NOT an observation extracted from a Kurzgesagt film and NOT a tested style rule. The implementer must create the actual skill mechanisms from new film evidence and real original output comparisons. Do not treat these examples as discovered visual facts.

## A. Typed art pipeline, not free-form prompting

Consider an original story about an unfamiliar coastal research vehicle examining bioluminescent microbial life. It is deliberately distinct from the five supplied film topics. We need a scientist character looking into a floating specimen chamber in a coherent, complex environment. `OriginalSceneBrief` describes the **content**, not the style. It might require: full-body scientist visible; floating transparent specimen container; hands interacting with apparatus; coherent laboratory environment; clearly visible action; future viewpoint shift from front 3/4 to side.

Before any image API call, the orchestrator must create independently:

- **OriginalBrief** (`creative content source`): novel subject, characters, scene props, subject proportions/identity goals as creative design choices, action required, environmental function, viewer-facing purpose. Never copy source characters or props.
- **StyleContract** (`a learned skill source`): each high-impact style-making mechanism sourced in actual original MP4 visual witnesses and qualified to the appropriate level, with conditional decisions, different material/subject classes, exclusions, evidence IDs and production route. Nothing from the designer's imagination is mislabeled as learned style.
- **SceneArtPlan** (`integration source`): image-space framing, hierarchy, depth and foreground/middle/background arrangement, materials, coherent world design, character sizes relative to the scene, focal object and next motion requirements.
- **CharacterBible** (`identity source`): once canonical character art approved, coherent visual identity and exact required face/view/pose/hand state drawings.
- **ProviderCapabilities** (`technical source`): actual verified image/edit model parameters, prompt max, width/height, reference-image count and legal/authorized reference handling. Never assume one provider supports alpha or segmentation.

`PromptCompiler` is deterministic given these typed inputs and a specified compiler version. During the **learning** phase a language model may propose a sourced candidate skill revision, but the **production-time prompt compiler MUST NOT author or rewrite any new aesthetic/style clauses**. Only pinned skill-owned templates generate targeted style wording. See authoritative v1.2 `09` and `11`. It resolves precedence: source-grounded style contract controls style; original brief controls original content; scene art plan controls composition/functional relations; character bible controls approved identity; provider cap controls technical representation. A required source/style conflict is a **BLOCK**, never a silent arbitrary merge.

## B. What one compiled request looks like (PLACEHOLDER mechanism IDs ONLY)

The following schema shows the *shape of the prompt*, NOT actual Kurzgesagt observations; `STYLE-X` placeholders must be replaced by verified style-mechanism evidence during real execution.

```
REQUEST_ROUTE: full-scene-canonical
SUBJECT: Original scientist inside an underwater microbial observatory, examining a floating specimen chamber. Entirely new face, outfit, machines and world.
VISUAL_COMPOSITION: 3/4 view; scientist in left foreground; specimen chamber at central focal depth; designed machinery continues coherently into middle and distant environment; no unrelated icon collage.
STYLE_CONSTRUCTION: [style mechanism STYLE-X1] determines large designed shape architecture and subject-specific internal divisions; [STYLE-X2] governs rich but controlled whole-world integration and emphasis; [STYLE-X3] governs conditional lighting/material treatment by object/focal role. These mechanisms must have actual source-derived content, not placeholder adjectives.
CHARACTER: [approved identity version] with deliberate silhouette, coherent head/face/hair/costume design, articulated full-body illustration and action-compatible hand states; no generic tube limbs or pasted face parts. If no approved identity exists, generate canonical design first and wait for review.
ANIMATION_PROVISION: planned face turn and hand-to-chamber interaction require editable or alternative hand, face and arm drawing states; preserve camera space, visibility and needed background clean plates. Do not claim assets are ready without actual images.
NEGATIVE: no reuse of original source characters, generic stick figures, broken anatomy, unrelated visual styles, missing hands, unplanned gradients or blank filler props.
TECHNICAL: native verified model resolution, image format and reference-image roles; do not issue unsupported alpha/edit instructions.
```

The actual image provider may have ONE positive prompt and a few reference slots. The rich structure remains saved in `PromptCompilation`; `PromptCompiler` prioritizes high-leverage clauses and role-specific reference images within the actual prompt length and task type. For Runware FLUX.2 [klein] 4B consult current docs; the example cited in the contract indicates a 10,000-character positive prompt limit and up to four references, **not** a guarantee those four always behave as intended.

## C. Required coverage report (must be compiled before expensive calls)

```
{
  "request_id": "example-scene-canonical-v1",
  "original_brief_id": "original-underwater-lab",
  "style_contract_sha": "sha256-of-frozen-style-version",
  "scene_art_plan_sha": "sha256-of-scene-art-plan",
  "character_bible_version": null,
  "provider_capabilities_id": "actual-provider-and-model-version",
  "route": "full-scene-canonical",
  "required_high_impact_clauses": [
    {"style_mechanism_id":"STYLE-X1", "execution":"prompt-span+reference-role", "target":"designed original object construction", "status":"REPRESENTED"},
    {"style_mechanism_id":"STYLE-X2", "execution":"prompt-span+art-plan", "target":"coherent original world", "status":"REPRESENTED"},
    {"style_mechanism_id":"STYLE-X3", "execution":"prompt-span+material-reference-role", "target":"material-aware finish", "status":"REPRESENTED"}
  ],
  "reference_roles": [],
  "pending_approved_original_art": [],
  "provenance":"example-only-not-qualified",
  "allow_call": false
}
```

`allow_call=false` because fake style mechanism IDs, source evidence, and provider capabilities are not valid. A genuine call is permitted only after every mandatory dependency is real, validated and authorized. A supplied real style mechanism should have `observable_predicted_effects` that a reviewer can look for in output.

## D. Character-construction example, same subject through changing poses

**Initial hero image must be approved**. Then produce, not merely describe, a connected set of *source-guided, canonical-image-conditioned original artworks*:
- whole standing pose front/3-4 with real silhouette and face design;
- 3/4 head slightly turned, with re-drawn nose/eyes/ears/hairline when necessary;
- key expression with changing eyelids/cheeks/mouth/brows in coherence, not 2D feature scaling;
- open hand and explicit grip hand matched to original prop in perspective;
- planted foot, leg bend and torso lean that retain actual intended cloth/limb silhouette;
- silhouette-only diagnostic sheet and recomposited layer sheet with verified background clean plate;
- animation test showing at least one actual drawing substitution, limb/prop relation and camera framing within visual constraints.

Each art state stores `source_canonical_image_hash`, `conditioning_inputs`, `prompt_compilation_id`, `visible_parts`, `layer_mask_hash`, `contact_relation`, `review_verdict`. A hand that floats or penetrates the prop is **failed** even if skeletal joint distances pass. If new views destroy identity, don't keep issuing slight text prompt variants; change the image/edit route, stronger anchor, partial edit, or state representation. If multiple state images are individually pretty but form an incoherent family, block animation.

## E. Explicit state examples

```
ART_GENERATING -> AWAITING_ARTWORK_REVIEW -> ARTWORK_REJECTED -> INVESTIGATE_ART_DEFECT -> ART_GENERATING
ART_GENERATING -> AWAITING_ARTWORK_REVIEW -> ARTWORK_APPROVED -> ASSET_PREPARING -> AWAITING_ASSET_REVIEW -> ASSETS_APPROVED -> VIDEO_RENDERING -> AWAITING_VIDEO_REVIEW
```

Do NOT render the final 12–20s MP4 when art is `AWAITING_*` or rejected. A poor portrait cannot be saved by adding camera movement. Internal short diagnostic render is allowed when named, but user must never confuse it with the completed integrated milestone.

## F. Test design anti-false-improvement at the *style* layer

Use the *same learned style mechanism* and *same original content type* across distinct creative subjects. For instance, if the question is whole-world coherence, test two different coherent worlds (not merely one with different labels); if the question is expressive character artwork, test two different anatomies and costumes while preserving quality of expression. Critically, require the mechanism to generate **multiple valid, nonidentical designs**: identical shapes/colours/camera found again indicate copied template. Compare interventions vs unconditioned same-model baseline and recognize when the model already did the job. Skill improvements can affect different images stochastically; use reasonable repeated comparisons where uncertainty matters. A rule is **learned style** only if reviewers can point to the general visual characteristic that improved without tracing the source-specific object.
