# 14 — Observation → transferable artistic decisions → actual skill: implementation manual

**AUTHORITATIVE.** This is the hand-holding algorithm for the coding agent, the investigation agent, and the skill builder. It supplements and sharpens v1.2 `09` and does NOT replace the 13-part mission. The goal is not to describe more source features; it is to learn artwork-producing choices that can be applied to DIFFERENT original subjects using actual models/tools.

## 0. Separation of authority

- `SOURCE_FACT`: what an actual authenticated film frame/sequence shows. A fact about one insect, city, planet or exact shot is evidence only.
- `VISUAL_EFFECT`: a high-impact quality shared by a meaningful class of artwork (e.g. legible complex world), named through actual contrasting images, never 'beautiful' alone.
- `CANDIDATE_CAUSE`: an evidence-grounded theory of which design *choices and relationships* cause that effect, with a counterexample.
- `CONDITIONAL_STYLE_DECISION`: for *original* content circumstances, choose a concrete artwork construction operation; specify exceptions and dependencies. Generality is conditional, not universal.
- `PRODUCING_RECIPE`: callable sequence of authorized image generation / reference conditioning / editing / asset extraction / animation with typed inputs/outputs.
- `WORKING_SKILL`: immutably versioned decisions + prompt fragments/reference images + producing recipe + executable code + actual original outputs and boundaries.
- `PROVEN_TRANSFER`: skill version frozen and applied unchanged to unlike original subjects, with observed retained quality. Do not mix qualification with code validation.

## 1. Identify visual qualities with the highest leverage

**Look at the actual film at normal viewing size first**; then examine relevant native detail and adjacent frames. Compare whole-frame, focal-subject, world coherence and motion state rather than starting from arbitrary nouns or measurements. Find the largest visible distinctions from ordinary/generic output. For EACH candidate difference:

1. **Locate** the viewer-noticeable feature in reference full-frame. Identify affected subject/region, relative importance, relation to surrounding elements and adjacent states.
2. **Specify** the quality with an observable contrast: 'Focal character's expression and hand-held prop read as one coherent gesture across the shot' is useful; 'expressive and polished' alone is not.
3. **Explain importance** using perceptual salience (attention, focal role, whole-frame consequence), cross-scene prevalence, and how improvement would change the original output. Do not invent an exact percentage.
4. **Rank candidate root causes, not symptoms**. An empty-looking world might result from weak scene structure, disconnected assets, missing scale/depth relationships, or wrong image generation route. Select a 2–5-member CONNECTED quality cluster, not dozens of unrelated style categories.
5. **Create a counterfactual target**: 'If we solve X, the original result should visibly differ in Y, even when content is changed.' If no predicted visual change, deprioritize.

### Do not ask

- 'What is the colour palette?' unless the quality difference demonstrably depends on colour roles and their relationship to other craft.
- 'What are the pixel coordinates?' unless placement itself controls a large missing relationship.
- 'Why is this beautiful?' without immediately decomposing it into *what is visible and what production decision would change it*.
- 'How did the studio make this?' as a factual question about inaccessible internal files. Instead: 'What callable operation can create this visible treatment on new subjects?'

## 2. The question generator: a precise loop, NOT a static checklist

Each question must name (A) an observed contrast, (B) the unknown needed for production, (C) the evidence needed to resolve it, (D) an actionable expected answer type. Proceed in order; generate a new question only where the preceding answer leaves an artwork-producing ambiguity.

**Q1 Locate the difference:** 'In this actual film frame/sequence, what specific picture feature makes [world/character/gesture/etc.] look substantially more [observable outcome] than our current original artwork? Which visible region/transition demonstrates it?' Answer must reference real film hash, frame ID(s), crop or short sequence, plus corresponding original output.

**Q2 Ask for construction causes:** 'Which specific art decisions involving [connected parts] could produce this feature, including foreground/background, part silhouette, finish, attention, pose, depth or temporal drawing states as actually relevant? Which evidence contradicts the candidate?' Answer must contain at most a few strong causal candidates with positive and contrasting witnesses, not an everything-list.

**Q3 Ask for variation:** 'What changes if the subject is an organism instead of a machine, or a far object rather than a focal character, or face view changes? Which relationship should stay and which must adapt?' Requires source examples or explicitly UNKNOWN. It may remain conditional on a narrow class (e.g. expressive bipeds) if evidence supports only that class.

**Q4 Ask for actionable form:** 'Given an entirely NEW brief, what decision must the producer make BEFORE image generation? What operations, references, masks or prompt clauses would implement it? What exact original visual state should result?' Answer must specify I/O and a concrete tool route.

**Q5 Ask to challenge the theory:** 'What observable original-art result would make this candidate wrong? Which competing explanation or tool limitation would it reveal?' Answer yields a discriminating test and required repair route.

**Q6 Ask what remains:** 'If a capable producer follows only the decisions and operations specified, which important *style* choices remain unassigned? Which are deliberately free creative content decisions?' Missing critical style choice generates a new Q2/Q3/Q4, not a default aesthetic prompt.

Questions with no evidence stay `UNRESOLVED`; revisit exact frames, other scenes, or a direct production experiment. **Question exhaustion isn't proof of style completeness**; the system stops investigating when it has an executable conditional decision and the resulting output demonstrates it, then focuses the next high-impact gap.

### Question record (must actually be saved)

`question_id`, `cluster_id`, `parent_question_id`, `visible_target`, `unknown_variable`, `film_witness_ids`, `original_output_ids`, `comparison_question`, `required_evidence_type`, `decision_to_enable`, `answer`, `answer_kind=OBSERVED|INFERRED|UNKNOWN|REFUTED`, `counterevidence`, `next_question_ids`, `status`, `producer_operation_affected`.

Don't let a generator produce paragraphs in place of these fields. The investigator can use prose for analysis, but production uses typed results.

## 3. How to OBSERVE at production-grade depth (source-first, not scene memorization)

For each selected high-impact question, assemble a **witness bundle**:

- A real full-size film frame in normal scene context, with film checksum, PTS/frame index and original bytes hash.
- Native crops or closely spaced adjacent frames when they materially answer the question.
- At least one meaningfully different case relevant to the proposed decision, and a contrasting/simpler treatment if available. If not available, state limited evidence; do not manufacture generality.
- A statement of only the observed *visible* relations: what objects/parts are present, how they are constructed relative to each other, what changes on viewpoint/scale/material/role, what moves in concert, and what remains legible.
- A separate statement of unobservables and competing explanations. A frame cannot prove a specific editing application or generation method.

**Specificity test:** Can an original-content producer determine which artwork to create and how it should visually differ from an ordinary result? If not, ask for the next high-impact missing relationship, not extra microgeometry.

**Generality test:** Replace all original subject nouns, colours, locations, exact timing and characters. If the extracted instruction stops making sense, it's a source witness, not a style rule. A rule may have conditional branches and still be transferable.

**High-impact test:** Imagine removing the proposed decision while keeping the rest. Would a substantial focal, whole-scene, character or moving-world quality degrade? If not, postpone until other gaps are addressed.

## 4. Convert a witness into a style mechanism: exact transformations

Each conversion uses seven recorded transformations; none can be skipped.

`T1 WITNESS`: immutable film frame/sequence IDs, visible feature and actual contrasting witness. Include `SCENE_FACTS_NOT_TO_COPY`.

`T2 EFFECT`: write a concrete target observable without objects from source, e.g. 'a complete illustrated world with coherent near/far detail and clear focal hierarchy'. Include why this particular effect is high impact.

`T3 CAUSE CANDIDATES`: propose 1–3 source-supported, contestable relationships; rank them by likely contribution, note conflicts. Distinguish observation from reasoning.

`T4 CONDITIONS`: produce `IF [original content class, visual role, material, distance, viewpoint, action, interaction] THEN [construction decision]`; list `INVARIANTS`, `ADAPTATIONS`, `EXCEPTIONS`, `FREEDOMS`, `DEPENDENCIES`, and `NOT_CLAIMED`. A rule missing any key distinction remains CANDIDATE only.

`T5 EXECUTION`: convert each selected construction decision into `OperationNode`s with `operator_type`, `typed_input_slots`, `visual_reference_roles`, `model_capabilities`, `skill_owned_prompt_clause_ids`, `mask_or_anchor_requirements`, `output_asset_contract`, `next_node`, `failure_alternative`. If the producer cannot name the operation and inputs, **it has not made a skill**.

`T6 COMPILE`: create versioned skill artifacts with frozen style templates and conditional dispatcher. For a new OriginalBrief, select rules using declared conditions, bind only permitted original-content slots, attach hashed visual references, choose actual provider route, and emit immutable compiled job. No runtime free-text 'make it prettier'.

`T7 DEMONSTRATE`: run on a NEW subject; inspect original actual image; if bad, isolate whether wrong source interpretation, conditional logic, prompt conditioning, model capability, edit/asset layout, or renderer implementation. Improve the UPSTREAM producing recipe. Freeze version and challenge on unlike unseen subjects before calling it transferable.

### Example 1 — Vague versus actionable observation (SYNTHETIC, NOT FILM CLAIM)

**Bad:** 'Kurzgesagt uses bright colours and many details.' Why bad: gives no choice for a new subject, no relationships, no operation.

**Better source witness:** 'In actual source frame X (to be filled only after inspection), the focal living subject has internally articulated colour regions while two distant supporting subjects use fewer internal divisions. The focal silhouette remains distinct from the environment through contrasting value grouping. A second different-subject source supports this, while a simplified diagram has an exception.' *This sentence is only the intended format, not an observation we already established.*

**Conditional decision candidate:** `IF role=focal AND subject=multi-part organism AND view=medium THEN design a single coherent outer mass, organize subparts as intentionally interlocking colour shapes according to anatomy and material, retain focal-region separation from world; IF role=background AND distant THEN simplify internal part articulation, while preserving identity silhouette; diagram scenes may intentionally override detailed material rendering.` Here actual materials/shape examples must be populated from source evidence.

**Executable recipe:** create original whole-subject art conditioned by selected source style references; define character/organism role and original anatomy from brief; use skill-owned prompt fragments for the style decisions; optional targeted reference-guided edits for the focal subparts; save composite and actual variants with masks if motion needs them. Do not claim `skill=qualified` without real original results.

### Example 2 — Character design+hand contact (SYNTHETIC)

**Bad:** 'Hands are flat shapes and arms are smooth curves.' This would drive generic tube limbs.

**Useful question:** 'When an expressive full-body figure turns and holds an object, which parts of the **designed drawing** must change together so the original silhouette, facial identity, visible/hidden limb side, hand-to-prop contact, and garment finish remain coherent? Which relationships generalize to new characters?'

**Candidate if/then:** `IF original_actor=stylized biped AND action=grip AND view=3/4 THEN choose whole-body acting pose with grounded weight and arm side; define prop position and hand-contact relation; create matched full pose as guided edit of canonical image; preserve head/face/costume identity; only after approved full pose derive separate moveable pieces and hidden surfaces for motion.` Do not substitute numerically rotated elbows for new illustrations.

**Concrete operations:** `MAKE_CANONICAL_CHARACTER → DESIGN_POSE_AND_CONTACT → REFERENCE_GUIDED_WHOLE_POSE_EDIT → MAKE_FACE/HAND_VARIANTS → SEGMENT/INPAINT_AS_NEEDED → RECOMPOSE → SCENE_EVENT_RUNTIME` (see 16/17). Failure of edit identity changes model route or prompts; a validator doesn't repair face design.

## 5. Store decision as a versioned, skill-owned executable object

Required file contents and exact relations:

- `decisions.json`: one decision per high-impact conditional quality, with independent source witness IDs, applicability, branch priority, exception policy, expected visible effect, and required visual artifacts.
- `prompt_templates/*.json`: only aesthetic instructions; clause IDs map to decision IDs and explicit permitted original brief slots; **never** let runtime rewrite these in free text.
- `references/manifest.json`: actual reference image sha, permitted role (style/identity/environment/pose/etc), native source witness, image hash, permissions, applicability; no untracked source conditioning.
- `recipes/*.json`: operation DAG of actual callables and output assets; no magic `GENERATE_KZ_STYLE` pseudo-function.
- `scripts/`: versioned producer adapters executing operation types; resolver refuses unknown operators.
- `examples/`: exact original brief, compiled request ID, actual provider response, produced PNG/WEBP, optional masks, canonical character and image comparisons.
- `SKILL.md`: thin entrypoint with usage conditions, required inputs, recipe path, exclusions and proven/unproven status. The style must still work if this Markdown is never pasted directly into the image prompt: it is the recipes and references that control art.

## 6. Which parts may the LLM decide?

**Research phase:** LLM can form questions and source-grounded candidate choices, with uncertainty and alternatives.

**Skill-development phase:** LLM can propose new aesthetic clauses ONLY as a `candidate_skill_revision` linked to witnesses, original outputs and actual manufacturing operations. Once reviewed/frozen, it has no untracked effect on runtime.

**Production phase:** LLM may invent original content when explicitly authorized by the Director/user; it may not add independent *style* directions, change skill-owned text, or silently substitute models or conditioning images. If a required style choice is absent, return `MISSING_STYLE_DECISION` and a focused new research question.

**Image model:** still synthesizes details/pixels. The intent is to minimize independent style drift by giving real art references and a good producing method; identical output is not guaranteed.

## 7. Failure diagnosis that changes creation, not just adds checks

When the result is bad, rank these causes using actual traces:

1. Missing/bad observation → inspect particular authentic source frames again and correct the witness.
2. Witness correct, conditional decision wrong → revise applicable/exception branches, using contrasts.
3. Decision right, manufacturing route wrong → change whole-scene vs guided-edit vs pose-family construction route.
4. Recipe right, request wrong → fix skill template/field binding/condition resolution; no LLM prompt patch.
5. Request right, model ignores/changes identity → change conditioning/reference allocation/edit method/provider; do not keep lengthening adjectives.
6. Image right, extracted parts bad → change mask/clean plate/part-family construction to preserve composite.
7. Art+parts right, motion wrong → fix pose transition, timing, contacts or camera renderer.
8. No meaningful visual gain across unlike subjects → demote technique, investigate another high-impact cause or capability limit.

The *first response* is to modify the producing stage actually responsible for the defect. Tests are secondary protection and proof.

## 8. Required implementation outputs and acceptance probes

One actual `investigate_cluster` command must output `WitnessBundle`, `QuestionTrace`, `CandidateStyleMechanism`, `DecisionContract`, `RecipeGraph`, `SkillVersion` and `CompiledRequestTrace`—or an honest `BLOCKED`/`UNKNOWN` where source/model unavailable. No codepath may silently fabricate a missing source witness or promote a scene fact to a learned decision. The build must accept a synthetic fixture for offline testing and use real film/VLM only after consent. Inspect a skill version change's *actual compiled request/operation graph difference*, not only a style hash change.
