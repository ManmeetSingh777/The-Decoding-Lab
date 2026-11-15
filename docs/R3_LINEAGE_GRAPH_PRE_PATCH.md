# R3 Step 0 — baseline and function/data lineage graph (written BEFORE any R3 source patch)

## Baseline
* Working dir `G:\The Decoding Lab\visual-mastery-engine`; HEAD `516af70c457f59cf82f01479403dec2ba6d67a9b` (master); only untracked
  `audit_build_v3/` (build output). Recoverable checkpoint branch `r3-baseline-516af70`; work branch `r3-repair`.
* Input `G:\The Decoding Lab\VME_V13_ONE_PASS_END_TO_END_REPAIR_R3.zip` SHA256 `24bc0849fc32b47dc2c6e9b55e43eeddc758304e00cf90c183c6b6ffd238131f`
  (25 entries), extracted to `G:\The Decoding Lab\_r3_input\`.
* Present: Spec v1.3 01–23, Addenda 24–27 (+ `_addenda_25/26`), Addendum 28 (7 files), Addendum 29
  (`G:\The Decoding Lab\29_CHARACTER_ART_DECISIONS_SOURCE_FIRST_ADDENDUM.md`), repair contract R01–R24, audits, six source MP4s in
  `G:\The Decoding Lab\source_clips`.
* **Absent (never on this machine):** "R1–R7.2 provenance", "source-reuse ledger", "166-question governance" as artefacts. The only local
  mention of 166 questions is `05_APPROVED_13_PART_REFERENCE.txt:31`, which *rejects* a 166-question form. They belonged to the earlier
  AnimationLab system that the original launch prompt forbade importing; nothing is invented for them.
* Baseline tests on unmodified live code (logs in `evidence/r3_baseline/`): INDEPENDENT_REDTEAM 0/5 (4 F, 1 E); reference guards 29/29
  (standalone fixtures — they do not exercise vme code); live-boundary 0/5 (4 F, 1 E).

## Lineage graph — intended vs actual (each edge)

| # | Edge (producer → consumer) | Live function(s) | Intended | Actual at baseline | R3 id |
|---|---|---|---|---|---|
| 1 | source file → SourceLock / frame index | `reference/ingest.py:ingest`, `frame_index.py` (ffmpeg framehash, every presented frame) | exact SHA, PTS, raw-frame hash | as intended (720p) | — |
| 2 | source audio → study | `reference/probe.py` counts audio streams only | decoded stream timebase, onsets/silence, meaning when legal | **no audio study anywhere** | F14 |
| 3 | survey → candidate windows → selection | `real.py:_windows/_review_order/_rationale_batch` → `request_json(window_rationale, RATIONALE_SYSTEM)` | P2 protocol text | **bespoke text, no P0/P2** | F06 |
| 4 | selection + 6th lock → S1 intervals | `_s0/_s1` | 15+1 | as intended (R13) | — |
| 5 | frames → packet → provider | `runner.plan_packets/PacketRunner.run` → `prompt.build_vision_request` (P1) → `claude_adapter.submit/request_json` | content-addressed packet id; P1; byte manifest | packet id uses **version label**, not prompt/parser content; committed packets never re-checked | F07 |
| 6 | provider response → frame records | `contracts.validate_packet_response` | generic text = NEEDS_REINSPECTION; structured ids | **vague text VALIDATED**; dict boundary ids **crash** | F01, F02 |
| 7 | adapter receipt | `claude_adapter.submit` sets `images_received = images_sent` | provider-observed only; SENT≠ANSWERED≠GROUNDED | **self-asserted receipt** | F09 |
| 8 | output budget | `max_output_tokens=16000` for 8 targets + ctx | per-target budget, truncation→reinspect | fixed packet size; truncation only NEEDS_REINSPECTION | F18 |
| 9 | frame records → witnesses / phenomena | `_extract_witnesses/_register_phenomena/_native_followups(NATIVE_SYSTEM)` | P5 protocol | **bespoke text** | F06 |
| 10 | witnesses → source-art coverage | `_ledger` (dimension/choice) | per scene/frame/actor/state/relation ledger | **no source-art ledger; only production choice ledger from the brief** | F11 |
| 11 | character evidence | none | source-first character dossier (Add. 29 C0–C10) | **absent** | F11, A29 |
| 12 | gap → one question | `review_visual_model_completeness/choose_controlling_gap → LoopController.step_question` | P3 record: one discriminating question, ≥2 outcomes | deterministic selection, no P3 record | F06 |
| 13 | question → answer | `_s2 → request_json(question_answer, QA_SYSTEM)` | P4 protocol; only sent witnesses citable | **QA_SYSTEM without P0/P4**; `validate_answer` lets the model **self-authorize** ids | F04, F06 |
| 14 | answer → decision write | `apply_answer → writer → author_decision` | central guard: stage, submitted manifest, sufficiency, joint condition, registered op | sufficiency only in `_s2` for STYLE_CONDITIONS; writer callable from **any** stage | F10 |
| 15 | decision → completeness | `coverage._owner_for`, `controller.locate_earliest_missing_handoff` | one branch covers the full condition tuple | **vacuous truth** for unmatched keys; **disjoint branches** count as joint | F03, F05 |
| 16 | decision → references | `authoring._package_references` | explicit per-branch policy; distinct roles | REFERENCE_REQUIRED **defaults false**; one witness `sorted(wids)[0]` per role | F08 |
| 17 | candidate → qualified | `decisions.witness_to_decision` (substitutes=None) | human/native source-art review before any qualification | no review record type | F16 |
| 18 | skill → image payload | `compiler.compile/_select_branch` → `gateway.submit` | unambiguous branch | first-by-priority among equally applicable branches | F05/F08 |
| 19 | actors → canonical/state graph | `_s5/_s7` | per actor identity/canonical/states | **one `n_canonical_character` for all actors**; S8 refuses other ids | F12 |
| 20 | skill → motion/camera/attention/world/audio | `_s8` → `SceneGraph.jsx` | typed source-derived event program | **linear interpolation + WHOLE_STATE_SWAP; no skill governs motion** | F13 |
| 21 | render → gate | `renderer.render_video` | ffprobe/motion/audio fatal | **returns even if ffprobe/motion fail** | F15 |
| 22 | audio → mux | none | approved original sound, mux, sync check | **absent** | F14 |
| 23 | S9 transfer | `_s9` | still vs animated vs AV separated | still only (labels correct) | F17 |
| 24 | stage cache | `_external_inputs` | protocol/prompt/parser hashes in keys | S0–S2 keys lack protocol/system-text hashes | F07 |
| 25 | capsule / cold start | `state/capsule.py` | replay identical hashes | implemented (Phase 3) | — |
