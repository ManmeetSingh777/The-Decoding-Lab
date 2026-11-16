# 15 — Style-owned prompt compiler and producing-operation planner (v1.3, authoritative)

## 1. This is a **prompt-producing METHOD**, not a prompt-writing instruction

A coding agent must implement `compile_scene_art` as deterministic code over structured, version-pinned inputs. The coding/production agent must not call `runware.imageInference` with a raw text field. All paid producer jobs pass through the sole `StyleImageGateway`, which accepts a signed/hashed `CompiledImageJob` created by `StyleProgramCompiler`. This is software-level API discipline, **not a cryptographic sandbox against arbitrary local code**; supply code-level integration tests to find bypasses.

`OriginalContentBrief` controls original subject, setting, story action, visual focus, subject identities and legitimate content-specific attributes such as a red laboratory coat **if the brief explicitly says so**. `ApprovedStyleSkill` controls the *artistic rendering and construction decisions*: shapes/parts relationship, colour role behavior, materials, lighting, world detail hierarchy, facial aesthetic, layer/pose design and reference conditioning. `ApprovedIdentityAssets` controls the appearance of already created original characters. `ProviderCapabilities` controls the legal model request envelope. **No fifth independent style authority exists at runtime.**

Important: original world/character invention necessarily leaves some content decisions to the model and Director. The requirement is **zero uncontrolled new style instructions in prompts**, not the impossible goal of zero generative choices in pixels.

## 2. Structured input types and owned fields

`OriginalContentBrief` must carry: `brief_id`, `shot_id`, `subjects` (new identity IDs, nouns, allowable visual-content constraints, object parts from script), `actions`, `world`, `visual_focus`, `camera_or_view_requirement`, `novelty_constraints`, `animation_requirements`, `content_provenance`. Treat broad user aesthetic wishes as a request to select or develop a compatible style decision, not as a new runtime clause.

`ApprovedStyleSkill` must carry: `skill_id`, `version`, `evidence_refs`, `applicability`, `condition_selectors`, `decisions`, `ordered_prompt_clauses`, `reference_roles_and_hashes`, `operation_dag`, `output_asset_contracts`, `exceptions`, `unassigned_style_fields` (must be empty for selected job), `status`. All references are source-grounded or approved original art with role and permission. A reference may be an art treatment guide, canonical character identity, pose guide, scene whole-art anchor; do not confuse their roles.

`ProviderCapabilities`: exact Runware `model` AIR ID from current docs/account, supported operations and `referenceImages` count, prompt maximum, width/height constraints, output format and transport, mask/edit guarantees (if any), cost model and version, user authorization. Do not hard-code an invented 'Flux 7B' model. Keys stay in environment, not files/logs.

`SceneArtPlan`: an intermediate representation **produced from resolved skills** and brief, with `required_art_ops`, `dependency_graph`, `style_decision_ids`, `character_anchor_ids`, `image_reference_roles`, `asset_output_specs`, `motion_state_needs`. It must not contain a free-form `aesthetic_prompt` field.

## 3. Actual prompt generation algorithm

1. **Resolve creative content**: get only typed subject identity, parts, situation, actions, relation and visual role slots from original brief. New subject design choices are allowed as content only and cannot overwrite chosen style decisions.
2. **Resolve capabilities needed**: Is this whole-scene concept, canonical actor, character turn, posed grip, region edit, clean plate or layer state? Select a *versioned skill production recipe*, not a generic text-to-image call for every job.
3. **Resolve decisions**: For each required image-quality attribute selected by skill (art identity, shape construction, full scene, colour/finish, view, character/pose if relevant), find a matching conditional decision. Resolve exceptions by priority and dependencies. If a required attribute lacks a decision, create a `MISSING_STYLE_DECISION` investigation ticket and stop the production job.
4. **Resolve references**: pick actual relevant source/approved visual images by `role`, `film/frame witness` and hash. Include canonical original actor identity in every derivative call. If provider limit forces dropping reference, do NOT drop a required identity/style anchor silently: split into supported edit stages or block.
5. **Resolve creation operations**: concrete function graph: whole composition/subject generation, reference-guided edits, alternate view/pose art, masks/inpaint, layer/clean-plate, quality-preserving compositing. Each node declares content+skill inputs and output image spec. No `beautify()` placebo operator.
6. **Build image text only from frozen skills**: selected clauses have controlled placeholders such as `{subject}`, `{action}`, `{view}`, `{visual_role}`, `{original_prop}` and must use an allowlist with escaping. No other braces, untracked strings, or runtime LLM art adjectives. Arrange clauses in the priority order specified by the skill and model profile. Content slots cannot be used to smuggle a new art-style instruction; typed allowed content/attributes only.
7. **Build negative instructions** only from skill and provider compatibility, not arbitrary generic lists of 'bad art' words.
8. **Check payload capacity before sending**: model-supported dimensions, prompt length, reference count, edit route, alpha assumptions. If too large, choose skill-owned shorter template or split staged operations; never autonomously truncate the most important art decisions.
9. **Emit `CompiledImageJob`**: immutable original brief hash, skill version+hash, decision IDs, clause ID-to-text mapping, reference hashes/roles, operation DAG node, model/parameters, requested output assets, exact provider payload bytes/hash and spend scope. The gateway may submit ONLY this job.
10. **Record actual provider result**: job UUID, image UUID/url/base64 response when available, actual pixel bytes, format, width, height, mode, alpha, checksum, cost and errors. A provider success flag without decoded actual pixels does not count.

If prompts are still generic, FIX the **skill's actual template/visual-reference/operation** during skill development. Do not add a prettier-prompt LLM after compilation. A syntactically perfect compiler can faithfully execute a poor skill; it doesn't automatically make the art excellent.

## 4. Prompt specificity at the correct level

A producing skill should encode **what the selected image-model operation must do**, not a 1,000-line description of scene-specific pixels. For a new visual role it should specify (a) original content, (b) intended spatial and part relations, (c) style decisions including high-impact silhouette/detail/finish, (d) visual conditioning images and their different roles, (e) operation type (whole scene, targeted edit, alternate pose), (f) required outputs for motion. The model may still fail; then repair image-generation method upstream.

A useful output should have an `art_decision_manifest` that states for each high-impact artistic property: which skill decision produced it; how represented in actual prompt/reference/model operation; where its reference evidence came from; and what visual effect is expected. If an important property is specified only in a prose report and nowhere in a provider request/conditioning step, the execution is WRONG.

## 5. Provider reality: Runware

Runware's current docs identify `runware:400@4` for FLUX.2 [klein] 4B, `runware:400@2` for FLUX.2 [klein] 9B; this is **not** evidence that the user's credit is attached to either model, or that 'FLUX Klein 7B' exists. Do not assume. User's Runware API key is an account-level credential; require exact selected `model` from Runware catalog/account and verify it supports the desired operations with a consented inexpensive probe. Consult documentation at https://runware.ai/docs/models .

For example, 4B docs currently allow `positivePrompt` up to 10,000 characters, width/height 128..2048 in increments of 16, and up to four `inputs.referenceImages`; other variants may differ. Build adapters from model-specific capabilities and version them, not these illustrative limits. Use outputType `URL`/`base64Data`/`dataURI` as supported; `outputFormat=PNG` or WEBP can carry alpha, **but a PNG response does not by itself mean transparency/layers exist**. Explicitly inspect the returned image and masks. (Docs: https://runware.ai/docs/models/bfl-flux-2-klein-4b .)

## 6. Bypass-prevention proof

- Direct call with `positivePrompt` from free-form agent code must fail at production entrypoint.
- Candidate skill not selected, missing essential decision, unpinned reference, unknown operator, content-to-style smuggling, unauthorized provider change or unsupported edit operation must fail **BEFORE** paid call.
- Changing only a JSON prose description with no actual selected recipe/clauses must not be counted as an artistic change.
- Changing an active skill decision MUST change the real compiled text/reference/edit-operation, not just a hash. If no effect, bug in compiler/dispatcher.
- Same skill + same brief + same provider capabilities yields identical canonical logical request; distinct `taskUUID` may be generated at submission, without affecting logical comparison.
- The gateway stores exact final request, provenance, cost/response and output byte hashes with no secret material.
- `BASELINE_ONLY` is separate experiment path with explicit label. It never pretends to be style-learned.

## 7. When skill has gaps

Never permit fallback style clauses from a general LLM. Return a structured `ResearchTicket` with `missing_art_decision`, `affected_scene_state`, `required_source_question`, `candidate_reference_frames`, `reason_for_block`. The investigator can develop a **new evidence-grounded candidate skill revision**, which is then compiled and actually trialled. The user need not answer every small research ticket; the lead agent progresses sequentially within authorized scope and stops for visible art review and spend.
