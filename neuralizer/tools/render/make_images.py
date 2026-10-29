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
ZT, WIN = P["Zt"], P["Zt"] + P["z_nut_top"] + 2.5          # window centre height

def A(name, mat, **kw): return {"file": f"asm/{name}.stl", "mat": mat, **kw}
def finished(state="open", lit="off", panel=True, skip=()):
    win = {"off": "clear", "red": "clear_red", "white": "clear_white"}[lit]
    parts = [A("body", "silver"), A(f"sleeve_{state}", "silver"), A(f"clip_{state}", "silver"), A("bottom_cap", "silver"),
             A("knurl_nut", "silver"), A("dome", "silver"), A("led_mount", "white"), A("light_window", win),
             A("btn_minutes", "black"), A("btn_hours_pressed" if lit == "white" else "btn_hours", "black"), A("btn_weeks", "black")]
    if panel:
        parts += [A("window_panel_base", "white"), A("window_panel_details", "black")]
    return [p for p in parts if not any(s in p["file"] for s in skip)]
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

FULL = cam([0, 0, 92], -22, 6, 700)
jobs = {}
# ----------------------------------------------------------------- previews
jobs["preview"] = ({"h": 1150, "views": [
    {"caption": "CLOSED", "sub": "sleeve up: window covered, lights off", "meshes": finished("closed"), "camera": FULL},
    {"caption": "OPEN", "sub": "sleeve down: red light in the window = ready", "meshes": finished("open", "red"), "lights": glow("red"), "camera": FULL},
    {"caption": "OPEN + HOURS PRESSED", "sub": "white flash through the same window", "meshes": finished("open", "white"), "lights": glow("white"), "camera": FULL}]},
    IMG / "preview_closed_open.png")
TOP = cam([0, 0, WIN - 8], -20, 8, 250)
jobs["top"] = ({"h": 700, "views": [
    {"caption": "LIGHTS OFF", "sub": "white dome, clear window, knurled nut", "meshes": finished("open"), "camera": TOP, "w": 420},
    {"caption": "READY (RED)", "sub": "sleeve open", "meshes": finished("open", "red"), "lights": glow("red"), "camera": TOP, "w": 420},
    {"caption": "FLASH (WHITE)", "sub": "HOURS pressed", "meshes": finished("open", "white"), "lights": glow("white"), "camera": TOP, "w": 420},
    {"caption": "INSIDE", "sub": "both LEDs shine into one window; the dome's cone reflects light outward",
     "meshes": finished("open", "red") + [A("led_red", "led_red"), A("led_white", "led_white")], "lights": glow("red"), "cut": True,
     "camera": cam([0, 0, WIN - 4], -90, 4, 230), "w": 420}]}, IMG / "top_window.png")
jobs["window_back"] = ({"h": 1000, "views": [
    {"caption": "WINDOW CLOSE-UP", "sub": "multicolour panel: white with black labels (AMS)", "meshes": finished("open", "red"), "lights": glow("red"),
     "camera": cam([0, 0, 128], 0, 0, 330), "w": 560},
    {"caption": "BACK: SLEEVE SWITCH", "sub": "key channel + copper pads; the finger hides in two flutes",
     "meshes": finished("open") + [A("tape_body", "copper")], "camera": cam([0, 0, 105], 180, 5, 330), "w": 560}]}, IMG / "window_and_back.png")
EX = {"bottom_cap": [0, 0, -120], "knurl_nut": [0, 0, 26], "led_mount": [0, 0, 44], "light_window": [0, 0, 60], "dome": [0, 0, 78],
      "window_panel_base": [34, 0, 0], "window_panel_details": [34, 0, 0], "btn_minutes": [17, 0, 0], "btn_hours": [17, 0, 0], "btn_weeks": [17, 0, 0],
      "sleeve_open": [0, 0, -92], "clip_open": [0, -22, -92]}
jobs["exploded"] = ({"h": 1400, "views": [{"caption": "EXPLODED VIEW", "sub": "dome, light window, LED head, knurled nut; panel + 3 buttons; sleeve + clip; bottom cap",
    "meshes": [dict(m, pos=EX.get(pathlib.Path(m["file"]).stem, [0, 0, 0])) for m in finished("open")], "w": 900,
    "camera": cam([0, 0, 70], -35, 10, 1350)}]}, IMG / "exploded.png")
CUT = lambda t, d: cam([0, 0, t], -90, 0, d, 18)
inside = [A("cells", "grey"), A("battery_spring", "orange"), A("push_switch", "black"), A("led_red", "led_red"), A("led_white", "led_white"), A("tape_body", "copper", nocut=True), A("tape_cap", "copper")]
jobs["cutaway"] = ({"h": 1100, "views": [
    {"caption": "CUTAWAY (OPEN)", "sub": "cells, spring, switch, LEDs, wire channel", "meshes": finished("open", "red") + inside, "cut": True, "lights": glow("red"), "camera": CUT(85, 700)},
    {"caption": "LED HEAD", "sub": "LEDs side by side under the clear window", "meshes": finished("open", "red") + inside, "cut": True, "lights": glow("red"), "camera": CUT(160, 160)},
    {"caption": "BATTERY BAY", "sub": "3× LR44, printed spring, copper contacts", "meshes": finished("open") + inside, "cut": True, "camera": CUT(12, 200)}]},
    IMG / "cutaway.png")

# ----------------------------------------------------------------- assembly steps
def step(n, title, sub, views):
    return ({"h": 760, "views": [dict(v, num=str(n) if i == 0 else None, caption=title if i == 0 else v.get("caption"), sub=sub if i == 0 else v.get("sub")) for i, v in enumerate(views)]},
            IMG / "assembly" / f"step_{n:02d}.png")
body = [A("body", "silver")]
HL = "orange"
S = {}
S[2] = step(2, "LED head", "drop both LEDs (with resistor + wires) into the white LED head",
            [{"meshes": [A("led_mount", "white"), A("led_red", "led_red"), A("led_white", "led_white")], "cut": True, "camera": cam([0, 0, ZT + 1], -60, 18, 150), "w": 560},
             {"meshes": [A("led_mount", "white"), A("led_red", "led_red"), A("led_white", "led_white")], "camera": cam([0, 0, ZT + 2], -30, 35, 150), "w": 460}])
S[3] = step(3, "Battery spring + B+ contact", "spring up into the bay (boss down), copper strip on the 45° cone",
            [{"meshes": body + [A("battery_spring", HL), A("tape_body", "copper", nocut=True)], "cut": True, "camera": CUT(16, 170), "w": 560},
             {"meshes": body + [A("battery_spring", HL), A("tape_body", "copper")], "camera": cam([0, 0, 5], -30, -45, 160), "w": 460}])
S[4] = step(4, "Sleeve-switch pads", "two 1.8 mm copper strips in the recesses on the contact land (back)",
            [{"meshes": body + [A("tape_body", "copper")], "camera": cam([0, 0, 74], 180, 10, 140), "w": 560},
             {"meshes": body + [A("tape_body", "copper")], "camera": cam([0, 0, 90], 160, 8, 420), "w": 460}])
S[5] = step(5, "HOURS switch", "6×6 switch, plunger out, into the pocket behind the middle hole",
            [{"meshes": body + [A("push_switch", HL)], "camera": cam([0, 0, 127], 15, 10, 150), "w": 560},
             {"meshes": body + [A("push_switch", HL)], "cut": True, "camera": CUT(127, 150), "w": 460}])
S[6] = step(6, "Buttons + window panel", "buttons in from behind, bottom tongue into its slot, lay the panel flat",
            [{"meshes": body + [A("push_switch", "black"), A("btn_minutes", HL, pos=[10, 0, 0]), A("btn_hours", HL, pos=[10, 0, 0]), A("btn_weeks", HL, pos=[10, 0, 0]),
                                A("window_panel_base", "white", pos=[22, 0, 0]), A("window_panel_details", "black", pos=[22, 0, 0])],
              "camera": cam([10, 0, 118], 40, 8, 380), "w": 560},
             {"meshes": body + [A("btn_minutes", "black"), A("btn_hours", "black"), A("btn_weeks", "black"), A("window_panel_base", "white"), A("window_panel_details", "black")],
              "camera": cam([0, 0, 118], 0, 0, 360), "w": 460}])
done_win = [A("btn_minutes", "black"), A("btn_hours", "black"), A("btn_weeks", "black"), A("window_panel_base", "white"), A("window_panel_details", "black")]
S[7] = step(7, "LED head + knurled nut", "LED head into the keyed socket, then screw the nut down to clamp it",
            [{"meshes": body + done_win + [A("led_mount", "white"), A("knurl_nut", HL, pos=[0, 0, 14])], "camera": cam([0, 0, ZT], -25, 15, 200), "w": 560},
             {"meshes": body + done_win + [A("led_mount", "white"), A("knurl_nut", HL)], "camera": cam([0, 0, ZT], -25, 15, 200), "w": 460}])
S[8] = step(8, "Light window + dome", "push the clear window into the nut, press the dome onto it",
            [{"meshes": body + done_win + [A("led_mount", "white"), A("knurl_nut", "silver"), A("light_window", "clear", pos=[0, 0, 10]), A("dome", HL, pos=[0, 0, 22])],
              "camera": cam([0, 0, ZT + 14], -25, 12, 230), "w": 560},
             {"meshes": body + done_win + [A("led_mount", "white"), A("knurl_nut", "silver"), A("light_window", "clear"), A("dome", "silver")],
              "camera": cam([0, 0, ZT + 6], -25, 12, 200), "w": 460}])
top_done = done_win + [A("led_mount", "white"), A("knurl_nut", "silver"), A("light_window", "clear"), A("dome", "silver")]
S[9] = step(9, "Sleeve + clip", "copper tape on the finger bump, slide on from the bottom until it clicks, snap on the clip",
            [{"meshes": body + top_done + [A("sleeve_open", HL, pos=[0, 0, -60]), A("tape_bump_open", "copper", pos=[0, 0, -60]), A("clip_open", "silver", pos=[0, -12, -60])],
              "camera": cam([0, 0, 50], 200, 10, 700), "w": 560},
             {"meshes": body + top_done + [A("sleeve_open", "silver"), A("clip_open", HL)], "camera": cam([0, 0, 40], -70, 5, 380), "w": 460}])
S[10] = step(10, "Batteries + bottom cap", "3× LR44 flat (+) side down, copper disc on the cap face, screw the cap home",
             [{"meshes": finished("open", skip=("bottom_cap",)) + [A("cells", "grey", pos=[0, 0, -26]), A("tape_cap", "copper", pos=[0, 0, -42]), A("bottom_cap", HL, pos=[0, 0, -42])],
               "camera": cam([0, 0, -10], -25, 5, 380), "w": 560},
              {"meshes": finished("open") + [A("cells", "grey"), A("tape_cap", "copper")], "cut": True, "camera": CUT(14, 180), "w": 460}])
S[11] = step(11, "Test", "slide open: red. Press HOURS: white flash. Close: off.",
             [{"meshes": finished("open", "red"), "lights": glow("red"), "camera": cam([0, 0, 125], -20, 6, 420), "w": 340, "caption": "open = red"},
              {"meshes": finished("open", "white"), "lights": glow("white"), "camera": cam([0, 0, 125], -20, 6, 420), "w": 340, "caption": "HOURS = white"},
              {"meshes": finished("closed"), "camera": cam([0, 0, 125], -20, 6, 420), "w": 340, "caption": "closed = off"}])
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
# plates overview (5 thumbnails + names)
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
