# 23 — What the v1.2 SPEC audit found, where failure remains possible, and what v1.3 actually fixes

Status: independently reviewed specification, **NOT** independently audited future Claude Code implementation. Preservation verified byte-for-byte for 14 inherited v1.2 files (other than intentionally replaced initial launch/README and generated manifest). Original 13-part user reference preserved unchanged.

| Weakness in v1.2 | Why it could wreck the project | v1.3 source-of-error fix | How to inspect actual future code |
|---|---|---|---|
| Observation rules could be 'high-detail' but not art-producing | Many notes about one scene, few transferable decisions | 14 asks specific production-unknown questions, contrasts examples and separates source facts; T1–T7 transformation | Actual `WitnessBundle → QuestionTrace → Decision → Recipe` with pictures and operators; B09–B16 |
| Recurrent patterns mistaken for universal style | Source creature geometry or scene colours copied everywhere | Conditional decisions depend on material/visual role/view/action; exceptions and *free original subject choices* explicitly recorded | Give two unlike hypothetical new subjects; prove choices vary appropriately; B10–B14 |
| Skill may be a Markdown report, not an execution path | Same old free-form prompt silently used | 15 typed operator DAG, exact selected rule IDs, frozen prompt clauses, reference-image role hashes, only compiled jobs reach gateway | Trace actual Runware caller; mutate active skill vs unselected prose; B15–B19 |
| Runtime composer could add its own aesthetic adjectives | Style authority bypass; learned art skills irrelevant | No runtime style author; original content and frozen skill separate; compiler rejects unsupported decisions or unauthorized style slots | Try direct `positivePrompt`, unpinned refs and content style smuggling; B19–B23 |
| Prompt 'specific' in text but no working references | Words cannot ensure consistent character/world pixels | Skill defines role-typed real image conditioning, whole-art edits and expected original asset state; verify provider route and image bytes | Real provider request, visual inputs, response images after consent; B22/B33 |
| Full image looked good but pose layers destroyed it | Limbs clip, wrong head/hand view, flat puppet | 16 whole design → canonical actor → guided whole pose+hand/prop → derive parts and hidden surfaces → comp | Asset family + actual final art/pose tests; B27–B29 |
| PNG assumed to be layered art | Missing alpha and clean plates, wrong masks and coords | 17 explicit pixel size/format/alpha/mask/coord/anchor/pose states; no flattened-asset deception | Inject opaque PNG, bad masks and asset swap; B25/B26 |
| No clear separation of structural image quality vs renderer bugs | Endless reanalysis when code broke; or patches when art weak | 13 causal failure table and 14 repair-source routing; upstream method changes before checks | Cause-specific fault injection and real visual comparison |
| Previous build prompt mixes huge learning with first coding session | Expensive inference before implementation is independently verified | 18 and new 00 mandate OFFLINE engineering → ZIP → independent audit → paid authorization | Actual ZIP contains source/tests/ledgers and zero unauthorized cloud calls; B35/B36 |
| Runware model silently guessed | Credits used on wrong model, unsupported reference/edit behavior | 19 verify user-approved exact model AIR ID, capabilities and output format; no assumption about '7B' | Model ID and cost/permission evidence; B23/B24 |
| ‘Every frame’ could be equated to decoded | False source-coverage claims, loss after timeout | Preserve v1.2 10; distinguish decoded/vision-seen/artistic/native states, atomic semantic commit+reconcile | Frame ledger and kill/resume tests B03–B08 |
| A dozen specialist agents produce incompatible reports | Quality falls apart when combining assets | One decision owner, connected gap clusters, shared scene+character asset contracts, on-demand specialists | Cross-operator DAG and integrated original art/pose |
| Same original scene improved repeatedly | Strong same-scene looks; no transferable skill | Retain same-brief controlled comparison, rotating unrelated original scenes and frozen unseen transfer | B32, real original visual transfer after consent |

## Remaining empirical unknowns that cannot be decided by spec writing

1. Whether the source-vision model can reliably distinguish artistic relations and decode the actual films at the detail required; cost/latency across hundreds of thousands of frames.
2. Whether the actual selected Runware model and its conditioning/editing routes can consistently create great original characters/worlds and coherent states.
3. Whether automated visual review agrees with professional/artistic judgment and user feedback on diverse scenes.
4. Whether any learned visual instruction genuinely raises original artwork quality above a strong unguided baseline on new subjects.
5. Whether complex original artwork retains richness under motion and camera perspective changes.

Do not claim these solved from offline tests or a paper spec. The build-first audit is necessary; *actual art* is the subsequent decisive evidence. When a model cannot follow a needed reference/edit operation, improve or replace the production route rather than add more validations or unlimited prompt prose.
