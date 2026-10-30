// =====================================================================
//  MEN IN BLACK NEURALIZER  -  parametric, support-free, PETG, no hardware
//  OpenSCAD 2021.01+   (Customizer friendly: Window > Customizer)
//
//  Coordinate system (assembly): Z = long axis, z = 0 is the bottom end
//  of the inner body.  +X = the window / buttons, -X = back (sleeve
//  switch finger), -Y = pocket-clip side (left when you face the window).
//
//  All electronics (cells, LEDs, resistors, both 6x6 tactile switches) live on
//  one printed SLED that is wired on the bench and slides into the body from the
//  top; the top cap screws down on it.  No wires are threaded through the body.
//  Every part prints without supports: no down-facing surface is flatter than
//  45 deg and nothing starts in mid-air (checked by tools/printcheck.py).
//
//  Export one part:   openscad -D 'part="body"' -o body.stl neuralizer.scad
//  (every part is placed in its print orientation unless pose="assembled")
// =====================================================================

/* [What to show] */
part = "assembly"; // [assembly, body, sleeve, sled, bottom_cap, top_cap, window_panel, btn_hours, clip, fit_test, thread_test, switch_test]
// Assembly view: sleeve position
sleeve_state = "open"; // [open, closed]
// Assembly view: cut away the near half to see inside
cutaway = false;
// Assembly view: light the LEDs (red when open, white = flash)
show_lit = true;
// "print" = on the bed in print orientation, "assembled" = in assembly coordinates (used by the checks)
pose = "print"; // [print, assembled]

/* [Battery] */
// LR44x3 = 3 x LR44/SR44/AG13/357 button cells (4.5 V)  <- default
battery = "LR44x3"; // [LR44x3, LR44x4, A23]

/* [6x6 tactile switches (HOURS + sleeve) - MEASURE YOURS with calipers] */
// square body size
sw_w = 6.0;
// body height: bottom of the plastic body to the top of the body (no plunger, no legs)
sw_body_h = 3.5;
// plunger height above the body
sw_plunger_h = 1.5;
// plunger travel to the click
sw_travel = 0.25;
// pocket clearance (total). 0.15 = snug PETG friction fit
sw_fit = 0.15;

/* [LEDs] */
led_d = 5.0;
led_rim_d = 5.8;
// rim (bottom of flange) to tip
led_len = 8.6;

/* [PETG clearances] */
// radial gap between sliding sleeve and body
slide_clr = 0.35;
// normal (flank) clearance on all printed threads
thread_clr = 0.25;
// radial gap for buttons in their holes
hole_clr = 0.25;
// small locating fits
fit_clr = 0.15;
// radial gap between the electronics sled and its bore
sled_clr = 0.25;
// how far the sleeve bump overlaps the switch tongue's pad when fully open
// (shared between the sleeve finger and the tongue; presses the sleeve switch)
pad_press = 1.0;

/* [Main dimensions] */
body_d = 20;
window_len = 72;
sleeve_od = 24.6;
flute_n = 20;
cap_d = 22;
// height of the clear light ring under the dome (hidden by the sleeve when closed)
window_h = 5.0;
// dome lip radius (also the sleeve's closed stop)
cap_lip_r = 11.3;

/* [Hidden] */
$fn = 160;
eps = 0.01;
FONT = "Liberation Sans:style=Bold";

// ------------------------------------------------------------- battery
BATT = [ // name, cell dia, cell length, cells, nominal volts
  ["LR44x3", 11.6,  5.4, 3,  4.5],
  ["LR44x4", 11.6,  5.4, 4,  6.0],
  ["A23",    10.3, 28.5, 1, 12.0]];
B = [for (b = BATT) if (b[0] == battery) b][0];
cell_d = B[1]; cell_l = B[2]; n_cells = B[3]; V_batt = B[4];

E12 = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2];
function e12_up(x) = let(d = pow(10, floor(log(x))), m = x / d,
   c = [for (e = E12) if (e >= m - 1e-9) e]) (len(c) ? c[0] : 10) * d;
R_RED   = e12_up((V_batt - 2.0) / 0.010);   // red  LED, Vf 2.0 V, ~10 mA
R_WHITE = e12_up((V_batt - 3.1) / 0.020);   // white LED, Vf 3.1 V, ~20 mA

// ------------------------------------------------------------- derived
R      = body_d / 2;

// bottom thread (decorative end cap), top thread (top cap)
bt_D = 16; bt_P = 2.0; bt_h = 0.8; bt_len = 7;
ct_D = 17; ct_P = 2.0; ct_h = 0.8; ct_len = 5;
fM = bt_D / 2 + thread_clr;
collar_h = 13.5;                               // body above the window: panel pocket, sled seat, cap thread

// sleeve travel: from "top edge at the window bottom" (open) to "top edge on the dome lip"
cap_gap = 0.2;                                 // cap shoulder sits this far above the body top
lip_engage = 0.95;                             // sleeve's top chamfer meets the dome's 45 deg lip here
travel  = window_len + collar_h + cap_gap + window_h + lip_engage;
s_open  = 0.5;
Lz_low  = travel + 4 + s_open;                 // length of the lower (sleeve) zone
Zw0 = Lz_low;                                  // window bottom
Zw1 = Lz_low + window_len;                     // window top
Zt  = Zw1 + collar_h;                          // top of body
Ls  = Lz_low - s_open;                         // sleeve length
s_pos = sleeve_state == "open" ? s_open : s_open + travel;
sl_ir = R + slide_clr;
sl_or = sleeve_od / 2;
Zwin0 = Zt + cap_gap; Zwin1 = Zwin0 + window_h;   // clear ring
top_closed = Zwin1 + lip_engage;

// back key channel + sleeve switch
ch_floor = 7.5;                                // floor distance from axis
ch_w     = 10.8;
bump_in  = ch_floor + slide_clr;               // bump face distance from axis
bump_w   = 10.0;
d_bump   = 16;                                 // bump top is this far below the sleeve top edge
z_cl     = Zw0 - d_bump - 8.5;                 // channel lower end = open stop
z_ridge  = z_cl + travel - 0.9;                // closed detent ridge
z_ch_top = z_cl + travel + 8.5 + 0.5;          // stays below the cap thread
x_pad    = -(bump_in + pad_press);             // switch-tongue pad surface
tongue_w = 6.0; tongue_root = 12; tongue_t = 1.4;   // flexure in the back wall
z_pc     = z_cl + 4;                           // sleeve switch (S1) height (under the pad)

// sled + bore
bore_r = 6.0; sled_r = bore_r - sled_clr;
spine = [[-2.75, 2.75], [-7.8, -5.0]];        // x, y range (runs in a keyway at -Y)
key_y = -5.4;                                  // sled sections are flat below this, 45 deg keel outside the spine
s1_tip = -(bore_r - 0.05);                     // S1 plunger tip (x), 0.05 behind the tongue

// front window
win_floor = bore_r;                            // panel back = bore tangent: the cells pass under it
panel_t   = 1.6;
win_w     = 13.3;
panel_w   = 13.0;
sw_tot    = sw_body_h + sw_plunger_h;
sw_pk     = (sw_w + sw_fit) / 2;               // half size of the 6x6 pocket
sw_tip    = bore_r - 0.1;                      // HOURS plunger tip: inside the bore, so the sled pulls out past it
sw_base   = sw_tip - sw_tot;
btn_gap   = 0.02;                              // HOURS button at rest: this far above the plunger
btn_trav  = btn_gap + sw_travel + 0.1;         // HOURS travel to its stop on the window floor (clicks + 0.1)
btn_fl_r  = 4.8;                               // flange radius; a 45 deg cone holds it in a countersink
btn_proud_h = 1.2;                             // HOURS head above the panel face
// buttons: name, centre (mm from window top), head dia, flange dia, moving
BTN = [["minutes", 8.0, 9.6, 9.6, false],
       ["hours",  22.5, 8.0, 9.6, true ],
       ["weeks",  36.0, 8.0, 9.6, false]];
btn_proud = 0.9;
hz = Zw1 - BTN[1][1];                          // HOURS button + switch centre

// LED head (top of the sled)
flange_r = 7.3; flange_t = 1.2;                 // r 7.3: its 45 deg keel stays inside the cap thread's core
led_x = 3.1;                                   // red at +x, white at -x
spig_ir = 6.3;                                 // light bore of the top cap
Zm = Zwin0 - ct_len - flange_t;                // flange bottom; the cap spigot clamps the flange
red_rim_z = (Zwin0 + window_h/2) - led_len - Zm;
wht_rim_z = red_rim_z;

// battery bay at the bottom of the sled (below the sleeve switch S1), so only one wire passes the cells
bh_t = 1.6; batt_preload = 0.5;
stack = n_cells * cell_l;
zbt = z_pc - 5 - 1.5;                          // top of the upper bulkhead (1.5 mm below the S1 holder: it flexes freely)
cb0 = zbt - bh_t + batt_preload - stack;       // bottom of the cell stack
z_sb = cb0 - bh_t;                             // bottom of the sled = underside of the lower bulkhead
// wiring: an open-top slot (the "trunk") through every holder, a full-depth slot through the upper
// bulkhead, and a channel under the cells. You lay the wires in from the top, like a cable tray.
tr_w = 0.8;                                    // trunk half width (1.6 mm slot: 28-24 AWG wire)
tr_y0 = 0.8;                                   // trunk floor (y)
ch_hw = 1.0;                                   // channel under the cells, half width

echo(str("=== NEURALIZER: battery ", battery, " = ", V_batt, " V,  red resistor ", R_RED,
         " ohm, white resistor ", R_WHITE, " ohm"));
echo(str("=== body ", Zt, " mm, sleeve ", Ls, " mm, travel ", travel, " mm, sled ", Zm + flange_t - z_sb,
         " mm, overall ~", Zwin1 + 12 + 17, " mm"));
// machine-readable values for tools/verify.py
echo(str("PARAMS {\"Zw0\":", Zw0, ",\"Zw1\":", Zw1, ",\"Zt\":", Zt, ",\"Ls\":", Ls, ",\"s_open\":", s_open,
  ",\"travel\":", travel, ",\"z_cl\":", z_cl, ",\"z_pc\":", z_pc, ",\"z_ridge\":", z_ridge, ",\"x_pad\":", x_pad,
  ",\"bump_in\":", bump_in, ",\"ch_floor\":", ch_floor, ",\"pad_press\":", pad_press, ",\"bt_P\":", bt_P, ",\"tt_P\":", ct_P,
  ",\"bt_D\":", bt_D, ",\"tt_D\":", ct_D, ",\"bt_h\":", bt_h, ",\"tt_h\":", ct_h, ",\"thread_clr\":", thread_clr,
  ",\"bt_core\":", tap_core(bt_D, bt_P, bt_h, thread_clr), ",\"tt_core\":", tap_core(ct_D, ct_P, ct_h, thread_clr),
  ",\"btn_trav\":", btn_trav, ",\"sw_travel\":", sw_travel, ",\"btn_gap\":", btn_gap, ",\"z_win_bot\":", Zwin0, ",\"z_win_top\":", Zwin1, ",\"top_closed\":", top_closed,
  ",\"red_tip\":", Zm + red_rim_z + led_len, ",\"wht_tip\":", Zm + wht_rim_z + led_len, ",\"bar_r\":", bar_r, ",\"V\":", V_batt,
  ",\"s1_tip\":", s1_tip, ",\"bore_r\":", bore_r, ",\"tongue_w\":", tongue_w, ",\"tongue_root\":", tongue_root, ",\"tongue_t\":", tongue_t,
  ",\"sled_len\":", Zm + flange_t - z_sb, ",\"batt_preload\":", batt_preload,
  ",\"panel_t\":", panel_t, ",\"R_RED\":", R_RED, ",\"R_WHITE\":", R_WHITE, ",\"battery\":\"", battery, "\"}"));

// =====================================================================
//  helpers
// =====================================================================
// cyclic axis maps (determinant +1, safe for CGAL)
module xprism(x0, x1) multmatrix([[0,0,1,x0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) linear_extrude(x1 - x0) children(); // 2D (y,z) along x
module yprism(y0, y1) multmatrix([[1,0,0,0],[0,0,-1,y1],[0,1,0,0],[0,0,0,1]]) linear_extrude(y1 - y0) children(); // 2D (x,z) along y
module box(xr, yr, zr) translate([xr[0], yr[0], zr[0]]) cube([xr[1]-xr[0], yr[1]-yr[0], zr[1]-zr[0]]);
// 2D square with a 45 deg gable on top (bridge-free horizontal holes)
module gable_sq(hw, hh) polygon([[-hw,-hh],[hw,-hh],[hw,hh],[0,hh+hw],[-hw,hh]]);
module teardrop(r) hull() { circle(r); polygon([[-r*0.7071, r*0.7071],[0, r*1.4142],[r*0.7071, r*0.7071]]); }
module diamond(r) rotate(45) square(r * 1.4142, center = true);
module stadium(r, y0, y1) hull() { translate([0, y0]) circle(r); translate([0, y1]) circle(r); }

// ---------------------------------------------------------------- threads
// one helical tooth, profile half-widths w_in (at r_in) and w_out (at r_out)
module thread_ridge(r_in, r_out, w_in, w_out, P, z0, z1, fn = 96) {
  n = ceil(((z1 - (floor(z0 / P) - 1) * P) / P + 1) * fn);
  s = (floor(z0 / P) - 1) * P;      // helix phase is global, so male/female always match
  pts = [for (i = [0:n]) let(a = 360 * i / fn, zc = s + P * i / fn) each [
      [r_in  * cos(a), r_in  * sin(a), zc - w_in ], [r_out * cos(a), r_out * sin(a), zc - w_out],
      [r_out * cos(a), r_out * sin(a), zc + w_out], [r_in  * cos(a), r_in  * sin(a), zc + w_in ]]];
  fcs = concat(
    [for (i = [0:n-1], j = [0:3]) [4*i+j, 4*(i+1)+j, 4*(i+1)+(j+1)%4, 4*i+(j+1)%4]],
    [[0,1,2,3], [4*n+3, 4*n+2, 4*n+1, 4*n]]);
  intersection() {
    polyhedron(pts, fcs, convexity = 10);
    translate([0, 0, z0]) cylinder(r = r_out + 1, h = z1 - z0, $fn = fn);
  }
}
// 90 deg included thread (45 deg flanks = support-free when printed upright).
// Tooth half-width at radius r: P/4 - (r - r_mid)*tan(flank)
thread_flank = 45;
function tw(r, D, P, h) = P/4 - (r - (D/2 - h/2)) * tan(thread_flank);
module male_thread(D, P, h, z0, z1, fn = 96) {
  rm = D/2 - h; ri = rm - 0.05;
  union() {
    translate([0, 0, z0]) cylinder(r = rm, h = z1 - z0, $fn = fn);
    thread_ridge(ri, D/2, tw(ri, D, P, h), tw(D/2, D, P, h), P, z0, z1, fn);
  }
}
// internal-thread minor radius produced by thread_tap()
function tap_core(D, P, h, c) =
  max(D/2 - h + c, (D/2 - h/2) + (P/4 + c/cos(thread_flank) - (P/2 - 0.01)) / tan(thread_flank)) + 0.03;
// the cutter for the matching internal thread: male tooth grown by c on every face
module thread_tap(D, P, h, c, z0, z1, fn = 96) {
  ri = tap_core(D, P, h, c) - 0.03; ro = D/2 + c;
  union() {
    translate([0, 0, z0]) cylinder(r = ri + 0.03, h = z1 - z0, $fn = fn);
    thread_ridge(ri, ro, tw(ri, D, P, h) + c/cos(thread_flank), tw(ro, D, P, h) + c/cos(thread_flank), P, z0, z1, fn);
  }
}

// =====================================================================
//  BODY  (a tube for the sled, window, sleeve channel + switch tongue)
// =====================================================================
// bore: circle + keyway for the spine (-Y) + flat lanes for the two switch plungers (+X / -X)
module bore_2d(r) union() { circle(r); translate([spine[0][0] - 0.25, spine[1][0] - 0.25]) square([spine[0][1] - spine[0][0] + 0.5, -spine[1][0] + 0.25]);
  translate([-r, -2.1]) square([2 * r, 4.2]); }
z_bore0 = min(z_sb - 0.5, z_cl - tongue_root);  // the tongue is free from its root up
module body() {
  difference() {
    union() {
      cylinder(r = R, h = Zt);
      // panel detent bumps on the window floor (diamond = support-free)
      for (sy = [-1, 1]) translate([win_floor - 0.3, sy * det_y, Zw0 + det_v]) rotate([0, 90, 0]) rotate(45) cylinder(r1 = 0.6, r2 = 0.05, h = 0.6, $fn = 4);
    }
    // decorative bottom cap thread (blind, 45 deg roof)
    thread_tap(bt_D, bt_P, bt_h, thread_clr, -1, bt_len);
    translate([0, 0, -eps]) cylinder(r1 = fM + 0.5, r2 = fM - 0.5, h = 1);
    translate([0, 0, bt_len - eps]) cylinder(r1 = fM, r2 = 0, h = fM);
    translate([0, 0, -eps]) difference() { cylinder(r = R + 1, h = 0.6); cylinder(r1 = R - 0.6, r2 = R, h = 0.6); }
    // sled bore with keyway, seat cone, cap thread
    translate([0, 0, z_bore0]) linear_extrude(Zt - z_bore0 + 1) bore_2d(bore_r);
    translate([0, 0, Zm - (flange_r + 0.15 - bore_r)]) cylinder(r1 = bore_r, r2 = flange_r + 0.15, h = flange_r + 0.15 - bore_r + eps);
    thread_tap(ct_D, ct_P, ct_h, thread_clr, Zm, Zt + 1);
    translate([0, 0, Zt - 0.5]) cylinder(r1 = ct_D/2 + thread_clr, r2 = ct_D/2 + thread_clr + 0.5 + eps, h = 0.5 + eps);
    back_channel_cuts();
    window_cuts();
  }
}
module back_channel_cuts() {
  // key channel the sleeve finger runs in; 90 deg lower wall = "open" hard stop
  difference() {
    yprism(-ch_w/2, ch_w/2) polygon([[-ch_floor, z_cl], [-R - 2, z_cl],
        [-R - 2, z_ch_top + (R + 2 - ch_floor)], [-ch_floor, z_ch_top]]);
    // raised pad on the switch tongue, 30 deg entry ramp
    yprism(-tongue_w/2, tongue_w/2) polygon([[-ch_floor + eps, z_cl - 1], [x_pad, z_cl - 1],
        [x_pad, z_cl + 8], [-ch_floor + eps, z_cl + 8 + (-x_pad - ch_floor) / tan(30)]]);
    // closed-position detent ridge (45 deg both sides)
    yprism(-ch_w/2 - 1, ch_w/2 + 1) polygon([[-ch_floor + eps, z_ridge - 0.75],
        [-ch_floor - 0.65, z_ridge], [-ch_floor + eps, z_ridge + 0.75]]);
  }
  // switch tongue: a U-slot frees a strip of the back wall; the sleeve bump pushes its pad
  // inward and the tongue presses the sled's S1 switch
  zt0 = z_cl - tongue_root; zt1 = z_cl + 11;
  for (sg = [-1, 1]) box([-R - 1, -bore_r + 0.5], sg > 0 ? [tongue_w/2, tongue_w/2 + 0.6] : [-tongue_w/2 - 0.6, -tongue_w/2], [zt0, zt1 + 0.6]);
  xprism(-R - 1, -bore_r + 0.5) polygon([[-tongue_w/2 - 0.6, zt1], [tongue_w/2 + 0.6, zt1], [tongue_w/2 + 0.6, zt1 + 0.6],
      [0, zt1 + 0.6 + tongue_w/2 + 0.6], [-tongue_w/2 - 0.6, zt1 + 0.6]]);   // 45 deg gable: no flat roof
  // thin, flexible root below the pad (45 deg chamfer under the pad)
  yprism(-tongue_w/2 - 0.6, tongue_w/2 + 0.6) polygon([[-bore_r - tongue_t, zt0 - eps], [-R - 2, zt0 - eps], [-R - 2, z_cl + eps],
      [x_pad, z_cl + eps], [-bore_r - tongue_t, z_cl - (-x_pad - bore_r - tongue_t)]]);
}
module window_cuts() {
  // window recess with a 45 deg bevelled top end
  yprism(-win_w/2, win_w/2) polygon([[win_floor, Zw0], [R + 2, Zw0],
      [R + 2, Zw1 + (R + 2 - win_floor)], [win_floor, Zw1]]);
  // panel tongue pockets: the panel goes in shifted up by panel_slide, then slides down
  box([win_floor - eps, win_floor + 1.5], [-3.2, 3.2], [Zw0 - tongue_l - 0.3, Zw0 + eps]);
  let(zr = Zw1 + tongue_l + panel_slide + 0.3)   // roof slopes down 45 deg toward the outside: no flat ceiling
    yprism(-3.2, 3.2) polygon([[win_floor - eps, Zw1 - eps], [win_floor + 1.5, Zw1 - eps], [win_floor + 1.5, zr], [win_floor - eps, zr + 1.5 + eps]]);
  // HOURS: the flange travels into the floor and stops on it (long enough for the install slide;
  // teardrop = 45 deg roof when the body prints upright)
  xprism(sw_tip + btn_gap - btn_trav, win_floor + eps) hull() {
    translate([0, hz]) teardrop(btn_fl_r + 0.3); translate([0, hz + panel_slide]) teardrop(btn_fl_r + 0.3); }
}

// =====================================================================
//  SLEEVE  (fluted, slides; finger + bump = sleeve switch actuator)
// =====================================================================
fing_ang = 36;   // finger edges sit in the flute grooves at 180 +/- 36 deg
fing_len = d_bump + 8.5 + 10.5;
module sleeve() {
  difference() {
    union() {
      cylinder(r = sl_or, h = Ls, $fn = 200);
      rotate(180) clip_lugs();   // clip on the left (-Y) like the prop
    }
    translate([0, 0, -1]) cylinder(r = sl_ir, h = Ls + 2, $fn = 200);
    for (k = [0:flute_n - 1]) rotate(k * 360 / flute_n) translate([sl_or + 0.3, 0, -1]) cylinder(r = 0.9, h = Ls + 2, $fn = 16);
    // finger slots (hidden inside two flute grooves)
    for (s = [-1, 1]) rotate(180 + s * fing_ang) translate([sl_ir - 1, 0, 0]) xprism(0, sl_or - sl_ir + 2)
      polygon([[-0.4, Ls - fing_len], [0, Ls - fing_len - 0.4], [0.4, Ls - fing_len], [0.4, Ls + 1], [-0.4, Ls + 1]]);   // pointed end: no flat roof
    // edge chamfers
    translate([0, 0, -eps]) cylinder(r1 = sl_ir + 0.6, r2 = sl_ir, h = 0.6, $fn = 200);
    translate([0, 0, Ls - 0.6]) cylinder(r1 = sl_ir, r2 = sl_ir + 0.6 + eps, h = 0.6 + eps, $fn = 200);
  }
  bump();
}
module bump() {
  intersection() {
    let(t = Ls - d_bump) yprism(-bump_w/2, bump_w/2) polygon([[-(sl_ir + 0.5), t - 8.5], [-bump_in, t - 8.5],
        [-bump_in, t - (sl_ir - bump_in)], [-(sl_ir + 0.5), t + 0.5]]);
    cylinder(r = sl_ir + 0.3, h = Ls, $fn = 200);
  }
}
// hinge lugs + bar for the clip (built on +Y, rotated to -Y in sleeve())
clip_w = 5.0; bar_y = 14.9; bar_z = 4.0; bar_r = 1.12;   // bar_r = diamond corner radius
module clip_lugs() {
  for (s = [-1, 1]) let(xc = s * (clip_w/2 + 0.2 + 0.6))
    multmatrix([[0,0,1,xc - 0.6],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) linear_extrude(1.2)
      polygon([[sl_or - 1.2, 0], [bar_y + 1.6, 0], [bar_y + 1.6, bar_z + 1.6], [sl_or - 1.2, bar_z + 1.6 + (bar_y + 2.8 - sl_or)]]);
  // hinge bar: a diamond (corner down on the bed = 45 deg faces); its corners turn freely in the clip's round hole
  translate([-(clip_w/2 + 0.3), bar_y, bar_z]) rotate([0, 90, 0]) linear_extrude(clip_w + 0.6) diamond(bar_r);
}

// =====================================================================
//  CLIP  (2D profile in (y,z), extruded along x; prints on its side)
// =====================================================================
module clip_2d() {
  difference() {
    union() {
      translate([bar_y, 0]) circle(r = 2.2, $fn = 40);
      polygon([[bar_y - 0.7, 1.0], [bar_y + 0.7, 1.0], [bar_y + 0.7, 38.5], [bar_y - 0.3, 44.5],
               [bar_y - 0.8, 46.8], [bar_y - 2.0, 46.6], [bar_y - 1.6, 44.0], [bar_y - 0.7, 38.0]]);
    }
    translate([bar_y, 0]) circle(r = bar_r + 0.15, $fn = 40);
    translate([bar_y, 0]) rotate(-45) translate([0, -0.7]) square([3, 1.4]);   // snap opening (1.4 < the bar's 1.58 width)
  }
}
module clip_part() linear_extrude(clip_w) clip_2d();

// =====================================================================
//  BOTTOM CAP  (decorative, screws on)
// =====================================================================
cap_r = cap_d / 2;
module bottom_cap() {
  difference() {
    union() {
      intersection() {
        male_thread(bt_D, bt_P, bt_h, -0.3, bt_len - 0.5);
        translate([0, 0, bt_len - 0.5 - 20]) cylinder(r1 = bt_D/2 + 20, r2 = bt_D/2 - 0.6, h = 20 + eps);
      }
      translate([0, 0, -0.3 - (cap_r - 7.6)]) cylinder(r1 = cap_r, r2 = 7.6, h = cap_r - 7.6);   // 45 deg shoulder
      translate([0, 0, -6]) cylinder(r = cap_r, h = 6 - 0.3 - (cap_r - 7.6) + eps);
      translate([0, 0, -6]) intersection() { sphere(r = cap_r, $fn = 96); translate([0, 0, -cap_r]) cylinder(r = cap_r + 1, h = cap_r); }
    }
    // decorative recessed strip with two dots (front)
    difference() {
      intersection() {
        let(xr = cap_r - 0.5) yprism(-1.2, 1.2) polygon([[0, -13.5 + xr], [xr, -13.5], [cap_r + 2, -13.5 - (cap_r + 2 - xr)],
            [cap_r + 2, -4.0 + (cap_r + 2 - xr)], [xr, -4.0], [0, -4.0 - xr]]);   // 45 deg ends
        difference() { translate([0, 0, -20]) cylinder(r = cap_r + 2, h = 20);
          union() { translate([0, 0, -6]) cylinder(r = cap_r - 0.5, h = 3); translate([0, 0, -6]) sphere(r = cap_r - 0.5, $fn = 96); } }
      }
      for (zz = [-6.0, -9.5]) let(rr = zz > -6 ? cap_r - 0.5 : sqrt(pow(cap_r - 0.5, 2) - pow(zz + 6, 2)))
        translate([rr, 0, zz]) sphere(r = 0.75, $fn = 16);
    }
  }
}

// =====================================================================
//  ELECTRONICS SLED  (prints lying on its spine, +Y up; everything is wired on the bench)
//  top: LED head (flange clamped by the top cap)  |  resistor bay  |  S2 = HOURS
//  switch  |  battery bay (sprung bulkheads)  |  wire run  |  S1 = sleeve switch
//  Support-free: every cross-section has a 45 deg keel down to the spine, horizontal holes
//  are teardrops, the switch troughs are open on top (+Y).
// =====================================================================
// 45 deg keel from the spine edges (the underside when the sled lies on its spine)
// = hull of the circle above its 45 deg tangent points and a flat base at y = yb, wide enough
//   (>= the spine) that both flanks are 45 deg or steeper
module keel_2d(r, yb = key_y, w0 = spine[0][1]) let(w = max(w0, r * sqrt(2) + yb)) hull() {
  intersection() { circle(r); translate([-r - 1, -r * 0.7071]) square([2 * r + 2, 2 * r + 2]); }
  translate([-w, yb]) square([2 * w, 0.01]);
}
module sled_2d() keel_2d(sled_r);
module section(z0, z1) translate([0, 0, z0]) linear_extrude(z1 - z0) sled_2d();
// spine: a plain bar that rides in the body's keyway
module spine_2d() translate([spine[0][0], spine[1][0]]) square([spine[0][1] - spine[0][0], spine[1][1] - spine[1][0]]);
// 6x6 pocket along x with a 45 deg gable toward +y (print-up)
module sw_pocket(x0, x1, zc, hw = sw_pk) xprism(x0, x1) polygon([[-hw, zc - sw_pk], [hw, zc - sw_pk], [hw + sw_pk, zc], [hw, zc + sw_pk], [-hw, zc + sw_pk]]);
// 6x6 holder cut: pocket (plunger toward +x, tip at x = tip), leg relief behind it (gabled, open on
// top in the print) with a centre rib the switch bears on, between the legs
module sw_holder_cut(tip, zc) let(base = tip - sw_tot) {
  sw_pocket(base, 20, zc);
  difference() {
    xprism(base - 1.8, base + 1.0) polygon([[-(sw_pk + 0.6), zc - 4.2], [20, zc - 4.2], [20, zc + 4.2], [-(sw_pk + 0.6), zc + 4.2]]);
    box([base - 3, base + 1], [-10, 0.8], [zc - 2.5, zc + 2.5]);
  }
}
module sled() {
  difference() {
    union() {
      // spine (rides in the keyway); between the bulkheads only two low rails stay (the cells sit on
      // them, the wire channel runs between them)
      difference() {
        translate([0, 0, z_sb]) linear_extrude(Zm + flange_t - z_sb) spine_2d();
        box([-6, 6], [-5.95, 0], [cb0 + eps, zbt - bh_t - eps]);
        box([-ch_hw, ch_hw], [-20, 0], [cb0 + eps, zbt - bh_t - eps]);
      }
      // LED head: flange + 45 deg seat cone (both with the keel), and a pull fin
      translate([0, 0, Zm]) linear_extrude(flange_t) keel_2d(flange_r, spine[1][0], 0);
      intersection() {
        translate([0, 0, Zm - (flange_r - sled_r)]) cylinder(r1 = sled_r, r2 = flange_r, h = flange_r - sled_r + eps);
        translate([0, 0, Zm - 10]) linear_extrude(11) keel_2d(flange_r, spine[1][0], 0);
      }
      translate([0, 0, Zm - (flange_r - sled_r) - 2]) linear_extrude(2 + eps) sled_2d();
      translate([-0.5, 0, Zm + flange_t - eps]) rotate([90, 0, 90]) linear_extrude(1.0)
        polygon([[-5.6, 0], [4.0, 0], [4.0, 5.0], [-0.6, 5.0]]);
      // S2 (HOURS) holder, S1 (sleeve) holder, battery bulkheads (they flex = battery spring)
      section(hz - 5, hz + 5);
      section(z_pc - 5, z_pc + 5);
      section(zbt - bh_t, zbt);
      section(cb0 - bh_t, cb0);
    }
    // LED bores + rim seats (teardrops: horizontal holes in the print)
    for (l = [[led_x, red_rim_z], [-led_x, wht_rim_z]]) {
      translate([l[0], 0, Zm - 12]) linear_extrude(12 + flange_t + eps) teardrop(led_d/2 + 0.1, $fn = 40);
      translate([l[0], 0, Zm + l[1]]) linear_extrude(flange_t - l[1] + eps) teardrop(led_rim_d/2 + 0.1, $fn = 40);
    }
    // S2 (HOURS): plunger +x, in from the front; front cut back so the HOURS flange can travel
    sw_holder_cut(sw_tip, hz);
    box([sw_tip - btn_trav - 0.1, 20], [-20, 20], [hz - 5.5, hz + 5.5]);
    // S1 (sleeve): plunger -x, in from the back (the body's tongue presses it)
    mirror([1, 0, 0]) sw_holder_cut(-s1_tip, z_pc);
    // wire trunk: open-top slot through both switch holders (wires pass above the rib, over the switches)
    for (zc = [z_pc, hz]) box([-tr_w, tr_w], [tr_y0, 20], [zc - 6, zc + 6]);
    // upper bulkhead: full-depth slot, so the B- wire comes up from under the cells and the B+ contact
    // wire goes down onto the cells' top face
    box([-tr_w, tr_w], [-20, 20], [zbt - bh_t - eps, zbt + eps]);
  }
}

// =====================================================================
//  TOP CAP (AMS: clear + white, one colour change): clear threaded spigot + clear
//  light ring, white dome on top. Screws into the body and clamps the LED head.
//  The dome's 45 deg lip is the sleeve's closed stop; the inner cone reflects the
//  LEDs out through the ring.
// =====================================================================
module top_cap() difference() {
  union() {
    intersection() {
      male_thread(ct_D, ct_P, ct_h, Zwin0 - ct_len, Zwin0 + eps);
      translate([0, 0, Zwin0 - ct_len]) cylinder(r1 = ct_D/2 - 0.6, r2 = ct_D/2 - 0.6 + 20, h = 20);
    }
    translate([0, 0, Zwin0 - ct_h]) cylinder(r1 = ct_D/2 - ct_h, r2 = R, h = R - ct_D/2 + ct_h + eps);   // 45 deg underside from the thread core
    translate([0, 0, Zwin0 + R - ct_D/2 - eps]) cylinder(r = R, h = window_h - (R - ct_D/2) + 2 * eps);  // clear ring, flush with the body
    translate([0, 0, Zwin1]) cylinder(r1 = R, r2 = cap_lip_r, h = cap_lip_r - R + eps);          // 45 deg lip = sleeve stop
    translate([0, 0, Zwin1 + cap_lip_r - R]) cylinder(r = cap_lip_r, h = 1.5);
    translate([0, 0, Zwin1 + cap_lip_r - R + 1.5 - eps]) scale([1, 1, 0.8]) intersection() { sphere(r = cap_lip_r); cylinder(r = cap_lip_r + 1, h = cap_lip_r + 1); }
  }
  // light bore + reflector cone (one profile: no coincident rims)
  rotate_extrude() polygon([[0, Zwin0 - ct_len - 1], [spig_ir, Zwin0 - ct_len - 1], [spig_ir, Zwin1 - 0.3], [0, Zwin1 - 0.3 + spig_ir]]);
}
module top_cap_white_zone() translate([0, 0, Zwin1]) cylinder(r = 30, h = 40);
module top_cap_clear() difference() { top_cap(); top_cap_white_zone(); }
module top_cap_white() intersection() { top_cap(); top_cap_white_zone(); }

// =====================================================================
//  WINDOW PANEL  (local: X across, Y along (0 = window bottom), Z up = face)
// =====================================================================
// raised label: 2.0 mm caps, condensed, letter-spaced, strokes fattened to >= 0.5 mm
module label(t, h = 2.0, sx = 0.85, sp = 1.16, fat = 0.11) offset(delta = fat) scale([sx, 1])
  resize([0, h], auto = true) text(t, font = FONT, halign = "center", valign = "center", size = 10, spacing = sp);
module seg7_8(w = 2.2, h = 4.0, t = 0.5) {   // a chunky "8" made of 7 raised bars
  for (y = [-h/2 + t/2, 0, h/2 - t/2]) translate([0, y]) square([w - 2*t - 0.2, t], center = true);
  for (x = [-1, 1], y = [-1, 1]) translate([x * (w/2 - t/2), y * h/4]) square([t, h/2 - t - 0.2], center = true);
}
function vy(v) = window_len - v;              // distance from window top -> panel Y
tongue_l = 2.0; panel_slide = 2.0;              // panel tongues and the install slide
det_y = 5.2; det_v = 3.0;                       // detent position (panel coords)
module window_panel() {
  T = panel_t;
  difference() {
    union() {
      // plate with softened face edges
      hull() {
        translate([-panel_w/2, 0.15, 0]) cube([panel_w, window_len - 0.3, T - 0.3]);
        translate([-panel_w/2 + 0.3, 0.15, 0]) cube([panel_w - 0.6, window_len - 0.3, T]);
      }
      // tongues into the pockets at both ends of the window
      translate([-3.0, -tongue_l, 0]) cube([6.0, tongue_l + 0.2, 1.2]);
      translate([-3.0, window_len - 0.2, 0]) cube([6.0, tongue_l + 0.2, 1.2]);
      // raised details (0.6 mm, paint-ready)
      translate([0, 0, T - eps]) linear_extrude(0.6) {
        translate([0, vy(15.0)]) label("MINUTES");
        translate([0, vy(29.0)]) label("HOURS");
        translate([0, vy(42.5)]) label("WEEKS");
        translate([0, vy(55.0)]) label("YEAR");
        for (v = [22.5, 36.0]) translate([-5.35, vy(v)]) polygon([[-0.7, -0.9], [0.75, 0], [-0.7, 0.9]]);  // arrows
        translate([5.3, vy(19.6)]) circle(r = 0.75, $fn = 20);                                           // indicator dot
      }
      // MINUTES + WEEKS button heads, printed in place (black via AMS)
      for (b = BTN) if (!b[4]) translate([0, vy(b[1]), T - eps]) hull() {
        cylinder(r = b[2]/2, h = btn_proud - 0.4, $fn = 64); cylinder(r = b[2]/2 - 0.4, h = btn_proud, $fn = 64); }
      for (s = [-1, 1]) translate([s * 5.2, vy(55.0), T - 0.3]) intersection() {
        sphere(r = 0.9, $fn = 24); cylinder(r = 1.0, h = 1.1, $fn = 24); }                               // YEAR buttons
    }
    // hole for the moving HOURS button (MINUTES / WEEKS are printed into the panel)
    for (b = BTN) if (b[4]) translate([0, vy(b[1]), 0]) {
      translate([0, 0, -1]) cylinder(r = b[2]/2 + hole_clr, h = T + 2, $fn = 64);
      // 45 deg countersink on the back: the button's cone sits in it (prints face-up without support)
      translate([0, 0, -eps]) cylinder(r1 = btn_fl_r + 0.25, r2 = b[2]/2 + hole_clr, h = btn_fl_r + 0.25 - b[2]/2 - hole_clr + eps, $fn = 64);
    }
    // detent dimples on the back (click over the body's bumps at the end of the slide)
    for (sy = [-1, 1]) translate([sy * det_y, det_v, -eps]) cylinder(r1 = 0.75, r2 = 0.25, h = 0.5, $fn = 24);
    // recessed M A F plate and display window (0.6 deep)
    translate([0, vy(49.0), T - 0.6]) linear_extrude(1) offset(r = 0.6) square([11 - 1.2, 5 - 1.2], center = true);
    translate([0, vy(63.0), T - 0.6]) linear_extrude(1) offset(r = 0.4) square([11 - 0.8, 6 - 0.8], center = true);
  }
  // raised letters inside the M A F plate (flush with the face)
  translate([0, vy(49.0), T - 0.6 - eps]) linear_extrude(0.6) label("M A F", h = 2.6, sx = 1.0, sp = 1.0);
  // 8888 display segments (raised 0.4 from the display floor)
  translate([0, vy(63.0), T - 0.6 - eps]) linear_extrude(0.4) for (i = [0:3]) translate([(i - 1.5) * 2.6, 0]) seg7_8();
}

// ---- multicolour split (AMS): everything above the face + the top 2 layers of the two
// recessed plates is printed in the detail colour (black), the rest in the panel colour (white)
detail_floor = 0.24;
module panel_detail_zone() {
  translate([-20, -10, panel_t + 0.01]) cube([40, window_len + 20, 5]);   // +0.01: no zero-thickness film on the face
  translate([0, vy(49.0), panel_t - 0.6 - detail_floor]) linear_extrude(detail_floor) offset(r = 0.6) square([11 - 1.2, 5 - 1.2], center = true);
  translate([0, vy(63.0), panel_t - 0.6 - detail_floor]) linear_extrude(detail_floor) offset(r = 0.4) square([11 - 0.8, 6 - 0.8], center = true);
}
module window_panel_base() difference() { window_panel(); panel_detail_zone(); }
module window_panel_details() intersection() { window_panel(); panel_detail_zone(); }

// =====================================================================
//  BUTTONS (black): flange behind the panel, head through it
// =====================================================================
// local z = 0: inner face (rests btn_gap above the HOURS plunger); +z = outward
btn_cone_z = 0.2;                                    // flange cylinder height below the cone
btn_top = win_floor - sw_tip - btn_gap + panel_t + btn_proud_h;   // head top (local z)
module button(i) let(b = BTN[i]) {
  cylinder(r = btn_fl_r, h = btn_cone_z + eps, $fn = 64);
  translate([0, 0, btn_cone_z]) cylinder(r1 = btn_fl_r, r2 = b[2]/2, h = btn_fl_r - b[2]/2 + eps, $fn = 64);   // 45 deg
  hull() {
    cylinder(r = b[2]/2, h = btn_top - 0.4, $fn = 64);
    cylinder(r = b[2]/2 - 0.4, h = btn_top, $fn = 64);
  }
}
module btn_print() children();                      // flange on the bed, head up: nothing overhangs
module btn_black_zone() translate([0, 0, win_floor - sw_tip - btn_gap + panel_t - 0.3]) cylinder(r = 20, h = 20);
// =====================================================================
//  QUICK TEST PRINTS - print these first (about 30 min) to tune clearances
// =====================================================================
// body stub (with the key channel) + three sleeve rings: 1 notch = slide_clr-0.1,
// 2 notches = slide_clr, 3 notches = slide_clr+0.1.  Use the one that slides freely
// without wobble and set slide_clr accordingly.
module fit_test() {
  difference() {
    cylinder(r = R, h = 25);
    yprism(-ch_w/2, ch_w/2) polygon([[-ch_floor, 3], [-R - 2, 3], [-R - 2, 26], [-ch_floor, 26]]);
    translate([0, 0, -eps]) difference() { cylinder(r = R + 1, h = 0.6); cylinder(r1 = R - 0.6, r2 = R, h = 0.6); }
  }
  for (i = [0:2]) let(c = slide_clr - 0.1 + 0.1 * i) translate([28 + i * 28, 0, 0]) difference() {
    cylinder(r = sl_or, h = 12, $fn = 200);
    translate([0, 0, -1]) cylinder(r = R + c, h = 14, $fn = 200);
    for (k = [0:i]) rotate(90 + (k - i/2) * 14) translate([sl_or, 0, 12]) cube([2.4, 1.4, 3], center = true);
  }
}
// 9 mm of the real bottom-cap thread: male stub + female ring. They must spin on by hand.
module thread_test() {
  cylinder(r = cap_r, h = 2);
  intersection() {
    male_thread(bt_D, bt_P, bt_h, 2 - eps, 11);
    translate([0, 0, 11 - 20]) cylinder(r1 = bt_D/2 + 20, r2 = bt_D/2 - 0.6, h = 20 + eps);
  }
  translate([30, 0, 0]) difference() {
    cylinder(r = cap_r, h = 9, $fn = 6);
    thread_tap(bt_D, bt_P, bt_h, thread_clr, -1, 10);
    translate([0, 0, -eps]) cylinder(r1 = fM + 0.5, r2 = fM - 0.5, h = 1);
    translate([0, 0, 8]) cylinder(r1 = fM - 0.5, r2 = fM + 0.5, h = 1 + eps);
  }
}

// 10 mm of the sled with the real 6x6 holder, printed the same way (lying on the spine): your
// switch must press in snugly, legs in the slots, plunger tip flush with the round outline.
module switch_test() translate([0, 0, -spine[1][0]]) rotate([90, 0, 0]) translate([0, 0, -(hz - 5)]) difference() {
  union() { translate([0, 0, hz - 5]) linear_extrude(10) spine_2d(); section(hz - 5, hz + 5); }
  sw_holder_cut(sw_tip, hz);
}

// ---------------------------------------------------------------- dummies (for the views + checks)
module dummy_switch(x_tip, zc) {   // 6x6 tactile, plunger toward +x, legs trimmed to 1.5 mm
  base = x_tip - sw_tot;
  for (sy = [-1, 1], sz = [-1, 1]) translate([base - 1.5, sy * 2.25 - 0.35, zc + sz * (sw_w/2 + 0.2) - 0.2]) cube([2.0, 0.7, 0.4]);
  translate([base, -sw_w/2, zc - sw_w/2]) cube([sw_body_h, sw_w, sw_w]);
  translate([x_tip - sw_plunger_h, 0, zc]) rotate([0, 90, 0]) cylinder(r = 1.75, h = sw_plunger_h, $fn = 24);
}
module dummy_led(x, rim_z) translate([x, 0, Zm + rim_z]) {
  cylinder(r = led_rim_d/2, h = 1.0, $fn = 32);
  cylinder(r = led_d/2, h = led_len - led_d/2, $fn = 32);
  translate([0, 0, led_len - led_d/2]) sphere(r = led_d/2, $fn = 32);
}
// wiring as built (for the pictures and the slide-out check): 1 mm insulated wire, diagonal 6x6 legs
module wire(pts, r = 0.45) for (i = [0:len(pts) - 2]) hull() { translate(pts[i]) sphere(r, $fn = 10); translate(pts[i + 1]) sphere(r, $fn = 10); }
s2_lo = [sw_tip - sw_tot - 1.3, -2.25, hz - 3.2];  s2_hi = [sw_tip - sw_tot - 1.3, 2.25, hz + 3.2];   // HOURS legs (diagonal)
s1_lo = [-(-s1_tip - sw_tot - 1.3), -2.25, z_pc - 3.2];  s1_hi = [-(-s1_tip - sw_tot - 1.3), 2.25, z_pc + 3.2];
r_z0 = Zm - 21; r_z1 = Zm - 15;                     // resistors hang under the LED bores, on the long legs
module wire_bp() wire([[0, -3.0, zbt - bh_t + 0.95], [0, 2.4, zbt - 0.3], [0, 2.4, s1_lo[2]], s1_lo]);
module wire_n()  wire([s1_hi, [0, 2.4, s1_hi[2]], [0, 2.4, s2_lo[2]], s2_lo, [0, 2.4, s2_lo[2]], [0, 2.4, hz + 6],
                      [led_x, 1.27, r_z0 - 3], [led_x, 1.27, r_z0]]);
module wire_x()  wire([s2_hi, [0, 3.3, s2_hi[2]], [0, 3.3, hz + 6], [-led_x, 1.27, r_z0 - 3], [-led_x, 1.27, r_z0]]);
module wire_bm() union() {
  wire([[0, -7.0, cb0 + 0.6], [0, -7.0, zbt - bh_t + 0.95], [0, 1.4, zbt - 0.45], [0, 1.4, hz + 6], [0, -1.27, Zm - 15]]);
  for (sx = [-1, 1]) wire([[0, -1.27, Zm - 15], [sx * led_x, -1.27, Zm - 14]]);
}
module dummy_resistors() for (sx = [-1, 1]) translate([sx * led_x, 1.27, r_z0]) cylinder(r = 0.9, h = r_z1 - r_z0, $fn = 16);
module dummy_led_legs() for (sx = [-1, 1], sy = [-1, 1]) translate([sx * led_x, sy * 1.27, Zm - 15]) cylinder(r = 0.25, h = 15 + red_rim_z, $fn = 8);
module dummy_cells() for (i = [0:n_cells - 1]) translate([0, 0, cb0 + i * cell_l + 0.02]) cylinder(r = cell_d/2, h = cell_l - 0.04, $fn = 48);

// =====================================================================
//  assembly transforms + part selector
// =====================================================================
M_panel = [[0,0,1,win_floor],[1,0,0,0],[0,1,0,Zw0],[0,0,0,1]];
module at_button(i, pressed = false) let(zc = Zw1 - BTN[i][1], x0 = sw_tip + btn_gap - (pressed ? btn_trav : 0))
  multmatrix([[0,0,1,x0],[1,0,0,0],[0,1,0,zc],[0,0,0,1]]) children();
module at_clip(s) rotate(180) multmatrix([[0,0,1,-clip_w/2],[1,0,0,0],[0,1,0,s + bar_z],[0,0,0,1]]) children();

SILVER = [0.78, 0.80, 0.83]; BLACK = [0.08, 0.08, 0.09];
module assembly() {
  s = s_pos;
  is_open = sleeve_state == "open";
  module cut() if (cutaway) difference() { children(); translate([-50, -100, -50]) cube([100, 100, 400]); } else children();
  cut() {
    color(SILVER) body();
    color(SILVER) translate([0, 0, s]) sleeve();
    color(SILVER) translate([0, 0, s]) at_clip(0) clip_part();
    color(SILVER) bottom_cap();
    color("white") multmatrix(M_panel) window_panel();
    color(BLACK) at_button(1) button(1);
    color("white") sled();
    color(show_lit && is_open ? [1, 0.1, 0.05, 0.85] : [0.85, 0.85, 0.88, 0.55]) top_cap_clear();
    color(SILVER) top_cap_white();
    if (cutaway) {
      color([0.6, 0.6, 0.6]) dummy_cells();
      color([0.2, 0.2, 0.2]) dummy_switch(sw_tip, hz);
      color([0.2, 0.2, 0.2]) mirror([1, 0, 0]) dummy_switch(-s1_tip, z_pc);
      color("red") dummy_led(led_x, red_rim_z);
      color("white") dummy_led(-led_x, wht_rim_z);
    }
  }
}
// sled print pose: lying on the spine (-Y down), axis along the bed
module sled_print() translate([0, 0, -spine[1][0]]) rotate([90, 0, 0]) translate([0, 0, -z_sb]) sled();
module print_pose(name) {
  if (name == "body") body();
  else if (name == "sleeve") translate([0, 0, Ls]) rotate([180, 0, 0]) sleeve();          // top edge on the bed
  else if (name == "sled") sled_print();
  else if (name == "bottom_cap") translate([0, 0, bt_len - 0.5]) rotate([180, 0, 0]) bottom_cap(); // spigot on the bed
  else if (name == "top_cap") translate([0, 0, ct_len - Zwin0]) top_cap();               // spigot down, dome up
  else if (name == "top_cap_zone") translate([0, 0, ct_len - Zwin0]) top_cap_white_zone();
  else if (name == "window_panel") translate([0, tongue_l, 0]) window_panel();
  else if (name == "panel_detail_zone") translate([0, tongue_l, 0]) panel_detail_zone();
  else if (name == "btn_hours") btn_print() button(1);
  else if (name == "btn_zone") btn_print() btn_black_zone();
  else if (name == "clip") clip_part();
  else if (name == "fit_test") fit_test();
  else if (name == "thread_test") thread_test();
  else if (name == "switch_test") switch_test();
}
module assembled_pose(name) {
  s = s_pos;
  if (name == "body") body();
  else if (name == "sleeve") translate([0, 0, s]) sleeve();
  else if (name == "clip") translate([0, 0, s]) at_clip(0) clip_part();
  else if (name == "bottom_cap") bottom_cap();
  else if (name == "sled") sled();
  else if (name == "top_cap") top_cap();
  else if (name == "top_cap_zone") top_cap_white_zone();
  else if (name == "window_panel") multmatrix(M_panel) window_panel();
  else if (name == "panel_detail_zone") multmatrix(M_panel) panel_detail_zone();
  else if (name == "btn_hours") at_button(1) button(1);
  else if (name == "btn_hours_pressed") at_button(1, true) button(1);
  else if (name == "btn_zone") at_button(1) btn_black_zone();
  // dummies used by the verification script and the pictures
  else if (name == "cells") dummy_cells();
  else if (name == "s2_switch") dummy_switch(sw_tip, hz);
  else if (name == "s1_switch") mirror([1, 0, 0]) dummy_switch(-s1_tip, z_pc);
  else if (name == "led_red") dummy_led(led_x, red_rim_z);
  else if (name == "led_white") dummy_led(-led_x, wht_rim_z);
  else if (name == "wire_bp") wire_bp();
  else if (name == "wire_bm") wire_bm();
  else if (name == "wire_n") wire_n();
  else if (name == "wire_x") wire_x();
  else if (name == "resistors") dummy_resistors();
  else if (name == "led_legs") dummy_led_legs();
}

if (part == "assembly") assembly();
else if (pose == "print") print_pose(part);
else assembled_pose(part);
