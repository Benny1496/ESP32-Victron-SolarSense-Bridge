#!/usr/bin/env python3
"""W23a regression: persistent named bore faces and boundary edges (not W13/W14)."""
import argparse
import json
import math
import pathlib
import subprocess
import sys
import traceback

SOURCE_SHA = "ebafe07487df5cdd108e091db939de765645e5eb"
XY = {"Bore1": (20.0, 20.0), "Bore2": (60.0, 50.0)}
SPECS = {
    "width_80_to_100": ({"command": "parameters.change", "params": {"name": "width", "expression": "100 mm"}}, {"Bore1": 5.0, "Bore2": 5.0}, "85-plate-width-100"),
    "bore1_10_to_12": ({"command": "parameters.change", "params": {"name": "bore1_d", "expression": "12 mm"}}, {"Bore1": 6.0, "Bore2": 5.0}, "86-plate-first-bore-12"),
    "delete_bore1": ({"command": "timeline.delete", "params": {"feature": "Bore1"}}, {"Bore2": 5.0}, "87-plate-bore1-deleted"),
}

def call(argv, cwd, logfile):
    p = subprocess.run([str(v) for v in argv], cwd=str(cwd), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       encoding="utf-8", errors="replace")
    logfile.write_text("COMMAND: " + " ".join(map(str, argv)) + "\nEXIT: " + str(p.returncode)
                       + "\nSTDOUT:\n" + p.stdout + "\nSTDERR:\n" + p.stderr,
                       encoding="utf-8")
    if p.returncode:
        raise RuntimeError(f"CLI exit={p.returncode}, log={logfile}")
    return p.stdout

def command(name, params=None):
    return {"command": name, "params": params or {}}

def near(a, b, tol=0.01):
    return isinstance(a, (float, int)) and math.isfinite(a) and abs(a-b) <= tol

def inspect_faces_and_edges(faces_result, edges_result, radii, label):
    assert faces_result.get("body") == "Plate", f"{label}: unexpected body (faces)"
    assert edges_result.get("body") == "Plate", f"{label}: unexpected body (edges)"
    faces = faces_result["faces"]
    edges = edges_result["edges"]
    assert isinstance(faces, list) and isinstance(edges, list), f"{label}: invalid response"
    cylinders = [f for f in faces if isinstance(f.get("cylinder"), dict)]
    assert len(cylinders) == len(radii), f"{label}: {len(cylinders)} cylinders, expected {len(radii)}"
    found = {}
    for bore, rad in radii.items():
        x, y = XY[bore]
        matches = [f for f in cylinders
                   if near(f["cylinder"].get("radius"), rad)
                   and isinstance(f["cylinder"].get("origin"), list)
                   and len(f["cylinder"]["origin"]) >= 2
                   and near(f["cylinder"]["origin"][0], x)
                   and near(f["cylinder"]["origin"][1], y)]
        assert len(matches) == 1, f"{label}: {bore} expected one radius {rad} at {(x,y)}, got {matches}"
        f = matches[0]
        name = f.get("name")
        assert isinstance(name, str) and name, f"{label}: unnamed cylindrical face of {bore}"
        assert f.get("exact") is True, (f"{label}: {bore} face {name} has unverified geometric naming, not reliable history")
        edge_names = sorted({e["name"] for e in edges
                             if isinstance(e.get("name"), str) and name in e["name"].split("|")})
        assert edge_names, f"{label}: no named boundary edges for {bore} ({name})"
        found[bore] = {"face": name, "exact": f.get("exact") is True,
                       "edges": edge_names, "radius": f["cylinder"]["radius"],
                       "index": f.get("index")}
    assert len(set(p["face"] for p in found.values())) == len(found), f"{label}: bore faces aliased"
    return found

def inspect_state(replies, positions, label, radii, expected):
    timeline, face_data, edge_data, measured = (replies[i] for i in positions)
    ids = {f.get("name"): f.get("id") for f in timeline.get("timeline", [])
           if f.get("name") in ("Stock", "Bore1", "Bore2")}
    assert len(ids) == len(set(ids.values())), f"{label}: feature ID collision"
    assert set(ids) == {"Stock", *radii}, f"{label}: unexpected feature IDs {ids}"
    assert measured.get("body_count") == 1, f"{label}: not exactly one body"
    for key in ("volume_mm3", "area_mm2"):
        got = measured["total"].get(key)
        want = expected[key]
        assert isinstance(got, (int, float)) and abs(got-want) <= max(0.001, abs(want)*1e-3), (
            f"{label}: {key} got {got}, expected {want}")
    geom = inspect_faces_and_edges(face_data, edge_data, radii, label)
    return {"ids": ids, "bore_refs": geom,
            "volume_mm3": measured["total"]["volume_mm3"],
            "area_mm2": measured["total"]["area_mm2"]}

def verify_refs(label, before, current, surviving):
    for bore in surviving:
        original = before["bore_refs"][bore]
        latest = current["bore_refs"][bore]
        assert original["face"] == latest["face"], (
            f"{label}: {bore} persistent face changed {original['face']} => {latest['face']}")
        assert set(original["edges"]) == set(latest["edges"]), (
            f"{label}: {bore} edge names changed {original['edges']} => {latest['edges']}")
        assert original["exact"] == latest["exact"], f"{label}: {bore} history verification changed"
        assert before["ids"][bore] == current["ids"][bore], f"{label}: {bore} feature ID changed"
    for disappeared in set(before["bore_refs"])-set(surviving):
        forbidden = before["bore_refs"][disappeared]["face"]
        assert all(info["face"] != forbidden for info in current["bore_refs"].values()), (
            f"{label}: deleted {disappeared} face silently reused")
        assert disappeared not in current["ids"], f"{label}: deleted feature still present"
    assert before["ids"]["Stock"] == current["ids"]["Stock"], f"{label}: stock feature ID changed"

def main():
    p=argparse.ArgumentParser()
    for arg in ("--cli","--source","--out"): p.add_argument(arg, required=True)
    a=p.parse_args()
    exe=pathlib.Path(a.cli).resolve(); source=pathlib.Path(a.source).resolve()
    output=pathlib.Path(a.out).resolve(); output.mkdir(parents=True, exist_ok=True)
    recipe=source/"tests/oracle/84-plate-two-bores/recipe.json"
    base_expected=json.loads((source/"tests/oracle/84-plate-two-bores/expected.json").read_text(encoding="utf-8"))
    raw=call([exe,"recipe",recipe],source,output/"recipe.log")
    creation=json.loads(raw)["commands"]
    assert sum(step.get("command") == "solid.hole" for step in creation)==2
    result={"purpose":"W23a B-rep named faces/edges, edit, undo/redo, save and reopen; NOT Drawing W13/W14",
            "source":f"tangency-labs/solidcraft@{SOURCE_SHA}", "cases":{}, "failed":0}
    for scenario,(edit,radii,oracle_folder) in SPECS.items():
        expected=json.loads((source/"tests/oracle"/oracle_folder/"expected.json").read_text(encoding="utf-8"))
        steps=list(creation); positions=[]
        for op in (command("document.inspect"),command("model.faces",{"body":"Plate"}),
                   command("model.edges",{"body":"Plate"}),command("inspect.measure"),
                   edit,
                   command("document.inspect"),command("model.faces",{"body":"Plate"}),
                   command("model.edges",{"body":"Plate"}),command("inspect.measure"),
                   command("edit.undo"),
                   command("document.inspect"),command("model.faces",{"body":"Plate"}),
                   command("model.edges",{"body":"Plate"}),command("inspect.measure"),
                   command("edit.redo"),
                   command("document.inspect"),command("model.faces",{"body":"Plate"}),
                   command("model.edges",{"body":"Plate"}),command("inspect.measure")):
            steps.append(op)
        start=len(creation)
        positions=[list(range(start, start+4)),
                   list(range(start+5, start+9)),
                   list(range(start+10,start+14)),
                   list(range(start+15,start+19))]
        saved=output/(scenario+".solidcraft")
        script=output/(scenario+"-script.json")
        script.write_text(json.dumps({"commands":steps},ensure_ascii=False,indent=2),encoding="utf-8")
        responses_path=output/(scenario+"-results.json")
        try:
            call([exe,"run",script,"--results","--json-out",responses_path,"--save",saved],source,output/(scenario+".log"))
            responses=json.loads(responses_path.read_text(encoding="utf-8"))
            assert len(responses)==len(steps),f"{scenario}: unexpected result count"
            before=inspect_state(responses,positions[0],scenario+"/before",{"Bore1":5.0,"Bore2":5.0},base_expected)
            after=inspect_state(responses,positions[1],scenario+"/after",radii,expected)
            undone=inspect_state(responses,positions[2],scenario+"/undo",{"Bore1":5.0,"Bore2":5.0},base_expected)
            redone=inspect_state(responses,positions[3],scenario+"/redo",radii,expected)
            assert before["bore_refs"]["Bore1"]["face"] != before["bore_refs"]["Bore2"]["face"]
            verify_refs(scenario+"/edit",before,after,set(radii))
            verify_refs(scenario+"/undo",before,undone,{"Bore1","Bore2"})
            verify_refs(scenario+"/redo",before,redone,set(radii))
            # Saving and reloading must never silently transfer the removed Bore1 reference.
            reopen_script=output/(scenario+"-reopen-script.json")
            reopen_script.write_text(json.dumps({"commands":[command("document.inspect"),
                        command("model.faces",{"body":"Plate"}),command("model.edges",{"body":"Plate"}),
                        command("inspect.measure")]},indent=2),encoding="utf-8")
            reopened_results=output/(scenario+"-reopen-results.json")
            call([exe,"run",reopen_script,"--in",saved,"--results","--json-out",reopened_results],
                 source,output/(scenario+"-reopen.log"))
            reopened=json.loads(reopened_results.read_text(encoding="utf-8"))
            assert len(reopened)==4
            persisted=inspect_state(reopened,[0,1,2,3],scenario+"/reopen",radii,expected)
            verify_refs(scenario+"/reopen",before,persisted,set(radii))
            assert {k:v["face"] for k,v in redone["bore_refs"].items()} == {
                k:v["face"] for k,v in persisted["bore_refs"].items()},f"{scenario}: post-reopen face mismatch"
            result["cases"][scenario]={"status":"PASS",
                 "before":before,"edited":after,"undo":undone,"redo":redone,"reopened":persisted}
            print(f"PASS {scenario}: named face/edge identities, geometry, undo/redo and save/reopen",flush=True)
        except Exception as e:
            result["failed"]+=1
            result["cases"][scenario]={"status":"FAIL","error":str(e),"traceback":traceback.format_exc()}
            print(f"FAIL {scenario}: {e}",file=sys.stderr,flush=True)
    result["status"]="PASS" if result["failed"]==0 else "FAIL"
    (output/"summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"W23A_PERSISTENT_REFS_CASES={len(SPECS)} FAILED_CHECKS={result['failed']}",flush=True)
    return 0 if result["failed"]==0 else 1

if __name__=="__main__":
    sys.exit(main())
