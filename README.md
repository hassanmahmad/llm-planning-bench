# Systematic Evaluation of LLM Planning Capabilities Across Multiple Domains and Model Families

Unified pipeline for comparing LLM planning performance on PDDL problems with iterative validator-guided feedback. Merges and extends two prior student projects into a single controlled comparative study.

**Course**: AI in Industry — Artificial Intelligence, Università di Bologna — April 2026

## Team

- Usama Shabbir Satti
- Muhammad Fahim Asim
- Hassan Ahmed Mujtaba

## Status

**Phase: results published.** Waves 1–3 have run on Leonardo; the analysis
notebook and all 15 plots live in [notebooks/](notebooks/) and
[report/figures/](report/figures/), and the final write-up is at
[report/report.pdf](report/report.pdf) (LaTeX source under [report/](report/)).
The pipeline below is what was used to produce them.

| Component | Status |
|---|---|
| Project B skeleton merged with Project A domains/metrics | Done |
| 6 active domains: blocksworld, citycar, tetris, basic_move, visit-all, satellite | Done |
| Harmonized prompts (`shell.py` / `descriptions.py` / `compose.py`) | Done |
| Baseline + CoT prompting conditions | Done |
| Stop-on-success iteration loop + per-iter CSV logging | Done |
| VAL-verbose metrics extractor | Done |
| Parametric SLURM (5 models × 6 domains × 2 conditions, staged in 3 waves) | Done |
| Analysis notebook + 15 plots + report | Done |

## Research Objectives

From the [project proposal](../Project%20Proposal%20-%20AI%20in%20Industry.pdf):

1. **Unify** the two prior codebases into a single repository with a consistent pipeline for model loading, plan generation, validation, and results reporting.
2. **Run a controlled comparative study** of 3 LLM families (5 model checkpoints) across 6 planning domains, with standardized prompts and iterative refinement (up to 4 rounds).
3. **Address the prompt-bias confound** by using a single unified prompt across all models, so performance differences reflect model capability rather than prompt tuning.
4. **Produce a comparative analysis** with success rates, iteration-convergence patterns, and domain-specific insights that extend both prior projects.

## Experimental Design

### Domains

Six active domains, split into a "main slate" (20 instances each) and a
"short slate" (10 instances each, used to broaden domain coverage in waves 2–3):

| Domain | Slate | n | Reasoning Challenge | Source |
|---|---|---|---|---|
| Blocksworld | main | 20 | Sequential state-space search, constraint chaining | Project A (Merola et al.) |
| City Car | main | 20 | Multi-agent coordination, infrastructure management | Project B (D'Ascenzo & Gentili) |
| Tetris | main | 20 | Spatial / geometric reasoning | Project B (D'Ascenzo & Gentili) |
| basic_move | short | 10 | Minimal navigation; sanity floor for short-plan tasks | Project A |
| visit-all | short | 10 | Coverage / traversal planning | IPC (visitall) |
| satellite | short | 10 | Resource-constrained scheduling with `:equality` | IPC (satellite) |

Eight more domains (Gripper, Logistics, Hanoi, Folding, Monkey, Travel,
Labyrinth, Shoe-Sock) are carried as dormant `domains.available` entries —
their PDDL files are present but no natural-language description is wired
up; activate by porting a description into [src/prompts/descriptions.py](src/prompts/descriptions.py).
See [src/data/README.md](src/data/README.md) for the full domain contract.

### Models (5 checkpoints, 3 families)

Core slate ran in waves 1–2; the two reasoning/cross-family additions ran in wave 3.

| Alias | HF repo | Family | Params | Wave | Role |
|---|---|---|---|---|---|
| `llama8` | [`meta-llama/Llama-3.1-8B-Instruct`](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) | Meta | 8B | 1–2 | Retained from Project B; intra-family scale anchor (small) |
| `qwen25` | [`Qwen/Qwen2.5-32B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-32B-Instruct) | Alibaba | 32B | 1–2 | Different family, dense mid-size |
| `llama33` | [`meta-llama/Llama-3.3-70B-Instruct`](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) | Meta | 70B | 1–2 | Retained from Project A; intra-family scale anchor (large) |
| `qwq32` | [`Qwen/QwQ-32B`](https://huggingface.co/Qwen/QwQ-32B) | Alibaba | 32B | 3 | Reasoning-trained sibling of `qwen25` (`<think>` traces stripped pre-validation) |
| `mistral24` | [`mistralai/Mistral-Small-24B-Instruct-2501`](https://huggingface.co/mistralai/Mistral-Small-24B-Instruct-2501) | Mistral | 24B | 3 | Third-family reference point, dense mid-size |

### Prompting conditions

Two conditions run against every (model, domain, instance):

- **Baseline** — zero-shot: direct PDDL problem description + structured output instructions.
- **Chain-of-Thought** — same prompt with a reasoning-step preamble.

Both conditions share a single harmonized system prompt and one validation-feedback template per iteration. For a given (domain, condition, instance), **every model sees the byte-identical string** — verified via automated diff checks before each wave was launched.

### Iteration policy

**Stop-on-success, up to 4 iterations.** On each iteration the plan text + VAL-verbose feature row is written to disk **before** the validity check, so failed iterations are still logged for iteration-gain analysis. First successful validation ends the loop.

### Cell matrix

5 models × 6 domains × 2 conditions = **60 cells**. Instance count varies by
slate: 20 per (domain, condition) for the main slate (blocksworld, citycar,
tetris) and 10 for the short slate (basic_move, visit-all, satellite) —
90 instances per (model, condition) total. Upper-bound generation count is
3,600 (90 × 5 × 2 × 4); actual count depends on how early cells converge.

### Metrics

Per-iteration row in `run_metrics.csv`:

```
model, domain, prompting_condition, instance, iteration,
plan_text, plan_len, solves_problem,
valid_action_percent, consecutive_valid_steps, logical_violations,
wallclock_s, prompt_tokens, completion_tokens
```

Aggregate analyses: success-rate matrix (with 95% CIs), iteration-gain curves, Baseline-vs-CoT delta, intra-family scale scatter (8B vs 70B), partial-credit distributions, domain-difficulty ranking. Full plot list in the analysis notebook.

## Ground-truth difficulty: `REFERENCE_PLANS.csv`

For each active domain we compute an **optimal-or-near-optimal plan length per instance** with a classical planner — *before* running any LLM. This separates "the model failed" from "the problem is genuinely hard," and gives the analysis a concrete x-axis for difficulty that doesn't depend on LLM behavior.

### What the file contains

`src/data/<domain>/REFERENCE_PLANS.csv`, one row per instance:

| column | meaning |
|---|---|
| `instance` | problem-file stem (e.g. `instance-01`) |
| `plan_len` | number of actions in the optimal plan the classical planner found |
| `status` | `ok` (planner solved), `manual-reference` (transcribed from another planner), or `parse-error: ...` if pyperplan can't parse the domain |
| `search` | which pyperplan algorithm was used (`bfs`, `astar`, …) |
| `heuristic` | heuristic used (only meaningful for non-blind A\*) |
| `elapsed_s` | planner wallclock (seconds) |

### How it's generated

[`scripts/verify/validate_instances.py`](scripts/verify/validate_instances.py) runs [pyperplan](https://github.com/aibasel/pyperplan) on every instance of every active domain. Two algorithms are wired in:

- **BFS** — provably optimal, used for short-plan domains (`basic_move`, `visit-all`).
- **A\* + `hff`** — admissible-heuristic search, much faster on richer domains; near-optimal in practice (used for `blocksworld`).

```bash
.venv/Scripts/python.exe scripts/verify/validate_instances.py
# subset / different settings:
.venv/Scripts/python.exe scripts/verify/validate_instances.py \
    --domains basic_move visit-all --search astar --heuristic hff --timeout 60
```

The script preserves any row tagged `manual-reference` across re-runs, so hand-curated entries can't be silently overwritten.

### Coverage by domain

| Domain | n | plan_len range | mean | source |
|---|---|---|---|---|
| `basic_move` | 10 | 1–7 | 4.2 | pyperplan BFS |
| `visit-all` | 10 | 2–10 | 5.4 | pyperplan BFS |
| `satellite` | 10 | 5–18 | 9.8 | manual (Fast Downward, transcribed — pyperplan can't parse `:equality`) |
| `blocksworld` | 20 | 4–26 | 14.4 | pyperplan A\*+hff |
| `citycar` | — | — | — | **no reference** — domain uses `:functions` (numeric fluents) which pyperplan can't parse |
| `tetris` | — | — | — | **no reference** — same `:functions` issue |

For `citycar` and `tetris` the analysis falls back on **empirical consensus difficulty** (fraction of LLM cells that ever solved an instance) — see Plot 14 below.

### How it's used in the analysis

The notebook [`notebooks/results_analysis.ipynb`](notebooks/results_analysis.ipynb) loads every `REFERENCE_PLANS.csv` and produces:

- **Plot 12 — per-domain reference plan-length boxplot.** Coarse difficulty ranking that doesn't depend on the LLMs. Confirms (e.g.) that blocksworld instances need substantially longer plans than basic_move.
- **Plot 13 — per-instance reference difficulty within each domain.** Sorted bar of plan_len per instance. Shows whether the instance set has a smooth difficulty gradient or sharp jumps.
- **Plot 15 — reference difficulty vs empirical model performance.** Scatter of optimal plan length (x) vs mean LLM partial validity across all 10 (model, condition) cells (y), one point per (domain, instance). The slope and correlation coefficient quantify whether longer reference plans really are harder for LLMs.

For domains without reference plans (citycar, tetris), Plot 14 supplies an alternative x-axis: **per-instance solve-rate across the 5×2 = 10 LLM cells.** "Universal-easy" instances solve in most cells; "universal-hard" in none. This works for any domain because it's derived from the run metrics, not from a planner.

### TL;DR

Reference plans answer: *"How short a plan does this problem actually need?"*  
LLM run metrics answer: *"How well did the model do?"*  
Putting them on the same axis is what makes the difficulty analysis quantitative rather than anecdotal.

## Quick Start

```bash
# Day 0 — local shake-out (~½ day, before any SLURM)
python -m venv .venv
# Linux/macOS:        source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Install VAL — see "Validator" section below for OS-specific instructions.

# Run the smoke test for all 3 domains × 2 conditions with the stub model
bash scripts/local/smoke_test.sh

# Day 1 — submit all SLURM jobs on Leonardo
bash scripts/slurm/submit_all.sh

# Ingest + plot (after jobs finish)
jupyter notebook notebooks/results_analysis.ipynb
```

For local config overrides that shouldn't be committed (e.g. dev paths, dtype tweaks),
use [config.local.yml](config.local.yml) — it shadows `config.yml` at runtime.

## Plug in your own model or domain

This repo is set up so a new model or domain drops in with **a handful of one-line
edits**, no Python changes. Concrete recipes:

- **New model** (local, single GPU): just pass `--weights_path <hf-repo-id>` — HF
  weights auto-download, output goes to `src/results/<basename>/`. Add an alias to
  [config.yml](config.yml) `models.active` if you want a tidy `--model my_alias`.
  For SLURM, also add a `case` arm in [scripts/slurm/run.sh](scripts/slurm/run.sh)
  and a profile entry in [scripts/slurm/submit_all.sh](scripts/slurm/submit_all.sh).
  Full contract: [src/models/README.md](src/models/README.md).

- **New domain**: drop `src/data/<your-domain>/{domain.pddl, instance-NN.pddl}`,
  add the name to [config.yml](config.yml) `domains.available`, and add a
  `<NAME>_DESCRIPTION` constant + `DOMAIN_DESCRIPTIONS` entry in
  [src/prompts/descriptions.py](src/prompts/descriptions.py). Optional but
  recommended: run `python scripts/verify/validate_instances.py --domains <your-domain>`
  to generate `REFERENCE_PLANS.csv` for the difficulty plots. Full contract:
  [src/data/README.md](src/data/README.md).

Smoke-test either before launching a real model:

```bash
python src/main.py --domain <your-domain> --condition baseline --model stub --iterations 1
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
│   │   ├── blocksworld/  citycar/  tetris/                  # active, main slate (20 instances each)
│   │   ├── basic_move/  visit-all/  satellite/              # active, short slate (10 instances each)
│   │   └── {folding,gripper,hanoi,labyrithn,logistics,monkey,shoe-sock,travel}/  # dormant
│   ├── results-final/                                       # checked-in run outputs (path is git-ignored as `src/results-final`)
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

Consumer-GPU fallback (8B–14B range) is available if HPC access is revoked mid-project.

## Validator

Plans are validated with [KCL-Planning/VAL](https://github.com/KCL-Planning/VAL).
Verbose output (per-step action validity) feeds the per-problem feature extractor.

The repo expects a `Validate` (or `Validate.exe`) binary at `VAL/`. Two paths to get it:

**Windows.** A pre-built `VAL/Validate.exe` is committed in this repo (Jan Dolejsi's
PDDL-extension build). No setup needed; verify with:

```powershell
VAL\Validate.exe --help
```

`config.yml` already sets `VAL_EXECUTABLE: "Validate.exe"` for this case.

**Linux / Leonardo.** Build VAL from source and drop the binary into `VAL/`:

```bash
git clone https://github.com/KCL-Planning/VAL /tmp/VAL && cd /tmp/VAL
./scripts/linux/build_linux64.sh all Release
cp build/linux64/Release/bin/Validate <repo>/VAL/Validate
cd <repo> && VAL/Validate --help
```

Then set `VAL_EXECUTABLE: "Validate"` (no `.exe`) in `config.yml` —
or, locally, in `config.local.yml`.

## Problem Sources

Planning problems are PDDL instances from the [potassco/pddl-instances](https://github.com/potassco/pddl-instances) repository and the Project A problem collection:

- [Tetris (IPC 2014)](https://github.com/potassco/pddl-instances/tree/master/ipc-2014/domains/tetris-sequential-satisficing) — carried from Project B
- [City Car (IPC 2014)](https://github.com/potassco/pddl-instances/tree/master/ipc-2014/domains/city-car-sequential-satisficing) — carried from Project B
- **Blocksworld** — carried from Project A's [`problem_dataset/problems_all/blocksworld/`](../merolasinghdardouri2425-master/problem_dataset/problems_all/blocksworld/)
- **basic_move** and **visit-all** — Project A's `problem_dataset` (added in waves 2–3 to broaden domain coverage)
- **satellite** — IPC satellite domain (`:equality` extension); reference plans in [src/data/satellite/REFERENCE_PLANS.csv](src/data/satellite/REFERENCE_PLANS.csv) were transcribed from Fast Downward, since pyperplan can't parse `:equality`

See [src/data/README.md](src/data/README.md) for per-domain instance details.

## References

Literature reviewed for this study lives in [assets/literature/](assets/literature/).
