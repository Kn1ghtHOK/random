#!/usr/bin/env bash
# Exports every part (plus dummy cells/LEDs/switches) in ASSEMBLY coordinates
# for the open and closed sleeve states.  Used by tools/verify.py.
set -e
# optional: BATTERY=AAAx3 tools/...  to build another battery variant
BOPT=()
[ -n "$BATTERY" ] && BOPT=(-D "battery=\"$BATTERY\"")
cd "$(dirname "$0")/.."
OUT=build/assembled; mkdir -p $OUT logs
STATIC="body bottom_cap battery_spring knurl_nut led_mount red_band dome window_panel btn_minutes btn_hours btn_hours_pressed btn_weeks cells push_switch fallback_switch led_red led_white"
for p in $STATIC; do
  openscad "${BOPT[@]}" -o $OUT/$p.stl -D "part=\"$p\"" -D 'pose="assembled"' neuralizer.scad > logs/asm_$p.log 2>&1 &
done
for st in open closed; do for p in sleeve clip; do
  openscad "${BOPT[@]}" -o $OUT/${p}_$st.stl -D "part=\"$p\"" -D 'pose="assembled"' -D "sleeve_state=\"$st\"" neuralizer.scad > logs/asm_${p}_$st.log 2>&1 &
done; done
wait
ls $OUT | wc -l
