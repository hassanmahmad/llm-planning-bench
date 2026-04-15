# Shoe & Socks (Sequential, Satisficing)

## Domain Description

A toy typed-STRIPS domain illustrating routine ordering constraints.
For every person, two socks have to be picked up, paired (via `match-socks`, which uses a static `sock-pair` relation) and worn before the matching shoes can be put on.
Predicates track whether each agent already holds (`has-sock`, `has-shoe`) or is wearing (`wearing-sock`, `wearing-shoe`) an item.
Instances typically involve multiple people and colour-coded sock/shoe pairs.

## Authors

Giacomo Da Scenzo, Davide Gentili

## Original File Names

| file            | original name         |
|-----------------|-----------------------|
| domain.pddl     | shoe-sock_domain.pddl |
| problem_01.pddl | shoe-sock_problem.pddl|
