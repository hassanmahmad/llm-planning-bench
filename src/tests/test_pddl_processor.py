#!/usr/bin/env python3
"""Verify PDDLProcessor wiring after STEPS.md §1.2 (per-iter logging via RunRecorder).

What this asserts:
- PDDLProcessor.__init__ accepts the new `model_name` kwarg and stamps
  it onto the CSV rows the iteration loop writes.
- _process_single_problem constructs a RunRecorder per problem and
  passes it as `recorder=` to model_manager.iterative_planning_with_validation.
- The processor no longer writes `_plan.txt` itself — finalize() does
  (so the result dict's `plan_path` is whatever the recorder produced).
"""

import csv
import shutil
import sys
import tempfile
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from core.file_manager import FileManager
from core.pddl_processor import PDDLProcessor
from utils.configuration import load_config
from utils.run_recorder import CSV_COLUMNS, RunRecorder


class RecorderCapturingMockModel:
    """Mock that records the kwargs PDDLProcessor passes to iterative planning.

    Drives the recorder the same way the real ModelManager does so we
    exercise the artifact-write contract end-to-end without touching VAL
    or any model weights.
    """

    def __init__(self, *, plan_text="(action_a)\n(action_b)", solves=True):
        self.plan_text = plan_text
        self.solves = solves
        self.last_call_kwargs = None

    def get_model_info(self):
        return {"loaded": False, "mock": True}

    def iterative_planning_with_validation(self, *, recorder=None, **kwargs):
        self.last_call_kwargs = {"recorder": recorder, **kwargs}
        if recorder is not None:
            metrics = {
                "plan_length": 2,
                "solves_problem": self.solves,
                "valid_action_percent": 100.0 if self.solves else 0.0,
                "consecutive_valid_steps": 2 if self.solves else 0,
                "logical_violations": 0 if self.solves else 1,
            }
            recorder.record_iter(
                iteration=1,
                plan_text=self.plan_text,
                metrics=metrics,
                wallclock_s=0.001,
                prompt_tokens=12,
                completion_tokens=8,
            )
            recorder.finalize(
                plan_text=self.plan_text,
                first_valid_iter=1 if self.solves else None,
                total_iterations=1,
            )
        return self.plan_text, 1, self.solves


def _first_active_domain(file_manager: FileManager, problems_path: str, active: list):
    """Pick the first ACTIVE domain (per config.yml) with at least one problem.

    Dormant domains (basic_move, hanoi, etc.) have `None` descriptions in
    the prompt registry — compose.build_problem_prompt raises
    NotImplementedError for them, which would silently fail this test.
    """
    active_lower = {a.lower() for a in active}
    for bundle in file_manager.find_pddl_files(problems_path):
        if bundle.domain_name.lower() in active_lower and bundle.problem_paths:
            return bundle
    return None


def test_pddl_processor_wires_recorder():
    print("Testing PDDLProcessor recorder wiring")
    print("=" * 50)

    config = load_config()
    problems_path = config["PROBLEMS_PATH"]
    abs_problems = Path(__file__).parent.parent.parent / problems_path
    if not abs_problems.exists():
        print(f"problems dir missing ({abs_problems}) — skipping")
        return True

    active = (config.get("domains") or {}).get("active") or []
    file_manager = FileManager()
    bundle = _first_active_domain(file_manager, str(abs_problems), active)
    if bundle is None:
        print(f"no active domain ({active}) with problem instances — skipping")
        return True
    print(f"using domain: {bundle.domain_name}")

    output_dir = Path(tempfile.mkdtemp(prefix="pddl_proc_test_"))
    try:
        # Trim to a single problem so the test stays cheap.
        bundle = type(bundle)(
            domain_name=bundle.domain_name,
            domain_path=bundle.domain_path,
            domain_text=bundle.domain_text,
            problem_paths=bundle.problem_paths[:1],
        )

        mock = RecorderCapturingMockModel(plan_text="(act_x)\n(act_y)", solves=True)
        processor = PDDLProcessor(
            model_manager=mock,
            output_dir=str(output_dir),
            model_name="mock-model",
        )

        result = processor.process_domain_with_validation(
            bundle, max_iterations=4, condition="cot"
        )

        # 1. processor passed a RunRecorder to the model
        rec = mock.last_call_kwargs["recorder"]
        assert isinstance(rec, RunRecorder), (
            "PDDLProcessor must pass recorder= to iterative_planning_with_validation"
        )
        assert rec.model == "mock-model", f"recorder.model={rec.model!r}"
        assert rec.condition == "cot", f"recorder.condition={rec.condition!r}"
        assert rec.domain == bundle.domain_name
        assert rec.instance == bundle.problem_paths[0].stem
        print(f"[OK] recorder passed with model={rec.model} condition={rec.condition}")

        # 2. recorder.finalize wrote the canonical _plan.txt; processor result points at it
        problem_result = result["problem_results"][0]
        plan_path = Path(problem_result["plan_path"])
        assert plan_path.exists(), f"final plan missing: {plan_path}"
        plan_body = plan_path.read_text(encoding="utf-8")
        for required in (
            "--- Processing Metadata ---",
            "First Valid Iteration: 1",
            "Plan Valid: True",
            "Model: mock-model",
            "Condition: cot",
        ):
            assert required in plan_body, f"metadata missing: {required!r}"
        print(f"[OK] final plan + metadata block at {plan_path.name}")

        # 3. CSV row is present with the §1.2 schema and right `model`
        csv_path = output_dir / bundle.domain_name / "cot" / "run_metrics.csv"
        assert csv_path.exists(), f"CSV missing: {csv_path}"
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1, f"expected 1 CSV row, got {len(rows)}"
        row = rows[0]
        assert list(row.keys()) == CSV_COLUMNS, "CSV header drift"
        assert row["model"] == "mock-model"
        assert row["prompting_condition"] == "cot"
        assert row["solves_problem"] == "True"
        print(f"[OK] CSV schema intact, model column = {row['model']!r}")

        print(f"\nPDDLProcessor wiring test passed!")
        return True
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    ok = test_pddl_processor_wires_recorder()
    sys.exit(0 if ok else 1)
