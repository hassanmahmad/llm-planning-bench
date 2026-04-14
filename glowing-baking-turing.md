# Controlled Comparative Study — 3 Families × 3 Domains × 2 Prompts, Full Rerun

*Aligned with the team's official course proposal "Systematic Evaluation of LLM Planning Capabilities Across Multiple Domains and Model Families" (AI in Industry, Università di Bologna, April 2026, team: Usama Shabbir Satti, Muhammad Fahim Asim, Hassan Ahmed Mujtaba).*

## Context

Two prior student projects investigated whether LLMs can solve PDDL planning problems using iterative validator-guided feedback, but neither gave a unified cross-model, cross-domain picture:

- **Project A — Merola et al.** (`merolasinghdardouri2425-master/`): LLaMA 3.3 70B across many domains (Blocksworld, Gripper, Logistics, Hanoi, …) + meta-networks for confidence estimation.
- **Project B — D'Ascenzo & Gentili** (`dascenzogentili2425-master/`): 4 models (LLaMA3-8B, Phi4-14B, Gemma3-27B, Kimi-Dev-72B) on 2 domains (City Car, Tetris), modular HPC-ready framework.

This plan delivers the team's four stated objectives:

1. **Unify** the two codebases into one pipeline for model loading, plan generation, validation, and results reporting.
2. **Run a controlled comparative study** — 3 LLM families × 3 planning domains × 2 prompting conditions × 4 iterations.
3. **Address the prompt-bias confound** — one prompt per (domain, condition), identical for every model, so differences reflect model capability rather than prompt tuning.
4. **Produce a comparative analysis** with success rates, iteration-convergence patterns, and domain-specific insights that extend both prior projects.

**Baked-in decisions**:
- **HPC confirmed** — CINECA/Leonardo access granted; plan assumes it (consumer-GPU fallback reduced to a one-line risk row).
- **No reuse of prior plans** — all cells re-run under the unified pipeline (pending supervisor confirmation per proposal §4.2 — revisit if they disagree).
- **Wrapper-level prompt harmonization** — shared system preamble, CoT scaffold, validation-feedback shell; each domain's core problem description stays verbatim from its original author.
- **Plan coexists with** [`smooth-snuggling-muffin.md`](smooth-snuggling-muffin.md) (the broader engineering-tour alternative).

---

## 1. Scope

**In**:
- 3 models × 3 domains × **2 prompting conditions (Baseline + CoT)** = **18 cells, all newly generated**.
- 20 instances per domain (as used by both prior projects).
- **Stop-on-success** iteration policy: up to 4 iterations; stop as soon as a plan validates. Record `first_valid_iter ∈ {1,2,3,4,null}`. Matches Project B's original behavior and the proposal's "up to 4 rounds" phrasing; avoids ~30-50% of wasted generations vs. fixed-K.
- Standardized generation config (temperature, top-p, max-tokens, stop tokens, seed) identical across all 3 models.
- Wrapper-harmonized prompts (see §4), with Baseline and CoT differing *only* in the CoT scaffold.
- VAL-verbose feature extraction per iteration (valid-action %, consecutive valid steps, logical violations, plan length).
- Comparative analysis notebook producing every deliverable under objective #4.

**Out** (explicitly):
- Meta-network / confidence-estimation model (Project A's downstream work — dataset columns are preserved for whoever picks it up later, but no model is trained here).
- Extra domains beyond the 3 (Gripper, Logistics, Hanoi, Folding, etc. from Project A remain in the codebase as `domains.available` but are not run).
- Reuse of Project A's LLaMA 3.3 70B Blocksworld plans or Project B's LLaMA3-8B / Phi-4 plans.
- Reasoning-mode toggles (Qwen3 `/think` etc.) — treated as a prompt/mode confound.

## 2. Model slate (matches proposal §3.2)

| Alias    | HF repo                               | Family    | Params | Role                          |
|----------|---------------------------------------|-----------|--------|-------------------------------|
| llama8   | `meta-llama/Llama-3.1-8B-Instruct`    | Meta      | 8B     | Retained from Project B; **intra-family scale anchor (small)** |
| qwen25   | `Qwen/Qwen2.5-32B-Instruct`           | Alibaba   | 32B    | **New addition** — different family, recent, dense mid-size |
| llama33  | `meta-llama/Llama-3.3-70B-Instruct`   | Meta      | 70B    | Retained from Project A; **intra-family scale anchor (large)** |

**Why this slate**:
- **Two Llama variants (8B + 70B)** → supports the proposal's implied "same-family scale effect" comparison (does a 9× parameter jump within the same family improve PDDL planning?).
- **Qwen2.5-32B** → different architectural family (Alibaba), sits between 8B and 70B by params, dense (no MoE), recent release. Preferred over DeepSeek (MoE complicates serving) and Mistral (Mistral-Small-24B is a sensible swap if Qwen is unavailable).
- All three dense → lets the "params vs success rate" plot stay interpretable.

**Third-model swap flexibility**: if Qwen2.5-32B has availability issues, candidate alternates are `mistralai/Mistral-Small-24B-Instruct-2501` or `Qwen/Qwen2.5-14B-Instruct` (cheaper). Decision-by date: end of Day 0.

### Standardized generation config (applied to every model, logged per job)

```yaml
generation:
  temperature: 0.6
  top_p: 0.95
  max_new_tokens: 4096
  stop: null
  seed: 42
```

No per-model overrides. Report methodology section lists every value.

## 3. Unified pipeline policy

- **Iteration policy**: stop-on-success, up to 4 iterations. On every iteration — **before** checking validity — write the plan text to disk and append a feature row to `run_metrics.csv`. If validation passes, set `first_valid_iter` and break out of the loop (no further iterations). If all 4 fail, `first_valid_iter = null`.
- **Output schema** — per-iteration row in `run_metrics.csv` (1 to 4 rows per instance):
  ```
  model, domain, prompting_condition, instance, iteration,
  plan_text, plan_len, solves_problem,
  valid_action_percent, consecutive_valid_steps, logical_violations,
  wallclock_s, prompt_tokens, completion_tokens
  ```
  The new column `prompting_condition ∈ {baseline, cot}` is the key addition vs. prior projects.
- **Feature extractor**: port `run_val_verbose` + `parse_val_output` from [merolasinghdardouri2425-master/utils/dataset_generator.py L23-63](d:\hassan-uni\AII\project\merolasinghdardouri2425-master\utils\dataset_generator.py#L23-L63) into `src/utils/metrics_extractor.py`. Drop meta-network-related code.
- **Patch site**: [src/core/model_manager.py L247-249](d:\hassan-uni\AII\project\dascenzogentili2425-master\src\core\model_manager.py#L247-L249) — **keep** the early-return on success; add per-iteration disk writes and `metrics_extractor` calls **before** the validity check so failed iterations are also logged.

## 4. Prompt harmonization (core methodological contribution)

Both prior projects already use one prompt text per domain across all their models — verified: [prompts.py:128-171 (Project B)](d:\hassan-uni\AII\project\dascenzogentili2425-master\src\prompts\prompts.py#L128-L171) and [prompts.py:11-54 (Project A)](d:\hassan-uni\AII\project\merolasinghdardouri2425-master\llama_planning_framework\prompts.py#L11-L54). Model type is never used to branch prompt content. But the two prompt sets were written by different authors in different styles, so we harmonize the **wrappers** around each domain's problem description.

### 4a. Shared shell (identical across all 3 domains × 3 models)

- `SYSTEM_PROMPT_PDDL` — single string: role definition, PDDL conventions preamble, output-format directive. Derived from Project B's `system_prompt_pddl` at [prompts.py:23-36](d:\hassan-uni\AII\project\dascenzogentili2425-master\src\prompts\prompts.py#L23-L36), generalized for all 3 domains.
- `COT_SCAFFOLD(domain_description, problem)` — single function producing the "think step by step before answering" block.
- `VALIDATION_FEEDBACK_TEMPLATE(val_output, previous_plan)` — single function turning VAL-verbose output into structured feedback; one template shape applies to all domains.

### 4b. Domain-specific core (verbatim from original authors)

- `BLOCKSWORLD_DESCRIPTION` — Project A's blocksworld description, unchanged.
- `CITYCAR_DESCRIPTION` — Project B's citycar description, unchanged.
- `TETRIS_DESCRIPTION` — Project B's tetris description, unchanged.

### 4c. The two prompting conditions (proposal §3.3)

| Condition   | Composition                                                                               |
|-------------|-------------------------------------------------------------------------------------------|
| `baseline`  | `SYSTEM_PROMPT_PDDL` + `DOMAIN_DESCRIPTION` + `pddl_domain` + `pddl_problem` (zero-shot, direct) |
| `cot`       | `SYSTEM_PROMPT_PDDL` + `COT_SCAFFOLD(DOMAIN_DESCRIPTION, pddl_problem)` + `pddl_domain` + `pddl_problem` (reasoning-step prefix) |

```python
def build_problem_prompt(domain: str, condition: str,
                         pddl_domain: str, pddl_problem: str) -> str:
    description = DOMAIN_DESCRIPTIONS[domain]
    if condition == "baseline":
        return f"{SYSTEM_PROMPT_PDDL}\n\n{description}\n\n{pddl_domain}\n\n{pddl_problem}"
    elif condition == "cot":
        return f"{SYSTEM_PROMPT_PDDL}\n\n{COT_SCAFFOLD(description, pddl_problem)}\n\n{pddl_domain}\n\n{pddl_problem}"
```

For a given (domain, condition, instance), **every model sees the byte-identical string**. Verified by §8.2.

## 5. Repo structure (minimal)

```
llm-planning-bench/
  README.md
  STEPS_controlled.md                      # execution doc for this plan
  config.yml                               # one cluster (Leonardo), no layering
  requirements.txt
  VAL/
  src/
    main.py                                # --model ∈ {llama8, qwen25, llama33, stub}
                                           # --condition ∈ {baseline, cot}
    core/
      model_manager.py                     # patched for fixed-K + per-iter writes
      pddl_processor.py                    # prompt router (3 domains × 2 conditions)
      pddl_planner.py, file_manager.py     # verbatim from Project B
    prompts/
      shell.py                             # SYSTEM_PROMPT_PDDL, COT_SCAFFOLD, VALIDATION_FEEDBACK_TEMPLATE
      descriptions.py                      # {BLOCKSWORLD,CITYCAR,TETRIS}_DESCRIPTION
      compose.py                           # build_problem_prompt(domain, condition, ...)
    utils/
      validator.py                         # + validate_plan_verbose
      metrics_extractor.py                 # NEW — ported from Project A
      {configuration,logging,answer_postprocessor,common}.py  # verbatim from Project B
    data/
      blocksworld/   citycar/   tetris/    # 20 instances each
    results/
      {model}/{domain}/{condition}/instance-XX_iter_{k}.txt
      {model}/{domain}/{condition}/instance-XX_plan.txt
      {model}/{domain}/{condition}/run_metrics.csv
      summary.csv
  scripts/
    local/smoke_test.sh                    # Day-0 gate
    slurm/run.sh                           # parametric (MODEL, DOMAIN, CONDITION)
    slurm/submit_all.sh                    # iterate 3×3×2 = 18 submissions
  notebooks/results_analysis.ipynb
  report/                                  # LaTeX + PDF
  slides/
```

## 6. Analysis deliverables (objective #4)

All plots / tables read from the unified `run_metrics.csv` files.

### Primary (proposal §3.4)
1. **Success-rate matrix** — model × domain × condition, 18 cells with 95% CIs.
2. **Iteration-gain curve** — cumulative % solved at iter 1, 2, 3, 4, per (model, domain, condition). Proposal metric.
3. **Average iterations to convergence** (for solved problems only) per cell.
4. **Per-problem feature distributions** — valid-action %, consecutive valid steps, logical violations, plan length. Kept rich for dataset construction (proposal §3.4).

### Secondary (extends prior work)
5. **Baseline-vs-CoT delta plot** — success-rate Δ = CoT − Baseline per (model, domain). Answers the headline question: does chain-of-thought help planning, and does it help *uniformly* across families?
6. **Intra-family scale scatter** — LLaMA3-8B vs LLaMA 3.3 70B on matched (domain, condition) cells. Answers: does the 9× parameter jump translate to PDDL planning success? Extends Project B's single-family-single-size setup.
7. **Cross-family comparison** — Meta (pooled 8B+70B) vs Alibaba (32B) on matched cells.
8. **First-valid-iteration distribution** — stacked bar per cell; port of Project A's `iteration_justification_plots.png`.
9. **Partial-credit boxplot** — `valid_action_percent` on failed plans, per cell.
   - **Caveat under stop-on-success**: iteration *k* only contains instances that failed iterations 1..*k-1*, so later iterations reflect increasingly hard residuals (selection bias). Document this in any figure that shows metrics per-iteration.
10. **Domain-difficulty ranking** — pooled success across models and conditions.

Report tables: 18-cell success matrix with CIs; family-level summary; CoT-effect per (model, domain); median iterations-to-first-valid (IQR).

## 7. Day-by-day (3 people, 4 days + Day 0)

Roles:
- **P1 = Pipeline + HPC** (Usama or Fahim): core ports, model_manager patch, metrics extractor, validator, SLURM scripts, job monitoring, OOM/timeout triage.
- **P2 = Prompts + Methodology** (Fahim or Hassan): harmonized shell + descriptions + compose, Baseline/CoT conditions, prompt-identity verification (§8.2), generation-config uniformity (§8.4), methodology writeup.
- **P3 = Analysis + Reporting** (Hassan or whoever): notebook, the 10 plots, report LaTeX, slides, dry-run.

### Day 0 — Local shake-out (mandatory, ½ day)
- **P1**: stub model backend, `scripts/local/smoke_test.sh` runs 1 instance per domain × each condition (6 runs).
- **P2**: first draft of harmonized `shell.py` + `descriptions.py` + `compose.py`; prompt-identity check script (dump prompts for stub, diff).
- **P3**: notebook skeleton — all 10 plot cells with dummy 18-cell dataframes so plots render before data lands.
- **Gate**: no SLURM submissions until stub pipeline produces parseable `run_metrics.csv` (with the new `prompting_condition` column populated) and plan files for all 3 domains × 2 conditions.

### Day 1 — Port, patch, submit all 18
- **P1 (0-3h)**: port `metrics_extractor.py`; patch `model_manager.py` L247-249 for fixed-K + per-iter writes; add `validate_plan_verbose` to `validator.py`; wire `prompting_condition` through to the CSV writer.
- **P1 (3-5h)**: parametric `scripts/slurm/run.sh` with 3 profiles — `small` (1× A100-80GB, llama8, 3h walltime); `mid` (2× A100-80GB, qwen25, 10h walltime); `large` (2× A100-80GB FP8, llama33, 14h walltime).
- **P1 (5-7h)**: `submit_all.sh` launches all **18 jobs in parallel** (3 models × 3 domains × 2 conditions). Record JobIDs in `scripts/slurm/SUBMITTED.md`.
- **P2 (parallel)**: finalize prompt harmonization; run `prompt-identity check` — byte-diff prompts across all 3 models for `instance-01` in each (domain, condition); commit the 6 reference prompt artifacts as test fixtures.
- **P3 (parallel)**: notebook cells 1-4 (success matrix, iteration-gain curves, avg iterations, per-problem distributions) driven by dummy data; report outline + intro draft.

### Day 2 — Monitor + ingest Llama8 & Qwen25
- **P1**: queue watch; OOM / timeout triage; llama8 finishes by ~noon (6 cells); qwen25 by EOD.
- **P2**: methodology section of the report (prompt-bias framing, harmonization design, generation-config uniformity table, verification checks).
- **P3**: as cells land, ingest into notebook; produce first real versions of plots 1-4 on the 12 populated cells (llama8 + qwen25); draft results-so-far section.

### Day 3 — Llama33 finishes, full analysis
- **P1**: llama33 FP8 cells finish overnight Day 2 → Day 3 morning; handle any reruns.
- **P2**: cross-check: re-run prompt-identity verification over actual job logs; write the "defending the uniformity claim" paragraph.
- **P3**: all 18 cells populated → finalize all 10 plots; write results + discussion; headline findings: (a) intra-family scale effect, (b) CoT delta, (c) domain difficulty, (d) iteration convergence.

### Day 4 — Polish, ship
- **P1**: README, reproduction walkthrough, final git tag, archive SLURM logs.
- **P2**: methodology + limitations section polish; list of every design decision with defense.
- **P3**: report PDF final pass; slide deck (10-12 slides: motivation → pipeline → slate → prompt harmonization → 18-cell results → CoT delta → scale effect → domain difficulty → limits → next steps); full dry-run.

## 8. Verification

1. **Local smoke test (Day 0 gate)**: stub × 1 instance × 3 domains × 2 conditions → 4 iter files each + populated `run_metrics.csv` (24 rows, `prompting_condition` column populated) + parseable plan files. Project B's notebook `parse_result_file()` must still work.
2. **Prompt-identity check**: for each (domain, condition, instance=01), dump the final prompt string sent to each of the 3 models; pairwise byte-diff → must be identical across models. Save the 6 reference prompts as test fixtures in `src/tests/fixtures/prompts/`.
3. **Condition-differentiation check**: for each (domain, instance=01), diff `baseline` prompt against `cot` prompt → must differ ONLY in the CoT scaffold block (verify via regex).
4. **Generation-config identity check**: log resolved generation config at job start; grep all 18 job logs → all 18 configs byte-identical.
5. **Validator parity**: run `validate_plan_verbose` on one known-valid + one known-invalid plan from Project A's `generated_plans/`; must match Project A's existing CSV entries (sanity check for extractor port).
6. **Row-count check**: `summary.csv` must contain one row per (model, domain, condition, instance, iteration). Under stop-on-success, row count varies with success patterns; the upper bound is **1,440 rows** (3 × 3 × 2 × 20 × 4) and the lower bound is **720 rows** (everyone succeeds at iter 1). Sanity check: every (model, domain, condition, instance) group has 1-4 rows, last row's `solves_problem` is either True (stopped early) or False (exhausted 4 iters).
7. **Notebook regression**: every cell runs to completion on the final data; each figure has a caption and is referenced from the report.

## 9. Risks and fallbacks

| Risk | Fallback |
|------|----------|
| LLaMA 3.3 70B FP8 OOM on 2× A100-80GB | Bump to TP=4 or drop to AWQ/GPTQ INT4 on 1× A100-80GB. |
| Qwen2.5-32B unavailable / serving issue | Swap to `mistralai/Mistral-Small-24B-Instruct-2501` (decision by end of Day 0). |
| HPC access suddenly revoked mid-project | Drop to consumer-GPU slate: llama8 + Phi4-14B + Qwen2.5-7B. Methodology + 10 plots stay identical; lose the 70B scale-effect axis; proposal §4.1 pre-authorizes this scope reduction. |
| Day 3 end, LLaMA 3.3 70B cells still running | Ship with 12/18 cells + partial 70B; label as preliminary. Do NOT fall back to reusing Project A's legacy plans — it re-introduces the exact confound this plan eliminates. |
| Wrapper harmonization breaks Project B's Tetris/CityCar output parseability | Budget 2h Day 1 "harmonization smoke": stub × known-solvable instance per (domain, condition); if `answer_postprocessor` fails, revert that domain's wrapper to original and document as exception. |
| CoT condition wall-clock much heavier than Baseline (longer completions) | Run CoT cells first in the queue; Baseline cells are cheaper and can slot into idle queue time. |
| VAL version drift Leonardo vs. local | Pin VAL commit SHA; verify via `VAL/Validate --version` at job start. |
| Supervisor rejects "no reuse" decision (proposal §4.2 open) | Cheapest compromise: rerun the 3 retained-model × retained-domain cells (LLaMA 3.3 70B × Blocksworld, LLaMA 8B × {CityCar, Tetris}) under the unified pipeline — which this plan already does anyway — and cite prior projects as descriptive context only. |

## 10. Critical files to touch

- [src/core/model_manager.py L247-249](d:\hassan-uni\AII\project\dascenzogentili2425-master\src\core\model_manager.py#L247-L249) — iteration loop patch (Project B file).
- [src/core/pddl_processor.py](d:\hassan-uni\AII\project\dascenzogentili2425-master\src\core\pddl_processor.py) — prompt router (domain × condition) + metrics_extractor hook.
- [src/utils/validator.py](d:\hassan-uni\AII\project\dascenzogentili2425-master\src\utils\validator.py) — add `validate_plan_verbose`.
- [utils/dataset_generator.py L23-63](d:\hassan-uni\AII\project\merolasinghdardouri2425-master\utils\dataset_generator.py#L23-L63) — source for `src/utils/metrics_extractor.py` (Project A file).
- `src/prompts/shell.py` / `descriptions.py` / `compose.py` — NEW, replaces Project B's monolithic `prompts.py`.
- [scripts/gemma3_iters_4_tetris.sh](d:\hassan-uni\AII\project\dascenzogentili2425-master\scripts\gemma3_iters_4_tetris.sh) — template for parametric `scripts/slurm/run.sh` (Project B file).
- [Results Analysis.ipynb](d:\hassan-uni\AII\project\dascenzogentili2425-master\Results Analysis.ipynb) — base for the extended notebook (Project B file).

## 11. Traceability to the proposal

| Proposal section | Plan coverage |
|---|---|
| §1 Context — merges A (Merola) + B (D'Ascenzo) | §Context |
| §2 Objective 1 (unify codebases) | §1, §5, §10 |
| §2 Objective 2 (3 families × 3 domains × 4 iter) | §1, §2, §3 |
| §2 Objective 3 (prompt-bias confound) | §4, §8.2, §8.3 |
| §2 Objective 4 (comparative analysis) | §6 |
| §3.1 Domains (Blocks World, City Car, Tetris) | §5 data/, §6 |
| §3.2 Models (70B retained, 8B retained, new family) | §2 |
| §3.3 Baseline + CoT prompting conditions | §4c, §7, §8.3 |
| §3.4 Metrics (success, avg iter, iter gain, per-problem features) | §6 primary |
| §4.1 Compute (CINECA) | HPC confirmed; fallback in §9 |
| §4.2 Data reuse (open) | Current default: no reuse; §9 last row handles alternative |
| §4.3 Deliverable format (open) | Report + slides + repo assumed; Day 4 covers all three |

---

## Differences from `smooth-snuggling-muffin.md` (the broader alternative)

| Aspect | `smooth-snuggling-muffin` | `glowing-baking-turing` (this) |
|---|---|---|
| Cell count | 9 (3 E + 6 N, single prompting condition) | 18 (all N, Baseline + CoT) |
| Prior-plan reuse | 60 plans reused | None — every cell re-runs |
| Prompting conditions | 1 (bundled CoT) | 2 (Baseline + CoT, proposal §3.3) |
| Model slate | Phi-4 14B + Qwen3-32B + LLaMA 3.3 70B | LLaMA3-8B + Qwen2.5-32B + LLaMA 3.3 70B (proposal §3.2) |
| Scale-effect comparison | Cross-family at 3 sizes | Intra-family (Llama 8B vs 70B) + cross-family |
| Team size in day-split | 2 people | 3 people (matches proposal) |
| Project A/B labels | Swapped vs proposal | Correct (A = Merola, B = D'Ascenzo) |
| Optional tracks (§9A/B/C) | Present | Dropped — proposal scope only |
| Framing | Engineering tour | Controlled experiment matching the proposal verbatim |

**Pick this plan** for submission alignment — it tracks the proposal's objectives, metrics, model slate, and prompting conditions exactly. The broader plan remains useful as a reference for optional extensions if the core study finishes early.
