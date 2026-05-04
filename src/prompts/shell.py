"""Shared prompt shell: system prompt, CoT scaffold, validation-feedback template.

Domain-agnostic primitives used by compose.py. Every domain description is plugged
into these through build_problem_prompt / build_feedback_prompt.
"""

from __future__ import annotations


SYSTEM_PROMPT_PDDL = (
    "You are an expert automated PDDL planning assistant.\n"
    "Your primary objective is to find the shortest / lowest-cost plan that achieves the goal.\n"
    "When asked to return a plan, follow these rules unless explicitly told otherwise:\n"
    "- Output only the action sequence, one action per line, using the exact PDDL action syntax: "
    "(action-name param1 param2 ...).\n"
    "- Do NOT repeat the domain or problem definition.\n"
    "- Do NOT output the initial state or goal state.\n"
    "- Do not include explanations, commentary, or extra metadata unless requested.\n"
    "- If you use <think> tags for reasoning, keep the reasoning concise and output the final "
    "plan clearly after the closing </think> tag.\n"
    "- Verify that all action preconditions are respected in the current state and that the plan "
    "achieves all goal predicates while minimising total-cost.\n"
)


def COT_SCAFFOLD(description: str, problem: str) -> str:
    """Prepend a step-by-step reasoning preamble to a domain description.

    description: natural-language domain framing (from descriptions.py)
    problem: raw PDDL :problem block, for the scaffold to reference
    """
    return (
        "Before giving the plan, think step by step about the following:\n"
        "  1. Parse the initial state and goal from the problem.\n"
        "  2. List the actions relevant to reaching each goal predicate.\n"
        "  3. Check preconditions for every chosen action.\n"
        "  4. Minimise plan length / total-cost.\n"
        "Wrap your reasoning in <think> ... </think>, then emit the final plan on its own, "
        "one action per line, with no extra commentary.\n\n"
        f"{description}"
    )


def VALIDATION_FEEDBACK_TEMPLATE(val_output: str, previous_plan: str) -> str:
    """Single feedback template shared across all domains."""
    return (
        "Your previous plan FAILED validation. Analyze the validator output below "
        "carefully and produce a corrected plan from scratch.\n\n"
        "===== YOUR PREVIOUS PLAN =====\n"
        f"{previous_plan}\n\n"
        "===== VALIDATOR (VAL) OUTPUT =====\n"
        f"{val_output}\n\n"
        "===== INSTRUCTIONS =====\n"
        "1. Identify the FIRST action that failed and the specific precondition "
        "or invariant that was violated. The validator usually names it directly "
        "(e.g. 'unsatisfied precondition', 'has no effect', or 'invalid action').\n"
        "2. Trace the state forward from the initial state and re-check every "
        "action's preconditions before that point — an earlier action may have "
        "left the world in a state you didn't expect.\n"
        "3. Output a CORRECTED plan from the very first action, not a partial fix.\n"
        "4. Output ONLY the action sequence, one action per line, in the exact "
        "PDDL syntax (action-name arg1 arg2 ...). No prose, no numbering, no "
        "code fences, no commentary."
    )


__all__ = ["SYSTEM_PROMPT_PDDL", "COT_SCAFFOLD", "VALIDATION_FEEDBACK_TEMPLATE"]
