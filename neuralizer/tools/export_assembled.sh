#!/usr/bin/env bash
# Exports every part (plus dummy cells/LEDs/switches) in ASSEMBLY coordinates
# for the open and closed sleeve states.  Used by tools/verify.py.
set -e
# optional: BATTERY=AAAx3 tools/...  to build another battery variant
BOPT=()
[ -n "$BATTERY" ] && BOPT=(-D "battery=\"$BATTERY\"")
cd "$(dirname "$0")/.."
OUT=build/assembled; mkdir -p $OUT logs
STATIC="body bottom_cap battery_spring knurl_nut led_mount light_window dome window_panel panel_detail_zone btn_minutes btn_hours btn_hours_pressed btn_weeks cells push_switch fallback_switch led_red led_white tape_body tape_cap tape_bump_open tape_bump_closed"
for p in $STATIC; do
  openscad "${BOPT[@]}" -o $OUT/$p.stl -D "part=\"$p\"" -D 'pose="assembled"' neuralizer.scad > logs/asm_$p.log 2>&1 &
done
for st in open closed; do for p in sleeve clip; do
  openscad "${BOPT[@]}" -o $OUT/${p}_$st.stl -D "part=\"$p\"" -D 'pose="assembled"' -D "sleeve_state=\"$st\"" neuralizer.scad > logs/asm_${p}_$st.log 2>&1 &
done; done
wait
python3 - <<'PY'
import trimesh, numpy as np, manifold3d as mf
d = "build/assembled"
M = lambda t: mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
P, Z = M(trimesh.load(f"{d}/window_panel.stl", force="mesh")), M(trimesh.load(f"{d}/panel_detail_zone.stl", force="mesh"))
for name, r in (("window_panel_base", P - Z), ("window_panel_details", P ^ Z)):
    r = sum((c for c in r.decompose() if c.volume() > 0.01), mf.Manifold()); o = r.to_mesh(); trimesh.Trimesh(o.vert_properties[:, :3], o.tri_verts).export(f"{d}/{name}.stl")
PY
ls $OUT | wc -l
