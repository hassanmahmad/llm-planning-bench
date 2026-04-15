# Travel / Bulldozer (Sequential, Satisficing)

## Domain Description

A simple vehicle-travel domain in which a person must board a vehicle, drive (or cross bridges) across a small road network, disembark and walk the rest of the way.
The domain treats both people and vehicles uniformly as "things" that can be `at` a place or `mobile`; a person becomes immobile once driving and the vehicle becomes mobile only when someone is driving.
Both `road` and `bridge` edges are bidirectional in the base encoding, which makes recursion and action selection the main challenges.

The domain header declares the name `bulldozer` (the original author's label); the folder is named `travel` here for readability.

## Authors

Classic STRIPS benchmark (unnamed original author; encoding commonly attributed to the SRI/Stanford collection).

## Original File Names

| file            | original name       |
|-----------------|---------------------|
| domain.pddl     | travel_domain.pddl  |
| problem_01.pddl | pb1.pddl            |
| problem_02.pddl | pb2.pddl            |
