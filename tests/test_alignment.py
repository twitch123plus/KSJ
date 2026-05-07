from PIL import Image

from post_process import ProcessConfig, align_frames


def make_frame(offset_x=0, offset_y=0):
    img = Image.new('RGBA', (320, 320), (0, 0, 0, 0))
    for y in range(140 + offset_y, 240 + offset_y):
        for x in range(130 + offset_x, 180 + offset_x):
            if 0 <= x < 320 and 0 <= y < 320:
                img.putpixel((x, y), (255, 255, 255, 255))
    return img


def test_align_frames_returns_same_count():
    frames = [make_frame(0, 0), make_frame(5, 3), make_frame(-4, -2)]
    cfg = ProcessConfig(frame_count=3, background_mode='rgba')
    aligned, metrics, validation = align_frames(frames, 'idle', cfg)
    assert len(aligned) == 3
    assert len(metrics) == 3
    assert validation is not None
