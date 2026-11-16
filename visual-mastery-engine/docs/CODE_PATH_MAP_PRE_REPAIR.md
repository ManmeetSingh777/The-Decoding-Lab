# Code-path map BEFORE the comprehensive repair (written before any source edit; HEAD 651c75b, tree clean)

Read in order: Repair Contract R01–R24, Independent Audit 2, Addendum 28 standard, versioned prompt contract,
worked calibration casebook, ST28 test plan, capsule schema. Then the current code. This map lists what EXISTS
and what is MISSING, per finding. Nothing here is a claim that the defect is fixed.

| ID | Existing function (file:symbol) | Observed defect in existing code | Missing function(s) |
|---|---|---|---|
| R01 | `vme/vision/runner.py:PacketRunner.run` builds `f"{idempotency_key}-{uuid5}"` (74 chars); `vme/loop/real.py:_s0` `rat-win_<sha10>_<a>_<b>`, `_native_followups` `nd-W-...-native-x-y`, `_s2` `qa-<24hex>`; `claude_adapter.request_json` forwards unchanged | no 64-char / charset validation anywhere | canonical request descriptor → `custom_id` derivation + validator; strict fake that rejects invalid ids |
| R02 | `claude_adapter.request_json` | `batches.create()` BEFORE any durable intent; crash between create and `task_*.json` write loses batch id | `SUBMISSION_ATTEMPTED` intent journal; `SUBMISSION_UNCERTAIN` state; human reconciliation entry point |
| R03 | `claude_adapter.production_client_factory` imports `anthropic` | `anthropic` absent from `pyproject.toml` / `requirements.lock` | pinned SDK + clean-install serialization check |
| R04 | `providers/gateway.py:StyleImageGateway._run` | `uuid.uuid5(NAMESPACE_URL, key)` as Runware taskUUID | UUIDv4 generated once, persisted with body hash before send; v4 validator on reuse |
| R05 | `gateway._run`, `runware.RunwareAdapter.parse_images` | URL result → `PROVIDER_URL_EXPIRED_OR_UNFETCHED`; no dataURI; no `includeCost` in payload (`compiler.compile`, `compile_baseline`) | `includeCost:true`; dataURI decode; controlled HTTPS fetch with host allow-list, size/time limits, content-type + decoded-size check |
| R06 | `gateway._run` IN_FLIGHT branch | any parse failure → UNKNOWN_BILLING; no processing/success/error/not-found distinction; no deadline | getResponse status machine, deadline, per-UUID receipt |
| R07 | `providers/authorization.py:AuthorizationRegistry.check/spent/record_spend` | check-then-spend race on a JSON file; spend recorded after commit; no reservation, no liability | transactional reserve/settle/release/liability ledger (SQLite, BEGIN IMMEDIATE) |
| R08 | `style/authoring.py:author_skill` | `references=[]`, `reference_roles: []`; `compiler.compile` reference plumbing exists but is never fed | witness exemplar packaging (bytes, hash, role, consent) → branch `reference_role_ids` → compiled `inputs.referenceImages`; named refusal when missing |
| R09 | `style/authoring.py:decision_id_for(dims)` | identity = hash(sorted dimension tags) → same-category findings collide; merge by `when`+op | semantic production-choice identity (phenomenon + producer choice), contradiction retention, no last-write-wins |
| R10 | `loop/real.py:_ledger` | dimension SUPPORTED when any decision has the tag; `set_relation(... evidence=[])` | per-phenomenon / per-choice ledger with witness-backed joint relations |
| R11 | `loop/real.py:_s2` (STOP on MISSING_SOURCE/CONTRADICTED), `_native_followups` (first 3 per sequence) | no gap-driven reinspection | gap-selected crops + temporal neighbours + new question; budget gated; no fixed 3 cap |
| R12 | `loop/real.py:RealLoopRunner.run` | skips any stage once COMPLETED, regardless of upstream change | stage input-hash cache key + deterministic invalidation of dependants |
| R13 | `loop/real.py:_s0` returns COMPLETED with sixth `PENDING_HUMAN_BOUNDARY_LOCK`; `_s1` silently omits it | — | hard stop before L0 until the sixteenth interval is locked |
| R14 | `reference/roles.py:role_status`, `_s0` stop | already stops on unconfirmed base five (kept) | FILM_SOURCE_STATUS export with true 720p resolution |
| R15 | `authoring.author_decision` copies branch text | no explicit exemplar / unknown / state field | candidate recipe states, explicit exemplars and unknowns |
| R16 | `compiler.compile` | mandatory skill reference roles never present | block when a mandatory reference/consent is missing (exists as `REQUIRED_STYLE_REFERENCE_MISSING`, unreachable from real skills) |
| R17 | `loop/real.py:_s7` | only CHARACTER_STATE view/grip produced; expressions → `not_generated`; layer/clean-plate steps ignored | demand → operator → artifact → consumer, or explicit NOT_IMPLEMENTED blocker per step |
| R18 | `_s5` whole scene + canonical; `_s8` overlays actor on the whole scene | actor duplicated over a scene that already contains it | separate clean world plate operation; scene assembly from plate + actor |
| R19 | `artwork/raster.py`, WHOLE_STATE_SWAP | no segmentation/clean-plate pipeline | honest blocked routes for unsupported extraction/occlusion |
| R20 | `_s8` actor at `x=W*0.55`, default pan | renderer does not consume a directed event/actor graph | shot-plan actor/world/event graph consumer; no default pan |
| R21 | `_s4` writes fixed `skills/real-<run>` folder in place | stale clause files may survive | content-addressed immutable version folders + atomic CURRENT pointer |
| R22 | `_windows` caps 10 evenly spaced windows/film | convenience cap | coverage-driven candidate expansion ledger |
| R23 | `_s9` one holdout still | may read as general transfer | separate still vs animated transfer labels |
| R24 | `tests/test_compiler_authority.py` static regex; `tests/test_real_path.py` child snippet lacks `Path` import | 2 failing tests | AST call-target scan; fixed child snippet |
| A28 | `vision/prompt.py:build_vision_request` single template; `vision/contracts.py:validate_packet_response` field-presence; `investigation/controller.py` | no protocol id/sha, no pass ids P0–P6, no capsule, no drift calibration | `vme/vision/protocol.py` (VME-A28-1 passes + sha), sufficiency check for producing choice, `vme/state/capsule.py` (export/import/verify against `28_INVESTIGATION_CAPSULE_SCHEMA.json`), model-drift calibration |
