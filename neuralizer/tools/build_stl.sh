#!/usr/bin/env bash
# Exports every printable part (print orientation) to stl/, in parallel.
set -e
# optional: BATTERY=AAAx3 tools/...  to build another battery variant
BOPT=()
[ -n "$BATTERY" ] && BOPT=(-D "battery=\"$BATTERY\"")
cd "$(dirname "$0")/.."
mkdir -p stl logs
PARTS="body sleeve bottom_cap battery_spring knurl_nut led_mount red_band dome window_panel btn_minutes btn_hours btn_weeks clip fit_test thread_test"
for p in ${@:-$PARTS}; do
  ( s=$(date +%s); openscad "${BOPT[@]}" -o stl/$p.stl -D "part=\"$p\"" neuralizer.scad > logs/$p.log 2>&1 \
      && echo "$p OK $(( $(date +%s)-s ))s" || echo "$p FAILED (see logs/$p.log)" ) &
done
wait
# OpenSCAD 2021 writes ASCII STL; convert to binary (5x smaller) when trimesh is available
python3 - <<'PY' 2>/dev/null || true
import glob, trimesh
for f in glob.glob("stl/*.stl"):
    m = trimesh.load(f, force="mesh"); m.export(f, file_type="stl")
PY
