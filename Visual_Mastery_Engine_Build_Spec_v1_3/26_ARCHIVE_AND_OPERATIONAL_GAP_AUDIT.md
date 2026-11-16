# VME archive preservation and operating-loop audit (2026-11-15)

## Inspected actual local artifacts

1. `/mnt/data/Visual_Mastery_Engine_Full_Build_Spec.zip` and its extracted `Visual_Mastery_Engine_Build_Spec/`.
2. `/mnt/data/Visual_Mastery_Engine_v1_1_REVISED_FULL_BUILD_SPEC.zip` and extracted `..._v1_1/`.
3. `/mnt/data/Visual_Mastery_Engine_v1_2_PREVENTION_FIRST_FULL_BUILD_SPEC.zip` and extracted `..._v1_2/`.
4. `/mnt/data/Visual_Mastery_Engine_v1_3_COMPLETE_PREBUILD_AUDIT_SPEC.zip` and extracted `..._v1_3/`.
5. `/mnt/data/VME_v13_Addendum/24_CHARACTER_STYLE_DISCOVERY_AND_PORTABLE_CONTINUITY_ADDENDUM.md`.
6. `/mnt/data/VME_v13_Addendum_25/25_FIFTEEN_SEQUENCE_DEEP_VISION_AND_QUESTION_ENGINE_ADDENDUM.md` and previous combined first-message text.

## Preservation result

**No substantive predecessor specification was accidentally dropped from v1.3.** This is a comparison of source documents and acceptance obligations, **not** an implementation audit of the software which Claude/Codex will later write.

- Original 13-part user-approved reference `05_APPROVED_13_PART_REFERENCE.txt` is byte-for-byte identical across v1.0, v1.1, v1.2 and v1.3. SHA256: `a2291652234d0c47…`.
- v1.2 → v1.3: files `01_IMPLEMENTATION_CONTRACT.md`, `02_DATA_SCHEMAS.json`, `03_ACCEPTANCE_TEST_PLAN.md`, `04_USER_REVIEW_PACKET.md`, `05_APPROVED_13_PART_REFERENCE.txt`, `06_BUILD_AUDIT_MAP.md`, `07_STYLE_FRAME_PROMPT_CHARACTER_GATES.md`, `08_PROMPT_PIPELINE_EXAMPLE.md`, `09_STYLE_OBSERVATION_TO_PRODUCTION_ALGORITHM.md`, `10_EXHAUSTIVE_FRAME_VISION_AND_CRASH_RESUME.md`, `11_CONCRETE_SKILL_CONTROLLED_IMAGE_PRODUCTION.md`, `12_EXACT_LAUNCH_AND_PROGRESS_CONTRACT.md` are byte-for-byte identical.
- All 68 named A-series acceptance requirements remain in v1.3. New v1.3 B-series requirements supplement them.
- v1.1 explicitly changed the earlier 'always render MP4 per iteration' rule into **artwork approval → animation-ready asset approval → full MP4**. That is an intentional change, not a lost feature.
- v1.3 intentionally supersedes the v1.2 launch prompt with **offline build + independent audit first**. The old v1.2 launch prompt remains in the v1.3 package as a clearly labeled NOT-TO-PASTE historical reference. Use only the newly generated complete launch prompt in Addendum 26.
- The v1.3 original files **do not include Addenda 24 or 25**. Keep those as three separate addendum markdown files together in the v1.3 spec folder. This new addendum 26 is also separate.

**Practical consequence:** In your new coding project, delete the older Full Build Spec, v1.1 and v1.2 packages. Keep the full v1.3 package and Addenda 24, 25 and 26. Do not include multiple old launch prompts in the coding-agent chat.

## Gaps found in current 1.3 + 24 + 25 behavior (before new addendum)

| Actual risk | Existing instruction | Remaining gap | Addendum 26 correction |
|---|---|---|---|
| Repeated questionnaire disguised as intelligent investigation | Addendum 25 Q0–Q7 asks effect, cause, contrast, conditions, operations, tests | Could literally run fixed prompts on every shot and never derive the **next** appropriate question from a newly observed output | `ActiveArtProblem` + earliest unfilled producer decision + ONE discriminating question + concrete answer consequences |
| Research proceeds when real failure is code/provider | v1.3 failure categories and prompt authority | No single unambiguous rule about which failure stage owns next question | Route by earliest failing handoff; compiler failures go to engineering, source gaps to research, image-model shortcomings to manufacturing/provider |
| Multiple connected quality gaps collapse to disconnected observations | v1.3 clusters; Addendum 25 questions | Can record linked qualities but not clearly preserve one moving dependency across questions, skills, images and review | Persist interconnected relations and active question/decision/operation linkage across loop S0–S9 |
| Sixth creative reference opening is missing | Original project locks to 5 films; Addendum 25 selects 15 = 3×5 | No sixth-clip locator, no extra per-frame sequence, tempting to invent start/end time | 15 + **one separately locked source-6 volcano→Earth-logo interval**, visually located from actual frames |
| 'Every frame observed' overstated | Full-frame VLM requirement from v1.2 and Addendum 25 | Per-frame index/receipt may be falsely conflated with genuine whole-art understanding | Separate decoded, VLM seen, artistically explained; combine complete-frame, consecutive-time and native-detail evidence |
| Question output not tied to production change | Addendum 25 Q procedures and style decision records | A model could answer detailed artistic questions without changing a real image operation | Require missing producer decision + exact skill clause/ref/operator + predicted visible difference for every completed answer |
| Original-art review does not change question selection | v1.3 review/feedback and skill revision | A new original image's largest difference might not update the active research question | Restart question derivation from latest output gap and earliest failing production stage, not reuse prior question |
| Continuation loses the precise next artistically meaningful operation | Addendum 24 state checkpoint and v1.2 journal | Checkpoint can save last question text but omit why it is blocking image construction | Persist active problem, selected witness state, decision/skill versions, provider pending IDs and exact next evidence/operation before switching tools |

These are *genuine operational ambiguities*, not a claim that v1.3 lacks the whole pipeline. Addendum 26 is the narrow correction rather than a redesigned engine.

## Sixth-clip access status in the auditing environment

Only the original **five** complete Kurzgesagt MP4s were available in this local runtime at `kz_five/`; **the newly mentioned six-minute sixth source was not locally present**. Its name, exact volcano opening frame and Earth-logo endpoint **cannot be verified here**. The coding agent must locate the user-supplied sixth file in its own `source_films/` folder, identify event boundaries visually, or honestly record `SIXTH_SOURCE_NOT_AVAILABLE`. No guessed timestamps.

## What can actually be certified before artistic runs

The first offline build must prove real code for survey, exact frame/PTS capture, vision-ledger semantics, dynamic questions from active gaps, conditional style decisions, executable skill-to-image job coupling, character and raster assets, review state, animation fixture, persistence/resume, and evidence export. It cannot certify high-end Kurzgesagt appearance, source understanding, or image-model artistic quality while cloud vision/image calls remain unauthorized.
