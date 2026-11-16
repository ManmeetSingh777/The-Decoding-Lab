# VME v1.3 — ADDENDUM 25: Exact First-15 Sequence Selection, Every-Frame Visual Investigation, High-Impact Question Teaching, and Causal Skill/Prompt Enforcement

**MANDATORY, ADDITIVE SPECIFICATION.** Keep the entire original v1.3 ZIP and Addendum 24 unchanged. Add this file beside Addendum 24 in `Visual_Mastery_Engine_Build_Spec_v1_3/`. This addendum supersedes older language **only** where it specifies the first 15 sequences, question/observation methodology, per-frame processing for these sequences, source-to-skill handoff, or associated audit evidence. The approved 13-part system, initial **offline BUILD → implementation-audit ZIP → STOP** gate, paid-call consent, visual approval before animation, full-five-film eventual per-frame coverage, and portable handoff all remain mandatory.

## 0. Unambiguous separation of the three actual phases

1. **PHASE E — OFFLINE ENGINEERING, NOW:** Implement the selection engine, every-frame reader and mock vision packets, question investigation controller, skill conversion/compilation, prompt authority, image/character asset contracts, audit reports, interruption recovery, and tests. Source MP4s can be locally inspected/indexed with tools; **do not call paid vision, Runware, or upload source frames to an external service**. Deliver `VME_V13_IMPLEMENTATION_AUDIT.zip` and STOP for ChatGPT's independent code audit. Synthetic fixture outputs MUST be labeled synthetic, NOT learned Kurzgesagt methods or verified artistic success.
2. **PHASE L0 — FIRST REAL LEARNING, ONLY AFTER AUDIT + CONSENT:** Survey all five source films; select an initial ~15 contiguous real sequences using the exact selection procedure below; supply **every actual frame** of each chosen sequence for vision inspection; use native-detail reinspection and cross-sequence comparisons to derive the first connected character+world+movement skill cluster. Do not call partial selected-sequence coverage complete. Preserve the other film frames in an explicit unprocessed queue.
3. **PHASE L1 — FIRST ORIGINAL ART, ONLY AFTER L0 HAS SUFFICIENT EVIDENCE:** Compile original art requests from the actual source-derived frozen skills; generate and show **full-resolution original artwork first**, particularly characters and integrated environments. If the art is weak, improve the upstream observations/decisions/skill/model route; **no compulsory video render**. Once the artwork and animation-ready character family are approved, animate. Continue full five-film study afterward as budget permits.

### What "very specific" means

Do NOT interpret it as writing more adjectives, multiplying categories, reporting exact SVG coordinates, or inferring a private proprietary pipeline. A sufficiently specific finding is a **source-supported, conditional visual construction decision** that identifies (a) the visible quality; (b) what decisions actually produce it; (c) how those decisions depend on subject/material/role/view/action/scale; (d) the concrete model/edit/code operations that can produce it for an unrelated original brief; and (e) what remains uncertain. If no applicable operation or clear construction decision follows, it is NOT a completed style skill.

No engineering contract can eliminate a vision/image model's inherent perceptual or generative uncertainty. It CAN eliminate untracked style-authoring routes, unverified coverage claims, fabricated observations, and hand-wavy missing handoffs. Keep those distinctions truthful.

---

## 1. EXACT pre-study procedure — select high-value sequences across five films

### 1.1 Film lock, no borrowed artistic findings

For each one of the five original MP4s (source files, NOT previously produced reports):

1. Compute full-file SHA256; probe real video stream codec, width, height, nominal and average frame rate, duration, stream timebase, start PTS, and rotation. Store these source-specific facts.
2. Decode **all actually presented frames** in timestamp order. Record per frame `film_sha`, `video_stream_id`, `presentation_index`, `pts`, `pts_time`, `frame_width`, `frame_height`, `frame_content_hash` or reproducible hash-on-demand path, and `decode_status`. A metadata `nb_frames` value by itself is insufficient: confirm by actual decode. Variable-frame-rate material retains its real PTS; never infer frames from fps multiplication. Never combine streams or silently drop an odd frame.
3. Create a *navigation-only* entire-film shot/event atlas using local scene-change/motion detection and contact sheets, plus visual inspection as available. Shot boundaries are candidates, not ground truth; fix false/missed boundaries from actual footage. Mark open credits/outros/sponsors explicitly rather than blindly stripping them; main-film style evidence normally takes priority.
4. Keep `INDEXED`, `SURVEYED_FOR_SELECTION`, `VLM_SEEN`, `PER_FRAME_ART_OBSERVED`, `NATIVE_DETAIL_INSPECTED` as separate fields. A contact sheet or motion detector does **not** satisfy per-frame VLM inspection.
5. Store an immutable `FilmSurvey` with shot ranges, recurring actor IDs (provisional), world types, transitions, reference qualities, uncertainty and source timestamps. No old AnimationLab style reports are permitted as evidence.

The cheap full-film survey is for **locating potentially important scenes only**. It is not the deep study and cannot claim visual mastery. It may use sparse *navigation thumbnails* without confusing them with the later exhaustive within-selection pass.

### 1.2 Candidate collection — learn from the actual footage BEFORE selecting

Create a candidate list of distinct contiguous intervals **for every film**, not merely a preselected favorite frame. Aim for 9–15 serious candidates per film if present; record fewer with a truthful reason if the material lacks that many meaningful different events. For each candidate, store:

```
CandidateSequence {
  film_sha; candidate_id; start_frame_index; end_frame_index_inclusive;
  start_pts; end_pts; optional_shot_ids; actual_frame_count;
  key_witness_frame_ids[]; visible_actors_or_entities[];
  whole_visual_quality_statement; art_construction_opportunity[];
  whole_world_opportunity[]; view_motion_opportunity[];
  face_pose_contact_opportunity[]; simultaneous_events[];
  visible_proof_for_each_opportunity[]; known_limitations[];
  selection_role_candidates[]; estimated_vision_cost; sample_uncertainty;
}
```

`whole_visual_quality_statement` is a grounded one- or two-sentence characterization of **what is visibly strong about the complete artwork or moving world** in this interval. Reject "beautiful", "vibrant", "Kurzgesagt style", "nice lighting" without a specific visible relationship. Example **ONLY as synthetic demonstration, not a claim about the films**: "A complex living subject is distinguished from its layered environment through coordinated large and small illustrated masses, controlled focal contrast, and independently moving foreground/background elements."

For each candidate ask, **in this order**:

- **C1 — Whole artwork:** Does this interval demonstrate an unusually strong illustrated character, object, complete world, or a significant difference between elaborate and deliberately simplified treatment? Cite actual frames.
- **C2 — Connected craftsmanship:** Does it expose important interactions among the actor design, background, material, colour, viewpoint, part overlap, or visible emphasis? Which observable relationships?
- **C3 — Changes, not just snapshots:** Does the sequence reveal a pose/state replacement, contact, camera/world transformation, or simultaneous independent actions that would be invisible in a single screenshot?
- **C4 — Transfer potential:** Would investigating this answer a construction problem for multiple unlike original subjects? Describe the conditional question without copying nouns from the source.
- **C5 — Contrasts:** What other candidate from this film or another film shows the same visual problem with a different type of subject or an exception?
- **C6 — Redundancy:** Does this add new evidence beyond candidates already selected? State the NEW causal or visual question it contributes.
- **C7 — Feasibility:** Is its whole relevant action contained in a manageable **contiguous interval** with adequate entry/exit context? If not, expand or split into explicitly linked contiguous intervals; never skip frames in the selected range.

Do not use computed numerical beauty scores as evidence that one film is artistically superior. Simple selection ranks are administrative aids, and need visual witness rationales.

### 1.3 Deterministic assignment of ~15 sequences

Select **three distinct sequences from each of five films**, ideally filling three roles **per film**:

- **Role W — complete illustrated world and art craftsmanship:** An excellent whole scene, including original objects/materials/finishing and organized visual richness; character-in-world is especially valuable.
- **Role C — character or designed-entity identity and acting:** The whole actor, proportion/shape decisions, expression/head/limbs/interaction, or visually coherent alternate states. Prefer human/mascot characters when genuinely available; different species/roles/viewpoints across the collection. Do not fabricate an actor if absent.
- **Role T — moving perspective/scene change/combined action:** A meaningful camera/world/scale change, interaction, animation-rich transformation or multi-layer choreography; preserve all participating artwork and not just the motion values.

Treat these as **sampling roles**, NOT permanent skill categories or an assertion that a film contains exactly three kinds of style. An especially rich candidate may exhibit several roles; still select three *different* intervals per film, prioritizing variety. When a film genuinely cannot fill one role, choose the most relevant documented alternative and report `ROLE_SUBSTITUTION` with reason and missing coverage. Do not invent evidence or silently bypass cross-film representativeness.

Select in this fixed order:

1. Eliminate candidates without authentic source boundaries/visible examples or with only sponsors/outro unless a rare indispensable style feature is demonstrated.
2. For each film choose the strongest **Role C** candidate for different character types and high-impact whole-actor construction first; this protects character learning from being crowded out by backgrounds.
3. Choose **Role W** that introduces the most important *additional* world/art relation not already present in selected candidate(s).
4. Choose **Role T** that introduces a genuinely observable changing viewpoint, coherent artwork state, or simultaneous motion not already captured.
5. Reconcile all 15 as one **cross-film selection set**. Prefer source contrasts (different actor types, materials, scales, world complexity and visual treatments) over 15 highly similar bright shots. Replace the weakest redundant pick if alternatives reveal a missing high-impact quality.
6. Publish the `SelectedSequenceManifest` with, for each pick, `selection_role`, exact inclusive start/end indices and PTS, frame count, source hash, local preview path, visible high-impact contribution, why alternatives were rejected, linked comparison sequences, and a question-cluster ID. Preserve candidate rankings and substitutions.
7. Require a bounded source/vision-cost estimate with model capability notes; **obtain explicit user authorization** for actual source uploads/paid VLM calls. Do not silently pay or downsample because a sequence is long.

**Whole-event boundaries rule:** pick the interval that contains the actual relevant visual event, including pre-action and settle/transition where they explain style. Aim for approximately 5–15 seconds per sequence when adequate; **this is NOT a fixed cropping rule**. A longer coherent event can remain longer if approved, or be split into linked contiguous units with all individual frames preserved. Do not choose a tiny fragment solely to save money. Frame coverage for the chosen range must be exact, and changing boundaries invalidates stale packet claims.

### 1.4 Selection coverage ledger — what the first 15 DO and DO NOT show

Create a concise cross-film coverage table of **observed, source-linked opportunities**, not a blanket category checklist:

```
(character shape / body-face relation / whole-body acting / hand-prop)
(complete world / integrated object artwork / colour-material finish)
(viewpoint / state substitution / choreographed coexistence / spatial transformation)
```

For each area, include actual selected sequence references or `NOT_SEEN_IN_INITIAL_SET`; examples from multiple film types when possible; identify the largest visually meaningful unknown. The user can review the 15 choices before approving expensive vision. **This ledger does not declare style skills learned**; it only proves source selection was intentional.

---

## 2. EXACT per-frame study — every displayed frame of the 15 sequences

### 2.1 Absolute inclusion rule

Let a selection range be `[a,b]` inclusive in **presentation-index order**. Required actual target frame set: `{a,a+1,...,b}`. Store the source SHA and PTS for each. A selected interval with N = b-a+1 requires N distinct per-frame vision records supported by N **real frame image inputs** (at least one actually verified model-seen occurrence for each). Sampling at 10/12 fps, interpolating, object tracking, or contact-sheet-only inspection is a **hard failure**. Packets may include neighboring frames as additional context, but that does not excuse a missing target frame. A duplicate frame still needs to be supplied and considered; its concise answer may record *genuinely unchanged state* rather than hallucinate change.

**Do not confuse** decoded/indexed with model-seen, model-seen with semantically considered, or semantically considered with exhaustive native-pixel artistic comprehension. The audit must expose these as different claims.

### 2.2 Build the actual per-frame jobs

For each selected sequence:

1. Validate exact source hash, read decoded frames from the original MP4, ensure PTS monotonic by presentation order with explicit handling for repeats or special stream behavior. Convert each actual image to provider-supported encoding without altering identity/order. Record any resize and its source/output dimensions; never call a reduced image a native-detail examination.
2. Partition target frames into small **contiguous non-overlapping target packets**. Determine real max image count/size and output-token budget from provider; start with ~4–8 target frames per packet IF supported, shrinking to 1–2 when per-frame artistic answers are weak. Add up to two preceding and two following **context frames** only if accessible and provider budget permits, clearly distinguishing context from target IDs.
3. Each target frame is an image item with a manifest containing `frame_id, source_sha, presentation_index, pts_time, image_sha, width, height, scale_factor`. Never replace the input with a filename, URL without retrievable pixels, motion vector, sampled video, or summary.
4. Persist the exact visual question cluster, previous `SemanticBoundaryState`, and visual context before submitting the packet. Store logical job identity/idempotency and authorization state as Addendum 24 requires.
5. Submit a **multimodal** question with all actual target frame images, explicitly mapped to frame IDs in order. If model/provider cannot reliably associate each image with its ID, reduce packet size or switch supported route; do NOT fabricate frame-specific responses.
6. Demand one `FrameObservation` per TARGET frame, plus a `PacketTransitionGraph` and a proposed *question update*. Validate IDs and source provenance, and persist the unedited raw response.
7. If a packet omits/mislabels a frame or gives a generic undifferentiated summary for all, mark `NEEDS_REINSPECTION` and rerun only the incomplete packet with smaller batches/better frame inputs. Never advance the coverage watermark for missing frames.
8. Commit the frame observations and boundary state transactionally. Continue to the exact next frame. On timeout, resume from the last verified committed packet and open its actual boundary frames (Addendum 24); do not start from zero or invent its unfinished reasoning.

A vision provider can return a string that **claims** it viewed frames. Programmatic validation can confirm bytes were sent and records returned but cannot prove genuine human-level perception. This is why the content itself must be challenged through targeted visual questions, contrast, source-native crops and subsequent creation trials.

### 2.3 Mandatory per-frame observation contract (not an essay on every frame)

For each target frame, create a machine-readable record with these exact *conceptual fields* (the coding agent may implement more precise typed equivalents but must not drop any meaning):

```
FrameObservation {
  frame_id; source_sha; pts_time; request_id; submitted_image_sha;
  active_question_ids[]; scene_and_world_state;
  actually_visible_actor_and_object_ids[];
  focal_whole_artwork_state;
  visible_design_relations[];          // e.g. whole shape ↔ internal parts ↔ scene
  character_face_limb_contact_state[]; // only when actually visible
  visible_layer_depth_attention_state;
  changed_since_prior_frame[];        // specify actor/part/scene, WHAT changed
  simultaneous_event_links[];        // what coexists/depends/moves independently
  camera_vs_actor_vs_drawing_state;   // distinguish; label UNKNOWN if not observable
  material_finish_or_colour_change[]; // when actually significant
  native_detail_followups[];
  source_fact_statements[];
  hypothesis_or_uncertainty[];
  no_significant_change_reason?;
  raw_response_path; confidence_limitations[];
}
```

**How to fill each field:**

- Start by seeing the **entire artwork at its displayed scale**. Name the visible high-impact constructed world, focal subject, supporting objects and visually important interrelationships; do NOT jump to contour statistics.
- Describe **which designed shapes/parts jointly create the distinctive artwork** where that information is actually visible. For characters: whole silhouette, relative mass/feature organization, face identity/pose, garment/limb/hand junctions and contact. For worlds: coherent object design and near/far organization. Avoid measuring arbitrary points when no production decision follows.
- Compare against the exact preceding/next actual frames. Record what *visibly* changes and what stays constant: a complete new drawing vs a rigid transform is an inference unless distinguishable from visual evidence. Describe supporting clues and `UNKNOWN` honestly.
- State how scene composition, visible layers, independently moving components and emphasis change *together*. Do not reduce a moving multi-object scene to one camera position number.
- Note only relevant style questions this frame helps answer, with links to exact visible regions/frame IDs. If it answers none, mark `NO_NEW_STYLE_EVIDENCE` while still preserving its real frame inspection and temporal state.
- For apparently identical frames: record that the **actual supplied pixels** were inspected, which subjects/states persisted, and `no_significant_change_reason` with prior-frame reference. Do not make up an artistic change just to create more text.
- Never claim any character eye/hand was inspected if it was cropped out or visually too small. Mark visibility/uncertainty and point to appropriate full-resolution reinspection where possible.

All fields must be **observational**, not instructions to the image model. The production decision is formed in the separate cross-frame/cross-film investigation.

### 2.4 Prompt to teach the VISION AGENT how to look — actual template to implement

The implementation must construct the following role-specific request from typed selection manifest and question-cluster inputs. This is for **SOURCE ANALYSIS ONLY**, never directly reused as image-generation aesthetics:

```
ROLE: Visual-artwork and temporal construction investigator.
INPUT: original consecutive image frames with manifest [frame ID -> actual image],
       current whole-scene/character state and 1-4 active high-impact questions.
SCOPE: Only source-visible evidence; never claim source art-making software or intent.

FIRST: inspect complete picture for each frame at normal displayed scale.
 Identify the focal artwork, its deliberate shape/part relationships, supporting world,
 material/colour organization, depth and notable simultaneous visible activity.
SECOND: compare EVERY target image to its real neighbor images in time.
 Identify preserved identity and changes of whole-actor drawing, face/eyes/hands,
 contact, world layers, apparent camera changes and moving focal emphasis.
THIRD: seek evidence relevant to active questions; identify which visible relations
 appear to create the sought high-impact artistic quality. Do not promote a source
 fact to style. What can be OBSERVED, what is an INFERENCE, what is UNKNOWN?
FOURTH: for EACH target frame emit a typed FrameObservation with exact frame ID,
 concise specific visual facts and temporal relations; if nothing meaningful changes,
 explain what persists without inventing novelty.
FIFTH: emit a PacketTransitionGraph of linked simultaneous changes and the
 unanswered HIGH-IMPACT question that the next source frames/crops should resolve.
DO NOT: use "vibrant", "dynamic", "professional", "clean vector" as standalone
 explanations; write fixed palettes/character coordinates as universal style;
 infer proprietary source tooling; hide missing frames; repeat empty prose;
 confuse character-art changes with camera motion; invent unseen features.
IF visual evidence is inadequate, state UNKNOWN + exact missing image/viewpoint.
OUTPUT: strict schema, no natural-language summary instead of frame entries.
```

This request is **not sufficient on its own**; the investigation controller must manage active questions, frame inputs, cross-frame comparison and native-detail followups as described here. The vision model must receive the actual pixels, not merely an LLM telling it what a frame contains.

### 2.5 Native-detail and temporal escalation — answer the questions, don't pad reports

After each sequence's initial all-frame pass, the controller MUST:

1. Build a timeline of actual **drawing/art states**, visual-change events, actor/environment relationships and active artistic uncertainties grounded in per-frame IDs.
2. Identify high-impact moments where the model's initial resolution or frame-by-frame account is insufficient (focal face/hand, character design, material boundaries, a transformed object, a new world reveal, interacting silhouettes, viewpoint change, simultaneous animations).
3. Reopen the **original decoded native-resolution images**, crop with real pixel coordinates and content hashes, AND inspect original neighboring frames for temporal context. Do not claim a source small facial expression exists without enough source pixels.
4. Ask a narrowed question comparing WHOLE context plus native crops. Example: "What coordinated eye/head/silhouette/hand changes actually occurred between frame IDs X and Y, and how do the corresponding reference images support or contradict the current character-art construction theory?" Here X/Y are genuine selected IDs at runtime.
5. Store all new evidence and revise the applicable `QuestionTrace`. A method that needs this evidence but hasn't received it stays RESEARCH_ONLY; missing native resolution cannot be patched with invented detail.
6. Perform a **reverse timeline check** of the sequence: walk from ending artwork state back toward the starting state, checking for omitted intermediate drawings, actors, world elements, interactions or unexpected changes. Use the original indexed frames; this is an additional evidence check, not a claim of backwards causality.
7. Check that the final explanation covers both (a) whole-scene art quality and (b) the important moving relationships. Deep study may require more than one question pass over the *same genuine frame images*, each recorded as a distinct analysis pass.

**Priority:** re-inspect evidence that changes the planned construction operation. A tiny accent that doesn't alter the scene's major artistic quality is not worth a full analysis loop merely because it can be measured.

---

## 3. Teach the RIGHT high-impact question process, not just provide a list

### 3.1 The exact investigation unit

An investigation is NOT "study all colours". Each unit is:

```
ArtInvestigation {
  target_visual_quality;                  // what must visibly improve in original work
  affected_original_production_capability; // actor/world/view/motion + linked fields
  selected_source_witnesses[];             // actual frames and sequence links
  candidate_causal_relations[1..3];       // observations vs competing explanations
  cross_case_and_countercase_refs[];      // unlike subject or exception
  active_question_ids[];
  predicted_original_visual_difference;   // what new work will visibly show
  required_producer_operation;             // what image/edit/animation work to build
  status; unresolved_reasons[];
}
```

Do **not** fix target classes before source inspection. Start from visible high-value qualities, then select temporary specialists only for the actual questions discovered. Investigate **clusters of 2–5 interconnected high-impact relations** when the finished quality depends on their coordination; don't split shape, colour, expression and environment into isolated analyses if they construct one coherent actor-in-world scene.

### 3.2 The eight-question procedure — apply in order and stop when the evidence answers it

**Q0. What is the observable high-impact result?** At normal screen size, state a specific thing a generic illustration would lack. Identify the whole-scene/whole-actor effect and exact source image evidence. If you can only say "beautiful" or "Kurzgesagt-like", refine.

**Q1. What visible relationships appear to create it?** Name at most three currently strongest relations among designed shapes, internal parts, roles, material finishes, layers, scene organization, or timed changes. Cite source frames/regions for each; no arbitrary geometry inventories.

**Q2. Which details are causally important versus merely present?** For each relation, imagine removing or changing it while keeping the subject. Would the high-impact quality noticeably degrade? Mark `STRONG_CANDIDATE`, `WEAK`, or `UNCERTAIN` and explain from evidence; this is a hypothesis, not empirical proof until an actual original-art comparison exists.

**Q3. What happens in different cases?** Seek an unlike actor/world/material/viewpoint from another selected sequence, including counterexamples and intentionally simplified scenes. Are there conditional variations? A relation need not repeat verbatim across films to be a true style mechanism.

**Q4. What decisions would a producer make on a NEW subject?** Rewrite source facts into **condition → visual-construction decision**, with `INVARIANT`, `ADAPTATION`, `EXCEPTION`, and when it is not applicable. Never insert source object names, character ratios, exact colour codes or one scene's layout as universal style.

**Q5. What would still be left for the image model or animator to invent in STYLE?** Enumerate remaining high-impact aesthetic ambiguities: whole-form organization, detail emphasis, material response, identity transfer, layer integration, alternate views, contact drawing, etc. Resolve each with additional evidence or state `MISSING_STYLE_DECISION`; content-level invention remains allowed only from the original brief. Do not endlessly specify invisible microdetails that cannot materially change the output.

**Q6. What executable operation produces the decision?** Identify: provider-supported whole-image generation vs reference-conditioned editing vs multiple related drawings vs layer/clean-plate creation vs code animation; required actual image references, mask/pose anchors, typed inputs, expected raster assets and failure alternative. If no operation exists, research/implement one; do not call it a skill yet.

**Q7. What would prove it changed original art?** State the predicted visual before/after difference, suitable unrelated original subject, likely failure modes, and which stage is responsible for each. A baseline/transfer comparison provides evidence later; checks are not a substitute for the upstream creation method.

**Loop control:** If Q1 or Q4 is weak, return to source witness selection; if Q5 has material ambiguities, create focused questions; if Q6 is missing, build/choose the producing operation. Do not generate a giant unsupported style paragraph and move on. If the highest-impact gap cannot be resolved from the chosen 15, expand source witnesses deliberately (do not invent an answer or declare completed style).

### 3.3 Exact question quality rules — how to transform weak questions

| Weak question (REJECT) | What is missing | Acceptable question form (still answer only from real evidence) |
|---|---|---|
| "How do they make nice characters?" | No target effect, no construction relations | "Across DIFFERENT visible character designs, which whole-body shape/face/garment decisions make them belong to a coherent illustrative family while keeping distinct identities, and how should these decisions adapt for a NEW nonhuman actor?" |
| "Which colours are used?" | Static facts with no design choice | "How do foreground actor colour groups and environment colour groups maintain visual separation and coherent material treatment across different lighting/world types, and what must change for a NEW environment?" |
| "What is the head-to-body ratio?" | Source actor coordinates overfit | "How are head/body/hand proportions *chosen conditionally* for different actor types, acting states and screen sizes while preserving expression and an attractive whole silhouette?" |
| "How many trees?" | Scene-specific content | "What makes a complete environment read as a coherent constructed place rather than isolated repeated assets, and which visible methods adapt from a forest to an unfamiliar manufactured world?" |
| "What is the zoom speed?" | Number divorced from art state | "During a scale reveal, which illustrated layers, drawing detail levels, world relationships, focal regions and motion events change together, and how could a NEW scene be built with all required states?" |
| "What changes in the hand?" | Part-only view loses actor | "When an actor grips a prop, how do the WHOLE pose, near/far arm artwork, hand silhouette, prop overlap, clothing treatment and body support change together? Which new drawing states are required for a different actor and prop?" |

**How to answer:** Each answer must explicitly state `VISIBLE_FACTS`, `SOURCE_EVIDENCE`, `BEST_CONSTRUCTION_EXPLANATION`, `ALTERNATIVES/COUNTEREVIDENCE`, `APPLIES_WHEN`, `NOT_APPLIES_WHEN`, `REUSABLE_NEW_SUBJECT_DECISION`, `ACTUAL_PRODUCING_STEP`, and `UNANSWERED`. No generic elegance adjectives as substitutes for relationships. The question engine should request more pixels or a contrasting sequence **only when these fields are genuinely unsupported**.

### 3.4 Source-specific versus transferable — two rewrite drills

**Drill A — synthetic character:** Actual source observation *would be* "this particular original actor has a tall oval head, two small eyes and a jacket". That is a **source fact**, not the style. Investigate why the whole illustration's head/body mass, facial emphasis, garment transitions and expressive silhouette work together, across DIFFERENT source actor types. Candidate conditional decisions should not say "draw all actors with this actor's head shape". They should state source-supported **ways to organize a new subject's head/face/garment relations** based on species, personality, scale and action, then pick reference-guided whole-actor image operations to implement them. The exact decisions must still be discovered from the genuine films; this drill is not a discovered Kurzgesagt rule.

**Drill B — synthetic world:** Actual source observation *would be* "there are five glowing rings behind a machine". The rings and count are source facts. A transferable question might instead investigate how **subject hierarchy, environment depth, repeated visual systems, colour/material coherence and selected illumination** make the whole scene rich and legible. The output skill would choose scene-specific new objects from the original brief, but its spatial/artistic organization and finish would follow real learned conditional rules. Again, this is a procedural example, not a claim about the five films.

### 3.5 Connected character investigation — required high-impact branch

For every chosen Role C sequence, the investigator must begin with the **whole actor in its environment**, then examine the following only when actually visible and relevant: whole silhouette and appealing mass distribution; artistic body/head/hand size relationships; shape groupings and contour treatment; facial image construction and eye/gaze/emotion; clothing/material and shadow treatment; coherent nearby world artwork; limb joins, near/far occlusions, body weight; head-turn redraws and expression substitutions; contact and prop-held poses; secondary response and connected scene actions. Explain which parts **change together** to keep the actor attractive and consistent. Distinguish a genuinely absent hand/face from one missed due to low resolution. For each strongly supported finding, immediately specify which **canonical character image**, **reference-guided full-pose edit**, **expression/hand variant**, **whole hand+prop interaction**, **layer/mask/clean-plate**, or **scene motion operation** must implement it. Do NOT substitute stick-figure rigs, cylinders or per-source actor ratio memorization.

Make a cross-actor comparison table between unrelated source actors: `shared conditional artistic choice`, `allowed variation`, `exception`, `evidence`, `effect on new actor skill`, and `actual prompt/ref/edit operation`. If no contrast supports the decision, record limited scope and look for more witnesses.

---

## 4. Actual artifact chain from investigation to provider — no unexplained "skill" step

The coding agent must implement the following named logical types and persist each version, with one producer consumer for each. Exact programming-language identifiers can differ, but **no data contract boundary may be skipped**:

```
ActualSourceFrame -> FrameObservation -> CrossFrameEventGraph
      -> QuestionTrace -> CrossSequenceComparison
      -> ConditionalVisualDecision -> SkillOperationRecipe
      -> FrozenSkillVersion -> TypedOriginalArtBrief + SceneArtPlan
      -> DeterministicStyleCompiler -> CompiledImageJob
      -> ImageGateway -> GeneratedRaster + RelatedViewAndPoseAssetPlan
      -> OriginalArtworkReview -> CharacterPack/SceneGraph -> Animation
```

### 4.1 Precise decision record (JSON-compatible)

```
ConditionalVisualDecision {
  decision_id; version; target_quality;
  conditions: {subject_kind, role, material, view, scale, action, environment};
  invariant_visual_relation; adaptive_visual_choices[];
  visible_shape_and_artwork_relationships[];
  scene_coherence_relationships[];
  temporal_or_pose_relationships[];
  applicability_constraints[]; exceptions[]; forbidden_source_specific_copies[];
  evidence_frame_ids[]; contrasting_evidence_ids[]; uncertainty[];
  prompt_clause_id[]; reference_role_ids[];
  operation_node_ids[]; required_asset_slots[];
  expected_visible_effect;
  status: RESEARCH_ONLY|EXECUTABLE_CANDIDATE|DEMONSTRATED|TRANSFERABLE;
}
```

No `ConditionalVisualDecision` may be marked executable unless its real operator is registered and its style clause/reference roles are resolved. A style candidate can contain unknowns, but they are **not** silently filled by generic image prompts. If original content demands a missing high-impact decision, emit `MISSING_STYLE_DECISION` and create a targeted new investigation.

### 4.2 Skill-owned template and resolver rules

- Each frozen skill owns `decisions.json`, `prompt_templates`, `references/manifest.json` with actual image hashes/roles, and an executable `recipes` operation graph. `SKILL.md` points to these; markdown prose alone has zero art-producing authority.
- The **OriginalArtBrief** may supply only genuine original subject, action, intended focus and environment requirements. It may NOT smuggle in independent artistic style adjectives, invented outlines, palettes, shading defaults or character/scene design grammar.
- For each new art job the compiler resolves branch conditions from the typed original brief and declared scene state, selects exactly the relevant pinned style-decision clauses and visual reference roles, binds permitted slots (actor species, gesture, viewpoint, world type, material, etc.), orders them as declared by the skill, and emits the **complete provider-visible aesthetic instructions**. A free-writing LLM is not an allowed prompt postprocessor.
- The compiler must render conditional details **specific to the actual original asset** (e.g., if actor changes viewpoint, compile the observed cross-view and whole-actor identity clauses plus canonical reference; if a prop interaction is required, compile grip/hand+prop pose clauses). It cannot merely repeat one generic "in style" paragraph for every image.
- Model editing operators need actual `referenceImages`, edit masks, original canonical art, pose/view state IDs and correct provider capabilities. If a model doesn't support a required operation or enough image references, do not drop a reference to save cost; split into supported guided edits, choose a verified alternative, or mark BLOCKED.
- **Runtime code must prevent untracked model-authored aesthetic text**: the image gateway has no raw prompt API; only a fully signed/frozen `CompiledImageJob` from registered skill hashes is accepted. Any model-authored candidate art clause goes through versioned skill revision with source witness and immutable approval, not a silent production prompt edit.
- For fixed brief, skill version, provider route, reference hashes and parameters, canonical logical compiled request is deterministic. Provider-generated pixels are NOT guaranteed deterministic.
- When the source proves only a vague quality but cannot yet specify how to construct it, **do not compile a pretend precise instruction**. Find relevant witnesses and produce a real operation-supported decision first.

### 4.3 Example of actual compiled prompt structure (SYNTHETIC; not discovered style)

```
[ORIGINAL CONTENT — controlled by typed brief]
One original older marine biologist character, working inside an unfamiliar
undersea observation workshop, reaching for a sealed specimen container.

[ARTISTIC CONSTRUCTION — ONLY skill-owned decisions, selected for actor/view/role]
<selected entire-character silhouette and shape organization clause>
<selected source-supported proportion variation/face construction clause>
<selected actor-world colour/material coherence and detail placement clause>
<selected identity-preserving hand/prop reach whole-pose clause>
<selected viewpoint-specific head/face state clause>
<selected integrated world/foreground/background construction clause>

[VISUAL REFERENCE INPUTS — attached actual images with approved roles]
<selected style witness images> + <canonical original actor image where available>

[OPERATION AND OUTPUT]
<registered provider-supported whole-art or reference-guided edit operation>
<actual canvas/layer/clean-plate/mask/pose requirements from asset plan>
```

Angle-bracket text is **not** acceptable real prompt output. The first actual skill must replace every applicable clause with evidence-grounded, specific artistic instructions and actual images; otherwise it remains `RESEARCH_ONLY` and cannot call Runware as a style-qualified job.

### 4.4 Differentiating bad artistic reasoning from bad implementation

When the original output misses the desired quality, record independent causal statuses:

- `OBSERVATION_GAP`: the key visible art relation was never examined or misread; reopen source frames/crops.
- `STYLE_DECISION_GAP`: actual observation is true but the conditional decision does not tell a new producer how to draw; rewrite the decision using cross-cases.
- `SKILL_RECIPE_GAP`: art decision exists but no real operation or reference guidance constructs it; implement/revise recipe.
- `PROMPT_COMPILER_GAP`: right clauses in frozen skill but absent/wrong in actual provider request; fix compiler/gateway.
- `MODEL_CAPABILITY_GAP`: correct submitted request but provider fails to follow/maintain identity; change image/edit/reference route or provider.
- `ASSET_CONSTRUCTION_GAP`: artwork good but masks/layers/poses degrade it; revise construction/edit procedure.
- `ANIMATION_GAP`: art assets good but motion/camera/contact breaks it; change movement method.

Do not automatically send every bad visual result back for more source analysis; trace the actual stage responsible.

---

## 5. Implementation states, tests, and exact audit artifacts

### 5.1 Selection, vision and question engine lifecycle

```
FILM_PROBED -> FRAME_INDEXED -> FILM_SURVEYED -> CANDIDATES_RECORDED
 -> FIFTEEN_SELECTED -> USER_APPROVED_SELECTION_AND_BUDGET
 -> PER_FRAME_PACKET_QUEUED -> PER_FRAME_SEMANTICS_COMMITTED
 -> NATIVE_DETAIL_GAPS_CLOSED_OR_DOCUMENTED
 -> CROSS_SEQUENCE_STYLE_CANDIDATES -> SKILL_RECIPE_WRITTEN
 -> SKILL_COMPILED_SYNTHETIC / SKILL_COMPILED_REAL -> ORIGINAL_ART_REVIEW
```

Every transition carries source/manifest/version checks and is durably persisted. The selection is not approved merely because fifteen IDs exist. The selected sequence manifest must have **real evidence and complementarity**, or stay `NEEDS_SELECTION_REVIEW`. A film missing an appropriate actor/transition is an explicit exception, not made-up source content.

### 5.2 Must-implement CLI/entrypoints (exact names may vary; functionality must exist)

```
vme sources probe --folder source_films
vme sources index --all --verify
vme survey build --all --navigation-only
vme selection candidates --film <film_sha>
vme selection propose --target 15 --per-film 3 --roles W,C,T
vme selection explain --manifest <selection_id>
vme vision estimate --selection <selection_id> --provider <verified_provider_id>
vme vision plan --selection <selection_id> --every-frame
vme vision run --selection <selection_id> --every-frame --authorization <token>
vme vision coverage --selection <selection_id> --by-frame
vme investigate questions --cluster <cluster_id> --evidence <selection_id>
vme investigate explain --question <question_id>
vme skill trace --decision <decision_id> --compiled-job <job_id>
vme audit export --offline --out VME_V13_IMPLEMENTATION_AUDIT.zip
```

`vision run` must not be executable without explicit provider/source-upload/spend authorization. `estimate` can run offline given pinned provider cost data; if prices/capabilities unknown, return BLOCKED_FOR_PRICE_VERIFICATION rather than guessing.

### 5.3 Offline implementation drills; not evidence of actual source learning

| Test ID | Failure injected | Required observed system behavior |
|---|---|---|
| ADD25-S01 | Four rather than five source films | Select proposal BLOCKED; no false five-film report |
| ADD25-S02 | Two candidates are duplicate intervals/near-identical visual coverage | Deduplicate/rank; choose actual diverse candidates or record coverage gap |
| ADD25-S03 | One film has no suitable character sequence | Require witnessed role substitution; no fabricated character |
| ADD25-S04 | Shot boundary misses pre-action context | Selection logic expands/relinks contiguous real frames before finalizing |
| ADD25-S05 | Candidate record has no whole-artwork evidence | Cannot select as high-value based on numerical motion alone |
| ADD25-F01 | Selected frame range 100–123 | Exactly 24 target frames planned; no sampled-frame substitution |
| ADD25-F02 | Frame 110 not supplied as actual image | `FRAME_SEEN` cannot advance for frame 110 even with completed summary |
| ADD25-F03 | VLM omits frame 112 from response | Packet NOT committed as complete; reinspection queued |
| ADD25-F04 | Duplicate image counted as new distinct frame without source index | Reject ambiguous frame identity; preserve actual duplicate source frame when verified |
| ADD25-F05 | VLM answer calls every frame "colourful and dynamic" | Mark weak/question unresolved; do not promote artistic understanding |
| ADD25-F06 | Crop is resized but labeled original native size | Reject false native-detail claim |
| ADD25-F07 | VLM provider accepts only two distinct images | Split to 1–2 target frames plus feasible context; never pretend eight were seen |
| ADD25-F08 | Crash between provider receipt and packet commit | Resume from saved response and exact semantic boundary; no missing/duplicate committed frames |
| ADD25-Q01 | Question = "What is the palette?" with no original-art decision | Request question refinement Q0–Q7 before promotion |
| ADD25-Q02 | Unverified source detail becomes general rule | Reject rule; require contrast/applicability/exception evidence |
| ADD25-Q03 | Stylized actor rule copies source head proportion universally | Reject as source overfit; request cross-actor conditional explanation |
| ADD25-Q04 | Complete source observation but no executable operation | Keep `RESEARCH_ONLY`, no supposedly learned skill |
| ADD25-Q05 | Connected character+environment evidence split into unrelated reports | Preserve joined cluster links and combined art decision dependencies |
| ADD25-P01 | LLM adds a new lighting adjective after frozen skill compilation | CompiledImageJob/Gateway rejects untracked style text |
| ADD25-P02 | Skill lacks required face/limb/contact decision | Compile blocks with precise `MISSING_STYLE_DECISION` ticket |
| ADD25-P03 | Change selected skill decision but compile same prompt/ref/operation | Causal-effect test fails; locate broken skill-to-provider dataflow |
| ADD25-P04 | Change unselected prose note only | Actual image request unchanged; never count as skill improvement |
| ADD25-P05 | Runtime input brief smuggles "use thick outlines and yellow highlights" | Reject style fields in typed content; only skill may supply aesthetics |
| ADD25-P06 | Provider cannot honor all required reference images | Split into legal image-editing route or BLOCKED; don't silently drop them |
| ADD25-R01 | Import from different agent with packet 7 committed and packet 8 pending | Read actual saved semantics, resume at exact packet 8; no rerun from packet 1 |
| ADD25-R02 | Committed source hash differs after moving computer | Refuse resume until original source is correctly rebound |
| ADD25-A01 | Audit ZIP contains source MP4 or provider token | Export test fails and removes sensitive/bulky content |
| ADD25-A02 | Coding agent labels offline synthetic fixture as learned professional art | Audit status fails; must label UNPROVEN |

Automated validation is a **support for the learning method**, not proof of beauty or genuine style comprehension. Real visual evidence, conditional production recipes and original-art outputs establish artistic competence later.

### 5.4 Exact offline audit additions

The first implementation-audit ZIP MUST include real produced (not invented prose-only) traces for these entries, alongside all v1.3 and Addendum 24 items:

```
FIRST15_SELECTION_LOGIC_TRACE.json       # synthetic 5-film candidate fixtures, chosen 3x5, rejected alternatives
FIRST15_SELECTION_CONTRACT.schema.json    # exact selected-candidate fields and roles
EVERY_FRAME_PLAN_AND_LEDGER.json          # synthetic range with all frame IDs, PTS, input hashes, packet plans
PER_FRAME_VISION_CONTRACT.schema.json     # frame, packet, uncertainty, boundary/temporal graph
FRAME_PACKET_CRASH_RESUME_EVIDENCE.json   # interrupted + clean resumed run
QUESTION_REFINEMENT_TRACE.json            # vague -> targeted Q0..Q7 -> witness-backed conditional candidate
CROSS_FILM_STYLE_DECISION_TRACE.json      # synthetic cross-subject/non-overfit evidence and exceptions
STYLE_TO_COMPILED_IMAGE_JOB_TRACE.json     # exact clause IDs/ref hashes/actual payload and bypass failures
ADDENDUM25_TEST_RESULTS.json             # observed pass/fail/blocked test results, not planned outcomes
```

Audit must include corresponding source modules/functions, tests and stdout/stderr logs; traces without executable source consumers do not prove implementation. Synthetic tests must **never** be represented as frames genuinely seen from Kurzgesagt films.

**Required source-level review:** Follow an actual data record through `FrameObservation -> QuestionTrace -> ConditionalVisualDecision -> frozen SkillVersion -> compiled provider request`. Inspect the actual function consuming each intermediate object. Mutation drills should remove one selected decision/reference and show the provider payload truly changes or compilation blocks. Check that only the compiler-gateway path can submit to Runware; user-facing models must not retain a raw prompt bypass. Verify the per-frame expected set equals the verified submitted frame set and verified returned semantic entry set before declaring range complete.

### 5.5 Honest end-state of OFFLINE first run

The only acceptable terminal marker is `STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT`. `PAID_VLM_FRAMES_SEEN` must be zero unless separately and explicitly authorized; `RUNWARE_REAL_IMAGE_GENERATION=0`; `KZ_STYLE_ARTISTIC_MASTERY=UNPROVEN`; `FIRST_15_SEQUENCE_REAL_SELECTION` may be `NOT_RUN` or survey-backed real local selection if permitted, never fictional. If any one ADD25 essential capability is not implemented, report `BLOCKED` with exact module/function and pending work rather than claiming a finished engine.

## 6. Preflight acceptance rationale — why this changes the ACTUAL INPUT, not just adds checks

This addendum teaches the agent **where to look** (whole artwork and coordinated motion in real footage), **which sequences to choose** (nonredundant role-bearing evidence across all five), **what it must actually inspect** (every actual frame in selected windows, then targeted native-detail), **how to ask high-impact questions** (Q0–Q7 anchored to producer decisions), **how to generalize without source copying** (cross-case conditions and exceptions), **how the answer enters the image model** (frozen conditional skill -> exact clauses/references/operators -> compiled job), and **what to change first when the image is weak** (the actual observing/constructing/conditioning operation). The tests are backup evidence that these steps weren't bypassed; they do not replace artistic judgment or source-grounded reasoning.

**No precommitment to style facts:** All illustrated statements in this document are *synthetic exercises*. The only real Kurzgesagt style facts are those later witnessed in the actual five source MP4s. Do not fill missing artistic decisions with invented principles just to achieve schema completion.
