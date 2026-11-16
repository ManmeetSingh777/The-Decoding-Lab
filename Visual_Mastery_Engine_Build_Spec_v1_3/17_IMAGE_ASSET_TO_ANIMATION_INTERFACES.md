# 17 — Actual image bytes to a correct rendered scene: pixel, layer, and motion contract

## Purpose

Runware's image model returns **raster pixels**; image output should ordinarily be **lossless PNG** or suitable WEBP, never assumed SVG. PNG does not imply transparent background or independent layers. The animated scene must be planned BEFORE image generation so the necessary artwork can be requested, derived and tracked. Don't force every scenic asset into a puppet or vector rig.

## 1. Make a shot visual-state plan first

Each planned original shot needs `SceneArtPlan` with: output frame dimensions; desired asset render resolution; whole scene start/completion art; focal content; subjects/props; scene camera; relevant foreground-midground-background relationships; drawing states and poses that will change; independently moving elements; occlusion/contact; world/scene transformations; palette/material treatment skill IDs; full-scene and character identity anchors. This originates from original brief + production skills; no untracked style defaults.

## 2. Provider asset contract

For each image generation/edit node include:

`asset_id`, `operator_id`, `skill_rule_ids`, `original_subject_id`, `kind=WHOLE_SCENE|CHARACTER_CANONICAL|CHARACTER_STATE|PROP|LAYER|CLEAN_PLATE|MASK|EFFECT`, `pixel_width`, `pixel_height`, `color_profile`, `alpha_expectation`, `reference_image_ids_and_roles`, `view_class`, `pose_state`, `natural_bounds`, `padding_policy`, `placement_target`, `identity_lock`, `provider_payload_sha`, `output_sha`, `transform_origin`, `depth/layer_order`, `compatible_states`, `delivery_format`, `editability_level`.

Use a dedicated scene coordinate space (e.g. 1920×1080 output) and record mapping for every generated image. Verify provider's allowed increments first; 1080 might be disallowed if model requires multiples of 16. If generating 1536×864 (both multiples of 16), a uniform scale maps it to 1920×1080; record actual scale and asset-specific placement. If generating 1920×1088, crop/position explicitly, don't silently stretch to 1920×1080. No hardcoded one-size-fits-all choice.

## 3. After the real image returns

1. Save unmodified bytes, verify decodable file, dimensions, colour mode, alpha-channel presence *and actual non-opaque alpha pixels*.
2. Detect provider task error and record request/task IDs, model, seed/settings if supplied, cost and raw response without secrets.
3. Associate image with exact original brief, skill version, conditional decision IDs, reference-image hashes and provider operation type.
4. If image is flattened opaque art, leave it a whole-scene composite until a separate producing operation generates extractable layers, alternate drawing states, or masks; never label opaque PNG `transparent` because it uses the PNG format.
5. For segmentation: create `mask` at identical pixel dimensions; record parent composite and coordinate transform; generate clean plate/occluded body fill with actual edit/inpaint if the part moves away.
6. For alpha: store premultiplied/straight-alpha convention, padding/bleed and color profile; wrong convention can create bright seams. Use one convention throughout and test output.
7. For view/pose state: preserve canonical character identity and natural frame, separate illustrated state from world transform so sprites don't jump when swapped.
8. Build an `AssetManifest` with SHA256 links; verify all objects referenced by the renderer exist and decode.

## 4. Layer, sprite, and camera relationships

The renderer's `SceneGraph` contains `world`, `camera`, `characters`, `props`, `backgrounds`, `effects`. Each actor has stable `character_local` coordinates. Each layer has a local transform relative to its owner and its own art state, not independently invented absolute screen positions. For character hand + held prop, specify shared event interval and attachment/occlusion; do not move a hand without moving or releasing its prop. Camera motion is a transform of the world view, not a deformation of source art. Where source-like viewpoint changes demand redraw, switch to approved alternate drawings with coordinated silhouette, light and face changes.

`MotionEvent`: event id, start/end times, actors and affected parts, required drawing states, interpolated transforms, dependent prop relationships, camera impact, attention/focus constraint, and sound/narration cue if provided by Director later. The visual-mastery engine may use an original predefined scene brief without autonomously inventing full narrative direction.

## 5. Recomposition and delivery before animation

Given a canonical artwork composite and proposed layers, reconstruct at the same resolution. Record holes, seams, wrong stacking, masks, clipping, part discontinuity and diff image. Replace producing asset method if visibly destructive. For animation preview, render diagnostic movement of only approved/explicitly experimental artwork; **no full film production after rejected art**. Include pose contact and camera/scale changes in the first meaningful motion sample.

## 6. Tool routing

- Image creation/editing: Runware account + a verified exact model AIR ID, with approved paid use, skill-owned prompt/reference/operation program.
- Complex character/scene artwork: image model, not new SVG basic-shape drawings or artificial reconstruction of artist strokes from coordinate counts.
- Masking, matte, alpha, clean plate: verified image processing/model operations, not transparencies fabricated by a filename.
- Animation: Remotion for programmatic scene composition and transitions; FFmpeg for encode, probes and proof frames. HyperFrames is optional only if verified installed and *needed*, not an architecture dependency.
- Files: keep original artwork, intermediate states and final frames; don't discard alternate drawings after video export.

## 7. Mandatory engineering failures to inject

Opaque PNG passed as transparent; mask wrong size; source asset changed after approval; missing clean plate; pose image with different canvas/bounds; contact anchor inconsistent; left/right arm swapped; erroneous z-order; parent world scale applied twice; image generation dimension not allowed; provider response URL expires; image adapter returns HTTP success with invalid bytes; render consumes unapproved art; part move creates visible hole. Each failure should result in explicit diagnosis and a producing-method correction path, not silent success.
