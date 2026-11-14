# Visual Mastery Engine (VME) — v1.3 + Addenda 24–27, OFFLINE ENGINEERING BUILD

**State: `STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT`.** This build implements and tests the offline engineering of the
specified system. It has made **zero** paid vision calls, **zero** Runware calls and **zero** source-frame uploads. It contains
**no learned Kurzgesagt style**: every style record, clause and reference image shipped here is a labelled SYNTHETIC fixture.

## What is real here
- Exact SHA256 identity, ffprobe facts and a full **decode of every presented frame** (true PTS, per-frame content hash) of the
  user's six local MP4s (`vme sources ingest --index-every-frame`), plus a navigation-only scene survey and a local, no-upload
  sixth-clip boundary candidate packet for human review.
- A transactional per-frame vision packet ledger with crash/resume and billing reconciliation (mock provider; real adapter gated).
- `ActiveArtProblem` + one-next-question controller; conditional style decisions; Addendum 27 completeness + provenance.
- Versioned skill folders → deterministic skill-exclusive compiler → sole `StyleImageGateway` → Runware adapter (offline transport).
- Character construction contracts, real raster/alpha/mask/recomposition checks, approval gates, Remotion+FFmpeg renderer,
  S0–S9 loop, portable handoff, audit export.

## Layout
`vme/reference` sources/frames/survey · `vme/selection` first-15 + sixth · `vme/vision` packets/ledger · `vme/investigation`
gaps/controller · `vme/style` decisions/coverage/provenance · `vme/skills` skill folders/operators · `vme/compiler` brief/compiler ·
`vme/providers` capabilities/authorization/runware/gateway · `vme/artwork` raster/assets/character · `vme/review` approvals/server ·
`vme/render` renderer (+ `render/remotion`) · `vme/experiments`, `vme/diagnose` · `vme/loop` S0–S9 · `vme/state` store/workspace/handoff ·
`vme/audit` matrix/traces/export · `tests/` (requirement-ID-tagged) · `config/provider_capabilities.json`.

See `audit/RUN_INSTRUCTIONS.md`, `audit/CONTINUE_HERE.md` and `audit/UNIMPLEMENTED_OR_BLOCKED.md` in the audit ZIP.
