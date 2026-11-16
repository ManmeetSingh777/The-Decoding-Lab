# VME v1.3 R3 — exact integration blueprint, not another open-ended audit

## 0. What is being fixed, and what counts as completion

The inspected baseline is the uploaded `VME_V13_COMPREHENSIVE_REPAIR_AUDIT.zip`, SHA256
`0e49e93bfc9f2f696fc816957406b46d87f15af58e73467851a8f7fe06ad939c`.
This is **not** a snapshot of the user's live Windows G: checkout. Before any merge,
read current call signatures, preserve newer code, and adapt patch hunks to that code.
Never overwrite a newer live file with an archived copy.

**One-run delivery requirement:** Implement every engineering blocker together in
one coherent integration branch, run compact tests while building, and perform the
two slow full-suite runs **once after all source edits stabilize**. If the final
tests expose a defect, fix it, rerun the *impacted* and full qualifying suites,
then deliver one final audit with unchanged versions/hashes. Avoid the prior loop
of silently running 80-minute suites after each tiny change.

Preserve the existing Root Cause R01–R24, ST28 A–G, Addenda 24–27, source-reuse
ledger, 166-question governance and R1–R7.2 provenance. Explicitly map each to
the current operator and evidence. This blueprint **adds** missing execution
authority; it does not delete, weaken, or hand-wave the old requirements.

The **three** connected systems, all mandatory:

1. **Source observer/investigator:** actually receive original native video/audio
   evidence, identify whole-picture effects and consequential micro-decisions,
   maintain temporal/character identity, and ask one precise discriminating
   question within its larger interlinked causal cluster.
2. **Evidence-to-conditional-skill:** turn reviewed source relations and opposing
   cases into an immutable *conditioned method*, with mandatory references/inputs,
   distinct exceptions, tested operation, counterfactuals and honest unknowns.
3. **Skill-to-original audiovisual construction:** make each selected method
   govern actual image-provider messages, approved character asset states, motion
   programs, camera/attention/choreography, world movement, audio design and
   rendering. Audit pixel/timeline results, not only prompt strings.

Do **not** equate passing schema tests with source-visible truth or professional
style. Qualification is **earned** by reviewed real-source witnesses and original
construction; a simulation cannot grant it.

## 1. Implementation order: dependencies before consumers

For each row, implement the concrete behavior, named rejection and exact live
tests. `reference_guards.py` gives small executable examples of key algorithms;
the production integration must invoke equivalent guards at the named runtime
boundaries, not simply install a new file and claim those tests.

| Order | Live code / new module | Exact change | Mandatory negative proof |
|---|---|---|---|
| 1 | `vme/vision/protocol.py`, new `vme/vision/dispatch.py` | Every P1–P6 external source request goes through one `prepare_verified_request(...)`; its system text MUST contain the live `pass_instructions(pass_id)` (P0 + chosen Pn), with exact `PROTOCOL_SHA`, binding and parser contract. | Replace `P4` text while leaving version string constant: new request ID, cache invalidation; intercept actual S2 fake-adapter call and assert P0/P4 text. |
| 2 | `vme/vision/runner.py`, `vme/loop/real.py::_external_inputs` | Semantic cache keys include actual exact system/user prompt, image byte manifests, parser schema/code hash, provider limits/model ID, film hash, scene selection, transforms, question, boundary and consent profile. | Prompt sentence changes: no old `SEMANTIC_COMMITTED` accepted; interruption resumes without duplicate paid submission. |
| 3 | `vme/vision/contracts.py`, `vme/investigation/controller.py` | Adopt corrected modules: no generic `VALIDATED`, normalize structured object IDs, source-authorize witness IDs, require joint branch applicability. All 5 independent red-team cases must pass. | Replay original five real failures; ensure production routes invoke guards. |
| 4 | `vme/loop/real.py::_s1/_s2`, new source-coverage ledger | Source-first **per scene/frame/event/actor/state/relation** witnesses; native crops/adaptive packets; P2 mechanism/P3 question/P4 answer/P5 critical reinspection, no stage bypass. Two separate coverage ledgers. | One non-empty 'dimension' but unexamined character redraw: scene NOT complete. A missing target frame cannot disappear due chunking. |
| 5 | `vme/style/authoring.py:author_decision`, `vme/investigation/controller.py:apply_answer` | Central **authoring** guard checks stage, actual submitted witnesses, source truth vs inference, sufficient producing action, contradictions, owner, one joint condition and registered op before writing. Earlier stages cannot publish. | Directly call writer from S1/S2 with fluent ungrounded answer: `RESEARCH_ONLY` or `Blocked`, no skill. |
| 6 | `vme/style/authoring.py:_package_references`, `vme/skills/*`, prompt compiler | Explicit per-branch conditioning policy. Missing `REFERENCE_REQUIRED` is **UNKNOWN**, not false. Preserve multiple distinct positive/contrast view/scale roles, hash bytes, consent and provider capacity. Hard-block unsupported required conditioning. | Omit field/one mandatory exemplar/provider unsupported/upload denied: no paid image request, no fallback. |
| 7 | `vme/loop/real.py::_s5/_s7/_s8`, art-state/scene compiler | Separate actor IDs and canonical/state graphs; source-owned character shape/art decisions; typed original asset, motion, camera, attention, interaction/world/audio operations. | Two actors and one prop: no shared canonical, no hand/prop slip, each track has source skill owner and local ablation. |
| 8 | `vme/render/renderer.py`, Remotion, audio pipeline | Native audiovisual timeline and mux, ffprobe/frame/PTS/audio/sync terminal gate. No unconditional `WHOLE_STATE_SWAP`/linear fake professional acting. | Corrupt video, dropped audio, off-sync, bad frame count and bad contacts: film blocked with concrete reason. |
| 9 | `_s9`, review and promotion | Separate technical green, source-art source truth, skill candidate, original still, multi-state motion and 2-min multi-subject full AV qualifications. A late human reject reopens exact causal ancestors only. | Beautiful but false source observation cannot qualify; still-only holdout never grants motion/AV. |
| 10 | capsule/cold restore/CLI/export | Reproduce final immutable source/evidence/skill/prompt/scene/art hashes and same scene outputs from a newly extracted folder. Deterministic admission, no bypass through alternate entrypoint. | Change one protocol or parser byte, remove a hand state or break a sound asset: replay aborts or reopens precise dependent work. |

## 2. Versioned source dispatch: exact required algorithm

Implement in `vme/vision/dispatch.py` a single submission constructor, and
replace **all** direct `vis.request_json(...)` paths touching source analysis:

```python
def prepare_verified_request(*, pass_id: str, source_sha: str,
    selection: dict, target_images: list[dict], context_images: list[dict],
    prior_boundary: dict, active_cluster: dict, controlling_problem: dict,
    competing_explanations: list[dict], required_response: dict,
    provider_profile: dict, parser_contract: dict, preprocess_contract: dict
) -> dict:
    system = pass_instructions(pass_id)  # P0 + exact P1..P6; NEVER QA_SYSTEM alone
    binding = bind(protocol={"version": PROTOCOL_VERSION, "sha": PROTOCOL_SHA,
                              "pass_id": pass_id},
                   source={"sha256": source_sha}, sequence=selection,
                   target_images=target_images, prior_boundary=prior_boundary,
                   active_cluster=active_cluster,
                   controlling_problem=controlling_problem,
                   current_competing_explanations=competing_explanations,
                   required_response=required_response)
    # Assert sha256(each image's actual locally-read bytes) == manifest's byte sha.
    # Assert selected source and native PTS; no fabricated "received" receipt.
    # Form canonical exact user text; pin parser and context images as inputs.
    request_sha = digest({"system_text": system, "binding": binding,
        "contexts": context_images, "provider": provider_profile,
        "parser_contract": parser_contract, "preprocess": preprocess_contract})
    return {"system": system, "binding": binding,
            "request_sha": request_sha, "response_schema": parser_contract,
            "actual_sent_byte_manifest": target_images + context_images}
```

The `bind()` signature above matches `vme.vision.protocol.bind`; ensure all
`REQUIRED_BINDING` keys are present even when an object is an explicit empty
list. `target_images` and contexts must include source SHA, source-local ID,
native PTS, region, dimensions, raw-frame SHA, image-byte SHA, original vs crop,
and target/context role. Compute byte digest **from bytes that will be sent**,
not a model echo.

Replace call-site roles exactly:

- `_rationale_batch` → P2 (source sequence and mechanism alternatives).
- One-question selection/controlling problem → P3 (even if deterministic DAG
  picks the candidate, the actual P3 contract must record one discriminating
  question and both branches of evidence outcome).
- `_s2` currently sending bare `QA_SYSTEM` → P4, with ONE selected question and
  actual six-or-fewer source witnesses; expand packet with native crops if needed.
- `_native_followups` → P5 (not stand-alone `NATIVE_SYSTEM`).
- `PacketRunner` initial frames → P1; stage/capsule resume → P6 as appropriate.

Persist request journal **before** provider submit; persist actual provider
response and its real receipt fields afterward. Response status progression:
`LOCAL_BYTES_VERIFIED` → `SUBMITTED` → `RESPONSE_RECEIVED` →
`IDENTITY_BOUND` → `ARTISTIC_CLAIM_UNVERIFIED` →
`SOURCE_ARTISTICALLY_REVIEWED` (independent native source check). Never set
`images_received=images_sent` yourself and claim it came from provider.

Packet commit check:

```python
current_request_sha = prepare_verified_request(...)["request_sha"]
saved = store.lookup_committed_request(packet_id)
if saved is not None:
    if saved["request_sha"] == current_request_sha:
        return "SEMANTIC_COMMITTED"  # only if manifest/capsule versions match too
    store.invalidate_downstream_without_deleting_raw_evidence(saved["request_sha"])
    raise Blocked("STALE_SEMANTIC_PACKET_REQUIRES_NEW_ID")
```

Do not retain a previous raw response as current after prompt, parser, model,
selection or question changes. Do not re-bill an **uncertain** charged submission:
reconcile task ID with provider or set `UNKNOWN_BILLING` for human action.

## 3. Deep source-first artistic investigation: HOW to observe each of 15+1

**Do not begin with prescribed anatomy fields or a generic picture template.**
Start with each actual selected source video, whole scene purpose and temporal
transitions. Discover only real visible constructs and their causal dependencies.
For every source frame show it to the model (or explicitly mark unexamined);
for high-impact visual uncertainty retrieve unresampled native image regions,
adjacent states and unlike examples from the existing evidence store. Reuse prior
R1–R7.2 findings only when source hash and witness identity exactly match;
record narrowly which unresolved gap justified additional decoding.

Use a **two-layer ledger** (independent fields/tables, never unioned):

1. `SourceArtObservation`: `(film_sha, selected_scene, native_pts, frame_id,
   actor_or_entity_id, drawing_state_id, event_id, part_or_relation_id,
   witness_ids, whole_art_context, observed_visual_relation,
   temporal_change_or_persistence, competing_mechanism, confidence,
   unknown_or_exact_crop, source_review_status)`. `UNKNOWN` must carry exact
   next witness/counterexample. A frame SHA/index alone has zero art coverage.
2. `ProductionDecisionCoverage`: `(original_subject, script_beat,
   condition_tuple, required_output_operation_id, owner_skill_sha,
   clause_sha, reference_roles, actor_art_state, motion/audio consumers,
   ablation_result, reviewer_verdict)`. This second ledger cannot claim source
   study completed and cannot reuse an image clause as a motion rule.

At each scene, record the actual joint art system: coherent large outer shapes;
part relationships, visual hierarchy and contrasts; character/prop/world
interactions; colors by **role** plus local values, gradients, materials, edges,
shadows and light direction; source-specific character contour and taper;
camera vs world vs drawing redraw (as competing mechanisms until established);
simultaneous events, attention, rhythm and transition; narration/music/SFX
and audiovisual timing. Investigate every visible **consequential** difference,
not just a fixed category list. Treat deliberately stable/quiet spans as
stable, with witness and persistence, not invented activity.

Make the cross-scale loop explicit for every high-impact cluster:

1. Identify the whole-frame design effect and the source event's purpose.
2. Record the 2–5 **coupled** most important unresolved design decisions.
3. Pick the earliest one that would change a real producer operation.
4. Ask ONE question that separates at least two plausible mechanisms, name
   exact source witnesses/crops and predicted **different** operator actions.
5. Compare same identity across frame states and *different subjects/films*;
   search contrary cases. Separate `VISIBLE_FACT`, `INFERRED_CAUSE` and UNKNOWN.
6. Write an explicit conditional construction action (when, what visual
   relation, how to draw/render it, required inputs and forbidden failure modes).
7. Reinspect at native size; check whole-picture integration and source identity.
8. Only then promote to candidate with formal source→operation lineage.

**Characters deserve their own dossier.** `reference_guards.validate_character_art_study`
provides a minimum machine-checkable record for: whole depicted entity,
outer-contour and thickness/taper along each visible segment, negative spaces,
specific piece junctions/occlusion, material/fill/edge, light/shadow treatment,
expression features as actually drawn, view/pose changes requiring new drawing,
grip/prop/ground contact, and integration with world. Include variations,
counterexamples, cross-scene identity and how art changes under motion.
Names like `arm`, `hand`, `skull` are semantic tags applied **after** observation,
not automatic extrusion instructions. A renderer must not invent tubes, fingers,
limb proportions, flat face plates, round contours or shading not supported by
the chosen conditional design.

Scene gate: every target ID accounted for, no unsupported high-impact claim,
all outstanding gaps listed by source frame/crop/operator, meaningful art
relations and all active character redraw states reviewed. Completion remains
`NEEDS_SOURCE_REINSPECTION` while any consequential open gap lacks action.
No shortcut by replacing 15 individual records with one general paragraph.

## 4. Decision promotion: exact authority check, at the WRITE site

Modify `vme/style/authoring.py:author_decision(...)` to reject any caller if:

- `question.owner_stage != "STYLE_CONDITIONS"` (S1/S2 source/causal answers only
  create observations and alternative hypotheses); OR
- the cited IDs are not a subset of the **locally recorded actually submitted**
  witnesses from this exact request/source/PTS/crop (not `answer_evidence_ids`);
  OR
- `assess_sufficiency(...)` lacks relational source facts, a real producing
  operator, specific construction action and unresolved uncertainty tracking;
  OR
- the selected branch does not jointly cover the *whole* output condition tuple
  (independently reviewed invariance is a narrow explicit exception); OR
- a contradiction/unknown/precondition makes this decision research-only; OR
- the operation is not in the registry or is only a text label without a real
  future consumer and an output contract.

Central invariant:

```python
def author_decision(..., authorized_submission_manifest: dict, ...):
    if question["owner_stage"] != "STYLE_CONDITIONS":
        raise Blocked("EARLY_STAGE_CANNOT_PUBLISH_SKILL")
    allowed = verified_local_witness_ids(authorized_submission_manifest)
    if not cited_answer_witness_ids(answer) <= allowed:
        raise Blocked("UNSENT_WITNESS_CITATION")
    proof = assess_sufficiency(answer,
        producing_operator=question["allowed_registered_ops"],
        known_witness_ids=allowed)
    if proof["verdict"] != "SUFFICIENT_FOR_PRODUCING_CHOICE":
        raise Blocked("INSUFFICIENT_FOR_PRODUCING_CHOICE")
    # Preserve opposing explanations and old candidate revisions.
    # Check all joint conditions and required art-state/reference inputs.
    # Only THEN perform registered immutable write + derive clause.
```

Update ALL writers/callers, including direct tests and restoration paths; no
alternate import can bypass this guard. `question.owner_stage` is a trustable
locally constructed envelope, not a free-form answer field.

`SOURCE_VISIBLE_FACTS` must tie each relation to exact visible parts and native
witness; do **not** reject a true observation merely because it lacks a preset
keyword. Strong automated tests show structural authority; human/native visual
review must confirm the actual source fact before calling it true.

### Branch ownership and uncertainty

If an output requires `(view=three_quarter, action=grip, light=right)`, branches
for just `view=three_quarter` and just `action=grip` DO NOT jointly establish
the intersection. A single coherent branch must cover the intersection,
unless every omitted axis has independent, contrasting and reviewer-approved
invariance evidence. Reject contradictory equally applicable branches instead
of silently using list order. Unknown applicability means BLOCK or targeted
study, not default interpolation/fallback.

## 5. Exact source-conditioned production: image prompts are NOT the whole system

Each accepted skill MUST be an immutable, content-hashed record with:

```json
{
  "skill_id": "SK-*", "source_sha256": "...", "source_witness_ids": ["W-*"],
  "phenomenon_id": "...", "producing_choice_id": "...", "status": "CANDIDATE",
  "branches": [{
    "when": {"view": "...", "action": "...", "lighting_role": "..."},
    "micro_specific_construction_action": "...",
    "operation_id": "image.actor_state | motion.contact | camera.attention | audio.cue | ...",
    "reference_policy": {
       "mode": "REQUIRED | TEXT_ONLY_DEMONSTRATED | NOT_APPLICABLE",
       "reference_roles": [{"role": "positive_view", "witness_id": "W-*",
           "image_bytes_sha256": "..."}]
    },
    "required_layers": [], "required_drawn_states": [], "forbidden_failures": [],
    "predicted_local_visual_effect": "...", "negative_counterfactual": "..."
  }],
  "tested_consumer_operation_ids": ["..."], "qualifying_reviews": []
}
```

Literal strings above are **schema illustrations**, not fake facts or a universal
fixed style. Do not put `status=QUALIFIED` without independent real-source and
original-art proofs. `TEXT_ONLY_DEMONSTRATED` needs a reviewed source-to-text
transfer test; it is not the silent fallback if a source exemplar cannot be
uploaded. Third-party image references stay local until explicit human consent
and provider capability limits are verified. Multiple different view/contrast
roles must preserve their actual distinct source witnesses; **never** choose
`sorted(wids)[0]` for every role.

**CRITICAL:** Neither a model-authored `approved: true` nor an inline skill
`qualification_proofs` object is trusted. All human approvals, source-upload
consents, provider capability checks, reviewed invariants and text-only transfer
test IDs must be verified against a **separately stored, authenticated local
authority registry**, scoped to source SHA, witness byte SHA, skill version,
provider model and task. The standalone guard module takes this registry via
`trusted_authority` deliberately; do not populate it from the model's reply.

Compile a `ProductionControlPlan` before any image call or render, with the
**complete required operation set** derived from the novel script and source
skill-conditioned choice graph, not merely a list of actions already selected
by the model. Require one unambiguous owner skill per required operation;
`reference_guards.build_locked_control_plan(...)` demonstrates the check.

**Image request producer:** emit (1) original story subject/semantic content
slots, (2) frozen per-source-qualified art-method clauses **verbatim**, (3)
positive/negative and alternate-view references with correct roles and hashes,
(4) proven scene-specific identity, layer, mask, light/shadow, silhouette and
art-state constraints, (5) forbidden generic tube/stock-face/improvised
features, (6) provider-supported generation/edit/variation controls, (7) exact
trace `(skill_sha, branch_id, operation, payload_sha, returned asset_sha)`.
Allow user to choose original content, NOT to free-form overwrite locked style.
Provider refusal or off-style asset blocks approval; never auto-promote a
well-worded prompt as a successful image.

**Non-image producers:** the *same* plan must issue separately typed operations
for alternate drawing states, masks/rig/contact, event and simultaneous-activity
graph, pose transitions and holds, easing/tempo, camera/world/attention tracks,
lighting changes, backgrounds, AV meaning and sound cue timing, narration and
audio mux. Every source art rule has a trace to the concrete code path (and
visible frame range or audible interval) it changes; removing that rule must
change the expected local result or BLOCK. The independent red-team script
tests missing IMAGE or MOTION operation ownership.

### Actors, character art and drawn states

Key `actor_id → identity_sha → approved_canonical → state family`. Each new
drawn pose/view/contact/expression state needs source-conditioned design, actual
asset hash, ownership and review; a different actor can NEVER alias the same
canonical by default. Reprojection, IK and deformation may be used only when
source-derived constraints/approved states bound their visible contour;
unconstrained tube-like limb extrusion is forbidden. Contacts include which
painted surface overlaps, near/far layer order, grip silhouette, object anchor,
local world orientation, feet and centre-of-mass/weight cue. The multiactor
test MUST render independent state and interaction over time.

### Motion and AV

`SceneGraph.jsx` must consume a versioned skill-derived event program, not
just unconditional linear transforms and `WHOLE_STATE_SWAP_ONLY`. Model a
temporal event DAG with simultaneous tracks, explicit art-state substitution,
hold/anticipation/overshoot when witnessed, actor/body/prop contact, camera
versus world motions, attention beats and offscreen continuity. Permit a
linear path only when the **specific learned decision** selects it and its
output is reviewed; no universal motion default masquerading as learned style.

For AV, inspect source stream timebase, narrated words/meaning by temporal
position where access/legal constraints allow, music and effects events,
silence, sync and transitions. For new original films, generate/choose approved
original voice/music/SFX, schedule and actually mux audio, then check PTS,
duration, peak/clipping, missing stream and sync against the event program.
`AUDIO_STUDY_UNAVAILABLE` or `NO_APPROVED_SOUND_ASSET` is a legitimate
BLOCK, not a silent video-only success. No unlicensed source-audio copying.

### Render result must refuse failure

At `render_video` and `_s8` immediately after ffprobe / motion / audio checks:

```python
if not ffprobe_result["ok"]:
    raise Blocked("TECHNICAL_RENDER_FAILED", "ffprobe or frame/codec/timebase")
if not timeline_motion_result["ok"]:
    raise Blocked("TECHNICAL_MOTION_FAILED", "required evidence/contacts")
if output_contract["needs_audio"] and not audio_mux_and_sync_result["ok"]:
    raise Blocked("AUDIOVISUAL_SYNC_FAILED")
```

Diagnostic silent and intentionally static tests MUST have explicit separate
scope and never satisfy full audiovisual qualification.

## 6. Full-scene quality consistency — no 'first scene good, last scene shallow'

For **each** of 15 selected scenes and the separately approved 16th source
interval, produce a scene certificate with these independently reviewed facts:

- Exact source hash + selection start/end native PTS + timeline frames actually
  transmitted, packet count, context, crop identity and P0–Pn prompt SHA.
- Visual entity/character/prop/world state graph, source-first whole→parts→whole
  art decisions including color/material/lighting/edge/contour/negative-space,
  and temporal state/interaction graph; what remained stable is explicit.
- Audio/meaning/editing cue graph for actual present signals and uncertainties.
- Every consequential `ObservedRelation` traced to at least one real target,
  native crop/contrast when needed, competing interpretation, applicability,
  candidate producing operation and confidence/status.
- Every unresolved consequence remains OPEN with exact next witness, new
  question and blocked operation; never quietly disappear because the prompt
  token budget was exhausted.
- Human/source-art review samples representative and **hardest**, most complex
  cases of each art family, plus deliberate counterexamples and multiple film
  styles. Require corrections before a generalization claim.

The system should determine packet sizes dynamically: large visible complexity
or dense character art → fewer targets and extra crops; simple stable span →
bounded sequential coverage with explicit persistence. Set hard response
budgets per target, signal truncation as incomplete, do not shrink output until
the observer ceases detecting phenomena. In doubt keep an **indexed UNKNOWN**.
An automatic audit should count witnesses, native-detail inspections, phenomena,
joint branches, source-grounded operations and open unknowns **per scene**,
not aggregate a reassuring single total.

## 7. The real pre-analysis go/no-go, tested on one actual source sequence

After offline wiring and independent ZIP verification, seek user authorization
for a **bounded, reviewed, legal** actual source canary, not a blind 15+1 run:

1. User confirms 5 film roles + 6th intro boundaries and selects one sequence
   with difficult expressive character redraw, interacting hands/prop, world,
   camera, shading and at least one AV cue. Confirm provider credentials,
   source upload rights, caps and expected spend independently.
2. In the live run capture exact source frames/audio/crops and raw request/response
   SHA, with a human reviewer verifying key artistic claims against pixels.
3. Ask and answer the highest-impact gap, promote no stronger than candidate,
   compile one original character+world image and **short animated audiovisual**
   counterfactual. Compare it with the frozen skill removed.
4. Verify source truth, character whole look, absence of generic tubes, actor
   identity, shading, lighting, interaction/pose/occlusion, temporal action,
   audio meaning/sync, scene readability and independent reviewer verdict.
5. Only if every check passes and the specific open gaps are resolved mark
   `READY_FOR_15_PLUS_1_SOURCE_INVESTIGATION`. Do **not** equate this with
   `PROFESSIONAL_2_MIN_PRODUCTION_QUALIFIED` until true held-out original films
   pass separately.

This canary is NOT an excuse to defer known architectural issues. All predictable
system responsibilities above must be designed, implemented and negative-tested
in the one repair. The canary tests real perception/art quality that no offline
synthetic output can establish.

## 8. Final evidence package — exact required export

At stop, archive these named files with internal SHA manifest and source paths:

1. `IMPLEMENTATION_MAP.md`: every R01–R24, ST28 A–G, F01–F18 and character-
   first/AV clause → actual function → proving test → final commit SHA → status.
2. `DELTA.patch` + full changed files + no unrelated modifications.
3. `INDEPENDENT_REDTEAM_ORIGINAL.log` +
   `REFERENCE_GUARDS_26_TESTS.log` + live-boundary tests, with adversarial
   before/after status. The 26 fixture tests alone do **not** prove integration.
4. `REAL_REQUEST_CAPTURE_INDEX.json`: sanitized exact outbound messages,
   frame byte manifests, protocol/parser hashes, stage handoff and receipt.
5. `SOURCE_AND_PRODUCTION_COVERAGE.json`: **two** separate ledgers; preserve
   original R1–R7.2 witnesses and never claim unexamined footage was reviewed.
6. `CONDITIONED_SKILL_CAUSALITY.json`: illustrative valid/invalid conditional
   skills, references, clauses, image payload, operation plan and ablation.
7. `CHARACTER_AND_MULTIACTOR_TEST/`: native witness studies (where authorized),
   drawn states, two actors, contact, shading, timecoded visual reviews.
8. `MOTION_CAMERA_AV_TEST/`: real compiled event program, local ablations,
   ffprobe + AV failure drills, original demo only if truly produced.
9. `TESTS_FINAL_COMMIT.txt`: repo and fresh-extraction full suite logs with
   exact totals/skip reasons, static scans, types, compilation, negative drills,
   temporal identity and cold-start reconciliation; no stale earlier results.
10. `CAPABILITY_VERDICT.md`: independent YES/NO for **engineering wired**,
    **source evidence ready**, **visual truth confirmed**, **skill qualified**,
    **original still art**, **character animation**, **sound**, **2-min held-out**;
    no overall 'ready' formed by averaging.

Export `G:\The Decoding Lab\VME_V13_R3_FINAL_INDEPENDENT_AUDIT.zip` and its
SHA256, then **STOP** with `STOPPED_FOR_INDEPENDENT_IMPLEMENTATION_AUDIT`.
Never start the paid/live 15+1 investigation merely because final pytest is green.
