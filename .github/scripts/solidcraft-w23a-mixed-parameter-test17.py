#!/usr/bin/env python3
"""Test 17: twelve combined length/width/bore diameter editing regressions.

One W23a plate, genuine modifications, full undo + redo histories, persistent
verified face names and edge names, analytic volume/area, save/reopen.
This only tests the 3D model, NOT 2D drawing W13/W14 refresh.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys
import traceback

SOURCE_SHA = "ebafe07487df5cdd108e091db939de765645e5eb"
INITIAL = {"length":100.0, "width":80.0, "bore1_d":10.0, "bore2_d":10.0}
XY = {"Bore1":(20.0,20.0), "Bore2":(60.0,50.0)}
MATRIX = {
    "width_and_bore1": [("width",100),("bore1_d",12)],
    "length_and_bore2": [("length",120),("bore2_d",12)],
    "both_dims_then_bores": [("width",100),("length",120),("bore1_d",12),("bore2_d",12)],
    "bores_then_both_dims": [("bore2_d",12),("bore1_d",12),("length",120),("width",100)],
    "alternating_width_bore1": [("width",100),("bore1_d",12),("width",80),
                                 ("bore1_d",10),("width",100),("bore1_d",12)],
    "alternating_length_bore2": [("length",120),("bore2_d",12),("length",100),
                                  ("bore2_d",10),("length",120),("bore2_d",12)],
    "size_flip_both_bores": [("width",100),("bore1_d",12),("bore2_d",12),
                              ("width",80),("bore1_d",10),("bore2_d",10)],
    "length_flip_both_bores": [("length",120),("bore2_d",12),("bore1_d",12),
                                ("length",100),("bore2_d",10),("bore1_d",10)],
    "dimensions_mix_six": [("width",100),("length",120),("bore1_d",12),
                             ("width",80),("bore2_d",12),("length",100)],
    "all_six_round_trip": [("bore1_d",12),("length",120),("width",100),
                            ("bore2_d",12),("length",100),("width",80)],
    "width_flip_bore2": [("width",100),("bore2_d",12),("width",80),("bore2_d",10)],
    "length_flip_bore1": [("length",120),("bore1_d",12),("length",100),("bore1_d",10)],
}

def shared():
    location=Path(__file__).with_name("solidcraft-w23a-post-reopen-test15.py")
    spec=importlib.util.spec_from_file_location("w23a_test15_ref",location)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load reference helpers {location}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def geometry_oracle(st):
    length=st["length"]; width=st["width"]; height=20.0
    v=length*width*height
    a=2*(length*width + length*height + width*height)
    for key in ("bore1_d","bore2_d"):
        d=st[key]
        v-=math.pi*d*d*height/4
        a+=math.pi*d*height-math.pi*d*d/2
    return {"volume_mm3":v,"area_mm2":a}

def inspect_dynamic(replies,indices,st,label,helper):
    doc,face_result,edge_result,measure=(replies[i] for i in indices)
    assert face_result.get("body")=="Plate" and edge_result.get("body")=="Plate", (
        f"{label}: wrong solid body")
    ids={}
    for row in doc.get("timeline",[]):
        if row.get("name") in ("Stock","Bore1","Bore2"):
            assert row["name"] not in ids, f"{label}: duplicate feature name {row['name']}"
            ids[row["name"]]=row.get("id")
    assert set(ids)=={"Stock","Bore1","Bore2"}, f"{label}: feature timeline {ids}"
    assert len(set(ids.values()))==3 and all(ids.values()), (
        f"{label}: invalid or colliding feature identifiers")
    assert all(r.get("error") in (None,"") for r in doc.get("timeline",[])), (
        f"{label}: timeline error")
    cylinders=[f for f in face_result.get("faces",[]) if isinstance(f.get("cylinder"),dict)]
    assert len(cylinders)==4, (
        f"{label}: expected four certified half-cylinder B-rep patches, got {len(cylinders)}")
    refs={}
    for feature,diamkey in (("Bore1","bore1_d"),("Bore2","bore2_d")):
        x,y=XY[feature]; radius=st[diamkey]/2
        matches=[]
        for f in cylinders:
            c=f["cylinder"]; p=c.get("origin",[])
            if (isinstance(p,list) and len(p)>=2
                and helper.approximate(p[0],x)
                and helper.approximate(p[1],y)
                and helper.approximate(c.get("radius"),radius)):
                matches.append(f)
        assert len(matches)==2, (
            f"{label}: {feature} at {x,y} radius={radius}: "
            f"expected 2 cylinder patches, got {[f.get('name') for f in matches]}")
        assert all(f.get("exact") is True for f in matches), (
            f"{label}: {feature} no longer has exact certified face history")
        face_names=sorted(f.get("name") for f in matches)
        assert all(isinstance(n,str) and n for n in face_names), (
            f"{label}: {feature} unnamed B-rep face")
        assert len(set(face_names))==2, f"{label}: {feature} duplicate face names"
        boundaries=sorted({e["name"] for e in edge_result.get("edges",[])
                           if isinstance(e.get("name"),str)
                           and any(n in e["name"].split("|") for n in face_names)})
        assert len(boundaries)>=4, (
            f"{label}: {feature} insufficient named boundary edges: {boundaries}")
        refs[feature]={"faces":face_names,"edges":boundaries,"exact":True}
    assert set(refs["Bore1"]["faces"]).isdisjoint(refs["Bore2"]["faces"]), (
        f"{label}: faces silently transferred between independent holes")
    assert set(refs["Bore1"]["edges"]).isdisjoint(refs["Bore2"]["edges"]), (
        f"{label}: boundary edge names silently transferred between holes")
    assert measure.get("body_count")==1, f"{label}: wrong body count"
    assert len(measure.get("bodies",[]))==1 and not measure["bodies"][0].get("error"), (
        f"{label}: B-rep measurement error")
    oracle=geometry_oracle(st)
    for key in ("volume_mm3","area_mm2"):
        got=measure["total"].get(key);want=oracle[key]
        assert isinstance(got,(float,int)) and abs(got-want)<=max(0.001,abs(want)*0.001), (
            f"{label}: analytical {key}: expected {want}, got {got}")
    return {"params":st,"ids":ids,"refs":refs,"volume":measure["total"]["volume_mm3"],
            "area":measure["total"]["area_mm2"],"oracle":oracle}

def require_identity(reference,current,label):
    for feature in ("Stock","Bore1","Bore2"):
        assert reference["ids"][feature]==current["ids"][feature], (
            f"{label}: {feature} feature ID changed")
    for feature in ("Bore1","Bore2"):
        for key in ("faces","edges","exact"):
            assert reference["refs"][feature][key]==current["refs"][feature][key], (
                f"{label}: {feature} {key} changed from "
                f"{reference['refs'][feature][key]} to {current['refs'][feature][key]}")

def run_case(helper,exe,source,out,creation,name,operations):
    seq=list(creation); states=[]; history=[]
    values=dict(INITIAL)
    def read(label):
        indices=helper.observe(seq)
        states.append((label,indices,dict(values)))
    read("baseline")
    for i,(param,newval) in enumerate(operations,1):
        previous=dict(values)
        assert param in INITIAL and values[param]!=float(newval), (
            f"{name}: redundant edit {i}")
        seq.append(helper.cmd("parameters.change",{
            "name":param,"expression":f"{newval} mm"}))
        values[param]=float(newval)
        history.append((previous,dict(values)))
        read(f"edit_{i}")
    for i in range(len(history),0,-1):
        seq.append(helper.cmd("edit.undo"))
        values=dict(history[i-1][0])
        read(f"undo_{i}")
    for i in range(1,len(history)+1):
        seq.append(helper.cmd("edit.redo"))
        values=dict(history[i-1][1])
        read(f"redo_{i}")
    output=out/(name+"-final.solidcraft")
    replies=helper.run_script(exe,source,out,name+"-main",seq,savefile=output)
    reports={}
    for stage,indices,parameters in states:
        reports[stage]=inspect_dynamic(replies,indices,parameters,name+"/"+stage,helper)
    original=reports["baseline"]
    for stage,record in reports.items():
        require_identity(original,record,name+"/"+stage)
    for i in range(1,len(history)+1):
        undo=reports[f"undo_{i}"]
        redo=reports[f"redo_{i}"]
        assert undo["params"]==history[i-1][0],f"{name}: undo_{i} incorrect parameters"
        assert redo["params"]==history[i-1][1],f"{name}: redo_{i} incorrect parameters"
    assert reports[f"redo_{len(history)}"]["params"]==reports[f"edit_{len(history)}"]["params"]
    reopened_steps=[]
    reopen_indices=helper.observe(reopened_steps)
    reopened=helper.run_script(exe,source,out,name+"-reopened",reopened_steps,infile=output)
    final=inspect_dynamic(reopened,reopen_indices,values,name+"/reopened",helper)
    require_identity(original,final,name+"/reopened")
    last=reports[f"redo_{len(history)}"]
    for key in ("ids","refs"):
        assert final[key]==last[key],f"{name}: persistence {key} diverged"
    return {"status":"PASS","edits":len(operations),
            "observed_states":len(states)+1,"final_params":values,
            "initial_refs":original["refs"],"final_refs":final["refs"],
            "initial_volume_mm3":original["volume"],"final_volume_mm3":final["volume"],
            "sequence":operations}

def main():
    parser=argparse.ArgumentParser()
    for opt in ("--cli","--source","--out"): parser.add_argument(opt,required=True)
    a=parser.parse_args()
    exe=Path(a.cli).resolve(); source=Path(a.source).resolve()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    assert exe.is_file(),f"CLI executable missing: {exe}"
    h=shared()
    recipe=source/"tests/oracle/84-plate-two-bores/recipe.json"
    original=json.loads(h.execute(exe,source,["recipe",recipe],out/"recipe.log"))["commands"]
    assert sum(c.get("command")=="solid.hole" for c in original)==2
    report={"source":SOURCE_SHA,"kind":"W23a 3D multi-parameter, W13/W14 2D NOT tested",
            "scenarios":{},"failed":0}
    for name,ops in MATRIX.items():
        try:
            record=run_case(h,exe,source,out,original,name,ops)
            report["scenarios"][name]=record
            print(f"PASS {name}: {len(ops)} mixed param edits; all undo/redo states; "
                  "exact faces/edges; analytic values; save/reopen",flush=True)
        except Exception as e:
            report["failed"]+=1
            report["scenarios"][name]={"status":"FAIL","error":str(e),
                "traceback":traceback.format_exc()}
            print(f"FAIL {name}: {e}",file=sys.stderr,flush=True)
    report["status"]="PASS" if not report["failed"] else "FAIL"
    (out/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"W23A_MIXED_3D_CASES={len(MATRIX)} FAILED_CHECKS={report['failed']}",flush=True)
    return 0 if not report["failed"] else 1

if __name__=="__main__":
    sys.exit(main())
