#!/usr/bin/env bash
# Exports every printable part (print orientation) to stl/, in parallel, then makes the
# exact colour splits (panel, top cap, HOURS button).
set -e
# optional: BATTERY=LR44x4 tools/...  to build another battery variant
BOPT=()
[ -n "$BATTERY" ] && BOPT=(-D "battery=\"$BATTERY\"")
cd "$(dirname "$0")/.."
mkdir -p stl logs
PARTS="body sleeve sled bottom_cap top_cap top_cap_zone window_panel panel_detail_zone btn_hours btn_zone clip fit_test thread_test"
for p in ${@:-$PARTS}; do
  ( s=$(date +%s); openscad "${BOPT[@]}" -o stl/$p.stl -D "part=\"$p\"" neuralizer.scad > logs/$p.log 2>&1 \
      && echo "$p OK $(( $(date +%s)-s ))s" || echo "$p FAILED (see logs/$p.log)" ) &
done
wait
# OpenSCAD 2021 writes ASCII STL: weld + convert to binary, then split the multicolour parts
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
PY
python3 tools/split_colours.py stl
