#!/usr/bin/env python3
"""Exact multicolour splits with manifold3d booleans (CGAL leaves slivers on coplanar faces).
   part ∩ zone -> <second colour>, part − zone -> <first colour>.   Usage: split_colours.py <dir>"""
import sys, os, numpy as np, trimesh, manifold3d as mf
d = sys.argv[1]
SPLITS = [("window_panel", "panel_detail_zone", "window_panel_base", "window_panel_details"),   # white / black
          ("top_cap", "top_cap_zone", "top_cap_clear", "top_cap_white"),                        # clear / white
          ("btn_hours", "btn_zone", "btn_hours_base", "btn_hours_top")]                          # white / black
M = lambda t: mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
for part, zone, a_name, b_name in SPLITS:
    pf, zf = f"{d}/{part}.stl", f"{d}/{zone}.stl"
    if not (os.path.exists(pf) and os.path.exists(zf)):
        continue
    P, Z = M(trimesh.load(pf, force="mesh")), M(trimesh.load(zf, force="mesh"))
    for name, r in ((a_name, P - Z), (b_name, P ^ Z)):
        r = sum((c for c in r.decompose() if c.volume() > 0.01), mf.Manifold())
        o = r.to_mesh(); trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts).export(f"{d}/{name}.stl")
    os.remove(zf)
