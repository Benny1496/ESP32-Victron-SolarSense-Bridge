#!/usr/bin/env python3
"""Test 20: run eight REAL upstream W17a drawing-view Rust unit tests.

This intentionally does not emulate W13/W14 model-to-drawing updates.
Emits one record for each executed native test and a separate API-readiness gate.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

EXPECTED_TESTS = {
    "each_named_view_looks_from_where_its_name_says",
    "a_view_from_a_direction_and_up_matches_the_named_views",
    "an_up_just_off_the_direction_still_looks_along_it",
    "a_50_mm_cube_measures_as_the_views_say",
    "the_views_centre_lands_on_its_position",
    "a_scale_reads_and_writes_as_paper_to_model",
    "the_fitted_scale_is_the_largest_preset_that_fits",
    "a_frame_refuses_hostile_input",
}
NAMESPACE = "drawing_view::tests::"
PIN = "ebafe07487df5cdd108e091db939de765645e5eb"

def command(source, out, name, args):
    env = os.environ.copy()
    env["CARGO_TERM_COLOR"] = "never"
    env["CARGO_INCREMENTAL"] = "0"
    before=time.monotonic()
    p=subprocess.run(args,cwd=source,env=env,text=True,encoding="utf-8",
                     errors="replace",capture_output=True)
    body=(f"COMMAND: {' '.join(args)}\nEXIT: {p.returncode}\n"
          f"DURATION: {time.monotonic()-before:.3f}s\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    (out/(name+".log")).write_text(body,encoding="utf-8")
    return p

def fail(msg):
    raise AssertionError(msg)

def main():
    parser=argparse.ArgumentParser()
    for key in ("--cli","--source","--out"):
        parser.add_argument(key,required=True)
    a=parser.parse_args()
    out=Path(a.out).resolve()
    source=Path(a.source).resolve()
    out.mkdir(parents=True,exist_ok=True)
    result={"source":PIN,"scope":"Executed real W17a Rust unit tests of drawing_view only",
            "failed":0,"scenarios":{},
            "w13_w14_end_to_end_executed":False}
    try:
        assert (source/"crates/geom/src/drawing_view_tests.rs").exists(), (
            "Actual W17a Rust tests missing from checked-out source")
        cargo=["cargo","test","--locked","-p","solidcraft-geom","--lib",
               "drawing_view::tests::","--"]
        listed=command(source,out,"rust-list",cargo+["--list"])
        if listed.returncode:
            fail(f"W17a native discovery command failed, exit {listed.returncode}")
        listed_names=set()
        for line in listed.stdout.splitlines():
            m=re.fullmatch(r"(drawing_view::tests::([A-Za-z_0-9]+)): test",line.strip())
            if m:
                listed_names.add(m.group(2))
        if listed_names != EXPECTED_TESTS:
            fail(f"Expected exact 8 native W17a tests; discovered {sorted(listed_names)}. "
                 f"Missing={sorted(EXPECTED_TESTS-listed_names)} extra={sorted(listed_names-EXPECTED_TESTS)}")

        executed=command(source,out,"rust-execute",cargo+["--nocapture"])
        outputs=executed.stdout+"\n"+executed.stderr
        passed=set();failed=set()
        for line in outputs.splitlines():
            m=re.fullmatch(r"test drawing_view::tests::([A-Za-z_0-9]+) \.\.\. (ok|FAILED|ignored)",
                           line.strip())
            if m:
                (passed if m.group(2)=="ok" else failed).add(m.group(1))
        for name in sorted(EXPECTED_TESTS):
            if name in passed and name not in failed:
                result["scenarios"][name]={"status":"PASS","source":"native Rust test binary"}
            else:
                result["scenarios"][name]={"status":"FAIL",
                    "error":"Native Rust test failed, was skipped, or lacked a completed success record"}
                result["failed"]+=1
        if executed.returncode:
            result["failed"]=max(1,result["failed"])
            result["execution_error"]=f"cargo test failed with exit {executed.returncode}"
        if passed != EXPECTED_TESTS or failed:
            result["failed"]=max(1,result["failed"])
            result["execution_error"]=f"Expected 8 passes, got passes={sorted(passed)} fails={sorted(failed)}"
    except Exception as error:
        result["failed"]=max(1,result["failed"])
        result["execution_error"]=str(error)
        result["traceback"]=traceback.format_exc()
        # Even if test-list discovery fails, require every intended native test
        # to be explicitly recorded as NOT RUN (counted as failure, never green).
        for name in sorted(EXPECTED_TESTS):
            result["scenarios"].setdefault(name,{
                "status":"FAIL","error":"W17a Rust test not executed successfully; "+str(error)})
    result["status"]="PASS" if result["failed"]==0 and len(result["scenarios"])==8 else "FAIL"
    (out/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"W17A_NATIVE_REAL_TESTS={len(EXPECTED_TESTS)} FAILED_CHECKS={result['failed']}",flush=True)
    for name,record in result["scenarios"].items():
        print(f"  {record['status']} native_W17a/{name}",flush=True)
    if result.get("execution_error"):
        print("W17A_ERROR: "+result["execution_error"],file=sys.stderr,flush=True)
    return 0 if result["status"]=="PASS" else 1

if __name__=="__main__":
    sys.exit(main())
