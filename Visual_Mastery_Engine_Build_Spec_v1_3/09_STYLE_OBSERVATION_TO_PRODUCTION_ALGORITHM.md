# 09 — Prevention-first style discovery → working production skill (v1.2, AUTHORITATIVE)

Status: **BUILD CONTRACT, NOT EVIDENCE OF SUCCESS**. This supersedes conflicting or looser wording in 01/07/08. Preserve the original approved 13-part objectives. This is a CLEAN project: only the newly provided five MP4s supply film-style evidence; none of the prior AnimationLab findings, image data, CMRs, clips, candidate style rules, or old implementation may be ingested as research.

## A. What we are actually trying to learn

The target is a **conditional visual design grammar implemented through production methods**: for a NEW subject, material, viewpoint, relative scale, desired visual emphasis and environment, what decisions produce a recognizably coherent, sophisticated illustrated look? The system must explain and execute the **relationships** among whole-frame/world design, original object art, character design, colour/material finish, viewpoint changes, and motion-compatible alternate art. Its evidence is the actual moving film, not an adjective list, colour averages, single source character, or a single example's geometry.

Do not confuse four distinct things:
1. `SOURCE_WITNESS`: something the original MP4 actually shows at a verified frame/shot/sequence; may be unique to the scene.
2. `STYLE_DECISION`: an artwork-producing choice expressed **independently of those exact source objects**; specifies conditions, construction, relationships, exclusions and freedoms, and is still a hypothesis at this stage.
3. `PRODUCTION_RECIPE`: real executable image generation/editing, visual-reference conditioning, asset construction and/or animation operations that implement that decision on original subjects.
4. `SKILL`: callable versioned recipe + evidence + interfaces + verified outputs + known conditions. `SKILL.md` is a human/agent entrypoint; it does not create quality by itself.

## B. Start at whole-image qualities, not nouns or numbers

Each learning cluster starts with an original output or benchmark task and several actual reference frames/segments. A source-only first cluster is permitted to select initial quality targets *before* the baseline is generated, but it must quickly create original outputs. The investigation must cover, when relevant, a connected *set* of large defects: e.g. original character design, distinctive world construction, shared colour/material finish, and artwork required for changing viewpoint/gesture. Do **not** force exactly one defect or a fixed number of agents.

For **each candidate visual difference**, record: (a) evidence from actual pixels/adjacent frames, (b) why a viewer notices it (subject salience, whole-frame scope, repetition, artistic coherence), (c) whether it is a cause or a symptom of another difference, (d) what *specific original pixels* should change if addressed, (e) which executable operation could produce those pixels. Rank a connected cluster by a **written counterfactual**: 'If this is fixed while other defects remain, what will look materially better?' Never invent a numerical beauty percentage.

The six questions below are REQUIRED *for the selected difference*, not a fixed per-frame generic checklist:

- **Contrast**: Looking directly at multiple relevant source images and our own output, what **specific visually consequential difference** is evident at the whole-frame, subject, and intended motion states?
- **Cause**: Which **observable art-design relationships** distinguish it? Identify the dominant decisions without jumping to isolated measurements. If a distinction remains generic ('rich', 'polished', 'balanced'), ask again what picture-producing choice that means.
- **Independence**: Remove the source nouns, script, precise colour codes, distinctive source character design, and the particular shot. What executable art choice still holds? What must change with subject, material, viewpoint, focus, camera distance or motion? What MUST remain free to invent original content?
- **Interaction**: What other visual decisions does it depend on? E.g. character face design depends on silhouette and perspective; environment detail depends on focus, depth, subject design, scale and motion; light depends on surface and overlap. Do not split a compound capability into incompatible isolated rules.
- **Manufacture**: Which exact model route, references, prompt clauses, edit masks, original character anchors, layer/alternate-drawing operations and renderer function will *make* this happen? Describe actual I/O; no 'Claude will decide later'.
- **Falsification**: What original image or animation outcome would prove the explanation or method inadequate? Which missing input/representation/provider capability would cause that outcome?

If a question has no supported answer, preserve its `UNKNOWN` and source range; select a focused study task. **Never fill unobserved details with an authoritative claim.**

## C. The reusable-style extraction algorithm (mandatory executable workflow)

Use these exact logical stages for a selected connected quality cluster:

**C1 — Witness set**. Retrieve 3 types of evidence wherever present: (i) a strong full scene, (ii) a different subject/world showing a related visual treatment, (iii) contrasting/exceptional case. Inspect original context plus native detail where needed. The five films may show no clear example of a proposed rule; mark `UNSUPPORTED`, not 'learnt'. One scene can start a candidate but never qualifies style generality.

**C2 — Observable difference record**. Write an anchored, picture-level statement: WHAT appears, HOW parts relate, WHAT changes with time/viewpoint. Example of adequate *form*: 'In source frame F, the focal object is a connected designed silhouette containing material-specific regions; peripheral structures follow the same illustration treatment; in counterexample G, distant supporting objects use less internal detail.' This is a structural example, NOT a claimed Kurzgesagt fact. Inadequate: 'bright colours, rounded shapes and layered compositions'.

**C3 — Conditional decision extraction**. Convert the difference to **if/when → visual-design operation → expected visible effect**. Every style decision must explicitly state:
- `applies_when`: subject role, visual role, material class, view/scale, scene density, intended action, or other evidence-supported conditions;
- `decision`: what artwork is to be constructed, how large masses/parts/finish/relationships are chosen, what is coordinated, what is *not* added;
- `adapts_with`: what changes when the content, viewpoint, distance or focal subject changes;
- `invariants`: visual relationships maintained across variations, *not absolute copied object dimensions*;
- `exceptions`: contradictions, simplified diagrams, changes of art treatment, source gaps;
- `creative_freedom`: new subject identity, original motifs, content palette choices when unspecified; do not mislabel this as learned source style;
- `dependencies`: other style decisions or required character/scene state;
- `visual_prediction`: a concrete visual difference the rule is expected to cause.

**C4 — Source-independent challenge before coding**. Verbally substitute at least **two unlike original subjects**, or a near/far/camera-view state, into the proposed decision. If the 'rule' still specifies a reference insect, one specific skull, exact source colour or copied composition, demote it to `SCENE_FACT`. If it merely repeats 'professional', 'charming', 'dynamic', it is `VAGUE`. If two distinct original subjects require completely different treatments, represent conditional branches rather than forcing a universal template. This challenge is an input-design method, not merely a retrospective holdout test.

**C5 — Manufacture plan**. Decide *before* any model call: full-scene visual concept, canonical character design, original prop, viewpoint/pose variation, targeted material edit, region refinement, layered extraction, clean-plate, camera/motion state. Assign an actual producing route and identify upstream design/art prerequisites. Specify input brief fields, required canonical/conditioning/reference images, exact prompt clause IDs, output image(s) and dimensions, relationship anchors, extraction/edit operations and expected state family. If no working route exists, the rule is `RESEARCH_ONLY`; it cannot silently shape a production prompt.

**C6 — Compile actual skill artifacts**. Every working skill directory must have:
```
skills/<id>/SKILL.md              # when to invoke, conditions, exclusions, entrypoint
skills/<id>/manifest.json         # IDs, provenance, dependencies, version, claim status
skills/<id>/decisions.json        # typed conditional if/when → chosen design decisions
skills/<id>/prompt_templates/     # skill-owned language templates, ordered by priority/route
skills/<id>/references/           # authorized, role-typed actual image crops + hashes
skills/<id>/recipes/              # provider/model-independent typed operation plans
skills/<id>/scripts/              # actual provider/edit/asset/motion functions or adapters
skills/<id>/examples/             # original briefs, exact requests, output images, revisions
skills/<id>/known_failures.json   # trigger, observed symptom, cause and repaired method
```
`manifest.json` points to callable code. The system must execute those recipes. `SKILL.md` alone is not an artistic asset, a trained model, or a producer.

**C7 — Real original production**. Generate a candidate **using only the style-decisions selected and realized by the skill**, with separate original content and identity information. Inspect actual full-resolution image and relevant multi-state outputs. Use a narrow edit route when only an isolated region is wrong and retain source/canonical subject identity. Do not paste a source frame into an output and claim original style learning.

**C8 — Decide what to repair**. If outcome fails, identify **which production decision was not made correctly**, not simply 'needs richer prompt'. Distinguish `WRONG_SOURCE_INFERENCE`, `BAD_STYLE_ABSTRACTION`, `MISSING_CONDITIONAL_BRANCH`, `MISSING_IMAGE_DESIGN_DECISION`, `POOR_SKILL_TEMPLATE`, `PROMPT_COMPILER_BUG`, `PROVIDER_CONDITIONING_LIMIT`, `IMAGE_OUTPUT_LIMIT`, `CHARACTER_STATE_PRODUCTION`, `LAYER_ASSET_EXTRACTION`, `ANIMATION_EXECUTION`, and `EVALUATOR_ERROR`. Go back to source **only if** the actual cause requires new source evidence; otherwise fix the producing operation/code/provider. Keep every failed result attached to the attempt record.

**C9 — Compare skill influence without overfitting**. Within a learning cluster, compare a same-brief controlled baseline and the skill-guided result where feasible; use a rotating original subject in the same capability class and later a frozen untouched challenge. A positive result is *evidence*, not a guarantee. Avoid polishing a single scene into a fake style improvement. Once the recipe is unchanged and can make visually distinct subjects, upgrade its transfer status according to evidence.

**C10 — Persist**. Save exact source hashes/frame ranges, material observations, conditional decisions, creative freedoms, recipe version, image request bytes, source/reference image permissions, output hashes, diagnosis, user verdict, and precise next unresolved question. Never preserve only a paragraph summary that forces future Claude to guess.

## D. Observation quality: positive and negative examples (illustrative, NOT film-derived)

**BAD**: 'The forest looks complex because it has many trees; the eyes are big; the light is blue; use the same shapes everywhere.' Why bad: object/topic bound, copies surface features, ignores relationships, not constructive.

**STILL BAD**: 'Use coherent large shapes, rich colour, appealing silhouettes and professional finish.' Why bad: universal adjectives; fails to specify actions or conditional branches.

**BETTER STRUCTURE**: 'For a focal living character at medium viewing distance, first produce an identity-bearing outer silhouette and coordinated head/torso/limb masses, then design the face and material-dependent internal regions to support the intended expression; for a distant supporting figure, simplify those internal regions while preserving the identity silhouette. For changing viewpoint, generate matched alternate drawings from the approved canonical image instead of rotating an unlayered face.' This is only a **method skeleton**, NOT yet a verified Kurzgesagt rule. A real skill must replace each generic phrase with source-grounded visible details and actual production operations from real experiments.

## E. Prompting is a skill-controlled EXECUTION STAGE, not independent art direction

**Authority and the non-negotiable distinction**:
- `ORIGINAL_BRIEF` controls WHAT (new subject, environment, story-required action, original personality and objects). It may include explicitly requested composition/content; cannot assert the learned brand style.
- `LEARNED_STYLE_SKILL` controls HOW it looks (the entire *target style*): design grammar, construction decisions, relative complexity, material treatment, facial/silhouette construction, stylistic rendering, conditions, references, required art-state production. No free-form LLM-created style clause may be appended between skill selection and image call.
- `SCENE_ART_PLAN` is a deterministic or skill-invoked mapping of content + chosen style recipe to placement/depth/focus/layer/pose needs. It cannot independently introduce decorative style motifs, colour treatment or unspecified art quality prose.
- `CHARACTER_BIBLE` locks previously created and approved original identity, face/limb/wardrobe/pose/view design; it cannot rewrite global style.
- `PROVIDER_CAPABILITIES` control representation (allowed reference images, resolution, prompt limits, edit features, cost), not aesthetics.

**Creation of style skill templates** is the artistic judgment stage: an investigator may propose candidate decisions grounded in source images and experiments, but the approved version becomes **fixed data**. At runtime the compiler must never generate new descriptive style paragraphs on its own. If it needs a new style clause, interrupt the compile and open a new explicit `SKILL_REVISION_REQUIRED` investigation, with user/art evidence. A new user-selected creative direction may change *content*, not covertly overwrite the style contract.

**Prompt compiler procedure** (prescriptive and implementable):
1. Validate original content and requested shot/asset route; load pinned exact style-skill version(s) with callable operation recipes. Reject unknown or unpinned skill IDs.
2. Evaluate the skill's typed applicability predicates against the original brief, material/view/visual roles, action needs, camera distance and approved character bible. Unmatched relevant visual decision => `UNRESOLVED_STYLE_DECISION`, not invented filler.
3. Resolve dependencies and conflicts in the skill's declared priority order. Construct a `DesignDecisionPlan` which contains **complete selected visual decisions**, exact source evidence IDs, declared condition values, art-component relationship graph and operation sequence. If mutually incompatible constraints remain, refuse with named conflict.
4. Render the SKILL-OWNED prompt templates for this route, filling **only typed original-content variables** and the already selected conditional style decision values. Source text for every style clause is the versioned skill template; source text for the novel subject/required action is the original brief. Do not allow a general LLM 'polish the prompt' postprocessor. Do not add ad-hoc style synonyms/adjectives.
5. Decide references using skill-owned **reference selection rules** and role-specific providers. Pass actual approved image bytes or authorized reference IDs; use canonical-image conditioning for variations. Do not exceed provider's actual limits; if important conditioning cannot fit, schedule a concrete staged edit operation or switch to a supported route, rather than silently dropping it.
6. Emit `CompiledImageRequest` with: ordered provider prompt, exact reference roles/hashes, original-brief provenance, all selected clause IDs, all operation stages, provider limits and output spec. No partially specified artistic decisions may be called complete. Any high-impact unresolved style construction decision causes `BLOCK_STYLE_INCOMPLETE` (not model improvisation).
7. Submit the **immutable compiled request** verbatim via provider adapter; no free-form prompt parameter accepted by the production API. Archive exact request, response, cost, output bytes and conditioning.
8. After image generation, judge artwork and repair **the appropriate source**, not by inserting untracked adjectives into the next request. Changes to an image's artwork must originate from a new skill revision, a permitted original content revision, or a declared edit operation inside the existing skill.

IMPORTANT: Even this cannot force image-model pixels. It prevents **unauthorized artistic instructions** at runtime. Model variability and latent interpretation remain, so production may use strong reference images, canonical edits, multi-stage generation and human judgment. No '100% non-improvisational pixel output' claim.

## F. Precision without 1,000-line positive prompts

Use a **hierarchy of constraints**, NOT more random adjectives: (1) whole illustration/art identity; (2) original subject's cohesive illustrated construction; (3) character and world relationships; (4) focal/background hierarchy and viewpoint; (5) material/colour/light treatment; (6) required local visual states; (7) small details only if demonstrated high impact; (8) exclusions. These are slots populated by **the selected skill and original brief**, not a universal assumed Kurzgesagt look. Some slots may be no-ops if not present in the references or irrelevant to a route.

Prefer actual reference image and localized editing when a style property cannot be reliably expressed in text; remember the approved original canonical art for dependent variations. Use multiple model stages if the chosen provider cannot handle all constraints at once. The compiler must produce multiple precise, short stage-specific requests rather than one huge contradictory prompt. Every required high-impact constraint has *a planned production operation*, not merely a keyword in a long prompt.

## G. Characters are built as coherent ART FAMILIES, not disjoint body parts

Start with **one complete, compelling canonical image**, generated from an original character brief and *character-specific style decisions learned from the source*. The image should show whole silhouette, designed parts, facial construction, costume, coherent colour/finish and intended scene integration; a skeleton is not a visual character design.

Before generating, derive an `AnimationDemandPlan` from intended shot actions: which views, expressions, gestures, prop contacts, body weight states, layer depth orders and camera scales actually occur. The canonical design process must anticipate these needs. Then create a **character art family** using approved original canonical art as visual conditioning:

- Design states by **whole silhouette / pose first**, then face and hands, not by rendering disconnected generic arms, circles and tube limbs.
- For a turn, change head outer contour, near/far eye/ear/nose/hair/face features and body overlap as a coherent drawing; do not rotate a full-face cutout as though it were a 3D head.
- For a reach/grip, construct **hand-on-prop as one coherent posed drawing** anchored on actual prop image, then segment only where motion benefits; don't generate hand/arm/prop independently and hope a numerical IK solver fixes mismatches.
- For walking/leaning, plan planted foot, shift of mass, torso/pelvis change, contact and clothing silhouette; art variants must match the canonical identity and intended pose relationship.
- For facial acting, expressions are coherent face drawings with interaction among eye/brow/mouth/cheek/hair/face contour—not independent tweened floating features.
- For complex turns/actions, prefer **full drawings/pose-swap with matched registration**; for stable rigid movement use separate quality-preserving raster layers and code-controlled paths. A hybrid route can vary by action.
- Obtain foreground/background occluded parts and clean plates through conditioning/editing or manual structured asset tools; actual alpha and layer order need a real source. Segmentation alone does not invent an unseen elbow, hidden torso or back of head.

`CharacterProductionRecipe` must explicitly specify: initial provider calls for identity and art, canonical references, pose/action manifest, reference-conditioned variation calls, hand/prop joint art route, layer segmentation strategy, occlusion generation, related scene placement, output images, registration anchors, exact motion and allowed substitutions. Full-art figure and face design must be a *primary visual success target* in first cluster, not deferred to the renderer. A poor character returns to the **character art-production procedure**, not another validation gate.

## H. Multi-error handling with real upstream fixes

Do not pick a single root cause by fiat. In one iteration maintain an interdependent list of significant defects; select a connected quality cluster and execute skill changes as a versioned bundle. Use diagnostic probes to distinguish observation/abstract rule/plan/compiled style request/provider image/canonical family/asset extraction/animation. Fix **inputs and producer method first**, while safety approvals and output checks act as backups. Cross-compare limited interventions if interacting changes make attribution unclear. No infinite loop of 'more checks'. User sees original full-res art at meaningful checkpoints, with defects and which producing decisions changed.

## I. Acceptance for this specific algorithm

The coder must implement executable tests where:
- Replace the original subject with an unrelated subject: the compiled style clauses/decisions remain style-governed and adapt through explicit conditions, while copied source nouns/character objects never reappear.
- Remove a high-impact style decision: the compiler changes the real provider request or refuses due to missing required operation; adding only a test/ledger is insufficient.
- Feed a new content brief with no style skills: **production refuses**; an unstyled comparison baseline is an explicitly separate `BASELINE_ONLY` experimental mode.
- Ask the runtime LLM to 'make it much more cinematic/beautiful' with no approved skill update: its message cannot alter the request's aesthetic instructions.
- Edit a canonical character's pose: the call reuses canonical-image identity and a typed motion/pose directive, not an unrelated generic character description.
- Change a style skill while preserving the same original brief: trace real image-request and, when paid use is authorized, observe actual visual differences.
- Ask for a source-specific object as a style rule: system reclassifies `SCENE_FACT` and excludes from general skill.
- Make observation vague: `VAGUE`, with a *targeted missing question*, never a fake complete style mechanism.
- Use provider incapable of the needed multi-view/edit/layer feature: select a truthful alternate production route or halt, rather than add a compliance gate pretending it fixed the art.

Success requires an **excellent original illustration** and evidence of reusable production effects. The schema, tests and compiler cannot themselves prove professional artistic quality.
