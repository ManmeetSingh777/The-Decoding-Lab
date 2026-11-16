# 12 — Exact launch sequence and what the first Claude Code/Codex session must do

**Do not run an outdated v1.0/v1.1 prompt alongside v1.2.** Use a new clean repo directory for implementation and extract only the v1.2 package, plus the five original MP4 files in a `source_films/` folder (names may vary; verify content using ffprobe and user mapping). Do not include previous AnimationLab evidence, artifacts, style observations or implementation. `05_APPROVED_13_PART_REFERENCE.txt` is a *requirements document*, not research input.

## First message in coding agent

Paste **the complete contents** of `00_PASTE_INTO_CLAUDE_OR_CODEX.md` from THIS v1.2 folder. Do not separately paste old prompts. The coding agent must read the files 01–12, the schemas and reference implementation, run its miniature compiler tests, and write a full requirement→module→test map.

## Build and execution order — no skipping hard dependencies

1. **Fresh environment**. Verify source MP4s, hashes, native frame dimensions/timebases and counts. Check ffmpeg, Python, Node, renderer available; install verified dependencies into project. Do not read old research. Implement DB and disk storage before long VLM work.
2. **Resume infrastructure first**. Build every-frame decoder/PTS index, packet ledger, per-frame semantic records, cost/scope estimator, pause/restart with semantic context, and crash tests. Don't start tens of thousands of expensive calls before the persistent recovery loop works.
3. **Provider trials**. Probe one inexpensive authorized image-model operation for real generation/editing/reference behavior; independently probe a real vision provider's accepted image input limits. Source frame upload to third-party requires separate user authorization. Use actual docs/current model parameters; record version/cost. No fake provider 'success'.
4. **Depth-first source study**. Show projected all-five frame coverage/cost and recommend first two complementary films as an explicit staging choice. If approved, perform a true per-frame VLM pass for chosen films in bounded semantic packets with every frame represented, plus native-detail follow-ups for focal style mechanisms. If budget runs out, stop with honest remaining frame ranges. Do not pretend that all five were viewed simply because indexed.
5. **Initial connected style cluster**. Gather actual world + character + visual-finish + viewpoint/pose witnesses. Ask question chain per 09 to derive conditions/invariants/creative freedoms, not object-specific recipes. Store the exact new style skill with selected rule IDs and producing operations.
6. **Freeze and compile**. Produce an `OriginalBrief` for a new subject unrelated to the five sources, and compile a skill-controlled world/character art production plan. The general LLM has no post-compiler aesthetic wording slot. Print the request with style authority provenance *before* paid image generation.
7. **Create actual artwork**. Under budget consent: generate beautiful original hero character + rich original scene, using canonical reference guidance and the actual skill recipe. Save full native images and actual API calls. The first visual review shows source examples, original outputs, main qualities, what methods caused them, and top remaining defects.
8. **STOP at user artwork review**. Persist exact state; do not automatically animate rejected character/world. On feedback improve upstream style decision, image construction method, prompt template or provider route. This user checkpoint is a meaningful iteration.
9. **After approval**, generate related face, full-body pose, hand/prop contact, multi-view art and necessary layers, keyed to canonical art; stop at user asset-family review. Only then use real Remotion/FFmpeg for controlled moving proof; not SVG-made generic stick figures.
10. **Transfer**. Once method works on one original scene, freeze it and test a different original subject without changing style rules; don't keep optimizing the same image. Report limits. Continue remaining source films with same validated packet architecture.

## Session progress requirement

For each major result save `CONTINUE_HERE.md` as specified in 10. User-visible progress must distinguish: **ENGINE READY**, **FRAMES DECODED**, **FRAMES VLM-SEEN**, **NATIVE-DETAIL INVESTIGATED**, **STYLE SKILL CANDIDATE**, **REAL ORIGINAL ART GENERATED**, **AWAITING ART REVIEW**, **ART APPROVED**, **CHARACTER STATES PROVED**, **ANIMATION PROVED**, **TRANSFER EVIDENCE**. Never replace these with one '100% done' score.

## Budget consent (do not guess account/provider entitlements)

Before paid work, show separate estimates and ask for explicit authorization for: (a) vision provider/model and how many original frames to process, (b) whether original copyrighted source frames may be uploaded to that third-party provider, (c) image generation/edit provider and maximum spend. If any consent missing, fully implement and demonstrate the **offline engineering** and real local frame decoding; mark paid visual results pending, not complete.

## Deliverables at the first human checkpoint

- Repo with actual source reader, DB, semantic packet resume, skill runtime and compiled-image-plan machinery.
- Verified `ffprobe` / hashes and frame-per-film coverage + vision cost estimate; accurate per-frame VLM coverage statuses.
- A source-evidence-ledger with the initial *conditional* connected style decision cluster; separate scene-specific facts and open questions.
- Actual style skill folder with callable producing method and versioned prompt templates/reference roles.
- Full native-size original character and original world illustrations if authorized providers/budget are present, otherwise explicit blocker and compiler trace (do not invent art).
- A gallery for user review explaining actual image quality gaps, what changed in source-derived skills, and next producing fix.
- Verified crash/restart tests, real spend report and exact `CONTINUE_HERE.md` command.

## Non-negotiable honesty

This package precisely specifies the required reasoning and software interfaces; it is **not an already-implemented full engine** and cannot make an unqualified image model magically produce expert illustration. The production method earns trust through real original visual results. Time and cost for hundreds of thousands of frame-level VLM observations must be estimated from actual provider limits, not guessed.
