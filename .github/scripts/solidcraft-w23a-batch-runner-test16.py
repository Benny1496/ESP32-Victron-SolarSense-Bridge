#!/usr/bin/env python3
"""Single-build W23a Windows test orchestrator: 5 suites, 16 real scenarios.

Each suite is independently invoked and its failures do not suppress later suites.
Outputs original run logs, per-suite artifacts and an independently checked
aggregate JSON/Markdown. This does not qualify W13/W14 2D drawing updates.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

SUITES = (
  ("test11_feature_ids", "solidcraft-w23a-model-identity.py",3),
  ("test13_persistent_face_edges", "solidcraft-w23a-persistent-refs.py",3),
  ("test14_deleted_bore_replacement","solidcraft-w23a-replacement-test14.py",2),
  ("test15_post_reopen_updates","solidcraft-w23a-post-reopen-test15.py",2),
  ("test16_six_stress_sequences","solidcraft-w23a-parameter-stress-test16.py",6),
)
SOURCE_SHA = "ebafe07487df5cdd108e091db939de765645e5eb"
# GitHub Windows job timeout is 90 min. A 75-min per-suite cap leaves
# room for compilation, failure summaries, and artifact upload.
SUITE_TIMEOUT_SECONDS = 75 * 60

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def main():
    p=argparse.ArgumentParser()
    for x in ("--cli","--source","--out"):p.add_argument(x,required=True)
    a=p.parse_args()
    exe=Path(a.cli).resolve()
    source=Path(a.source).resolve()
    folder=Path(a.out).resolve()
    scripts=Path(__file__).resolve().parent
    folder.mkdir(parents=True,exist_ok=True)
    assert exe.is_file(),f"Missing built CLI: {exe}"
    expected=sum(group[2] for group in SUITES)
    result={"title":"SolidCraft W23a integrated Windows batch - test 16",
      "official_source":f"tangency-labs/solidcraft@{SOURCE_SHA}",
      "scope":"3D source model ONLY; no executed W13/W14 2D-drawing refresh",
      "started_at":now(),"expected_suites":len(SUITES),"expected_scenarios":expected,
      "suites":[],"scenarios_pass":0,"scenarios_fail":0,"scenarios_missing":0,
      "suites_pass":0,"suites_fail":0}
    print(f"W23A_BATCH_BEGIN suites={len(SUITES)} scenarios={expected} source={SOURCE_SHA}",flush=True)
    for name,script,count in SUITES:
        dir_=folder/name
        dir_.mkdir(parents=True,exist_ok=True)
        executable=scripts/script
        argv=[sys.executable,str(executable),
              "--cli",str(exe),"--source",str(source),"--out",str(dir_)]
        entry={"suite":name,"script":script,"expected_scenarios":count,
               "start":now(),"command":argv,"cases":[]}
        print(f"W23A_SUITE_BEGIN {name} expected={count}",flush=True)
        t=time.monotonic()
        output=""
        try:
            p=subprocess.run(argv,cwd=str(source),capture_output=True,
                             encoding="utf-8",errors="replace",text=True,
                             timeout=SUITE_TIMEOUT_SECONDS)
            output=p.stdout+"\n"+p.stderr
            entry["exit_code"]=p.returncode
        except subprocess.TimeoutExpired as e:
            output=(e.stdout or b"").decode("utf-8","replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
            entry["exit_code"]=-1
            entry["exception"]=f"Test suite timed out after {SUITE_TIMEOUT_SECONDS} seconds"
        except Exception as e:
            entry["exit_code"]=-1
            entry["exception"]=str(e)
            output=traceback.format_exc()
        entry["duration_s"]=round(time.monotonic()-t,3)
        entry["completed_at"]=now()
        (dir_/"suite-output.log").write_text(
            "RUN: "+" ".join(argv)+"\nEXIT: "+str(entry["exit_code"])+"\n"
            +"DURATION_S: "+str(entry["duration_s"])+"\n\n"+output,
            encoding="utf-8")
        summary=dir_/"summary.json"
        try:
            if not summary.exists():
                raise AssertionError("No per-suite summary.json was produced")
            summary_data=json.loads(summary.read_text(encoding="utf-8"))
            records=summary_data.get("cases",summary_data.get("scenarios"))
            if not isinstance(records,dict):
                raise AssertionError("Invalid summary: no cases or scenarios dictionary")
            entry["cases"]=[{"case":k,"status":v.get("status"),"error":v.get("error")}
                            for k,v in records.items()]
            observed=len(records)
            if observed!=count:
                raise AssertionError(f"Expected {count} scenario records, got {observed}")
            statuses=[r["status"] for r in entry["cases"]]
            passes=statuses.count("PASS")
            failures=sum(s=="FAIL" for s in statuses)
            if passes+failures!=count:
                raise AssertionError(f"Invalid per-case statuses: {statuses}")
            if summary_data.get("failed")!=failures:
                raise AssertionError("Per-suite failed count disagrees with case statuses")
            entry["scenarios_pass"]=passes
            entry["scenarios_fail"]=failures
            entry["scenarios_missing"]=0
            entry["status"]="PASS" if entry["exit_code"]==0 and failures==0 and summary_data.get("status")=="PASS" else "FAIL"
            if entry["exit_code"]!=0 and failures==0:
                entry["exception"]=f"Script exited non-zero ({entry['exit_code']}) despite zero reported failures"
        except Exception as e:
            entry["status"]="ERROR"
            entry["exception"]=str(e)
            counted_pass=sum(r["status"]=="PASS" for r in entry["cases"])
            counted_fail=sum(r["status"]=="FAIL" for r in entry["cases"])
            entry["scenarios_pass"]=counted_pass
            entry["scenarios_fail"]=counted_fail
            entry["scenarios_missing"]=max(0,count-counted_pass-counted_fail)
        result["scenarios_pass"]+=entry["scenarios_pass"]
        result["scenarios_fail"]+=entry["scenarios_fail"]
        result["scenarios_missing"]+=entry["scenarios_missing"]
        result["suites_pass"]+=entry["status"]=="PASS"
        result["suites_fail"]+=entry["status"]!="PASS"
        result["suites"].append(entry)
        print(f"W23A_SUITE_END {name}: {entry['status']} "
              f"pass={entry['scenarios_pass']} fail={entry['scenarios_fail']} "
              f"missing={entry['scenarios_missing']} duration={entry['duration_s']}s",flush=True)
        for case in entry["cases"]:
            print(f"  {case['status']} {name}/{case['case']}"
                  + (f": {case['error']}" if case.get("error") else ""),flush=True)
        if entry.get("exception"):
            print(f"  SUITE_ERROR {name}: {entry['exception']}",flush=True)
    result["completed_at"]=now()
    result["status"]="PASS" if (result["suites_fail"]==0 and result["scenarios_pass"]==expected
                             and result["scenarios_fail"]==0 and result["scenarios_missing"]==0) else "FAIL"
    (folder/"aggregate-summary.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# SolidCraft W23a Batch Test #16", "",
        f"Overall: **{result['status']}** — {result['scenarios_pass']}/{expected} scenarios passed, "
        f"{result['scenarios_fail']} failed, {result['scenarios_missing']} missing.",
        f"Suites: {result['suites_pass']}/{len(SUITES)} passed.", "",
        f"Official pinned source: `{SOURCE_SHA}`. Windows with Rust 1.99.1.", "",
        "Scope: 3D source feature/face/edge reference validity; NOT drawing W13/W14.", "",
        "| Suite | Passed | Failed | Missing | Outcome |",
        "| --- | ---: | ---: | ---: | --- |"]
    for row in result["suites"]:
        md.append(f"| {row['suite']} | {row['scenarios_pass']} | "
                  f"{row['scenarios_fail']} | {row['scenarios_missing']} | {row['status']} |")
    md+=["", "## Scenario details"]
    for row in result["suites"]:
        md+=["",f"### {row['suite']}"]
        for case in row["cases"]:
            md.append(f"- {case['status']}: `{case['case']}`"+
                      (f" — {case['error']}" if case.get("error") else ""))
        if row.get("exception"):
            md.append(f"- Suite problem: {row['exception']}")
    (folder/"aggregate-summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(f"W23A_BATCH_RESULT={result['status']} SUITES_PASS={result['suites_pass']}/{len(SUITES)} "
          f"CASES_PASS={result['scenarios_pass']}/{expected} "
          f"CASES_FAIL={result['scenarios_fail']} CASES_MISSING={result['scenarios_missing']}",flush=True)
    return 0 if result["status"]=="PASS" else 1

if __name__=="__main__":
    sys.exit(main())
