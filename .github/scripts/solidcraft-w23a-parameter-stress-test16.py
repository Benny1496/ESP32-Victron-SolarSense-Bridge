#!/usr/bin/env python3
"""Stress test for W23a persistent source references under repeated 3D parameter edits.

Reusable component of one-build/many-tests CI. It does NOT test W13/W14 drawing update.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import traceback

def helper(source_path):
    spec = importlib.util.spec_from_file_location("w23a_test15_helpers", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load test helpers: {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def change(name, diameter):
    return (name, diameter)

MATRIX = {
    "bore1_six_toggles": [change("bore1_d", d) for d in (12,10,12,10,12,10)],
    "bore2_six_toggles": [change("bore2_d", d) for d in (12,10,12,10,12,10)],
    "expand_both_1_then_2": [change("bore1_d",12),change("bore2_d",12)],
    "expand_both_2_then_1": [change("bore2_d",12),change("bore1_d",12)],
    "interleaved_four_changes": [change("bore1_d",12),change("bore2_d",12),
                                  change("bore1_d",10),change("bore2_d",10)],
    "zigzag_six_changes": [change("bore1_d",12),change("bore2_d",12),
                           change("bore1_d",10),change("bore2_d",10),
                           change("bore2_d",12),change("bore1_d",12)],
}

def run_case(m, exe, source, out, create, label, operations):
    source_commands=list(create)
    visits=[]
    diameters={"Bore1":10.0,"Bore2":10.0}

    def observe(tag):
        indices=m.observe(source_commands)
        visits.append((tag, indices, dict(diameters)))

    observe("baseline")
    history=[]
    for ix,(name,d) in enumerate(operations,1):
        before=dict(diameters)
        bname={"bore1_d":"Bore1","bore2_d":"Bore2"}[name]
        assert before[bname]!=float(d),f"{label}: no-op at edit {ix}"
        source_commands.append(m.cmd("parameters.change",
                  {"name":name,"expression":f"{d} mm"}))
        diameters[bname]=float(d)
        history.append((before,dict(diameters)))
        observe(f"edit_{ix}")
    for ix in range(len(history),0,-1):
        source_commands.append(m.cmd("edit.undo"))
        diameters=dict(history[ix-1][0])
        observe(f"undo_{ix}")
    for ix in range(1,len(history)+1):
        source_commands.append(m.cmd("edit.redo"))
        diameters=dict(history[ix-1][1])
        observe(f"redo_{ix}")

    final_file=out/(label+"-saved.solidcraft")
    replies=m.run_script(exe,source,out,label+"-main",source_commands,savefile=final_file)
    states={}
    for tag,indices,expect in visits:
        states[tag]=m.inspect(replies,indices,expect,label+"/"+tag)
    origin=states["baseline"]
    for tag,state in states.items():
        m.assert_stable(origin,state,("Bore1","Bore2"),label+"/"+tag)
    for ix in range(1,len(history)+1):
        before=states[f"edit_{ix}"]["measured"]["volume_mm3"]
        undostate=states[f"undo_{ix}"]["measured"]["volume_mm3"]
        undo_expected=m.oracle_geom(history[ix-1][0])["volume_mm3"]
        assert abs(undostate-undo_expected)<=max(0.001,undo_expected*0.001), (
            f"{label}: undo_{ix} did not restore analytical previous volume")
        redo_actual=states[f"redo_{ix}"]["measured"]["volume_mm3"]
        redo_expected=m.oracle_geom(history[ix-1][1])["volume_mm3"]
        assert abs(redo_actual-redo_expected)<=max(0.001,redo_expected*0.001), (
            f"{label}: redo_{ix} did not recover expected volume")

    opened_commands=[]
    snapshot_index=m.observe(opened_commands)
    opened_replies=m.run_script(exe,source,out,label+"-reopened",opened_commands,infile=final_file)
    after_reopen=m.inspect(opened_replies,snapshot_index,diameters,label+"/reopened")
    m.assert_stable(origin,after_reopen,("Bore1","Bore2"),label+"/reopened")
    states["reopened"]=after_reopen
    return {"status":"PASS","steps":len(operations),"observations":len(visits)+1,
            "final_diameters":diameters,
            "persistent_ids":origin["ids"],
            "persistent_faces":{name:val["faces"] for name,val in origin["refs"].items()},
            "first_geometry":origin["measured"],
            "final_geometry":after_reopen["measured"],
            "sequence":operations}

def main():
    parser=argparse.ArgumentParser()
    for item in ("--cli","--source","--out"):
        parser.add_argument(item,required=True)
    args=parser.parse_args()
    exe=Path(args.cli).resolve();source=Path(args.source).resolve()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    m=helper(Path(__file__).parent/"solidcraft-w23a-post-reopen-test15.py")
    assert exe.is_file(),f"Missing SolidCraft CLI: {exe}"
    recipe=source/"tests/oracle/84-plate-two-bores/recipe.json"
    data=json.loads(m.execute(exe,source,["recipe",recipe],out/"recipe.log"))
    commands=data["commands"]
    assert sum(x.get("command")=="solid.hole" for x in commands)==2
    report={"kind":"source-model param sequence stress, not drawing refresh",
            "source":"tangency-labs/solidcraft@ebafe07487df5cdd108e091db939de765645e5eb",
            "scenarios":{},"failed":0}
    for label,ops in MATRIX.items():
        try:
            record=run_case(m,exe,source,out,commands,label,ops)
            report["scenarios"][label]=record
            print(f"PASS {label}: {len(ops)} edits, undo/redo, exact faces/edges, reopen",flush=True)
        except Exception as error:
            report["failed"]+=1
            report["scenarios"][label]={"status":"FAIL","error":str(error),
                                          "traceback":traceback.format_exc()}
            print(f"FAIL {label}: {error}",file=sys.stderr,flush=True)
    report["status"]="PASS" if report["failed"]==0 else "FAIL"
    (out/"summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"W23A_STRESS_CASES={len(MATRIX)} FAILED_CHECKS={report['failed']}",flush=True)
    return 0 if not report["failed"] else 1

if __name__=="__main__":
    sys.exit(main())
