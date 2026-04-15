"""VAL-verbose metrics extractor.

Ports run_val_verbose + parse_val_output from Project A's
utils/dataset_generator.py (L23-63), stripped of all meta-network
coupling. Pure parser + subprocess wrapper; no filesystem side effects
beyond the subprocess call and optional tempfile for text input.

See STEPS.md §1.1.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Dict, Optional

try:
    from .validator import get_val_executable
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.validator import get_val_executable


def run_val_verbose(
    domain_file: str,
    problem_file: str,
    plan_file: str,
    val_executable: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """Run VAL with -v on (domain, problem, plan) and return stdout."""
    if val_executable is None:
        val_executable = get_val_executable()
    result = subprocess.run(
        [val_executable, "-v", domain_file, problem_file, plan_file],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout


def parse_val_output(val_output: str) -> Dict:
    """Parse VAL -v stdout into the metrics schema used by run_metrics.csv."""
    plan_length = 0
    valid_steps = 0
    logical_violations = 0
    solves_problem = False
    for line in val_output.split("\n"):
        if line.startswith("Plan size:"):
            plan_length = int(line.split(":")[1].strip())
        if line.startswith("Checking next happening"):
            valid_steps += 1
        if "unsatisfied precondition" in line or "Plan failed" in line:
            logical_violations += 1
        if "Plan valid" in line:
            solves_problem = True
    valid_action_percent = (
        100.0 * valid_steps / plan_length if plan_length > 0 else 0.0
    )
    return {
        "valid_action_percent": valid_action_percent,
        "consecutive_valid_steps": valid_steps,
        "logical_violations": logical_violations,
        "plan_length": plan_length,
        "solves_problem": solves_problem,
    }


def extract(
    domain_path: str,
    problem_path: str,
    plan_path: str,
    val_executable: Optional[str] = None,
    timeout: int = 300,
) -> Dict:
    """End-to-end: run VAL verbose on a plan file, return parsed metrics."""
    return parse_val_output(
        run_val_verbose(domain_path, problem_path, plan_path, val_executable, timeout)
    )


def extract_from_text(
    domain_path: str,
    problem_path: str,
    plan_text: str,
    val_executable: Optional[str] = None,
    timeout: int = 300,
) -> Dict:
    """Run VAL verbose on plan text via a temp file.

    Keeps only PDDL action lines (those starting with '(') and comment
    lines, so trailing metadata like 'Generated in N iterations.' does
    not poison the VAL parse.
    """
    kept = [
        line for line in plan_text.splitlines()
        if not line.strip() or line.lstrip().startswith(("(", ";"))
    ]
    cleaned = "\n".join(kept)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".plan", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(cleaned)
        tmp_path = tmp.name
    try:
        return extract(domain_path, problem_path, tmp_path, val_executable, timeout)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
