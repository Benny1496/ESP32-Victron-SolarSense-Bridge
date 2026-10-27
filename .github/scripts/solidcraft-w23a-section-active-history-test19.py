#!/usr/bin/env python3
"""W23a Test 19: 12 two-edit cycles while a section view stays active.

All 42 legacy cases remain separate in the batch. Each new case adds 2 actual
model parameter edits, 2x undo/redo WITHOUT clearing the section, save/reopen,
a further post-reopen edit and independent second save/reopen verification.
The source command inspect.section is view-only, NOT a W13/W14 Drawing API.
"""
import argparse
import json
import pathlib
import sys
import traceback

PIN = "ebafe07487df5cdd108e091db939de765645e5eb"
BASE = {"length": 100.0, "width": 80.0, "bore1_d": 10.0, "bore2_d": 10.0}
CUTS = (
    "xy_at_10", "xy_at_10_flipped", "xz_at_40",
    "xz_at_40_flipped", "yz_at_50_flipped", "custom_tilted",
)
EDIT_PLANS = {
    "width_then_bore1": {
        "first": ("width", 100.0),
        "second": ("bore1_d", 12.0),
        "after_reopen": ("bore2_d", 12.0),
    },
    "bore2_then_length": {
        "first": ("bore2_d", 12.0),
        "second": ("length", 120.0),
        "after_reopen": ("bore1_d", 12.0),
    },
}

def command_parameter(h, parameter, value):
    return h.cmd("parameters.change", {
        "name": parameter, "expression": f"{value:g} mm"
    })

def changed(parameters, operation):
    name, value = operation
    assert name in parameters and parameters[name] != float(value), (
        f"Invalid/no-op parameter edit {operation}")
    after = dict(parameters)
    after[name] = float(value)
    return after

def scan(m, h, responses, positions, expected, label):
    state = m.inspect_dynamic(responses, positions, expected, label, h)
    assert state["params"] == expected, f"{label}: wrong parameter expectation"
    return state

def stable(m, baseline, snapshots, label):
    for phase, state in snapshots.items():
        m.require_identity(baseline, state, f"{label}/{phase}")

def volume_equal(a, b, label):
    for key in ("volume", "area"):
        assert abs(a[key] - b[key]) < 0.0001, (
            f"{label}: {key} undo/redo mismatch {a[key]} vs {b[key]}")

def scenario(h, m, sect, exe, source, out, recipe, name, cutting, plan):
    cut_params, origin, normal, axis, at = sect.PLANES[cutting]
    first = plan["first"]
    second = plan["second"]
    third = plan["after_reopen"]
    v0 = dict(BASE)
    v1 = changed(v0, first)
    v2 = changed(v1, second)
    v3 = changed(v2, third)

    # First independent CLI process. The section remains ACTIVE for both
    # geometry-changing edits, BOTH undo steps and BOTH redo steps.
    seq = list(recipe)
    positions = {}
    def observe(stage):
        positions[stage] = h.observe(seq)

    observe("original")
    section_index = len(seq)
    seq.append(h.cmd("inspect.section", cut_params))
    observe("section_active")
    seq.append(command_parameter(h, *first))
    observe("after_edit_1")
    seq.append(command_parameter(h, *second))
    observe("after_edit_2")
    undo2 = len(seq)
    seq.append(h.cmd("edit.undo"))
    observe("undo_2")
    undo1 = len(seq)
    seq.append(h.cmd("edit.undo"))
    observe("undo_1")
    redo1 = len(seq)
    seq.append(h.cmd("edit.redo"))
    observe("redo_1")
    redo2 = len(seq)
    seq.append(h.cmd("edit.redo"))
    observe("redo_2")
    clear_index = len(seq)
    seq.append(h.cmd("inspect.section", {"clear": True}))
    observe("cleared")

    saved_first = out / f"{name}-stage1.solidcraft"
    r = h.run_script(exe, source, out, name+"-stage1", seq, savefile=saved_first)
    sect.verify_section(r[section_index], origin, normal, axis, at, name)
    assert r[clear_index].get("section", "not cleared") is None, (
        f"{name}: section clear failed")
    for command_index, response_key in ((undo2, "undone"), (undo1, "undone"),
                                        (redo1, "redone"), (redo2, "redone")):
        assert r[command_index].get(response_key) is not None, (
            f"{name}: model {response_key} missing while section active")
    expected = {
        "original": v0, "section_active": v0, "after_edit_1": v1,
        "after_edit_2": v2, "undo_2": v1, "undo_1": v0,
        "redo_1": v1, "redo_2": v2, "cleared": v2,
    }
    states = {phase: scan(m,h,r,indices,expected[phase],f"{name}/{phase}")
              for phase,indices in positions.items()}
    old = states["original"]
    stable(m,old,states,name)
    for a,b in (("original","section_active"),("original","undo_1"),
                ("after_edit_1","undo_2"),("after_edit_1","redo_1"),
                ("after_edit_2","redo_2"),("after_edit_2","cleared")):
        volume_equal(states[a],states[b],f"{name}:{a}->{b}")
    assert abs(states["after_edit_2"]["volume"]-old["volume"])>100, (
        f"{name}: first two real edits did not alter measured volume")

    # New CLI process. Model must be editable after clearing section and save.
    seq2 = []
    indices2 = {}
    def observe2(stage):
        indices2[stage] = h.observe(seq2)
    observe2("loaded")
    seq2.append(command_parameter(h,*third))
    observe2("third_edit")
    undo3 = len(seq2)
    seq2.append(h.cmd("edit.undo"))
    observe2("undo_third")
    redo3 = len(seq2)
    seq2.append(h.cmd("edit.redo"))
    observe2("redo_third")
    saved_second = out / f"{name}-stage2.solidcraft"
    r2 = h.run_script(exe,source,out,name+"-stage2",seq2,
                      infile=saved_first, savefile=saved_second)
    assert r2[undo3].get("undone") is not None, (
        f"{name}: post-reopen undo failed")
    assert r2[redo3].get("redone") is not None, (
        f"{name}: post-reopen redo failed")
    expected2 = {"loaded":v2,"third_edit":v3,"undo_third":v2,"redo_third":v3}
    states2 = {phase:scan(m,h,r2,positions,expected2[phase],f"{name}/{phase}")
               for phase,positions in indices2.items()}
    stable(m,old,states2,name+"/post_reopen")
    volume_equal(states["cleared"],states2["loaded"],f"{name}:reload")
    volume_equal(states2["loaded"],states2["undo_third"],f"{name}:third_undo")
    volume_equal(states2["third_edit"],states2["redo_third"],f"{name}:third_redo")
    assert abs(states2["third_edit"]["volume"]-states2["loaded"]["volume"])>100, (
        f"{name}: third real edit did not alter volume")

    # Third process proves second persisted document has the exact expected
    # named faces and edges, with all three model edits retained.
    seq3=[]
    final_positions = h.observe(seq3)
    r3=h.run_script(exe,source,out,name+"-stage3",seq3,infile=saved_second)
    final=scan(m,h,r3,final_positions,v3,f"{name}/final_reopen")
    stable(m,old,{"final_reopen":final},name)
    volume_equal(states2["redo_third"],final,f"{name}:final")
    return {"status":"PASS","section":cutting,"edit_order":[first,second,third],
            "phases_checked":len(states)+len(states2)+1,
            "initial_references":old["refs"],"saved_references":final["refs"],
            "initial_volume_mm3":old["volume"],"final_volume_mm3":final["volume"]}

def main():
    p=argparse.ArgumentParser()
    for item in ("--cli","--source","--out"):
        p.add_argument(item,required=True)
    args=p.parse_args()
    exe=pathlib.Path(args.cli).resolve()
    source=pathlib.Path(args.source).resolve()
    out=pathlib.Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert exe.is_file(), f"SolidCraft CLI missing: {exe}"
    # Import previously certified positive-path fixture inspectors, no
    # change in analytic volume/area or exact face/edge ID acceptance.
    import importlib.util
    def load(script, module):
        spec=importlib.util.spec_from_file_location(module,pathlib.Path(__file__).with_name(script))
        assert spec and spec.loader
        inst=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inst)
        return inst
    h=load("solidcraft-w23a-post-reopen-test15.py","test19_source_helper")
    m=load("solidcraft-w23a-mixed-parameter-test17.py","test19_geometry_helper")
    sect=load("solidcraft-w23a-section-view-test18.py","test19_section_helper")
    fixture=source/"tests/oracle/84-plate-two-bores/recipe.json"
    recipe=json.loads(h.execute(exe,source,["recipe",fixture],out/"recipe.log"))["commands"]
    assert sum(row.get("command")=="solid.hole" for row in recipe)==2
    report={"source":PIN,"scope":"3D feature/section view isolation, NOT W13/W14 drawing API",
            "scenarios":{},"failed":0}
    for cutting in CUTS:
        for order, plan in EDIT_PLANS.items():
            name=f"{cutting}_{order}"
            try:
                evidence=scenario(h,m,sect,exe,source,out,recipe,name,cutting,plan)
                report["scenarios"][name]=evidence
                print(f"PASS {name}: active section, two edits, 2x undo+redo, "
                      f"clear, save/reopen, third edit, undo/redo, second save/reopen",flush=True)
            except Exception as error:
                report["failed"]+=1
                report["scenarios"][name]={"status":"FAIL","error":str(error),
                                           "traceback":traceback.format_exc()}
                print(f"FAIL {name}: {error}",file=sys.stderr,flush=True)
    report["status"]="PASS" if not report["failed"] else "FAIL"
    (out/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"W23A_SECTION_ACTIVE_LONG_HISTORY_CASES={len(CUTS)*len(EDIT_PLANS)} "
          f"FAILED_CHECKS={report['failed']}",flush=True)
    return 0 if not report["failed"] else 1

if __name__=="__main__":
    sys.exit(main())
