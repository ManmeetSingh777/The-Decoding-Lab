# Addendum 28 — Calibration casebook: how to observe, question and implement (synthetic only)

All situations and frame IDs here are **made up** to train software and agent behavior. They make NO assertion about the six real Kurzgesagt films. The final system must replace these with actual authenticated source witnesses.

## Case 1: Whole-character design under a turn and reach

**Synthetic source sequence:** A fictional lavender-coloured explorer stands in a richly illustrated workshop; over frames `SYN:0200..0248`, the explorer looks right, reaches forward and grasps a machine handle. A different synthetic anthropomorphic creature performs a related gesture with a different head/body shape in `SYN2:0400..0440`.

**BAD investigation:** "The character has a big head, expressive eyes, purple clothes, and good limb animation; it uses fluid easing."

Reasons this fails: it doesn't distinguish where the eyes, head and shoulders change together; it asserts a technique not recoverable from pixels; it universalizes a colour and proportion belonging to one actor; it has no exact source states or production method. It cannot guide a consistent new character.

**First whole-frame operation:** identify the focal character, machine, foreground occluders, world illumination, shot size, actor silhouette at start/peak/contact and what other entities move simultaneously. Cite real frame/image IDs when live. Determine whether the gesture is legible at normal viewing size; do not start with eye coordinates.

**Per-frame temporal operation:** for each real target frame, reconcile `actor_id`, `head_state`, `near/far hand visibility`, `machine_handle_state`, `contact onset`, `world layers` and `camera_vs_actor_motion`. At unchanged frames, point to persistent pose/lighting/contour state. For changing frames, record which *whole-actor silhouette* and internal features change together; compare to adjacent exact frames.

**Native detail operation:** inspect initial and intermediate head views, face occlusion, sleeve–forearm–wrist contours, overlap around handle, consistent costume detail and shadow shapes in native crops with whole-frame parent. Identify where the source is too low resolution for a reliable inference.

**Cross-character contrast:** study a substantially different head/torso morphology in the second source sequence. Ask which shape-design relationship transfers (e.g. a readable arm+prop contact silhouette with deliberate near/far overlap) and which specifics are actor-only (exact pupil size, colour, individual sleeve cut). Do not claim either hypothesis established absent actual differing witnesses.

**Live gap:** Our original scene will show a new many-eyed creature grabbing a ring. The producer has no rule for how near and far hands overlap the ring as the head turns.

**High-impact controlling question:** "For an unfamiliar illustrated actor whose head rotates while one forelimb grasps a circular prop, how do the source witnesses coordinate near/far limb overlap, visible hand/prop boundaries, shoulder support and expression changes so the contact reads as a coherent whole-body gesture? Which frames distinguish a new combined hand–prop drawing state from a simple transformed arm?" 

**Answer shape if evidence resolves it:**
- Observed: cite actual full-frame + temporal + crop + contrasting character witnesses, explicit visible relation changes.
- Inferred mechanism: *candidate* conditional decision, distinguish from alternate explanation. No assertion about hidden source studio process.
- Conditions: actor body design, available appendages, camera/view, grasp geometry, material and focus.
- Chosen implementation: approve original canonical full actor, create a pose family driven by the chosen skill, request an image-guided combined hand+prop contact state with identity and art-finish references, preserve head/view and sleeve relations, produce mask/anchor/clean-world requirements, consume actual output through animation event state. If capability absent, mark precise `MISSING_OPERATOR`.
- Skill-owned clause: must be written from THIS source-supported decision with declared variants, not copied from the synthetic example; runtime only binds new actor/action slots.
- Expected difference: contact visibly legible and identity preserved across related states; using only a rotated whole-head and stretched tubes would visibly fail. No claim of success until original images are generated.

**False shortcut:** write an animated skeleton with hand positioning constraints, then declare artistic acting learned. This may satisfy motion constraints but fails the source-derived *drawing-state and whole silhouette* requirement.

## Case 2: Colour and lighting interacting with world depth

**BAD:** "Blue and orange palette, dark purple backgrounds, bright characters."

**Better investigation question (form only):** "Across a real focal-subject closeup and a different distant world shot, which subject/background colour-value and material-light choices keep the intended focus readable, including when scene illumination or depth changes? What role-level decision, not a copied source hex palette, should a new-scene art skill make?"

**Evidence needed:** entire frame; regions with relative light/dark hierarchy; how form-shadow planes follow surfaces; atmospheric treatment; changed state sequence; contradictory example where the subject is intentionally subdued; different material and world. **Don't claim studio lighting implementation.**

**Production method if supported:** skill owns relative colour and surface-finish construction for specific original subject/environment material and focus roles; provider operation receives real full-frame illustrative examples plus controlled original-content slots; original assets generated with coordinated character/world plan and same lighting-state. If original style relation is ambiguous, record uncertainty and request exact new witnesses. A copied RGB triplet is not the operation.

## Case 3: Complex viewpoint transition involving actual drawing changes

**BAD:** "The camera zooms 2× and layers move with parallax." Could be false even if frames look magnified.

**Needed investigation:** track new details revealed/disappearing; actor geometry at front/profile; world layer occlusion; attention handoff; foreground insertions; focus and cut timing; transition audio if actually available; whether a new drawing state is required. Distinguish observed image differences from a hypothetical 3D camera.

**Producer consequence:** pre-plan original world plate(s), actor drawing/view states, foreground masks and transitions; renderer applies the director-defined event graph with verified asset dependencies. A generic Remotion transform cannot replace an absent redrawn view state.

## Case 4: A complete category grid still hides a hole

All of these individual categories have one decision: `FACE`, `WORLD_LIGHT`, `VIEWPOINT`, `GESTURE`. Yet no decision explains what happens to face shading **during** a head rotation under stable directional lighting. Another missing dependency is `HAND × PROP × BODY SUPPORT` during grasp.

**Required behavior:** Reverse planner enumerates the upcoming original action and produces two precise missing producer decisions, not one broad `ART_SUPPORTED` flag. Active cluster records both. Next controlling question asks for the earliest source relationship causing the most consequential visible defect. After it is answered, the next dependent question is re-ranked. Preserve both entries and their distinct witnesses.

## Case 5: Output review drives a meaningful next iteration

**Original artwork defect:** Nice canonical image, but in the second pose the alien actor's cheek, eyes, sleeve and hand lose identity. The world plate contains a second duplicate actor.

**Do not do:** add more enthusiastic prompt adjectives, make more tests for the character gate, restart source analysis from frame zero, or blame Remotion.

**Root-cause separation:**
- Difference in face/eye/sleeve identity may be missing cross-state source evidence, weak conditional skill, incorrectly selected canonical reference, unsuitable Runware edit method or a provider capability limit. Determine which by inspecting actual compiled requests and image pairs.
- Duplicate actor in world is an asset-plan/segmentation/clean-plate problem, not a style-question problem. Fix producer inputs/scene assembly, not source visual investigation.

**Actual iteration:** persist defects → affected decision/operation IDs → targeted new witness or provider job → new immutable skill/art version (if learning issue) → distinct provider payload bytes → revised images → user art review → then asset/animation review. The output may remain weak; report observed outcome, not invented improvement.

## Case 6: Coding-environment handoff while the next question is unanswered

**Prior environment committed:** 410/470 target frames VLM-verified; 16 frames require native crops; an artistic hypothesis on head-state contours contradicted by another actor; same-category hand-contact and face-occlusion decisions have separate IDs; `QUESTION=Q-0082` is open; provider batch `B-6` was submitted but its remote ID is unknown; frozen skill hash `SKILL-H1` controls compiled example `JOB-J7`; art review rejected pose variant; original video hashes and permission flags locked.

**New environment must do:**
1. Import coherent DB and content-addressed artifacts; verify source/media and protocol hashes.
2. Reopen the last actually relevant full-frame/crops and raw answer; read both competing interpretations.
3. Produce a factual recap: what is OBSERVED, INFERRED, CONTRADICTED, UNKNOWN and why `Q-0082` is still open.
4. Preserve the 410 accepted frame results; resume from the first incomplete operation, not from beginning or a newly generated question unrelated to `Q-0082`.
5. Block billable reissue of `B-6` until actual reconciliation; do not assume same `custom_id` is globally idempotent.
6. Reproduce a frozen synthetic prompt payload and show exact compiled hash; if a different model proposes an alternative artistic rule, retain it as a *separate unverified hypothesis* pending evidence.
7. Carry user rejection of pose variant and all skill/asset dependencies; do not regenerate older approved outputs automatically.

**If new executor cannot inspect full source, cannot use the actual visual model or has lost the reference image bytes:** status `BLOCKED_MISSING_EVIDENCE`/`BLOCKED_MODEL_CAPABILITY`, not a smooth-sounding continuation.

## Calibration: how the system teaches rather than merely checks

Before massive real spend, the learning investigator must be *trained in-session* by a few concrete paired demonstrations like the above: weak superficial answer → why it fails for a producer → corrected evidence operation → conditional creation decision → expected output difference. Use actual source witnesses later to calibrate these behaviors, without treating examples as facts about the six films. The exact prompts are versioned and retained in portable state, so Claude Code and another model consume the same instructions.

The purpose of these examples is to **shape the first observations**, not pretend an offline LLM can be guaranteed to perform professional art critique merely because it passed a JSON-schema checker.
