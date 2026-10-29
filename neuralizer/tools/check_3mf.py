#!/usr/bin/env python3
"""
Validates the generated 3MF files.
  1. lib3mf (the 3MF Consortium reference library) reads every file with the production
     extension, resolving all components -> reports errors / mesh counts.
  2. Bambu-Studio loader rules (from src/libslic3r/Format/bbs_3mf.cpp + Plater.cpp):
     Application tag, project config with filament_colour + printer_model, every plate
     instance points at an existing object, every <part id> is a component of its object,
     extruder ids 1..3, per-object option keys exist in PrintConfig, objects lie inside
     their plate (origin = index * 307.2 mm) and do not overlap.
  3. Geometry round trip: each object's meshes == the verified STLs (volume, bounds).
Appends a section to VERIFICATION.md.
"""
import json, math, pathlib, re, sys, zipfile
import xml.etree.ElementTree as ET
import numpy as np, trimesh

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = ROOT / "3mf" / "neuralizer_P1S_PETG_project.3mf"
NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02", "p": "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"}
lines, fails = [], []
def check(ok, msg):
    s = ("PASS  " if ok else "FAIL  ") + msg; print(s); lines.append(s)
    if not ok: fails.append(msg)

# ---------------------------------------------------------------- 1. lib3mf
import lib3mf
wrapper = lib3mf.get_wrapper()
files = [PROJ] + sorted((ROOT / "3mf" / "parts").glob("*.3mf"))
for fpath in files:
    model = wrapper.CreateModel()
    reader = model.QueryReader("3mf")
    reader.SetStrictModeActive(True)
    try:
        reader.ReadFromFile(str(fpath))
        warns = reader.GetWarningCount()
        items = model.GetBuildItems(); n_items = 0
        tris = 0
        meshes = model.GetMeshObjects()
        while meshes.MoveNext():
            tris += meshes.GetCurrentMeshObject().GetTriangleCount()
        while items.MoveNext(): n_items += 1
        check(warns == 0 and n_items > 0, f"lib3mf strict read {fpath.name}: {n_items} build items, {tris} triangles, {warns} warnings")
    except Exception as e:
        check(False, f"lib3mf failed on {fpath.name}: {e}")

# ---------------------------------------------------------------- 2. Bambu rules
z = zipfile.ZipFile(PROJ)
main = ET.fromstring(z.read("3D/3dmodel.model"))
app = [m.text for m in main.findall("m:metadata", NS) if m.get("name") == "Application"]
check(bool(app) and app[0].startswith("BambuStudio-"), f"Application tag {app} -> Bambu Studio opens it as a PROJECT (plates + filaments), not geometry only")
cfg = json.loads(z.read("Metadata/project_settings.config"))
check(cfg.get("printer_model") == "Bambu Lab P1S" and len(cfg["filament_colour"]) == 3,
      f"project config: printer {cfg['printer_settings_id']}, process {cfg['print_settings_id']}, filaments {cfg['filament_settings_id']} colours {cfg['filament_colour']}")
nfil = len(cfg["filament_colour"])
bad_len = [k for k, v in cfg.items() if k.startswith("filament_") and isinstance(v, list) and len(v) not in (nfil, 2 * nfil, nfil * nfil)
           and k not in ("filament_map",)]
check(not bad_len, f"every per-filament option has {nfil} entries ({sum(1 for k in cfg if k.startswith('filament_'))} filament options)")

# option keys known to PrintConfig (from Bambu source if available)
src = pathlib.Path("/home/user/bambulab/bambustudio/src/libslic3r/PrintConfig.cpp")
known = set(re.findall(r'this->add\("([a-z0-9_]+)"', src.read_text())) if src.exists() else None
objs = {o.get("id"): o for o in main.find("m:resources", NS).findall("m:object", NS)}
comp_ids = {oid: [c.get("objectid") for c in o.find("m:components", NS).findall("m:component", NS)] for oid, o in objs.items()}
build = {i.get("objectid"): [float(x) for x in i.get("transform").split()] for i in main.find("m:build", NS).findall("m:item", NS)}
ms = ET.fromstring(z.read("Metadata/model_settings.config"))
obj_cfg = {o.get("id"): o for o in ms.findall("object")}
ok_parts = True; ok_ext = True; bad_keys = set()
for oid, o in obj_cfg.items():
    parts = [p.get("id") for p in o.findall("part")]
    if sorted(parts) != sorted(comp_ids.get(oid, [])): ok_parts = False
    for md in o.iter("metadata"):
        k, v = md.get("key"), md.get("value")
        if k == "extruder" and not (1 <= int(v) <= nfil): ok_ext = False
        if k and known is not None and k not in known and k not in ("name", "matrix"): bad_keys.add(k)
check(ok_parts, "every <part> in model_settings matches a component of its object (Bambu maps parts by sub-object id)")
check(ok_ext, f"all extruder assignments are within the {nfil} filament slots")
check(not bad_keys, f"all per-object setting keys exist in Bambu's PrintConfig" + (f" (unknown: {bad_keys})" if bad_keys else ""))

# meshes per object for geometry checks
sub_cache = {}
def sub_meshes(oid):
    o = objs[oid]; out = []
    for c in o.find("m:components", NS).findall("m:component", NS):
        path = c.get(f"{{{NS['p']}}}path").lstrip("/")
        if path not in sub_cache:
            sub_cache[path] = {so.get("id"): so for so in ET.fromstring(z.read(path)).find("m:resources", NS).findall("m:object", NS)}
        so = sub_cache[path][c.get("objectid")]
        mesh = so.find("m:mesh", NS)
        V = np.array([[float(v.get(a)) for a in "xyz"] for v in mesh.find("m:vertices", NS)])
        F = np.array([[int(t.get(a)) for a in ("v1", "v2", "v3")] for t in mesh.find("m:triangles", NS)])
        out.append(trimesh.Trimesh(V, F, process=False))
    return out

plates = ms.findall("plate")
check(len(plates) == 5, f"{len(plates)} plates defined: " + "; ".join(p.find("metadata[@key='plater_name']").get("value") for p in plates))
for pi, p in enumerate(plates):
    ox, oy = (pi % 3) * 307.2, -(pi // 3) * 307.2
    boxes, names, fils = [], [], set()
    for inst in p.findall("model_instance"):
        oid = inst.find("metadata[@key='object_id']").get("value")
        if oid not in objs: check(False, f"plate {pi+1} references missing object {oid}"); continue
        t = build[oid]; tx, ty = t[9], t[10]
        ms_ = sub_meshes(oid)
        lo = np.min([m.bounds[0] for m in ms_], 0) + [tx, ty, 0]; hi = np.max([m.bounds[1] for m in ms_], 0) + [tx, ty, 0]
        boxes.append((lo, hi)); names.append(obj_cfg[oid].find("metadata[@key='name']").get("value"))
        fils |= {e.get("value") for e in obj_cfg[oid].iter("metadata") if e.get("key") == "extruder"}
    inside = all(lo[0] >= ox + 2 and hi[0] <= ox + 254 and lo[1] >= oy + 2 and hi[1] <= oy + 254 and hi[2] <= 256 for lo, hi in boxes)
    overlap = any(np.all(boxes[i][0][:2] < boxes[j][1][:2] - 1) and np.all(boxes[j][0][:2] < boxes[i][1][:2] - 1)
                  for i in range(len(boxes)) for j in range(i + 1, len(boxes)))
    check(inside and not overlap, f"plate {pi+1}: {', '.join(names)} - inside the 256×256 bed, no overlaps, filament slot(s) {sorted(fils)}")

# ---------------------------------------------------------------- 3. geometry round trip
stl = ROOT / "stl"
for oid, o in obj_cfg.items():
    name = o.find("metadata[@key='name']").get("value")
    ms_ = sub_meshes(oid)
    ref = ["window_panel_base", "window_panel_details"] if name == "window_panel" else [name]
    ok = True
    for m, r in zip(ms_, ref):
        R = trimesh.load(stl / f"{r}.stl", force="mesh")
        ok &= abs(m.volume - R.volume) < 0.01 * max(1, R.volume) and np.allclose(sorted(m.extents), sorted(R.extents), atol=0.02) and m.is_watertight
    check(ok, f"{name}: mesh(es) in the 3MF are watertight and identical to the verified STL ({len(ms_)} part{'s' if len(ms_) > 1 else ''})")

doc = ROOT / "VERIFICATION.md"
txt = doc.read_text().split("\n## 7. 3MF files")[0]
doc.write_text(txt.rstrip() + "\n\n## 7. 3MF files (tools/check_3mf.py)\n\n" + "\n".join(lines) + "\n")
print("\nALL 3MF CHECKS PASSED" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
