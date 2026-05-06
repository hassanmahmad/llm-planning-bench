#!/usr/bin/env python3
"""Unit test for src/utils/run_recorder.py.

Asserts the contract the iteration loop relies on:
- record_iter writes <instance>_iter_<k>.txt with verbatim plan text
- record_iter appends a row to run_metrics.csv with the 14-column
  schema; header is written exactly once even across multiple appends
- finalize writes <instance>_plan.txt with Project B's
  `--- Processing Metadata ---` block, including First Valid Iteration
  (or 'null' on exhaustion) and the new Model field
"""

import csv
import shutil
import sys
import tempfile
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils.run_recorder import CSV_COLUMNS, RunRecorder


VALID_METRICS = {
    "plan_length": 3,
    "solves_problem": True,
    "valid_action_percent": 100.0,
    "consecutive_valid_steps": 3,
    "logical_violations": 0,
}

PARTIAL_METRICS = {
    "plan_length": 4,
    "solves_problem": False,
    "valid_action_percent": 50.0,
    "consecutive_valid_steps": 2,
    "logical_violations": 1,
}


def _new_recorder(tmp: Path, **overrides) -> RunRecorder:
    kwargs = dict(
        output_dir=tmp,
        model="stub",
        domain="blocksworld",
        condition="baseline",
        instance="instance-01",
    )
    kwargs.update(overrides)
    return RunRecorder(**kwargs)


def test_record_iter_writes_per_iter_file():
    tmp = Path(tempfile.mkdtemp(prefix="recorder_test_"))
    try:
        recorder = _new_recorder(tmp)
        plan = "(pickup b1)\n(stack b1 b2)\n(pickup b3)"
        recorder.record_iter(
            iteration=1,
            plan_text=plan,
            metrics=VALID_METRICS,
            wallclock_s=0.5,
            prompt_tokens=42,
            completion_tokens=17,
        )
        iter_file = tmp / "instance-01_iter_1.txt"
        assert iter_file.exists(), f"per-iter file missing: {iter_file}"
        assert iter_file.read_text(encoding="utf-8") == plan, (
            "per-iter file content drifted from plan_text"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_csv_header_written_once_with_full_schema():
    tmp = Path(tempfile.mkdtemp(prefix="recorder_test_"))
    try:
        recorder = _new_recorder(tmp)
        for k in (1, 2):
            recorder.record_iter(
                iteration=k,
                plan_text=f"(act_{k})",
                metrics=PARTIAL_METRICS,
                wallclock_s=0.1 * k,
                prompt_tokens=k,
                completion_tokens=k * 2,
            )
        with open(recorder.csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2, f"expected 2 rows, got {len(rows)}"
        assert list(rows[0].keys()) == CSV_COLUMNS, (
            f"CSV schema drift: {list(rows[0].keys())} vs {CSV_COLUMNS}"
        )
        # First row must reflect iter=1 inputs
        assert rows[0]["model"] == "stub"
        assert rows[0]["prompting_condition"] == "baseline"
        assert rows[0]["instance"] == "instance-01"
        assert rows[0]["iteration"] == "1"
        assert rows[0]["plan_len"] == "4"
        assert rows[0]["solves_problem"] == "False"
        assert rows[0]["wallclock_s"] == "0.100"
        assert rows[0]["prompt_tokens"] == "1"
        assert rows[0]["completion_tokens"] == "2"
        # Header line should appear only once even with multiple appends
        with open(recorder.csv_path, encoding="utf-8") as f:
            header_count = sum(1 for line in f if line.startswith("model,"))
        assert header_count == 1, f"header appears {header_count}x, expected 1"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_finalize_success_metadata():
    tmp = Path(tempfile.mkdtemp(prefix="recorder_test_"))
    try:
        recorder = _new_recorder(tmp)
        plan = "(pickup b1)\n(putdown b1)"
        recorder.finalize(plan_text=plan, first_valid_iter=2, total_iterations=2)
        body = recorder.final_plan_path.read_text(encoding="utf-8")
        for required in (
            "(pickup b1)",
            "--- Processing Metadata ---",
            "Domain: blocksworld",
            "Problem: instance-01",
            "Iterations: 2",
            "Plan Valid: True",
            "Condition: baseline",
            "Model: stub",
            "First Valid Iteration: 2",
        ):
            assert required in body, f"missing: {required!r}\nbody:\n{body}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_finalize_exhaustion_metadata_uses_null():
    tmp = Path(tempfile.mkdtemp(prefix="recorder_test_"))
    try:
        recorder = _new_recorder(tmp, condition="cot")
        recorder.finalize(plan_text="(act_x)", first_valid_iter=None, total_iterations=4)
        body = recorder.final_plan_path.read_text(encoding="utf-8")
        assert "Plan Valid: False" in body
        assert "Iterations: 4" in body
        assert "Condition: cot" in body
        assert "First Valid Iteration: null" in body, (
            "exhaustion path must record `null` (not 'None') for First Valid Iteration"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_token_counts_omitted_when_none():
    """Stub model passes prompt/completion_tokens=None → CSV cells should be empty."""
    tmp = Path(tempfile.mkdtemp(prefix="recorder_test_"))
    try:
        recorder = _new_recorder(tmp)
        recorder.record_iter(
            iteration=1,
            plan_text="(act)",
            metrics=PARTIAL_METRICS,
            wallclock_s=None,
            prompt_tokens=None,
            completion_tokens=None,
        )
        with open(recorder.csv_path, encoding="utf-8") as f:
            row = next(csv.DictReader(f))
        assert row["wallclock_s"] == ""
        assert row["prompt_tokens"] == ""
        assert row["completion_tokens"] == ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    tests = [
        ("record_iter writes per-iter file", test_record_iter_writes_per_iter_file),
        ("CSV header written once with full schema", test_csv_header_written_once_with_full_schema),
        ("finalize (success) metadata block", test_finalize_success_metadata),
        ("finalize (exhaustion) uses null for First Valid Iteration", test_finalize_exhaustion_metadata_uses_null),
        ("None token counts -> empty CSV cells", test_token_counts_omitted_when_none),
    ]
    print("Testing run_recorder")
    print("=" * 50)
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
    print("=" * 50)
    print(f"{'All tests passed' if not failed else f'{failed} test(s) failed'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
