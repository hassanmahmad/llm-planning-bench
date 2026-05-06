#!/usr/bin/env python3
"""Unit test for src/utils/metrics_extractor.py.

Ground truth: one known-valid plan (pddl_5_13) and one known-invalid plan
(pddl_10_1) from Project A's generated dataset. The expected metrics and
the plan text both come from the same CSV row so the test verifies our
extractor reproduces Project A's scoring byte-for-byte.

Note: we read the plan text from the CSV's `final_plan` column rather
than the _plan.txt files on disk — the on-disk files were overwritten by
a later run with different contents than what was scored in the CSV.
"""

from __future__ import annotations

import csv
import math
import re
import sys
from pathlib import Path

SRC = Path(__file__).parent.parent
sys.path.insert(0, str(SRC))

from utils.metrics_extractor import (  # noqa: E402
    extract_from_text,
    parse_val_output,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROJECT_A = PROJECT_ROOT / "merolasinghdardouri2425-master"
PROBLEMS = PROJECT_A / "problem_dataset" / "problems_blocksworlds" / "blocksworld"
CSV_PATH = (
    PROJECT_A
    / "generated_datasets_metamodel"
    / "blocksworld_generations_dataset_llama.csv"
)
DOMAIN = PROBLEMS / "blocksworld_domain.pddl"

ACTION_RE = re.compile(r"\([^()]+\)")


def _row(problem_name: str) -> dict:
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["problem"] == problem_name:
                return row
    raise LookupError(problem_name)


def _expected(row: dict) -> dict:
    return {
        "valid_action_percent": float(row["valid_action_percent"]),
        "consecutive_valid_steps": int(row["consecutive_valid_steps"]),
        "logical_violations": int(row["logical_violations"]),
        "plan_length": int(row["plan_len"]),
        "solves_problem": row["solves_problem"].strip().lower() == "true",
    }


def _plan_text(row: dict) -> str:
    return "\n".join(ACTION_RE.findall(row["final_plan"]))


def _run(problem_name: str) -> dict:
    row = _row(problem_name)
    problem_file = PROBLEMS / f"{problem_name}.pddl"
    return extract_from_text(str(DOMAIN), str(problem_file), _plan_text(row)), _expected(row)


def _assert_match(name: str, got: dict, expected: dict) -> None:
    assert got["solves_problem"] == expected["solves_problem"], (
        f"{name}: solves_problem {got['solves_problem']} != {expected['solves_problem']}"
    )
    assert got["plan_length"] == expected["plan_length"], (
        f"{name}: plan_length {got['plan_length']} != {expected['plan_length']}"
    )
    assert got["consecutive_valid_steps"] == expected["consecutive_valid_steps"], (
        f"{name}: consecutive_valid_steps {got['consecutive_valid_steps']} "
        f"!= {expected['consecutive_valid_steps']}"
    )
    assert got["logical_violations"] == expected["logical_violations"], (
        f"{name}: logical_violations {got['logical_violations']} "
        f"!= {expected['logical_violations']}"
    )
    assert math.isclose(
        got["valid_action_percent"], expected["valid_action_percent"], abs_tol=1e-6
    ), (
        f"{name}: valid_action_percent {got['valid_action_percent']} "
        f"!= {expected['valid_action_percent']}"
    )


def test_parse_val_output_valid_synthetic() -> None:
    """Parser-only test — does not require VAL to be installed."""
    sample = "\n".join(
        [
            "Checking plan: plan.txt",
            "Plan size: 3",
            "Checking next happening (time 1)",
            "Checking next happening (time 2)",
            "Checking next happening (time 3)",
            "Plan executed successfully - checking goal",
            "Plan valid",
        ]
    )
    got = parse_val_output(sample)
    assert got == {
        "valid_action_percent": 100.0,
        "consecutive_valid_steps": 3,
        "logical_violations": 0,
        "plan_length": 3,
        "solves_problem": True,
    }, got


def test_parse_val_output_invalid_synthetic() -> None:
    sample = "\n".join(
        [
            "Plan size: 5",
            "Checking next happening (time 1)",
            "Checking next happening (time 2)",
            "(action_x) has an unsatisfied precondition at time 2",
            "Plan failed to execute",
        ]
    )
    got = parse_val_output(sample)
    assert got["plan_length"] == 5
    assert got["consecutive_valid_steps"] == 2
    assert got["logical_violations"] == 2
    assert got["solves_problem"] is False
    assert math.isclose(got["valid_action_percent"], 40.0)


def test_known_valid_plan() -> None:
    """pddl_5_13: solved → 100% valid actions, 10 steps, 0 violations."""
    got, expected = _run("pddl_5_13")
    _assert_match("pddl_5_13", got, expected)


def test_known_invalid_plan() -> None:
    """pddl_10_1: unsolved → 2 of 24 actions valid, 3 logical violations."""
    got, expected = _run("pddl_10_1")
    _assert_match("pddl_10_1", got, expected)


def main() -> int:
    print("Testing metrics_extractor")
    print("=" * 50)

    synth_tests = [
        ("parse_val_output (valid synthetic)", test_parse_val_output_valid_synthetic),
        ("parse_val_output (invalid synthetic)", test_parse_val_output_invalid_synthetic),
    ]
    val_tests = [
        ("pddl_5_13 (known valid)", test_known_valid_plan),
        ("pddl_10_1 (known invalid)", test_known_invalid_plan),
    ]

    failed = 0
    for name, fn in synth_tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")

    if not CSV_PATH.exists():
        print(f"  SKIP  VAL-ground-truth tests (CSV not found at {CSV_PATH})")
        return 1 if failed else 0

    for name, fn in val_tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except FileNotFoundError as e:
            print(f"  SKIP  {name}: VAL or fixture missing ({e})")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")

    print("=" * 50)
    print(f"{'All tests passed' if not failed else f'{failed} test(s) failed'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
