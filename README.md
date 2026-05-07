# Character Sprite GIF Pipeline

Production-oriented skill for turning a short character prompt into reusable 2D pixel-art animation assets.

This repo is designed for stable sprite generation, not showcase boards. It prioritizes:

- canonical character consistency
- per-frame generation instead of one-shot wide sheets
- deterministic alignment and validation
- aligned PNG assets first, preview GIFs second

## What it does

Given a character prompt, the pipeline will:

1. Generate one canonical base character reference.
2. Generate action animations as individual frames.
3. Align frames with deterministic post-processing.
4. Assemble aligned sprite sheets programmatically.
5. Export preview GIFs if needed.
6. Produce logs and metadata for downstream use.

Default actions:

- `idle`
- `attack`
- `run`
- `hurt`

## Why this approach

Most image models are not reliable at producing a strict multi-frame sprite sheet in one pass. Wide-sheet generation often causes:

- identity drift across frames
- broken spacing or merged frames
- center-frame distortion
- unstable feet and body alignment
- presentation-board contamination

This repo avoids that by using keyframe-first, atomic frame generation and then stitching frames with deterministic code.

## Background priority

1. Transparent RGBA background
2. Chroma-key green fallback
3. Black background only as last resort

## Output priority

PNG is the master asset. GIF is a preview format.

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run post-processing for one action:

```bash
python post_process.py idle ./examples/input_idle ./examples/output_idle --background-mode rgba --gif
```

Run tests:

```bash
pytest
```

## Repository contents

- `SKILL.md` — full skill specification and operational contract
- `post_process.py` — deterministic frame alignment, validation, and export
- `docs/` — background policy, failure taxonomy, validation rules
- `prompts/` — reusable prompt templates by stage and action
- `examples/` — minimal examples and expected directory layout
- `tests/` — basic regression tests for masks, alignment, and validation

## Suggested workflow

1. Create the canonical base character.
2. Generate keyframes for an action.
3. Generate in-between frames.
4. Save atomic frames as `frame_01.png` through `frame_08.png`.
5. Run `post_process.py`.
6. Review `metadata.json`, `alignment_log.txt`, aligned sheets, and preview GIFs.

## License

This repository uses the MIT License.
