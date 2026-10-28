#!/usr/bin/env python3
"""Top-down paint guide for the window panel, rasterised straight from stl/window_panel.stl
(so it shows exactly what will print). Silver = panel face, black = recesses/buttons,
white = raised details to dry-brush, red/green = arrows / indicator dot."""
import numpy as np, trimesh, pathlib
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
ROOT = pathlib.Path(__file__).resolve().parent.parent
m = trimesh.load(ROOT / "stl/window_panel.stl", force="mesh")
res = 24.0; lo = np.array([-7.5, -4.5]); W, H = int(15 * res), int(84 * res)
def layer(z):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    path, _ = sec.to_2D(to_2D=np.eye(4))
    img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
    px = lambda x, y: ((x - lo[0]) * res, H - (y - lo[1]) * res)
    for p in path.polygons_full:
        d.polygon([px(x, y) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors: d.polygon([px(x, y) for x, y in h.coords], fill=0)
    return np.array(img) > 0
base, mid, top = layer(0.6), layer(1.5), layer(2.1)
rgb = np.zeros((H, W, 3), np.uint8); rgb[:] = (40, 40, 44)
rgb[base] = (20, 20, 22)                       # recess floors (paint black)
rgb[mid] = (196, 200, 207)                      # panel face (silver)
inrec = base & ~mid
ins = layer(1.5) & inrec                        # nothing; letters are at 1.5 -> already in mid
rgb[top] = (250, 250, 250)                      # raised labels (white)
# colour the two arrows red and the indicator dot green (matched by their design position)
lab, n = ndimage.label(top)
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    x = xs.mean() / res + lo[0]; y = (H - ys.mean()) / res + lo[1]
    for (px_, v, col) in ((-5.55, 22.5, (215, 30, 30)), (-5.55, 36.0, (215, 30, 30)), (5.4, 19.6, (40, 190, 60))):
        if abs(x - px_) < 0.8 and abs(y - (72 - v + 3.5)) < 0.8: rgb[lab == i] = col
# display segments (inside the lower recess) red
yd = (72 - 63 + 3.5)
r0, r1 = int(H - (yd + 2.6 - lo[1]) * res), int(H - (yd - 2.6 - lo[1]) * res)
seg = layer(1.35) & ~layer(1.65)
box = np.zeros_like(seg); box[r0:r1, int((-5 - lo[0]) * res):int((5 - lo[0]) * res)] = True
rgb[seg & box] = (230, 40, 30)
# buttons (holes) black with a highlight ring
for v, dia in ((8.0, 9.6), (22.5, 8.0), (36.0, 8.0)):
    cy = H - ((72 - v + 3.5) - lo[1]) * res; cx = (0 - lo[0]) * res; r = dia / 2 * res
    yy, xx = np.ogrid[:H, :W]; disc = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
    rgb[disc] = (10, 10, 12)
img = Image.fromarray(rgb).resize((W * 2, H * 2), Image.NEAREST)
canvas = Image.new("RGB", (W * 2 + 520, H * 2), (235, 236, 238)); canvas.paste(img, (0, 0))
d = ImageDraw.Draw(canvas)
try: f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 30); g = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 26)
except Exception: f = g = None
x0 = W * 2 + 30
d.text((x0, 40), "WINDOW PANEL - PAINT GUIDE", fill=(20, 20, 20), font=f)
rows = [((196, 200, 207), "panel face: silver (chrome paint)"), ((250, 250, 250), "raised labels: dry-brush white"),
        ((20, 20, 22), "recessed plates: black"), ((215, 30, 30), "arrows: red"), ((40, 190, 60), "indicator dot: green"),
        ((230, 40, 30), "display digits: red"), ((10, 10, 12), "buttons: printed black")]
for i, (c, t) in enumerate(rows):
    y = 110 + i * 56
    d.rectangle([x0, y, x0 + 36, y + 36], fill=c, outline=(80, 80, 80)); d.text((x0 + 52, y + 4), t, fill=(30, 30, 30), font=g)
d.text((x0, 540), "Rasterised from stl/window_panel.stl", fill=(90, 90, 90), font=g)
d.text((x0, 576), "raised details 0.6 mm, recesses 0.6 mm", fill=(90, 90, 90), font=g)
d.text((x0, 612), "panel 13 x 72 mm (shown 2:1 scale-ish)", fill=(90, 90, 90), font=g)
canvas.save(ROOT / "images/panel_paint_guide.png")
print("ok", canvas.size)
