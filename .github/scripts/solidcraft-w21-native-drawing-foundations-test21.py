#!/usr/bin/env python3
"""Test 21: 62 distinct upstream Rust tests for drawing foundations.

Unlike emulated "checks", these are the actual upstream Rust test functions:
  15 drawing sheet + 11 paper geometry + 17 section geometry + 13 title block
  + 6 visible/hidden-line calculations = 62 NEW cases.
The prior W17a eight native tests and 54 model CLI cases stay in the batch.
This is NOT the as-yet-unimplemented associative W13/W14 drawing refresh.
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

MODULE_CASES = {
" drawing_sheet".strip(): (
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
"rounding_past_a_whole_number_of_fields_leaves_no_sliver",
),
"paper": (
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
"unknown_fields_kinds_and_ids_are_refused_when_read",
),
"section": (
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
"an_accuracy_scales_with_its_curve",
),
"title_block": (
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
"fuzzed_definitions_never_panic_and_an_accepted_one_lays_out_inside_its_outline",
),
}
HLR_CASES = (
"iso_cube_hides_the_three_back_edges",
"a_box_in_front_hides_the_middle_of_an_edge",
"a_cylinder_seen_from_the_side_has_exact_silhouette_lines",
"a_sphere_outline_is_exact_conic_arcs_in_any_view",
"every_hole_of_a_plate_hides_the_same_part_of_its_bottom_circle",
"coaxial_cylinders_seen_along_their_axis_draw_one_circle",
)
PIN="ebafe07487df5cdd108e091db939de765645e5eb"
BASE=["cargo","test","--locked","-p","solidcraft-geom","--lib"]
LOG_PATTERN=re.compile(r"^test ([a-z0-9_]+::tests::([a-zA-Z0-9_]+)) \.\.\. (ok|FAILED|ignored)$")

def run_command(source,folder,label,argv):
    started=time.monotonic()
    env=os.environ.copy()
    env["CARGO_INCREMENTAL"]="0"
    env["CARGO_TERM_COLOR"]="never"
    p=subprocess.run(argv,cwd=source,env=env,capture_output=True,
                     text=True,encoding="utf-8",errors="replace")
    (folder/(label+".log")).write_text(
        f"COMMAND: {' '.join(argv)}\nEXIT: {p.returncode}\nDURATION_SEC: {time.monotonic()-started:.3f}\n"
        f"STDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}",encoding="utf-8")
    return p

def main():
    parser=argparse.ArgumentParser()
    for arg in ("--cli","--source","--out"):parser.add_argument(arg,required=True)
    args=parser.parse_args()
    source=Path(args.source).resolve()
    out=Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=True)

    groups={k+"::tests::":tuple(v) for k,v in MODULE_CASES.items()}
    groups["hlr::tests::"]=HLR_CASES
    expected={prefix+n for prefix,names in groups.items() for n in names}
    assert len(expected)==62, f"Expected exactly 62 distinct real drawing Rust tests, got {len(expected)}"
    report={"source":PIN,"scope":"62 REAL native drawing sheet/paper/section/title block/HLR tests, not W13/W14 updates",
            "expected":62,"groups":{k:len(v) for k,v in groups.items()},
            "scenarios":{},"failed":0,"status":"FAIL"}
    for fullname in sorted(expected):
        report["scenarios"][fullname]={"status":"FAIL","error":"Not executed or did not finish successfully"}

    try:
        for candidate in ("drawing_sheet_tests.rs","paper_tests.rs",
                          "section_tests.rs","title_block_tests.rs","hlr_tests.rs"):
            assert (source/"crates"/"geom"/"src"/candidate).is_file(), (
                f"Official geometry native Rust fixture missing: {candidate}")
        listing=run_command(source,out,"native-discovery",BASE+["--","--list"])
        assert listing.returncode==0,f"Failed compiling/discovering Rust native tests: exit {listing.returncode}"
        available=set()
        for line in listing.stdout.splitlines():
            match=re.fullmatch(r"([a-zA-Z_0-9:]+): test",line.strip())
            if match:available.add(match.group(1))
        missing=expected-available
        assert not missing,f"Expected native drawing tests absent from compiled official source: {sorted(missing)}"
        for prefix,names in groups.items():
            wanted={prefix+n for n in names}
            if prefix!="hlr::tests::":
                runnable=sorted(x for x in available if x.startswith(prefix))
                assert set(runnable)==wanted, (
                    f"Native module {prefix} differs from fixed test list; extra/missing: "
                    f"{sorted(set(runnable)^wanted)}")
                runs=[(prefix.replace(":","_"),BASE+[prefix,"--","--nocapture"],wanted)]
            else:
                runs=[("hlr_"+n, BASE+[prefix+n,"--","--exact","--nocapture"],
                       {prefix+n}) for n in names]

            for label,argv,subset in runs:
                executed=run_command(source,out,label,argv)
                raw=executed.stdout+"\n"+executed.stderr
                statuses={}
                for row in raw.splitlines():
                    match=LOG_PATTERN.fullmatch(row.strip())
                    if match:statuses[match.group(1)]=match.group(3)
                actual=set(statuses)
                assert actual==subset, (
                    f"Module {label}: expected exactly {sorted(subset)}, saw {sorted(actual)}; "
                    f"exit={executed.returncode}")
                if executed.returncode:
                    raise AssertionError(f"Native suite {label}: exit {executed.returncode}")
                for fullname in subset:
                    assert statuses[fullname]=="ok", (
                        f"Native {fullname} status {statuses[fullname]} instead of ok")
                    report["scenarios"][fullname]={"status":"PASS",
                      "evidence":f"native Rust cargo test, {label}.log"}
                print(f"PASS native_{label}: {len(subset)} real Rust drawing tests",flush=True)
    except Exception as e:
        report["execution_error"]=str(e)
        report["traceback"]=traceback.format_exc()
        print(f"NATIVE_DRAWING_FAILURE: {e}",file=sys.stderr,flush=True)
    report["failed"]=sum(x["status"]!="PASS" for x in report["scenarios"].values())
    report["status"]="PASS" if report["failed"]==0 else "FAIL"
    (out/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"W21_NATIVE_DRAWING_CASES=62 PASS={62-report['failed']} "
          f"FAILED_CHECKS={report['failed']}",flush=True)
    return 0 if report["status"]=="PASS" else 1

if __name__=="__main__":
    sys.exit(main())
