# Character Sprite GIF Pipeline

## Purpose

This skill turns a short character prompt into a production-oriented 2D pixel-art animation package.

Primary goals:

1. Generate one canonical base character reference.
2. Generate action animations as individual frames, not as a single wide strip.
3. Align frames using deterministic post-processing.
4. Export aligned PNG frame sequences and aligned sprite sheets.
5. Optionally export preview GIFs.
6. Prefer stable, reusable game assets over presentation images.

Default actions:

- `idle`
- `attack`
- `run`
- `hurt`

Primary objective: **deliver aligned sprite assets first, preview GIFs second**.

---

## Invocation

Use this skill when the user provides a character prompt and wants automatic sprite animation output.

Example user prompt:

```text
small chibi anime man, red eyes, round head, compact body, short limbs,
brown and cream fur, fluffy tail, cute but focused expression,
clean readable silhouette, pixel-friendly
```

Expected default outputs:

```text
/output/
  base_reference.png

  idle/
    frame_01.png
    frame_02.png
    ...
    frame_08.png
    idle_sheet_aligned.png
    idle_preview.gif

  attack/
    frame_01.png
    frame_02.png
    ...
    frame_08.png
    attack_sheet_aligned.png
    attack_preview.gif

  run/
    frame_01.png
    frame_02.png
    ...
    frame_08.png
    run_sheet_aligned.png
    run_preview.gif

  hurt/
    frame_01.png
    frame_02.png
    ...
    frame_08.png
    hurt_sheet_aligned.png
    hurt_preview.gif

  metadata.json
  alignment_log.txt
```

---

## Core Rules

### Do

- Generate a canonical base character first.
- Use the base character as the identity reference for all later frames.
- Generate one frame at a time.
- Assemble sprite sheets programmatically after generation.
- Prefer transparent RGBA backgrounds.
- Use deterministic post-processing for alignment.
- Export aligned PNG assets even if the user also wants GIFs.
- Treat GIFs as preview outputs, not the master assets.
- Reject invalid generations instead of trying to salvage everything.

### Do Not

- Do not generate a full multi-frame sprite sheet in one prompt unless the user explicitly demands it.
- Do not create presentation boards.
- Do not add text, frame numbers, labels, UI, grids, borders, or captions.
- Do not rely on pure black background as the only segmentation strategy.
- Do not skip validation before export.
- Do not deliver only GIFs when the user asked for production-ready sprite assets.
- Do not assume one alignment rule works equally well for every action.

---

## Default Output Contract

Unless the user explicitly requests otherwise, produce:

```text
/output/
  base_reference.png

  idle/frame_01.png ... idle/frame_08.png
  attack/frame_01.png ... attack/frame_08.png
  run/frame_01.png ... run/frame_08.png
  hurt/frame_01.png ... hurt/frame_08.png

  idle/idle_sheet_aligned.png
  attack/attack_sheet_aligned.png
  run/run_sheet_aligned.png
  hurt/hurt_sheet_aligned.png

  idle/idle_preview.gif
  attack/attack_preview.gif
  run/run_preview.gif
  hurt/hurt_preview.gif

  metadata.json
  alignment_log.txt
```

If the user asks only for GIFs, still generate aligned frames internally first, then return only the GIF links in the final response.

---

## Background Policy

Use this priority order:

1. **Transparent RGBA background** — preferred.
2. **Chroma-key green background** — acceptable fallback if transparent output is unavailable.
3. **Pure black background** — allowed only as a fallback or preview background, not preferred for segmentation.

### Why

- Transparent RGBA provides the cleanest mask via alpha channel.
- Chroma-key green is usually more reliable than black for segmentation.
- Pure black can collide with black outlines, shadows, clothing, or weapons.

If transparency is available, use it.

If transparency is not available, use chroma-key green and explicitly forbid green on the character body and effects.

---

## Default Technical Specification

Use this unless the user overrides it:

```text
Frame canvas:
- 320x320 per frame
- 8 frames per default action
- side view facing right unless the user specifies otherwise

Master asset format:
- RGBA PNG
- transparent background preferred
- sharp pixel edges
- no blur
- no glow
- no antialiasing halo

Character framing:
- character occupies roughly 35% to 40% of frame height
- character occupies roughly 35% to 40% of frame width
- large empty margin around the body
- character remains inside a fixed central safe area
- no overflow to frame edges

Sheet assembly:
- one horizontal row
- assembled programmatically from aligned frames
- each frame preserves exact frame dimensions
```

---

## Frame Count Policy

Default frame counts:

```json
{
  "idle": 8,
  "attack": 8,
  "run": 8,
  "hurt": 8
}
```

Recommended flexible ranges:

- `idle`: 6 to 8
- `attack`: 8 to 10
- `run`: 8
- `hurt`: 6 to 8

If the downstream pipeline requires a uniform count, keep all actions at 8.

---

## Generation Strategy

## 1. Base Character Reference

Generate a single canonical base reference first.

Template:

```text
Create a single base character reference image.

Subject:
{USER_CHARACTER_PROMPT}

Requirements:
- one full-body character only
- no sprite sheet
- no presentation board
- no labels, text, UI, grid, frame numbers, or captions
- side view facing right unless the user specifies otherwise
- clean pixel art
- sharp edges
- 32-bit sprite style
- transparent background preferred
- centered with large empty space
- compact game-sprite-friendly silhouette

Purpose:
This is the canonical identity reference for all later animation frames.
Preserve identity, palette, silhouette, proportions, hairstyle, outfit,
weapons, accessories, ears, tail, and facial expression.
```

---

## 2. Keyframe-First Generation

Do not start by generating all frames blindly.

For each action:

1. Generate the canonical keyframes first.
2. Validate them.
3. Generate in-between frames using the base reference and adjacent keyframes.

### Default keyframe plan

#### Idle
1. ready idle
2. bob down
3. bob up
4. blink or subtle twitch

#### Attack
1. anticipation
2. wind-up peak
3. impact
4. recovery

#### Run
1. contact
2. passing
3. opposite contact
4. opposite passing

#### Hurt
1. ready
2. impact reaction
3. recoil or stunned peak
4. recovery

---

## 3. Per-Frame Generation Constraints

Each generated frame should follow these rules:

```text
- exactly one character
- transparent RGBA background preferred
- same scale as the canonical base
- same camera angle
- same silhouette family
- no text, labels, borders, grid, UI, or showcase layout
- no frame-to-frame identity mutation
- no extra characters
- no presentation formatting
```

If the image model cannot produce transparency reliably, use chroma-key green instead.

---

## 4. Assembly Strategy

After frame generation:

1. Validate each frame.
2. Align frames using deterministic post-processing.
3. Save aligned PNG frame sequence.
4. Assemble aligned frames into a horizontal sprite sheet.
5. Export preview GIF only after alignment.

Never treat the one-shot generated wide sheet as the primary generation method.

---

## Alignment Policy

Different actions require different alignment priorities.

### Anchor hierarchy

Use this fallback order when computing alignment anchors:

1. planted foot baseline
2. torso / pelvis anchor
3. head center sanity check
4. bounding box fallback

### Action-specific rules

#### Idle
- primary: feet + torso
- expected motion: minimal vertical drift
- goal: stable standing loop

#### Run
- primary: torso / center of mass
- feet can alternate and leave the ground
- allow moderate vertical oscillation

#### Attack
- primary: torso
- secondary: planted foot when grounded
- effects must not dominate anchor estimation

#### Hurt
- primary: torso
- feet only matter if the pose is still grounded
- airborne or recoiling frames should not be forced to a fake grounded baseline

---

## Segmentation Policy

Preferred mask extraction order:

1. alpha channel from RGBA PNG
2. chroma-key green mask
3. black-background fallback mask

### Important notes

- Black-only masking is fragile when the character has black outlines, clothing, or weapons.
- Green-screen fallback requires forbidding key-green on the character body and effects.
- Detached effects should be excluded from anchor estimation whenever possible.

---

## Validation Rules

All actions must pass deterministic validation before export.

### Structural checks

- correct frame count
- correct frame dimensions
- no text, labels, UI, grid, or borders
- no cross-frame bleeding
- no edge truncation
- sprite remains inside safe box

### Consistency checks

- identity consistency
- stable scale
- palette continuity
- accessory persistence
- weapon consistency

### Alignment checks

- torso anchor jitter below threshold
- foot baseline jitter below threshold when applicable
- bounding-box area variance within allowed range

### Anomaly checks

- empty frame detection
- near-empty frame detection
- anomalous pixel-count detection

---

## Failure Taxonomy

### F1 — Presentation contamination
Generated image contains labels, UI, borders, text, or showcase layout.

**Fix**
- reject affected action
- strengthen negative prompt
- regenerate the affected action or frames only

### F2 — Layout invalid
Frame count, spacing, or per-frame geometry is invalid.

**Fix**
- reject assembly
- regenerate or reassemble from atomic frames

### F3 — Identity drift
Palette, face, body proportions, weapon, or accessories drift between frames.

**Fix**
- regenerate from canonical base reference
- tighten reference conditioning
- shorten generation span

### F4 — Segmentation failure
Mask misses body parts or captures background noise.

**Fix**
- switch to alpha-based mask
- use green-screen fallback if needed
- avoid black-only mask unless no better option exists

### F5 — Alignment instability
Feet bounce or torso drifts unnaturally.

**Fix**
- re-run alignment using the action-specific anchor policy
- mask out detached effects

### F6 — Effect overflow
Slash arcs, sparks, or hit effects dominate the bbox or exceed the safe box.

**Fix**
- reduce effect size
- exclude effects during alignment
- regenerate only affected frames when needed

### F7 — Palette flicker
Preview GIF flashes because frames quantize differently.

**Fix**
- compute a shared palette for all frames
- keep PNG frames as master assets

### F8 — Empty or anomalous frame
A frame is nearly blank or has extreme pixel-count drift.

**Fix**
- fail validation
- regenerate the anomalous frame

---

## Post-Processing Contract

Post-processing should:

1. normalize frame size using nearest-neighbor only
2. compute segmentation masks
3. estimate per-frame torso anchor and lower-bound baseline
4. validate action stability
5. translate frames into aligned positions
6. export aligned frames
7. export aligned horizontal sheet
8. export preview GIF from aligned frames
9. write metadata and alignment logs

Do not smooth pixel art during normalization.

---

## Quality Checklist

Before final delivery, verify:

- [ ] Base reference exists
- [ ] Frames were generated individually
- [ ] No presentation board exists
- [ ] No labels, text, UI, borders, or grids
- [ ] Aligned PNG frames exist
- [ ] Aligned sprite sheets exist
- [ ] GIFs, if requested, were generated from aligned frames
- [ ] Background policy was followed
- [ ] Validation passed for each action
- [ ] Alignment logs and metadata were written

---

## Final Response Template

If the user wants full asset delivery:

```text
已完成：

PNG Frames:
[idle frames](...)
[attack frames](...)
[run frames](...)
[hurt frames](...)

Aligned Sprite Sheets:
[idle sheet](...)
[attack sheet](...)
[run sheet](...)
[hurt sheet](...)

Preview GIFs:
[idle GIF](...)
[attack GIF](...)
[run GIF](...)
[hurt GIF](...)
```

If the user only asks for GIF delivery, return only the GIF links after aligned internal processing is complete.

---

## Failure Recovery

If generation returns a showcase board, text, or multi-character layout:

1. reject the generation
2. regenerate only the affected frames or action
3. strengthen negative constraints:

```text
Do not create a presentation board.
Do not add text, labels, captions, UI, borders, grid lines, or showcase layout.
Generate only one single character frame.
```

If alignment is poor:

1. re-run alignment with action-specific anchor rules
2. switch to alpha-based segmentation if possible
3. exclude effects from anchor estimation
4. regenerate only failed frames if validation still fails

If GIF flickers:

1. keep PNG frames as the master output
2. rebuild the GIF with a shared palette derived from all aligned frames

---

## Output Priority Reminder

The correct priority order is:

1. aligned PNG frames
2. aligned sprite sheet PNG
3. metadata and logs
4. preview GIF

This skill exists to create **stable sprite assets**, not just animated previews.
