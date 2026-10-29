# Assembly tutorial: MIB Neuralizer

**About 20–25 minutes after printing, about 10 of them soldering.** Nothing is threaded through the body any more. All the electronics sit on one printed **sled** that you wire on the bench and then drop into the body from the top. There is no copper tape, no glue, no screws and no springs. The mechanical parts all click or screw together by hand.

You need:
- a soldering iron and solder;
- side cutters;
- your own 2 tactile switches, 2 LEDs, 2 resistors and a little wire (nothing extra to buy);
- 3 LR44 cells, the only thing on the shopping list in [BUILD_GUIDE.md](BUILD_GUIDE.md).

![finished](images/preview_closed_open.png)

| Step | What | Time |
|---|---|---|
| 0 | Print | — |
| 1 | Sleeve, clip, bottom cap | 2 min |
| 2 | Window panel + HOURS button | 1 min |
| 3 | Wire the sled | 12–15 min |
| 4 | Batteries | 1 min |
| 5 | Sled into the body | 30 s |
| 6 | Top cap | 30 s |
| 7 | Test | 30 s |

---

## Step 0: Print

Open **`3mf/neuralizer_P1S_PETG_project.3mf`** in Bambu Studio. It loads as a project with 4 plates and 3 filament slots.

| Slot | Filament | Used for |
|---|---|---|
| 1 | **White PETG** | body, sleeve, sled, bottom cap, clip, panel, HOURS button, top-cap dome |
| 2 | **Black PETG** | panel labels and buttons, top of the HOURS button |
| 3 | **Clear PETG** | top-cap spigot and light ring |

![plates](images/print_plates.png)

1. **Map the slots.** On *Sync / AMS mapping*, point slot 1 at white, slot 2 at black and slot 3 at clear.
   - Plates 3 (panel + HOURS button) and 4 (top cap) use the AMS.
   - Plates 1 and 2 use white only.
2. **Print plate 1 first: the test parts.**
   - The ring with the right number of notches should slide over the stub.
   - The thread ring should spin on by hand.
   - If either is wrong, adjust `slide_clr` / `thread_clr` (BUILD_GUIDE.md §7) and regenerate before printing plates 2–4.
3. **Leave the per-object settings alone.** Supports stay **off**.
4. **Remove the brims.** Deburr the sleeve bore and the body's back channel with a fingernail.

**Optional paint** (chrome look): body, sleeve, clip and bottom cap.
- Mask the sleeve bore, the back channel, the threads and the window recess.
- Leave the panel, sled and top cap unpainted.

---

## Step 1: Sleeve, clip, bottom cap

![step 1](images/assembly/step_01.png)

1. **Sleeve:** slide it onto the body from the **bottom**, with the finger at the back in line with the back channel. Push until the finger's bump **clicks** into the channel. From then on it can't fall off.
2. **Clip:** snap it onto the bar on the sleeve.
3. **Bottom cap:** screw it on hand-tight. It is decorative; nothing electrical touches it.

---

## Step 2: Window panel + HOURS button

![step 2](images/assembly/step_02.png)

1. Slide the sleeve **down** (open) so the window is free.
2. **Load the button:** lay the panel face down and drop the HOURS button into the middle hole from behind. Its thin flange sits in the round recess in the panel's back.
3. **Fit the panel:**
   - Hold the button in with a finger.
   - Push the panel's **top tongue** into the slot above the window.
   - Lay the panel flat into the window.
   - Slide it **down 2 mm** until both tongues sit in their slots and the detents **click**.

MINUTES and WEEKS are printed into the panel. Only HOURS moves.

---

## Step 3: Wire the sled

![step 3](images/assembly/step_03.png)
![wiring](images/wiring.png)

Everything happens on the bench, with the sled lying on its spine.

1. **Switches:**
   - Trim the legs of both 6×6 switches to about 1.5 mm.
   - **S2 (HOURS):** press it into the pocket under the LED head, plunger toward the front (+x, the side the panel faces).
   - **S1 (sleeve):** press it into the pocket at the bottom end, plunger toward the back.
2. **LEDs and resistors:**
   - Solder the 270 Ω resistor to the red LED's long leg, and the 82 Ω resistor to the white LED's long leg.
   - Push the legs down through the two holes in the LED head until the LED rims sit in their seats. **Red** goes on the side nearest the S2 plunger.
   - The resistors lie in the bay under the head.
3. **Wires:** run them along the notches either side of the spine. Each is 25–70 mm long; the lengths are in the diagram.
   - **B+ (red):** strip and tin 4 mm at one end. Push it through the hole in the **top** bulkhead and bend it flat against the bulkhead's lower face, which is where the + side of the cells will press. Run it down to one S1 leg.
   - **N (orange):** from the other S1 leg up to one S2 leg, and on to the 270 Ω resistor.
   - **X (yellow):** from the S2 leg on the opposite side to the 82 Ω resistor.
   - **B− (black):** a tinned end through the hole in the **bottom** bulkhead, bent flat against its upper face. Run it up to **both** LED short legs.
4. **Test before batteries go in.** Hold 3 cells against the two bent wire ends. Press S1 and red should light; press S1 and S2 together and white should light too.

---

## Step 4: Batteries

![step 4](images/assembly/step_04.png)

Stack **3 × LR44** with **+ (the flat, marked side) toward the LEDs**. Push the stack in **sideways** between the two bulkheads. The bulkheads flex 0.5 mm and clamp it onto the wire contacts; they act as the battery spring.

To change batteries later, undo steps 6 and 5 (cap off, sled out), swap the cells and put it back. That takes about a minute.

---

## Step 5: Sled into the body

![step 5](images/assembly/step_05.png)

1. **Close the sleeve first** (slide it all the way up). When it is open, it pushes the switch tongue into the bore, and the tongue would catch S1.
2. Slide the sled into the top of the body with its spine on the same side as the clip, where it runs in a keyway. It only fits one way round.
3. Push until the LED flange sits on the cone at the top of the bore.

---

## Step 6: Top cap

![step 6](images/assembly/step_06.png)

Screw the top cap (clear ring + white dome) on hand-tight. Its spigot clamps the sled's LED flange, so nothing rattles.

---

## Step 7: Test

![step 7](images/assembly/step_07.png)

| Action | Expected |
|---|---|
| Slide the sleeve **down** | It clicks against its stop and the clear ring glows **red** |
| Press **HOURS** | **White** flash through the same ring |
| Slide the sleeve **up** | Everything goes off, and the panel and ring are hidden: a plain fluted tube |

If something doesn't work, see *Troubleshooting* in [BUILD_GUIDE.md](BUILD_GUIDE.md#10-troubleshooting).
