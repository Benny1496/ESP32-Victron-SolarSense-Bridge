#!/usr/bin/env python3
"""Read-only API-readiness report for the actual associative Drawing goal.

NOT a set of passing runtime tests. The W13/W14 end-to-end path is explicitly
NOT RUN until real source reference, drawing record and dimensions APIs exist.
"""
import argparse
import json
from pathlib import Path

PIN="ebafe07487df5cdd108e091db939de765645e5eb"
DEPENDENCIES={
 "W12_drawing_persistence":{
    "task":"Save Drawing objects within the design and reopen with source links",
    "issue":"https://github.com/tangency-labs/solidcraft/issues/3890",
    "claim":"Draft work #3891; not integrated at pinned official drawings SHA"
 },
 "W13_persistent_source_resolution":{
    "task":"Resolve saved 2D dimensions to persistent model face/edge identity",
    "issue":"https://github.com/tangency-labs/solidcraft/issues/4892",
    "claim":"Assigned draft PR #4893; real resolver not available in pinned runtime"
 },
 "W14_model_change_invalidation":{
    "task":"Rebuild views, mark LOST and discard outdated asynchronous drawing results",
    "issue":"https://github.com/tangency-labs/solidcraft/issues/4892",
    "claim":"Requires drawing session and publication token; cannot execute end-to-end"
 },
 "W19_associative_dimensions":{
    "task":"Stored 2D dimensions compute and display changed model measurement",
    "issue":"https://github.com/tangency-labs/solidcraft/issues/4896",
    "claim":"Dimension APIs depend on references, views and drawing records"
 },
}
ACCEPTANCE=[
 ("A01","Draw and save a 2D view with two persistent diameter dimensions"),
 ("A02","Change Bore1 10mm to 12mm and update existing 2D dimension to 12mm"),
 ("A03","Verify Bore2 remains 10mm with original persistent source"),
 ("A04","Delete Bore1; bound 2D dimension becomes LOST (not nearest hole)"),
 ("A05","Recreate identical Bore1 position; old LOST dimension stays LOST"),
 ("A06","Undo/redo deletion; drawing references and status follow correctly"),
 ("A07","Reopen model+Drawing and preserve refs, value, status and paper placement"),
 ("A08","Late drawing update result after undo/close is rejected"),
 ("A09","Repeated occurrence source paths resolve to distinct instances"),
 ("A10","Manual note position and text override survive model updates"),
]
def main():
 p=argparse.ArgumentParser()
 for name in ("--cli","--source","--out"):p.add_argument(name,required=True)
 a=p.parse_args();root=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 assert (root/"crates/geom/src/drawing_view.rs").exists(),"W17a ViewFrame data missing"
 assert (root/"crates/geom/src/drawing_view_tests.rs").exists(),"W17a native tests missing"
 reg=(root/"crates/engine/src/cmd/mod.rs").read_text(encoding="utf-8")
 # Evidence is only a best-effort indication; do NOT take this as a proof that
 # no API exists elsewhere. In particular this never turns into a green E2E test.
 discovered={name:(name in reg) for name in
             ("drawing.reference.resolve","drawing.view.refresh","drawing.dimension.add")}
 report={
  "source_sha":PIN,
  "scope":"Actual 3D->2D user goal; API readiness / NOT executed integration tests",
  "status":"NOT_RUN_AWAITING_IMPLEMENTATION",
  "verified_W17a_native_tests_in_separate_suite":True,
  "source_registry_command_strings_found":discovered,
  "dependencies":{k:{"status":"NOT_RUN","details":v} for k,v in DEPENDENCIES.items()},
  "end_to_end_acceptance":{name:{"status":"NOT_RUN","expected":description}
                           for name,description in ACCEPTANCE},
  "explicit_limitation":"Neither the static check nor W17a unit tests proves associative Drawing updates. Do not count NOT_RUN as PASS."
 }
 (out/"drawing-readiness.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
 md=["# Drawing 3D→2D readiness – Test 20","",
     "**Native W17a views tested separately. The actual associative Drawing workflow has NOT RUN.**","",
     f"Official read-only revision: `{PIN}`.","",
     "| Gate | Status |", "| --- | --- |"]
 for gate in DEPENDENCIES:md.append(f"| {gate} | NOT RUN / dependency pending |")
 md+=["","## End-to-end target acceptance – NOT RUN"]
 for name,description in ACCEPTANCE:md.append(f"- **{name}: NOT RUN** — {description}")
 md+=["","No automatic 3D→2D regeneration, stale dimension warning or late-result cancellation was executed in Test #20.",""]
 (out/"drawing-readiness.md").write_text("\n".join(md),encoding="utf-8")
 print("DRAWING_W13_W14_E2E=NOT_RUN W12_W13_W14_W19_GATES=4 BLOCKED=4",flush=True)
 return 0

if __name__=="__main__":
 raise SystemExit(main())
