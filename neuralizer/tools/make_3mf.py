#!/usr/bin/env python3
"""
Builds the Bambu Studio project and per-part 3MF files from stl/ (print orientation).

  3mf/neuralizer_P1S_PETG_project.3mf   Bambu Studio project: 4 plates, 3 filament slots
                                        (1 white, 2 black, 3 clear PETG), per-object print
                                        settings, multicolour panel, button and top cap (AMS)
  3mf/parts/<part>.3mf                  one plain 3MF per part (any slicer), with colour
                                        and the same per-object settings

The file layout mirrors Bambu Studio's own exporter (src/libslic3r/Format/bbs_3mf.cpp):
3D/3dmodel.model with component objects -> 3D/Objects/object_N.model meshes,
Metadata/model_settings.config (objects, parts, plates), Metadata/project_settings.config
(full printer + process + filament config, flattened from Bambu's system profiles).

Usage:  python3 tools/make_3mf.py [--profiles <BambuStudio>/resources/profiles/BBL] [--thumbs <dir>]
Without --profiles the cached tools/bambu/project_settings_P1S_PETG.json is used.
"""
import argparse, glob, io, json, math, os, pathlib, uuid, zipfile, datetime
import numpy as np
import trimesh

ROOT = pathlib.Path(__file__).resolve().parent.parent
STL, OUT = ROOT / "stl", ROOT / "3mf"
CACHE = ROOT / "tools" / "bambu" / "project_settings_P1S_PETG.json"
APP = "BambuStudio-02.08.04.57"          # generator tag -> loaded as a Bambu project
BED = 256.0                               # P1S printable area
STRIDE = BED * 1.2                        # PartPlateList::plate_stride_x(): width * (1 + 1/5)

PRINTER, PROCESS, FILAMENT = "Bambu Lab P1S 0.4 nozzle", "0.16mm Optimal @BBL X1C", "Generic PETG"
FILAMENTS = [("White PETG", "#F2F2F2"), ("Black PETG", "#161616"), ("Clear PETG", "#D6EAF2")]
W, B, C = 1, 2, 3

# per-object print settings (object scope in Bambu Studio). All support-free.
S_STRUCT = {"layer_height": "0.16", "wall_loops": "4", "sparse_infill_density": "15%", "sparse_infill_pattern": "gyroid",
            "seam_position": "back"}
S_FINE = {"layer_height": "0.12", "wall_loops": "4", "sparse_infill_density": "30%", "sparse_infill_pattern": "gyroid",
          "top_shell_layers": "6"}
S_SOLID = {"layer_height": "0.12", "wall_loops": "2", "sparse_infill_density": "100%", "sparse_infill_pattern": "zig-zag"}
PARTS = {   # name: (filament, settings, rotate_z_deg)
    "body":           (W, {**S_STRUCT, "brim_type": "outer_only", "brim_width": "5"}, -90),
    "sleeve":         (W, {**S_STRUCT, "wall_loops": "3", "brim_type": "outer_only", "brim_width": "3"}, -90),
    "sled":           (W, {**S_FINE, "layer_height": "0.16", "wall_loops": "3", "brim_type": "outer_only", "brim_width": "3"}, 0),
    "bottom_cap":     (W, S_FINE, 0),
    "clip":           (W, {**S_SOLID, "wall_loops": "3"}, 0),
    "window_panel":   (W, {"layer_height": "0.12", "wall_loops": "3", "sparse_infill_density": "100%",
                           "top_surface_pattern": "monotonicline"}, 0),
    "btn_hours":      (W, S_SOLID, 0),
    "top_cap":        (C, {"layer_height": "0.16", "wall_loops": "3", "sparse_infill_density": "100%",
                           "sparse_infill_pattern": "zig-zag"}, 0),
    "fit_test":       (W, {"layer_height": "0.16", "wall_loops": "3", "sparse_infill_density": "15%"}, 0),
    "thread_test":    (W, {"layer_height": "0.12", "wall_loops": "4", "sparse_infill_density": "30%"}, 0),
}
# multicolour objects: one volume per colour (exact splits made by tools/split_colours.py)
MULTI = {"window_panel": [("panel (white)", W, "window_panel_base"), ("labels + plates (black)", B, "window_panel_details")],
         "btn_hours":    [("button (white)", W, "btn_hours_base"), ("top (black)", B, "btn_hours_top")],
         "top_cap":      [("spigot + light ring (clear)", C, "top_cap_clear"), ("dome (white)", W, "top_cap_white")]}
PLATES = [
    ("1 - Test prints - print first (white)", ["fit_test", "thread_test"]),
    ("2 - White parts", ["body", "sleeve", "sled", "bottom_cap", "clip"]),
    ("3 - Window panel + HOURS button - AMS white + black", ["window_panel", "btn_hours"]),
    ("4 - Top cap - AMS clear + white", ["top_cap"]),
]

# ------------------------------------------------------------------ project config
META = {"type", "name", "inherits", "from", "instantiation", "setting_id", "filament_id", "compatible_printers",
        "compatible_printers_condition", "compatible_prints", "compatible_prints_condition", "description",
        "is_custom_defined", "version", "printer_variant"}

def build_project_settings(profiles):
    idx = {}
    for kind in ("machine", "process", "filament"):
        for f in glob.glob(f"{profiles}/{kind}/*.json"):
            try:
                j = json.load(open(f))
            except Exception:
                continue
            if "name" in j:
                idx[(kind, j["name"])] = j
    def flat(kind, name):
        j = idx[(kind, name)]
        base = dict(flat(kind, j["inherits"])) if j.get("inherits") else {}
        base.update(j)
        return base
    pr, ps, fl = flat("machine", PRINTER), flat("process", PROCESS), flat("filament", FILAMENT)
    cfg = {}
    for src in (pr, ps):
        cfg.update({k: v for k, v in src.items() if k not in META})
    n = len(FILAMENTS)
    for k, v in fl.items():                     # filament options are per-filament vectors
        if k in META or not isinstance(v, list) or len(v) != 1:
            continue
        cfg[k] = v * n
    cfg.update({
        "name": "project_settings", "from": "project", "version": APP.split("-")[1],
        "printer_settings_id": PRINTER, "print_settings_id": PROCESS,
        "filament_settings_id": [FILAMENT] * n, "filament_ids": [fl.get("filament_id", "")] * n,
        "filament_colour": [c for _, c in FILAMENTS], "filament_map": ["1"] * n,
        "inherits_group": [""] * (n + 2), "different_settings_to_system": [""] * (n + 2),
        "curr_bed_type": "Textured PEI Plate",
        # purge volumes (mm^3) from row -> to column; used: white<->black (plate 3), clear->white (plate 4)
        "flush_volumes_matrix": ["0", "160", "280", "560", "0", "620", "240", "160", "0"],
        "flush_volumes_vector": ["140"] * (2 * n), "flush_multiplier": "1",
    })
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cfg, indent=4, sort_keys=True))
    return cfg

# ------------------------------------------------------------------ geometry
def load_part(name):
    """returns list of (volume_name, filament, mesh) in print orientation, xy-centred, on z=0"""
    if name in MULTI:
        vols = [(vn, fil, trimesh.load(STL / f"{f}.stl", force="mesh")) for vn, fil, f in MULTI[name]]
    else:
        vols = [(name, PARTS[name][0], trimesh.load(STL / f"{name}.stl", force="mesh"))]
    rz = math.radians(PARTS[name][2])
    R = trimesh.transformations.rotation_matrix(rz, [0, 0, 1])
    allv = np.vstack([v[2].vertices for v in vols])
    allv = trimesh.transform_points(allv, R)
    lo, hi = allv.min(0), allv.max(0)
    T = trimesh.transformations.translation_matrix([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    out = []
    for vn, fil, m in vols:
        m = m.copy(); m.apply_transform(T @ R); out.append((vn, fil, m))
    return out, (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])

def layout(sizes, gap=10.0, margin=18.0):
    """simple shelf packing on the 256x256 bed, centred; returns xy centres"""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    rows, row, x, rw = [], [], 0.0, BED - 2 * margin
    for i in order:
        w = sizes[i][0]
        if row and x + w > rw:
            rows.append(row); row, x = [], 0.0
        row.append(i); x += w + gap
    rows.append(row)
    pos = [None] * len(sizes)
    heights = [max(sizes[i][1] for i in r) for r in rows]
    total_h = sum(heights) + gap * (len(rows) - 1)
    y = BED / 2 + total_h / 2
    for r, h in zip(rows, heights):
        total_w = sum(sizes[i][0] for i in r) + gap * (len(r) - 1)
        x = BED / 2 - total_w / 2
        for i in r:
            pos[i] = (x + sizes[i][0] / 2, y - h / 2)
            x += sizes[i][0] + gap
        y -= h + gap
    return pos

# ------------------------------------------------------------------ xml writers
def f(v): return f"{v:.6g}"
def mesh_xml(oid, mesh, uuid_s):
    vs = "".join(f'     <vertex x="{f(a)}" y="{f(b)}" z="{f(c)}"/>\n' for a, b, c in mesh.vertices)
    ts = "".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in mesh.faces)
    return (f'  <object id="{oid}" p:UUID="{uuid_s}" type="model">\n   <mesh>\n    <vertices>\n{vs}    </vertices>\n'
            f'    <triangles>\n{ts}    </triangles>\n   </mesh>\n  </object>\n')

def model_header(meta):
    h = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
         'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
         'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
         'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n')
    return h + "".join(f' <metadata name="{k}">{v}</metadata>\n' for k, v in meta.items())

def xfm(rz_deg, tx, ty):
    # 3MF transform: column-major 3x4 (m00 m01 m02 m10 ... m30 m31 m32), row-vector convention
    return f"1 0 0 0 1 0 0 0 1 {f(tx)} {f(ty)} 0"

def write_3mf(path, plates, bambu_project, cfg=None, thumbs=None, title="MIB Neuralizer"):
    """plates: list of (plate_name, [(obj_name, settings, volumes, (x, y))])"""
    z = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    today = datetime.date.today().isoformat()
    meta = {"Title": title, "Designer": "", "Description": "MIB Neuralizer - parametric, support-free PETG prop",
            "CreationDate": today, "ModificationDate": today, "BambuStudio:3mfVersion": "1"}
    if bambu_project:
        meta["Application"] = APP
    else:
        meta["Application"] = "neuralizer-make_3mf"
    main_objs, build, cfg_objs, plate_xml, rel_targets = [], [], [], [], []
    nid, backup = 1, 0
    for p_i, (pname, objs) in enumerate(plates):
        # plate origins: PartPlateList::compute_shape_position (3 columns for 4-9 plates)
        ox, oy = ((p_i % 3) * STRIDE, -(p_i // 3) * STRIDE) if bambu_project else (0.0, 0.0)
        inst = []
        for oname, settings, vols, (x, y) in objs:
            backup += 1
            sub = f"3D/Objects/object_{backup}.model"
            rel_targets.append(sub)
            vol_ids, sub_xml = [], []
            for k, (vn, fil, m) in enumerate(vols):
                vol_ids.append(nid)
                sub_xml.append(mesh_xml(nid, m, f"{(k + (backup << 16)):08x}-81cb-4c03-9d28-80fed5dfa1dc"))
                nid += 1
            oid = nid; nid += 1
            z.writestr(sub, model_header({"BambuStudio:3mfVersion": "1"}) + " <resources>\n" + "".join(sub_xml) + " </resources>\n <build/>\n</model>\n")
            comps = "".join(f'    <component p:path="/{sub}" objectid="{v}" p:UUID="{(k + (backup << 16)):08x}-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                            for k, v in enumerate(vol_ids))
            main_objs.append(f'  <object id="{oid}" p:UUID="{backup:08x}-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <components>\n{comps}   </components>\n  </object>\n')
            build.append(f'  <item objectid="{oid}" p:UUID="{oid:08x}-b1ec-4553-aec9-835e5b724bb4" transform="{xfm(0, ox + x, oy + y)}"/>\n')
            # model_settings: object + parts
            fil0 = vols[0][1]
            o = [f'  <object id="{oid}">\n', f'    <metadata key="name" value="{oname}"/>\n', f'    <metadata key="extruder" value="{fil0}"/>\n']
            for k, v in settings.items():
                v = ",".join(v) if isinstance(v, list) else v
                o.append(f'    <metadata key="{k}" value="{v}"/>\n')
            o.append(f'    <metadata face_count="{sum(len(m.faces) for *_, m in vols)}"/>\n')
            for k, (vn, fil, m) in enumerate(vols):
                o.append(f'    <part id="{vol_ids[k]}" subtype="normal_part">\n'
                         f'      <metadata key="name" value="{vn}"/>\n'
                         f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                         f'      <metadata key="extruder" value="{fil}"/>\n'
                         f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                         f'    </part>\n')
            o.append("  </object>\n")
            cfg_objs.append("".join(o))
            inst.append(oid)
        px = [f'  <plate>\n', f'    <metadata key="plater_id" value="{p_i + 1}"/>\n', f'    <metadata key="plater_name" value="{pname}"/>\n',
              f'    <metadata key="locked" value="false"/>\n', f'    <metadata key="bed_type" value="Textured PEI Plate"/>\n']
        if thumbs and (thumbs / f"plate_{p_i + 1}.png").exists():
            z.write(thumbs / f"plate_{p_i + 1}.png", f"Metadata/plate_{p_i + 1}.png")
            px.append(f'    <metadata key="thumbnail_file" value="Metadata/plate_{p_i + 1}.png"/>\n')
        for j, oid in enumerate(inst):
            px.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n'
                      f'      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{1000 + oid}"/>\n    </model_instance>\n')
        px.append("  </plate>\n")
        plate_xml.append("".join(px))
    main = (model_header(meta) + " <resources>\n" + "".join(main_objs) + " </resources>\n"
            f' <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">\n' + "".join(build) + " </build>\n</model>\n")
    z.writestr("3D/3dmodel.model", main)
    z.writestr("3D/_rels/3dmodel.model.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
               + "".join(f' <Relationship Target="/{t}" Id="rel-{i + 1}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n' for i, t in enumerate(rel_targets))
               + "</Relationships>\n")
    rels = (' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n')
    if thumbs and (thumbs / "plate_1.png").exists():
        rels += ' <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>\n'
    z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + rels + "</Relationships>")
    z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
               ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
               ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
               ' <Default Extension="png" ContentType="image/png"/>\n <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>')
    z.writestr("Metadata/model_settings.config", '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(cfg_objs)
               + ("".join(plate_xml) if bambu_project else "") + "</config>\n")
    if bambu_project and cfg is not None:
        z.writestr("Metadata/project_settings.config", json.dumps(cfg, indent=4, sort_keys=True))
    z.close()

def plan():
    """[(plate_name, [(obj, settings, vols, (x,y))])] for the project"""
    out = []
    for pname, names in PLATES:
        loaded = [load_part(n) for n in names]
        pos = layout([s for _, s in loaded])
        out.append((pname, [(n, PARTS[n][1], v, p) for n, (v, s), p in zip(names, loaded, pos)]))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles"); ap.add_argument("--thumbs"); ap.add_argument("--layout-json")
    a = ap.parse_args()
    cfg = build_project_settings(a.profiles) if a.profiles else json.loads(CACHE.read_text())
    # Bambu Studio checks filament_extruder_variant against filament_self_index (one entry per
    # filament variant). A missing filament_self_index defaults to [1], so a 3-filament project
    # without it is rejected with "Invalid configuration file" (PresetBundle::load_config_file_config).
    nfil = len(cfg["filament_colour"])
    cfg["filament_self_index"] = [str(i + 1) for i in range(nfil)]
    plates = plan()
    if a.layout_json:   # for the plate thumbnail renderer: centred meshes + positions
        md = ROOT / "build" / "plate_meshes"; md.mkdir(parents=True, exist_ok=True)
        js = []
        for pn, objs in plates:
            jo = []
            for o, s_, v, p in objs:
                vols = []
                for k, (vn, fil, m) in enumerate(v):
                    fn = md / f"{o}_{k}.stl"; m.export(fn); vols.append({"file": f"plate_meshes/{o}_{k}.stl", "fil": fil})
                jo.append({"name": o, "pos": p, "vols": vols})
            js.append({"name": pn, "objects": jo})
        pathlib.Path(a.layout_json).write_text(json.dumps(js, indent=1))
    OUT.mkdir(exist_ok=True); (OUT / "parts").mkdir(exist_ok=True)
    thumbs = pathlib.Path(a.thumbs) if a.thumbs else None
    write_3mf(OUT / "neuralizer_P1S_PETG_project.3mf", plates, True, cfg, thumbs)
    for pname, objs in plates:
        for o in objs:
            single = [(f"{o[0]}", [(o[0], o[1], o[2], (BED / 2, BED / 2))])]
            write_3mf(OUT / "parts" / f"{o[0]}.3mf", single, False, title=f"MIB Neuralizer - {o[0]}")
    print("wrote", OUT / "neuralizer_P1S_PETG_project.3mf", "and", len(list((OUT / 'parts').glob('*.3mf'))), "part files")
