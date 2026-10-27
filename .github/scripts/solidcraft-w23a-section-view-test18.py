#!/usr/bin/env python3
"""SolidCraft test18: twelve view-only section planes and two edit-with-section cases.

Checks actual engine command inspect.section and independent analytic 3D geometry.
The command does NOT extract associative drawing curves or validate W13/W14.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys
import traceback

PIN="ebafe07487df5cdd108e091db939de765645e5eb"
INITIAL={"length":100.0,"width":80.0,"bore1_d":10.0,"bore2_d":10.0}

PLANES={
    "xy_at_10":({"plane":"XY","at":"10 mm"},[0,0,10],[0,0,1],"Z",10),
    "xy_offset_10":({"plane":"XY","offset":"10 mm"},[0,0,10],[0,0,1],"Z",10),
    "xy_at_10_flipped":({"plane":"XY","at":"10 mm","flip":True},[0,0,10],[0,0,-1],"Z",10),
    "xy_at_zero_flipped":({"plane":"XY","at":"0 mm","flip":True},[0,0,0],[0,0,-1],"Z",0),
    "xz_at_40":({"plane":"XZ","at":"40 mm"},[0,40,0],[0,1,0],"Y",40),
    "xz_offset_40":({"plane":"XZ","offset":"40 mm"},[0,40,0],[0,1,0],"Y",40),
    "xz_at_40_flipped":({"plane":"XZ","at":"40 mm","flip":True},[0,40,0],[0,-1,0],"Y",40),
    "yz_at_50":({"plane":"YZ","at":"50 mm"},[50,0,0],[1,0,0],"X",50),
    "yz_offset_50":({"plane":"YZ","offset":"50 mm"},[50,0,0],[1,0,0],"X",50),
    "yz_at_50_flipped":({"plane":"YZ","at":"50 mm","flip":True},[50,0,0],[-1,0,0],"X",50),
    "custom_translation":({"plane":{"origin":[5,6,7],"normal":[0,0,1]},
                           "offset":"2 mm"},[5,6,9],[0,0,1],None,None),
    "custom_tilted":({"plane":{"origin":[0,0,0],"normal":[0,1,1]},
                      "offset":"10 mm"},[0,10/math.sqrt(2),10/math.sqrt(2)],
                       [0,1/math.sqrt(2),1/math.sqrt(2)],None,None),
}
EDIT_CASES={
    "width_change_while_section_active":
        ({"plane":"XY","at":"10 mm"},[0,0,10],[0,0,1],"Z",10,"width",100.0),
    "bore_change_while_section_active":
        ({"plane":"XZ","at":"40 mm","flip":True},[0,40,0],[0,-1,0],"Y",40,"bore1_d",12.0),
}

def import_local(filename, name):
    path=Path(__file__).with_name(filename)
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load helper {path}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def verify_section(value,origin,normal,axis,at,label):
    sec=value.get("section")
    assert isinstance(sec,dict),f"{label}: missing section response"
    for key,expected in (("origin",origin),("normal",normal)):
        actual=sec.get(key)
        assert isinstance(actual,list) and len(actual)==3, (
            f"{label}: malformed section {key} {actual}")
        assert all(isinstance(x,(int,float)) and abs(x-y)<0.000001
                   for x,y in zip(actual,expected)), (
            f"{label}: section {key} expected {expected}, got {actual}")
    if axis is None:
        assert "axis" not in sec and "at" not in sec, (
            f"{label}: unexpected axis metadata in custom plane")
    else:
        assert sec.get("axis")==axis, (
            f"{label}: expected axis {axis}, got {sec.get('axis')}")
        assert isinstance(sec.get("at"),(int,float)) and abs(sec["at"]-at)<1e-6, (
            f"{label}: expected at={at}, got {sec.get('at')}")

def evaluate(model,helpers,results,idx,parameters,label):
    return model.inspect_dynamic(results,idx,parameters,label,helpers)

def baseline_case(model,helpers,exe,source,out,commands,label,entry):
    params,origin,normal,axis,at=entry
    seq=list(commands)
    base_idx=helpers.observe(seq)
    sec_i=len(seq)
    seq.append(helpers.cmd("inspect.section",params))
    active_idx=helpers.observe(seq)
    clear_i=len(seq)
    seq.append(helpers.cmd("inspect.section",{"clear":True}))
    cleared_idx=helpers.observe(seq)
    saved=out/(label+"-after-clear.solidcraft")
    replies=helpers.run_script(exe,source,out,label+"-run",seq,savefile=saved)
    verify_section(replies[sec_i],origin,normal,axis,at,label)
    assert replies[clear_i].get("section","not cleared") is None, (
        f"{label}: section clear failed")
    original=evaluate(model,helpers,replies,base_idx,INITIAL,label+"/base")
    during=evaluate(model,helpers,replies,active_idx,INITIAL,label+"/section")
    cleared=evaluate(model,helpers,replies,cleared_idx,INITIAL,label+"/clear")
    for item,phase in ((during,"active"),(cleared,"cleared")):
        model.require_identity(original,item,label+"/"+phase)
        assert item["volume"]==original["volume"] and item["area"]==original["area"],(
            f"{label}: view-only section changed 3D geometry")
    reseq=[]
    ri=helpers.observe(reseq)
    reopened=helpers.run_script(exe,source,out,label+"-reopen",reseq,infile=saved)
    again=evaluate(model,helpers,reopened,ri,INITIAL,label+"/reopen")
    model.require_identity(original,again,label+"/reopen")
    return {"status":"PASS","section_result":replies[sec_i],
            "initial_ids":original["ids"],"initial_refs":original["refs"]}

def edit_case(model,helpers,exe,source,out,commands,label,entry):
    params,origin,normal,axis,at,parameter,new_value=entry
    changed=dict(INITIAL)
    changed[parameter]=float(new_value)
    seq=list(commands)
    initial_idx=helpers.observe(seq)
    sec_i=len(seq)
    seq.append(helpers.cmd("inspect.section",params))
    during_idx=helpers.observe(seq)
    edit_i=len(seq)
    seq.append(helpers.cmd("parameters.change",{
        "name":parameter,"expression":f"{new_value} mm"}))
    edited_idx=helpers.observe(seq)
    clear_i=len(seq)
    seq.append(helpers.cmd("inspect.section",{"clear":True}))
    cleared_idx=helpers.observe(seq)
    undo_i=len(seq)
    seq.append(helpers.cmd("edit.undo"))
    undo_idx=helpers.observe(seq)
    redo_i=len(seq)
    seq.append(helpers.cmd("edit.redo"))
    redo_idx=helpers.observe(seq)
    saved=out/(label+"-edited.solidcraft")
    replies=helpers.run_script(exe,source,out,label+"-run",seq,savefile=saved)
    verify_section(replies[sec_i],origin,normal,axis,at,label)
    assert replies[clear_i].get("section","not cleared") is None, (
        f"{label}: section clear failed")
    assert replies[undo_i].get("undone") is not None, (
        f"{label}: Undo did not undo the previous REAL model edit")
    assert replies[redo_i].get("redone") is not None, (
        f"{label}: Redo did not redo the previous REAL model edit")
    base=evaluate(model,helpers,replies,initial_idx,INITIAL,label+"/before")
    active=evaluate(model,helpers,replies,during_idx,INITIAL,label+"/section-active")
    edited=evaluate(model,helpers,replies,edited_idx,changed,label+"/edited")
    cleared=evaluate(model,helpers,replies,cleared_idx,changed,label+"/cleared")
    undone=evaluate(model,helpers,replies,undo_idx,INITIAL,label+"/undo")
    redone=evaluate(model,helpers,replies,redo_idx,changed,label+"/redo")
    for phase,item in (("active",active),("edited",edited),("cleared",cleared),
                       ("undo",undone),("redo",redone)):
        model.require_identity(base,item,label+"/"+phase)
    assert base["volume"]==undone["volume"] and base["area"]==undone["area"],(
        f"{label}: Undo failed to restore original model")
    assert edited["volume"]==redone["volume"] and edited["area"]==redone["area"],(
        f"{label}: Redo failed to restore changed model")
    assert abs(base["volume"]-edited["volume"])>100,(
        f"{label}: model edit did not cause real volume change")
    sequel=[]
    i=helpers.observe(sequel)
    r2=helpers.run_script(exe,source,out,label+"-reopen",sequel,infile=saved)
    persisted=evaluate(model,helpers,r2,i,changed,label+"/reopen")
    model.require_identity(base,persisted,label+"/reopen")
    return {"status":"PASS","parameter":parameter,"value":new_value,
            "section_result":replies[sec_i],
            "base_volume":base["volume"],"edited_volume":edited["volume"]}

def main():
    p=argparse.ArgumentParser()
    for flag in ("--cli","--source","--out"):
        p.add_argument(flag,required=True)
    a=p.parse_args()
    exe=Path(a.cli).resolve()
    source=Path(a.source).resolve()
    out=Path(a.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert exe.is_file(),f"CLI unavailable: {exe}"
    h=import_local("solidcraft-w23a-post-reopen-test15.py","test15_shared")
    geom=import_local("solidcraft-w23a-mixed-parameter-test17.py","test17_geometry")
    recipe=source/"tests/oracle/84-plate-two-bores/recipe.json"
    commands=json.loads(h.execute(exe,source,["recipe",recipe],out/"recipe.log"))["commands"]
    assert sum(x.get("command")=="solid.hole" for x in commands)==2
    result={"source":PIN,"kind":"View-only inspect.section, not drawing W13/W14",
            "scenarios":{},"failed":0}
    for name,entry in list(PLANES.items())+list(EDIT_CASES.items()):
        try:
            if name in PLANES:
                evidence=baseline_case(geom,h,exe,source,out,commands,name,entry)
            else:
                evidence=edit_case(geom,h,exe,source,out,commands,name,entry)
            result["scenarios"][name]=evidence
            print(f"PASS {name}: section plane/clear, source identity, measured geometry, and reopen",flush=True)
        except Exception as ex:
            result["failed"]+=1
            result["scenarios"][name]={"status":"FAIL","error":str(ex),
                                       "traceback":traceback.format_exc()}
            print(f"FAIL {name}: {ex}",file=sys.stderr,flush=True)
    result["status"]="PASS" if result["failed"]==0 else "FAIL"
    (out/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"W23A_SECTION_VIEW_CASES={len(PLANES)+len(EDIT_CASES)} "
          f"FAILED_CHECKS={result['failed']}",flush=True)
    return 0 if not result["failed"] else 1

if __name__=="__main__":
    sys.exit(main())
