#!/usr/bin/env bash
# Exports every part (plus dummy cells/LEDs/switches) in ASSEMBLY coordinates
# for the open and closed sleeve states.  Used by tools/verify.py and the renderer.
set -e
BOPT=()
[ -n "$BATTERY" ] && BOPT=(-D "battery=\"$BATTERY\"")
cd "$(dirname "$0")/.."
OUT=build/assembled; rm -rf $OUT; mkdir -p $OUT logs
STATIC="body bottom_cap sled top_cap top_cap_zone window_panel panel_detail_zone btn_hours btn_hours_pressed btn_zone cells s2_switch s1_switch led_red led_white"
for p in $STATIC; do
  openscad "${BOPT[@]}" -o $OUT/$p.stl -D "part=\"$p\"" -D 'pose="assembled"' neuralizer.scad > logs/asm_$p.log 2>&1 &
done
for st in open closed; do for p in sleeve clip; do
  openscad "${BOPT[@]}" -o $OUT/${p}_$st.stl -D "part=\"$p\"" -D 'pose="assembled"' -D "sleeve_state=\"$st\"" neuralizer.scad > logs/asm_${p}_$st.log 2>&1 &
done; done
wait
python3 - <<'PY'
import glob, trimesh
for f in glob.glob("build/assembled/*.stl"):
    trimesh.load(f, force="mesh").export(f)
PY
python3 tools/split_colours.py $OUT
ls $OUT | wc -l
