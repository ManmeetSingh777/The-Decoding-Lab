# Addendum 28 — Implementation crosswalk and decisive evidence drills

This is **not** a substitute for the original v1.3/24–27 tests or Comprehensive Repair R01–R24. It tests the newly specified **input-quality and reasoning process**. Its machine-readable schema validates fields; a competent source/art reviewer must still judge factual and artistic truth. Every synthetic case must be explicitly labeled synthetic; no simulated record counts as the user's original-film study.

## Quality standard crosswalk (failure → first-principles repair → actual consumer)

| ID | Weakness reproduced | Correct behavior at the producing source | Actual consumer |
|---|---|---|---|
| ST28-01 | A packet gets one empty or repeated frame entry | Vision request analyzes exact target image, temporal neighbors, persistent identities and reasoned unchanged state; reinspection when unclear | Frame witness ledger |
| ST28-02 | Full frame labelled "pretty vector art" | Whole-scene relations and specific important observable artwork organization recorded with source hash and region | Active visual problem |
| ST28-03 | Only facial crops studied | Whole-frame first/after, crop linked to original context, actor/world relationship retained | Character style mechanism |
| ST28-04 | Colour listed as fixed palette values | Explain role-specific colour/material/light relationships across unlike conditions; preserve counterexamples | Conditional colour/render skill |
| ST28-05 | Numeric camera shift mistaken for camera move | Record observed pixel changes; retain possible redraw/parallax/object-motion alternatives until evidence discriminates | Layer/state planning |
| ST28-06 | All frames processed but motion relationship forgotten | Persistent event/actor states across packet boundaries; reconcile open/close and simultaneous events | Acting/choreography model |
| ST28-07 | Static question list Q0–Q7 emitted | Derive the one highest-leverage missing producer choice from current gaps; multiple cluster gaps stay queued | Dynamic investigation controller |
| ST28-08 | Quality question has no impact on image request | Source investigate the missing conditional choice or classify as low-impact observation; no artificial "skill" | Skill authoring |
| ST28-09 | One source actor's proportions copied universally | Contrast unlike actor, adapt conditionally or scope to a narrow class, mark unknown | Character skill |
| ST28-10 | Same visual category has multiple important choices | Preserve independent phenomenon IDs, witness sets, conditions, relationships and histories | Skill and provenance graph |
| ST28-11 | All atlas categories "filled" while crucial cross-link missing | Reverse-plan original multi-actor action, discover missing face×view×light/hand×prop etc. | Completeness investigator |
| ST28-12 | Incorrect/unsupported art hypothesis accepted as factual | Separate source fact, inference, competing explanation and novel conditional recipe; request discriminating witness | Evidence→decision builder |
| ST28-13 | Source observation becomes a generic prompt paragraph | Build actual operation with declared conditions, reference image hashes, masks/edits/actor identity inputs and prompt clauses owned by skill | Prompt compiler/provider adapter |
| ST28-14 | Image provider adds significant untraceable visual styling | Report uncontrolled generated appearance as a limitation; do not credit learned skill or invent pixel-level ownership | Original art review |
| ST28-15 | A canonical character generates poor second view or grip | Trace identity/pose dependency back to actual missing evidence or model/edit operator; no generic SVG/tube fallback | Character art operation |
| ST28-16 | Renderer receives no production art state for turn | Stop named missing state or true operation; no generic panning actor substitute | Remotion consumer |
| ST28-17 | After crash, source work restarts from frame zero | Exact committed frame/packet, raw answers, open question, event identity and next action reloaded from coherent store | Vision runner/state |
| ST28-18 | New coding model silently downgrades standard | Protocol version/hash, evidence, fixed witness calibration and actual image input capability checked; flag regression | Cross-environment continuation |
| ST28-19 | New coding model rewrites previously accepted observation | Immutable old record maintained; new interpretation is separately versioned hypothesis with cited contradicting evidence | Knowledge store |
| ST28-20 | Export summary omits visual image refs or approvals | Content hashes + real bytes/rebind paths, source hashes, unknown costs, review/skill versions and dependencies; import stops when missing | Handoff export/import |
| ST28-21 | An actual original output rejected, but stage cache reused | Reopen responsible producer choice, revise skill and invalidate only affected downstream stages; actual new request differs | S0–S9 orchestrator |
| ST28-22 | A supposed full six-film capability learned from only 16 selected intervals | Preserve all-film unfinished frame queue, distinguish selection survey vs selected-frame vision coverage vs artistic competence | Coverage reporting |
| ST28-23 | Synthetic prompts presented as real source observations | Trace `origin=SIMULATED` through raw response, decision, skill and output; never allow into `REAL_SOURCE_QUALIFIED` | Claim/status authority |
| ST28-24 | Live provider mismatch, crash billing or overspend | Retain R01–R07 exact API/budget fixes, strict fakes, uncertain paid request stop and reconciliation | Vision + Runware provider gateway |

## Mandatory demonstration files in the new repair ZIP

- `ART_INVESTIGATION_STANDARD_TRACE.json`: actual protocol version/hash, named multiscale passes, real code paths for every pass, source/target frame packet metadata (synthetic only), one detailed construction-grade observation, counterevidence, actual unresolved relation and next requested evidence.
- `SOURCE_FACT_TO_SKILL_TO_REQUEST.json`: at least two distinct same-category decisions with different witnesses; valid conditional branches; operation graph; exact skill hash; actual reference byte hashes/roles; compiled request structure; no independent artistic text.
- `DYNAMIC_QUESTION_AND_GAP_QUEUE.json`: whole-scene and specific cross-dimension unknowns, multiple queued decisions, one controlling question with explicit effect on producing operator, updated ledger after the answer.
- `PORTABLE_INVESTIGATION_CAPSULE_TEST.json`: after cold import into a new workspace with no prior chat, exact committed packet/target, raw witnesses, open hypothesis/contradiction, active question, pinned skill/compiled payload hash and next operation reproduced; all missing artifacts reported.
- `MODEL_STANDARD_DRIFT_TEST.json`: a deliberately shallow replacement vision response is rejected as insufficient *for the producing choice* even when JSON fields and IDs are present; a substantively different, appropriately supported alternative is retained as a competing hypothesis, not keyword-rejected.
- `CRITICAL_REPAIR_CROSSWALK.json`: all R01–R24 plus ST28-01..24 with actual code symbol, affected path, pre-fix failure, new behavior, runnable regression, status `PASS/BLOCKED/UNPROVEN/FAIL`. No global pass status for missing visual evidence.
- Exact full test logs, changed source, clean install script, hashes and external contract examples; real source files, extracted user movie frames and API secrets excluded.

## No-regression constraints

The additional standard does NOT permit bypassing: strict Runware task UUIDv4 and persistent receipts; valid Anthropic batch IDs; budget reservations/reconciliation; image byte/reference consent; exact sixth sequence locks; human art/asset approvals; the distinction between image and animation transfer; and full source-index integrity. Existing v1.3/Addenda 24–27 and R01–R24 acceptance tests remain operative.

## What the audit can and cannot conclude

A detailed synthetic investigation trace demonstrates that the *software asks, records and routes the right types of operations*; it does not prove an LLM knows the source studio's craft or will interpret the real frames correctly. The next authorized canary should include a small set of real source frames, real inspected answers, original image output and human visual review, under explicit consent/budget. The eventual 15+1 per-frame study is a separate, much larger authorized phase.
