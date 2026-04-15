# Towers of Hanoi (Sequential, Satisficing)

## Domain Description

PDDL encoding of the classic Towers of Hanoi puzzle.
Discs of different sizes are stacked on three pegs, and the planner must move them one at a time from a starting configuration to a goal configuration while respecting the rule that a larger disc may never rest on a smaller one.
The domain exposes a single action, `move`, whose preconditions combine `(clear ?x)`, `(on ?x ?y)` and a static `(smaller ?x ?y)` relation between disc sizes/pegs.
Instance difficulty grows exponentially with the number of discs.

## Authors

Classic AI benchmark, PDDL encoding by Malte Helmert and the Fast Downward community.

## Original File Names

| file            | original name |
|-----------------|---------------|
| domain.pddl     | hanoi_domain.pddl |
| problem_01.pddl | pb1.pddl      |
| problem_02.pddl | pb2.pddl      |
| problem_03.pddl | pb3.pddl      |
| problem_04.pddl | pb4.pddl      |
| problem_05.pddl | pb5.pddl      |
| problem_06.pddl | pb6.pddl      |
