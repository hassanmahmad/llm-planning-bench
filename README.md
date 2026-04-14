# Systematic Evaluation of LLM Planning Capabilities Across Multiple Domains and Model Families

Unified pipeline for comparing LLM planning performance on PDDL problems with iterative validator-guided feedback. Merges and extends two prior student projects into a single controlled comparative study.

**Course**: AI in Industry — Artificial Intelligence, Università di Bologna — April 2026

## Team

- Usama Shabbir Satti
- Muhammad Fahim Asim
- Hassan Ahmed Mujtaba

## Status

**Phase: scaffolding (pre-execution).** The codebase is currently the inherited skeleton from Project B (D'Ascenzo & Gentili). Planned changes are tracked step-by-step in [STEPS.md](STEPS.md); the underlying design is in [plans/glowing-baking-turing.md](../../../../../Users/Hassan/.claude/plans/glowing-baking-turing.md).

| Component | Status |
|---|---|
| Project B skeleton (core, utils, main, SLURM templates) | Inherited |
| Tetris + CityCar domains | Present |
| Blocksworld domain (from Project A) | Pending (Day 0, STEPS §0.3) |
| Harmonized prompts (`shell.py` / `descriptions.py` / `compose.py`) | Pending (Day 0, STEPS §0.4) |
| Baseline + CoT prompting conditions | Pending (Day 0) |
| Stop-on-success iteration loop + per-iter CSV logging | Pending (Day 1, STEPS §1.2) |
| VAL-verbose metrics extractor | Pending (Day 1, STEPS §1.1) |
| Parametric SLURM for 18-cell submission | Pending (Day 1, STEPS §1.4) |
| Analysis notebook (10 plots) | Pending (Day 0 skeleton → Day 3 final) |

## Research Objectives

From the [project proposal](../Project%20Proposal%20-%20AI%20in%20Industry.pdf):

1. **Unify** the two prior codebases into a single repository with a consistent pipeline for model loading, plan generation, validation, and results reporting.
2. **Run a controlled comparative study** of 3 LLM families across 3 planning domains, with standardized prompts and iterative refinement (up to 4 rounds).
3. **Address the prompt-bias confound** by using a single unified prompt across all models, so performance differences reflect model capability rather than prompt tuning.
4. **Produce a comparative analysis** with success rates, iteration-convergence patterns, and domain-specific insights that extend both prior projects.

## Experimental Design

### Domains

| Domain | Reasoning Challenge | Source |
|---|---|---|
| Blocksworld | Sequential state-space search, constraint chaining | Project A (Merola et al.) |
| City Car | Multi-agent coordination, infrastructure management | Project B (D'Ascenzo & Gentili) |
| Tetris | Spatial / geometric reasoning | Project B (D'Ascenzo & Gentili) |

Nine additional Project A domains (Gripper, Logistics, Hanoi, Folding, Monkey, Travel, Labyrinth, Basic-Move, Shoe-Sock) are carried in the codebase as `domains.available` but are **not** run by the core experiment — they preserve optionality for follow-up work.

### Models (3 families)

| Alias | HF repo | Family | Params | Role |
|---|---|---|---|---|
| `llama8` | [`meta-llama/Llama-3.1-8B-Instruct`](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) | Meta | 8B | Retained from Project B; intra-family scale anchor (small) |
| `qwen25` | [`Qwen/Qwen2.5-32B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct) | Alibaba | 32B | **New** — different family, dense mid-size |
| `llama33` | [`meta-llama/Llama-3.3-70B-Instruct`](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) | Meta | 70B | Retained from Project A; intra-family scale anchor (large) |

Fallback for third-model availability: `mistralai/Mistral-Small-24B-Instruct-2501`.

### Prompting conditions

Two conditions run against every (model, domain, instance):

- **Baseline** — zero-shot: direct PDDL problem description + structured output instructions.
- **Chain-of-Thought** — same prompt with a reasoning-step preamble.

Both conditions share a single harmonized system prompt and one validation-feedback template per iteration. For a given (domain, condition, instance), **every model sees the byte-identical string** — verified via automated diff checks ([STEPS §1.6](STEPS.md)).

### Iteration policy

**Stop-on-success, up to 4 iterations.** On each iteration the plan text + VAL-verbose feature row is written to disk **before** the validity check, so failed iterations are still logged for iteration-gain analysis. First successful validation ends the loop.

### Cell matrix

3 models × 3 domains × 2 conditions = **18 cells**, 20 instances per (domain, condition). Upper-bound generation count is 1,440; actual count depends on how early cells converge.

### Metrics

Per-iteration row in `run_metrics.csv`:

```
model, domain, prompting_condition, instance, iteration,
plan_text, plan_len, solves_problem,
valid_action_percent, consecutive_valid_steps, logical_violations,
wallclock_s, prompt_tokens, completion_tokens
```

Aggregate analyses: success-rate matrix (with 95% CIs), iteration-gain curves, Baseline-vs-CoT delta, intra-family scale scatter (8B vs 70B), partial-credit distributions, domain-difficulty ranking. Full list in [plans/glowing-baking-turing.md §6](../../../../../Users/Hassan/.claude/plans/glowing-baking-turing.md).

## Quick Start

Full procedure in [STEPS.md](STEPS.md). Abbreviated:

```bash
# Day 0 — local shake-out (~½ day, before any SLURM)
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
# install VAL locally, verify: VAL/Validate --help

# Run the smoke test for all 3 domains × 2 conditions with a stub model
bash scripts/local/smoke_test.sh

# Day 1 — submit all 18 SLURM jobs on Leonardo
bash scripts/slurm/submit_all.sh

# Ingest + plot (after jobs finish)
jupyter notebook notebooks/results_analysis.ipynb
```

## Planned Repository Structure

```text
llm-planning-bench/
├── README.md
├── STEPS.md                               # execution guide (day-by-day, owner-tagged)
├── config.yml                             # domains, models, conditions, generation, iteration policy
├── requirements.txt
├── requirements_analysis.txt
├── assets/                                # literature, images, Leonardo tutorials (from Project B)
├── notebooks/
│   └── results_analysis.ipynb             # extends Project B's notebook with 10 plots
├── scripts/
│   ├── local/
│   │   └── smoke_test.sh                  # Day-0 gate
│   └── slurm/
│       ├── run.sh                         # parametric: MODEL, DOMAIN, CONDITION
│       ├── submit_all.sh                  # launches all 18 jobs
│       └── SUBMITTED.md                   # JobID log
├── src/
│   ├── main.py                            # --model, --domain, --condition, --iterations, --cluster
│   ├── core/
│   │   ├── model_manager.py               # stop-on-success + per-iter CSV writes
│   │   ├── pddl_processor.py              # prompt router (domain × condition)
│   │   ├── pddl_planner.py, file_manager.py
│   ├── prompts/
│   │   ├── shell.py                       # SYSTEM_PROMPT_PDDL, COT_SCAFFOLD, VALIDATION_FEEDBACK_TEMPLATE
│   │   ├── descriptions.py                # {BLOCKSWORLD,CITYCAR,TETRIS}_DESCRIPTION verbatim
│   │   └── compose.py                     # build_problem_prompt(domain, condition, ...)
│   ├── utils/
│   │   ├── validator.py                   # + validate_plan_verbose
│   │   ├── metrics_extractor.py           # NEW — ported from Project A
│   │   └── {configuration,logging,answer_postprocessor,common}.py
│   ├── models/
│   │   └── stub.py                        # local smoke-test backend
│   ├── data/
│   │   ├── blocksworld/  citycar/  tetris/   # active
│   │   └── {basic_move,folding,gripper,hanoi,labyrinth,logistics,monkey,shoe-sock,travel}/  # dormant
│   ├── results/
│   │   └── {model}/{domain}/{condition}/
│   │       ├── instance-XX_iter_{k}.txt
│   │       ├── instance-XX_plan.txt
│   │       └── run_metrics.csv
│   └── tests/
│       └── fixtures/prompts/              # 6 reference prompts for identity checks
└── VAL/                                   # KCL-Planning/VAL source
```

## Prior Work

This project directly builds on two prior Università di Bologna student projects:

- **Project A — Merola, Singh & Dardouri** ([repo](https://dvcs.apice.unibo.it/pika-lab/courses/ai-ethics/projects/merolasinghdardouri2425)): evaluated LLaMA 3.3 70B across many PDDL domains (Blocksworld, Gripper, Logistics, Hanoi, …) and built meta-networks for plan-success confidence estimation.
- **Project B — D'Ascenzo & Gentili** ([repo](https://github.com/alessandrogentili001/LLM-Needs-a-Plan)): compared four models (LLaMA3-8B, Phi4-14B, Gemma3-27B, Kimi-Dev-72B) on two domains (City Car, Tetris) with a modular HPC-ready framework.

Both projects shared the core **LLM planner + VAL validator + feedback loop** architecture, but neither produced a unified cross-model, cross-domain picture. This project merges their code paths into a single pipeline with standardized prompts and generation config, so the comparative numbers are actually interpretable.

## Leonardo HPC (CINECA)

Experiments run on the Leonardo supercomputer at CINECA. Access is confirmed for this project.

Setup guides (inherited from Project B):

- [Pre-Configuration Steps](assets/tutorials/1.%20Pre%20Configuration.md)
- [Cluster Node Configuration](assets/tutorials/2.%20Cluster%20Set%20Up.md)
- [Load Local Files Into The Cluster](assets/tutorials/3.%20Load%20Local%20Files%20Into%20The%20Cluster.md)
- [First Job Submission](assets/tutorials/4.%20First%20Job%20Submission.md)
- [Work Directory And LLMs Download](assets/tutorials/5.%20Work%20Directory%20And%20LLMs%20Download.md)
- [SLURM Files Explained](assets/tutorials/6.%20SLURM%20Files%20Explained.md)

Consumer-GPU fallback (8B–14B range) is available if HPC access is revoked mid-project — see [plans/glowing-baking-turing.md §9](../../../../../Users/Hassan/.claude/plans/glowing-baking-turing.md).

## Validator

Plans are validated with [KCL-Planning/VAL](https://github.com/KCL-Planning/VAL). Verbose output (per-step action validity) feeds the per-problem feature extractor.

## Problem Sources

Planning problems are PDDL instances from the [potassco/pddl-instances](https://github.com/potassco/pddl-instances) repository and the Project A problem collection:

- [Tetris (IPC 2014)](https://github.com/potassco/pddl-instances/tree/master/ipc-2014/domains/tetris-sequential-satisficing) — carried from Project B
- [City Car (IPC 2014)](https://github.com/potassco/pddl-instances/tree/master/ipc-2014/domains/city-car-sequential-satisficing) — carried from Project B
- **Blocksworld** — carried from Project A's [`problem_dataset/problems_all/blocksworld/`](../merolasinghdardouri2425-master/problem_dataset/problems_all/blocksworld/)

See [src/data/README.md](src/data/README.md) for per-domain instance details.

## References

Literature reviewed for this study lives in [assets/literature/](assets/literature/).

## Planning Documents

- [STEPS.md](STEPS.md) — step-by-step execution guide (Day 0 through Day 4)
- [glowing-baking-turing.md](../../../../../Users/Hassan/.claude/plans/glowing-baking-turing.md) — canonical plan aligned with the course proposal
- [smooth-snuggling-muffin.md](../../../../../Users/Hassan/.claude/plans/smooth-snuggling-muffin.md) — broader engineering-tour alternative (reference only)
