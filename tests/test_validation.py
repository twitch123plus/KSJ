from PIL import Image

from post_process import ProcessConfig, compute_metrics, validate_metrics


def make_frame():
    img = Image.new('RGBA', (320, 320), (0, 0, 0, 0))
    for y in range(140, 240):
        for x in range(130, 180):
            img.putpixel((x, y), (255, 255, 255, 255))
    return img


def test_validate_metrics_passes_simple_consistent_frames():
    cfg = ProcessConfig(background_mode='rgba')
    frames = [make_frame() for _ in range(3)]
    metrics = [compute_metrics(f, i + 1, cfg) for i, f in enumerate(frames)]
    result = validate_metrics(metrics, 'idle', (320, 320))
    assert isinstance(result.passed, bool)
    assert result.failures == []
