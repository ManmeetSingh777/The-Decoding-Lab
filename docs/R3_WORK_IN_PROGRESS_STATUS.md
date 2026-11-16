# R3 repair — status (branch `r3-repair`, GitHub `vme/r3-repair`)

The R3 one-pass repair (prompt verbatim in `docs/R3_PROMPT_VERBATIM.txt`) is **IMPLEMENTED AND OFFLINE-VERIFIED**, and is
**STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT**. The full 15+1 reference investigation must NOT start until the independent audit
approves this implementation.

## Evidence package
`G:\The Decoding Lab\VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip`, built by `python -m vme.audit.r3_audit` from a CLEAN committed HEAD
(the builder refuses a dirty tree). It contains IMPLEMENTATION_MAP, DELTA.patch (vs pre-R3 `516af70`), red-team / reference-guard /
live-boundary logs BEFORE (pre-patch) and AFTER (final), REAL_REQUEST_CAPTURE_INDEX, the two SEPARATE coverage ledgers,
CONDITIONED_SKILL_CAUSALITY, CHARACTER_AND_MULTIACTOR_TEST/, MOTION_CAMERA_AV_TEST/, MUTATION_RESULTS, full repo + fresh-extraction
suite results, TESTS_FINAL_COMMIT.txt, CAPABILITY_VERDICT.md, GAPS_AND_UNRESOLVED.md and a SHA256 manifest.

## What was done after the WIP checkpoint `17030e3`
* S2 blocker fixed without weakening validation: `LOCAL_SIGNAL_ANALYSIS` observer is valid ONLY for `AUDIO_SIGNAL`; every audio onset
  witness is bound to a same-film full-frame parent within ±1 frame (`AUDIO_WITHOUT_FULL_FRAME_CONTEXT`, `AUDIO_PARENT_MISALIGNED`);
  `_pick_witnesses` and the S2 send-set carry the parents; unlinked onsets are recorded, never cited.
* Legacy callers/tests migrated to `vme.vision.dispatch` manifests, the motion contract, typed frame facts and explicit reference policy.
* `tests/test_r3_contract.py`: positive + negative (exact root-cause code) tests for F01–F18.
* Two-actor canary (`vme/testing/drill.py:two_actor_brief`, `tests/test_r3_canary.py`): keeper + moth, distinct canonical jobs
  (compiler `actor_scope`: decisions owned only by the other actor are excluded; shared ones stay required; the gateway recompile keeps
  the scope), per-actor states bound to their own canonical, hand/prop contact, overlapping events, skill-owned ACTOR_ACTING ×2 /
  DRAWING_STATE ×2 / CAMERA / ATTENTION / WORLD / AUDIO tracks, AV gate, capture index, ablations, counterfactuals, held-out still
  transfer, fresh-directory capsule restore replaying both actors' jobs.
* Motion ownership: several decisions owning one track must AGREE (`co_owner_decision_ids`), otherwise `CONFLICTING_MOTION_OWNERS`.
* `vme/audit/mutation.py`: 28 guard mutants run in a throwaway copy; each must be KILLED by its targeted tests.

## Not done / not provable offline (see GAPS_AND_UNRESOLVED.md in the ZIP)
Real source perception, source-art truth review, qualified skills, real images, professional animation, audio meaning and a held-out
animated AV film all remain OPEN. Required user resources: the actual 15+1 files, exact sixth boundaries, paid-call approval with a cap,
per-film source-upload consent, Runware model confirmation by probe.
