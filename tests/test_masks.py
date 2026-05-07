from PIL import Image

from post_process import ProcessConfig, get_mask


def make_rgba_square(size=(320, 320), square=(100, 100, 180, 220)):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    for y in range(square[1], square[3]):
        for x in range(square[0], square[2]):
            img.putpixel((x, y), (255, 0, 0, 255))
    return img


def test_rgba_mask_detects_visible_pixels():
    img = make_rgba_square()
    cfg = ProcessConfig(background_mode='rgba')
    mask = get_mask(img, cfg)
    assert mask.sum() > 0


def test_green_mask_excludes_key_background():
    img = Image.new('RGBA', (320, 320), (0, 255, 0, 255))
    for y in range(120, 200):
        for x in range(120, 200):
            img.putpixel((x, y), (255, 0, 0, 255))
    cfg = ProcessConfig(background_mode='green')
    mask = get_mask(img, cfg)
    assert mask.sum() > 0
