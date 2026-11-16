# VME v1.3 — Addendum 29: Source-first character-art decision investigation

**Status:** Proposed additive requirement for independent review **after** the running Addendum 28 implementation finishes. Do not inject into an active coding run, interrupt its audit export, or treat this file as already implemented. Do not alter the 15+1 every-frame obligation, human approval, source authorization, offline financial safety, or source-to-skill provenance rules.

## 1. The gap and the corrected order of operations

Addendum 28 mentions silhouettes, anatomy, faces, eyes, hands, views, costume, light, materials, acting and cross-character relationships. Those are necessary *search domains*, but their presence in a checklist does not require the investigator to discover the actual **studio-specific design choices** that make a source character coherent and beautifully illustrated. A generic human/anatomical template can produce a valid skeleton yet the wrong illustrative character. A checklist can also produce an anatomically plausible but ugly actor with tube limbs, unconsidered joints, facial features pasted on a circle, and arbitrary shading.

**Required ordering for each character family:**

1. See the **entire source-drawn actor** at native viewing size and understand its artistic effect, identity, narrative role, and relation to the whole frame. Avoid anatomy labels at this stage.
2. Describe the actual **visible masses, lines, boundaries, shape rhythms, negative spaces, colour/light regions, detail accents, and their relationships** without assuming a human skeleton or standard body parts.
3. Observe how that *same visual design* changes across frames, expressions, actions, viewpoint, lighting and shot scale. Identify which components preserve identity, which are redrawn and which are intentionally hidden, exaggerated, simplified or omitted.
4. Only then map semantic roles such as hand, arm, face, head, torso, clothing, held object or support point onto their *observed illustrated treatment*. The anatomy is an **interaction/pose constraint**, never the source of the aesthetic recipe.
5. Compare unlike original character families and meaningful counterexamples across references. Separate common style grammar from character-specific inventions, view/action conditions, scene lighting, shot distance and possible exceptions.
6. Derive exact actionable **conditional artistic decisions** capable of making new, non-copied characters. Preserve source examples and unknowns. Compile only supported choices through the skill and production operators; no freeform anatomical or generic-cartoon aesthetic fallback.

The character cannot become `CHARACTER_STYLE_LEARNED` because fields named `silhouette`, `face` and `hands` contain text. The standard is source-grounded, distinctively illustrated, identity-preserving output across new characters and their required states, with honest unproven status until reviewed.

## 2. Required source evidence before any character-design conclusion

For **each actually visible character** in the selected 15+1 sequence frame ledger:

- Assign stable `source_actor_id`, `source_character_family_id` where justified, `frame_id/PTS`, `shot_id`, whole-frame witness, visible region/bounding polygon or clearly described bounds, foreground/occlusion status, view and action state. Do not force identities across edits when ambiguous.
- Per actual frame retain observable changes to external contour, internal contour, colour/light/shadow and finish, joint/part occlusion, expression, contact, state entry/exit and whole-frame visual role. The existing every-frame inspection remains mandatory; **deep character dossiers aggregate these records** so redundant text is not invented for hundreds of unchanged frames.
- When a high-impact artistic distinction cannot be seen at the supplied resolution, request a real native-source crop and its contextual whole frame. Persist both image-byte hashes and request/provider receipt; mark `INSUFFICIENT_NATIVE_DETAIL` if true visibility is impossible. Do not declare eyelashes, brush texture, cast-shadow causality, exact eye construction, or artist intent from compression artifacts.
- Make an actor state sheet from **actual witnessed** examples: resting presentation, most informative head views, meaningful expressions, body poses, gestures, prop contacts, lighting changes, and scale changes. It is an evidence index, not an imagined model sheet. Never invent an unobserved turnaround or expression state and call it source evidence.
- Keep previously investigated film/frame/character evidence by source hash and witness ID. Reinspect only where a *named precise gap or contradiction* remains. Preserve existing raw vision answers, not only a character-summary paragraph.

If the 15+1 footage contains inadequate diversity for a consequential proposed character rule, mark the family/condition `UNRESOLVED_BY_CURRENT_WITNESSES`, specify the **exact missing witness type** and its new source interval if available, and seek authorization under the existing sequence-selection contract. Never fake cross-character transfer by repeatedly comparing the same near-identical actor.

## 3. Character-focused investigation passes: observe phenomena before labels

These passes are conducted on whole-character witnesses, supporting native crops, changing frames, and cross-reference examples. They are an **investigation procedure**, not hard-coded answers. An irrelevant item is marked not witnessed for the specified interval; an unlisted consequential phenomenon must be added.

### C0 — Whole-look and attention test

At actual intended display size, record what the actor visually communicates: focal character or background figure; warmth, gravity, tension, humor, tenderness, danger, competence or another source-observable effect; perceived simplicity versus sophistication; visual weight and balance; shape/colour/finish harmony with its world; recognizability at small scale. Separate the **effect** from its candidate causes. Identify the exact artwork that attracts attention first and what keeps the design cohesive. Do not record adjectives as production rules.

### C1 — Shape construction before anatomy

Trace the **outer silhouette as art**: successive bulges, tapers, flats, concavities, rounded vs sharp transitions, intentionally unequal sides, contour tension, soft/hard inflection, long-vs-short curve rhythm, negative-space pockets, thickness transitions, source-visible deformability, and where outlines merge or separate. Work at overall-body, major-mass, and contact-region scale. Locate which contour segments dominate recognition. Observe head-to-body *artistic* mass relations only if visible; avoid assuming a universal head/body ratio.

For a source-drawn appendage, do not write only `arm: tapered`, `leg: tube` or `hand: mitten`. Record how its **entire visible contour originates, expands, narrows, curves, merges into the parent mass, changes width near a bend, terminates, overlaps, and participates in negative space**; which edges exist only due to costume seams, shadow shapes or occlusion; and how the shape changes under action and different views. Explicitly capture visible non-tubular, asymmetric, broad-to-narrow and integrated silhouettes where witnessed. A semantic limb label is secondary to these visual observations.

### C2 — Character graphic language and detail hierarchy

Find the specific treatment of large, medium and tiny detail: where surfaces are deliberately empty, where small contrasting accents are concentrated, edge termination, line/no-line boundary choice, border widths relative to scale, smooth vs irregular curves, repeated motif shapes, seams, notches, emblems, folds, pattern distribution and silhouette-supporting internal shapes. Explain *why the placement supports the whole look* as an evidence-tied hypothesis; do not spray decorative details across empty regions.

### C3 — Face as a composed artwork, not a standard feature inventory

At supported crops and whole viewing scale, observe the facial **design composition**: relationship among visible head contour, forehead/cheek/chin shape, near/far face visibility, brows/eyes/eyelids/gaze, nose depiction or omission, mouth shape/placement, expression marks, ears/hair/helmet, and each feature's relation to head angle, emotion and whole-actor pose. Record eye and mouth boundaries and negative space relative to the illustrated face, not generic human landmarks. Distinguish drawn facial exaggeration from temporary pose/expression states. Inspect where facial details are intentionally absent. Trace which contours, highlights, shadows, overlaps or facial designs are redrawn at head turns; never simply rotate a flat face without evidence the effect is appropriate.

### C4 — Character identity and expressive construction

Identify what remains visually recognizable between expressions, rotations, scale changes and staging: coarse contour identity, palette roles, signature shapes, face composition, costume/accessories, pose attitude, asymmetry and rendering treatment. Identify which of those are universal studio language and which belong only to this character. For each expression/action, compare the **whole pose and whole silhouette**, not eyes/mouth in isolation. Record gaze, weight, head, shoulders, arms, hands and costume changes together when observed.

### C5 — Hands, contact and joint *illustration*

Inspect **the actual visible drawn solution** for hand/arm/prop contacts: boundaries that belong to the hand, sleeve, limb or object; visible finger grouping or deliberate finger omission; contact points; grip-facing surfaces; foreshortening; overlap order; hidden surfaces; shadow shape; and how the hand shape changes from open/relaxed to pointing, holding, pulling or pushing. Compare physically equivalent actions drawn by unlike actors, and the same character under different action conditions. Validate contact and joint feasibility in an underlying interaction model **without replacing the source's distinctive shape with tubes, generic stick limbs or block hands**.

### C6 — Materials, colour and lighting as *character illustration*

Track specific colour **roles** across face, body, clothing, accessories, and contacts: relative warm/cool, value/chroma grouping, focal accent placement, large-colour-area boundaries, shifts under illumination or mood, and how colour segmentation supports form/readability. Investigate shadow shapes and transitions: which shapes carry form, which imply an overlap/cast shadow, which are decorative drawn shapes, softness, hue shift, highlight/rim/accent placement, edge hierarchy, self-occlusion and environmental light relationship. Record source ambiguity. Do not call one flat gradient `complex lighting`, fabricate a physically accurate light rig, or transfer a different character's lighting unchanged.

### C7 — Costumes, accessories, and organic/inorganic part relationships

Observe whether costume surfaces follow/replace silhouette or sit over an inner body; how seams, collars, sleeves, belts, helmets, protective gear, body panels, fur/feathers, scales, hair and accessories alter character identity and body/limb readability. Trace the rendered interfaces: where a sleeve creates the visible arm silhouette; where a glove changes hand grouping; where an accessory casts a shadow; where a prop requires a different pose illustration. Do not impose human clothing/skin construction on non-human source designs.

### C8 — Temporal art-state analysis

For each meaningful motion event, classify what actually **changes in the drawing**: whole silhouette, local shape, view, face elements, clothing/hair overlap, shadow plane, highlight, hand/prop contact, layer order, body balance. Distinguish observed pixel change from hypothesized software technique (replacement drawing, deformation, transform or camera). Identify minimum required *original-production* pose/view/expression/hand-state assets for analogous novel actions. Link states to movement/event dependency and prevent impossible grip, limb length and occlusion. A generic skeletal rig is not evidence of matching the source's finished art.

### C9 — Character in environment and at final display scale

Compare character vs world illustration: edge softness, palette relationship, contrast hierarchy, ambient colour, foot-ground contact and cast shadows when visible, reflection/occlusion, silhouette readability over backgrounds, focal/secondary character density, spatial placement and cropping. Review reduced-size frames: ensure facial accents and limb contours retain designed readability rather than dissolving into noise. A beautiful detached character that clashes with the world is not a successful art model.

### C10 — Whole→parts→whole synthesis

After dissecting a character, return to the entire frame and ask whether the proposed design mechanisms explain **the complete visual character**, including overall appeal and visual consistency. If a mathematically detailed recipe would still plausibly produce ugly/tubular/flat/randomly shaded artwork, label the earliest unsupported producing choice and reopen it. Do not promote a component-level interpretation that violates observed whole-artwork aesthetics.

## 4. Cross-character transfer: discover the artist's *choices*, not an average anatomy

For consequential candidate choices, compare at least **two materially different witnessed characters where available**, plus a counterexample/exception or explicit missing evidence. Prefer contrast involving genuinely different shape language, role, material, species, costume, viewpoint, expression or staging rather than arbitrary pairs. Compare also within the same character across changing states.

Classify every supported decision at the smallest defensible scope:

- `STYLE_INVARIANT_CANDIDATE`: a repeated relational decision across unlike characters, with counterexample search.
- `CONDITIONAL_STYLE_RULE`: changes with actor class, view, pose, scale, material, light or attention role.
- `CHARACTER_IDENTITY_RULE`: essential to one character's identity; **must not** be copied into unrelated original characters.
- `SHOT_OR_EVENT_RULE`: only supported for a particular situation, edit or lighting event.
- `UNKNOWN_OR_CONTRADICTED`: evidence insufficient, conflicting, compressed, or not visually discernible.

An artistic choice must remain conditional even if multiple examples share it; do not infer an unconditional brand rule from two near-identical characters. Preserve exceptions and allow later evidence to reopen previously accepted decisions.

**No generic-anatomy backfill:** If the source does not reveal an appendage, facial feature, joint, shadow, clothing part or alternative view, the source does not prescribe its artistic treatment. Ask which unseen artwork an original action *requires* and obtain an approved original generation/edit path; do not invent that it was observed in the references.

## 5. Question selection: move from a *failed production choice* to its decisive source witness

Use the existing ActiveArtProblem/cluster system. A character-specific gap has priority if it can dominate perceived quality or make animation impossible. Select the single **most consequential discriminating question at that decision point**, resolve it with exact whole/crop/temporal/cross-character witnesses, then continue through related gaps inside the same iteration. Never enforce a fixed number of questions, a pre-scripted face/arm checklist, or a separate disconnected character loop.

The investigator must identify:

1. **Exact visible failure or missing producer choice:** e.g., an unqualified forearm-to-glove contour rule, eye placement under a three-quarter view, a matte gradient that should be shape-specific, or a grip that requires newly drawn overlap.
2. **Why the present observation is inadequate:** e.g., source seen only front-facing; no meaningful contrast; a cropped hand lacks context; lighting vs material not distinguishable.
3. **Exact discriminating source evidence:** source IDs, frames/PTS, whole-frame context, native crop and neighboring frames, unlike-character witness, possible exception.
4. **Conditional choice to be resolved:** distinct alternative constructions, each predicted to produce a different visible outcome.
5. **Real effect in the original-production operator:** reference role, prompt clause, changed drawing states, masks/clean plates, rig limits or shader/edit instructions.
6. **Remaining uncertainty:** if source cannot settle the choice, keep UNKNOWN; do not dress an inference as observed studio intent.

Example of a **bad** question: `What should arms look like in this style?`

Example of a **good question *structure*, not a source finding**: `In the witnessed bent-arm and relaxed-arm states for actor A, which observed contour-width and forearm-to-cuff transitions preserve the character's graphic mass and avoid a cylindrical look, how do these differ for contrasting actor B, and which exact state-dependent drawing rule should the producer apply to a new original actor under a bent elbow and sleeve contact?` Actual source observations and any claimed contour direction must come from real frames, not the question's wording.

## 6. Convert the evidence into authoritative, usable character-production skill

For each consequential character-art decision, persist at least:

```
decision_id; family/scope; observed_effect; source_witnesses_and_native_crops;
direct_visible_facts; inferred_mechanism_and_alternatives; contrast/counterexample;
character_identity_vs_shared_style; triggering_subject/view/action/scale/light/role;
construction_choices_and_geometry_relationships; colour/material/light_regions;
required_original_illustration_states; contact/occlusion/layer_constraints;
reference_roles_and_consented_actual_bytes; producing_operator_and_parameters;
skill_owned_positive_and_negative_clauses; exception_rules;
expected_original_visual_change; unresolved_questions; human_review_status
```

**Every field must have actual substance where relevant; an empty-but-valid schema is not art knowledge.** Do not infer source truth from a field's presence, a confidence number, or a regex. If the model cannot convert the answer to a precise action without inventing an appearance choice, return the knowledge to investigation as `UNACTIONABLE_OR_UNKNOWN`.

The *original character identity* is designed for the new script, using source-derived transferable **conditional style rules**; it must not clone the exact reference actor. The character's canonical art must be approved as a whole illustration before it becomes the source of identity continuity for subsequent original pose/face/hand state generation.

**Real producer path:** witnessed source → scoped artistic decision → immutable skill clause/reference bytes → skill-controlled chosen generation/edit operator → actual provider request → original canonical art → inspected/approved original states → contact- and view-aware animation → original rendered frames. The image model receives the exact source-supported construction clauses and actual authorized visual reference bytes; no second prompt writer can append its preferred `cute cartoon`, `smooth tubes`, generic face, default shadows, or other independent aesthetics. If required references exceed provider limits, apply an authorized staged plan, not silent omission. Record a provenance trace for all consequential requested choices.

**Important boundary:** A skill controls which instructions/refs the image model is given. It cannot literally dictate every pixel the generative model decides to output. Unexpected pixels become observed production deviations and new learning questions; never falsely mark them skill-controlled just because they came from a skill-owned prompt.

## 7. Explicit character-art qualification evidence

The engineering implementation must show a working source-to-operator path in the **existing** code, not a new disconnected character report. In addition to ST28 and R01–R24, require:

1. **Source-first negative test:** a fake visual description containing generic human-anatomy labels but no source-derived contour/material/face relationships cannot be marked construction-ready; an actual source-grounded proposal changes the producing instruction/operation.
2. **Contour-type discrimination:** two conflicting, source-witnessed actor appendage treatments survive as different conditional rules; the compiler never replaces them with a universal `tube limb` or stock human-skeleton shape.
3. **Identity vs transfer:** a source character's signature face/costume is not generalized into every unrelated original actor, while shared demonstrated rendering language can be transferred under its supported conditions.
4. **Face/view relation:** a meaningful view change requires supported redraw/ref/pose specification; an absent state remains missing and blocks claiming correct animation, not silently solved by rotation.
5. **Colour/light relation:** an observed character-specific illumination region is preserved as an actual prompt/edit choice with correct scene relationship; an unsupported generic flat gradient does not qualify as matching source shadow treatment.
6. **Hand/prop and contact:** true overlap order, placement and grip constraints are consumed by art and animation; missing original state assets block the capability honestly.
7. **Whole-art look vs component syntax:** an original test character can fail whole-frame human artistic review despite every JSON category being populated; rejection reopens named decisions with exact source or provider gaps.
8. **Joint quality:** changing a relevant face×view×light or sleeve×hand×prop condition changes the exact frozen skill-owned clauses/reference roles and actual compiled request; no independent freeform prompt additions.
9. **Cross-character generalization:** hold out unfamiliar original actor designs and assess design coherence, facial quality, silhouette beauty, shading/material consistency, contact feasibility, identity across poses and scene integration separately. Preserve failures rather than averaging them away.
10. **Portability:** a fresh coding environment reconstructs the character dossiers, source frame IDs/crops, accepted and contradicted decisions, original canonical assets, action/view states, skill and provider request hashes, and precise next character question from the Investigation Capsule; it cannot auto-promote unknowns.

Offline strict fakes can show logical behavior, reference propagation, refusal and compiler control. They **cannot prove** visually beautiful artwork, good VLM interpretations or true generalization. Those require later authorized, source-grounded observation and human inspection of original outputs.

## 8. Implementation integration and safe sequencing

- Existing `vme/vision` source prompt, packet schema and observation parser must make character C0–C10 real model instructions and store their results/citations, not merely refer to this Markdown file.
- Existing `vme/investigation` gap/cluster selector must produce discriminating character questions and native frame reinspection requests from *actual observed failures*. No hard-coded universal character questions.
- Existing `vme/style` decisions, authoring, coverage and skill-compiler path must represent conditional character-art decisions and exclude generic visual fallback.
- Existing `vme` character producer, art asset/state generator, Remotion event/actor/layer consumer and approvals must preserve the resulting shape/face/view/material/lighting/contact artwork with clear missing-operator refusals.
- Existing audit export must contain source→character observation→distinct artistic decisions→skill clause/reference bytes→exact actual compiled request→original state operator trace, plus tests, limits and unknowns. Do not include user source frames or secrets in the audit ZIP without authorization.

**Current-run instruction:** Do not send this new addendum into Claude's already-running Comprehensive Repair + Addendum 28 session. Wait for its final audit ZIP; independently inspect the real character-investigation and production paths against this document, then implement only demonstrated deficits in one bounded subsequent code repair. Do not start the full 15+1 film study or spend Runware/Anthropic calls before that verification and explicit authorization.

**Acceptance principle:** A character investigator succeeds when it identifies the source's consequential *artistic design relationships* precisely enough for an actual conditional original-character drawing and animation process to reproduce the intended visual language. Human anatomy vocabulary may constrain physical plausibility, but it never substitutes for observed illustrated art.
