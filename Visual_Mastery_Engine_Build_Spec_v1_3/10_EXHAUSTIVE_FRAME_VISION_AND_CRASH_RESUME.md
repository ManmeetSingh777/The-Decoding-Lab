# 10 — Every-frame semantic study, bounded execution, and exact durable resumption (v1.2, AUTHORITATIVE)

Status: software to implement, NOT frame analysis already performed. This is a **clean implementation of a proven architectural idea**: durable frame packets + semantic checkpoints. Import *no* historical source findings, datasets, reports, code or style hypotheses into this new project's learning record.

## 1. Frame requirements, three very different claims

- `FRAME_DECODED`: each original displayed frame decoded in presentation order with its true frame index, PTS/timebase, dimensions, source SHA and retrieval route. This is necessary, cheap, **not artistic vision**.
- `FRAME_SEEN_BY_VISION`: that **specific actual frame image** was provided to the chosen vision model, the request/response has been verified, and the model returned a valid record for **that exact frame**. For unchanged frames the record may say 'same as preceding state', but ONLY if the model actually received and inspected the frame. Sending a sampled 10/12fps video, estimated interpolated observations, motion tracking, or a single contact sheet is not this status.
- `FRAME_ARTISTICALLY_EXAMINED`: for each frame, a vision output describing relevant visible elements/changes and its relationship to adjacent frames exists, with neighboring context and recorded limitations. A pass at low resolution can miss native small detail: it must never claim **complete native-detail understanding** without targeted native-resolution examination. An agent may not honestly certify perfect artistic knowledge of any frame simply because it processed it.

The user requests actual frame-by-frame artistic visual study. The software must support completing a **non-sampled per-frame VLM pass**, in addition to every-frame decoding. It shall not silently replace the user's requirement with sparse keyframes, optical flow, tracking, or periodic contact sheets. Those are secondary aids only. FULL FIVE-FILM VISION COMPLETION may take significant calls, time and cost; do not claim it until done.

## 2. Rollout stage choice

Start by probing all five original videos, indexing every frame, and estimating input tokens/images and cost for the intended VLM provider. Default investigation budget **first two complementary films**, selected by observable subject diversity and user input, with whole-frame vision completed frame by frame on these two before claiming their source-vision coverage. Continue the other three as budget/authorization allows. Every frame of all five remains on the global queue, with exact coverage status. The first image-proof iteration may proceed from a truthfully labeled partial source set if the user authorizes this sequence; it must not be called full five-film mastery. Never promise full paid vision processing at an unapproved cost.

## 3. Bounded per-frame vision packets

Process in consecutive **small packets** set from actual provider limits (start with candidate **8–12 distinct source frames** per request if supported; dynamically reduce rather than hide omissions). For each packet:

1. Load actual decoded frame images (not approximations) plus **up to 2 overlapping boundary frames** from previous packet for semantic continuity. Use index/PTS/source hash in each frame's manifest; preserve actual bytes and image-to-request ordering. Avoid low-resolution collages if they sacrifice artistic features; dedicated image inputs are preferred when provider allows.
2. Provide the model *a specific scoped task*: describe source-visible objects and visual states, transitions/change from adjacent frames, active attention/composition, meaningful drawing/lighting/pose changes, interacting objects, and relevant unknowns; investigate the packet's active high-impact question to greater detail. **Do not attempt to describe arbitrary microscopic geometry** on every nearly unchanged frame.
3. Require a machine-readable `FrameSemanticEntry` for **each non-overlap frame ID** in the request (also possible `UNCHANGED_RELATIVE_TO_FRAME` with explicit visible-content comparison and current style/identity continuity). Entries may point to shared `PacketSemanticState`, but cannot omit frame-specific evidence and changes. Record per-frame uncertainty and relevant regions needing native enlargement.
4. Maintain across-packet `SemanticBoundaryState` containing current scene/world, active objects and identities, artistic treatments, drawing states, positions/relations, visible actions, focal/attention changes, hypotheses, source questions, and open temporal events. Include a preview of boundary frames in the next packet. Explicitly reconcile an object/action that crosses packet boundaries.
5. For source changes, interactions, expression/limb shifts, scale/perspective transformations and art-design details central to the current question: reopen the **native-resolution original frames and adjoining frames**, produce specific crops and independent scene-level synthesis. This is a deeper *additional pass*, not a substitute for the per-frame pass.
6. Verify source frame IDs in response against manifest (no duplicates, no missing entries, no silent subsampling, no hallucinated PTS). `SENT` is not `SEEN`; mark `VERIFIED` only after checking the returned frame-specific records. If the provider cannot reliably accept/evaluate all supplied images, reduce batch size, change provider/mode, or mark `UNSUPPORTED` and stop the claim.
7. Store raw input frame manifest, exact request and response, frame records, packet summary, changed-entity graph, cost/request ID, and unresolved evidence tickets; only then commit the packet and advance.

Model summaries are hypotheses and observations. They do NOT by themselves provide style-producing knowledge. High-impact style questions still run the method in `09_STYLE_OBSERVATION_TO_PRODUCTION_ALGORITHM.md` against original creative subjects.

## 4. Hard resumability: never restart already committed source analysis

**Packet identity** = `SHA256(original MP4) + decoded start frame + decoded end frame + frame manifest SHA + analysis pass ID + active question-cluster ID + model/version + prompt/version + source transform/resolution version`.

Each packet uses explicit state transitions:
`PLANNED → INPUTS_READY → REQUEST_IN_FLIGHT → RESULT_RECEIVED → VALIDATED → SEMANTIC_COMMITTED`, or `QUARANTINED / RETRY_WAIT / BLOCKED_CONSENT / UNKNOWN_BILLING`.

Store records in SQLite WAL or equivalent durable transactional store. For each packet:
- Set `REQUEST_IN_FLIGHT` and provider task/idempotency ID in a transaction **before** submitting a paid request.
- When response arrives, write raw output and each `FrameSemanticEntry` to temporary files, flush and atomically rename; fsync when supported; then commit the status and SHA manifest in one database transaction. Do not advance watermark before all semantic outputs are durable.
- `SEMANTIC_COMMITTED` packet must include **semantic** content (not just 8 frames with labels), current artistic decision investigation, considered/discarded hypotheses, unknowns, and next specific question. Important source inference is preserved as readable structured records, not model-hidden thoughts.
- When interrupted or timed out, reopen the ledger, verify committed file hashes and source identities; skip valid committed packets; quarantine partial/contradictory packets; resolve unfinished provider tasks by polling with their stored IDs, if supported; **never blindly reissue a potentially billed call**. Record `UNKNOWN_BILLING` and require reconciliation if outcome cannot be determined.
- Reinspect boundary frames around the last complete packet after resuming; DO NOT restart from frame zero. Recreate the new model context from committed packet summaries, current style questions, decisions, evidence IDs and the last boundary state. Hidden chain-of-thought cannot be transferred across model sessions, but the *substantive verified investigation state* can be.
- Resume by **source+packet+question-pass**, not just timestamp; processing the same frames for a different new high-impact question is allowed with its own `analysis_pass_id` and no overwrite of previous findings.
- A corrupt packet or retry cannot silently erase other versioned observations. Raw input, unresolved claims, source exceptions and previous failures are immutable or append-only.

## 5. What to save at every semantic checkpoint

```
frames/<film_sha>/index.jsonl                 # exact per-frame decoded index + PTS
frames/<film_sha>/packets.sqlite              # packet states + provider ids + costs
vision/<pass_id>/<packet_id>/input.json       # frame-by-frame image & timestamp evidence
vision/<pass_id>/<packet_id>/response.json    # exact vision response, no editing
vision/<pass_id>/<packet_id>/frames.jsonl     # 1 source frame record per target frame
vision/<pass_id>/<packet_id>/boundary.json    # active objects/actions and adjacent state
investigation/current_questions.json         # highest-impact unresolved visual causes
investigation/style_candidates.jsonl         # evidence-linked conditional mechanisms
investigation/unknowns.jsonl                 # deliberate unanswered questions
investigation/decisions.jsonl                # what changed and why, non-secret
art/skill_versions.json                       # current skill→prompt artifact versions
runs/current_state.json                       # pending stage, spend, review, file hashes
CONTINUE_HERE.md                              # one-screen cold-start reconstruction
```

`CONTINUE_HERE.md` must specify: last semantic-committed packet ID and exact `next_frame_index`, film SHA, current scene/world and active artistic event, source evidence already examined, leading hypotheses and contrary evidence, unresolved questions, last source crops that should be reopened, current skill version, last provider task status, spending/permissions, pending human review, **one exact next command**. Reading this plus the structured records must restore the task without copying old chats.

## 6. Interruptions we must simulate before large paid runs

- Kill between request submit and response; restart and query status rather than duplicate bill.
- Kill after raw response write but before semantic commit; validate raw response and safely complete packet without charging again.
- Kill after semantic commit but before next packet; resume from exact next committed boundary.
- Restart with changed model or investigation question; keep old pass intact and re-run only explicitly requested new pass.
- Deliberately omit a source frame / mismatch PTS / repeat duplicate frame ID / provider silently resamples one in ten; refuse any 100%-vision claim.
- Resume in a **new Claude Code session or account** with no chat context; verify semantic continuity across a shot boundary using stored state and adjoining source frames.
- Force vision timeout and corrupt JSON: retry only the affected packet, record errors and unknowns, preserve completed work.

## 7. Realistic limits and terminology

Five known source MP4s in earlier verified file set were about 242,095 frames, but **reprobe the actual user's five file bytes** at launch; content may differ. Even with 8–12 frames per vision request, this can be tens of thousands of calls. Native 1080p crops and repeated artistic reviews add cost. Avoid claiming this is a brief setup step or offering a made-up price. First output a real estimate from the chosen provider, and get authorization. The user can choose two-films-first or all-five-full processing after seeing real cost. No automatic substitution of 10fps sampling, and no quiet declaration that 'frame indexed' means understood.

The video learning goal is transferable **style and production capability**. Frame-by-frame records are a source evidence reservoir; excellent style mechanisms still require cross-subject conditional reasoning and actual better original outputs. Completing every frame is valuable but not automatically equal to learning Kurzgesagt artwork.
