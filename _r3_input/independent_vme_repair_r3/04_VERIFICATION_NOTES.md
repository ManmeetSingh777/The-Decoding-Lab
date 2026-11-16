# R3 independent verification record — 2026-11-15

Source original: `VME_V13_COMPREHENSIVE_REPAIR_AUDIT.zip` SHA256
`0e49e93bfc9f2f696fc816957406b46d87f15af58e73467851a8f7fe06ad939c`.

**Observed direct test results on the extracted archived VME copy with the
seven example corrected modules overlaid:**

1. `PYTHONPATH=<extracted repo> python3 INDEPENDENT_REDTEAM.py`:
   5 passed, 0 failures, 0 errors (`0.016s`). Previously established on the
   unmodified uploaded code: 4 failures, 1 error; all five acceptance cases
   failed or crashed.
2. `PYTHONPATH=<extracted repo> python3 -m unittest discover -s
   <R3 package> -p 'test_*.py' -v`: **34 passed** (29 standalone synthetic
   reference contracts + 5 tests against imported patched VME production
   modules), 0 failures, 0 errors (`0.084s`).
3. `python3 -m compileall -q ...`: successful exit 0.

**These are narrowly scoped tests.** The new reference guards are a blueprint
that must still be integrated into actual source/skill/asset production paths;
five live-module tests check protocol constants/cache IDs/technical rendering,
not the whole investigation loop. The code currently in the user's live Windows
checkout was not accessed; the full repo pytest (~38 min) and fresh-extraction
pytest (~38 min) were NOT rerun by this independent process. No original MP4
source images/audio or paid image-model calls were available. Do not claim
real source artistic understanding, qualified skill transfer, multi-actor
professional animation, audio or 15+1 readiness from these local results.

**The remaining work is not open-ended:** the complete mandatory engineering
integration sequence is fixed in `02_EXACT_END_TO_END_IMPLEMENTATION.md` and
the F01–F18 plus prior 12 blockers have explicit failure-mode tests listed in
`03_NO_WAIVER_ACCEPTANCE_MATRIX.md`. Claude must implement all and produce
one final evidence package for independent acceptance, with no downgrade to
reports-only implementation.
