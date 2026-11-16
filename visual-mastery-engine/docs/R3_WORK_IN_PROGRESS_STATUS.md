# R3 repair — exact work-in-progress status (branch `r3-repair`)

The R3 one-pass repair (prompt verbatim in `docs/R3_PROMPT_VERBATIM.txt`) is **IN PROGRESS, NOT COMPLETE**. No final test runs, no
`VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip` yet. Paused at the user's request to push everything to GitHub.

## Done (committed on `r3-repair`)
* Step 0: baseline logs `evidence/r3_baseline/` (independent red-team 0/5, live-boundary 0/5, reference guards 29/29 standalone),
  lineage graph `docs/R3_LINEAGE_GRAPH_PRE_PATCH.md`; checkpoint branch `r3-baseline-516af70`.
* Merged the seven narrow corrected modules → red-team 5/5 and live-boundary 5/5 pass.

## Implemented in this WIP commit (not yet fully tested)
* F06/F09 `vme/vision/dispatch.py`: single P0+Pn dispatcher, verified byte manifests, adapter requires a manifest, honest receipt.
  All `real.py` source requests (P2 rationale, P4 QA + P3 record, P5 native/reinspection, P2 character dossier) routed through it.
* F07 stale-semantic packet check from the saved manifest (no re-decode).
* F04/F05/F08/F10 central guard in `vme/style/authoring.py:authorize_answer/author_decision` (stage, submitted manifest, wrong source/PTS/crop,
  sufficiency, unregistered op, joint-condition coverage, conflicting branches, explicit reference policy, character-dossier & audio gates).
* `vme/state/authority.py` trusted human authority registry.
* F11 + Addendum 29 `vme/style/source_ledger.py` (character dossier validator, SourceArtObservation ledger, ProductionDecisionCoverage ledger);
  S2 `_character_study`, S4 `SOURCE_ART_LEDGER_OPEN` gate.
* F12 per-actor canonical/state graph (S5/S7/S8), ACTOR_IDENTITY_COLLISION.
* F13 `vme/render/motion_program.py` skill-owned event program + `SceneGraph.jsx` per-segment easing/attention; new motion operators.
* F14 `vme/reference/audio.py` local source-audio study, AUDIO_SIGNAL witnesses, approved original sound, cue track, mux, AV gate.
* F15 render/AV failures fatal; F16/F17 `vme/review/qualification.py`; F18 per-target budget + truncated-packet splitting.

## Exactly where it stopped
Last drill run (`/tmp/drill_run.py`) stopped at S2 `GAP_NOT_CLOSED_BY_EVIDENCE`: the audio-timing decision failed
`INVALID_WITNESS_BUNDLE` (audio witnesses had an unregistered observer and no whole-frame parent). The fix being applied when paused:
1. `vme/investigation/evidence.py`: add `"LOCAL_SIGNAL_ANALYSIS"` to `OBSERVERS`.
2. `vme/loop/real.py:_study_audio`: give each AUDIO_SIGNAL witness `parent_full_frame_witness` (nearest `W-<film10>-<k>-0`).
3. `vme/loop/real.py:_pick_witnesses`: when an AUDIO_SIGNAL witness is picked, also add its parent full-frame witness.
(The patch script for 1–3 failed on a heredoc quoting error; none of 1–3 is applied yet.)

## Remaining R3 steps
Re-run drill to S9; update legacy callers needing `motion_contract` (`vme/loop/stages.py`, `tests/test_gates_render.py`) and tests calling
`request_json` without a manifest (`tests/test_provider_contracts.py` `_ask`) to use `vme.vision.dispatch`; new tests for every F01–F18 and
12 blockers (positive/negative/mutation); two-actor canary; mutation runner; final repo + fresh-extraction suites; build and export
`G:\The Decoding Lab\VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip`; stop with `STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT`.
