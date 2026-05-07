from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Literal

import numpy as np
from PIL import Image

FrameMode = Literal["rgba", "green", "black"]
ActionName = Literal["idle", "attack", "run", "hurt"]

FRAME_WIDTH = 320
FRAME_HEIGHT = 320
DEFAULT_TARGET_SIZE = (128, 128)
GREEN_KEY = (0, 255, 0)


@dataclass
class FrameMetrics:
    frame_index: int
    bbox: tuple[int, int, int, int] | None
    anchor_x: float | None
    anchor_y: float | None
    foot_y: float | None
    alpha_pixels: int
    bbox_area: int
    shift_x: int = 0
    shift_y: int = 0


@dataclass
class ValidationResult:
    passed: bool
    failures: list[str]
    metrics: dict


@dataclass
class ProcessConfig:
    frame_width: int = FRAME_WIDTH
    frame_height: int = FRAME_HEIGHT
    target_size: tuple[int, int] = DEFAULT_TARGET_SIZE
    frame_count: int = 8
    background_mode: FrameMode = "rgba"
    green_tolerance: int = 35
    alpha_threshold: int = 64
    black_threshold: int = 10
    export_gif: bool = True
    gif_duration_ms: int = 110


ACTION_POLICY: dict[str, dict] = {
    "idle": {
        "primary_anchor": "feet_and_torso",
        "max_x_jitter": 2.0,
        "max_y_jitter": 1.5,
        "max_area_variance_pct": 12.0,
    },
    "run": {
        "primary_anchor": "torso",
        "max_x_jitter": 3.0,
        "max_y_jitter": 3.0,
        "max_area_variance_pct": 20.0,
    },
    "attack": {
        "primary_anchor": "torso",
        "max_x_jitter": 4.0,
        "max_y_jitter": 4.0,
        "max_area_variance_pct": 25.0,
    },
    "hurt": {
        "primary_anchor": "torso",
        "max_x_jitter": 4.0,
        "max_y_jitter": 4.0,
        "max_area_variance_pct": 25.0,
    },
}


def ensure_rgba(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img = img.convert("RGBA")
    if img.size != size:
        img = img.resize(size, Image.Resampling.NEAREST)
    return img


def alpha_mask(img: Image.Image, alpha_threshold: int = 64) -> np.ndarray:
    arr = np.array(img.convert("RGBA"))
    return arr[:, :, 3] >= alpha_threshold


def green_mask(img: Image.Image, key: tuple[int, int, int] = GREEN_KEY, tolerance: int = 35,
               alpha_threshold: int = 1) -> np.ndarray:
    arr = np.array(img.convert("RGBA"))
    rgb = arr[:, :, :3].astype(np.int16)
    key_arr = np.array(key, dtype=np.int16)
    dist = np.linalg.norm(rgb - key_arr, axis=2)
    alpha = arr[:, :, 3]
    return (dist > tolerance) & (alpha >= alpha_threshold)


def black_mask(img: Image.Image, black_threshold: int = 10, alpha_threshold: int = 1) -> np.ndarray:
    arr = np.array(img.convert("RGBA"))
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    return (np.any(rgb > black_threshold, axis=2)) & (alpha >= alpha_threshold)


def get_mask(img: Image.Image, cfg: ProcessConfig) -> np.ndarray:
    if cfg.background_mode == "rgba":
        return alpha_mask(img, cfg.alpha_threshold)
    if cfg.background_mode == "green":
        return green_mask(img, GREEN_KEY, cfg.green_tolerance, cfg.alpha_threshold)
    if cfg.background_mode == "black":
        return black_mask(img, cfg.black_threshold, cfg.alpha_threshold)
    raise ValueError(f"Unsupported background mode: {cfg.background_mode}")


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def safe_percentile(values: np.ndarray, p: float) -> float | None:
    if values.size == 0:
        return None
    return float(np.percentile(values, p))


def estimate_torso_anchor(mask: np.ndarray) -> tuple[float | None, float | None]:
    bbox = bbox_from_mask(mask)
    if bbox is None:
        return None, None
    x1, y1, x2, y2 = bbox
    xs = np.where(mask)[1]
    ys = np.where(mask)[0]
    if xs.size == 0:
        return None, None

    width = max(1, x2 - x1)
    height = max(1, y2 - y1)
    center_band = (xs >= x1 + 0.25 * width) & (xs <= x1 + 0.75 * width)
    mid_band = (ys >= y1 + 0.25 * height) & (ys <= y1 + 0.70 * height)
    selector = center_band & mid_band

    if np.any(selector):
        ax = float(np.median(xs[selector]))
        ay = float(np.median(ys[selector]))
        return ax, ay

    return float(np.median(xs)), float(np.median(ys))


def estimate_lower_bound(mask: np.ndarray) -> float | None:
    ys = np.where(mask)[0]
    return safe_percentile(ys, 95)


def translate_rgba(img: Image.Image, dx: int, dy: int, size: tuple[int, int]) -> Image.Image:
    src = np.array(img.convert("RGBA"))
    out = np.zeros((size[1], size[0], 4), dtype=np.uint8)

    src_x1 = max(0, -dx)
    src_y1 = max(0, -dy)
    src_x2 = min(size[0], size[0] - dx)
    src_y2 = min(size[1], size[1] - dy)

    dst_x1 = max(0, dx)
    dst_y1 = max(0, dy)
    dst_x2 = dst_x1 + max(0, src_x2 - src_x1)
    dst_y2 = dst_y1 + max(0, src_y2 - src_y1)

    if src_x2 > src_x1 and src_y2 > src_y1:
        out[dst_y1:dst_y2, dst_x1:dst_x2] = src[src_y1:src_y2, src_x1:src_x2]

    return Image.fromarray(out, mode="RGBA")


def compute_metrics(frame: Image.Image, frame_index: int, cfg: ProcessConfig) -> FrameMetrics:
    mask = get_mask(frame, cfg)
    bbox = bbox_from_mask(mask)
    anchor_x, anchor_y = estimate_torso_anchor(mask)
    foot_y = estimate_lower_bound(mask)
    alpha_pixels = int(mask.sum())
    bbox_area = 0 if bbox is None else int((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
    return FrameMetrics(
        frame_index=frame_index,
        bbox=bbox,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        foot_y=foot_y,
        alpha_pixels=alpha_pixels,
        bbox_area=bbox_area,
    )


def validation_thresholds(action: str) -> dict:
    if action not in ACTION_POLICY:
        raise ValueError(f"Unsupported action: {action}")
    return ACTION_POLICY[action]


def validate_metrics(metrics: list[FrameMetrics], action: str, frame_size: tuple[int, int]) -> ValidationResult:
    thresholds = validation_thresholds(action)
    failures: list[str] = []

    valid = [m for m in metrics if m.bbox is not None and m.alpha_pixels > 0]
    if len(valid) != len(metrics):
        failures.append("empty_or_undetected_frame")

    if valid:
        anchor_xs = np.array([m.anchor_x for m in valid if m.anchor_x is not None], dtype=float)
        anchor_ys = np.array([m.anchor_y for m in valid if m.anchor_y is not None], dtype=float)
        areas = np.array([m.bbox_area for m in valid], dtype=float)

        x_jitter = float(np.std(anchor_xs)) if anchor_xs.size else math.inf
        y_jitter = float(np.std(anchor_ys)) if anchor_ys.size else math.inf
        area_median = float(np.median(areas)) if areas.size else 0.0
        area_variance_pct = 0.0
        if area_median > 0:
            area_variance_pct = float(np.max(np.abs(areas - area_median)) / area_median * 100.0)

        if x_jitter > thresholds["max_x_jitter"]:
            failures.append("anchor_x_jitter_too_high")
        if y_jitter > thresholds["max_y_jitter"]:
            failures.append("anchor_y_jitter_too_high")
        if area_variance_pct > thresholds["max_area_variance_pct"]:
            failures.append("bbox_area_variance_too_high")

        for m in valid:
            x1, y1, x2, y2 = m.bbox
            if x1 <= 0 or y1 <= 0 or x2 >= frame_size[0] or y2 >= frame_size[1]:
                failures.append("touches_frame_edge")
                break
    else:
        x_jitter = y_jitter = area_variance_pct = math.inf

    return ValidationResult(
        passed=not failures,
        failures=failures,
        metrics={
            "x_jitter": None if not valid else x_jitter,
            "y_jitter": None if not valid else y_jitter,
            "area_variance_pct": None if not valid else area_variance_pct,
        },
    )


def target_anchor(metrics: list[FrameMetrics], action: str) -> tuple[float | None, float | None]:
    policy = ACTION_POLICY[action]
    xs = [m.anchor_x for m in metrics if m.anchor_x is not None]
    ys = [m.anchor_y for m in metrics if m.anchor_y is not None]
    feet = [m.foot_y for m in metrics if m.foot_y is not None]

    tx = float(np.median(xs)) if xs else None

    if policy["primary_anchor"] == "feet_and_torso" and feet:
        ty = float(np.median(feet))
    else:
        ty = float(np.median(ys)) if ys else None

    return tx, ty


def align_frames(frames: list[Image.Image], action: ActionName, cfg: ProcessConfig) -> tuple[list[Image.Image], list[FrameMetrics], ValidationResult]:
    metrics = [compute_metrics(fr, idx + 1, cfg) for idx, fr in enumerate(frames)]
    validation = validate_metrics(metrics, action, (cfg.frame_width, cfg.frame_height))
    tx, ty = target_anchor(metrics, action)

    aligned_frames: list[Image.Image] = []
    for frame, m in zip(frames, metrics):
        dx = dy = 0
        if tx is not None and m.anchor_x is not None:
            dx = int(round(tx - m.anchor_x))
        if ty is not None:
            if ACTION_POLICY[action]["primary_anchor"] == "feet_and_torso" and m.foot_y is not None:
                dy = int(round(ty - m.foot_y))
            elif m.anchor_y is not None:
                dy = int(round(ty - m.anchor_y))

        translated = translate_rgba(frame, dx, dy, (cfg.frame_width, cfg.frame_height))
        m.shift_x = dx
        m.shift_y = dy
        aligned_frames.append(translated)

    return aligned_frames, metrics, validation


def save_frames(frames: list[Image.Image], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, fr in enumerate(frames, start=1):
        fr.save(out_dir / f"frame_{i:02d}.png")


def assemble_sheet(frames: list[Image.Image]) -> Image.Image:
    if not frames:
        raise ValueError("No frames to assemble")
    fw, fh = frames[0].size
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        sheet.alpha_composite(fr, (i * fw, 0))
    return sheet


def shared_palette_frames(frames: list[Image.Image]) -> list[Image.Image]:
    if not frames:
        return []
    sheet = assemble_sheet(frames)
    pal_ref = sheet.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
    palette = pal_ref.getpalette()
    pal_frames = []
    for fr in frames:
        p = fr.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        p.putpalette(palette)
        pal_frames.append(p)
    return pal_frames


def save_gif(frames: list[Image.Image], output_path: Path, duration: int = 110) -> None:
    pal_frames = shared_palette_frames(frames)
    if not pal_frames:
        return
    pal_frames[0].save(
        output_path,
        save_all=True,
        append_images=pal_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=False,
    )


def write_logs(metrics: list[FrameMetrics], validation: ValidationResult, out_dir: Path, action: str) -> None:
    log_lines = [f"action: {action}", f"passed: {validation.passed}"]
    if validation.failures:
        log_lines.append("failures:")
        for f in validation.failures:
            log_lines.append(f"- {f}")
    log_lines.append("")
    for m in metrics:
        log_lines.append(
            f"frame {m.frame_index}: bbox={m.bbox}, anchor=({m.anchor_x},{m.anchor_y}), "
            f"foot_y={m.foot_y}, alpha_pixels={m.alpha_pixels}, area={m.bbox_area}, "
            f"shift=({m.shift_x},{m.shift_y})"
        )
    (out_dir / "alignment_log.txt").write_text("\n".join(log_lines), encoding="utf-8")


def write_metadata(metrics: list[FrameMetrics], validation: ValidationResult, out_dir: Path, action: str) -> None:
    data = {
        "action": action,
        "validation": asdict(validation),
        "frames": [asdict(m) for m in metrics],
    }
    (out_dir / "metadata.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_frames_from_dir(input_dir: Path, cfg: ProcessConfig) -> list[Image.Image]:
    files = sorted(input_dir.glob("frame_*.png"))
    if len(files) != cfg.frame_count:
        raise ValueError(f"Expected {cfg.frame_count} frames in {input_dir}, found {len(files)}")
    return [ensure_rgba(Image.open(p), (cfg.frame_width, cfg.frame_height)) for p in files]


def process_action(input_dir: Path, output_dir: Path, action: ActionName, cfg: ProcessConfig | None = None) -> ValidationResult:
    cfg = cfg or ProcessConfig()
    frames = load_frames_from_dir(input_dir, cfg)
    aligned_frames, metrics, validation = align_frames(frames, action, cfg)

    output_dir.mkdir(parents=True, exist_ok=True)
    save_frames(aligned_frames, output_dir)

    sheet = assemble_sheet(aligned_frames)
    sheet.save(output_dir / f"{action}_sheet_aligned.png")

    if cfg.export_gif:
        save_gif(aligned_frames, output_dir / f"{action}_preview.gif", duration=cfg.gif_duration_ms)

    write_logs(metrics, validation, output_dir, action)
    write_metadata(metrics, validation, output_dir, action)
    return validation


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process atomic sprite frames into aligned outputs.")
    parser.add_argument("action", choices=["idle", "attack", "run", "hurt"])
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--background-mode", choices=["rgba", "green", "black"], default="rgba")
    parser.add_argument("--frame-count", type=int, default=8)
    parser.add_argument(
        "--gif",
        dest="export_gif",
        action="store_true",
        default=True,
        help="export preview GIFs, enabled by default",
    )
    parser.add_argument(
        "--no-gif",
        dest="export_gif",
        action="store_false",
        help="skip preview GIF export",
    )
    args = parser.parse_args()

    config = ProcessConfig(
        frame_count=args.frame_count,
        background_mode=args.background_mode,
        export_gif=args.export_gif,
    )
    result = process_action(args.input_dir, args.output_dir, args.action, config)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
