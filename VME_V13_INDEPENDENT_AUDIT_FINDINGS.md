# Visual Mastery Engine — independent code audit

**Source examined:** `VME_V13_IMPLEMENTATION_AUDIT.zip` (SHA256 `7fa6ad8e5ff9a3759801bd6bd7a7505a6c89e17a64036920cbee0829e37d837f`), containing the `visual-mastery-engine/` code, tests, audit records, frame indexes and specifications. All references below are to extracted relative paths. This report assesses the offline implementation; there were no paid vision or image calls and no actual source frames in the ZIP.

## Verdict

**PASS for substantial offline engineering progress; NOT READY for authorized real artistic learning or first original artwork.** The synthetic end-to-end demo is **not** an implemented real-data S0–S9 loop. Keep Remotion + FFmpeg for the first real integrated demonstration; do not integrate REA-Video or migrate to HyperFrames at this stage.

## Evidence actually checked independently

- ZIP integrity and exact SHA256 matched the agent's report.
- Parsed all six compressed frame-index files: **267,896 indexed records; sequential presentation indexes; no observed index gaps**. These are metadata/hashes, not actual visually reviewed frames.
- Reran **52/52** tests in question, decision, compiler and completeness suites; **13/13** gateway tests; and **8/8** selection/sixth tests. Other suites were not completely reproduced in this inspection environment; the archive *reports* 169/169 in the original workspace and 165 passed / four skipped in clean extraction. Do not label the full suite independently reproduced.
- Ran `python -m vme vision run` and `python -m vme art generate`: both unconditionally returned blocked messages. Read source implementing this behavior and all ten loop stage handlers.
- Inspected the real source manifest: **five base sources + one tentative sixth**, all **1280×720**, with base film titles different from the five titles originally named in `01_IMPLEMENTATION_CONTRACT.md`. Source film IDs are hash-tracked but the project's intended reference set must be confirmed *before study*.
- ZIP contains no MP4s or generated image bytes, so no artistic result could be judged.

## P0 — Required corrections before authorizing paid calls

### P0-1. REAL loop is disconnected at the point it matters most

`vme/loop/stages.py:100–111` requires existing `CandidateSequence` records and cannot generate artistic selection rationales from real frames. `stages.py:125–132` unconditionally raises `BLOCKED_CONSENT` in S1 REAL; later S2–S4 use `fixtures.loop_fixtures` (lines 158–239), S5 uses fixture briefs/recording transport (lines 243–271), and S7–S9 are fixture-based (lines 291–385). This is not a matter of missing API keys alone. `vme/cli.py:126–144` and `:176–191` independently hard-block actual vision and actual generation. **Fix:** implement the REAL handlers and CLI drivers using the persistent records, verified provider adapters, non-synthetic artistic observations, and the real selected brief; no synthetic witnesses, questions, answers, decisions, skills, images or approvals may appear in REAL. A clean REAL pre-consent run may stop at authorization, but after valid authorization the real provider call and next stage must exist.

### P0-2. The vision system lacks an actual provider integration and artistic-response conversion

`vme/vision/providers.py:146–188` defines a generic transport-injected shape with `query()` returning `None`. No vision provider was selected or fully integrated. The packet runner and per-frame ledger are technically meaningful; the visual interpretations are **not demonstrated**. `vme/vision/prompt.py` contains a broadly relevant investigation prompt but the concrete artistic depth comes from what the real VLM outputs and what the system does with it. **Fix:** choose a real provider with documented image limits, multi-image/mapping response format, pricing and idempotency/polling behavior; build the authorized adapter, structured response parser, witness extraction, cross-packet temporal state and source-bound follow-up queue; preserve all actual frames and prove receipt/observation counts. Start with a small authorized set, not a massive run. Real source upload requires explicit informed consent.

### P0-3. Observation→skill is a data structure and classifier, not yet a working autonomous learning engine

`vme/style/decisions.py:104–157` accepts a caller-provided proposal. `vme/loop/stages.py:197–209` manufactures that proposal through `fixtures.face_view_proposal_from_answer`; `:222–239` creates skills with `fixtures.build_synthetic_skill`. There is **no real producer that learns the decision branches, reference roles, prompt clauses and executable recipe from actual vision evidence**. `style/decisions.py:92–101` substitutes two nouns in text; this is not a visual transfer demonstration. `vme/style/provenance.py:86–119` uses lexical word overlap (>=0.7) for clause grounding; this can pass an artistically incorrect instruction if its words overlap. **Fix:** build an evidence-to-decision authoring procedure that ingests real frame/crop/temporal witnesses, synthesizes conditional branches and counterexamples, creates source-grounded prompt templates/references, binds real provider operations, records inference versus observation and produces an actual non-synthetic skill. The code must not infer visual correctness merely from lexically similar text. Unsupported fields remain RESEARCH_ONLY; the model must explicitly request further specific visual evidence.

### P0-4. Question/cluster/completeness integration is synthetic

The question engine's stage-aware templates are meaningful and the completeness ledger catches designed negative fixtures. But `vme/loop/stages.py:176–194` feeds synthetic gaps/answers and loops up to three times on the same cluster's first gap. The main REAL loop cannot discover and resolve multiple high-impact unsolved decisions from actual frame output, update the completeness ledger, and revisit source frames. **Fix:** real multi-gap controller: collect source/output defects; group connected gaps; derive a precise question from the earliest causal unknown; consult actual contrasting witnesses; persist an evidence-backed answer and decision effect; recompute all affected gaps; repeat as needed within the same major iteration. The Q0–Q7 dimensions should not become a fixed questionnaire.

### P0-5. Source identity and visual fidelity need correction

The manifest names the base files `A.I. …`, `AI Just Crossed the Terrifying Line`, `GERMANY IS OVER`, `The Most Insane Megaproject…`, `You're More Stressed Than Ever…`. The spec originally names `A.I.`, `How Are Memories Stored…`, `Why Humanity Will Never Leave…`, `How Nuclear Flies…`, `Why Your Brain Blinds…`. The developer report candidly notes the mismatch. All six indexed sources are **720p**. **Fix:** ask user to verify precisely which five files are authoritative and whether they have native 1080p versions; do not silently switch sources, infer role from filename/duration, or discard the already computed indexes unless a source actually changes. Confirm the sixth-film identity and find volcano-start/Earth-logo boundaries through actual observed frames.

### P0-6. Real Runware, character asset creation, and human review are not completed

`vme/providers/runware.py` has a plausible HTTP transport, but the live command in `vme/cli.py:188–190` explicitly refuses; no paid probe was done and no real model capability verified. `vme/artwork/character.py` computes a planning DAG; it does not itself generate consistent whole character variants. `vme/artwork/assets.py` checks layers and masks but production segmentation/clean plates are not provided. `vme/skills/skill.py:133` writes an `ENTRYPOINT.json` referencing **`vme.skills.runtime:execute`**, which does not exist. `vme/review/server.py` documents art/asset verdict endpoints but `do_POST` handles only `/feedback`; `vme/cli.py` has a partial art verdict path but no full asset verdict submission path. `vme/cli.py:213–224` render command checks authorization rather than rendering a real scene. **Fix:** implement the producing operations and real image/asset/review/scene/animation handoffs, making all claims observable with real (user-approved) images. Keep the existing single skill-owned prompt compiler and gateway, rather than rewriting their passing functionality.

## Other important engineering concerns

- The prompt compiler (`vme/compiler/compiler.py`) and gateway (`vme/providers/gateway.py`) are among the strongest parts: pinned skills, deterministic clauses, actual reference bytes, a single gateway and tamper refusal. Keep these controls. They enforce **authorship and content provenance**, not artistic truth.
- The style classifier blanket-flags some ratios and hex colours as source-specific (`vme/style/decisions.py:19,81–82`). Avoid indiscriminately rejecting measurements; grounded conditional proportions, palette relationships and value ranges may be legitimate transferable construction information. Preserve the distinction between arbitrary copied constants and evidenced conditional visual relationships.
- The current sample renderer produces a valid synthetic moving MP4 but has not demonstrated the required professional character acting, stable identity across states, source-trained choreography, audio, original multi-shot continuity or real artwork. These are properly unproven, not verified failures of Remotion itself.
- `vme/state/handoff.py` correctly uses a coherent SQLite backup and hashed manifest; good portability groundwork. Need a real interrupted vision/skill/provider continuation test after the real adapters exist.
- The requirement report's `192 PASS / 37 BLOCKED / 0 NOT_BUILT` is **over-optimistic about REAL functionality**. Reclassify REAL-stage implementations as `NOT_WIRED`/`NOT_IMPLEMENTED` when they are unconditional stops, versus `AWAITING_CONSENT` where a functioning producer exists and simply awaits authorization. Keep synthetic tests as distinct engineering evidence.

## Decision on other toolkits

1. **Remotion + FFmpeg: KEEP as primary now.** It already runs the tested scene-graph scaffold and can place/show layered raster assets. A renderer migration does not repair the missing vision/learning/image-production pipeline. Introduce a renderer-neutral scene and asset contract where feasible, but do not port/render two engines now.
2. **HyperFrames: DO NOT integrate now.** Its free engine and ready-made animation functions may become helpful if genuine motion shortcomings are established in the first real approved animation. No premium template/pro subscription.
3. **REA-Video: DO NOT integrate now.** It primarily produces shot-by-shot production/recreation breakdowns; the project already has frame indexes, source navigation and shot surveys. It does not supply our missing cross-reference artistic knowledge conversion; use it only if a specific missing shot/timing-analysis function is proven later.

## Staged exit criteria (no paid work in repair phase)

**Offline repair acceptance**: all REAL handlers are implemented and covered with deliberately non-synthetic orchestration tests using a *synthetic source but a simulated REAL-compatible provider response*: no `fixtures.*` in REAL branches; no unconditional `raise Blocked` except missing authorization; real non-synthetic records reach skill assembly, compiler and gateway; image requests remain skill-authored; real character asset creation supports the provider and approved state; complete human approval and resume paths exist; source identities are quarantined until confirmed; honest requirement matrix reissued; corrected self-contained evidence ZIP exported.

**After independent audit:** one explicitly authorized tiny vision calibration set on actual source (every frame of a small contiguous segment) → grounded visible questions/answers/skill → one low-cost original-image-model request via the frozen skill → real artwork review. Only scale to the selected 15+1 full-resolution every-frame study after this proves the actual producing chain and budget estimate.

**Do not:** copy prior failed AnimationLab research, silently change source films, buy HyperFrames Pro, introduce REA as a mandatory dependency, replace the renderer now, or mark synthetic fixture evidence as real art learning.
