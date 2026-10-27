#!/usr/bin/env python3
"""Executable W23a source-design identity regression, not a Drawing W13/W14 test."""
import argparse
import json
import pathlib
import subprocess
import sys
import traceback


def run_process(argv, cwd, log_path):
    proc = subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8",
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, errors="replace")
    log_path.write_text(
        "COMMAND: " + " ".join(map(str, argv)) + "\n"
        + "EXIT: " + str(proc.returncode) + "\n\nSTDOUT:\n"
        + proc.stdout + "\nSTDERR:\n" + proc.stderr, encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"Exit {proc.returncode}: see {log_path}")
    return proc.stdout


def cmd(name, params=None):
    return {"command": name, "params": params or {}}


def state(value, label):
    if not isinstance(value, dict) or not isinstance(value.get("timeline"), list):
        raise AssertionError(f"{label}: document.inspect did not return a timeline")
    ids = {}
    for row in value["timeline"]:
        assert row.get("error") in (None, ""), f"{label}: feature error {row}"
        if row.get("name") in ("Stock", "Bore1", "Bore2"):
            name = row["name"]
            assert name not in ids, f"{label}: duplicate {name}"
            assert isinstance(row.get("id"), int), f"{label}: no numeric id {name}"
            ids[name] = row["id"]
    params = {r.get("name"): r.get("expression") for r in value.get("params", [])}
    return {"ids": ids, "params": params, "undo": value.get("undo"), "redo": value.get("redo")}


def compare(label, base, other, expected):
    for name in ("Stock", "Bore1", "Bore2"):
        exists = name == "Stock" or name in expected
        if exists:
            assert name in other["ids"], f"{label}: missing {name}"
            assert base["ids"].get(name) == other["ids"][name], (
                f"{label}: {name} ID changed {base['ids'].get(name)} -> {other['ids'][name]}")
        else:
            assert name not in other["ids"], f"{label}: {name} should be deleted"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    opts = parser.parse_args()
    source = pathlib.Path(opts.source).resolve()
    out = pathlib.Path(opts.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    exe = pathlib.Path(opts.cli).resolve()
    recipe = source / "tests/oracle/84-plate-two-bores/recipe.json"
    if not exe.is_file() or not recipe.is_file():
        raise RuntimeError(f"Missing pinned CLI or W23a case 84: {exe}, {recipe}")
    converted = run_process([str(exe), "recipe", str(recipe)], source, out / "00-recipe.log")
    commands = json.loads(converted).get("commands")
    assert isinstance(commands, list) and len(commands) > 3
    assert sum(1 for row in commands if row.get("command") == "solid.hole") == 2
    cases = {
        "width_80_to_100": (
            cmd("parameters.change", {"name": "width", "expression": "100 mm"}),
            ("Bore1", "Bore2"), {"width": "100 mm"}),
        "bore1_10_to_12": (
            cmd("parameters.change", {"name": "bore1_d", "expression": "12 mm"}),
            ("Bore1", "Bore2"), {"bore1_d": "12 mm"}),
        "delete_bore1": (cmd("timeline.delete", {"feature": "Bore1"}), ("Bore2",), {}),
    }
    summary = {"purpose": "3D source-design in-session feature identities; not W13/W14",
               "source": "tangency-labs/solidcraft@ebafe07487df5cdd108e091db939de765645e5eb",
               "fixture": "84-plate-two-bores", "cases": {}, "failed": 0}
    for label, (change, exists, expected_params) in cases.items():
        steps = list(commands)
        marks = []
        for extra in (cmd("document.inspect"), change, cmd("document.inspect"),
                      cmd("edit.undo"), cmd("document.inspect"),
                      cmd("edit.redo"), cmd("document.inspect")):
            steps.append(extra)
            if extra["command"] == "document.inspect":
                marks.append(len(steps)-1)
        path = out / (label + "-script.json")
        path.write_text(json.dumps({"commands": steps}, indent=2, ensure_ascii=False), encoding="utf-8")
        dest = out / (label + "-results.json")
        try:
            run_process([str(exe), "run", str(path), "--results", "--json-out", str(dest)],
                        source, out / (label + ".log"))
            responses = json.loads(dest.read_text(encoding="utf-8"))
            assert len(responses) == len(steps), f"{label}: incomplete results"
            before, after, undone, redone = (
                state(responses[index], label)
                for index in marks
            )
            compare(label+"/baseline", before, before, ("Bore1", "Bore2"))
            compare(label+"/changed", before, after, exists)
            compare(label+"/undo", before, undone, ("Bore1", "Bore2"))
            compare(label+"/redo", before, redone, exists)
            for name, expected in expected_params.items():
                assert after["params"].get(name) == expected, f"{label}: changed {name} mismatch"
                assert redone["params"].get(name) == expected, f"{label}: redo {name} mismatch"
                assert undone["params"].get(name) == before["params"].get(name), f"{label}: undo {name} mismatch"
            summary["cases"][label] = {"status": "PASS", "baseline": before, "edit": after,
                                        "undo": undone, "redo": redone}
            print(f"PASS {label} (actual edit, feature identities, undo/redo)", flush=True)
        except Exception as ex:
            summary["cases"][label] = {"status": "FAIL", "error": str(ex), "traceback": traceback.format_exc()}
            summary["failed"] += 1
            print(f"FAIL {label}: {ex}", file=sys.stderr, flush=True)
    summary["status"] = "PASS" if summary["failed"] == 0 else "FAIL"
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"W23A_CASES={len(cases)} FAILED_CHECKS={summary['failed']}", flush=True)
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
