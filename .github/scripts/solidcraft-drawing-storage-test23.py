#!/usr/bin/env python3
"""Test #23: real native Drawing persistence and command tests from CamWight PR #3891.

Only the pinned PR source is executed. No mock tests, no invented 3D->2D
refresh results. The binaries are already compiled together in ONE cargo
test --no-run step; this runner never invokes cargo or rebuilds sources.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

PIN = "36cf48a3f64c530a128f5d794f37b7cfa24cc3ab"
LIMIT_SECONDS = 75 * 60
SUITES = [
    ("k3b_embedded_drawing_io", "solidcraft_io", [
        "a_designs_drawings_round_trip_through_both_forms_byte_for_byte",
        "a_container_refuses_drawing_entries_it_cant_take",
        "a_design_with_two_drawings_of_one_id_is_not_saved",
    ]),
    ("drawing_record_and_inline_json", "solidcraft_doc", [
        "a_drawing_reads_back_as_saved_and_saves_the_same_bytes_again",
        "a_file_may_leave_out_what_has_a_default",
        "every_cap_holds_on_both_sides",
        "the_language_is_a_bcp_47_tag_of_2_to_35_characters",
        "a_fixed_unit_is_a_length_unit_of_the_expression_table",
        "a_border_is_saved_as_a_copy_of_its_profile",
        "damaged_files_are_refused_and_never_patched",
        "a_run_never_gives_an_id_twice",
        "properties_are_kept_as_they_are",
        "a_drawing_too_large_to_reopen_is_not_saved",
        "a_new_drawing_has_one_sheet_and_keeps_the_rules",
        "mutated_files_give_an_error_or_a_valid_drawing_never_a_panic",
        "a_design_keeps_its_drawings_inline_in_plain_json",
        "a_drawing_a_design_cant_read_refuses_the_design",
    ]),
    ("design_container_integrity_regression", "solidcraft_io", [
        "native_cache_round_trip_and_preview_defer_original_sources",
        "model_cache_stores_repeated_parts_once_and_keeps_placed_copies",
        "native_cache_mismatch_is_only_a_cache_miss",
        "metadata_snapshot_survives_in_place_changes_after_preview",
        "round_trip_deduplicates_and_preserves_binary_precision",
        "required_blobs_must_exist_and_match_hashes",
        "hostile_archive_paths_versions_and_truncations_are_errors",
        "rejects_duplicate_entries_and_declared_expansion_before_reading_payloads",
        "metadata_round_trip_preserves_new_and_existing_fields",
    ]),
    ("engine_drawing_commands_and_undo", "solidcraft_engine", [
        "a_drawing_of_the_design_is_kept_in_it_and_opened",
        "a_drawing_is_made_only_of_a_design_with_something_in_it",
        "model_and_drawing_commands_each_run_on_their_own_part",
        "drawing_edits_are_undo_steps_of_the_drawing_that_evaluate_nothing",
        "undo_and_redo_go_through_one_part_at_a_time",
        "a_new_step_ends_what_could_be_redone_in_its_part_only",
        "a_designs_drawings_are_listed_by_name_then_id",
        "deleting_a_drawing_is_a_step_of_the_model",
        "a_refused_change_leaves_the_drawing_as_it_was",
        "a_checkpoint_brings_back_the_drawings_and_the_one_open",
        "a_designs_drawings_are_saved_with_it_and_come_back",
        "a_drawings_properties_follow_the_design_properties_rules",
        "hostile_drawing_params_never_panic",
        "drawing_steps_in_any_order_keep_the_rules",
    ]),
    ("design_io_deeper_regression", "solidcraft_io", [
        "seekable_reader_validates_required_blobs_after_preview",
        "seekable_reader_without_preview_preserves_authoritative_document",
        "a_model_cache_too_big_for_the_file_is_left_out_not_a_failed_save",
        "draft_container_marker_remains_readable",
        "optional_preview_is_bounded_keyed_and_never_authoritative",
        "rejects_invalid_references_and_repeated_payload_expansion",
    ]),
    ("engine_file_save_and_reopen", "solidcraft_engine", [
        "a_save_run_on_a_copy_and_adopted_matches_saving_directly",
        "save_and_save_as_keep_the_model_unless_opted_out",
        "save_as_names_an_untitled_design_after_its_file",
        "save_as_keeps_a_name_the_user_chose",
        "opening_an_untitled_file_shows_its_file_name",
        "design_save_formats_reopen_and_preserve_atomic_backups",
    ]),
]

def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def log_file(path, title, args, result, elapsed):
    path.write_text(
        "TEST: " + title + "\nCOMMAND: " + " ".join(map(str, args))
        + "\nEXIT: " + str(result.returncode)
        + "\nDURATION_S: " + str(round(elapsed, 3)) + "\n\n"
        + result.stdout + "\n" + result.stderr,
        encoding="utf-8"
    )

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    source = Path(a.source).resolve()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    expected = sum(len(s[2]) for s in SUITES)
    report = {
        "test": 23, "official_pr": "tangency-labs/solidcraft#3891",
        "source": "CamWight/solidcraft", "expected_source_sha": PIN,
        "expected_cases": expected, "expected_suites": len(SUITES),
        "started_at": utc(), "suites": [], "pass": 0, "fail": 0, "missing": 0,
        "scope": "52 distinct native Rust tests: K3b drawing storage, records, IO, K4 drawing commands, undo, save/reopen; W13/W14/W19 E2E NOT_RUN"
    }
    try:
        head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                              text=True, capture_output=True, check=True, timeout=30).stdout.strip()
    except Exception as e:
        print(f"TEST22_PREFLIGHT_ERROR cannot obtain source revision: {e}", flush=True)
        return 2
    report["actual_source_sha"] = head
    (out / "source-commit.txt").write_text(head + "\n", encoding="utf-8")
    if head != PIN:
        (out / "preflight-error.txt").write_text(
            f"Source SHA mismatch expected {PIN} actual {head}\n", encoding="utf-8")
        print(f"TEST22_PREFLIGHT_ERROR SHA expected={PIN} actual={head}", flush=True)
        return 2
    binary_dir = source / "target" / "debug" / "deps"
    binaries = {}
    discovered = {}
    for crate in ("solidcraft_io", "solidcraft_doc", "solidcraft_engine"):
        candidates = sorted(binary_dir.glob(crate + "-*.exe"))
        if len(candidates) != 1:
            print(f"TEST22_PREFLIGHT_ERROR {crate}: expected one native test binary; got {len(candidates)}", flush=True)
            (out / ("binary-error-" + crate + ".txt")).write_text("\n".join(map(str, candidates)), encoding="utf-8")
            return 2
        binaries[crate] = candidates[0]
        listing = subprocess.run([str(candidates[0]), "--list"], cwd=source, text=True,
                                 encoding="utf-8", errors="replace",
                                 capture_output=True, timeout=90)
        (out / (crate + "-test-list.log")).write_text(
            listing.stdout + "\n" + listing.stderr, encoding="utf-8")
        if listing.returncode:
            print(f"TEST22_PREFLIGHT_ERROR {crate} test discovery exit={listing.returncode}", flush=True)
            return 2
        discovered[crate] = [line[:-6].strip() for line in listing.stdout.splitlines()
                            if line.rstrip().endswith(": test")]
    print(f"TEST22_BEGIN SHA={head} SUITES={len(SUITES)} CASES={expected}", flush=True)
    for suite, crate, names in SUITES:
        begin = time.monotonic()
        deadline = begin + LIMIT_SECONDS
        suite_dir = out / suite
        suite_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        print(f"TEST22_SUITE_BEGIN {suite} expected={len(names)}", flush=True)
        for n, name in enumerate(names, start=1):
            full = [s for s in discovered[crate] if s.rsplit("::", 1)[-1] == name]
            row = {"case": name, "test_name": full[0] if len(full) == 1 else None,
                   "status": "MISSING", "exit_code": None}
            if len(full) != 1:
                row["error"] = f"Expected one native Rust test, found {len(full)}"
            elif time.monotonic() >= deadline:
                row["status"] = "FAIL"
                row["error"] = "75-minute group deadline exceeded"
            else:
                args = [str(binaries[crate]), full[0], "--exact", "--nocapture"]
                t = time.monotonic()
                try:
                    result = subprocess.run(args, cwd=source, text=True,
                                            encoding="utf-8", errors="replace",
                                            capture_output=True,
                                            timeout=max(1, int(deadline - time.monotonic())))
                    row["exit_code"] = result.returncode
                    row["duration_s"] = round(time.monotonic() - t, 3)
                    log_file(suite_dir / f"{n:02d}.log", name, args, result, row["duration_s"])
                    found = re.search(r"(?m)^test " + re.escape(full[0]) + r" \.\.\. ok\s*$",
                                      result.stdout)
                    one = re.search(r"test result: ok\.\s+1 passed;\s+0 failed;", result.stdout)
                    if result.returncode == 0 and found and one:
                        row["status"] = "PASS"
                    else:
                        row["status"] = "FAIL"
                        row["error"] = "Native test missing ok line, failed, or nonzero exit; see raw log"
                except subprocess.TimeoutExpired as e:
                    row["status"] = "FAIL"
                    row["exit_code"] = -1
                    row["error"] = "Native test timeout"
                    (suite_dir / f"{n:02d}.log").write_text(
                        str(e.stdout or "") + "\n" + str(e.stderr or ""), encoding="utf-8")
                except Exception as e:
                    row["status"] = "FAIL"
                    row["exit_code"] = -1
                    row["error"] = str(e)
            rows.append(row)
            print(f"TEST22_CASE {suite} {name} {row['status']}", flush=True)
        passed = sum(x["status"] == "PASS" for x in rows)
        failed = sum(x["status"] == "FAIL" for x in rows)
        missing = sum(x["status"] == "MISSING" for x in rows)
        item = {"suite": suite, "source_crate": crate, "expected": len(names),
                "pass": passed, "fail": failed, "missing": missing, "cases": rows,
                "duration_s": round(time.monotonic()-begin, 3),
                "status": "PASS" if passed == len(names) else "FAIL"}
        report["suites"].append(item)
        report["pass"] += passed
        report["fail"] += failed
        report["missing"] += missing
        (suite_dir / "summary.json").write_text(json.dumps(item, indent=2), encoding="utf-8")
        print(f"TEST22_SUITE_END {suite} {item['status']} pass={passed} fail={failed} missing={missing}", flush=True)
    report["completed_at"] = utc()
    report["status"] = "PASS" if (report["pass"] == expected and
                                    report["fail"] == 0 and report["missing"] == 0) else "FAIL"
    (out / "aggregate-summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = ["# SolidCraft Test #23 - PR #3891 Drawing commands, persistence and undo", "",
          f"Result: **{report['status']}**, {report['pass']}/{expected} PASS; {report['fail']} FAIL; {report['missing']} MISSING.",
          f"Pinned source: CamWight/solidcraft@{head}", "",
          "| Suite | PASS | FAIL | MISSING |", "|---|---:|---:|---:|"]
    for s in report["suites"]:
        md.append(f"| {s['suite']} | {s['pass']} | {s['fail']} | {s['missing']} |")
    md += ["", "**NOT_RUN:** W13 geometry reference resolver, W14 automatic refresh, W19 dimensions and all A01-A10 3D->2D E2E acceptance tests.", "",
           "All executed native Rust test outputs are archived separately."]
    (out / "aggregate-summary.md").write_text("\n".join(md)+"\n", encoding="utf-8")
    print(f"TEST22_RESULT={report['status']} SUITES_PASS={sum(s['status']=='PASS' for s in report['suites'])}/{len(SUITES)} CASES_PASS={report['pass']}/{expected} CASES_FAIL={report['fail']} CASES_MISSING={report['missing']}", flush=True)
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
