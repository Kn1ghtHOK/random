# MIB Neuralizer: Build Guide

A support-free PETG prop for a Bambu Lab P1S. It has no screws, springs, magnets or glue.
- **Sleeve slides down:** the clear window under the white dome glows **red** (ready).
- **Press HOURS while open:** a **white** flash shines through the same window.
- **Sleeve closed:** nothing lights.

![closed vs open](images/preview_closed_open.png)

**Quick start:**
1. Open `3mf/neuralizer_P1S_PETG_project.3mf` in Bambu Studio.
2. Map AMS slot 1 to white, slot 2 to black and slot 3 to clear PETG.
3. Print plate 1 (the test parts), then plates 2–5.
4. Assemble with [ASSEMBLY.md](ASSEMBLY.md).

---

## 0. Assumptions and safe defaults

| Topic | What I assumed | Safe default in `neuralizer.scad` |
|---|---|---|
| Tactile switch | No switch photo arrived with the request, so I assumed a standard 6×6 mm through-hole switch: 3.5 mm body + 1.5 mm plunger (5.0 mm total), 0.25 mm travel, legs on two opposite sides | `sw_w=6`, `sw_body_h=3.5`, `sw_plunger_h=1.5`, `sw_travel=0.25`. **Measure yours** (§8). |
| Battery | 1 AA (1.5 V) can't light the LEDs, and 2 AAA (3 V) barely can. A 4.5 V stack of AAA cells won't fit a slim prop. | **3 × LR44 / SR44 = 4.5 V**, a 16 mm stack. `battery`: `LR44x3`, `LR44x4` (6 V), `A23` (12 V), `AAAx3` (body grows to 245 mm) |
| LEDs | 5 mm through-hole; red Vf ≈ 2.0 V, white Vf ≈ 3.1 V; long leg = + | `led_d=5`, `led_rim_d=5.8`, `led_len=8.6` |
| Top look | White, opaque dome and nut, with one **clear window ring** between them. Both LEDs shine through it. | `window_h=5` |
| Colours | White, black and clear PETG, AMS for the window panel's black lettering. Everything else is single-colour. | slots 1/2/3 in the 3MF |
| Copper tape | Copper foil tape with conductive adhesive, about 0.1 mm thick | `tape_t=0.1` (depth of the pad recesses) |
| PETG fits | PETG needs more clearance than PLA | sliding 0.35 mm radial, threads 0.25 mm per flank, button holes 0.25 mm, push-fits 0.1 mm interference |
| Size | About 192 mm long, 20 mm body, 24.6 mm fluted sleeve | `body_d`, `window_len`, `sleeve_od` |
| Threads | Printed, 90° included angle (45° flanks print without supports), 2 mm pitch | bottom Ø16, top Ø19, `thread_clr=0.25` |
| Wires | Your circuit needs node **N** (between the two switches) at the top, for the red LED. So **3 wires** leave the LED head: N, X (the push-button pair) and B−. | 3.2 × 3.4 mm wire channel |

---

## 1. Files

| Path | What it is |
|---|---|
| **`3mf/neuralizer_P1S_PETG_project.3mf`** | **Bambu Studio project.** 5 plates, 3 filament slots, per-object settings, multicolour window panel, plate thumbnails |
| `3mf/parts/*.3mf` | One 3MF per part, for any slicer. Carries colour slot and print settings. |
| `ASSEMBLY.md` | Step-by-step assembly tutorial with pictures |
| `neuralizer.scad` | The parametric model (*Window → Customizer*) |
| `stl/*.stl` | The same parts as STL, in print orientation |
| `VERIFICATION.md` | Proof report: collisions, threads, mechanisms, overhangs, bed fit, text, 3MF validation |
| `images/` | Previews, top window, cutaway, exploded view, print plates, wiring, assembly steps |
| `tools/` | `build_stl.sh`, `export_assembled.sh`, `verify.py`, `make_3mf.py`, `check_3mf.py`, renderers |

Rebuild everything after changing a parameter. You need OpenSCAD plus `pip install trimesh manifold3d scipy scikit-image pillow lib3mf`.

```bash
cd neuralizer && tools/build_stl.sh && tools/export_assembled.sh && python3 tools/verify.py && python3 tools/make_3mf.py && python3 tools/check_3mf.py
```

---

## 2. Shopping list (only what you said you don't have)

| Item | Qty | Notes |
|---|---|---|
| **LR44 button cells** (also sold as A76, AG13, L1154, 357; **SR44** silver-oxide is best) | 3 + spares | All the same size. SR44 holds its voltage better. |
| **Copper foil tape, 5–6 mm wide, with conductive adhesive** | ~1 m | Sleeve switch, battery contacts, spring pad |
| Spray filler-primer + gloss black + chrome/bright-silver spray | 1 can each | Only for the chrome look (§5) |
| Wet/dry sandpaper 240 / 400 / 800 | 1 each | |
| *Optional:* 28 AWG silicone wire in 4 colours, small heat-shrink | | Much easier to thread than 22 AWG solid wire (which does fit) |
| *Optional:* graphite powder or a dab of silicone grease | | Smoother slide |
| *Optional:* red paint marker | | Arrows / display digits, if you want them red like the film prop |

---

## 3. Print plan: what's in the 3MF project

![plates](images/print_plates.png)

| Plate | Filament | Parts | Notes |
|---|---|---|---|
| **1 Test prints** (print first) | 1 white | `fit_test`, `thread_test` | ≈ 30 min. Tune the fits before the long prints (§7). |
| **2 White parts** | 1 white | body, sleeve, bottom cap, knurled nut, dome, LED head, clip, battery spring | Body: 5 mm brim. Sleeve: printed top-edge down with a 3 mm brim. Back seams. |
| **3 Window panel** | **1 white + 2 black (AMS)** | window panel | Black only in the top 2.4 mm: labels, arrows, YEAR dots, and the M A F plate and display floors. About 11 colour changes in total. |
| **4 Black buttons** | 2 black | MINUTES, HOURS, WEEKS | |
| **5 Clear window** | 3 clear | light window | 100 % infill for an even glow |

The settings are stored per object, so you don't have to set anything:

| Object | Layer | Walls | Infill |
|---|---|---|---|
| body, sleeve | 0.16 | 4 / 3 | 15 % gyroid |
| caps, nut, LED head | 0.12 | 4 / 3 | 30 % gyroid |
| dome | 0.16 | 4 | 30 % |
| panel | 0.12 | 3 | 100 % |
| buttons, clip, spring | 0.12 | 2–3 | 100 % |
| light window | 0.16 | 2 | 100 % |

- **Global settings:** printer *Bambu Lab P1S 0.4 nozzle*, process *0.16mm Optimal*, filament *Generic PETG* ×3 (swap in your own brand's preset if you like), Textured PEI plate, supports off.
- **Purge volumes** for the white ↔ black panel plate are pre-set: 160 mm³ white→black, 560 mm³ black→white.
- **Without an AMS:**
  - Print plate 3 in white only: right-click the panel's "labels" part and set it to filament 1. Then colour the raised letters with a black paint marker.
  - Or use a *colour change at layer* at 1.80 mm and again at 0.96 mm.
- **Clearances** are tuned for PETG. If plate 1 shows a different fit, change `slide_clr` / `thread_clr` and regenerate (§1).

---

## 4. Wiring

![wiring](images/wiring.png)

| `battery` | Voltage | Red LED (≈ 9 mA) | White LED (≈ 17 mA) | Body length |
|---|---|---|---|---|
| **LR44x3 (default)** | 4.5 V | **270 Ω** | **82 Ω** | 156 mm |
| LR44x4 | 6 V | 470 Ω | 150 Ω | 156 mm |
| A23 | 12 V | 1 kΩ | 470 Ω | 156 mm |
| AAAx3 | 4.5 V | 270 Ω | 82 Ω | 245 mm |

If you don't have the exact value, use the next value **up** (e.g. 100 Ω for 82 Ω, 330 Ω for 270 Ω). Don't go below 220 Ω (red) or 68 Ω (white) at 4.5 V.

---

## 5. Finish (aesthetics)

![top window](images/top_window.png)

- **Unpainted, straight off the printer:** white body with black buttons and black-lettered window. It reads like the white-panel replica in your first reference image.
- **Chrome look** (film prop):
  1. Sand the body, sleeve, caps, nut, dome and clip 240 → 400, filler-primer, then 800 wet.
  2. Spray gloss black, then chrome in light coats.
  3. **Mask:** the sleeve bore, the back channel and contact land, the threads, the window recess, the dome's inner cone, and the nut's lip hole.
- **Keep the window panel unpainted:** white with black print is the look. Optionally colour the two arrows and the display digits with a red marker, and the dot green.
- **Light window:** leave it glossy for a crisp ring, or frost it with 400 grit for a softer, even glow. The dome's white inner cone works as a reflector, pushing light out sideways through the window.

---

## 6. Assembly

Follow **[ASSEMBLY.md](ASSEMBLY.md)**: 11 illustrated steps.

![exploded](images/exploded.png)
![cutaway](images/cutaway.png)

**Fallback sleeve switch:** if the tape contact is unreliable, press a second 6×6 switch, plunger out, into the pocket in the middle of the back contact land.
Pull the P1 and P2 wires out through the pocket (their holes break into it) and solder them to two opposite legs. The bump then presses the plunger 0.85 mm when fully open.

---

## 7. Getting the sliding fit right (PETG)

1. **`fit_test`** (plate 1): a body stub plus three sleeve rings. 1 notch = `slide_clr − 0.1`, 2 = current, 3 = `+ 0.1`.
   - The right ring slides under its own weight with barely any wobble. Set `slide_clr` to its value.
2. **`thread_test`**: the real cap thread. It should spin on by hand. Tight → `thread_clr` + 0.05; sloppy → − 0.05.
3. Keep elephant-foot compensation on (the profile default). Seams are set to *back*: deburr the sleeve bore seam.
4. A few strokes of 400 grit on the body and a pinch of graphite give a buttery slide.
5. **Detent and contact force** come from the finger flexing:
   - `finger_preload` (0.5 mm) gives ≈ 4 N on the pads and holds the sleeve open.
   - A 0.65 mm ridge holds it closed.
   - Too stiff: 0.4. Flicker: 0.6.
6. Don't paint inside the sleeve or the channel.

---

## 8. Measure your tactile switch (calipers)

1. **Body width**, flat to flat → `sw_w` (6.0).
2. **Body height**, from the bottom of the plastic body (not the legs) to where the plunger starts → `sw_body_h` (3.5).
3. **Total height** to the plunger top. `sw_plunger_h` = total − body. Common totals: 4.3 / 5.0 / 6.0 / 7.0 / 8.0 / 9.5 mm.
4. **Travel to the click** → `sw_travel` (0.25).

The pocket depth, the button stop and the fallback pocket all follow automatically. Rebuild and re-run the checks (§1).

---

## 9. What was verified (numbers in `VERIFICATION.md`)

- **STLs:** all are closed manifold solids, on the bed, and fit 256 mm³. The body is the tallest at 156 mm.
- **Collisions:** every part pair in the **open** and **closed** positions, including dummy cells, LEDs, and switches with legs. The only overlaps are the designed ones:
  - spring preload (0.8 mm) and finger preload (0.5 mm);
  - the push-fits: spring disc, light window into nut, dome onto window.
- **Threads:** screwing off along the helix every 30° shows zero overlap. Pulling straight off or turning without advancing both collide, so the teeth are engaged. 0.51 mm engagement.
- **Mechanisms:**
  - The HOURS button clicks the switch (0.35 mm > 0.25 mm) and stops on its flange.
  - Both end-stops and the detent work, and the window is fully covered or revealed.
  - Both LED tips sit inside the clear window band.
  - The clip snap works.
- **Multicolour panel:** white base + black details rebuild the panel exactly, with no overlap. Every letter is a separate island, and no stroke is thinner than a 0.4 mm nozzle line.
- **3MF:**
  - All 16 files pass a strict read by **lib3mf** (the 3MF Consortium library).
  - The project follows Bambu Studio's loader rules (checked against its source): application tag, full P1S/PETG config, parts ↔ components, filament slots, plates inside the beds, no overlaps.
  - Every mesh is identical to the verified STLs.

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Red flickers while open | Burnish the pad tape flat. Make sure the bump tape wraps its edges. Raise `finger_preload` to 0.6, or use the fallback switch. |
| Nothing lights | Check the battery orientation (flat + side toward the cap). Screw the cap fully home so its tape touches the cone pad. |
| Red works, white never flashes | Make sure S2 is wired to legs on **opposite** sides. If your switch is shorter than 5 mm total, set `sw_plunger_h`. |
| Window glow is dim or patchy | Frost the window. Keep the dome's inner cone white (unpainted). Use SR44 cells. |
| Bambu Studio warns about presets | Accept. The project uses system *Generic PETG* / *0.16mm Optimal* presets, which you can swap for your own. |
| Sleeve won't click on | Ease the bump's 45° lead-in with a file. It needs about 2 mm of finger flex. |
| Nut or cap is tight | `thread_clr` = 0.3, then reprint that part only. |
