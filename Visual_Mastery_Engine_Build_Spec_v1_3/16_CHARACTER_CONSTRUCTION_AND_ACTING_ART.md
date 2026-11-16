# 16 — Character-first visual manufacture (not tube-rig enforcement)

This section creates the art itself, not merely QA gates. **Character is a whole illustration with related alternate drawings**, not a tree of SVG lines. Use image generation/reference-conditioned edits for distinctive artwork; code coordinates motion, never substitutes low-quality placeholder geometry for the character.

## A. What to investigate in the actual five films

Do **not** start with pixel ratios for one face. The high-impact questions focus on what makes new characters belong in the same art family and retain appeal in motion:

1. **Whole-actor attractiveness**: What visible relationships among the main silhouette, torso/head/appendage masses, costume design, facial region and pose make a character look intentionally illustrated? Compare structurally different characters (humans, mascots, animals where present); what art-design choices transfer and what should vary?
2. **View and identity**: When viewed front/3/4/profile, what remains identifiable? Which head outline, ears/nose/mouth/eyes, body/garment arrangement and visible-side occlusion are redrawn? Is there a source-visible viewpoint exception?
3. **Expression construction**: How do eyebrows, eye opening, pupils/gaze, mouth/cheeks, skull contour, head orientation, hands, shoulders and whole pose combine? Which expression elements are not universal across characters?
4. **Limb visual language**: What makes limbs visually belong to the torso/costume/hand; which joints are hidden by sleeves or pose; how do near/far limbs overlap; how do hands transition from decorative shapes to functional grips? Do not assume tube limbs from a skeleton.
5. **Acting and physical support**: At action anticipation/peak/settle, what changes in body silhouette, foot support, hip/chest relationship, face, hand, costume and prop contact? Which changes are new drawings, which transform continuous parts?
6. **Material/finish coherence**: Does face/garment/body have consistent, role-specific colour and shading treatment when turning or interacting with light?
7. **Scene integration**: Does the character have compatible environment perspective, scale, light, occlusion and focal detail, instead of looking like a pasted sticker?

For EVERY selected high-impact question, study actual full artwork and relevant consecutive source states; contrast unrelated actors/scenes. Report `SOURCE_FACT` separately from transferable conditional `STYLE_DECISION` and real edit/art method. No source-specific head/proportions as universal design constants.

## B. Prevent bad character art at its source

**B1 — Before art generation**: Build typed `CharacterArtPlan` from OriginalBrief + selected character-style skill decisions: original identity, body type, prominent silhouette, proportions **as art relationships not arbitrary source numbers**, attire/hair, view, expression, visible body parts, environment light and upcoming motion states. Fix silhouette and design language through skill-owned visual examples, NOT a generic 'cute scientist' prompt.

**B2 — Canonical whole drawing**: Real image-model call generating a complete appealing original actor (whole body when needed). Preserve full native PNG/WEBP+hash and original design choices. The canonical image is a **real identity reference**, never text alone. If the canonical is weak, revise the **art creation procedure**, not coordinate checks.

**B3 — Plan complete action poses**: Before slicing layers, prepare a state graph with `idle → anticipation → reach → hand contacts prop → reaction/turn → settle` as applicable. For each state specify which whole-body silhouette, balance/support, face, visible arm/hand side, prop and material/lighting relationships must exist. Draw any genuinely changed states as **whole appealing drawings** conditioned on canonical original actor. Avoid independently generating separate random faces/hands.

**B4 — Whole hand/prop design**: Place original hand and prop together as one coherent designed illustration; understand grip, visible digits, occlusion and near/far arms. If model struggles with fingers, use guided region edits or alternate proven producing route. A physically possible arm path isn't evidence of attractive art, and beautiful hand shapes cannot excuse physically impossible contact.

**B5 — Derive layers ONLY AFTER whole poses exist**: Decide the minimum art elements needing independent motion. Extract masks from approved artwork; fill hidden backgrounds/underarms/behind props using separate inpainting/clean-plate operations as needed. For face/hand turns use drawing substitutions if transforms would crush design. When cutting a layer damages finish, use approved full-pose frames and crossfades/state swaps instead of destructive segmentation.

**B6 — Recompose original at same pixels**: Composite layers into their original anchors and compare original rendered character at source resolution for mismatched masks, holes, seams, colour shifts, crop and lighting. This is not an aesthetic check in place of art; it detects mistakes introduced during extraction.

**B7 — Connect drawing states to motion**: Code holds character local coordinate/anchor frames, pose state timing and transitions; prop movement uses contact attachment constraints or synchronized whole-pose art. Whole-body states and camera world transforms are separate. No leg/hand snapping at state change.

## C. Required character asset family

`CharacterIdentity`: original subject name/id, approved canonical image hash, fixed design descriptors (content), selected frozen style skill hash, body/face design view, baseline bounding box, original story attributes.

`CharacterState`: state id, view angle class, emotion/gesture/pose, full-size image hash, image route/conditioning references, character-local anchors, near/far visible side, held props, world light state, comparison to canonical identity.

`ArtLayer`: image hash; `RGBA` or opaque texture mode; mask hash; local origin; natural size; pivot anchor; body owner; z-order; parent transform; whether occluded content has a valid fill; state applicability; reference to source composite and character family. Alpha must be verified from pixels, never presumed from file extension.

`Contact`: `actor_id`, `hand_side`, `prop_id`, anchor in character-local and prop-local coordinates, intended visible contact region, near/far/occlusion relation, event interval, approved hand+prop drawing state or tracking strategy.

`StateTransition`: from/to art hashes, timing key, whether transforms or substitution, how parts and parent/world/camera transforms change, interpolation limitations and required new drawings.

`CharacterPack`: immutable list of all above + pixel-size and scene placement contract. Reuse canonical+related art, do not derive fresh actor identities from unconstrained text at each frame.

## D. Anti-failure art strategies based on the cause

| Visible defect | Producing method to change FIRST |
|---|---|
| Generic/ugly actor even before motion | Whole-character art skill: identity/design references and high-impact silhouette/detail construction route |
| Actor identity changes with view | Canonical image conditioning, paired view sheet, targeted edit and model/provider route |
| Dead/sticker expression | Expression+head/torso/gesture drawing family, not only animating eye points |
| Tube arms / mitten hands | Change source-conditioned whole acting-pose art and original hand/prop construction, not just solver constraints |
| Impossible reach/contact | Design full interaction pose with prop placement and near/far sides before parts, then implement attachment |
| Legs slide despite nice art | Fix body world motion/support events and coordinated full pose sequence |
| Head/hand clipped or layered wrongly | Repair artwork canvas, transforms, occlusion and state-specific z order at asset-contract stage |
| Paper-cut seams after segmentation | Improve segmentation+inpaint or abandon destructive layers for full-state drawings |
| Too simplistic character compared with source | Investigate the **artistic quality gap** and change construction/edit method and references, not simply add decorative pieces |

## E. First integrated cluster must include characters

The first two *meaningful visual cycles* must give conspicuous time to character art, face and whole-body silhouette, gesture and layered interaction, alongside richly designed worlds. A cycle can stop at full art review if quality is poor; do not force video. Do not promise mastery in two attempts. Actual image/art results are the evidence. The initial offline build ZIP must prove it *can* produce the correct plan, compile pose requests and track family dependencies, even though no real art may exist yet.
