# Examples

This directory documents the expected input and output structure for the pipeline.

## Minimal input

For each action, place atomic frames into an input directory:

```text
examples/
  input_idle/
    frame_01.png
    frame_02.png
    ...
    frame_08.png
```

## Example processing command

```bash
python post_process.py idle ./examples/input_idle ./examples/output_idle --background-mode rgba --gif
```

## Expected output

```text
examples/
  output_idle/
    frame_01.png
    ...
    frame_08.png
    idle_sheet_aligned.png
    idle_preview.gif
    metadata.json
    alignment_log.txt
```
