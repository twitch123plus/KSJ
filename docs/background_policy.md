# Background Policy

## Priority Order

1. Transparent RGBA background
2. Chroma-key green background
3. Pure black background

## Why

Transparent RGBA is preferred because the alpha channel provides a direct and reliable foreground mask.
Green background is an acceptable fallback when the generator cannot produce a transparent PNG consistently.
Pure black background should only be treated as a preview-oriented fallback because black outlines, clothing,
and weapons can break naive non-black masking.

## Rules

### Transparent RGBA
- Preferred for master assets
- Use alpha channel as the primary segmentation mask
- No halo, no shadow, no glow

### Chroma-key Green
- Use only if transparency is unavailable
- Use a forbidden key color such as `#00FF00`
- Character design and effects must avoid that color
- Use color-distance thresholding, not exact RGB equality only

### Pure Black
- Allowed only as last-resort fallback
- Do not rely on black-background masking as the only segmentation method
- Not recommended for production master assets
