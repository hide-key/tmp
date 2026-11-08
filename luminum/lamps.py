"""Cut the four lamp illustrations out of the source scan as transparent PNGs.

Ink is kept black and paper becomes transparent (alpha = darkness), so the
illustrations sit cleanly on the white slide. Text that touches the crop boxes
is masked out (it is re-typeset as live text in the deck).
"""
import os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source.jpg")
OUT = os.path.join(HERE, "build", "img")

# name: (crop box, [mask boxes in source px])
LAMPS = {
    "lamp_4F": ((128, 436, 484, 816), [(110, 700, 190, 780)]),
    "lamp_4": ((548, 428, 934, 816), [(565, 682, 634, 756), (848, 722, 1045, 800)]),
    "lamp_4H": ((996, 436, 1404, 824), [(1322, 706, 1404, 782), (996, 768, 1048, 816)]),
    "lamp_7": ((772, 1160, 1424, 1877), [(772, 1150, 1020, 1214), (1198, 1648, 1424, 1722),
                                        (1198, 1750, 1424, 1872)]),
}


def cut(name, box, masks):
    im = Image.open(SRC).convert("L")
    m = ImageDraw.Draw(im)
    for mb in masks:
        m.rectangle(mb, fill=255)
    c = np.asarray(im.crop(box), dtype=np.float32)
    # paper (~235-255) -> 0 alpha; ink -> opaque. Soft ramp keeps anti-aliasing.
    a = np.clip((232.0 - c) / (232.0 - 60.0), 0, 1)
    # remove isolated specks (tiny paper noise) with a 3x3 neighbourhood test
    solid = a > 0.25
    pad = np.pad(solid, 1)
    neigh = sum(pad[1 + dy:pad.shape[0] - 1 + dy, 1 + dx:pad.shape[1] - 1 + dx]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - solid
    a[(solid) & (neigh == 0)] = 0
    rgba = np.zeros(c.shape + (4,), np.uint8)
    rgba[..., 3] = (a * 255).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    # trim to ink bbox, remember offset so placement stays exact
    bb = out.getbbox()
    out = out.crop(bb)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, name + ".png"), optimize=True)
    return (box[0] + bb[0], box[1] + bb[1], box[0] + bb[2], box[1] + bb[3])


def main():
    res = {}
    for k, (box, masks) in LAMPS.items():
        res[k] = cut(k, box, masks)
    return res


if __name__ == "__main__":
    for k, v in main().items():
        print(k, v)
