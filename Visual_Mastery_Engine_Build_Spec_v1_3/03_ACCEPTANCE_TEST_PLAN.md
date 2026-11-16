# VISUAL MASTERY ENGINE — ACCEPTANCE TEST PLAN v1.2

**v1.2 supersession:** A07/A24/A25 video milestones only run AFTER immutable user artwork and essential asset-pack approvals. Initial artwork learning stops with actual full-resolution stills and `AWAITING_ARTWORK_REVIEW`; it MUST NOT render an integrated MP4 from rejected or unreviewed art. For new style, prompt, character and every-frame tests see A26–A48 below.

This is an implementation checklist for the coding agent and independent auditor. Evidence must consist of real command output, source/asset hashes, rendered visual files and user feedback. A PASS without evidence is a FAIL.

| Test ID | Concrete test action | PASS means | Must be caught if broken |
|---|---|---|---|
| A01 | Fresh repository audit | No previous AnimationLab source/research imported; approved spec is the only prior planning material | Historical CMR/source maps found in runtime inputs |
| A02 | Ingest all 5 source files, ffprobe, SHA256, decode frame per file | Exact source bytes catalogued, decodable video/time, read-only source | Wrong filename identity or corrupted MP4 |
| A03 | Targeted source retrieval at known times + native crops + adjacent sequence | Returned frame witnesses can be opened and source times verified | 1 fps indexes claimed as exhaustive artistic analysis |
| A04 | Provider capability call under approved budget | Real image API returns valid file and cost/provider response; actual edit/reference features tested separately | Mock image or undocumented option treated as real |
| A05 | Payment/consent safety | No paid image requests when max budget absent; no external reference upload without consent | API invoked with undefined cost budget |
| A06 | Scene/asset schema validation | Scene has unique object IDs, layers, temporal events and versioned refs | Duplicate IDs, absent asset, wrong order accepted |
| A07 | Real renderer after approved artwork | Once necessary user art/asset approvals exist, MP4 is ffprobe-verified and actual frame/object motion inspected; before approval, renderer must refuse | Unapproved art silently rendered; static pan over one still treated as rich animation |
| A08 | Multi-gap finder | Several distinct ranked gaps with source and original output witnesses, ranking reasoning and expected improvement | Generic 'needs polish' as sole gap |
| A09 | Cluster selection | Multiple related gaps, explicit dependencies, excluded items, hypotheses and actionable questions | Random categories merged without common cause |
| A10 | Specific observation | Full-frame context + relevant closeups + cross-source examples, distinctions OBSERVED/INFERRED/TESTED, a producing decision | RGB numbers/geometry with no usable production decision |
| A11 | Skill conversion | Real executable code/recipe used by producer with run trace referencing concrete output bytes | SKILL.md only, no producing operation |
| A12 | Causality | Disable method, run changed method same brief, inspect actual intended visual differences | Rule appears in trace but doesn't change artwork |
| A13 | Multi-change attribution | Toggle at least top ambiguous subchanges; keep combinations where interaction matters | 'All changes helped' without tests |
| A14 | Multiple-root diagnosis | Deliberately introduce bad model output, missing layer, invalid animation and wrong art hypothesis; classifier separates causes with evidence | Everything incorrectly blamed on reference analysis |
| A15 | Controlled anchor | Same original brief, provider settings, skill off/on, reported stochastic variability | Comparisons with different subjects/model settings presented as causal proof |
| A16 | Rotating development | Run different original subject with same skill; no per-scene manual rescue | Same original laboratory used all iterations |
| A17 | Blind transfer | Freeze method, generate new challenge after freeze, apply unchanged, record real outputs | Test brief edited retroactively / new skill patched after seeing test |
| A18 | Human review | User sees actual stills, MP4s, ranked gaps and patch diff; feedback saved and reflected in next priority | Skill marked approved before review |
| A19 | Checkpoint/restart | Kill process after partial provider request and restart; no duplicate billed call if idempotency state is available; all valid files verified | Missing artifacts marked complete or duplicated spend |
| A20 | Per-run cost accounting | Returns calls, image counts, costs and unknown costs clearly, never invent costs | Unlogged paid work |
| A21 | Image-to-motion consistency | A beautiful canonical frame and corresponding animated state preserve identity/detail; layer restoration checked | Pretty static art but crude/no moving states |
| A22 | Unsupported capability stop | Unsupported provider edit/transparency/model limits cause named error with evidence | Silent fallback claimed as equivalent quality |
| A23 | User-facing run status | PASS/FAIL/UNTESTED separate for engineering, art, transfer, animation and review | 100% tests reported as visual mastery |
| A24 | Integrated approved iteration | After approved original artwork and asset pack: several specific linked observations, skill changes, comparison stills and actual 12–20s moving MP4, pending video review. Before approval, stop at artwork/asset gate with stills only. | Premature video render; skipped art gate; still falsely claimed integrated motion |
| A25 | End-to-end milestone | Original 20–30s multi-shot visual film produced under frozen skills, reviewed independently and by user | A slideshow/pan used as full motion proof |

## Negative-test examples

- Replace an image-model response with an invalid URL or corrupt bytes: producer must not report successfully generated art.
- Supply duplicate scene `object_id` or layer IDs: validator rejects.
- Change a skill's rule ID but leave actual renderer/provider args unchanged: causality test refuses promotion.
- Render every frame equal except a global camera translation: integrated motion gate detects missing object/secondary activity and does not qualify.
- Swap foreground and background masks: asset/occlusion check detects.
- Make user review missing: run ends `AWAITING_HUMAN_REVIEW`, not `QUALIFIED`.
- Reveal unseen challenge to the skill builder before freeze, or patch recipe afterward: mark test contaminated; generate a new test.
- Kill during semantic evidence commit: resume uses last complete committed state and indicates any incomplete packet.
- Generate improved baseline and intervention with different provider versions: evaluator marks confounded comparison.
- Deliberately give a model vague style-only prompt and capture failure: mark as provider/workflow baseline, not reference investigation accomplishment.

## Review of first user-visible cycle

A first-cycle report must contain readable local paths to:

`reference_examples.html`, `original_baseline_full.png`, `original_improved_full.png`, `original_baseline.mp4` (when comparable), `original_improved.mp4`, `rotating_original_full.png`, `ranked_gaps.json`, `question_graph.json`, `skill_changes.md`, `actual_provider_calls.jsonl`, `causal_test.json`, `diagnostic_report.md`, `costs.json`, `user_review.html`, `CONTINUE_HERE.md`.

If output is unavailable, state which missing dependency prevented it and mark UNTESTED. No invented paths, costs or claims. Core module tests can pass without satisfying artistic outcomes.


## Preserved v1.1 mandatory tests — all should have executable positive and negative cases

| Test ID | Test action | PASS requirement | Must refuse/detect |
|---|---|---|---|
| A26 | Probe 5 actual MP4 frame totals and PTS; stream count every decoded frame | All decoded frame indexes/PTS represented, missing ranges precisely reported; expected original collection ~242,095 frames reverified from source bytes | 1/10 fps sample called all-frame indexing; incorrect frame count; VFR timestamps collapsed |
| A27 | Compare source full-frame index vs frames actually processed by vision | Coverage ledger separates `INDEXED_ONLY`, `SENT_TO_VISION`, `VISION_OUTPUT_VERIFIED` and `NATIVE_DETAIL_REVIEWED` with real source hashes/input IDs | Silent provider subsampling; stale results; low-res contact sheet claimed native detail |
| A28 | All-frame vision estimator and gated segmented execution | Real model limits, total estimated cost, external-source consent and budget enforced before exhaustive VLM execution; resumable contiguous batches | 242k uncontrolled paid calls or unsupported all-frame claim |
| A29 | Corrupt/skipped/VFR/last-frame injected test | Coverage validator rejects false 100% completeness, preserves failed-range status, resumes without double-count | Missing end frame or bad PTS unnoticed |
| A30 | Style mechanism versus source fact | Claims distinguish source-specific artwork from reusable conditional production decisions; each rule names source-specific facts to exclude | One source insect's exact eye geometry promoted as universal style |
| A31 | Cross-subject style question/counterexample | Mechanism includes subject changes, conditional variants and independent source evidence/inferred label | Repeated colour/theme treated as unconditional style law |
| A32 | Originality/abstraction discriminating test | Skill produces distinct viable original subjects while maintaining a demonstrable shared visual language; reference clones rejected | Cosmetic recolour of the source frame reported style transfer |
| A33 | Prompt compiler source-of-truth | Every image-provider prompt style clause traces to skill version; content clauses trace to original brief/scene; provider args trace to capability probe | Claude appends untracked creative style text or improvises production settings |
| A34 | Prompt clause coverage and contradiction | Every required high-impact clause maps to a real prompt span, reference role or linked producing operation; contradictions block | Mandatory detail omitted, promised as later without executable operation |
| A35 | Prompt length, reference count and option validation | Enforces actual API limits, unsupported alpha and image dimensions; no silent drops | 11,000-character prompt to 10k limit, >max references or fake alpha |
| A36 | Skill-to-prompt-to-output causality | Alter high-impact skill while holding original brief and provider stable: meaningful actual request AND intended output behavior change where feasible | Only log/skill text changes; compiled request unchanged |
| A37 | Visual prompt-output review | Review source-grounded art decisions, original brief and real returned image; separately diagnose provider vs prompt vs skill failure | 100% prompt-text coverage called 100% art quality |
| A38 | Character canonical art approval | Captures human verdict tied to exact immutable artwork/brief/model/skill hash and a major-quality image gallery | Blob/tube-limb character silently approved through passing geometry checks |
| A39 | Coherent multi-view/face state | Generated canonical-conditioned views/expressions retain identity and coherent face topology/part relations | Every pose from unrelated text-to-image, drifting eyes/hair/face |
| A40 | Limb/hand/prop/ground relationships | Validate layered drawings against visible whole silhouette, non-stretched attachments, grip/foot contact, clothing and object overlap | Invisible arm stretches; hand crosses mouth; clipping; impossible grip |
| A41 | Layer/mask/clean plate recomposition | Reconstitute separated assets and compare to approved hero image; actual alpha/masks and hidden background coverage checked | White/green matte halo, holes, duplicate body parts, wrong render order |
| A42 | Artwork approval gate | Actual early user verdict `APPROVED/REJECTED` persisted with asset hashes and defects; rejected art cannot render integrated video | Render of rejected art, auto-approval, forged/cached verdict |
| A43 | Asset pack approval gate | Character/art states, layers, poses, hands, face and masks reviewed and approved as versioned pack | Approved still but corrupt poses/masks render anyway |
| A44 | Reapproval after replacement | Changing approved art/pack bytes invalidates downstream approval tokens and all render authorization | Swap in bad art after signoff; render sees stale approval |
| A45 | First 1–2 cycles character emphasis | First visual-cluster report includes real original character canonical artwork and identified top character defects plus skill changes; no unsupported promise of expert quality | Character work deferred entirely into future renderer milestone |
| A46 | Independent multi-failure diagnosis | Identify simultaneous wrong skill inference, vague prompt, model limitation, bad mask, renderer defect with evidence and discriminating checks | Everything called 'needs more frame analysis' |
| A47 | Resume after art approval and edit | Crash and resume retain exact approvals/versions and pending review; provider call idempotency tracked | New session loses refusal state or re-bills accidentally |
| A48 | Updated statuses and report integrity | Every claimed fact separately passes `FRAME_INDEXED`, `VISION_VERIFIED`, `STYLE_ABSTRACTION`, `PROMPT_COMPILED`, `ART_APPROVED`, `CHARACTER_PACK_APPROVED`, `VIDEO_REVIEWED`, `TRANSFER_QUALIFIED` | 100% unit test report used to claim artistic mastery |

---
# v1.2 AUTHORITATIVE prevention-first acceptance additions (A49–A68)

These tests check whether the **production input and actual producing operation** are correct. Checks/gates remain backup safeguards, not substitutes for skill-learnt artwork. The implementation cannot mark these as PASS based on a draft spec or simulated images.

| ID | Constructive execution requirement | Evidence and deliberate counterexample |
|---|---|---|
| A49 | Source-only observation and exact scene facts are separated from conditional transferable style decisions before the skill is written | Feed an insect-specific palette/head/eye description: categorized `SCENE_FACT`, not general style; show a real conditional source-grounded alternative |
| A50 | Question ladder does not stop on adjectives and operates across whole-scene, object, view and required art states for a connected high-impact cluster | Force a 'polished, rich' answer; investigator must ask which source-visible producing decisions explain it and link to exact art outputs |
| A51 | Candidate style decision records include applicability, changes with subject/material/scale/view, invariants, exclusions, creativity freedoms, dependencies, and actual expected output | Changing novel subject changes content fields, not the learnt design grammar; unsupported source claims do not silently become facts |
| A52 | Source-independent design hypothesis and production recipe is created **before** the image provider call | Given an unfamiliar character+world, generate `DesignDecisionPlan` and exact operation sequence; demonstrate no post-hoc styling made up during prompt construction |
| A53 | Entire image-model style instructions are emitted ONLY from skill-owned fixed templates and selected conditional values | Runtime agent tries to insert 'add shiny Pixar-style lighting' with no approved skill revision: the compiled provider request must not change |
| A54 | Every non-style prompt segment has content, character-bible or provider provenance, and required style gaps are blocked upstream | Delete one essential art decision; compilation blocks or a named alternate production operation resolves it; never invents a default 'detailed Kurzgesagt style' |
| A55 | Skills compile **stage-specific** original full-scene, canonical-character, pose-edit, hand-to-prop, world-layer and detail-edit operations | Demonstrate actual different provider calls/conditioning for canonical design vs hand/face view variation, rather than one universal prompt |
| A56 | Original image subjects and style instructions are separated, including style-like language in brief | Injection tries to override learned look through content description; reject conflicting style change or require explicit approved skill change; novel physical subject properties still pass |
| A57 | Visual reference-image slots are chosen by learned skill rules and capability not by guess | An image provider that supports no reference guidance must not receive invented reference params; an identity-preserving edit must use actual canonical bytes or halt/change route |
| A58 | Character is generated first as a coherent canonical **whole illustration**, not from a skeleton or independent tube limbs | Capture first actual full art, face close-up and designed body silhouette; show provenance to character style decision and model request |
| A59 | Build specific required face/pose/hand/contact states from canonical-conditioned art | Change head view and hand grip: show original full drawing, source canonical anchor, prop-based grip drawing, coherent silhouette and correct parts; non-corresponding independent generations fail |
| A60 | Need for layers and alternate drawings is determined by scene's intended movement before art generation | Show `AnimationDemandPlan`; missing occluded visual surfaces trigger planned creation step, not later guessed blob-filled art |
| A61 | Every original source frame was decoded and per-frame VLM study has a separate, truthful coverage status | Index 60fps test clip and supply only 10fps vision: cannot mark remaining frames seen or reviewed |
| A62 | Full-frame VLM pass produces actual frame-ID-specific semantic entries, with individual source image bytes and adjacent context | Mock vision provider returns one summary for 10 frames: packet incomplete and coverage cannot advance |
| A63 | Boundary state preserves ongoing visual actions, object IDs, attentional changes and unanswered art questions across packets | Put a head turn and hand/prop contact across packet boundary; resume packet must preserve state and verify boundary frames |
| A64 | Interruption-safe **semantic** replay across new session, not only filename checkpoint | Kill during response write, during commit, after commit; verify raw response, question state, source SHA, complete records, exact next frame |
| A65 | Paid requests are idempotent or reconciled and full-frame budget is explicit | Kill after provider submit before response. Must find original provider task ID, recover/reconcile without silently resubmitting or claiming zero costs |
| A66 | Two-film-first mode and all-five mode use same accurate coverage process | Full five indexed but two vision-studied: report exact two studied + three incomplete, and never claim five-film full visual learning |
| A67 | User review is attached to actual full-size original artwork and character art *before* layer prep and motion | Deliberately produce bad original face: do not create final video; change upstream character-generation method rather than just bolting on another gate |
| A68 | Executable compiler behavior and production trace are verified | `reference_impl` seven self-tests pass as a minimal illustration; actual app independently demonstrates pinned-skill → real compiled image request → real image → visible art change |

**Implementation acceptance sequence:** (1) data and source identity; (2) semantic frame packets + crash recovery; (3) source-derived style decisions; (4) deterministic style-controlled art plan and real image request; (5) actual original world + character; (6) human artwork review; (7) character states/layers; (8) only then real animation and visual review; (9) transfer. No check count may replace original artistic output.
