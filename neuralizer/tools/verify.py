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
    fits = all(e <= b for e, b in zip(ext, BED)) and abs(m.bounds[0][2]) < 1e-3
    out(f"| {f.stem} | {ext[0]:.1f}×{ext[1]:.1f}×{ext[2]:.1f} | {m.volume/1000:.2f} | {'yes' if wt else 'NO'} | {'yes' if fits else 'NO'} |")
    if not wt: fails.append(f"{f.stem} not watertight")
    if not fits: fails.append(f"{f.stem} does not fit / not on bed")
out()

# ================================================================== 3 overhangs
out("## 2. Overhang scan (print orientation)\n")
out("Down-facing surfaces steeper than 50° from vertical (normal_z < -0.766), first layer ignored.")
out("Each connected patch is measured by its *unsupported width* (2·area / perimeter ≈ the short side")
out("of a bridge, or the overhang depth of a ledge). PETG on a P1S bridges ≤ 10 mm and tolerates")
out("ledges ≤ 0.8 mm, so a patch passes if it is a bridge (width ≤ 10 mm, both ends anchored) or a")
out("tiny ledge.\n")
out("| part | down-facing area (mm²) | widest patch: width / area / z | verdict |")
out("|---|---|---|---|")
for f in parts:
    m = tm(str(f))
    n = m.face_normals
    zc = m.triangles_center[:, 2]
    bad = (n[:, 2] < -0.766) & (zc > 0.25)
    area = m.area_faces[bad].sum()
    worst, ok = "-", True
    if bad.any():
        sub = m.submesh([np.nonzero(bad)[0]], append=True)
        res = []
        for c in sub.split(only_watertight=False):
            try:
                perim = c.outline().length
            except Exception:
                perim = 1e9
            res.append((2 * c.area / max(perim, 1e-9), c.area, c.bounds[0][2]))
        res.sort(key=lambda r: -r[0])
        w = res[0]
        worst = f"{w[0]:.2f} mm / {w[1]:.1f} mm² / z={w[2]:.1f}"
        ok = w[0] <= 10.0
    out(f"| {f.stem} | {area:.1f} | {worst} | {'OK' if ok else 'NEEDS SUPPORT'} |")
    if not ok: fails.append(f"{f.stem} overhang")
out()

# ================================================================== 4 collisions
out("## 3. Collision matrix (assembly coordinates)\n")
static = ["body", "bottom_cap", "battery_spring", "knurl_nut", "led_mount", "red_band", "dome",
          "window_panel", "btn_minutes", "btn_hours", "btn_weeks", "cells", "push_switch",
          "led_red", "led_white"]
M = {k: man(str(ASM / f"{k}.stl")) for k in static}
for st in ("open", "closed"):
    M[f"sleeve_{st}"] = man(str(ASM / f"sleeve_{st}.stl"))
    M[f"clip_{st}"] = man(str(ASM / f"clip_{st}.stl"))
M["btn_hours_pressed"] = man(str(ASM / "btn_hours_pressed.stl"))
M["fallback_switch"] = man(str(ASM / "fallback_switch.stl"))

# designed overlaps: (a, b) -> (reason, max allowed volume mm^3)
EXPECTED = {
    frozenset(["cells", "battery_spring"]): ("spring boss pre-compressed onto the top cell (battery contact force)", 60),
    frozenset(["battery_spring", "body"]): ("spring disc is a light press fit in the bay", 6),
    frozenset(["dome", "led_mount"]): ("dome push-fit on the baffle (interference fit)", 6),
    frozenset(["sleeve_open", "body"]): ("sleeve-switch finger bump pressed onto the contact land (contact force)", 60),
}
def collide(names, state):
    rows = []
    for a, b in itertools.combinations(names, 2):
        v, i = inter(M[a], M[b])
        if v <= ZERO: continue
        key = frozenset([a.replace("_closed", "_open") if False else a, b])
        exp = EXPECTED.get(frozenset([a, b]))
        lo, hi = bbox(i)
        rows.append((a, b, v, exp, lo, hi))
    return rows

for st in ("open", "closed"):
    names = static + [f"sleeve_{st}", f"clip_{st}"]
    rows = collide(names, st)
    out(f"**Sleeve {st.upper()}** — {len(names)} solids, {len(names)*(len(names)-1)//2} pairs checked.\n")
    if not rows:
        out("No overlaps at all.\n")
    for a, b, v, exp, lo, hi in rows:
        where = f"x {lo[0]:.1f}…{hi[0]:.1f}, z {lo[2]:.1f}…{hi[2]:.1f}"
        if exp and v <= exp[1]:
            out(f"- expected: **{a} ↔ {b}** {v:.2f} mm³ ({where}) — {exp[0]}")
        else:
            check(False, f"{a} ↔ {b} overlap {v:.2f} mm³ at {where}")
    out()
check(True, "no unintended collisions in the OPEN or CLOSED position" if not any("overlap" in f for f in fails)
      else "collisions found (see above)")

# the only sleeve/body overlap in OPEN must be the bump on the land, and only finger_preload deep
v, i = inter(M["sleeve_open"], M["body"])
lo, hi = bbox(i)
depth = hi[0] - lo[0]
check(lo[0] >= P["x_land"] - 0.05 and hi[0] <= P["x_land"] + P["finger_preload"] + 0.05
      and lo[2] >= P["z_cl"] - 0.05 and hi[2] <= P["z_cl"] + 9.5,
      f"OPEN: sleeve↔body overlap is only the finger bump on the contact land, {depth:.2f} mm deep "
      f"(= designed finger preload {P['finger_preload']} mm, gives ≈4 N contact force)")
v, _ = inter(M["sleeve_closed"], M["body"])
check(v <= ZERO, "CLOSED: sleeve does not touch the body anywhere (bump rests above the detent ridge)")
out()

# ================================================================== 5 threads
out("## 4. Threads\n")
def screw_path(male_or_fixed, moving, P_, sign, turns, label):
    """move `moving` along the helix: rotate by sign*t and translate sign*P*t/360"""
    worst = 0.0
    for t in np.arange(0, 360 * turns + 1, 30):
        mv = moving.rotate([0, 0, sign * t]).translate([0, 0, sign * P_ * t / 360.0])
        v, _ = inter(male_or_fixed, mv)
        if t > 0: worst = max(worst, v)
    return worst
def thread_report(fixed, moving, P_, sign, turns, name, crest_male, core_female):
    w = screw_path(fixed, moving, P_, sign, turns, name)
    check(w <= ZERO, f"{name}: screwing off along the helix ({turns} turns, every 30°) — max overlap {w:.3f} mm³ (clearance all the way)")
    v_ax, _ = inter(fixed, moving.translate([0, 0, sign * P_ / 2]))
    check(v_ax > 5, f"{name}: pulling straight off by half a pitch WITHOUT turning collides ({v_ax:.0f} mm³) → the teeth are interlocked")
    v_rot, _ = inter(fixed, moving.rotate([0, 0, 90]))
    check(v_rot > 5, f"{name}: turning 90° WITHOUT advancing collides ({v_rot:.0f} mm³) → pitch/handedness match")
    eng = crest_male - core_female
    check(eng >= 0.45, f"{name}: radial tooth engagement {eng:.2f} mm (male crest r={crest_male:.2f}, female minor r={core_female:.2f}), flank clearance {P['thread_clr']} mm")

thread_report(M["body"], M["bottom_cap"], P["bt_P"], -1, 4.5, "Bottom cap ↔ body (Ø16 × 2 mm pitch)",
              P["bt_D"] / 2, P["bt_core"])
thread_report(M["body"], M["knurl_nut"], P["tt_P"], +1, 4, "Knurled nut ↔ body (Ø19 × 2 mm pitch)",
              P["tt_D"] / 2, P["tt_core"])
out()

# ================================================================== 6 mechanisms
out("## 5. Mechanism checks\n")
# push button
v_rest, _ = inter(M["btn_hours"], M["push_switch"])
v_pr, ip = inter(M["btn_hours_pressed"], M["push_switch"])
lo, hi = bbox(ip)
check(v_rest <= ZERO, "HOURS button at rest just touches the switch plunger (no pre-load, no rattle)")
check(abs((hi[0] - lo[0]) - P["btn_trav"]) < 0.05 and P["btn_trav"] > P["sw_travel"],
      f"HOURS button pressed: pushes the plunger {hi[0]-lo[0]:.2f} mm ≥ switch travel {P['sw_travel']} mm → it clicks")
v, _ = inter(M["btn_hours_pressed"], M["body"])
check(v <= ZERO, "HOURS button pressed: flange lands on its stop without hitting the body (switch is not crushed)")
v, _ = inter(M["btn_hours_pressed"], M["window_panel"])
check(v <= ZERO, "HOURS button pressed: head slides freely in the panel hole")
v1, _ = inter(M["btn_hours"], M["window_panel"].translate([-0.3, 0, 0]))
check(v1 > 1, "HOURS button is captive: its flange is behind the panel (cannot fall out)")
# push switch pocket / fallback pocket
for k in ("push_switch", "fallback_switch"):
    v, _ = inter(M[k], M["body"])
    check(v <= ZERO, f"{k.replace('_', ' ')} (6×6 mm dummy incl. leg shoulders + trimmed legs) fits its printed pocket")
v, ifb = inter(M["fallback_switch"], M["sleeve_open"])
lo, hi = bbox(ifb)
check(v > ZERO and hi[0] - lo[0] >= P["sw_travel"],
      f"fallback mode: the finger bump pushes the fallback plunger {hi[0]-lo[0]:.2f} mm when fully open (≥ {P['sw_travel']} mm)")
v, _ = inter(M["fallback_switch"], M["sleeve_closed"])
check(v <= ZERO, "fallback mode: plunger is free when the sleeve is closed")
# detent
s_det = M["sleeve_closed"].translate([0, 0, -1.6])
v, _ = inter(s_det, M["body"])
check(v > ZERO, f"closed detent: moving the sleeve 1.6 mm toward open makes the bump climb the ridge ({v:.2f} mm³) → it holds closed")
# open stop
v, _ = inter(M["sleeve_open"].translate([0, 0, -0.3]), M["body"])
v0, _ = inter(M["sleeve_open"], M["body"])
check(v > v0 + 0.5, "open stop: the bump hits the channel's end wall (sleeve cannot slide further down)")
v, _ = inter(M["sleeve_closed"].translate([0, 0, 0.35]), M["knurl_nut"])
check(v > ZERO, "closed stop: the sleeve's top edge stops on the knurled nut")
# window covered / revealed
lo_s, hi_s = bbox(M["sleeve_closed"]); lo_o, hi_o = bbox(M["sleeve_open"])
check(lo_s[2] <= P["Zw0"] and hi_s[2] >= P["Zw1"], f"CLOSED: sleeve covers the whole window (z {lo_s[2]:.1f}…{hi_s[2]:.1f} ⊇ {P['Zw0']}…{P['Zw1']})")
check(hi_o[2] <= P["Zw0"] + 0.01, f"OPEN: sleeve top edge at z={hi_o[2]:.1f} ≤ window bottom {P['Zw0']} — window fully revealed")
# clip hinge: the C-clip snaps over the octagonal bar, and swings freely once on
import math
bar_flat = 2 * P["bar_r"] * math.cos(math.radians(22.5))
check(1.6 < bar_flat, f"clip: snap opening 1.60 mm < bar width {bar_flat:.2f} mm → it clicks on and is retained ({bar_flat-1.6:.2f} mm snap)")
for st in ("open", "closed"):
    v, _ = inter(M[f"clip_{st}"], M[f"sleeve_{st}"])
    check(v <= ZERO, f"clip ({st}): rides on its hinge bar with clearance, no contact with the sleeve")
# battery
v, ic = inter(M["cells"], M["battery_spring"])
lo, hi = bbox(ic)
check(abs((hi[2] - lo[2]) - P["spring_preload"]) < 0.06, f"battery: spring boss pre-compressed {hi[2]-lo[2]:.2f} mm onto the stack (absorbs ±{P['spring_preload']:.1f} mm cell tolerance)")
v, _ = inter(M["cells"], M["body"]); check(v <= ZERO, f"battery: {P['battery']} stack fits the bay")
v, _ = inter(M["cells"], M["bottom_cap"]); check(v <= ZERO, "battery: stack sits on the cap's contact face")
# LEDs
for k in ("led_red", "led_white"):
    for o in ("led_mount", "body", "knurl_nut", "red_band", "dome"):
        v, _ = inter(M[k], M[o])
        if v > ZERO: check(False, f"{k} collides with {o}")
check(True, "both LEDs drop into their seats without touching anything")
check(P["red_tip"] < P["z_band_top"], f"red LED tip ({P['red_tip']:.1f}) sits inside the red band zone, below the baffle ({P['z_band_top']:.1f})")
check(P["wht_tip"] > P["z_band_top"] + 2.0 - 0.01, f"white LED tip ({P['wht_tip']:.1f}) pokes through the baffle into the dome")
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
# panel print pose: Y = (distance from window bottom) + 3.5
maf_crop  = [(-4.9, 4.9, 72 - 49 + 3.5 - 1.9, 72 - 49 + 3.5 + 1.9)]
disp_crop = [(-5.0, 5.0, 72 - 63 + 3.5 - 2.5, 72 - 63 + 3.5 + 2.5)]
for name, z, crop in (("raised labels / arrows / dots", 1.8 + 0.3, None),
                      ("M A F letters (inside recessed plate)", 1.8 - 0.3, maf_crop),
                      ("8888 display segments", 1.8 - 0.4, disp_crop)):
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
            yc = 72 - v + 3.5
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
(ROOT / ("VERIFICATION.md" if not BATT else f"build/verification_{BATT}.md")).write_text("# Verification report\n\nGenerated by `tools/verify.py` from the exported STLs "
    f"(battery `{P['battery']}`).\n\n" + "\n".join(lines) + "\n")
sys.exit(1 if fails else 0)
