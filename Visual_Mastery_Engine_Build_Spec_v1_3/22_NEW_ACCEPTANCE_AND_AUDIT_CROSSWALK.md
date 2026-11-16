# 22 — v1.3 acceptance, coverage, and conflict crosswalk

The original requirement base is unchanged: 05 is byte-identical to the approved 13-part reference in v1.2. Every prior v1.2 contract is copied verbatim (01–12, 02 schemas, v1.2 tests), except `00` which now contains the first-session **audit-only** launch prompt; the old 00 is archived as `00_PREVIOUS_V12_LAUNCH_REFERENCE_DO_NOT_PASTE.md`. New 13–22 ADD implementation specifics. For conflicts, new 13–22 + new 00 have precedence, preserving the older mission. `05` is requirements, NEVER film-style evidence.

## B01–B36 new acceptance tests for coding agent

Tests labeled OFFLINE must run before first audit ZIP. Tests labeled PAID/ART require explicit budget+provider authorization and/or real artistic results later and must truthfully remain BLOCKED at offline audit, not be faked.

| ID | Condition to inject or demonstrate | Expected actual result | Phase |
|---|---|---|---|
| B01 | Open project without previous art/analysis | Only five allowed MP4s enter film-source provenance | OFFLINE |
| B02 | Given real film frame/time data | Presentation frame index+PTS hash and retrieval exact | OFFLINE |
| B03 | Index all frames but send none to VLM | Index coverage yes; VLM coverage exactly zero | OFFLINE |
| B04 | Vision result lacks one requested frame | No semantic commit, no per-frame 100% claim | OFFLINE |
| B05 | Vision input frame hash mismatches ledger | Packet quarantined | OFFLINE |
| B06 | Kill before/after paid request state | No duplicated billable call without status reconciliation | OFFLINE |
| B07 | Kill after response but before semantic commit | Resume stored response without recharging | OFFLINE |
| B08 | New session reads only CONTINUE_HERE+DB | Restores live questions, scene objects, next packet | OFFLINE |
| B09 | Ask vague 'style is polished' without picture consequence | Question engine returns targeted missing visual cause | OFFLINE fixture |
| B10 | Source-specific scene noun in a style decision | Rule demoted or blocked, source fact retained | OFFLINE fixture |
| B11 | Single source example presented as cross-film rule | Remains conditional candidate, not transferable | OFFLINE fixture |
| B12 | Connected world/character/colour deficits | One dependency-aware investigation cluster | OFFLINE fixture |
| B13 | Each visual question lacks an original-producing unknown | Agent must resolve or park as irrelevant | OFFLINE fixture |
| B14 | Candidate has no exceptions/adaptations | Cannot become frozen conditional style skill | OFFLINE fixture |
| B15 | Candidate has no actual callable producing operation | Skill state remains research-only | OFFLINE |
| B16 | Skill contains only SKILL.md | Runtime refuses production | OFFLINE |
| B17 | Change selected skill clause | Exact compiled prompt or relevant operation changes | OFFLINE |
| B18 | Change nonselected report adjective | Actual produced request does not change; no false improvement | OFFLINE |
| B19 | Agent attempts raw `positivePrompt` through production path | Refused before adapter/network | OFFLINE |
| B20 | Scene brief contains unapproved style rewrite | Separated into style-revision ticket or blocked | OFFLINE |
| B21 | Missing original actor identity reference on pose edit | Generation route refuses | OFFLINE |
| B22 | Reference count exceeds chosen Runware model | Stage plan changes with documented route or blocks | OFFLINE |
| B23 | Provider ID says '7B' without verified model | No paid call or silent model substitution | OFFLINE |
| B24 | No spend or third-party frame-upload consent | Corresponding network action refused | OFFLINE |
| B25 | PNG is opaque | Renderer/asset catalog never treats as transparent | OFFLINE |
| B26 | Generated layer wrong dimension or origin | Assembly identifies mismatch before motion | OFFLINE |
| B27 | Hand/prop contact requested | Whole pose+grip state planned before independent layers | OFFLINE |
| B28 | Alternate view differs from canonical identity | Producing edit route reexamined, don't auto-qualify | ART |
| B29 | Weak actor art returned | No full render; change upstream art method | ART |
| B30 | Approved character/scene hash changes | User approval invalidated and re-requested | OFFLINE |
| B31 | Multiple visible failures in one output | Maintain separate root-cause trails and connected cluster | OFFLINE fixture |
| B32 | Output improves one scene only | Not transferable until frozen distinct brief | ART |
| B33 | Skill cannot produce source-conditioned visual difference | Report failed skill, no fake success | PAID/ART |
| B34 | Whole-frame artwork rich but movement flat | Animate independent actor/art/camera state; no pan-only proof | ART |
| B35 | Audit ZIP packaged | Contains actual repo, tests, build/readme/inputs hashes, no keys/videos | OFFLINE |
| B36 | Read an implementation completion report | Each claim maps to concrete source function, test and evidence | OFFLINE |

## Existing A01–A68 remain required

`03_ACCEPTANCE_TEST_PLAN.md` is copied from v1.2 in its entirety. All A-tests still apply; the coding agent must list A01–A68 in requirement matrix even when a PAID/ART test cannot be run in the offline phase. `13_CRITICAL_PATH_AND_FAILURE_PREVENTION.md` lists C01–C38 (38 critical prevention mechanisms). Software tests are necessary but not sufficient for assessing the artistry of observation or production.

## Major conflicts resolved without dropping goals

| Old requirement | v1.3 interpretation |
|---|---|
| 'Complete film analysis and initial render in first engineering run' | Build full real infrastructure FIRST, stop for ZIP forensic audit; afterwards run the source+art learning with proper consent, artwork review and only approved video |
| 'One biggest gap' | Keep all high-impact gaps and prioritize one *connected* deep quality cluster (may contain several deficits) |
| 'Video at every major iteration' | Full-resolution original artwork first; rejected art cannot be forced into video; meaningful clip after art and animation-ready asset approval |
| 'All frames accounted for' | Decoded every frame, VLM-seen every frame only upon real provider proof, native-detail claims separately; preserve semantic resume |
| 'Prompt follows skill' | Prompt and image-operating recipe OWNED by skill; no general runtime aesthetic author; gateway blocks raw style calls |
| 'Character requirements/qualification' | Character manufacturing process: source-grounded whole design, canonical art, conditioned whole-pose edits, grip/face/limbs, intentional layers/clean plates, THEN backup review gates |
| 'One sample/one source pattern' | Conditional style decisions across unlike subjects, exceptions, genuine producing operators, original frozen transfer, no source trace copies |
| 'Runware Klein 4B default' | Runware key/account as chosen provider, exact AIR model must be verified. No unsupported named 7B assumption or silent 4B swap |
| 'Passed code tests = ready' | Engineer-ready / source-vision / art-quality / transfer are separate; audit ZIP before paid work |
