#!/usr/bin/env python3
"""Test #24: 122 real native Drawing storage, commands and 2D geometry tests on PR #3891.

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
    ("geom_drawing_sheet_native", "solidcraft_geom", [
            "every_size_is_its_published_millimetres",
            "landscape_is_the_default_and_either_orientation_turns_every_size",
            "a3_landscape_has_a_400_by_277_drawing_border_and_8_by_6_fields",
            "a3_landscape_has_a_grid_border_and_centring_marks_across_the_margin",
            "a3_landscape_with_iso_5457s_full_border_has_its_filing_margin_and_every_mark",
            "every_sheet_has_centring_marks_on_its_centre_lines_and_trimming_marks_only_when_asked",
            "the_filing_margin_puts_20_mm_on_the_left_of_every_sheet",
            "the_iso_rule_gives_the_standard_field_counts_for_a0_to_a4_either_way",
            "one_iso_profile_labels_a4_on_its_top_and_right_and_every_other_size_all_round",
            "an_equal_division_cuts_the_drawing_border_evenly",
            "rows_skip_i_and_o_and_letters_go_on_past_z",
            "hostile_sizes_and_profiles_are_refused",
            "names_round_trip_and_unknown_fields_are_refused",
            "fields_tile_every_drawing_border_exactly",
            "rounding_past_a_whole_number_of_fields_leaves_no_sliver"
    ]),
    ("geom_paper_native", "solidcraft_geom", [
            "an_a3_drawing_border_and_its_trimming_marks_validate_and_round_trip",
            "each_kind_names_its_layer_in_the_capitals_of_its_id",
            "each_side_of_the_sheet_is_above_zero_and_at_most_5000_mm",
            "a_line_is_above_zero_and_at_most_10_mm_wide",
            "coordinates_and_radii_are_finite_and_at_most_1e5_mm",
            "every_piece_goes_through_the_section_checks_at_the_papers_bound",
            "a_strokes_pieces_meet_within_1e_9_mm_and_a_closed_one_ends_where_it_starts",
            "stroke_shapes_one_piece_reversed_duplicated_and_doubled_back",
            "every_loop_of_a_fill_is_closed_within_1e_9_mm",
            "at_most_100_000_records_are_counted_before_any_geometry",
            "unknown_fields_kinds_and_ids_are_refused_when_read"
    ]),
    ("geom_section_native", "solidcraft_geom", [
            "section_frame_preserves_named_translated_tilted_offset_and_flip_conventions",
            "strict_frame_validation_does_not_repair_raw_or_deserialized_axes",
            "line_arc_region_conversion_preserves_winding_and_analytic_area",
            "empty_contacts_and_open_wires_remain_distinct_without_inferred_material",
            "bad_references_empty_disconnected_and_unclosed_wires_fail",
            "duplicate_boundaries_are_local_to_a_region_and_large_reference_tables_are_bounded",
            "aggregate_counts_fail_before_geometry_or_reference_inspection",
            "closure_tolerance_is_bounded_and_not_used_to_collapse_short_curves",
            "curve_number_and_domain_errors_are_rejected_before_evaluation",
            "bezier_degree_and_every_serialized_control_slot_are_validated",
            "supported_curve_limits_keep_evaluation_finite_without_claiming_accuracy",
            "transient_serialization_preserves_accuracy_tags_and_plane_names",
            "accuracy_values_are_validated_without_promoting_zero_sampled_error",
            "conversion_revalidates_mutated_data_and_does_not_trust_an_earlier_success",
            "reversed_large_arc_conversion_rechecks_actual_connectivity_without_snapping",
            "connected_bow_tie_and_wrong_winding_are_not_certified_or_silently_repaired",
            "an_accuracy_scales_with_its_curve"
    ]),
    ("geom_title_block_native", "solidcraft_geom", [
            "the_default_geometry_validates_and_its_cells_tile_the_block",
            "on_a3_landscape_the_block_sits_on_the_drawing_borders_lower_right_corner",
            "the_padding_starts_at_the_lines_inner_edge",
            "a_drawing_border_line_wider_than_the_outline_pads_the_right_and_bottom_cells",
            "a_cells_room_is_checked_again_where_the_block_sits",
            "the_block_follows_the_drawing_border_on_a2_and_a4",
            "a5_landscape_holds_the_block_and_a5_portrait_is_too_narrow",
            "on_every_sheet_each_cell_keeps_its_place_from_the_corner",
            "the_wrapped_cells_hold_the_lines_the_plan_gives_them",
            "hostile_definitions_are_refused",
            "a_block_round_trips_through_json_and_unknown_fields_are_refused",
            "a_drawing_border_that_isnt_finite_holds_no_block",
            "fuzzed_definitions_never_panic_and_an_accepted_one_lays_out_inside_its_outline"
    ]),
    ("geom_hlr_native", "solidcraft_geom", [
            "iso_cube_hides_the_three_back_edges",
            "a_box_in_front_hides_the_middle_of_an_edge",
            "a_cylinder_seen_from_the_side_has_exact_silhouette_lines",
            "a_sphere_outline_is_exact_conic_arcs_in_any_view",
            "every_hole_of_a_plate_hides_the_same_part_of_its_bottom_circle",
            "coaxial_cylinders_seen_along_their_axis_draw_one_circle"
    ]),
    ("geom_drawing_view_native", "solidcraft_geom", [
            "each_named_view_looks_from_where_its_name_says",
            "a_view_from_a_direction_and_up_matches_the_named_views",
            "an_up_just_off_the_direction_still_looks_along_it",
            "a_50_mm_cube_measures_as_the_views_say",
            "the_views_centre_lands_on_its_position",
            "a_scale_reads_and_writes_as_paper_to_model",
            "the_fitted_scale_is_the_largest_preset_that_fits",
            "a_frame_refuses_hostile_input"
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
        "test": 24, "official_pr": "tangency-labs/solidcraft#3891",
        "source": "CamWight/solidcraft", "expected_source_sha": PIN,
        "expected_cases": expected, "expected_suites": len(SUITES),
        "started_at": utc(), "suites": [], "pass": 0, "fail": 0, "missing": 0,
        "scope": "122 native Rust tests: 52 drawing persistence/commands/undo + 70 geometry/views/sheets/HLR. 3D->2D W13/W14/W19 E2E NOT_RUN"
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
    for crate in ("solidcraft_io", "solidcraft_doc", "solidcraft_engine", "solidcraft_geom"):
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
    md = ["# SolidCraft Test #24 - PR #3891 Drawing commands, persistence, view geometry and HLR", "",
          f"Result: **{report['status']}**, {report['pass']}/{expected} PASS; {report['fail']} FAIL; {report['missing']} MISSING.",
          f"Pinned source: CamWight/solidcraft@{head}", "",
          "| Suite | PASS | FAIL | MISSING |", "|---|---:|---:|---:|"]
    for s in report["suites"]:
        md.append(f"| {s['suite']} | {s['pass']} | {s['fail']} | {s['missing']} |")
    md += ["", "**NOT_RUN:** W13 geometry reference resolver, W14 automatic refresh, W19 dimensions and all A01-A10 3D->2D E2E acceptance tests.", "",
           "All executed native Rust test outputs are archived separately."]
    (out / "aggregate-summary.md").write_text("\n".join(md)+"\n", encoding="utf-8")
    print(f"TEST24_RESULT={report['status']} SUITES_PASS={sum(s['status']=='PASS' for s in report['suites'])}/{len(SUITES)} CASES_PASS={report['pass']}/{expected} CASES_FAIL={report['fail']} CASES_MISSING={report['missing']}", flush=True)
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
