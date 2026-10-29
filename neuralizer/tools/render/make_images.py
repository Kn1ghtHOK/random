#!/usr/bin/env python3
"""Renders every picture in images/ (and the 3MF plate thumbnails) with three.js in headless
Chromium.  Needs: tools/export_assembled.sh + tools/make_3mf.py --layout-json build/plates.json
run first, and `npm install three@0.160.0` reachable as tools/render/node_modules."""
import json, os, pathlib, subprocess, sys, time
from PIL import Image

R = pathlib.Path(__file__).resolve().parent
ROOT = R.parent.parent
IMG = ROOT / "images"; (IMG / "assembly").mkdir(parents=True, exist_ok=True)
SC = ROOT / "build" / "scenes"; SC.mkdir(parents=True, exist_ok=True)
THUMBS = ROOT / "build" / "thumbs"; THUMBS.mkdir(parents=True, exist_ok=True)
P = json.loads((ROOT / "build/params.echo").read_text().split("PARAMS ", 1)[1].rsplit('"', 1)[0].replace('\\"', '"'))
ZT, WIN = P["Zt"], (P["z_win_bot"] + P["z_win_top"]) / 2      # light-ring centre height
ZW0, ZW1, HZ = P["Zw0"], P["Zw1"], P["Zw1"] - 22.5               # window, HOURS switch

def A(name, mat, **kw): return {"file": f"asm/{name}.stl", "mat": mat, **kw}
TOPCAP = lambda lit="off": [A("top_cap_clear", {"off": "clear", "red": "clear_red", "white": "clear_white"}[lit]), A("top_cap_white", "white")]
PANEL = [A("window_panel_base", "white"), A("window_panel_details", "black")]
def finished(state="open", lit="off", panel=True, skip=()):
    parts = [A("body", "silver"), A(f"sleeve_{state}", "silver"), A(f"clip_{state}", "silver"), A("bottom_cap", "silver")] + TOPCAP(lit)
    if panel:
        parts += PANEL + ([A("btn_hours_pressed", "black")] if lit == "white" else [A("btn_hours_base", "white"), A("btn_hours_top", "black")])
    return [p for p in parts if not any(s in p["file"] for s in skip)]
ELEC = [A("cells", "grey"), A("s1_switch", "black"), A("s2_switch", "black"), A("led_red", "led_red"), A("led_white", "led_white")]
SLED = [A("sled", "white")] + ELEC
def glow(lit):
    if lit == "red": return [{"color": 0xff2010, "i": 26000, "pos": [0, 0, WIN]}]
    if lit == "white": return [{"color": 0xff2010, "i": 16000, "pos": [0, 0, WIN]}, {"color": 0xffffff, "i": 60000, "pos": [0, 0, WIN]}]
    return []
def cam(target, yaw, pitch, dist, fov=20): return {"target": target, "yaw": yaw, "pitch": pitch, "dist": dist, "fov": fov}

def render(name, scene, out):
    f = SC / f"{name}.json"; f.write_text(json.dumps(scene))
    rel = f"scenes/{name}.json"
    r = subprocess.run(["node", "render.js", rel, str(out)], cwd=R, capture_output=True, text=True)
    if r.returncode or r.stdout.strip():
        print(name, r.stdout, r.stderr[-2000:])
    print("rendered", out.relative_to(ROOT))

FULL = cam([0, 0, 100], -22, 6, 760)
jobs = {}
# ----------------------------------------------------------------- previews
jobs["preview"] = ({"h": 1150, "views": [
    {"caption": "CLOSED", "sub": "a plain fluted tube: panel and light ring hidden", "meshes": finished("closed"), "camera": FULL},
    {"caption": "OPEN", "sub": "sleeve down: panel + clear ring show, red = ready", "meshes": finished("open", "red"), "lights": glow("red"), "camera": FULL},
    {"caption": "OPEN + HOURS PRESSED", "sub": "white flash through the same ring", "meshes": finished("open", "white"), "lights": glow("white"), "camera": FULL}]},
    IMG / "preview_closed_open.png")
TOP = cam([0, 0, WIN - 6], -20, 8, 250)
jobs["top"] = ({"h": 700, "views": [
    {"caption": "CLOSED", "sub": "sleeve covers the clear ring", "meshes": finished("closed"), "camera": TOP, "w": 420},
    {"caption": "READY (RED)", "sub": "sleeve open", "meshes": finished("open", "red"), "lights": glow("red"), "camera": TOP, "w": 420},
    {"caption": "FLASH (WHITE)", "sub": "HOURS pressed", "meshes": finished("open", "white"), "lights": glow("white"), "camera": TOP, "w": 420},
    {"caption": "INSIDE", "sub": "both LEDs shine into the clear ring; white dome above, white body below",
     "meshes": finished("open", "red") + SLED, "lights": glow("red"), "cut": True,
     "camera": cam([0, 0, WIN - 6], -90, 4, 230), "w": 420}]}, IMG / "top_window.png")
jobs["window_back"] = ({"h": 1000, "views": [
    {"caption": "WINDOW CLOSE-UP", "sub": "multicolour panel + HOURS button (AMS)", "meshes": finished("open", "red"), "lights": glow("red"),
     "camera": cam([0, 0, (ZW0 + ZW1) / 2], 0, 0, 380), "w": 560},
    {"caption": "BACK: SLEEVE SWITCH", "sub": "the sleeve's finger presses a flexing tongue onto switch S1",
     "meshes": finished("open"), "camera": cam([0, 0, 90], 180, 5, 330), "w": 560}]}, IMG / "window_and_back.png")
EX = {"bottom_cap": [0, 0, -40], "top_cap_clear": [0, 0, 150], "top_cap_white": [0, 0, 150],
      "window_panel_base": [34, 0, 0], "window_panel_details": [34, 0, 0], "btn_hours_base": [20, 0, 0], "btn_hours_top": [20, 0, 0],
      "sleeve_open": [0, 0, -70], "clip_open": [0, -22, -70]}
EXS = [0, 0, 120]   # sled lifted out of the top
jobs["exploded"] = ({"h": 1400, "views": [{"caption": "EXPLODED VIEW", "sub": "8 printed parts: top cap, sled (all electronics), body, panel + HOURS, sleeve, clip, bottom cap",
    "meshes": [dict(m, pos=EX.get(pathlib.Path(m["file"]).stem, [0, 0, 0])) for m in finished("open")] + [dict(m, pos=EXS) for m in SLED], "w": 900,
    "camera": cam([0, 0, 130], -35, 10, 1700)}]}, IMG / "exploded.png")
CUT = lambda t, d: cam([0, 0, t], -90, 0, d, 18)
jobs["cutaway"] = ({"h": 1100, "views": [
    {"caption": "CUTAWAY (OPEN)", "sub": "the sled carries everything: LEDs, HOURS switch, cells, sleeve switch", "meshes": finished("open", "red") + SLED, "cut": True, "lights": glow("red"), "camera": CUT(100, 760)},
    {"caption": "TOP", "sub": "LED head clamped by the top cap; HOURS button on S2", "meshes": finished("open", "red") + SLED, "cut": True, "lights": glow("red"), "camera": CUT(162, 180)},
    {"caption": "BOTTOM", "sub": "sleeve finger → tongue → S1", "meshes": finished("open") + SLED, "cut": True, "camera": CUT(78, 180)}]},
    IMG / "cutaway.png")

# ----------------------------------------------------------------- assembly steps
def step(n, title, sub, views):
    return ({"h": 760, "views": [dict(v, num=str(n) if i == 0 else None, caption=title if i == 0 else v.get("caption"), sub=sub if i == 0 else v.get("sub")) for i, v in enumerate(views)]},
            IMG / "assembly" / f"step_{n:02d}.png")
body = [A("body", "silver")]
HL = "orange"
S = {}
SIDE = lambda z, d: cam([0, 0, z], -60, 12, d)
S[1] = step(1, "Sleeve, clip, bottom cap", "sleeve on from the bottom (finger at the back) until it clicks; snap on the clip; screw on the cap",
            [{"meshes": body + [A("sleeve_open", HL, pos=[0, 0, -60]), A("clip_open", "silver", pos=[0, -14, -60]), A("bottom_cap", "silver", pos=[0, 0, -90])],
              "camera": cam([0, 0, 60], 200, 10, 760), "w": 560},
             {"meshes": body + [A("sleeve_closed", "silver"), A("clip_closed", HL), A("bottom_cap", "silver")], "camera": cam([0, 0, 120], -70, 5, 520), "w": 460}])
S[2] = step(2, "Window panel + HOURS button", "slide the sleeve down; button into the panel's back; top tongue in first, lay flat, push down 2 mm: click",
            [{"meshes": body + [A("sleeve_open", "silver"), A("btn_hours_base", HL, pos=[14, 0, 2]), A("btn_hours_top", HL, pos=[14, 0, 2]),
                                A("window_panel_base", "white", pos=[24, 0, 2]), A("window_panel_details", "black", pos=[24, 0, 2])],
              "camera": cam([10, 0, ZW0 + 36], 40, 8, 420), "w": 560},
             {"meshes": body + [A("sleeve_open", "silver")] + PANEL + [A("btn_hours_base", "white"), A("btn_hours_top", "black")],
              "camera": cam([0, 0, ZW0 + 36], 0, 0, 400), "w": 460}])
S[3] = step(3, "Wire the sled", "both switches + both LEDs click into the sled; solder 7 joints on the bench (see wiring.svg)",
            [{"meshes": SLED[:1] + SLED[2:], "camera": cam([0, 0, 125], -55, 14, 440), "w": 560},
             {"meshes": SLED[:1] + SLED[2:], "camera": cam([0, 0, 165], 120, 20, 200), "w": 460, "caption": "LED head"}])
S[4] = step(4, "Batteries", "3× LR44, + toward the LEDs, snap in between the springy bulkheads",
            [{"meshes": [A("sled", "white"), A("cells", HL)] + ELEC[1:], "camera": cam([0, 0, 128], -55, 14, 330), "w": 560},
             {"meshes": [A("sled", "white"), A("cells", HL, pos=[14, 0, 0])] + ELEC[1:], "camera": cam([0, 0, 128], -20, 10, 330), "w": 460}])
S[5] = step(5, "Sled into the body", "close the sleeve, then slide the sled in from the top - it only fits one way round",
            [{"meshes": finished("closed", panel=True, skip=("top_cap",)) + [dict(m, pos=[0, 0, 70], mat=HL if m["file"].endswith("sled.stl") else m["mat"]) for m in SLED],
              "camera": cam([0, 0, 150], -40, 10, 900), "w": 560},
             {"meshes": finished("closed", skip=("top_cap",)) + SLED, "cut": True, "camera": CUT(130, 560), "w": 460}])
S[6] = step(6, "Top cap", "screw the clear/white top cap on hand-tight: it clamps the sled",
            [{"meshes": finished("closed", skip=("top_cap",)) + [dict(m, pos=[0, 0, 22], mat=HL if "white" in m["file"] else m["mat"]) for m in TOPCAP()],
              "camera": cam([0, 0, ZT + 6], -25, 12, 260), "w": 560},
             {"meshes": finished("closed"), "camera": cam([0, 0, ZT], -25, 12, 260), "w": 460}])
S[7] = step(7, "Test", "slide open: red. Press HOURS: white flash. Close: off.",
            [{"meshes": finished("open", "red"), "lights": glow("red"), "camera": cam([0, 0, 140], -20, 6, 520), "w": 340, "caption": "open = red"},
             {"meshes": finished("open", "white"), "lights": glow("white"), "camera": cam([0, 0, 140], -20, 6, 520), "w": 340, "caption": "HOURS = white"},
             {"meshes": finished("closed"), "camera": cam([0, 0, 140], -20, 6, 520), "w": 340, "caption": "closed = off"}])
for k, v in S.items(): jobs[f"step{k}"] = v

# ----------------------------------------------------------------- plates (3MF thumbnails + overview)
plates = json.loads((ROOT / "build/plates.json").read_text())
FILMAT = {1: "pla_white", 2: "pla_black", 3: "pla_clear"}
for i, p in enumerate(plates):
    meshes = [{"file": v["file"], "mat": FILMAT[v["fil"]], "pos": [o["pos"][0], o["pos"][1], 0]} for o in p["objects"] for v in o["vols"]]
    jobs[f"plate{i+1}"] = ({"h": 512, "views": [{"meshes": meshes, "bed": [0, 0], "bg": 0xe9eaec, "w": 512,
                            "camera": cam([128, 118, 0], -90, 58, 640, 30)}]}, THUMBS / f"plate_{i+1}.png")

only = sys.argv[1:]
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=R, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
try:
    for k, (scene, out) in jobs.items():
        if not only or any(k.startswith(o) for o in only):
            render(k, scene, out)
finally:
    srv.terminate()
# plates overview (thumbnails + names)
if not only or any(o.startswith("plate") for o in only):
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 18)
    tiles = [Image.open(THUMBS / f"plate_{i+1}.png") for i in range(len(plates))]
    sheet = Image.new("RGB", (512 * 3, (512 + 40) * 2), (240, 241, 243))
    for i, t in enumerate(tiles):
        x, y = (i % 3) * 512, (i // 3) * 552
        sheet.paste(t, (x, y + 40)); ImageDraw.Draw(sheet).text((x + 14, y + 10), "Plate " + plates[i]["name"], fill=(30, 30, 30), font=font)
    d = ImageDraw.Draw(sheet)
    d.text((1024 + 20, 552 + 60), "AMS slots in the 3MF:", fill=(20, 20, 20), font=font)
    for j, (c, t) in enumerate([((242, 242, 242), "1  White PETG"), ((22, 22, 22), "2  Black PETG"), ((214, 234, 242), "3  Clear PETG")]):
        d.rectangle([1044, 552 + 100 + j * 40, 1074, 552 + 130 + j * 40], fill=c, outline=(90, 90, 90)); d.text((1090, 552 + 104 + j * 40), t, fill=(30, 30, 30), font=font)
    sheet.save(IMG / "print_plates.png"); print("rendered images/print_plates.png")
