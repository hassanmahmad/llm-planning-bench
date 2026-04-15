# Monkey and Bananas (Sequential, Satisficing)

## Domain Description

The textbook Monkey-and-Bananas puzzle, a staple of introductory AI planning.
A monkey must retrieve bananas hanging from the ceiling of a room.
To do so it has to navigate to the right spot, push a box under the bananas, climb on it, and grab the bananas once it also holds the knife.
The domain additionally models fetching water (`PICKGLASS`, `GETWATER`) from a water fountain.
Predicates track the monkey/box/knife/bananas/glass/water locations and whether the monkey is currently on the floor or on the box.

## Authors

Classic AI benchmark (McCarthy), PDDL encoding widely distributed as part of early planning-benchmark collections.

## Original File Names

| file            | original name |
|-----------------|---------------|
| domain.pddl     | monkey_domain.pddl |
| problem_01.pddl | pb1.pddl      |
| problem_02.pddl | pb2.pddl      |
| problem_03.pddl | pb3.pddl      |
