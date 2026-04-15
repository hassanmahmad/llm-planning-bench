"""Per-run artifact recorder for the iterative planning loop.

Owns the three disk artifacts produced by a single (model, domain,
condition, instance) run:

* `<output_dir>/<instance>_iter_<k>.txt` — plan text at each iteration
* `<output_dir>/run_metrics.csv` — one row per iteration; columns per STEPS.md §1.2
* `<output_dir>/<instance>_plan.txt` — final plan + Project B's
  `--- Processing Metadata ---` block (including `first_valid_iter`)

The CSV header is written lazily on first append so multiple instances
sharing one cell directory all contribute to the same file.
"""

from __future__ import annotations

import csv
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

CSV_COLUMNS = [
    "model",
    "domain",
    "prompting_condition",
    "instance",
    "iteration",
    "plan_text",
    "plan_len",
    "solves_problem",
    "valid_action_percent",
    "consecutive_valid_steps",
    "logical_violations",
    "wallclock_s",
    "prompt_tokens",
    "completion_tokens",
]

_CSV_LOCK = threading.Lock()


@dataclass
class RunRecorder:
    output_dir: Path
    model: str
    domain: str
    condition: str
    instance: str
    _finalized: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def csv_path(self) -> Path:
        return self.output_dir / "run_metrics.csv"

    @property
    def final_plan_path(self) -> Path:
        return self.output_dir / f"{self.instance}_plan.txt"

    def iter_plan_path(self, iteration: int) -> Path:
        return self.output_dir / f"{self.instance}_iter_{iteration}.txt"

    def record_iter(
        self,
        *,
        iteration: int,
        plan_text: str,
        metrics: Dict,
        wallclock_s: Optional[float] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> None:
        self.iter_plan_path(iteration).write_text(plan_text, encoding="utf-8")

        row = {
            "model": self.model,
            "domain": self.domain,
            "prompting_condition": self.condition,
            "instance": self.instance,
            "iteration": iteration,
            "plan_text": plan_text,
            "plan_len": metrics.get("plan_length", 0),
            "solves_problem": bool(metrics.get("solves_problem", False)),
            "valid_action_percent": float(metrics.get("valid_action_percent", 0.0)),
            "consecutive_valid_steps": int(metrics.get("consecutive_valid_steps", 0)),
            "logical_violations": int(metrics.get("logical_violations", 0)),
            "wallclock_s": f"{wallclock_s:.3f}" if wallclock_s is not None else "",
            "prompt_tokens": "" if prompt_tokens is None else int(prompt_tokens),
            "completion_tokens": "" if completion_tokens is None else int(completion_tokens),
        }

        with _CSV_LOCK:
            needs_header = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                if needs_header:
                    writer.writeheader()
                writer.writerow(row)

    def finalize(
        self,
        *,
        plan_text: str,
        first_valid_iter: Optional[int],
        total_iterations: int,
    ) -> None:
        is_valid = first_valid_iter is not None
        first_valid_repr = (
            str(first_valid_iter) if first_valid_iter is not None else "null"
        )
        metadata = (
            "\n\n--- Processing Metadata ---\n"
            f"Domain: {self.domain}\n"
            f"Problem: {self.instance}\n"
            f"Iterations: {total_iterations}\n"
            f"Plan Valid: {is_valid}\n"
            f"Condition: {self.condition}\n"
            f"Model: {self.model}\n"
            f"First Valid Iteration: {first_valid_repr}\n"
        )
        self.final_plan_path.write_text(plan_text + metadata, encoding="utf-8")
        self._finalized = True


__all__ = ["RunRecorder", "CSV_COLUMNS"]
