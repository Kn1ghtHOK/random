// =====================================================================
//  MEN IN BLACK NEURALIZER  -  parametric, support-free, PETG, no hardware
//  OpenSCAD 2021.01+   (Customizer friendly: Window > Customizer)
//
//  Coordinate system (assembly): Z = long axis, z = 0 is the bottom end
//  of the inner body.  +X = the window / buttons, -X = back (sleeve
//  switch finger), -Y = pocket-clip side (left when you face the window).
//
//  Export one part:   openscad -D 'part="body"' -o body.stl neuralizer.scad
//  (every part is placed in its print orientation unless pose="assembled")
// =====================================================================

/* [What to show] */
part = "assembly"; // [assembly, body, sleeve, bottom_cap, battery_spring, knurl_nut, led_mount, light_window, dome, window_panel, window_panel_base, window_panel_details, btn_minutes, btn_hours, btn_weeks, clip, fit_test, thread_test]
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
battery = "LR44x3"; // [LR44x3, LR44x4, A23, AAAx3]

/* [Tactile switch - MEASURE YOURS with calipers] */
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
// diametral interference of the light-window / dome push-fits
dome_press = 0.10;
// copper tape thickness (pads are recessed by this)
tape_t = 0.10;
// how far the sleeve finger is bent by the contact land (contact force / detent)
finger_preload = 0.5;

/* [Main dimensions] */
body_d = 20;
window_len = 72;
sleeve_od = 24.6;
flute_n = 20;
cap_d = 22;
nut_od = 24.5;
dome_d = 17;
// height of the clear light window under the dome
window_h = 5.0;

/* [Hidden] */
$fn = 160;
eps = 0.01;
FONT = "Liberation Sans:style=Bold";

// ------------------------------------------------------------- battery
BATT = [ // name, cell dia, cell length, cells, nominal volts
  ["LR44x3", 11.6,  5.4, 3,  4.5],
  ["LR44x4", 11.6,  5.4, 4,  6.0],
  ["A23",    10.3, 28.5, 1, 12.0],
  ["AAAx3",  10.5, 44.5, 3,  4.5]];
B = [for (b = BATT) if (b[0] == battery) b][0];
cell_d = B[1]; cell_l = B[2]; n_cells = B[3]; V_batt = B[4];

E12 = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2];
function e12_up(x) = let(d = pow(10, floor(log(x))), m = x / d,
   c = [for (e = E12) if (e >= m - 1e-9) e]) (len(c) ? c[0] : 10) * d;
R_RED   = e12_up((V_batt - 2.0) / 0.010);   // red  LED, Vf 2.0 V, ~10 mA
R_WHITE = e12_up((V_batt - 3.1) / 0.020);   // white LED, Vf 3.1 V, ~20 mA

// ------------------------------------------------------------- derived
R      = body_d / 2;
sw_tot = sw_body_h + sw_plunger_h;
sw_pk  = (sw_w + sw_fit) / 2;                 // half size of switch pocket

// bottom thread (female in body, male on cap)
bt_D = 16; bt_P = 2.0; bt_h = 0.8; bt_len = 7;
// top thread (male on body spigot, female in knurled nut)
tt_D = 19; tt_P = 2.0; tt_h = 0.8; spig_len = 6;

bay_r   = cell_d / 2 + 0.3;
fM      = bt_D / 2 + thread_clr;               // crest radius of internal bottom thread
z_cone0 = bt_len;                              // battery + contact cone starts here
r_face  = bay_r - 0.1;
z_face  = z_cone0 + fM - r_face;               // cap contact face (cells sit on it)
stack_top = z_face + n_cells * cell_l;
boss_h = 2.0; spring_t = 1.2; spring_preload = 0.8;
z_sd    = stack_top + boss_h - spring_preload; // underside of spring disc
roof_base = z_sd + spring_t;
roof_apex = roof_base + bay_r;

Lz_low = max(78, roof_apex + 16);              // length of lower (sleeve) zone
Zw0 = Lz_low;                                  // window bottom
Zw1 = Lz_low + window_len;                     // window top
Zt  = Zw1 + spig_len;                          // top of body

// sleeve
s_open  = 0.5;
nut_gap = 0.3;
Ls      = Lz_low - s_open;                     // sleeve length
travel  = window_len + nut_gap;
s_pos   = sleeve_state == "open" ? s_open : s_open + travel;
sl_ir   = R + slide_clr;
sl_or   = sleeve_od / 2;

// back key channel / sleeve switch
ch_floor = 7.5;                                // floor distance from axis
ch_w     = 10.8;
land_h   = slide_clr + finger_preload;
x_land   = -(ch_floor + land_h);               // contact land surface
bump_in  = ch_floor + slide_clr;               // bump face distance from axis (undeflected)
bump_w   = 10.0;
z_cl     = Zw0 - 9;                            // channel lower end = open stop
z_pc     = z_cl + 3;                           // fallback switch centre
sw_press = 0.35;                               // fallback plunger sticks out of land by this
fb_base  = x_land - sw_press + sw_tot;         // fallback switch base (x)
z_ridge  = z_cl + travel - 0.9;                // closed detent ridge
z_ch_top = Zw1 - 0.2;

// front window
win_floor = 5.8;
panel_t   = 1.8;
win_w     = 13.3;
panel_w   = 13.0;
btn_ft    = 0.8;                               // button flange thickness
btn_trav  = sw_travel + 0.1;                   // functional button travel (flange stop)
sw_tip    = win_floor - btn_ft;                // plunger tip at rest
sw_base   = sw_tip - sw_tot;
// buttons: name, centre (mm from window top), head dia, flange dia, functional
BTN = [["minutes", 8.0, 9.6, 11.6, false],
       ["hours",  22.5, 8.0, 10.0, true ],
       ["weeks",  36.0, 8.0, 10.0, false]];
btn_proud = 0.9;

// LED head
flange_r = 8.0; flange_t = 1.2; lip_t = 1.5; stem_len = 11;
y_red = -3.6; y_wht = 2.6; stem_r = 3.6;
win_ir = 7.0; win_or = dome_d / 2;
z_nut_top = flange_t + lip_t;                  // local to Zt
z_win_top = z_nut_top + window_h;              // window spans z_nut_top .. z_win_top
spig_ir = 6.3; spig_h = 1.3;                   // window push-fit spigots (into nut lip / into dome)
red_rim_z = z_nut_top + window_h/2 - 0.0 - led_len;   // both LED tips in the middle of the window
wht_rim_z_ = z_nut_top + window_h/2 + 0.5 - led_len;
wht_rim_z = wht_rim_z_;

// wire channel
WC = [[-2.0, 1.2], [-6.8, -3.6]];              // x range, y range

echo(str("=== NEURALIZER: battery ", battery, " = ", V_batt, " V,  red resistor ", R_RED,
         " ohm, white resistor ", R_WHITE, " ohm"));
echo(str("=== body ", Zt, " mm, sleeve ", Ls, " mm, travel ", travel,
         " mm, overall ~", Zt + z_win_top + 12 + 17, " mm"));

// machine-readable values for tools/verify.py
echo(str("PARAMS {\"Zw0\":", Zw0, ",\"Zw1\":", Zw1, ",\"Zt\":", Zt, ",\"Ls\":", Ls, ",\"s_open\":", s_open,
  ",\"travel\":", travel, ",\"z_cl\":", z_cl, ",\"z_pc\":", z_pc, ",\"z_ridge\":", z_ridge, ",\"x_land\":", x_land,
  ",\"bump_in\":", bump_in, ",\"ch_floor\":", ch_floor, ",\"finger_preload\":", finger_preload, ",\"bt_P\":", bt_P, ",\"tt_P\":", tt_P,
  ",\"bt_D\":", bt_D, ",\"tt_D\":", tt_D, ",\"bt_h\":", bt_h, ",\"tt_h\":", tt_h, ",\"thread_clr\":", thread_clr,
  ",\"bt_core\":", tap_core(bt_D, bt_P, bt_h, thread_clr), ",\"tt_core\":", tap_core(tt_D, tt_P, tt_h, thread_clr),
  ",\"z_face\":", z_face, ",\"stack_top\":", stack_top, ",\"z_sd\":", z_sd, ",\"spring_preload\":", spring_preload,
  ",\"btn_trav\":", btn_trav, ",\"sw_travel\":", sw_travel, ",\"sw_press\":", sw_press, ",\"z_nut_top\":", z_nut_top, ",\"z_win_top\":", z_win_top,
  ",\"red_tip\":", red_rim_z + led_len, ",\"wht_tip\":", wht_rim_z + led_len, ",\"bar_r\":", bar_r, ",\"V\":", V_batt,
  ",\"R_RED\":", R_RED, ",\"R_WHITE\":", R_WHITE, ",\"battery\":\"", battery, "\"}"));

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
//  BODY  (inner body, window, battery bay, sleeve switch, top spigot)
// =====================================================================
module body() {
  difference() {
    union() {
      cylinder(r = R, h = Zw1);
      // top spigot, male thread with a 45 deg lead-in
      intersection() {
        male_thread(tt_D, tt_P, tt_h, Zw1 - eps, Zt);
        translate([0, 0, Zt - 10]) cylinder(r1 = tt_D/2 - 0.8 + 10, r2 = tt_D/2 - 0.8, h = 10);
      }
    }
    // ---------------- bottom: battery bay -------------------------------
    thread_tap(bt_D, bt_P, bt_h, thread_clr, -1, bt_len);
    translate([0, 0, -eps]) cylinder(r1 = fM + 0.5, r2 = fM - 0.5, h = 1);      // thread entry chamfer
    translate([0, 0, z_cone0 - eps]) cylinder(r1 = fM, r2 = bay_r, h = fM - bay_r + eps); // + contact cone
    translate([0, 0, z_cone0]) cylinder(r = bay_r, h = roof_base - z_cone0);
    translate([0, 0, roof_base - eps]) cylinder(r1 = bay_r, r2 = 0, h = bay_r);    // 45 deg roof
    // B+ wire groove up the bay wall (-Y), joins the wire channel
    box([-0.9, 0.9], [-(bay_r + 1.4), -(bay_r - 0.3)], [z_cone0 + 0.2, roof_base + 1]);
    // ---------------- wire channel (bay roof -> LED head) ---------------
    box(WC[0], WC[1], [roof_base - eps, Zt - stem_len]);
    // ---------------- outer bottom chamfer -------------------------------
    translate([0, 0, -eps]) difference() { cylinder(r = R + 1, h = 0.6); cylinder(r1 = R - 0.6, r2 = R, h = 0.6); }

    back_channel_cuts();
    window_cuts();

    // ---------------- top: LED-head socket -------------------------------
    translate([0, 0, Zt - stem_len - 0.5]) linear_extrude(stem_len + 1) stadium(stem_r + 0.2, y_red, y_wht);
    translate([0, 0, Zt - (flange_r + 0.15 - stem_r)]) cylinder(r1 = stem_r + 0.15, r2 = flange_r + 0.15, h = flange_r + 0.15 - stem_r + eps);
  }
}

// space behind a 6x6 switch pocket: legs (+/-z sides) + solder joints, with a centre rib
// that the switch base rests on.  base = x of the switch base, dir = +1 if the plunger points +x
module switch_relief(base, zc, dir) {
  x0 = dir > 0 ? base - 1.8 : base - 1.0;
  x1 = dir > 0 ? base + 1.0 : base + 1.8;
  difference() {
    box([x0, x1], [-sw_pk, sw_pk], [zc - 4.2, zc + 4.2]);
    box(dir > 0 ? [x0 - 1, base] : [base, x1 + 1], [-0.8, 0.8], [zc - 5, zc + 5]);   // support rib
  }
}
module back_channel_cuts() {
  // key channel the sleeve finger runs in; 90 deg lower wall = "open" hard stop
  difference() {
    yprism(-ch_w/2, ch_w/2) polygon([[-ch_floor, z_cl], [-R - 2, z_cl],
        [-R - 2, z_ch_top + (R + 2 - ch_floor)], [-ch_floor, z_ch_top]]);
    // raised contact land with 30 deg entry ramp
    yprism(-ch_w/2 - 1, ch_w/2 + 1) polygon([[-ch_floor + eps, z_cl - 1], [x_land, z_cl - 1],
        [x_land, z_cl + 8], [-ch_floor + eps, z_cl + 8 + land_h / tan(30)]]);
    // closed-position detent ridge (45 deg both sides)
    yprism(-ch_w/2 - 1, ch_w/2 + 1) polygon([[-ch_floor + eps, z_ridge - 0.75],
        [-ch_floor - 0.65, z_ridge], [-ch_floor + eps, z_ridge + 0.75]]);
  }
  // copper-tape pad recesses on the land (two strips, bridged by the finger bump)
  for (s = [-1, 1]) box([x_land - 1, x_land + tape_t], s > 0 ? [sw_pk + 0.3, ch_w/2 - 0.2] : [-(ch_w/2 - 0.2), -(sw_pk + 0.3)], [z_cl + 0.3, z_cl + 8]);
  // fallback tactile pocket (plunger points out of the land)
  xprism(x_land - 1, fb_base) translate([0, z_pc]) gable_sq(sw_pk, sw_pk);
  // leg/solder relief behind it, and passage into the wire channel
  switch_relief(fb_base, z_pc, -1);
  box([WC[0][0] - 0.4, fb_base + 1.8], [WC[1][0] + 1, -0.8], [z_pc - 2, z_pc + 2]);
  // pad wire holes (they break into the pocket so the same wires can serve the fallback switch)
  for (s = [-1, 1]) xprism(x_land - 1, -1.0) translate([s * 3.6, z_cl + 5]) diamond(0.8);
  // tunnel from the +Y pad hole across to the wire channel
  yprism(WC[1][0] + 1, 4.4) translate([-1.4, z_cl + 5]) diamond(0.6);
}

module window_cuts() {
  // window recess with a 45 deg roof hidden under the knurled nut
  yprism(-win_w/2, win_w/2) polygon([[win_floor, Zw0], [R + 2, Zw0],
      [R + 2, Zw1 + (R + 2 - win_floor)], [win_floor, Zw1]]);
  // pocket for the panel's bottom tongue, slot for its top tongue
  box([win_floor - eps, win_floor + 1.5], [-3.2, 3.2], [Zw0 - 4, Zw0 + eps]);
  box([win_floor - eps, win_floor + 1.5], [-3.2, 3.2], [Zw1 - eps, Zt + 1]);
  // button flange pockets (teardrop = bridge-free)
  for (b = BTN) let(zc = Zw1 - b[1], dep = btn_ft + (b[4] ? btn_trav : 0.05))
    xprism(win_floor - dep, win_floor + eps) translate([0, zc]) teardrop(b[3]/2 + 0.3);
  // push-button tactile switch pocket behind HOURS
  zh = Zw1 - BTN[1][1];
  xprism(sw_base, win_floor - btn_ft - btn_trav + eps) translate([0, zh]) gable_sq(sw_pk, sw_pk);
  switch_relief(sw_base, zh, 1);                                                   // legs + solder joints
  box([sw_base - 1.8, sw_base - 0.4], [WC[1][0] + 1, -0.8], [zh - 2, zh + 2]);     // into wire channel
}

// =====================================================================
//  SLEEVE  (fluted, slides; finger + bump = sleeve switch actuator)
// =====================================================================
fing_ang = 36;   // finger edges sit in the flute grooves at 180 +/- 36 deg
fing_len = 18;
module sleeve() {
  difference() {
    union() {
      cylinder(r = sl_or, h = Ls, $fn = 200);
      rotate(180) clip_lugs();   // clip on the left (-Y) like the prop
    }
    translate([0, 0, -1]) cylinder(r = sl_ir, h = Ls + 2, $fn = 200);
    for (k = [0:flute_n - 1]) rotate(k * 360 / flute_n) translate([sl_or + 0.3, 0, -1]) cylinder(r = 0.9, h = Ls + 2, $fn = 16);
    // finger slots (hidden inside two flute grooves)
    for (s = [-1, 1]) rotate(180 + s * fing_ang) translate([sl_ir - 1, -0.4, Ls - fing_len]) cube([sl_or - sl_ir + 2, 0.8, fing_len + 1]);
    // edge chamfers
    translate([0, 0, -eps]) cylinder(r1 = sl_ir + 0.6, r2 = sl_ir, h = 0.6, $fn = 200);
    translate([0, 0, Ls - 0.6]) cylinder(r1 = sl_ir, r2 = sl_ir + 0.6 + eps, h = 0.6 + eps, $fn = 200);
  }
  bump();
}
module bump() {
  intersection() {
    yprism(-bump_w/2, bump_w/2) polygon([[-(sl_ir + 0.5), Ls - 9], [-bump_in, Ls - 9],
        [-bump_in, Ls - 0.5 - (sl_ir - bump_in)], [-(sl_ir + 0.5), Ls - 0.5 + 0.5]]);
    cylinder(r = sl_ir + 0.3, h = Ls, $fn = 200);
  }
}
// hinge lugs + bar for the clip (built on +Y, rotated to -Y in sleeve())
clip_w = 5.0; bar_y = 14.9; bar_z = 4.0; bar_r = 1.0;
module clip_lugs() {
  for (s = [-1, 1]) let(xc = s * (clip_w/2 + 0.2 + 0.6))
    multmatrix([[0,0,1,xc - 0.6],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) linear_extrude(1.2)
      polygon([[sl_or - 1.2, 0], [bar_y + 1.6, 0], [bar_y + 1.6, bar_z + 1.6], [sl_or - 1.2, bar_z + 1.6 + (bar_y + 2.8 - sl_or)]]);
  translate([-(clip_w/2 + 0.3), bar_y, bar_z]) rotate([0, 90, 0]) rotate(22.5) cylinder(r = bar_r, h = clip_w + 0.6, $fn = 8);
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
    translate([bar_y, 0]) rotate(-45) translate([0, -0.8]) square([3, 1.6]);   // snap opening: outward + down
  }
}
module clip_part() linear_extrude(clip_w) clip_2d();

// =====================================================================
//  BOTTOM CAP  (male thread, battery + contact face, domed)
// =====================================================================
r_neck = tap_core(bt_D, bt_P, bt_h, thread_clr) - 0.15;
cap_r  = cap_d / 2;
module bottom_cap() {
  difference() {
    union() {
      intersection() {
        male_thread(bt_D, bt_P, bt_h, -0.3, bt_len - 0.5);
        translate([0, 0, bt_len - 0.5 - 20]) cylinder(r1 = bt_D/2 + 20, r2 = bt_D/2 - 0.6, h = 20 + eps);
      }
      translate([0, 0, -0.3]) cylinder(r = r_neck, h = z_cone0 + fM - r_neck + 0.3);
      translate([0, 0, z_cone0 + fM - r_neck - eps]) cylinder(r1 = r_neck, r2 = r_face, h = r_neck - r_face + eps);
      translate([0, 0, -0.3 - (cap_r - 7.6)]) cylinder(r1 = cap_r, r2 = 7.6, h = cap_r - 7.6);   // 45 deg shoulder
      translate([0, 0, -6]) cylinder(r = cap_r, h = 6 - 0.3 - (cap_r - 7.6) + eps);
      translate([0, 0, -6]) intersection() { sphere(r = cap_r, $fn = 160); translate([0, 0, -cap_r]) cylinder(r = cap_r + 1, h = cap_r); }
    }
    // decorative recessed strip with two dots (front)
    difference() {
      intersection() {
        box([0, cap_r + 1], [-1.2, 1.2], [-13.5, -4.0]);
        difference() { translate([0, 0, -20]) cylinder(r = cap_r + 2, h = 20);
          union() { translate([0, 0, -6]) cylinder(r = cap_r - 0.5, h = 3); translate([0, 0, -6]) sphere(r = cap_r - 0.5, $fn = 160); } }
      }
      for (zz = [-6.0, -9.5]) let(rr = zz > -6 ? cap_r - 0.5 : sqrt(pow(cap_r - 0.5, 2) - pow(zz + 6, 2)))
        translate([rr, 0, zz]) sphere(r = 0.75, $fn = 16);
    }
  }
}

// =====================================================================
//  BATTERY SPRING  (printed flexure, flat; boss presses the cell's - end)
// =====================================================================
module sector(a0, a1, r = 20) polygon(concat([[0, 0]], [for (a = [a0:5:a1]) [r * cos(a), r * sin(a)]]));
module battery_spring_2d() {
  Ro = bay_r + 0.05;
  difference() { circle(r = Ro); circle(r = Ro - 0.8); rotate(90) translate([Ro - 1.2, -1.0]) square([2, 2]); } // ring + wire notch
  circle(r = 2.2);
  for (k = [0:2]) rotate(30 + k * 120) {
    intersection() { difference() { circle(r = 4.35); circle(r = 3.45); } sector(0, 100); }  // 100 deg flex arm
    translate([1.8, -0.45]) square([2.0, 0.9]);                                             // spoke to centre
    rotate(100) translate([4.0, -0.45]) square([Ro - 0.5 - 4.0, 0.9]);                       // spoke to ring
  }
}
module battery_spring() {
  difference() {
    union() {
      linear_extrude(spring_t) battery_spring_2d();
      cylinder(r = 2.0, h = spring_t + boss_h, $fn = 32);
    }
    translate([0, 0, -1]) cylinder(r = 0.6, h = 10, $fn = 12);         // wire through the boss
  }
}

// =====================================================================
//  KNURLED NUT  (screws onto the top spigot, clamps the LED head)
// =====================================================================
nut_z0 = Zw1 + nut_gap;
nut_lip_r = 7.1;
module knurl_nut() {
  difference() {
    translate([0, 0, nut_z0]) cylinder(r = nut_od/2, h = Zt + z_nut_top - nut_z0, $fn = 200);
    for (k = [0:23]) rotate(k * 15) translate([nut_od/2 + 0.15, 0, nut_z0 - 1]) cylinder(r = 0.55, h = 30, $fn = 12);
    thread_tap(tt_D, tt_P, tt_h, thread_clr, nut_z0 - 1, Zt + 0.1);
    translate([0, 0, nut_z0 - eps]) cylinder(r1 = tt_D/2 + thread_clr + 0.4, r2 = tt_D/2 - 0.6, h = 1.0);
    translate([0, 0, Zt - 0.3]) cylinder(r = flange_r + 0.3, h = flange_t + 0.3 + eps);
    translate([0, 0, Zt]) cylinder(r = nut_lip_r, h = 10);
  }
}

// =====================================================================
//  LED HEAD (white = reflector): both LEDs side by side, tips in the middle of
//  the clear light window; resistors + wires in the bores below.
//  local z = 0 is the top face of the body (Zt)
// =====================================================================
module led_mount() {
  difference() {
    union() {
      translate([0, 0, -stem_len]) linear_extrude(stem_len) stadium(stem_r, y_red, y_wht);
      translate([0, 0, -(flange_r - stem_r)]) cylinder(r1 = stem_r, r2 = flange_r, h = flange_r - stem_r);
      cylinder(r = flange_r, h = flange_t);
    }
    for (l = [[y_red, red_rim_z], [y_wht, wht_rim_z]]) {
      translate([0, l[0], -stem_len - 1]) cylinder(r = led_d/2 + 0.1, h = stem_len + 1 + flange_t + eps, $fn = 40);
      translate([0, l[0], l[1]]) cylinder(r = led_rim_d/2 + 0.1, h = flange_t - l[1] + eps, $fn = 40);
    }
  }
}
// clear ring both LEDs shine through; push-fits into the nut lip below and the dome above
module light_window() translate([0, 0, z_nut_top]) difference() {
  union() {
    ch = win_or - nut_lip_r;                       // 45 deg bevel underneath = prints without support
    cylinder(r1 = nut_lip_r, r2 = win_or, h = ch + eps, $fn = 160);
    translate([0, 0, ch]) cylinder(r = win_or, h = window_h - ch, $fn = 160);
    translate([0, 0, -spig_h]) cylinder(r = nut_lip_r + dome_press/2, h = spig_h + eps, $fn = 160);
    translate([0, 0, window_h - eps]) cylinder(r = win_ir, h = spig_h + eps, $fn = 160);
  }
  translate([0, 0, -spig_h - 1]) cylinder(r = spig_ir, h = window_h + 2 * spig_h + 2, $fn = 160);
}
// opaque dome cap (white); its 45 deg inner cone reflects the light out through the window
dome_skirt = 3.5;
module dome() translate([0, 0, z_win_top]) difference() {
  union() {
    cylinder(r = win_or, h = dome_skirt, $fn = 160);
    translate([0, 0, dome_skirt]) intersection() { sphere(r = win_or, $fn = 160); cylinder(r = win_or + 1, h = win_or + 1, $fn = 160); }
  }
  translate([0, 0, -1]) cylinder(r = win_ir - dome_press/2, h = spig_h + 1 + 0.2, $fn = 160);
  translate([0, 0, spig_h + 0.2 - eps]) cylinder(r1 = spig_ir, r2 = 0, h = spig_ir);
}

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
module window_panel() {
  T = panel_t;
  difference() {
    union() {
      // plate with softened face edges
      hull() {
        translate([-panel_w/2, 0.15, 0]) cube([panel_w, window_len - 0.3, T - 0.3]);
        translate([-panel_w/2 + 0.3, 0.15, 0]) cube([panel_w - 0.6, window_len - 0.3, T]);
      }
      // tongues (bottom into body pocket, top under the knurled nut)
      translate([-3.0, -3.5, 0]) cube([6.0, 3.7, 1.2]);
      translate([-3.0, window_len - 0.2, 0]) cube([6.0, 3.2, 1.2]);
      // raised details (0.6 mm, paint-ready)
      translate([0, 0, T - eps]) linear_extrude(0.6) {
        translate([0, vy(15.0)]) label("MINUTES");
        translate([0, vy(29.0)]) label("HOURS");
        translate([0, vy(42.5)]) label("WEEKS");
        translate([0, vy(55.0)]) label("YEAR");
        for (v = [22.5, 36.0]) translate([-5.35, vy(v)]) polygon([[-0.7, -0.9], [0.75, 0], [-0.7, 0.9]]);  // arrows
        translate([5.3, vy(19.6)]) circle(r = 0.75, $fn = 20);                                           // indicator dot
      }
      for (s = [-1, 1]) translate([s * 5.2, vy(55.0), T - 0.3]) intersection() {
        sphere(r = 0.9, $fn = 24); cylinder(r = 1.0, h = 1.1, $fn = 24); }                               // YEAR buttons
    }
    // button holes
    for (b = BTN) translate([0, vy(b[1]), -1]) cylinder(r = b[2]/2 + hole_clr, h = T + 2, $fn = 64);
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
module button(i) let(b = BTN[i], hl = panel_t + btn_proud) {
  cylinder(r = b[3]/2, h = btn_ft, $fn = 64);
  translate([0, 0, btn_ft - eps]) hull() {
    cylinder(r = b[2]/2, h = hl - 0.4, $fn = 64);
    cylinder(r = b[2]/2 - 0.4, h = hl, $fn = 64);
  }
}

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

// =====================================================================
//  assembly transforms
// =====================================================================
M_panel = [[0,0,1,win_floor],[1,0,0,0],[0,1,0,Zw0],[0,0,0,1]];
module at_button(i, pressed = false) let(zc = Zw1 - BTN[i][1], x0 = win_floor - btn_ft - (pressed ? btn_trav : 0))
  multmatrix([[0,0,1,x0],[1,0,0,0],[0,1,0,zc],[0,0,0,1]]) children();
module at_clip(s) rotate(180) multmatrix([[0,0,1,-clip_w/2],[1,0,0,0],[0,1,0,s + bar_z],[0,0,0,1]]) children();

// ---------------------------------------------------------------- dummies (for the view + checks)
module dummy_switch(x_tip, zc, outward = 1) {   // outward = +1: plunger toward +x
  base = outward > 0 ? x_tip - sw_tot : x_tip + sw_tot;
  for (sy = [-1, 1], sz = [-1, 1])               // leg shoulders + legs trimmed to 1.5 mm
    translate([outward > 0 ? base - 1.5 : base - 0.5, sy * 2.25 - 0.35, zc + sz * (sw_w/2 + 0.2) - 0.2])
      cube([2.0, 0.7, 0.4]);
  if (outward > 0) {
    translate([x_tip - sw_tot, -sw_w/2, zc - sw_w/2]) cube([sw_body_h, sw_w, sw_w]);
    translate([x_tip - sw_plunger_h, 0, zc]) rotate([0, 90, 0]) cylinder(r = 1.75, h = sw_plunger_h, $fn = 24);
  } else {
    translate([x_tip + sw_plunger_h, -sw_w/2, zc - sw_w/2]) cube([sw_body_h, sw_w, sw_w]);
    translate([x_tip, 0, zc]) rotate([0, 90, 0]) cylinder(r = 1.75, h = sw_plunger_h, $fn = 24);
  }
}
module dummy_led(y, rim_z) translate([0, y, Zt + rim_z]) {
  cylinder(r = led_rim_d/2, h = 1.0, $fn = 32);
  cylinder(r = led_d/2, h = led_len - led_d/2, $fn = 32);
  translate([0, 0, led_len - led_d/2]) sphere(r = led_d/2, $fn = 32);
}
// copper tape, drawn only for the build-guide pictures (where each piece goes)
module tape_body() {
  for (sg = [-1, 1]) box([x_land, x_land + tape_t], sg > 0 ? [sw_pk + 0.3, ch_w/2 - 0.2] : [-(ch_w/2 - 0.2), -(sw_pk + 0.3)], [z_cl + 0.3, z_cl + 8]);  // pads P1/P2
  intersection() {                                                                   // B+ strip on the contact cone
    translate([0, 0, z_cone0 - 0.02]) difference() { cylinder(r1 = fM + 0.02, r2 = bay_r + 0.02, h = fM - bay_r); cylinder(r1 = fM - 0.12, r2 = bay_r - 0.12, h = fM - bay_r); }
    box([-2, 2], [-10, 0], [0, 20]);
  }
}
module tape_bump() intersection() {                                                   // on the sleeve finger bump (sleeve coords)
  yprism(-bump_w/2 + 0.3, bump_w/2 - 0.3) polygon([[-bump_in - 0.1, Ls - 8.8], [-bump_in + 0.01, Ls - 8.8], [-bump_in + 0.01, Ls - 3.2], [-bump_in - 0.1, Ls - 3.2]]);
  cylinder(r = sl_ir, h = Ls);
}
module tape_cap() translate([0, 0, z_face]) cylinder(r = r_face, h = 0.1);           // disc on the cap face
module dummy_cells() for (i = [0:n_cells - 1]) translate([0, 0, z_face + i * cell_l + 0.02]) cylinder(r = cell_d/2, h = cell_l - 0.04, $fn = 48);

// =====================================================================
//  part selector
// =====================================================================
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
    color(SILVER) knurl_nut();
    color(SILVER) multmatrix(M_panel) window_panel();
    for (i = [0:2]) color(BLACK) at_button(i) button(i);
    color(SILVER) translate([0, 0, Zt]) led_mount();
    color(show_lit && is_open ? [1, 0.1, 0.05, 0.85] : [0.85, 0.85, 0.88, 0.55]) translate([0, 0, Zt]) light_window();
    color(SILVER) translate([0, 0, Zt]) dome();
    if (cutaway) {
      color([0.6, 0.6, 0.6]) dummy_cells();
      color("orange") translate([0, 0, z_sd + spring_t]) rotate([180, 0, 0]) battery_spring();
      color([0.2, 0.2, 0.2]) dummy_switch(sw_tip, Zw1 - BTN[1][1], 1);
      color("red") dummy_led(y_red, red_rim_z);
      color("white") dummy_led(y_wht, wht_rim_z);
    }
  }
}

module print_pose(name) {
  if (name == "body") body();
  else if (name == "sleeve") translate([0, 0, Ls]) rotate([180, 0, 0]) sleeve();          // top edge on the bed
  else if (name == "bottom_cap") translate([0, 0, z_face]) rotate([180, 0, 0]) bottom_cap(); // contact face on the bed
  else if (name == "battery_spring") battery_spring();
  else if (name == "knurl_nut") translate([0, 0, Zt + z_nut_top]) rotate([180, 0, 0]) knurl_nut(); // lip on the bed
  else if (name == "led_mount") translate([0, 0, stem_len]) led_mount();
  else if (name == "light_window") translate([0, 0, spig_h - z_nut_top]) light_window();
  else if (name == "dome") translate([0, 0, -z_win_top]) dome();
  else if (name == "window_panel") translate([0, 3.5, 0]) window_panel();
  else if (name == "window_panel_base") translate([0, 3.5, 0]) window_panel_base();
  else if (name == "window_panel_details") translate([0, 3.5, 0]) window_panel_details();
  else if (name == "panel_detail_zone") translate([0, 3.5, 0]) panel_detail_zone();
  else if (name == "btn_minutes") button(0);
  else if (name == "btn_hours") button(1);
  else if (name == "btn_weeks") button(2);
  else if (name == "clip") clip_part();
  else if (name == "fit_test") fit_test();
  else if (name == "thread_test") thread_test();
}
module assembled_pose(name) {
  s = s_pos;
  if (name == "body") body();
  else if (name == "sleeve") translate([0, 0, s]) sleeve();
  else if (name == "clip") translate([0, 0, s]) at_clip(0) clip_part();
  else if (name == "bottom_cap") bottom_cap();
  else if (name == "battery_spring") translate([0, 0, z_sd + spring_t]) rotate([180, 0, 0]) battery_spring();
  else if (name == "knurl_nut") knurl_nut();
  else if (name == "led_mount") translate([0, 0, Zt]) led_mount();
  else if (name == "light_window") translate([0, 0, Zt]) light_window();
  else if (name == "dome") translate([0, 0, Zt]) dome();
  else if (name == "window_panel") multmatrix(M_panel) window_panel();
  else if (name == "window_panel_base") multmatrix(M_panel) window_panel_base();
  else if (name == "window_panel_details") multmatrix(M_panel) window_panel_details();
  else if (name == "panel_detail_zone") multmatrix(M_panel) panel_detail_zone();
  else if (name == "btn_minutes") at_button(0) button(0);
  else if (name == "btn_hours") at_button(1) button(1);
  else if (name == "btn_hours_pressed") at_button(1, true) button(1);
  else if (name == "btn_weeks") at_button(2) button(2);
  // dummies used by the verification script
  else if (name == "cells") dummy_cells();
  else if (name == "push_switch") dummy_switch(sw_tip, Zw1 - BTN[1][1], 1);
  else if (name == "fallback_switch") dummy_switch(x_land - sw_press, z_pc, -1);
  else if (name == "led_red") dummy_led(y_red, red_rim_z);
  else if (name == "led_white") dummy_led(y_wht, wht_rim_z);
  else if (name == "tape_body") tape_body();
  else if (name == "tape_cap") tape_cap();
  else if (name == "tape_bump_open") translate([0, 0, s_open]) tape_bump();
  else if (name == "tape_bump_closed") translate([0, 0, s_open + travel]) tape_bump();
}

if (part == "assembly") assembly();
else if (pose == "print") print_pose(part);
else assembled_pose(part);
