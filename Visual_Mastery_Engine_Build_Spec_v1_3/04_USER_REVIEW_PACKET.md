# USER VISUAL REVIEW PACKET — REQUIRED FORMAT v1.2

**Preserved v1.1 art-first change:** THREE GATES, not one. First the user approves the actual FULL-RESOLUTION original artwork and character design; then the animation-ready character/assets pack; ONLY THEN may the full original MP4 be rendered for motion review. Rejected art must not be animated into a purported completed iteration. No generic aesthetic score substitutes for user visual judgment.

The coding agent must provide a working local review page for every major iteration, paired with a machine-readable `review.json`. The user must be able to see and compare real outputs without reading code.

## Heading

`Visual Mastery — Iteration <id> — <short visual cluster name>`

*Exact original briefs and subjects*. Which film sources supplied relevant visual examples (film name + time ranges, local cropped witness links). Which model/provider and renderer generated the original content. Cost of this iteration. Meaningful baseline. This is not a reconstruction of source footage.

## Show the work

- **Gallery:** 2–4 native or near-native reference witnesses in a local-only view, labeled with the specific visual attribute rather than a generic 'Kurzgesagt' label.
- **Before/after full-resolution:** actual baseline original artwork side-by-side with revised original artwork at the same brief/scene/camera conditions. Let user zoom into details.
- **Motion proof (ONLY AFTER art + asset approval):** actual before/after video players with synchronized playback / timestamp control where possible; one genuine original 12–20s MP4 per approved major animation iteration. List animation states, viewpoint and layer actions.
- **Rotating original:** a different original brief using current skill, not a reworked version of the same character/environment.
- **Unseen challenge:** only after freeze, mark if verified or pending.
- **Change table:** multiple investigated high-impact quality gaps, exact source evidence, what the procedure changed, which pixels/objects/behaviors changed, what worsened or failed, and if this is transferable.
- **Diagnostic:** 3 largest remaining observed deficits PLUS any distinct technical failures; classify observation/skill/provider/asset/renderer/integration/assessment appropriately.
- **Claim level:** `EXECUTABLE`, `IMPROVING`, `TRANSFER_PENDING`, or `TRANSFER_QUALIFIED`, never infer from passing tests.

## Feedback form (functional, persistent)

Required fields: iteration ID; chosen verdict one of `APPROVED_IMPROVEMENT`, `PARTIAL`, `REJECTED`, `NEEDS_EVIDENCE`; user-ranked biggest remaining issues (free text; multiple allowed); optional preferred next visual focus; timestamp. Submit feedback to backend or CLI and atomically commit the review record. Do not fake a saved review by only copying text to clipboard.

## Learning-loop continuation

The next iteration must read and visibly acknowledge all unresolved user feedback by mapping each point to an actual gap card, tested method and outcome. It may reject a proposed correction if evidence contradicts it, but must explain with visual evidence rather than silently ignoring it.

The user must never be asked to approve a numerical metric instead of seeing artwork and moving frames.


## Mandatory ARTWORK review page before video

Display actual full-resolution whole-scene original baseline and skill-guided art at identical original brief; art-quality comparison gallery with local-only film reference witnesses; detailed original character design shown both alone and in scene; face/eyes/mouth/head/hair crop panels; full-body and limb silhouettes; colour/material/finish fit to world; original content brief separate from exact skill-driven prompt text and conditioning images. Show `PromptCompilation` high-impact clause coverage and the strongest observed gaps. User marks `ARTWORK_APPROVED` or `ARTWORK_REJECTED` and ranks multiple visible failures. The system must persist immutable content hashes in approval event, not just a boolean.

## Mandatory CHARACTER/ASSET review page before video

Display approved hero art, original canonical character view, consistent alternate face/pose/hand views, matching costumes/proportions, leg/arm/hand attachments, contact/foot/grip relations, per-layer images and masks, occlusion order, recomposed result compared to canonical image and the actual planned scene actions. Optional tiny diagnostic preview cannot be called qualified animation. User marks `ASSETS_APPROVED` or `ASSETS_REJECTED`, independently from whole-frame art acceptance. If a character is rejected, an environment may remain approved in a separate signed record.

## VIDEO review page after both approvals

Show true MP4, selected original rendered frames, action / focus / camera timeline, character identity and silhouette continuity, background motion, prop contact, perspective changes, baselines, defects and improvements. Preserve existing video review behavior and transfer protocol. Changing any signed art or pack invalidates subsequent approvals.

## Reference/skill clarity

Show which observed source traits are `SOURCE_FACT`, which are hypotheses about `STYLE_MECHANISM`, what original design freedom the generator received, what the actual provider prompt contained, which style clauses reached that request, which failure might come from the model rather than observation, and any missing/unreviewed film frames. Never claim that a film was artistically understood because each decoded frame had a machine index.

## v1.2: evidence-first art decision review (supersedes any obligatory early video render)

Before asking for art approval, show the user: (1) the original new brief; (2) real full-size scene artwork and character design, including detailed face and full-body silhouette; (3) selected professional source witness images with exact source frame IDs and no source imitation; (4) major **visual differences** in ranked connected cluster, not generic adjectives; (5) the **source-derived conditional style decisions** and the production recipe used; (6) the **exact skill-owned image prompt clauses and references** submitted to the provider; (7) full-res outputs and revision attempts; (8) deficiencies separated into observation error, style rule, prompt recipe, provider limit, and character design; (9) provider spend and current full-frame vision coverage. The user can accept world design but reject hero character independently.

Do not force the user to answer dozens of technical questions. Ask one grounded question: **'Which important visual qualities are still missing or wrong?'** Preserve their freeform feedback and the linked original image hashes. A rejection must change the relevant upstream artistic decision or image-production operation; adding an automated check without improving the method is not a valid response.

If no paid image call or full-frame VLM study was authorized, show genuine engineering state and cost estimate, not a fabricated visual packet.
