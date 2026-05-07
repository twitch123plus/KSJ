# Validation Rules

## Structural Checks
- Correct frame count
- Uniform frame size
- No text, labels, UI, borders, or grid
- No cross-frame bleeding
- Character remains inside safe box
- No severe edge truncation

## Consistency Checks
- Same character identity across frames
- Stable scale within allowed variance
- Palette drift below threshold
- Weapon and accessory persistence

## Alignment Checks
- Torso anchor jitter below per-action threshold
- Foot baseline jitter below threshold when action is grounded
- Bounding-box area variance within allowed range

## Anomaly Checks
- Empty-frame detection
- Near-empty-frame detection
- Outlier pixel-count detection

## Suggested Default Thresholds

```json
{
  "idle": {
    "torso_anchor_x_stddev_px": 2,
    "foot_baseline_y_stddev_px": 1,
    "bbox_area_variance_pct": 12
  },
  "run": {
    "pelvis_y_stddev_px": 3,
    "bbox_area_variance_pct": 20
  },
  "attack": {
    "torso_anchor_x_stddev_px": 4,
    "bbox_area_variance_pct": 25
  },
  "hurt": {
    "torso_anchor_x_stddev_px": 4,
    "bbox_area_variance_pct": 25
  }
}
```
