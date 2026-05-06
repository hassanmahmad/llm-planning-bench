#!/usr/bin/env python3
"""Verify VAL validator integration.

Covers:
- VAL executable detection / `--help` smoke.
- The canonical `validate_plan_verbose`: contract is
  `(is_valid, raw_stdout)`; raw stdout must be parsable by
  `metrics_extractor.parse_val_output`.
- Legacy `validate_plan_from_text` — still in place for backwards
  compatibility, but no production caller goes through it anymore.
"""

import subprocess
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils.configuration import load_config
from utils.metrics_extractor import parse_val_output
from utils.validator import (
    get_val_executable,
    validate_plan_from_text,
    validate_plan_verbose,
)


def test_val_integration():
    print("Testing VAL Validator Integration")
    print("=" * 50)

    # --- 1. Configuration loading -------------------------------------
    try:
        config = load_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        return False
    print("VAL Configuration:")
    print(f"  VAL_PATH: {config.get('VAL_PATH')}")
    print(f"  VAL_EXECUTABLE: {config.get('VAL_EXECUTABLE')}")
    print(f"  VAL_TIMEOUT: {config.get('VAL_TIMEOUT')}")

    # --- 2. Executable detection --------------------------------------
    val_exec_path = get_val_executable()
    print(f"\nVAL Executable Detection:")
    print(f"  Detected path: {val_exec_path}")
    val_present = Path(val_exec_path).exists()
    print(f"  Status: {'Found' if val_present else 'Not found (will try system PATH)'}")

    # --- 3. --help smoke ---------------------------------------------
    print(f"\nVAL Executable Test:")
    try:
        result = subprocess.run(
            [val_exec_path, "--help"], capture_output=True, text=True, timeout=10
        )
        # VAL's --help may exit non-zero; success is "we got SOME output".
        if result.stdout or "usage" in (result.stdout + result.stderr).lower():
            print(f"  VAL executable responds")
            print(f"  Help output sample: {(result.stdout or result.stderr)[:100]}...")
        else:
            print(f"  VAL executable returned no output (rc={result.returncode})")
    except subprocess.TimeoutExpired:
        print("  VAL executable timeout (10s)")
    except FileNotFoundError:
        print(f"  VAL executable not found at: {val_exec_path}")
        return False

    # --- 4. Sample-domain validation ----------------------------------
    print(f"\nSample Domain Check:")
    project_root = src_path.parent
    tetris_domain = project_root / "src/data/tetris/tetris_domain.pddl"
    tetris_problem = project_root / "src/data/tetris/instance-01.pddl"

    if not (tetris_domain.exists() and tetris_problem.exists()):
        print("  No tetris fixture available — skipping sample validation")
        print(f"    Domain exists: {tetris_domain.exists()}")
        print(f"    Problem exists: {tetris_problem.exists()}")
        return True

    sample_plan = "(move_square pos1 pos2 piece1)"  # garbage, expected invalid

    # 4a. canonical validator
    print(f"\n  validate_plan_verbose (canonical):")
    is_valid, raw = validate_plan_verbose(
        str(tetris_domain), str(tetris_problem), sample_plan
    )
    print(f"    is_valid: {is_valid}")
    print(f"    raw stdout length: {len(raw)} chars")
    metrics = parse_val_output(raw)
    print(f"    parsed metrics: {metrics}")
    assert isinstance(is_valid, bool), "is_valid must be a bool"
    assert isinstance(raw, str), "raw stdout must be a str"
    assert set(metrics) == {
        "valid_action_percent",
        "consecutive_valid_steps",
        "logical_violations",
        "plan_length",
        "solves_problem",
    }, f"unexpected metrics keys: {set(metrics)}"

    # 4b. legacy wrapper (still callable, no production caller now)
    print(f"\n  validate_plan_from_text (legacy):")
    legacy = validate_plan_from_text(str(tetris_domain), str(tetris_problem), sample_plan)
    print(f"    valid: {legacy.get('valid')}")
    print(f"    error head: {(legacy.get('error') or '')[:80]!r}")
    assert "valid" in legacy and "error" in legacy, (
        "legacy validate_plan_from_text contract changed"
    )

    print(f"\nVAL Integration test completed!")
    return True


if __name__ == "__main__":
    success = test_val_integration()
    if success:
        print("\nVAL validator is ready for use!")
        print("Canonical entry point: utils.validator.validate_plan_verbose")
    else:
        print("\nVAL integration needs attention.")
    sys.exit(0 if success else 1)
