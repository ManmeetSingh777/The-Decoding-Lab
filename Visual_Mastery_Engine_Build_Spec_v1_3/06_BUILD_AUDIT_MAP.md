# Independent contract inspection — requirements and evidence map v1.2

**Latest requirement supersession:** 07/08 add style abstraction, every-frame tracking, skill-compiled image prompt, character-state and limb construction, and artwork/asset user approval before motion. The previous "12–20s MP4 every major iteration" is now conditional on art+asset approval. Other 13-part commitments remain.

This document is **not** proof of implemented software. It is a static preflight of the build specification, verifying that each user-requested change has an explicit implementation requirement and test.

| User-specific correction | Contract location | Required code/evidence | Acceptance |
|---|---|---|---|
| No prior AnimationLab source/evidence contamination | §0; §1; §16 | clean repo, source allowlist, audit provenance | A01, A02 |
| Several important gaps, not one only | §2, §6 | multi-gap register ranked from original images | A08 |
| High-impact priority, not arbitrary geometry | §2-3 | source witnesses, affected visual qualities, ranking justification | A08-A10 |
| Deeply specific cross-category and connected observations | §3 | evidence-backed question/relations graph with cross-source contrasts | A10 |
| First run investigates cluster of related causes | §2, §6, §11 | first integrated cluster 2-5 linked gaps and targeted questions | A09, A24 |
| Multiple questions -> multiple skills and changes in one run | §4, §6 | skill versions plus actual callable operations | A11, A12 |
| Isolate implementation bugs from analytical mistakes | §6, §12 | diagnostic classes, discriminating tests, masked failures | A14 |
| Don't overfit original reference clips | §0, §3, §9 | cross-film source witnesses, conditional art procedures | A10, A17 |
| Don't overfit our one original scene | §9 | fixed anchor, rotating subjects, unseen challenge after freeze | A15-A17 |
| Video endpoint rather than image-only | §6, §8, §11 | full-resolution art and 12-20s *genuine moving* MP4 per major iteration | A07, A24 |
| Need entire rendering and image production stack | §8, §10, §14 | real provider + Remotion + FFmpeg + verified assets | A04-A07, A21-A22 |
| Sequential lead but possible efficient bounded parallelism | §5 | one shared state, independent tasks permitted, single decision/commit lane | A19 |
| User visually reviews every iteration | §6, §10; review packet | actual functional gallery and durable review record | A18 |
| No fake qualification after tests pass | §4, §13 | evidence-linked separate skill and visual quality status | A12, A23 |
| Preserve all approved 13 sections | §1-13; §16 | structure and original reference copied as requirements | entire plan |

## Remaining true uncertainties that software must resolve

- Actual available credentials, authorized spending and permission for any third-party frame conditioning.
- Whether the chosen image provider can deliver high enough art quality, identity-preserving variants and motion-ready layered assets.
- Whether source-specific styling and original art are consistent across diverse subjects without per-scene manual work.
- Whether the first real A/B output is visibly better, and whether user agrees.

These are **empirical unknowns**, not missing instructions to the coding agent. Code must expose them as real runtime states rather than assuming success.


## New user corrections v1.1

| User correction | Actual spec consumer | Acceptance |
|---|---|---|
| Observations must be style-making, not source-object descriptions | 07 §0 `StyleMechanism` / source facts exclusion and conditional production decisions; new style schema | A30–A32 |
| Frame-by-frame coverage, not 10/12 fps pretended complete | 07 §1 `FrameCoverageLedger`, separate verified VLM input ledger, actual PTS and cost gate | A26–A29 |
| Image prompts governed by learned style skills, original content kept distinct | 07 §2 `PromptCompiler`, `SceneArtPlan`, provenance, coverage, provider validation; 08 working example | A33–A37 |
| Raster image models main art producer, no generic SVG drawing of people | 07 §2–§3; prompt's hard prohibition and provider capability probe | A04, A22, A37 |
| Exceptional character artwork, face, proportions, hands, limbs and states | 07 §3 `CharacterAssetFamily`, approved canonical conditioned variants and layer reconciliation | A38–A41, A45 |
| Stop poor images before costly MP4 rendering | 07 §4 `ArtApproval`, `AssetApproval`, immutable gated state; updated 04 review page | A42–A44 |
| Maintain several connected deep questions and original-scene rotation | original 13 section 2/3/6/9 retained; style mechanisms supplement, not replace | A08–A17, A46 |
| Audit claims separate from actual skill and art evidence | 07 §6 success status breakdown; prompt/workflow validation | A48 |

## v1.2 prevention-first correction map

| User constraint | Authoritative implementation owner | Required real evidence |
|---|---|---|
| No scene-bound style analysis | `09` sections A–D, `ConditionalStyleDecision`, A49–A52 | Source witness → conditional transferable decision; copied scene fact refused |
| Observations must actually produce sophisticated original artwork | `09` C5–C9, `SkillProductionRecipe`, A52/A55 | Real provider image produced from exact recipe and contrasted with baseline |
| Image model's aesthetic prompt authored SOLELY by learned skills | `09` E–F, `11`, `PromptAuthorityTrace`, A53–A57 | Frozen skill clauses are only style text; runtime improvised style has no route to provider |
| Characters designed as coherent family, not crude generic SVG rig | `09` G, `CharacterConstructionPlan`, A58–A60 | Full canonical art, viewpoint/face/hand/prop states, actual composites |
| Every single video frame visually processed (not 10fps) | `10` sections 1–3, `FrameSemanticEntry`, A61/A62/A66 | Verified per-frame provider input/response ledger; incomplete reported honestly |
| No timeout restart, preserve substantive understanding | `10` sections 4–6, `SemanticPacketCheckpoint`, A63–A65 | Kill/restart after request/response/commit and resume at exact valid packet+question |
| Checks secondary to input/production correction | `09` E/H, `11`, A53–A59/A67 | Changed producing decision and real actual image; not just a guard |
| Original user approved 13 points remain | `05`, `01`, `06`, launch prompt | No deleted requirement; any conflict explicitly superseded by 09/10/11 |
