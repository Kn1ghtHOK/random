#!/usr/bin/env python3
"""
Verification suite for neuralizer.scad.

  1. every exported STL is a closed, manifold solid
  2. every print-orientation part sits on the bed and fits the Bambu P1S (256 mm cube)
  3. overhang scan in print orientation (support-free check)
  4. pairwise collision matrix of the whole assembly, sleeve OPEN and CLOSED
     (only the designed contacts / preloads are allowed to overlap)
  5. threads: they really engage (cannot be pulled off axially) AND they can be
     screwed on/off along the helix without any interference
  6. mechanism numbers: button travel vs switch travel, sleeve-switch preload,
     closed-position detent, battery spring preload, LED positions
  7. raised text / detail stroke widths on the window panel vs 0.4 mm nozzle

Run:  tools/build_stl.sh && tools/export_assembled.sh && python3 tools/verify.py
Writes VERIFICATION.md next to the .scad.
"""
import json, re, sys, itertools, pathlib, subprocess
import numpy as np
import trimesh
import manifold3d as mf

ROOT = pathlib.Path(__file__).resolve().parent.parent
STL = ROOT / "stl"
ASM = ROOT / "build" / "assembled"
BED = (256.0, 256.0, 256.0)            # Bambu Lab P1S build volume
ZERO = 0.02                            # mm^3: below this two parts only touch

lines, fails = [], []
def out(s=""):
    print(s); lines.append(s)
def check(ok, msg):
    out(("PASS  " if ok else "FAIL  ") + msg)
    if not ok: fails.append(msg)
    return ok

# ------------------------------------------------------------------ params
import os
BATT = os.environ.get("BATTERY", "")
echo = subprocess.run(["openscad", "-o", str(ROOT / "build/params.echo"), "-D", 'part="none"'] + (["-D", f'battery="{BATT}"'] if BATT else []) + [
                       str(ROOT / "neuralizer.scad")], capture_output=True, text=True)
txt = (ROOT / "build/params.echo").read_text()
P = json.loads(re.search(r'PARAMS (\{.*\})', txt).group(1).replace('\\"', '"'))

# ------------------------------------------------------------------ helpers
_cache = {}
def tm(path):
    if path not in _cache:
        _cache[path] = trimesh.load(path, force="mesh")
    return _cache[path]
def man(path):
    m = tm(path)
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))
def vol(m): return m.volume()
def inter(a, b):
    i = a ^ b
    return vol(i), i
def bbox(m):
    lo, hi = m.bounding_box()[:3], m.bounding_box()[3:]
    return np.array(lo), np.array(hi)

# ================================================================== 1+2 parts
out("## 1. Printable parts: closed solids, on the bed, fit the P1S\n")
out("| part | size X×Y×Z (mm) | volume (cm³) | watertight | fits 256³ |")
out("|---|---|---|---|---|")
parts = sorted(STL.glob("*.stl"))
for f in parts:
    m = tm(str(f))
    ext = m.bounds[1] - m.bounds[0]
    wt = m.is_watertight and m.is_volume
    sub = f.stem in ("window_panel_details", "top_cap_white", "btn_hours_top", "btn_hours_base")   # colour regions inside a multicolour object
    fits = all(e <= b for e, b in zip(ext, BED)) and (sub or abs(m.bounds[0][2]) < 1e-3)
    out(f"| {f.stem} | {ext[0]:.1f}×{ext[1]:.1f}×{ext[2]:.1f} | {m.volume/1000:.2f} | {'yes' if wt else 'NO'} | {'yes' if fits else 'NO'} |")
    if not wt: fails.append(f"{f.stem} not watertight")
    if not fits: fails.append(f"{f.stem} does not fit / not on bed")
# multicolour parts: the colour bodies must rebuild each part exactly, without overlap
for whole, a_, b_, desc in (("window_panel", "window_panel_base", "window_panel_details", "window panel: white base + black labels/buttons"),
                            ("top_cap", "top_cap_clear", "top_cap_white", "top cap: clear spigot + ring, white dome"),
                            ("btn_hours", "btn_hours_base", "btn_hours_top", "HOURS button: white core, black top")):
    pa, pb, pd = (man(str(STL / f"{n}.stl")) for n in (whole, a_, b_))
    ov = vol(pb ^ pd); diff = abs(vol(pb) + vol(pd) - vol(pa)); xor = vol(pa - (pb + pd))
    check(ov <= ZERO and diff < 0.05 and xor < 0.05,
          f"multicolour {desc}: {vol(pb):.0f} + {vol(pd):.0f} mm³ = {vol(pa):.0f} mm³, no overlap, nothing missing")
out()

# ================================================================== 3 overhangs
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import printcheck
out("## 2. Support-free check (print orientation, tools/printcheck.py)\n")
out("Strict rules, so no part needs supports or a bridge:")
out("- **overhangs:** no down-facing surface flatter than 45° (normal_z < −0.72) above the first layer;")
out(f"  only patches narrower than {printcheck.MAX_LEDGE} mm are tolerated (the nozzle prints straight over them).")
out(f"- **floating islands:** each part is sliced every {printcheck.LAYER} mm; every region of a layer must sit on")
out("  the layer below (this is what Bambu Studio warns about as floating / needs support).\n")
out("| part | overhang patches | floating islands | verdict |")
out("|---|---|---|---|")
for f in parts:
    if f.stem in printcheck.SKIP:
        continue
    oh, fl, _ = printcheck.check(f)
    ok = not oh and not fl
    out(f"| {f.stem} | {len(oh)} | {len(fl)} | {'OK, no supports' if ok else 'NEEDS SUPPORT'} |")
    if not ok: fails.append(f"{f.stem} needs support")
out()

# ================================================================== 4 collisions
out("## 3. Collision matrix (assembly coordinates)\n")
static = ["body", "bottom_cap", "sled", "top_cap", "window_panel", "btn_hours", "cells", "s2_switch", "s1_switch",
          "led_red", "led_white"]
M = {k: man(str(ASM / f"{k}.stl")) for k in static}
for st in ("open", "closed"):
    M[f"sleeve_{st}"] = man(str(ASM / f"sleeve_{st}.stl"))
    M[f"clip_{st}"] = man(str(ASM / f"clip_{st}.stl"))
M["btn_hours_pressed"] = man(str(ASM / "btn_hours_pressed.stl"))

# designed overlaps: (a, b) -> (reason, max allowed volume mm^3)
EXPECTED = {
    frozenset(["cells", "sled"]): (f"battery bulkheads pre-loaded {P['batt_preload']} mm on the cell stack (they flex = battery spring)", 80),
    frozenset(["sleeve_open", "body"]): ("sleeve bump pressing the switch tongue's pad (the tongue flexes and clicks S1)", 130),
}
def collide(names):
    rows = []
    for a, b in itertools.combinations(names, 2):
        v, i = inter(M[a], M[b])
        if v <= ZERO: continue
        lo, hi = bbox(i)
        rows.append((a, b, v, EXPECTED.get(frozenset([a, b])), lo, hi))
    return rows
for st in ("open", "closed"):
    names = static + [f"sleeve_{st}", f"clip_{st}"]
    rows = collide(names)
    out(f"**Sleeve {st.upper()}** — {len(names)} solids, {len(names)*(len(names)-1)//2} pairs checked.\n")
    if not rows: out("No overlaps at all.\n")
    for a, b, v, exp, lo, hi in rows:
        where = f"x {lo[0]:.1f}…{hi[0]:.1f}, z {lo[2]:.1f}…{hi[2]:.1f}"
        if exp and v <= exp[1]:
            out(f"- expected: **{a} ↔ {b}** {v:.2f} mm³ ({where}) — {exp[0]}")
        else:
            check(False, f"{a} ↔ {b} overlap {v:.2f} mm³ at {where}")
    out()
check(not any("overlap" in f for f in fails), "no unintended collisions in the OPEN or CLOSED position")
v, i = inter(M["sleeve_open"], M["body"])
i = sum((q for q in i.decompose() if q.volume() > 1e-3), start=type(i)())   # drop zero-volume face contact at the stop
lo, hi = bbox(i)
check(lo[0] >= P["x_pad"] - 0.05 and hi[0] <= P["x_pad"] + P["pad_press"] + 0.05 and abs(lo[1]) <= P["tongue_w"] / 2 + 0.05,
      f"OPEN: the only sleeve↔body overlap is the bump on the tongue pad, {hi[0]-lo[0]:.2f} mm (= pad_press)")
v, _ = inter(M["sleeve_closed"], M["body"])
check(v <= ZERO, "CLOSED: sleeve touches nothing (bump rests above the detent ridge)")
out()

# ================================================================== 5 threads
out("## 4. Threads\n")
def screw_path(fixed, moving, P_, sign, turns):
    worst = 0.0
    for t in np.arange(30, 360 * turns + 1, 30):
        v, _ = inter(fixed, moving.rotate([0, 0, sign * t]).translate([0, 0, sign * P_ * t / 360.0]))
        worst = max(worst, v)
    return worst
def thread_report(fixed, moving, P_, sign, turns, name, crest_male, core_female):
    w = screw_path(fixed, moving, P_, sign, turns)
    check(w <= ZERO, f"{name}: screwing off along the helix ({turns} turns, every 30°) — max overlap {w:.3f} mm³ (clearance all the way)")
    v_ax, _ = inter(fixed, moving.translate([0, 0, sign * P_ / 2]))
    check(v_ax > 5, f"{name}: pulling straight off by half a pitch WITHOUT turning collides ({v_ax:.0f} mm³) → the teeth interlock")
    v_rot, _ = inter(fixed, moving.rotate([0, 0, 90]))
    check(v_rot > 5, f"{name}: turning 90° WITHOUT advancing collides ({v_rot:.0f} mm³) → pitch/handedness match")
    check(crest_male - core_female >= 0.45, f"{name}: radial tooth engagement {crest_male-core_female:.2f} mm, flank clearance {P['thread_clr']} mm")
thread_report(M["body"], M["bottom_cap"], P["bt_P"], -1, 4, "Bottom cap ↔ body (Ø16 × 2 mm)", P["bt_D"] / 2, P["bt_core"])
cap_free = M["top_cap"]
thread_report(M["body"], cap_free, P["tt_P"], +1, 3, "Top cap ↔ body (Ø17 × 2 mm)", P["tt_D"] / 2, P["tt_core"])
v, _ = inter(M["top_cap"].translate([0, 0, -0.05]), M["sled"])
check(v > 0, "top cap: its spigot lands on the sled flange (clamps the electronics sled when screwed home)")
out()

# ================================================================== 6 mechanisms
out("## 5. Mechanism checks\n")
# electronics sled: slides out of / into the body along its whole length (top cap removed)
assy = M["sled"] + M["cells"] + M["s1_switch"] + M["s2_switch"] + M["led_red"] + M["led_white"]
worst = 0.0; others = M["body"] + M["window_panel"] + M["btn_hours"]
for dz in np.arange(1.0, P["sled_len"] + 12, 2.0):
    v, _ = inter(assy.translate([0, 0, dz]), others); worst = max(worst, v)
check(worst <= ZERO, f"electronics sled (with cells, both switches, LEDs) slides out of the body over its full {P['sled_len']:.0f} mm, checked every 2 mm — max overlap {worst:.3f} mm³")
v, _ = inter(assy.rotate([0, 0, 180]), M["body"])
check(v > 1, "sled is keyed: rotated 180° it does not fit (it can only go in the right way round)")
for k in ("s1_switch", "s2_switch"):
    v, _ = inter(M[k], M["sled"]); check(v <= ZERO, f"{k.split('_')[0].upper()} " + "(6×6 tactile incl. trimmed legs) fits its sled pocket")
# HOURS
v_rest, _ = inter(M["btn_hours"], M["s2_switch"])
v_g, _ = inter(M["btn_hours"].translate([-P["btn_gap"] - 0.03, 0, 0]), M["s2_switch"])
check(v_rest <= ZERO and v_g > 0, f"HOURS at rest: {P['btn_gap']} mm above the S2 plunger (no preload)")
v_pr, ip = inter(M["btn_hours_pressed"], M["s2_switch"]); lo, hi = bbox(ip)
depth = hi[0] - lo[0]
check(depth >= P["sw_travel"], f"HOURS pressed: pushes the plunger {depth:.2f} mm (≥ {P['sw_travel']} travel → it clicks), then stops on the window floor")
for o in ("body", "window_panel"):
    v, _ = inter(M["btn_hours_pressed"], M[o]); check(v <= ZERO, f"HOURS pressed: no contact with the {o.replace('_', ' ')} (stops on its flange ledges)")
v, _ = inter(M["btn_hours"], M["window_panel"].translate([-0.3, 0, 0]))
check(v > 1, "HOURS button is captive behind the panel")
# sleeve switch S1 through the flexure tongue (spring model; PETG E ≈ 2000 MPa)
E = 2000.0
fing_len = 16 + 8.5 + 10.5
Lf = fing_len - 16 - 4.25; If = 13.4 * 1.6 ** 3 / 12; kf = 3 * E * If / Lf ** 3
# tongue: free from its root (the bore reaches below it) to the pad centre
Lt = P["tongue_root"] + 4.0; It = P["tongue_w"] * P["tongue_t"] ** 3 / 12; kt = 3 * E * It / Lt ** 3
gap = P["bore_r"] - (-P["s1_tip"])
v, _ = inter(M["s1_switch"], M["body"]); v2, _ = inter(M["s1_switch"].translate([-gap - 0.03, 0, 0]), M["body"])
check(v <= ZERO and v2 > 0, f"S1 plunger rests {gap:.2f} mm behind the tongue (free when the sleeve is not fully open)")
for Fsw in (1.6, 2.5, 3.5):   # 6x6 tactile actuation forces 160 / 250 / 350 gf
    dt = max(0.0, (kf * P["pad_press"] - Fsw) / (kf + kt))
    press = dt - gap
    check(press >= P["sw_travel"], f"S1 with a {Fsw*1000/9.81:.0f} gf switch: finger k={kf:.1f} N/mm, tongue k={kt:.1f} N/mm, overlap {P['pad_press']} mm "
          f"→ tongue moves {dt:.2f} mm, plunger {press:.2f} mm (≥ {P['sw_travel']}) → clicks")
s_mid = M["sleeve_closed"].translate([0, 0, -P["travel"] / 2]); v, _ = inter(s_mid, M["body"])
check(v <= ZERO, "half-open: the bump is off the pad → S1 released (lights only at full open)")
# detent / stops / coverage
v, _ = inter(M["sleeve_closed"].translate([0, 0, -1.6]), M["body"])
check(v > ZERO, f"closed detent: 1.6 mm toward open the bump climbs the ridge ({v:.2f} mm³) → holds closed")
v, _ = inter(M["sleeve_open"].translate([0, 0, -0.3]), M["body"]); v0, _ = inter(M["sleeve_open"], M["body"])
check(v > v0 + 0.5, "open stop: the bump hits the channel end wall")
v, _ = inter(M["sleeve_closed"].translate([0, 0, 0.35]), M["top_cap"])
check(v > ZERO, "closed stop: the sleeve's top edge lands on the dome's 45° lip")
lo_s, hi_s = bbox(M["sleeve_closed"]); lo_o, hi_o = bbox(M["sleeve_open"])
check(lo_s[2] <= P["Zw0"] and hi_s[2] >= P["z_win_top"], f"CLOSED: sleeve covers the panel AND the clear ring (z {lo_s[2]:.1f}…{hi_s[2]:.1f} ⊇ {P['Zw0']:.1f}…{P['z_win_top']:.1f}): a plain fluted tube")
check(hi_o[2] <= P["Zw0"] + 0.01, f"OPEN: sleeve top at z={hi_o[2]:.1f} ≤ window bottom {P['Zw0']:.1f}: ring and panel fully visible")
import math
bar_flat = P["bar_r"] * math.sqrt(2)   # narrowest width of the diamond bar (flat to flat)
check(1.4 < bar_flat, f"clip: snap opening 1.40 mm < bar {bar_flat:.2f} mm → clicks on and stays")
for st in ("open", "closed"):
    v, _ = inter(M[f"clip_{st}"], M[f"sleeve_{st}"]); check(v <= ZERO, f"clip ({st}) clear of the sleeve")
v, ic = inter(M["cells"], M["sled"]); lo, hi = bbox(ic)
check(v > 0 and v <= 80, f"battery: {P['battery']} stack clamped between the sprung bulkheads ({P['batt_preload']} mm preload)")
for k in ("led_red", "led_white"):
    for o in ("sled", "top_cap", "body"):
        v, _ = inter(M[k], M[o])
        if v > ZERO: check(False, f"{k} collides with {o}")
for nm, tip in (("red", P["red_tip"]), ("white", P["wht_tip"])):
    check(P["z_win_bot"] + 1 < tip < P["z_win_top"] - 1, f"{nm} LED tip z={tip:.1f} sits inside the clear ring ({P['z_win_bot']:.1f}…{P['z_win_top']:.1f})")
out()

# ================================================================== 7 text
out("## 6. Raised detail stroke widths (window panel)\n")
from skimage.morphology import skeletonize, opening, disk
from scipy import ndimage
from PIL import Image, ImageDraw
pm = tm(str(STL / "window_panel.stl"))
res = 40.0  # px / mm
def raster(z, crop=None):
    sec = pm.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    path, _ = sec.to_2D(to_2D=np.eye(4))
    lo = np.array([-7.0, -5.0]); W, H = int(14 * res), int(85 * res)
    img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
    px = lambda x, y: ((x - lo[0]) * res, (y - lo[1]) * res)
    for p in path.polygons_full:
        d.polygon([px(x, y) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors:
            d.polygon([px(x, y) for x, y in h.coords], fill=0)
    a = np.array(img) > 0
    if crop is not None:
        m = np.zeros_like(a)
        for (x0, x1, y0, y1) in crop:
            m[int((y0 - lo[1]) * res):int((y1 - lo[1]) * res), int((x0 - lo[0]) * res):int((x1 - lo[0]) * res)] = True
        a &= m
    return a
# panel print pose: Y = (distance from window bottom) + 2.0
maf_crop  = [(-4.9, 4.9, 72 - 49 + 2.0 - 1.9, 72 - 49 + 2.0 + 1.9)]
disp_crop = [(-5.0, 5.0, 72 - 63 + 2.0 - 2.5, 72 - 63 + 2.0 + 2.5)]
for name, z, crop in (("raised labels / arrows / dots", P["panel_t"] + 0.3, None),
                      ("M A F letters (inside recessed plate)", P["panel_t"] - 0.3, maf_crop),
                      ("8888 display segments", P["panel_t"] - 0.4, disp_crop)):
    a = raster(z, crop)
    # sweep a 0.42 mm "extrusion line" over the feature (morphological opening): a stroke
    # narrower than one line disappears completely, a printable one keeps nearly all its area
    op = opening(a, disk(int(round(0.42 * res / 2))))
    lab, n = ndimage.label(a)
    kept = [(op & (lab == i)).sum() / (lab == i).sum() for i in range(1, n + 1)]
    dt = ndimage.distance_transform_edt(a) / res
    widths = 2 * dt[skeletonize(a) & (dt > 0.075)]
    if crop is None:
        # every letter must be its own island (fattened letters must not fuse together)
        for word, v, nlet, hw in (("MINUTES", 15.0, 7, 6.6), ("HOURS", 29.0, 5, 6.6), ("WEEKS", 42.5, 5, 6.6), ("YEAR", 55.0, 4, 4.3)):
            yc = 72 - v + 2.0
            band = np.zeros_like(a); band[int((yc - 1.3 + 5) * res):int((yc + 1.3 + 5) * res), int((-hw + 7) * res):int((hw + 7) * res)] = True
            k = ndimage.label(a & band)[1]
            check(k == nlet, f"label {word}: {k} separate letters (expected {nlet}) - letters do not fuse")
            xs = np.nonzero((a & band).any(axis=0))[0]
            check((xs.max() - xs.min()) / res <= 12.2, f"label {word}: {(xs.max()-xs.min())/res:.1f} mm wide, fits the 13 mm panel")
    check(min(kept) >= 0.85, f"{name}: {n} features, every one keeps ≥ {min(kept)*100:.0f}% of its area under a 0.42 mm line "
          f"sweep (none thinner than a 0.4 mm nozzle line); median stroke {np.median(widths):.2f} mm")
out()

# ================================================================== summary
out("## Summary\n")
out(f"**{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' CHECK(S) FAILED'}**")
for f in fails: out(f"- {f}")
(ROOT / ("VERIFICATION.md" if not BATT else f"VERIFICATION_{BATT}.md")).write_text("# Verification report\n\nGenerated by `tools/verify.py` from the exported STLs "
    f"(battery `{P['battery']}`).\n\n" + "\n".join(lines) + "\n")
sys.exit(1 if fails else 0)
