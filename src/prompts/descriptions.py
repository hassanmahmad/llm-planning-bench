"""Natural-language domain descriptions plugged into the shared prompt shell.

Active domains carry verbatim text from the source projects (Project A for
Blocksworld, Project B for Tetris / CityCar). Dormant domains are left as
None until their descriptions are ported — compose.build_problem_prompt raises
NotImplementedError if a dormant domain is requested.
"""

from __future__ import annotations


# --------------------------------------------------------------------------
# Blocksworld — verbatim from Project A
# merolasinghdardouri2425-master/llama_planning_framework/prompts.py:239-276
# --------------------------------------------------------------------------
BLOCKSWORLD_DESCRIPTION = """BLOCKSWORLD PLANNING TASK:
Problem description: you are an agent capable of solving the planning problems described using the PDDL syntax.
In the following problem there is a table with some blocks and the agent can perform some actions (described later) to achieve a specific goal.
The problem domain is defined by: types (the type of the elements), predicates (statements that can be true in the current state) and actions (what the agent can do to modify the current state).
Types:
1. block
Predicates:
1. (on ?x - block ?y - block): means the block ?x is on the block ?y
2. (ontable ?x - block): means the block ?x is on the table
3. (clear ?x - block): means there is nothing on the block ?x
4. (handempty): the hand is empty
5. (holding ?x - block): the agent is holding the block ?x
Actions:
1. pick-up
   :parameters (?x - block)
   :precondition (and (clear ?x) (ontable ?x) (handempty))
   :effect (and (not (ontable ?x)) (not (clear ?x)) (not (handempty)) (holding ?x))
2. put-down
   :parameters (?x - block)
   :precondition (holding ?x)
   :effect (and (not (holding ?x)) (clear ?x) (handempty) (ontable ?x))
3. stack
   :parameters (?x - block ?y - block)
   :precondition (and (holding ?x) (clear ?y))
   :effect (and (not (holding ?x)) (not (clear ?y)) (clear ?x) (handempty) (on ?x ?y))
4. unstack
   :parameters (?x - block ?y - block)
   :precondition (and (on ?x ?y) (clear ?x) (handempty))
   :effect (and (holding ?x) (clear ?y) (not (clear ?x)) (not (handempty)) (not (on ?x ?y)))
Provide only the action sequence, one action per line. Use the exact action names from the domain.
"""


# --------------------------------------------------------------------------
# CityCar — verbatim framing from Project B
# dascenzogentili2425-master/src/prompts/prompts.py:267-308
# --------------------------------------------------------------------------
CITYCAR_DESCRIPTION = """CITYCAR PLANNING TASK:
You are solving an urban traffic planning problem modeled in PDDL.
The domain involves cars moving through a grid of junctions connected by roads.
Cars can start from garages, build or destroy roads, and move between junctions.
Key actions include car_start, car_arrived, move_car_in_road, move_car_out_road,
build_straight_oneway, build_diagonal_oneway, destroy_road.

OUTPUT INSTRUCTIONS:
- Provide ONLY the action sequence in PDDL action syntax, one action per line.
- Do NOT include narrative or explanations.
- Respect traffic rules, signals, and collision avoidance encoded in the domain.
- Use the exact token names from the problem/domain.
"""


# --------------------------------------------------------------------------
# Tetris — verbatim framing from Project B
# dascenzogentili2425-master/src/prompts/prompts.py:128-171
# --------------------------------------------------------------------------
TETRIS_DESCRIPTION = """TETRIS PLANNING TASK:
You are solving a Tetris configuration planning problem.
The domain uses explicit coordinate positions (e.g. f0-0f, f1-2f) connected by
connected/clear predicates. Pieces may be single squares, two-piece straights,
or L-shapes, and are moved via actions such as move_square, move_two,
move_l_down, etc. Each action shifts a piece from one set of positions to
another, requires target cells to be clear, and preserves piece identity.

OUTPUT INSTRUCTIONS:
- Provide ONLY the action sequence in PDDL action syntax, one action per line.
- Do NOT include narrative, reasoning, or extraneous text.
- Use the exact token names from the domain/problem.
"""


# --------------------------------------------------------------------------
# Dormant domains — placeholders. compose.build_problem_prompt raises
# NotImplementedError for these until verbatim descriptions are ported.
# --------------------------------------------------------------------------
BASIC_MOVE_DESCRIPTION = None  # TODO: port if activated
FOLDING_DESCRIPTION = None     # TODO: port if activated
GRIPPER_DESCRIPTION = None     # TODO: port if activated
HANOI_DESCRIPTION = None       # TODO: port if activated
LABYRINTH_DESCRIPTION = None   # TODO: port if activated (dir name is "labyrithn" on disk)
LOGISTICS_DESCRIPTION = None   # TODO: port if activated
MONKEY_DESCRIPTION = None      # TODO: port if activated
SHOE_SOCK_DESCRIPTION = None   # TODO: port if activated
TRAVEL_DESCRIPTION = None      # TODO: port if activated


DOMAIN_DESCRIPTIONS = {
    "blocksworld": BLOCKSWORLD_DESCRIPTION,
    "citycar":     CITYCAR_DESCRIPTION,
    "tetris":      TETRIS_DESCRIPTION,
    "basic_move":  BASIC_MOVE_DESCRIPTION,
    "folding":     FOLDING_DESCRIPTION,
    "gripper":     GRIPPER_DESCRIPTION,
    "hanoi":       HANOI_DESCRIPTION,
    "labyrinth":   LABYRINTH_DESCRIPTION,
    "labyrithn":   LABYRINTH_DESCRIPTION,
    "logistics":   LOGISTICS_DESCRIPTION,
    "monkey":      MONKEY_DESCRIPTION,
    "shoe-sock":   SHOE_SOCK_DESCRIPTION,
    "travel":      TRAVEL_DESCRIPTION,
}


__all__ = [
    "DOMAIN_DESCRIPTIONS",
    "BLOCKSWORLD_DESCRIPTION",
    "CITYCAR_DESCRIPTION",
    "TETRIS_DESCRIPTION",
]
