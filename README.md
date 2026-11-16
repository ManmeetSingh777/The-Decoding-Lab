# The Decoding Lab — Visual Mastery Engine (VME v1.3)

Everything from `G:\The Decoding Lab`: the specification, every addendum and repair package, every audit ZIP, and the engine
(`visual-mastery-engine/`).

## Current state (read this first)
* **Engine branch on disk:** `r3-repair`. The R3 one-pass repair is **in progress, not complete**.
  * Exact status and resume point: `visual-mastery-engine/docs/R3_WORK_IN_PROGRESS_STATUS.md`.
  * The last prompt, verbatim: `visual-mastery-engine/docs/R3_PROMPT_VERBATIM.txt`.
* **Last finished deliverable:** `VME_V13_COMPREHENSIVE_REPAIR_AUDIT.zip` (Phase 3: R01–R24 + Addendum 28).
  * SHA256 `0e49e93bfc9f2f696fc816957406b46d87f15af58e73467851a8f7fe06ad939c`.
  * Results: repo 227/227 tests passed; fresh extraction 225 passed with 2 expected skips.
* **R3 input package:** `VME_V13_ONE_PASS_END_TO_END_REPAIR_R3.zip`, extracted in `_r3_input/`.
* **No paid API call, source upload or real 15+1 investigation has been done.**
* **Decisions still waiting on the user:**
  * confirm the five base films;
  * lock the sixth clip's boundaries;
  * authorize the paid canary and source-reference upload.

## Engine git history
The engine's full commit history is on these branches of this remote:
* `vme/master`
* `vme/r3-repair` — current work
* `vme/r3-baseline-516af70`

The `main` branch holds the whole folder as a single snapshot.

## Not included
* **Source films:** not included. See `SOURCE_FILMS_NOT_INCLUDED.md` for their SHA256s.
* **Decoded source frames:** not included.
* **Environments and caches:** `.venv`, `node_modules`, caches and the rebuildable `audit_build*` folders.

To recreate the environment:
* Python: `pip install -r visual-mastery-engine/requirements.lock`
* Remotion: `npm ci` in `visual-mastery-engine/render/remotion`
