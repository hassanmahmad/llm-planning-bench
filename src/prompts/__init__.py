"""Prompt package for PDDL planning.

Split into three files:
  - shell.py:        SYSTEM_PROMPT_PDDL, COT_SCAFFOLD, VALIDATION_FEEDBACK_TEMPLATE
  - descriptions.py: DOMAIN_DESCRIPTIONS (verbatim from source projects)
  - compose.py:      build_problem_prompt(domain, condition, pddl_domain, pddl_problem)
                     build_feedback_prompt(val_output, previous_plan)

All model-facing prompt construction goes through compose.build_problem_prompt.
"""

from .shell import SYSTEM_PROMPT_PDDL, COT_SCAFFOLD, VALIDATION_FEEDBACK_TEMPLATE
from .compose import build_problem_prompt, build_feedback_prompt
from .descriptions import DOMAIN_DESCRIPTIONS

__all__ = [
    "SYSTEM_PROMPT_PDDL",
    "COT_SCAFFOLD",
    "VALIDATION_FEEDBACK_TEMPLATE",
    "DOMAIN_DESCRIPTIONS",
    "build_problem_prompt",
    "build_feedback_prompt",
]
