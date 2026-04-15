"""Compose prompts from the shared shell + a domain description.

Single source of truth for the (domain, condition) prompt used across all models.
The byte-identity of prompts across models is the foundation of the experiment's
prompt-uniformity claim — do not introduce model- or instance-specific branching.
"""

from __future__ import annotations

from prompts.descriptions import DOMAIN_DESCRIPTIONS
from prompts.shell import (
    COT_SCAFFOLD,
    SYSTEM_PROMPT_PDDL,
    VALIDATION_FEEDBACK_TEMPLATE,
)


def _require_description(domain: str) -> str:
    key = domain.lower()
    if key not in DOMAIN_DESCRIPTIONS:
        raise KeyError(f"Unknown domain '{domain}'. Add an entry to DOMAIN_DESCRIPTIONS.")
    description = DOMAIN_DESCRIPTIONS[key]
    if description is None:
        raise NotImplementedError(
            f"Domain '{domain}' is dormant — port its description from the source "
            f"project into src/prompts/descriptions.py before using it."
        )
    return description


def build_problem_prompt(
    domain: str,
    condition: str,
    pddl_domain: str,
    pddl_problem: str,
) -> str:
    """Return the full user prompt for (domain, condition).

    Byte-identical across models. `condition` ∈ {"baseline", "cot"}.
    """
    description = _require_description(domain)

    if condition == "baseline":
        body = description
    elif condition == "cot":
        body = COT_SCAFFOLD(description, pddl_problem)
    else:
        raise ValueError(f"Unknown condition '{condition}'. Expected 'baseline' or 'cot'.")

    return (
        f"{SYSTEM_PROMPT_PDDL}\n\n"
        f"{body}\n\n"
        f"=== DOMAIN DEFINITION ===\n{pddl_domain}\n\n"
        f"=== PROBLEM DEFINITION ===\n{pddl_problem}\n\n"
        "Provide the plan now (one action per line)."
    )


def build_feedback_prompt(val_output: str, previous_plan: str) -> str:
    """Feedback after a VAL rejection — same template across all domains."""
    return VALIDATION_FEEDBACK_TEMPLATE(val_output, previous_plan)


__all__ = ["build_problem_prompt", "build_feedback_prompt"]
