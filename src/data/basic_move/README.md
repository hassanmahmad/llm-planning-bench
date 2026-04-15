# Basic Move (Sequential, Satisficing)

## Domain Description

A minimal STRIPS domain modelling an agent that moves between discrete locations connected by directional edges.
The state is captured by the single predicate `(at ?l)` describing the agent's current location, and `(conn ?l1 ?l2)` describing the set of allowed transitions.
The only action, `move`, takes the agent from a location to a directly connected one.
Problem variants add extra constraints (e.g. "clear" goals, "without-unicity" scenarios, satisfiable vs. unsatisfiable instances) to stress-test simple state-space reasoning.

## Authors

Giacomo Da Scenzo, Davide Gentili

## Original File Names

| file            | original name                          |
|-----------------|----------------------------------------|
| domain.pddl     | basic_move_domain.pddl                 |
| problem_01.pddl | easy_BasicMove-four.pddl               |
| problem_02.pddl | easy_BasicMove-six-sat.pddl            |
| problem_03.pddl | easy_BasicMove-six-unsat.pddl          |
| problem_04.pddl | easy_BasicMoveClearWOU-four-sat.pddl   |
| problem_05.pddl | easy_BasicMoveClearWOU.pddl            |
| problem_06.pddl | easy_BasicMoveWO-four-sat.pddl         |
| problem_07.pddl | easy_BasicMoveWO-four-unsat.pddl       |
| problem_08.pddl | easy_BasicMoveWO.pddl                  |
| problem_09.pddl | easy_BasicMoveWOU-five-sat.pddl        |
| problem_10.pddl | easy_BasicMoveWOU-four-unsat.pddl      |
| problem_11.pddl | easy_BasicMoveWOU.pddl                 |
