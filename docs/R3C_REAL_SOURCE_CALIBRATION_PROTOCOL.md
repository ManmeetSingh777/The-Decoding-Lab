# Bounded real-source calibration — protocol (prepared, NOT yet executed)

Status: **AWAITING_AUTHORIZED_SOURCE_TRANSFER**. No frame of any reference film has been shown to any model in this repair.

## Two different things, never merged

| Route | What it is | What it can prove | Status label |
|---|---|---|---|
| **A. Direct Claude Code inspection** | The Claude Code session itself views the locally extracted native frames/crops (its own vision), writes typed observations with exact frame ids/PTS, runs the adversarial and contrast checks, and records everything as files. | Whether a capable vision model can produce construction-grade observations of THIS interval under the VME standard; which gates/algorithms fail on real art. | `CLAUDE_CODE_DIRECT_INSPECTION` (never `REAL_VLM`) |
| **B. VME automated API pipeline** | `vme loop run` through `vme.vision.dispatch` → Anthropic Messages/Batches API with the user's own key and spend cap. | That the shipped pipeline itself works end to end on real frames. | `REAL_VLM` |

Route B is **not** run: no API key is configured, no paid-call authorization exists. A Route-A result is never reported as Route-B
evidence, never promotes a skill to `SKILL_TRANSFER_QUALIFIED`, and never replaces human source-art review.

## Interval

Candidates were ranked from LOCAL signals only (`tools/calibration_candidates.py`: shot-cut candidates + local audio envelope;
nobody has looked at the frames). The top candidate is prepared locally (`tools/calibration_prepare.py`):

* film `AI Just Crossed the Terrifying Line - Now What_.mp4` (`584dbc4c…faa8d`), PTS 588.68–598.68 s, frames 35320–35919
  (600 native 1280×720 frames, 1 shot-cut candidate, narration over ~93% of the window, 12 local onsets)
* other candidates: `workspace/calibration/CANDIDATES.json`

The human chooses the interval; the content requirement (detailed illustrated actor, contrasting view/actor, grip or pose change,
world/camera transition, narration over visible action) can only be confirmed by looking.

## Route A procedure (once authorized)

1. **Navigation**: contact sheet (navigation only) → choose the frames to read at native resolution; every frame read is logged with
   frame id + PTS + PNG SHA (`TRANSFER_LOG.json`) — the log is the exact list of source bytes shown to the model.
2. **Whole artwork first**, then entities: silhouette, construction, negative space, value/colour hierarchy, material, lighting,
   depth/camera space, metaphor; per entity every distinct view/state/contact/occlusion (state inventory, C09).
3. **Temporal graph**: onset/anticipation/overlap/hold/redraw vs camera vs world, attention target, link to the local audio onsets
   (narration MEANING stays `AUDIO_MEANING_UNSTUDIED` unless a local transcript backend or a human transcript exists, C06).
4. **Adversarial pass**: re-read native crops and contrasting frames specifically to refute each claim; record refutations.
5. **Recorded through the real gates**: observations are written in the P1 schema and run through `validate_packet_response` +
   `audit_phenomenon_coverage`; decisions through `author_decision`; skill → `StyleProgramCompiler` image payloads (NOT sent) and
   `compile_event_program` animation programs (rendered locally only with ORIGINAL placeholder assets, never source art).
6. **Ablations**: remove/alter each skill clause / motion parameter and record the exact payload/track change or block.
7. **Gap report**: every gate failure on real art → root cause in the general method → algorithm change → regression test
   (never a per-scene patch).

## Authorizations required (and nothing else)

* **Source transfer (Route A)**: explicit approval that this Claude Code session may view the native frames of ONE named interval
  (film + PTS range). Viewing sends those images to Anthropic as part of this conversation.
* **Route B / paid**: provider, model, interval, spending ceiling, `vme authorize` with the confirm phrase — not requested now.
* **Paid artwork** (Runware): not requested now.
