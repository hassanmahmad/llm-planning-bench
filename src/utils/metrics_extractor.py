"""VAL-verbose metrics parser.

`parse_val_output` is ported from Project A's utils/dataset_generator.py
(L38-63), stripped of all meta-network coupling, and left as a pure
function.

After STEPS.md §1.3 the VAL subprocess call lives in
`utils.validator.validate_plan_verbose` — this module only composes
that helper with the parser. See STEPS.md §1.1 for the port and §1.3
for the validator unification.
"""

from __future__ import annotations

from typing import Dict

try:
    from .validator import validate_plan_verbose
except ImportError:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.utils.validator import validate_plan_verbose


ZERO_METRICS: Dict = {
    "plan_length": 0,
    "solves_problem": False,
    "valid_action_percent": 0.0,
    "consecutive_valid_steps": 0,
    "logical_violations": 0,
}


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


def extract_from_text(
    domain_path: str,
    problem_path: str,
    plan_text: str,
) -> Dict:
    """Run VAL -v via the unified validator, return parsed metrics."""
    _is_valid, raw = validate_plan_verbose(domain_path, problem_path, plan_text)
    return parse_val_output(raw)
