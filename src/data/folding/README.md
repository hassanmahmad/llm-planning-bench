# Folding (Sequential, Cost-Optimal)

## Domain Description

The Folding domain models a one-dimensional string of connected nodes that must be folded into a target 2-D shape on a discrete grid.
Each node has a position `(at ?n ?x ?y)` and a heading direction.
The `rotate` action pivots the suffix of the string around a chosen node in either clockwise or counter-clockwise direction; this triggers two passes (`rotate-first-pass` / `rotate-second-pass`) that propagate the new coordinates to every downstream node while making sure no two nodes collide.
Actions have costs (rotate-cost, update-cost) so optimal-planning metrics apply.

## Authors

Giacomo Da Scenzo, Davide Gentili

## Original File Names

| file            | original name          |
|-----------------|------------------------|
| domain.pddl     | folding_domain.ppdl    |
| problem_01.pddl | folding_problem.ppdl   |
| problem_02.pddl | folding_problem_2.pddl |
| problem_03.pddl | folding_problem_3.pddl |

> Note: the original domain and first problem files used a `.ppdl` extension (typo); both were normalised to `.pddl` during import.
