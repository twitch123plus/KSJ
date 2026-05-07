# Failure Taxonomy

## F1 — Presentation contamination
Generated image contains text, labels, UI, borders, or showcase layout.

**Fix**
- Reject affected action
- Strengthen negative prompt
- Regenerate only the failed action or frame set

## F2 — Layout invalid
Frame count is wrong, widths are inconsistent, or frames bleed into each other.

**Fix**
- Reject sheet assembly
- Reassemble from atomic frames or regenerate affected frames

## F3 — Identity drift
Face, palette, accessories, weapon shape, or silhouette changes between frames.

**Fix**
- Re-run from canonical reference
- Increase reference conditioning strength
- Reduce frame-span generation scope

## F4 — Segmentation failure
Foreground mask misses body parts or includes background noise.

**Fix**
- Prefer RGBA alpha mask
- Fall back to green-screen chroma key
- Do not rely on black-only masking unless no better option exists

## F5 — Alignment instability
Feet bounce, torso drifts, or center anchor jitters unnaturally.

**Fix**
- Re-run alignment with action-specific anchor rules
- Exclude detached effects from anchor estimation

## F6 — Effect overflow
Slash arcs, sparks, or hit effects dominate bbox or exceed safe box.

**Fix**
- Reduce effect size in prompt
- Mask effects during alignment
- Regenerate only affected frames when necessary

## F7 — Palette flicker
GIF preview flashes because frames quantize differently.

**Fix**
- Use a shared palette derived from all frames
- Keep PNG frames as master assets

## F8 — Empty or anomalous frame
A frame is nearly blank or has an outlier pixel count.

**Fix**
- Flag frame in validation
- Reject and regenerate the anomalous frame
