#!/usr/bin/env python3
"""W23a Test 14: delete a bore; rebuild it at the SAME location; never reuse old references.

This test is for the SolidCraft 3D source design only, NOT the W13/W14 drawing resolver.
Pin is official tangency-labs/solidcraft drawings as of 2026-10-27.
"""
import argparse
import json
import math
import pathlib
import subprocess
import sys
import traceback

SOURCE = "ebafe07487df5cdd108e091db939de765645e5eb"
BORE1 = (20.0, 20.0)
BORE2 = (60.0, 50.0)
VARIANTS = {
    "identical_replacement": {"diameter": "bore1_d", "radius": 5.0,
                              "oracle": "84-plate-two-bores"},
    "different_diameter_replacement": {"diameter": "12 mm", "radius": 6.0,
                                       "oracle": "86-plate-first-bore-12"},
}

def cmd(name, params=None):
    return {"command": name, "params": params or {}}

def cli(argv, cwd, log):
    process = subprocess.run([str(x) for x in argv], cwd=cwd, encoding="utf-8",
                             errors="replace", text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    log.write_text("COMMAND: " + " ".join(str(x) for x in argv) + "\n"
                   + "EXIT: " + str(process.returncode) + "\nSTDOUT:\n"
                   + process.stdout + "\nSTDERR:\n" + process.stderr,
                   encoding="utf-8")
    if process.returncode != 0:
        raise RuntimeError(f"CLI exit {process.returncode}, see {log}")
    return process.stdout

def close_number(actual, target, absolute=0.01):
    return isinstance(actual, (float, int)) and math.isfinite(actual) and abs(actual-target) <= absolute

def identify_bore(faces, edges, x, y, radius, label):
    cylinders = [f for f in faces if isinstance(f.get("cylinder"), dict)]
    group = []
    for f in cylinders:
        c = f["cylinder"]
        org = c.get("origin")
        if (isinstance(org, list) and len(org) >= 2
            and close_number(org[0], x) and close_number(org[1], y)
            and close_number(c.get("radius"), radius)):
            group.append(f)
    assert len(group) == 2, (f"{label}: expected two B-rep cylindrical patches "
                             f"at ({x},{y}) radius {radius}; got {[f.get('name') for f in group]}")
    assert all(f.get("exact") is True for f in group), (
        f"{label}: unverified face names: {[(f.get('name'), f.get('exact')) for f in group]}")
    names = sorted(f.get("name") for f in group)
    assert len(set(names)) == 2 and all(isinstance(n, str) and n for n in names), (
        f"{label}: invalid / duplicate half-cylinder name {names}")
    enames = sorted(set(e["name"] for e in edges if isinstance(e.get("name"), str)
                        and any(n in e["name"].split("|") for n in names)))
    assert len(enames) >= 4, f"{label}: missing boundary edges for {names}: {enames}"
    return {"faces": names, "edges": enames, "radius": radius, "exact": True}

def snapshot(results, indices, active_bores, oracle, label):
    doc, ff, ee, measurement = [results[i] for i in indices]
    assert ff.get("body") == "Plate" and ee.get("body") == "Plate", f"{label}: wrong body"
    names = ("Stock", "Bore1", "Bore2", "Bore1New")
    features = [v for v in doc.get("timeline", []) if v.get("name") in names]
    ids = {v["name"]: v["id"] for v in features}
    assert len(ids) == len(features) and len(set(ids.values())) == len(ids), (
        f"{label}: duplicate feature IDs or names")
    assert set(ids) == {"Stock", *active_bores}, (
        f"{label}: expected Stock + {active_bores}, got {ids}")
    assert all(v.get("error") in (None, "") for v in doc.get("timeline", [])), (
        f"{label}: timeline feature error")
    assert measurement.get("body_count") == 1, f"{label}: wrong body count"
    assert len(measurement.get("bodies", [])) == 1 and not measurement["bodies"][0].get("error"), (
        f"{label}: B-rep measurement error")
    for metric in ("volume_mm3", "area_mm2"):
        want = oracle[metric]
        got = measurement["total"].get(metric)
        assert isinstance(got, (int,float)) and abs(got-want) <= max(0.001, abs(want)*0.001), (
            f"{label}: {metric} {got} vs analytic {want}")
    fs = ff.get("faces", [])
    es = ee.get("edges", [])
    refs = {}
    specs = {"Bore1": (*BORE1, 5.0), "Bore2": (*BORE2, 5.0)}
    if "Bore1New" in active_bores:
        specs["Bore1New"] = (*BORE1, active_bores["Bore1New"])
    for bore, (x,y,radius) in specs.items():
        if bore in active_bores:
            refs[bore] = identify_bore(fs,es,x,y,radius,label+"/"+bore)
    cylinder_count = sum(isinstance(f.get("cylinder"),dict) for f in fs)
    assert cylinder_count == 2*len(refs), (
        f"{label}: unexpected cylinder patch count {cylinder_count} for {len(refs)} bores")
    all_faces = [face for bore in refs.values() for face in bore["faces"]]
    assert len(set(all_faces)) == len(all_faces), f"{label}: overlapping bore face references"
    return {"feature_ids": ids, "references": refs, "volume_mm3": measurement["total"]["volume_mm3"],
            "area_mm2": measurement["total"]["area_mm2"]}

def require_same(label, earlier, later, bore):
    assert earlier["feature_ids"][bore] == later["feature_ids"][bore], (
        f"{label}: {bore} feature ID changed")
    for key in ("faces","edges","exact"):
        assert earlier["references"][bore][key] == later["references"][bore][key], (
            f"{label}: {bore} {key} changed: {earlier['references'][bore][key]} "
            f"-> {later['references'][bore][key]}")

def no_reuse(label, old, new):
    assert old["feature_ids"]["Bore1"] != new["feature_ids"]["Bore1New"], (
        f"{label}: deleted feature ID reused")
    previous = set(old["references"]["Bore1"]["faces"])
    latest = set(new["references"]["Bore1New"]["faces"])
    assert previous.isdisjoint(latest), (
        f"{label}: old Bore1 cylinder face names reassigned to new hole")
    assert set(old["references"]["Bore1"]["edges"]).isdisjoint(
        set(new["references"]["Bore1New"]["edges"])), (
        f"{label}: old Bore1 boundary edge names reused on new hole")

def run_one(opts, commands, variant, info, oracles):
    source, exe, out = opts
    stages = {}
    seq = list(commands)
    def observe(stage):
        start = len(seq)
        seq.extend([cmd("document.inspect"),cmd("model.faces",{"body":"Plate"}),
                    cmd("model.edges",{"body":"Plate"}),cmd("inspect.measure")])
        stages[stage] = list(range(start, start+4))
    observe("baseline")
    seq.append(cmd("timeline.delete",{"feature":"Bore1"}))
    observe("deleted")
    seq.append(cmd("solid.hole",{
        "name":"Bore1New", "type":"simple",
        "position":[20,20,20],"direction":[0,0,-1],
        "diameter":info["diameter"]}))
    observe("recreated")
    seq.append(cmd("edit.undo"))
    observe("undo_recreate")
    seq.append(cmd("edit.undo"))
    observe("undo_delete")
    seq.append(cmd("edit.redo"))
    observe("redo_delete")
    seq.append(cmd("edit.redo"))
    observe("redo_recreate")

    script = out / (variant+"-script.json")
    saved = out / (variant+".solidcraft")
    results_path = out / (variant+"-results.json")
    script.write_text(json.dumps({"commands":seq},indent=2),encoding="utf-8")
    cli([exe,"run",script,"--results","--json-out",results_path,"--save",saved],
        source,out/(variant+".log"))
    responses=json.loads(results_path.read_text(encoding="utf-8"))
    assert len(responses)==len(seq),f"{variant}: incomplete responses"
    base={"Bore1":5.0,"Bore2":5.0}
    deleted={"Bore2":5.0}
    recreated={"Bore2":5.0,"Bore1New":info["radius"]}
    expected = {
        "baseline": (base,oracles["baseline"]),
        "deleted": (deleted,oracles["deleted"]),
        "recreated": (recreated,oracles[info["oracle"]]),
        "undo_recreate": (deleted,oracles["deleted"]),
        "undo_delete": (base,oracles["baseline"]),
        "redo_delete": (deleted,oracles["deleted"]),
        "redo_recreate": (recreated,oracles[info["oracle"]]),
    }
    states={name:snapshot(responses,stages[name],act,oracle,variant+"/"+name)
            for name,(act,oracle) in expected.items()}
    original=states["baseline"]
    for stage in states:
        if stage!="baseline":
            require_same(variant+"/"+stage,original,states[stage],"Bore2")
            assert original["feature_ids"]["Stock"]==states[stage]["feature_ids"]["Stock"],(
                f"{variant}/{stage}: Stock ID changed")
    for stage in ("deleted","undo_recreate","redo_delete"):
        assert "Bore1" not in states[stage]["feature_ids"],f"{variant}/{stage}: Bore1 still present"
    require_same(variant+"/undo_delete",original,states["undo_delete"],"Bore1")
    require_same(variant+"/redo_recreate",states["recreated"],states["redo_recreate"],"Bore1New")
    no_reuse(variant+"/recreated",original,states["recreated"])
    no_reuse(variant+"/redo_recreate",original,states["redo_recreate"])

    # A separate CLI process opens the saved final model and inspects its independent history.
    script_open=out/(variant+"-reopen-script.json")
    script_open.write_text(json.dumps({"commands":[cmd("document.inspect"),
        cmd("model.faces",{"body":"Plate"}),cmd("model.edges",{"body":"Plate"}),
        cmd("inspect.measure")]},indent=2),encoding="utf-8")
    output_open=out/(variant+"-reopen-results.json")
    cli([exe,"run",script_open,"--in",saved,"--results","--json-out",output_open],
        source,out/(variant+"-reopen.log"))
    reopened=json.loads(output_open.read_text(encoding="utf-8"))
    assert len(reopened)==4
    opened=snapshot(reopened,[0,1,2,3],recreated,oracles[info["oracle"]],variant+"/reopened")
    for bore in ("Bore2","Bore1New"):
        require_same(variant+"/reopened",states["redo_recreate"],opened,bore)
    no_reuse(variant+"/reopened",original,opened)
    states["reopened"]=opened
    return states

def main():
    parser=argparse.ArgumentParser()
    for key in ("--cli","--source","--out"): parser.add_argument(key,required=True)
    a=parser.parse_args()
    exe=pathlib.Path(a.cli).resolve()
    source=pathlib.Path(a.source).resolve()
    out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    assert exe.is_file(),f"Missing SolidCraft CLI: {exe}"
    recipe=source/"tests/oracle/84-plate-two-bores/recipe.json"
    commands=json.loads(cli([exe,"recipe",recipe],source,out/"recipe.log"))["commands"]
    assert sum(x["command"]=="solid.hole" for x in commands)==2
    oracles={key:json.loads((source/"tests/oracle"/path/"expected.json").read_text(encoding="utf-8"))
             for key,path in {
                "baseline":"84-plate-two-bores",
                "deleted":"87-plate-bore1-deleted",
                "84-plate-two-bores":"84-plate-two-bores",
                "86-plate-first-bore-12":"86-plate-first-bore-12",
             }.items()}
    summary={"source":f"tangency-labs/solidcraft@{SOURCE}","kind":"3D design B-rep lifecycle, NOT a W13/W14 drawing test",
             "scenarios":{},"failed":0}
    for key,info in VARIANTS.items():
        try:
            states=run_one((source,exe,out),commands,key,info,oracles)
            summary["scenarios"][key]={"status":"PASS","states":states}
            print(f"PASS {key}: delete, new hole at same XY, no reference reuse, 2x undo/redo, saved/reopened",flush=True)
        except Exception as e:
            summary["failed"]+=1
            summary["scenarios"][key]={"status":"FAIL","error":str(e),"traceback":traceback.format_exc()}
            print(f"FAIL {key}: {e}",file=sys.stderr,flush=True)
    summary["status"]="PASS" if summary["failed"]==0 else "FAIL"
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"W23A_REPLACE_CASES={len(VARIANTS)} FAILED_CHECKS={summary['failed']}",flush=True)
    return 0 if summary["failed"]==0 else 1

if __name__=="__main__":
    sys.exit(main())
