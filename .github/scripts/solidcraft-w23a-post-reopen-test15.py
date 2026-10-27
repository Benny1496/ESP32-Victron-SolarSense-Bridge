#!/usr/bin/env python3
"""Test 15: W23a feature identity after save -> reopen -> further edit -> undo/redo -> save/reopen.

Not a W13/W14 2D drawing refresh test. Uses the immutable official drawings source.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import traceback

SOURCE_SHA = "ebafe07487df5cdd108e091db939de765645e5eb"
XY = {"Bore1": (20.0, 20.0), "Bore1New": (20.0, 20.0), "Bore2": (60.0, 50.0)}
CASES = {
    "replaced_hole_resized_after_reopen": {
        "initial_diameters": {"Bore1New": 10.0, "Bore2": 10.0},
        "new_hole_diameter": "bore1_d",
        "change_param": "bore1_d",
        "changed_diameters": {"Bore1New": 12.0, "Bore2": 10.0},
        "description": "Saved replacement Bore1New Ø10 -> Ø12",
    },
    "survivor_resized_to_match_replacement": {
        "initial_diameters": {"Bore1New": 12.0, "Bore2": 10.0},
        "new_hole_diameter": "12 mm",
        "change_param": "bore2_d",
        "changed_diameters": {"Bore1New": 12.0, "Bore2": 12.0},
        "description": "Saved replacement Ø12, surviving Bore2 Ø10 -> Ø12",
    },
}

def cmd(name, params=None):
    return {"command": name, "params": params or {}}

def execute(exe, source, args, log):
    argv = [str(exe), *map(str, args)]
    p = subprocess.run(argv, cwd=source, capture_output=True, encoding="utf-8",
                       errors="replace", text=True)
    log.write_text("COMMAND: " + " ".join(argv) + "\nEXIT: " + str(p.returncode) +
                   "\nSTDOUT:\n" + p.stdout + "\nSTDERR:\n" + p.stderr, encoding="utf-8")
    if p.returncode:
        raise RuntimeError(f"CLI exit {p.returncode}; log={log}")
    return p.stdout

def run_script(exe, source, out, name, commands, infile=None, savefile=None):
    path = out / (name + "-script.json")
    dest = out / (name + "-results.json")
    path.write_text(json.dumps({"commands": commands}, indent=2), encoding="utf-8")
    opts = ["run", path]
    if infile is not None: opts += ["--in", infile]
    opts += ["--results", "--json-out", dest]
    if savefile is not None: opts += ["--save", savefile]
    execute(exe, source, opts, out / (name + ".log"))
    replies = json.loads(dest.read_text(encoding="utf-8"))
    assert isinstance(replies, list) and len(replies) == len(commands), (
        f"{name}: incomplete CLI command results")
    return replies

def observe(commands):
    at = len(commands)
    commands.extend([cmd("document.inspect"), cmd("model.faces", {"body": "Plate"}),
                     cmd("model.edges", {"body": "Plate"}), cmd("inspect.measure")])
    return list(range(at, at + 4))

def approximate(got, wanted, tol=0.01):
    return isinstance(got, (int,float)) and math.isfinite(got) and abs(got-wanted) < tol

def oracle_geom(diameters):
    # 100 x 80 x 20 mm plate minus two exactly cylindrical, through bores.
    L,W,T = 100.,80.,20.
    a = 2*(L*W + L*T + W*T)
    v = L*W*T
    for diameter in diameters.values():
        v -= math.pi * diameter*diameter*T/4
        a += math.pi*diameter*T - math.pi*diameter*diameter/2
    return {"volume_mm3": v, "area_mm2": a}

def inspect(replies, indices, diameters, label):
    document, faces_result, edges_result, measured = [replies[i] for i in indices]
    assert faces_result.get("body") == edges_result.get("body") == "Plate", (
        f"{label}: inspected wrong body")
    relevant = [f for f in document.get("timeline", [])
                if f.get("name") in ("Stock", "Bore1", "Bore1New", "Bore2")]
    ids = {f["name"]: f["id"] for f in relevant}
    assert set(ids) == {"Stock", *diameters}, f"{label}: stale/incorrect feature set {ids}"
    assert len(ids) == len(relevant) == len(set(ids.values())), f"{label}: colliding feature IDs"
    assert all(f.get("error") in (None, "") for f in document.get("timeline", [])), (
        f"{label}: broken feature in timeline")
    cylinders = [f for f in faces_result.get("faces", []) if isinstance(f.get("cylinder"), dict)]
    assert len(cylinders) == len(diameters)*2, (
        f"{label}: expected two cylindrical B-rep halves per through hole, got {len(cylinders)}")
    refs = {}
    for name, d in diameters.items():
        x, y = XY[name]
        hits = []
        for face in cylinders:
            cyl = face["cylinder"]
            origin = cyl.get("origin", [])
            if (isinstance(origin, list) and len(origin)>=2
                and approximate(origin[0],x) and approximate(origin[1],y)
                and approximate(cyl.get("radius"),d/2)):
                hits.append(face)
        assert len(hits)==2, (
            f"{label}: expected two cylinder patches for {name} at {(x,y)}, radius {d/2}; "
            f"found {[(f.get('name'),f.get('cylinder')) for f in hits]}")
        names = sorted(f.get("name") for f in hits)
        assert all(isinstance(s,str) and s for s in names) and len(set(names))==2, (
            f"{label}: unnamed/duplicate {name} faces")
        assert all(f.get("exact") is True for f in hits), (
            f"{label}: {name} face history is not certified exact")
        edges = sorted(set(e["name"] for e in edges_result.get("edges", [])
                           if isinstance(e.get("name"),str)
                           and any(n in e["name"].split("|") for n in names)))
        assert len(edges)>=4, f"{label}: missing persistent boundary edges for {name}"
        refs[name] = {"faces":names, "edges":edges, "diameter":d, "exact":True}
    all_faces = [n for r in refs.values() for n in r["faces"]]
    assert len(set(all_faces)) == len(all_faces), f"{label}: bore faces reused across features"
    assert measured.get("body_count")==1 and not measured["bodies"][0].get("error"), (
        f"{label}: invalid solid measurement")
    expected = oracle_geom(diameters)
    for key in ("volume_mm3", "area_mm2"):
        got = measured["total"].get(key)
        want = expected[key]
        assert isinstance(got,(int,float)) and abs(got-want)<=max(0.001,abs(want)*0.001), (
            f"{label}: analytic {key} mismatch {got} != {want}")
    return {"ids":ids, "refs":refs, "measured":measured["total"],
            "analytical":expected}

def assert_stable(initial, later, bores, label):
    assert initial["ids"]["Stock"]==later["ids"]["Stock"], (
        f"{label}: stock identity changed")
    for bore in bores:
        assert initial["ids"][bore]==later["ids"][bore], (
            f"{label}: {bore} feature ID changed")
        for key in ("faces", "edges", "exact"):
            assert initial["refs"][bore][key]==later["refs"][bore][key], (
                f"{label}: {bore} {key} changed {initial['refs'][bore][key]} "
                f"-> {later['refs'][bore][key]}")

def check_no_reuse(old, newer, label):
    assert old["ids"]["Bore1"] != newer["ids"]["Bore1New"], (
        f"{label}: old Bore1 feature id was reused")
    for item in ("faces","edges"):
        old_values=set(old["refs"]["Bore1"][item])
        for bore in ("Bore1New","Bore2"):
            assert old_values.isdisjoint(newer["refs"][bore][item]), (
                f"{label}: deleted Bore1 {item} silently transferred to {bore}")

def scenario(exe, source, out, creation, name, info):
    pre = list(creation)
    p_baseline = observe(pre)
    pre.append(cmd("timeline.delete",{"feature":"Bore1"}))
    pre.append(cmd("solid.hole",{"name":"Bore1New","type":"simple",
               "position":[20,20,20],"direction":[0,0,-1],
               "diameter":info["new_hole_diameter"]}))
    p_replaced = observe(pre)
    origin_file=out/(name+"-origin.solidcraft")
    rs=run_script(exe,source,out,name+"-prepare",pre,savefile=origin_file)
    old=inspect(rs,p_baseline,{"Bore1":10.0,"Bore2":10.0},name+"/original")
    prepared=inspect(rs,p_replaced,info["initial_diameters"],name+"/replacement")
    assert_stable(old,prepared,["Bore2"],name+"/prepare")
    check_no_reuse(old,prepared,name+"/prepare")

    # Source design is first saved and OPENED IN A NEW CLI PROCESS.
    seq=[];p_before=observe(seq)
    seq.append(cmd("parameters.change",
              {"name":info["change_param"],"expression":"12 mm"}))
    p_edited=observe(seq)
    seq.append(cmd("edit.undo"))
    p_undo=observe(seq)
    seq.append(cmd("edit.redo"))
    p_redo=observe(seq)
    changed_file=out/(name+"-final.solidcraft")
    rr=run_script(exe,source,out,name+"-second-process",seq,
                  infile=origin_file,savefile=changed_file)
    loaded=inspect(rr,p_before,info["initial_diameters"],name+"/loaded")
    edited=inspect(rr,p_edited,info["changed_diameters"],name+"/edited")
    undone=inspect(rr,p_undo,info["initial_diameters"],name+"/undone")
    redone=inspect(rr,p_redo,info["changed_diameters"],name+"/redone")
    for label,item in (("loaded",loaded),("edited",edited),("undone",undone),("redone",redone)):
        assert_stable(prepared,item,["Bore2","Bore1New"],name+"/"+label)
        check_no_reuse(old,item,name+"/"+label)
    assert abs(loaded["measured"]["volume_mm3"]-edited["measured"]["volume_mm3"])>100, (
        f"{name}: parameter edit did not actually change geometry")
    assert abs(loaded["measured"]["volume_mm3"]-undone["measured"]["volume_mm3"])<0.001, (
        f"{name}: undo did not restore original geometry")
    assert abs(edited["measured"]["volume_mm3"]-redone["measured"]["volume_mm3"])<0.001, (
        f"{name}: redo did not reapply changed geometry")

    # Verify a second separate save/reopen; no stale Bore1 references.
    seq_final=[];p_final=observe(seq_final)
    rf=run_script(exe,source,out,name+"-third-process",seq_final,infile=changed_file)
    persisted=inspect(rf,p_final,info["changed_diameters"],name+"/final_reopen")
    assert_stable(prepared,persisted,["Bore2","Bore1New"],name+"/final_reopen")
    check_no_reuse(old,persisted,name+"/final_reopen")
    return {"original":old,"prepared":prepared,"loaded":loaded,
            "edited":edited,"undone":undone,"redone":redone,"final_reopen":persisted}

def main():
    p=argparse.ArgumentParser()
    for key in ("--cli","--source","--out"):p.add_argument(key,required=True)
    a=p.parse_args()
    exe=Path(a.cli).resolve(); source=Path(a.source).resolve(); out=Path(a.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert exe.is_file(),f"Missing SolidCraft CLI {exe}"
    recipe=source/"tests/oracle/84-plate-two-bores/recipe.json"
    recipe_data=json.loads(execute(exe,source,["recipe",recipe],out/"recipe.log"))
    commands=recipe_data["commands"]
    assert sum(c.get("command")=="solid.hole" for c in commands)==2
    summary={"source":SOURCE_SHA,"scope":"3D design only; W13/W14 drawing APIs NOT tested",
             "scenarios":{},"failed":0}
    for name,info in CASES.items():
        try:
            states=scenario(exe,source,out,commands,name,info)
            summary["scenarios"][name]={"status":"PASS","states":states}
            print(f"PASS {name}: source save/reopen, further edit, exact IDs/faces/edges, "
                  f"undo/redo, final reopen",flush=True)
        except Exception as exc:
            summary["failed"]+=1
            summary["scenarios"][name]={"status":"FAIL","error":str(exc),"traceback":traceback.format_exc()}
            print(f"FAIL {name}: {exc}",file=sys.stderr,flush=True)
    summary["status"]="PASS" if summary["failed"]==0 else "FAIL"
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"W23A_POST_REOPEN_EDIT_CASES={len(CASES)} FAILED_CHECKS={summary['failed']}",flush=True)
    return 0 if summary["failed"]==0 else 1

if __name__=="__main__":
    sys.exit(main())
