# 11 — Concrete input-first image production: what Claude must build, not just audit

Status: **ILLUSTRATIVE MANUFACTURING EXAMPLE ONLY**. None of these invented design decisions is asserted to be a real observation of the five Kurzgesagt films. The project must replace them after source investigation. A small executable deterministic compiler reference is included in `reference_impl/`; it demonstrates authority separation, not a complete image generator.

## Example: create an original expressive explorer + striking biological world

New user-created subject brief (not a source-film script): 'A curious explorer studying a floating living organism in an enormous underwater observatory. Explorer watches the organism, reaches toward a transparent chamber, then turns to react.' From this, the producer needs a gorgeous full illustration, expressive face, usable reach+turn states, and a world that remains coherent as camera/view changes.

**Wrong route**: Claude asks an image model to 'draw a beautiful Kurzgesagt scientist' and regenerates different faces for each pose, then tries to assemble a puppet from those unrelated JPEGs. This predictably puts all difficult style and identity decisions back onto the model.

**Correct route**: the learned conditional skills (as discovered from real films and tested on original material) determine concrete stylization choices, while the subject brief determines *who, what and why*. The style-owned production recipe schedules these operations:

| Stage | Artistic question answered upstream | Actual creation operation | Preserved dependency |
|---|---|---|---|
| Original whole-scene concept | How are subject hierarchy, environment design, richness, objects and atmosphere treated in this visual language for THIS viewpoint? | Generate full original art using exact selected skill clauses + role-typed visual references + original scene brief | Scene art plan/version |
| Canonical character art | How does the learned character-illustration method create appealing silhouette, face, proportions, clothing and expression for this NEW character? | Conditioned canonical image generation; approve source of character identity | Full-size image SHA |
| Original complete environment | How does art language adapt to biological/machine structures and foreground/far-view roles? | World-construction route, with a plan for foreground/near/mid/far layers *before* generating | Approved scene/character look |
| Necessary expression / pose | What must change in the full drawing for head turn, focus, surprise, reach, hand contact, clothing response? | Reference-guided edit / canonical-conditioned alternate drawings; coherent full-pose art first | Canonical character + actual prop image |
| Layer extraction | Which parts actually need independent movement, which are hidden and must be newly drawn? | Mask/segmentation + inpainting/clean plates/occluded surfaces as appropriate | Approved full composite + pose family |
| Animation program | Which motions can remain transforms, which require replacement drawings, how does camera, prop, character/world interaction change? | Compile event/state graph and use renderer to move approved asset versions | Exact drawing/version hashes |

If the chosen provider can't preserve the same face while drawing a head turn, the answer is **not** a longer prompt about facial beauty. Choose a different conditioning/edit approach, explicit key-drawing route, or provider, then record the actual working method. If layering damages the image, use approved composite images plus matching state drawings instead of slicing apart the artwork at all costs.

## Image prompt, with ownership of every artistic decision

A real compiled request should contain (in priority order, not as independent free-form prose):

1. `CONTENT` from original brief: original explorer, original organism, original room and explicit needed action.
2. `STYLE DECISIONS` from pinned learned skill: conditional art construction for this kind of original subject and visual role; exact selected style clauses and role-typed reference images, **no agent-added decorative adjectives**.
3. `SCENE RELATIONSHIPS` from skill-specific layout/representation recipe applied to new brief: what occupies foreground/background, focal relationship, visual relation to environment, coherence of art treatment.
4. `IDENTITY` from approved canonical art when generating derivatives, with exact image conditioning and edit scope. Do not recreate identity from text alone.
5. `OUTPUT TECHNICALS` from provider adapter: real supported dimensions, reference/edit/mask limits; output file requirements.

A production prompt can be long if necessary, but writing 1,000 lines that contradict each other is worse than using 1–3 strong art references with a targeted, precise task. A *large* amount of learning lives in the skill's assets and provider operations, not only in the positive prompt string.

### Required rules preventing independent style invention

- Runtime style descriptors appear ONLY in `skills/<id>/prompt_templates` and `decisions.json` from **frozen** style skill versions. The scene art plan is populated with pre-declared skill decisions and content fields; it does not author new style.
- All required style decisions are prioritized before compilation by the skill recipe. A generic language model can select a source-grounded **question to investigate**, or create a candidate skill revision, but may NOT 'improve' an approved image prompt by authoring new untracked adjectives or style methods.
- Image production API accepts **a compiled request ID**, not arbitrary `positivePrompt` from an orchestration agent. An explicit `BASELINE_ONLY` test may use unspecialized provider prompts, but its outputs are never promoted as learned style.
- Each art operation takes source/original subject/reference role hashes and emits real image bytes+provider task ID+cost and a content-addressed output record. The canonical image is used as reference for all variants where supported.
- Changes in skill version **must change the selected art operation, provider prompt/reference conditioning, or both**. Merely editing a Markdown file does nothing.
- The system may propose an additional candidate style rule only by returning to the explicit observation→decision→production recipe stages in `09`, with source grounding; it cannot invent it mid-prompt.

## How to make the original prompt specific WITHOUT overfitting

At runtime, select decision clauses by **conditions** like `visual_role=focal`, `subject_class=living`, `view=three-quarter`, `distance=mid`, `action=hand-grip`, `world_complexity=complex`. These are creative requirements and observable states, NOT the source movie's specific bug, insect, city or character. A single rule may have variants for focal/detail-dense versus distant/simplified subjects; no one-size-fits-all template.

Each chosen rule includes: `trigger; goal; concrete design operation; visual-reference role; prompt_template; required output state; interacting rules; exception cases; unresolved degrees of freedom`. The image generator is given the **relevant** variant only. Do not fill unrelated clauses with boilerplate.

## Stop from the producer, not only from the review gate

The compiler must refuse **before generating** whenever a required artistic decision isn't defined, the required original identity image is missing, the model does not support the assigned reference/edit operation, or a compound rule depends on an absent world/character decision. Do not silently use default 'professional vector style'.

Following image generation, the first response to ugly characters is to identify whether the construction method specified the appealing silhouette and whole-body/face relationships in the first place and whether the provider followed it. Improve **that design and production step**. The user's review then prevents approved downstream animation of poor results; it isn't the mechanism that creates beauty.

## Evidence that this architecture actually works

For the first cluster: show the real ORIGINAL full-size whole scene and ORIGINAL character closeups, not source copies; the actual style-owned design clauses selected, actual compiled provider requests, true images, a change in output resulting from the skill, and the most significant remaining artistic deficiencies. User may reject. Only build the view/pose/hand/layer family from approved canonical art; only render an integrated motion scene after usable art-family approved. No claim of mastery until the methods produce distinct original subjects with attractive artwork.
