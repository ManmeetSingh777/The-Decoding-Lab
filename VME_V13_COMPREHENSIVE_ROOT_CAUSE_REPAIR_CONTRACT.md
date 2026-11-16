# VME v1.3 — Comprehensive root-cause repair contract

**Source:** Independent inspection of `VME_V13_REAL_PATH_REPAIR_AUDIT.zip` (259 ZIP entries, source at `visual-mastery-engine/vme/`), prior independent audit 2, original v1.3 and Addenda 24–27. Written 2026-11-15. **This is a repair contract for existing code, not a claim that code has already been fixed.**

## 0. Engineering decision and non-negotiable boundaries

Preserve the existing repo, six-film indexes, all previous state, human choices, working compiler, prompt gateway, Remotion renderer and independent reviews. Do NOT restart and do not add REA, HyperFrames, OmniSVG or Rive as new dependencies. Fix the actual S0–S9 real paths; use versioned migrations. **Runware model:** FLUX.2 [klein] 4B, official AIR ID `runware:400@4`, but the user must still confirm they actually have access. The Runware key is a local secret and has **not** been supplied. Implement real readiness without live billing. **No paid or external source-frame calls** during this repair; stop at an independently auditable archive. Avoid inventing API pricing and provider permissions.

There are two proof standards: (i) offline executable correctness of routing, provenance, state, contracts and resume, and (ii) real artistic capability, which *cannot* be proven from mocks. Mark the latter UNPROVEN until authorized real visual evidence and generated artwork. Do not rename simulation as real learning.

A finite prompt cannot guarantee every visual-artistic decision, and `assert`-style gates cannot substitute for a producing method. For each issue below, **repair the producing path**, then run narrow regression tests proving the path. Do not just revise statuses or test fixtures.

## 1. Root-cause map: 24 specific findings

| ID | Severity | Root cause | Exact location / observed defect | Required outcome |
|---|---|---|---|---|
| R01 | P0 | API-contract implementation | `vision/runner.py` constructs ~74-char task IDs; official Claude Batch custom ID length <=64 | Stable unique <=64 ASCII IDs for all tasks, stored before create |
| R02 | P0 | Billing/resume design+implementation | `vision/claude_adapter.py::request_json` submits before persisting remote `batch.id`; crash ambiguity | Durable intent and safe `SUBMISSION_UNCERTAIN` state; no blind resubmit |
| R03 | P0 | Dependency omission | `anthropic` imported in production but absent in `requirements.lock` and install manifest | Pinned SDK + reproducible clean installation and request-schema validation |
| R04 | P0 | Provider API-contract implementation | `providers/gateway.py` uses `uuid.uuid5` as Runware `taskUUID`; official docs require UUID v4 | Generate UUIDv4 **once**, atomically persist with logical job key, reuse only for query/reconcile; reject non-v4 |
| R05 | P0 | Provider response implementation | `gateway.py` raises for URL-only Runware result; assumed base64 response unproven | Explicit `outputType`/`outputFormat`, response parsing for base64/dataURI/URL, controlled authenticated URL fetch, real probe planned for later |
| R06 | P0 | Provider state machine | `gateway.py` treats any unsuccessful getResponse parse as uncertain and lacks explicit processing/error/success handling | Correct documented `getResponse` task states, polling, deadline, durable per-UUID receipt, no blind resend |
| R07 | P0 | Spend accounting design | `AuthorizationRegistry.check` uses `spent` only, no reservations; `gateway._run` commits before `record_spend` | Transactional reserve-before-submit, settle-on-receipt, unknown-cost liabilities and crash recovery. Concurrent jobs cannot overrun cap |
| R08 | P0 | Implementation + evidence model | `style/authoring.py::author_skill` writes `references=[]`, `reference_roles=[]` even with source witnesses | Actual approved full-frame/crop reference bytes/roles/hashes routed to the *compiled* provider payload |
| R09 | P0 | Data-model design | `style/authoring.py::decision_id_for(dims)` keys identity on category tags; unrelated findings collide | Separate phenomenon/production-choice identity from dimension tags; preserve multiple same-category rules with versions and contradictions |
| R10 | P0 | Completeness logic | `loop/real.py::_ledger` tags a dimension supported when one decision exists; relation SUPPORT may have evidence `[]` | Track every required phenomenon/operation/conditional branch and joint relation with actual witness IDs; no category-level shortcut |
| R11 | P0 | Investigation control | `_s2` returns STOPPED for `MISSING_SOURCE`; `_native_followups` takes first three suggestions | Gap-driven, scoped reinspection of relevant actual frames/crops and neighbours; durable new witnesses/questions; budget-gated |
| R12 | P0 | Workflow orchestration | `loop/real.py::run` skips previous COMPLETED stages irrespective of changes in source, skill, approvals or brief | Dependency/hash-based invalidation and new run/iteration version. Rejected artwork propagates questions and triggers real revised outputs |
| R13 | P0 | Required-source enforcement | `_s0` may complete with sixth boundary pending; `_s1` silently omits it | Separate source role lock from volcano→logo boundary lock; initial 15+1 study cannot start/finish unless sixteenth locked |
| R14 | P0 | Real-source identity | Actual base-film names/hashes differ from original specification, files are 720p | Stop for user confirmation, preserve exact hashes, report true source resolution, no substitution or claimed native 1080p |
| R15 | P0 | Artistic generation authority | Answers are text with `CONSTRUCTION_EXPLANATION`; branch text copied verbatim into skill, not proved visually correct | Evidence-backed conditional recipe with explicit visual exemplars, operations and unknowns; mark candidate, never claim mastery from formatting |
| R16 | P0 | Prompt context authority | Compiler supports references but not every generated prompt/identity edit has required skill-backed art and identity inputs | Model request contains exact selected skills, visual references, brief content, only authorized technical fields; missing mandatory input blocks |
| R17 | P0 | Operation/consumer mismatch | `operators.py` lists layer/clean-plate/mask operators, but `_s7` ignores non-CHARACTER_STATE steps and skips expressions | Demand plan must map to executable operator, actual output artifact and downstream consumer or explicit NOT_IMPLEMENTED blocker |
| R18 | P0/P1 | Image-to-scene structural logic | `_s5` creates whole-scene and canonical character separately; `_s8` overlays character on whole scene | Separate clean environment/world plate, canonical actor and action/state assets; prevent actor duplication, coordinate mismatch and stale backgrounds |
| R19 | P0/P1 | Asset preparation | `artwork/raster.py` verifies pixels/alpha but no production segmentation/hidden-surface/clean-plate pipeline; WHOLE_STATE_SWAP fallback | Real view/pose state plans; mark unsupported extraction and occlusion routes honestly; do not pretend output is layered or approved |
| R20 | P1 before animation claim | Animation expressivity | `_s8` builds one actor over one background with default pan/motion and fixed positioning | Renderer consumes actual directed multi-actor/layer/event graph, contact and depth ordering; no generic pan substituted for missing animation |
| R21 | P0 | Skill-version lifecycle | `_s4` rewrites fixed skill folder; old clause files may survive | Immutable content-addressed skill versions; atomically publish current pointer; no stale templates or in-place post-freeze mutations |
| R22 | P0 | Source selection breadth | `_windows` samples a hard maximum of 10 evenly spaced candidates per film; 3 stills/window determine ranking | Survey coverage ledger, event/character diversity, source candidate expansion when necessary; 3 per film after informed review; every selected frame remains required |
| R23 | P0/P1 | Learning outcome / transfer | `_s9` checks one generated whole-scene holdout and may mark transfer workflow complete without video/general acting test | Separate still transfer from animated transfer; frozen skill; original unfamiliar subjects, no target-specific repairs; honestly scoped labels |
| R24 | P0 | Test reliability / audit | Reported 2 failures: AST-overbroad static checker, child process missing `Path` | Correct test implementation **without deleting the protected behavior**, add provider-accurate failure injection and full clean extraction evidence |

**Additionally:** examine risks in `vision/claude_adapter.py::parse_json_text` for truncated/refusal/non-JSON outputs, source/receipt hash checks, `output_config` compatibility with confirmed model, request-image count and token budgeting, and `compiler/brief.py` style-smuggling checks (regex is not a semantic guarantee). Any new concrete issue becomes a row with module, cause, negative reproduction and repair—not silently skipped.

## 2. Exact intended semantics, by subsystem

### A. External provider engineering: no invalid ID or accidental bill

**Anthropic Vision:**

1. Construct a *canonical request descriptor* (`source_sha`, sequence id, pass, exact target/context frame hashes, questions hash, provider/model/version, instruction hash, size, output schema hash). Derive a short stable `custom_id` from a hash of that descriptor, e.g. `vme_` plus 40 hex chars; enforce `^[A-Za-z0-9_-]{1,64}$`. Never derive a new ID simply because the process restarted.
2. Pin a real SDK version and check the actual request serialization in a clean environment. Validate model alias and output params against current official docs or an authorized metadata call; do not rely on cached table alone. Keep model choice user-approved.
3. Persist `request_sha`, short `custom_id`, source consent scope, estimated worst-case charge, authorization version, and `SUBMISSION_ATTEMPTED` *before* calling batches.create. Store remote batch ID atomically when received.
4. If the remote accepted but the local process crashes before saving batch ID, resume to `SUBMISSION_UNCERTAIN`: query/list account batches only if that reliably disambiguates the exact request; otherwise halt for user reconciliation. **Do not infer that reusing custom_id deduplicates across batches.**
5. For a known batch ID, poll it; handle pending/ended/expired/cancelled, per-request result errors, refusal, max-token truncation and malformed JSON. Only mark `VISION_OUTPUT_VERIFIED` when the actual provider response has matching target frame IDs and hashes. Label simulated client results as simulation.
6. Store raw response, verified parse, model identifier, input/output token usage and a unique receipt identity; reserve/settle expenditure once; checkpoint open artistic questions and last frame to resume without lost conclusions.

**Runware:**

1. Confirm model `runware:400@4` as the user's selected model before future paid calls; verify its actual capabilities from official docs: imageInference, `referenceImages` under `inputs`, supported output types, image constraints, up to 4 reference images, and `includeCost`.
2. Make each new logical job choose `uuid.uuid4()` once. Persist that v4 taskUUID and exact request-body hash atomically *before* network submission. On retry/restart, reuse that persisted UUID solely to check/reconcile task status. The request may need manual reconciliation if server acceptance is uncertain; don't assume same UUID avoids duplicate billing.
3. Always use declared `outputType` (`base64Data` for smoke test if supported), `outputFormat` (`PNG`), `includeCost: true`, numberResults=1 and an explicit capability snapshot; do not silently switch model, aspect, style, reference count or image format.
4. Parse normal results *and* errors. Decode `imageBase64Data` or approved dataURI safely; if a URL is returned, fetch promptly over approved HTTPS host only, within size/time limits, verify content type and actual decoded dimensions; don't log or export secrets.
5. Poll `getResponse` or documented task-details endpoint correctly on interrupted requests; distinguish `processing`, `success`, `error`, `not found`, and unknown acceptance. Manual reconciliation when uncertain. Never blind-resubmit after possible acceptance.
6. Maintain a reservation ledger: `(auth_id, logical_job_id, estimated_max_cost, status, actual_cost, provider_receipt)`; before network, reserve within cap in one transactional durable operation; on success settle once, on uncertainty preserve liability, on definitely rejected release. Repeating completed job returns exact saved bytes and receipt without another request.
7. Verify the production model's image editing/reference route with strict offline contract fixtures first. An eventual *authorized* one-image provider probe is a distinct next phase, not part of the current repair; user supplies `RUNWARE_API_KEY` locally only then.

### B. Source selection and deep evidence fidelity

1. Keep the five survey films individually identified by file SHA, title, resolution, frame count and human-confirmed role. Do not silently use 720p clips as 1080p.
2. All fifteen selected contiguous windows plus the sixth opening sequence must have exact boundaries locked before any claim of the **complete** initial 15+1 study. The user must visually confirm volcano start and Earth-logo arrival. Preserve existing evidence, no re-index unless hashes changed.
3. Candidate selection begins from existing shot/event indexes and visual novelty. Evaluate character types, whole-scene artwork, expressions, hands/props, camera/world interactions, cuts, transformations, simultaneous events, palette/material/light, transitions and their *connections*. Expand candidates beyond convenience cap if a needed phenomenon would be missing; retain 3 per base film as initial target and the separate sixth.
4. Every target frame in the sixteen locked sequences must have actual VLM submissions and per-frame verified observation, with exact frame/image hash/PTS and temporal boundary state. Exclude context-only frames from coverage claims. Frame-by-frame paperwork alone must not be called deep artistic understanding.
5. When a high-impact decision remains unknown, re-open the original imagery at the *actual available resolution*, select the most revealing contiguous neighbours and region crops, and investigate the question at the source. Don't stop merely because `MISSING_SOURCE` was classified, and don't cap important follow-ups at an arbitrary three per sequence. Bound cost by authorized budget; pause with exact next input if not enough evidence.
6. Store observation claims **separately** from inferred artistic causes, proposed transferable rules, candidate producing operations and verified output improvements. Each source-witness claim links exact source hash, frames, region if present and visual contents. Never hallucinate source design intent or software.

### C. The knowledge transformation that must actually produce usable art

**Unit of learning = a distinct production choice, not a visual dimension.** Each `ProductionChoice` must contain:

- Stable semantic identity: actual phenomenon and producer decision, not just tags (e.g. `face/three_quarter/eye_occlusion` vs `face/three_quarter/skull_contour` are different).
- Visual target: a concrete whole-image quality and the important visual relationships that create it; avoid adjectives without relationships.
- Evidence: real source witness IDs/images, temporal neighbours, relevant positive and contrasting examples; source hashes and regions.
- Supported observation: what visibly exists; causal hypothesis: what likely creates it; uncertainty and alternatives.
- Conditional rule: subject/view/action/material/light/attention conditions; action to take for a *new* subject; exceptions, dependencies and when not to apply.
- Executable operation: registered provider or local operator, named inputs/outputs, constraints, reference roles, slots and expected visible consequence.
- Prompt segment/reference: exact skill-owned artistic clause or image operation with immutable provenance to choice and witness. New content comes from the typed original brief only.
- State: OBSERVED, INFERRED, METHOD_CANDIDATE, TRIED_ON_ORIGINAL, TRANSFER_SUPPORTED, UNRESOLVED. Do not turn a source description into professional mastery by adding fields.

**Transform algorithm:**

A1. From complete selected footage and individual evidence, build a set of `VisualPhenomenon` records. Each records which visually important distinction is not yet explained, including cross-domain relationships. Multiple independent phenomena may share a category.
A2. Group connected phenomena into one causal cluster for efficient investigation; preserve each identity and open ticket. The completeness investigator examines whole image/sequence and asks which *necessary creative choices* remain unowned by evidence-backed skills. Reopen seemingly supported choices when contradicted.
A3. For each unresolved producer choice, derive one highly specific next question from the **earliest missing causal link**. It must say exactly which frames/views answer it and which construction operation would change under alternative answers. Ask and answer as many questions per *iteration* as needed to close a connected group—not a fixed single question per iteration and not a hardcoded checklist.
A4. Perform source reinspection if the answer is not visually determined. Inferred explanations must remain inferred; they can become candidate trial rules, not verified facts.
A5. Author a **unique** conditional rule and branch. Never merge different observations merely because both have FACE, LIGHT or same condition tags. Merge only explicitly equivalent production-choice identities, retaining contradicting versions and witnesses. No deletion by last-write-wins.
A6. From the rule, compile an **executable** recipe with real operations (whole character, reference edit, world plate, alternate views/expressions/contacts, layer or mask when available). Every recipe node has real code and an output consumer; otherwise block with a named missing operation.
A7. Make the real skill own the **appearance-affecting instructions and visual references**. Package a small set of relevant cropped/full-frame exemplars as locally accessible immutable byte files with licenses/consent metadata, role names, content hashes, applicability and exceptions. Include source image refs only with explicit third-party upload consent. The compiler selects a provider-supported subset (<=4 model refs, counting identity references) based on decision relevance; never silently drop mandatory references.
A8. The deterministic compiler assembles content-only slots plus these skill-owned clauses/references/settings. Image-model requests contain no independent assistant-written style instructions, and no unsupported provider fields. A change to a skill-owned rule or selected image reference must change the compiled request. A style rule that doesn't change anything downstream is not implemented.
A9. After the image model produces artwork, inspect the **actual pixels** and attribute deficits to source observation, causal rule, prompt/reference, model capability, asset/pose conversion or renderer. Fix the responsible method. No new artistic design may be added outside the skill.

**Completeness means** all high-impact, currently relevant `ProductionChoice`s for the original brief have an evidenced method, a producing operator and a downstream consumer *or* are explicitly unresolved (not quietly passed). It does **not** mean a fixed set of categories were each mentioned at least once. Keep supported/unsupported/contradicted states revisable.

### D. Art production and animation-ready assets

1. Derive artwork from the intended actions BEFORE generation: actor design, canonical art, head views, facial expressions, full-body poses, hand–prop contact drawings, separate world plate, occlusion needs, planned camera and layer states. The action plan is an executable demand plan, not merely metadata.
2. Generate an original character and world using skill-owned clauses and references. Avoid layering a second actor over a whole-scene image that already contains that actor. Prefer a verified clean world plate and separate actor artwork; if impossible, stop and explicitly identify missing clean-plate/mask capability.
3. For every required pose/expression/grip state, call a suitable real provider-backed edit or registered local operation, anchor it to the *approved canonical character*, preserve identity and correct anatomy, and output verified bytes. No silent skipping of expression states or unsupported layer operations. A missing route blocks that asset demand rather than generating an inaccurate fallback.
4. Whole-state swap is a legitimately named temporary method; it **does not** imply semantically separated arms, clean plates, IK, hidden surfaces or correct continuity. If a directed motion requires true articulated parts, implement a genuine provider-supported part/mask/clean-plate pipeline or stop with its exact unsupported action. Do not substitute tubes/SVG character art.
5. Every produced asset has: immutable bytes/hash, pixel dimensions, alpha/mask status, coordinate frame/origin, pose/view/expression/contact and prop relationships, identity source hash, art skill hash, foreground/background depth and the exact intended animation consumer. Real compositing must preserve whole approved artwork visually.
6. S6 is mandatory human artwork approval. S7 requires successful actual state/part creation and human asset approval. S8 consumes only approved art/assets with explicit shot-plan actor/world/event/timing fields. Do not invent a default actor at 55% or default pan as if it were learned choreography. An animation route can remain NOT_IMPLEMENTED honestly until actual art quality and assets prove it.
7. S9 distinguishes *still-image transfer* from character/world/acting/animation transfer. A frozen skill used on one unseen still never certifies multi-subject professional audiovisual output.

### E. Versioning, iteration, portable continuation

1. Each event in the learning workflow has input content hashes (sources and selected frames, questions, decisions, skill version, brief, output contract, consent, model), output hashes and parent IDs.
2. The S0–S9 stage cache key must include all relevant upstream IDs. If an upstream fact/decision/skill/brief/asset/approval changes, invalidate *exact dependent* stages and rerun while preserving existing append-only evidence; never blindly skip because a stage was once marked COMPLETED.
3. Human art rejection creates structured defects, keeps the rejected output evidence, opens multiple connected high-impact gap tickets, asks precise questions and rebuilds a **new** skill version. A corrected image request must differ from the previous one in the predicted way; do not recycle old original image or overwrite its receipt.
4. Save checkpoints at each durable external submit, response, source observation packet, question answer, decision publication, skill freeze, image request and human review. On crash or tool/model switch, resume from the first uncommitted, precisely identified operation; uncertain external charges must stop for reconciliation.
5. Keep original comparison anchor, rotating development briefs, and sealed holdouts separate. A held-out brief can only be opened after the relevant skill hash is frozen. Keep different status labels for demonstrated engineering vs visual quality.

## 3. Exact priority and stopping conditions

**During this offline repair:** Finish and individually prove R01–R18 and R21–R24 insofar as they are software mechanisms. R19/R20 contain production-artistic capabilities that cannot be honestly proven without approved real artwork; implement their demand contracts and correct blocks, but do not fake success. Prepare live Runware and Claude vision adapters to exact documented API requests; *don't* provide keys or call them.

**Before any big film-analysis spend:** Require (a) repeatable clean offline build, (b) external-contract strict fakes with UUID4/Batch length/unknown-bill cases and sustained cap reservations, (c) real source-role confirmation + sixth boundary lock, (d) evidence-to-visual-reference-to-compiled-payload chain, (e) proper gap-driven reinspection and reruns, (f) no unresolved false-completeness issue, (g) zero unauthorized network calls.

**After independent audit:** with separately authorized keys/consent and very small caps, first make an actual API capability/vision/image *canary*; inspect the actual returned source observations and an original artwork still. Scale only when quality and cost are empirically acceptable. Without a real API call, network behavior is `OFFLINE_CONTRACT_VALIDATED`, not `LIVE_VERIFIED`.

## 4. Mandatory independent evidence (not test-count theatre)

Build an export `VME_V13_COMPREHENSIVE_REPAIR_AUDIT.zip` containing:

- Entire changed repo, changed-file diff, pinned dependency lock, spec docs or hashes; no source movie bytes, extracted proprietary frames, secret keys or downloaded user art unless specifically allowed.
- `ROOT_CAUSE_MATRIX.json`: each R01–R24, root cause classification (SPEC_LOGIC/IMPLEMENTATION/API_ASSUMPTION/EXTERNAL_UNPROVEN), exact code symbol, pre-fix reproducer, actual change, behavior path, test, status with truthful exceptions.
- `REQUEST_PROVIDER_CONTRACTS/`: real sanitized Anthropic batch payload shape, valid short IDs; Runware payload shape with UUIDv4, outputType, includeCost, reference count, and independent strict rejection fixtures.
- `CRASH_AND_COST/`: accepted-before-batch-ID hard kill; image send-before-receipt hard kill; concurrent spend reservations; no duplicated send or silent unreserved expenditure; manual reconciliation for ambiguity.
- `REAL_EVIDENCE_TO_REQUEST/`: 2 distinct same-category artistic decisions with different input witnesses → 2 retained branches → immutable skill reference files and hashes → provider payload with reference bytes, field ownership and required operations. Alter witness/reference/skill and show causal payload difference; remove reference and show named refusal.
- `DYNAMIC_REINSPECTION/`: an invented-but-clearly-SYNTHETIC significant unexplained artistic phenomenon causing new targeted crop+neighbour requests and one new meaningful question, then changing the operator/skill; source unknowns that cannot be answered remain unresolved.
- `ITERATION_INVALIDATION/`: reject an image, update evidence/decision, freeze new skill, show only necessary stage reruns and a changed image request, never silent reuse of stale outputs.
- `ASSET_MANUFACTURING/`: from a structured directed brief, list exact required original art, character states, mask/occlusion/clean-plate routes and actual execution/missing-route errors; no fake multi-part actor from WHOLE_STATE_SWAP. Show asset consumer and coordinate/alpha contract.
- `FILM_SOURCE_STATUS/`: confirmed/unconfirmed source hash list; true resolution; locked/unlocked sixth frame boundaries; exact first future human action.
- Full pytest, lint, typecheck, JS syntax, spec's reference suites from a *fresh extraction*, plus hashes of outputs. No hiding, deleting or disabling failing tests, and no 0 FAIL claim unless reproduced.
- `WHAT_IS_NOT_YET_PROVEN.md`: exact remaining real vision/image/art-quality/complex-animation limits with named next actions, and clear **NO REAL SPEND** evidence.

**No meta passes:** `STYLE_GENERATION_COMPLETE` requires actual generated output + human approval; `SOURCE_VISUAL_COVERAGE_COMPLETE` requires per-frame real-provider evidence; `PROFESSIONAL_ANIMATION` requires real multi-part/multi-actor motion evidence. A synthetic S0–S9 run is *engineering only*.

## 5. Source-specific provider documentation (recheck when coding)

- Anthropic Message Batches create: https://platform.claude.com/docs/en/api/messages/batches/create (`custom_id` 1–64 `[a-zA-Z0-9_-]`).
- Runware FLUX.2 Klein 4B: https://runware.ai/docs/models/bfl-flux-2-klein-4b (`runware:400@4`, UUID v4, `referenceImages` 1–4, outputType, includeCost).
- Runware Task Polling: https://runware.ai/docs/models-api/task-polling (processing/success/error).
- Runware Task Details: https://runware.ai/docs/models-api/task-details (original request/response for reconciliation).
- Runware account authentication: https://runware.ai/docs/models-api/authentication (secret in local environment only).

