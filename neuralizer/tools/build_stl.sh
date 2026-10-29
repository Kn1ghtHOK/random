#!/usr/bin/env bash
# Exports every printable part (print orientation) to stl/, in parallel.
set -e
# optional: BATTERY=AAAx3 tools/...  to build another battery variant
BOPT=()
[ -n "$BATTERY" ] && BOPT=(-D "battery=\"$BATTERY\"")
cd "$(dirname "$0")/.."
mkdir -p stl logs
PARTS="body sleeve bottom_cap battery_spring knurl_nut led_mount light_window dome window_panel panel_detail_zone btn_minutes btn_hours btn_weeks clip fit_test thread_test"
for p in ${@:-$PARTS}; do
  ( s=$(date +%s); openscad "${BOPT[@]}" -o stl/$p.stl -D "part=\"$p\"" neuralizer.scad > logs/$p.log 2>&1 \
      && echo "$p OK $(( $(date +%s)-s ))s" || echo "$p FAILED (see logs/$p.log)" ) &
done
wait
# OpenSCAD 2021 writes ASCII STL; convert to binary (5x smaller) when trimesh is available
python3 - <<'PY' 2>/dev/null || true
import glob, trimesh, numpy as np
try:
    import manifold3d as mf
except ImportError:
    mf = None
for f in glob.glob("stl/*.stl"):
    m = trimesh.load(f, force="mesh")
    if mf is not None and not m.is_watertight:   # weld CGAL T-junctions into a clean 2-manifold
        mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
        if mm.status() == mf.Error.NoError:
            o = mm.to_mesh(); m = trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts)
    m.export(f, file_type="stl")
# multicolour window panel: exact boolean split (panel ∩ zone = black details, panel − zone = white base)
def split(dir_):
    import os
    a, z = f"{dir_}/window_panel.stl", f"{dir_}/panel_detail_zone.stl"
    if mf is None or not (os.path.exists(a) and os.path.exists(z)): return
    M = lambda t: mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    P, Z = M(trimesh.load(a, force="mesh")), M(trimesh.load(z, force="mesh"))
    for name, r in (("window_panel_base", P - Z), ("window_panel_details", P ^ Z)):
        r = sum((c for c in r.decompose() if c.volume() > 0.01), mf.Manifold()); o = r.to_mesh(); trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts).export(f"{dir_}/{name}.stl")
    os.remove(z)
split("stl")
PY
