"""Processing pipeline orchestrating prompt creation, generation, and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .file_manager import DomainBundle, FileManager
from .model_manager import ModelManager
from prompts import compose
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def _feedback_adapter(initial_prompt: str, plan_text: str, error_msg: str) -> str:
    """Bridge ModelManager's (initial_prompt, plan, error) → compose's (val_output, plan)."""
    return compose.build_feedback_prompt(error_msg, plan_text)


class PDDLProcessor:
    """Coordinates domain processing, prompt creation, and plan validation."""

    def __init__(self, model_manager: ModelManager, output_dir: str):
        self.model_manager = model_manager
        self.output_dir = Path(output_dir)
        self.file_manager = FileManager()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("PDDLProcessor initialized (output=%s)", self.output_dir)

    # ------------------------------------------------------------------
    # Domain-level processing
    # ------------------------------------------------------------------

    def process_domain_with_validation(
        self,
        domain_data: DomainBundle,
        *,
        max_iterations: int = 3,
        condition: str = "baseline",
        add_system_prompt: bool = True,
        sampling: bool = False,
        **generation_kwargs,
    ) -> Dict[str, Any]:
        domain_output_dir = self.output_dir / domain_data.domain_name / condition
        domain_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Processing domain %s (%d problems)",
            domain_data.domain_name,
            len(domain_data.problem_paths),
        )

        results = {
            "domain_name": domain_data.domain_name,
            "total_problems": len(domain_data.problem_paths),
            "successful_plans": 0,
            "failed_plans": 0,
            "problem_results": [],
            "output_directory": str(domain_output_dir),
        }

        for idx, problem_path in enumerate(domain_data.problem_paths, start=1):
            logger.info(
                "[%d/%d] %s",
                idx,
                len(domain_data.problem_paths),
                problem_path.name,
            )
            try:
                problem_result = self._process_single_problem(
                    domain=domain_data,
                    problem_path=problem_path,
                    output_dir=domain_output_dir,
                    max_iterations=max_iterations,
                    condition=condition,
                    add_system_prompt=add_system_prompt,
                    sampling=sampling,
                    **generation_kwargs,
                )
                results["problem_results"].append(problem_result)
                if problem_result["plan_valid"]:
                    results["successful_plans"] += 1
                else:
                    results["failed_plans"] += 1
            except Exception as exc:
                logger.exception(
                    "Problem %s failed with error", problem_path.name
                )
                results["failed_plans"] += 1
                results["problem_results"].append(
                    {
                        "problem_path": str(problem_path),
                        "problem_name": problem_path.stem,
                        "plan_valid": False,
                        "iterations": 0,
                        "error": str(exc),
                    }
                )

        success_rate = (
            (results["successful_plans"] / results["total_problems"]) * 100
            if results["total_problems"]
            else 0
        )
        logger.info(
            "Domain %s done: %d/%d valid (%.1f%%)",
            domain_data.domain_name,
            results["successful_plans"],
            results["total_problems"],
            success_rate,
        )

        return results

    def batch_process_domains(
        self,
        domains_data: List[DomainBundle],
        *,
        max_iterations: int = 3,
        condition: str = "baseline",
        **kwargs,
    ) -> Dict[str, Any]:
        logger.info("Starting batch processing of %d domain(s)", len(domains_data))
        batch_results = {
            "total_domains": len(domains_data),
            "domain_results": [],
            "overall_stats": {
                "total_problems": 0,
                "total_successful": 0,
                "total_failed": 0,
            },
        }

        for domain_bundle in domains_data:
            result = self.process_domain_with_validation(
                domain_bundle,
                max_iterations=max_iterations,
                condition=condition,
                **kwargs,
            )
            batch_results["domain_results"].append(result)
            stats = batch_results["overall_stats"]
            stats["total_problems"] += result["total_problems"]
            stats["total_successful"] += result["successful_plans"]
            stats["total_failed"] += result["failed_plans"]

        stats = batch_results["overall_stats"]
        success_rate = (
            (stats["total_successful"] / stats["total_problems"]) * 100
            if stats["total_problems"]
            else 0
        )
        logger.info(
            "Batch complete: %d problems, %.1f%% success",
            stats["total_problems"],
            success_rate,
        )
        return batch_results

    # ------------------------------------------------------------------
    # Problem-level processing
    # ------------------------------------------------------------------

    def _process_single_problem(
        self,
        *,
        domain: DomainBundle,
        problem_path: Path,
        output_dir: Path,
        max_iterations: int,
        condition: str,
        add_system_prompt: bool,
        sampling: bool,
        **generation_kwargs,
    ) -> Dict[str, Any]:
        problem_text = self.file_manager.read_file(problem_path)
        if problem_text is None:
            raise ValueError(f"Unable to read problem file {problem_path}")

        prompt = compose.build_problem_prompt(
            domain.domain_name, condition, domain.domain_text, problem_text
        )

        response_text, iterations, is_valid = self.model_manager.iterative_planning_with_validation(
            domain_path=str(domain.domain_path),
            problem_path=str(problem_path),
            initial_prompt=prompt,
            max_iterations=max_iterations,
            add_system_prompt=add_system_prompt,
            validation_feedback_fn=_feedback_adapter,
            sampling=sampling,
            **generation_kwargs,
        )

        plan_path = output_dir / f"{problem_path.stem}_plan.txt"
        metadata = (
            "\n\n--- Processing Metadata ---\n"
            f"Domain: {domain.domain_name}\n"
            f"Problem: {problem_path.stem}\n"
            f"Iterations: {iterations}\n"
            f"Plan Valid: {is_valid}\n"
            f"Condition: {condition}\n"
        )
        self.file_manager.save_file(plan_path, response_text + metadata)

        return {
            "problem_path": str(problem_path),
            "problem_name": problem_path.stem,
            "plan_path": str(plan_path),
            "plan_valid": is_valid,
            "iterations": iterations,
            "response_length": len(response_text),
            "condition": condition,
        }

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_processor_info(self) -> Dict[str, Any]:
        return {
            "output_directory": str(self.output_dir),
            "model_info": self.model_manager.get_model_info(),
            "file_manager_available": self.file_manager is not None,
        }


__all__ = ["PDDLProcessor"]