#!/usr/bin/env python3
"""SolidCraft batch #25: 244 unique native tests from CamWight PR #3891.

Runs 122 known K3b/K4/Drawing tests (same list as batch #24) plus 122
additional model-identity and reference tests verified directly from source.
Requires the existing batch #24 test-runner in the same folder.
"""
import importlib.util
import json
from pathlib import Path
import re
import sys

BASE = Path(__file__).with_name("solidcraft-drawing-storage-test24.py")
spec = importlib.util.spec_from_file_location("solidcraft_batch24", BASE)
if spec is None or spec.loader is None:
    raise SystemExit("TEST25_PREFLIGHT_ERROR: missing test24 runner")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

FILES = [
    ("model_parameter_changes", "solidcraft_engine", "crates/engine/src/cmd/parameters_tests.rs", 24),
    ("persistent_face_lineage", "solidcraft_engine", "crates/engine/src/cmd/lineage_face_tests.rs", 11),
    ("offset_reference_identity", "solidcraft_engine", "crates/engine/src/cmd/offset_identity_tests.rs", 2),
    ("sketch_driving_dimensions", "solidcraft_engine", "crates/engine/src/cmd/sketch_dimensioned_tests.rs", 5),
    ("model_edit_and_history", "solidcraft_engine", "crates/engine/src/cmd/edit_tests.rs", 18),
    ("sketch_persistent_ids", "solidcraft_engine", "crates/engine/src/cmd/sketch_ids_tests.rs", 11),
    ("face_naming_history", "solidcraft_engine", "crates/engine/src/naming_history_tests.rs", 13),
    ("projected_edge_identity", "solidcraft_engine", "crates/engine/src/cmd/sketch_project_edge_tests.rs", 5),
    ("projection_lost_references", "solidcraft_engine", "crates/engine/src/cmd/sketch_project_tests.rs", 20),
    ("guarded_offset_reference", "solidcraft_engine", "crates/engine/src/cmd/offset_edit_guard_tests.rs", 4),
    ("feature_dependency_inspection", "solidcraft_doc", "crates/doc/src/feature_walk_tests.rs", 5),
    ("persistent_face_names", "solidcraft_doc", "crates/doc/src/history_names_tests.rs", 4),
]
EXCLUDED = set("""g2_fillet_survives_edit_undo_and_reopen
redefining_a_fillet_as_g2_on_sloped_ends_survives_undo_and_reopen
redefining_a_blend_replaces_persistent_edge_selection_and_survives_resize
inserting_variable_fillet_control_preserves_parameters_at_existing_positions
redefining_fillet_style_keeps_primary_parameter_and_downstream_references
redefining_a_shell_replaces_persistent_face_selection
redefine_rejects_sheet_exports_before_they_touch_any_files
redefine_maps_placement_inputs_in_the_feature_owner_frame""".split())

source = Path(sys.argv[sys.argv.index("--source") + 1]).resolve()
pattern = re.compile(r"#\[(?:tokio::)?test[^\]]*\]\s*(?:#\[[^\]]*\]\s*)*(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*\(")
existing = [name for _, _, cases in previous.SUITES for name in cases]
additional = []
for suite, crate, relpath, expected in FILES:
    names = [name for name in pattern.findall((source / relpath).read_text(encoding="utf-8")) if name not in EXCLUDED]
    if len(names) != expected:
        raise SystemExit(f"TEST25_PREFLIGHT_ERROR {relpath}: expected {expected} source tests, found {len(names)}")
    additional.append((suite, crate, names))
new = [name for _, _, cases in additional for name in cases]
if len(existing) != 122 or len(new) != 122 or len(set(existing + new)) != 244:
    raise SystemExit("TEST25_PREFLIGHT_ERROR: expected 244 different native tests")
previous.SUITES.extend(additional)
print("TEST25_BEGIN 244 source-verified DISTINCT native Rust tests in 24 suites", flush=True)
result = previous.main()

out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
summary_file = out / "aggregate-summary.json"
if summary_file.exists():
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    summary["test"] = 25
    summary["expected_cases"] = 244
    summary["scope"] = ("244 native checks of Drawing K4, model parameter edits, persistent face/edge IDs, "
                        "lost references and Undo; W13/W14/W19 associative drawing refresh NOT_RUN")
    summary_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    markdown_file = out / "aggregate-summary.md"
    if markdown_file.exists():
        markdown_file.write_text(
            markdown_file.read_text(encoding="utf-8").replace("# SolidCraft Test #24", "# SolidCraft Test #25"),
            encoding="utf-8")
    print(f"TEST25_RESULT={summary['status']} CASES_PASS={summary['pass']}/244 "
          f"CASES_FAIL={summary['fail']} CASES_MISSING={summary['missing']}", flush=True)
sys.exit(result)
