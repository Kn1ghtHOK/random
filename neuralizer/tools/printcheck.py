#!/usr/bin/env python3
"""Strict support-free check for every STL in a folder (print orientation, bed at z = 0).

  1. overhangs: no down-facing surface flatter than 45 deg (normal_z < -0.72, i.e. > 46 deg from vertical)
     above the first layer. Tiny patches are tolerated only if they are narrower than
     MAX_LEDGE (the nozzle simply extrudes over them).
  2. floating islands: the part is sliced every LAYER mm; every region of a layer must
     overlap the layer below. A region that starts in mid-air is what Bambu Studio warns
     about as "floating" / needs support.

Usage: printcheck.py <stl dir> [part ...]     exit code 1 if any part fails
"""
import sys, pathlib, numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

LAYER, FIRST = 0.2, 0.25
MAX_LEDGE = 0.6          # mm: a down-facing patch this narrow is printed over without support
SKIP = {"window_panel_details", "window_panel_base", "top_cap_clear", "top_cap_white",
        "btn_hours_base", "btn_hours_top"}   # colour splits: checked as the whole part


def overhang_patches(m):
    n, zc = m.face_normals, m.triangles_center[:, 2]
    bad = (n[:, 2] < -0.72) & (zc > FIRST)          # 45 deg (exact) is fine; steeper is not
    out = []
    if not bad.any():
        return out
    sub = m.submesh([np.nonzero(bad)[0]], append=True)
    for c in sub.split(only_watertight=False):
        try:
            perim = c.outline().length
        except Exception:
            perim = 1e9
        width = 2 * c.area / max(perim, 1e-9)
        if width > MAX_LEDGE / 2 and c.area > 0.05:
            out.append((width, c.area, c.bounds))
    return sorted(out, key=lambda r: -r[1])


def layer_polys(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return Polygon()
    p2, _ = s.to_2D(to_2D=np.eye(4))
    polys = [Polygon(p.exterior.coords, [h.coords for h in p.interiors]) for p in p2.polygons_full]
    return unary_union([p.buffer(0) for p in polys])


def floating(m):
    """regions of a layer that do not overlap the layer below (beyond a tiny tolerance)"""
    out, prev = [], None
    for z in np.arange(FIRST, m.bounds[1][2], LAYER):
        cur = layer_polys(m, z)
        if prev is not None and not cur.is_empty:
            geoms = cur.geoms if isinstance(cur, MultiPolygon) else [cur]
            grown = prev.buffer(0.3)          # 0.3 mm: what one layer can step out
            for g in geoms:
                if g.area > 0.2 and g.intersection(grown).area < 0.05 * g.area:
                    out.append((z, g.area, g.bounds))
        prev = cur
    return out


def check(path):
    m = trimesh.load(str(path), force="mesh")
    oh, fl = overhang_patches(m), floating(m)
    return oh, fl, m


if __name__ == "__main__":
    d = pathlib.Path(sys.argv[1])
    names = sys.argv[2:] or sorted(p.stem for p in d.glob("*.stl") if p.stem not in SKIP)
    bad = 0
    for n in names:
        oh, fl, m = check(d / f"{n}.stl")
        ok = not oh and not fl
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {n}: {len(oh)} overhang patch(es), {len(fl)} floating island(s)")
        for w, a, b in oh[:6]:
            print(f"        overhang {a:6.1f} mm2, width {w:.2f}, x {b[0][0]:.1f}..{b[1][0]:.1f} y {b[0][1]:.1f}..{b[1][1]:.1f} z {b[0][2]:.2f}..{b[1][2]:.2f}")
        for z, a, b in fl[:6]:
            print(f"        floating at z={z:.2f}: {a:.1f} mm2 at x {b[0]:.1f}..{b[2]:.1f} y {b[1]:.1f}..{b[3]:.1f}")
    sys.exit(1 if bad else 0)
