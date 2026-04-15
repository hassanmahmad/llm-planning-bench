# Gripper (Sequential, Satisficing)

## Domain Description

A classic IPC domain in which a two-handed robot must transport a set of balls between rooms.
Predicates identify rooms, balls and grippers, the robot's current room (`at-robby`), the location of each ball (`at`), whether a gripper is free or carrying a ball (`free`, `carry`).
Actions are `move` between rooms, `pick` a ball with a free gripper, and `drop` a carried ball in the current room.
The planning challenge scales quickly with the number of balls despite the extremely small action set.

## Authors

Jana Koehler (original IPC benchmark).

## Original File Names

| file            | original name |
|-----------------|---------------|
| domain.pddl     | gripper_domain.pddl |
| problem_01.pddl | pb1.pddl      |
| problem_02.pddl | pb2.pddl      |
| problem_03.pddl | pb3.pddl      |
| problem_04.pddl | pb4.pddl      |
