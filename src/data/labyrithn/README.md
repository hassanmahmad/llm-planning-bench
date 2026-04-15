# Labyrinth (Sequential, Cost-Optimal)

## Domain Description

Inspired by the "Labyrinth" board game, this domain lays out a grid of movable maze cards.
A robot sits on one of the cards and can `move-west`, `move-east`, `move-north` or `move-south` to an adjacent card provided the shared edge is not blocked.
Between moves the player can also rotate entire rows or columns of cards (`start-move-card-*`, `move-card-*`, `stop-move-card-*`) to reshape the maze.
The goal is to reach the bottom-right card and `leave` the labyrinth.
The domain uses `:adl` features and action costs to distinguish robot movements from card shuffling.

## Authors

Giacomo Da Scenzo, Davide Gentili

## Original File Names

| file            | original name            |
|-----------------|--------------------------|
| domain.pddl     | labyrithn_domain.pddl    |
| problem_01.pddl | labytinth_problem.pddl   |
| problem_02.pddl | labyrinth_problem_2.pddl |
| problem_03.pddl | labyrinth_problem_3.pddl |

> Note: the folder name preserves the original misspelling "labyrithn" (rather than "labyrinth") for compatibility with existing scripts and result paths.
