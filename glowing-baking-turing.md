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

### 2a. Core slate (waves 1–2, the proposal's 18 cells)

| Alias    | HF repo                               | Family    | Params | Wave | Role                          |
|----------|---------------------------------------|-----------|--------|------|-------------------------------|
| llama8   | `meta-llama/Llama-3.1-8B-Instruct`    | Meta      | 8B     | 1    | Retained from Project B; **intra-family scale anchor (small)** |
| qwen25   | `Qwen/Qwen2.5-32B-Instruct`           | Alibaba   | 32B    | 1    | **New addition** — different family, recent, dense mid-size |
| llama33  | `meta-llama/Llama-3.3-70B-Instruct`   | Meta      | 70B    | 2    | Retained from Project A; **intra-family scale anchor (large)** |

**Why this slate**:
- **Two Llama variants (8B + 70B)** → supports the proposal's implied "same-family scale effect" comparison (does a 9× parameter jump within the same family improve PDDL planning?).
- **Qwen2.5-32B** → different architectural family (Alibaba), sits between 8B and 70B by params, dense (no MoE), recent release.
- All three dense → the "params vs success rate" plot stays interpretable.

### 2b. Wave 3 — exploratory comparison additions

Wave 1 ([report/wave1_findings.md](report/wave1_findings.md)) showed a stark result on the 12 wave-1 cells: only `qwen25/blocksworld` produced any solves (5/120), and `llama8` did not solve a single instance across any of its 6 cells. Vanilla instruction-tuned models appear to be the bottleneck, not the harness or prompts. Two additions probe two distinct hypotheses while keeping all other axes (domains, prompts, generation config, iteration policy) unchanged:

| Alias      | HF repo                                              | Family    | Params | Hypothesis tested |
|------------|------------------------------------------------------|-----------|--------|-------------------|
| qwq32      | `Qwen/QwQ-32B`                                       | Alibaba   | 32B    | Does **reasoning-style post-training** on the same base lift solve rate? |
| mistral24  | `mistralai/Mistral-Small-24B-Instruct-2501`          | Mistral   | 24B    | Does a **fourth, recent dense family** at the qwen25 size band behave differently? |

**Why these two specifically**:
- **`qwq32`** is built on the same Qwen2.5-32B base as `qwen25`, with reasoning-style post-training added. Pairing it with `qwen25` isolates "reasoning post-training" as the *only* changing variable — the cleanest controlled comparison the slate can support given wave 1's finding that the qwen25/blocksworld cell is the only one with traction. If reasoning post-training helps PDDL planning, qwq32 should show measurable solve-rate gain on blocksworld and meaningful vap (valid-action %) gain on citycar/tetris over qwen25 under both prompting conditions.
- **`mistral24`** adds a fourth model family (Mistral) at almost the same parameter count as `qwen25` (24B vs 32B). It tests whether the wave-1 cross-family signal (Meta-8B at 0/120 vs Alibaba-32B at 5/120) replicates when we swap in another vendor at the same scale band — i.e., whether the gap is "Meta vs Alibaba" or "small vs mid-size", or genuinely model-specific. We use the **2501 text-only release** (`Mistral-Small-24B-Instruct-2501`) rather than the more recent 2503 / "3.1" release: the 3.1 release is multimodal (`Mistral3ForConditionalGeneration`, requires vLLM + `mistral_common` tokenizer) and would force a backend swap that breaks parity with waves 1/2. The 2501 release is the same 24B dense model and the direct text-only ancestor of 3.1, loadable via the existing `AutoModelForCausalLM` path.

**Why not other candidates considered**:
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` — overlaps too heavily with `qwq32` (both are reasoning-distilled Qwen2.5-32B variants). Pick one; QwQ is the original-vendor release.
- `google/gemma-3-27b-it` — adds Google as a fifth family, attractive but Gemma3-27B is already covered in Project B's prior runs and wave 3 budget is tight.
- `microsoft/phi-4` (14B) — already used in Project B; adds little new information.
- Full `DeepSeek-V3` / `R1` — 671B MoE, won't fit on Leonardo's 4× A100-64GB nodes within the proposal's compute envelope.
- `Qwen/Qwen3-30B-A3B-Instruct` — MoE complicates serving; the proposal's "all dense" interpretability constraint applies.

**Wave 3 additive cell count**: 2 models × 3 domains × 2 conditions = **12 extra cells**, run after wave 2 completes. The core 18-cell deliverable (proposal §3.4) is unaffected — wave 3 is reported in a separate "exploratory extensions" section of the report.

**Caveat for `qwq32`**: it emits a `<think>...</think>` reasoning trace before the final answer. The harness already strips these via `clean_response_text` in [src/core/model_manager.py](src/core/model_manager.py) before re-prompting on iter 2+, so iteration accounting is clean, but completion-token totals on `qwq32` cells will run noticeably higher than `qwen25`. Worth a 12288-token cap (vs the wave-1/2 cap of 8192) for QwQ to avoid the cap-collision pattern that hit `llama8` in wave 1 (see [report/wave1_findings.md §5](report/wave1_findings.md)).

**Third-model swap flexibility (core slate)**: if Qwen2.5-32B had availability issues, candidate alternates were `mistralai/Mistral-Small-24B-Instruct-2501` or `Qwen/Qwen2.5-14B-Instruct`. With wave 3, `mistral24` is now part of the slate explicitly, so this fallback collapses naturally.

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

## 12. Wave 3 — running the exploratory additions

Wave 3 launches **after wave 2 finishes** (i.e. all six `llama33/{domain}/{condition}` cells from [scripts/slurm/SUBMITTED.md](scripts/slurm/SUBMITTED.md) are in the `COMPLETED` state and `src/results/llama33/**/run_metrics.csv` files are populated). Wave 3 reuses the same parametric pipeline — it is just two more entries in `MODELS_OVERRIDE`.

### 12.1 Pre-flight (run on a Leonardo login node, from project root)

Leonardo Booster compute nodes have **no outbound internet access**, so weights must be staged from the login node before any `sbatch` runs. We use the same `src/models/<dir>` convention as waves 1 and 2 — `run.sh` detects `${LOCAL_WEIGHTS}/config.json` and resolves `WEIGHTS_SOURCE=local`, avoiding any HF cache lookup at job time.

```bash
# 1. Confirm wave 2 finished cleanly (all 6 llama33 cells present)
ls src/results/llama33/*/{baseline,cot}/run_metrics.csv | wc -l   # → expect 6

# 2. HF auth — both repos are gated. Visit each model card once in a browser
#    to accept the license, then log in with a read-token from
#    huggingface.co/settings/tokens
huggingface-cli login

# 3. Download weights into src/models/<dir> (same layout as waves 1–2).
#    --local-dir-use-symlinks=False writes real files (not cache symlinks)
#    so the dir is self-contained and survives an HF cache wipe on $WORK.
huggingface-cli download Qwen/QwQ-32B \
  --local-dir src/models/QwQ32 \
  --local-dir-use-symlinks False

huggingface-cli download mistralai/Mistral-Small-24B-Instruct-2501 \
  --local-dir src/models/MistralSmall \
  --local-dir-use-symlinks False

# 4. Sanity check — config.json must exist for run.sh's "local" branch to fire
[ -f src/models/QwQ32/config.json ]        && echo "qwq32 OK"
[ -f src/models/MistralSmall/config.json ] && echo "mistral24 OK"

# 5. Smoke-test prompts locally with the stub backend (no GPU needed,
#    confirms the prompt pipeline still parses for both new model aliases).
bash scripts/local/smoke_test.sh
```

**Disk budget**: `Qwen/QwQ-32B` ≈ 64 GB, `Mistral-Small-24B-Instruct-2501` ≈ 48 GB. Together with the wave-1/2 weights already in `src/models/`, total project-tree weight footprint is ~250 GB. `src/models/` should live on `$WORK` (typically 1 TB on Leonardo), not `$HOME` — symlink the dir if needed:

```bash
# One-time, only if src/models/ is currently on $HOME:
mv src/models "${WORK}/llm-planning-bench-models"
ln -s "${WORK}/llm-planning-bench-models" src/models
```

### 12.2 Submit wave 3 (12 cells)

```bash
# From project root, on Leonardo login node:
MODELS_OVERRIDE="qwq32 mistral24" bash scripts/slurm/submit_all.sh
```

`submit_all.sh` will create 12 sbatch jobs (2 models × 3 domains × 2 conditions), each on the `mid` profile (`--time=10:00:00 --gres=gpu:2`, matches `qwen25`). Track them in [scripts/slurm/SUBMITTED.md](scripts/slurm/SUBMITTED.md) — a fresh dated block is appended on every run.

### 12.3 Monitor

```bash
squeue -u "$USER" -o "%.10i %.30j %.2t %.10M %.20R"
tail -f scripts/slurm/logs/qwq32_blocksworld_baseline_*.out
```

### 12.4 Verify per-cell

After each cell completes, check the run produced 1–4 rows per instance in `run_metrics.csv` and the `prompting_condition` column is populated:

```bash
python - <<'PY'
import pandas as pd, glob
for f in sorted(glob.glob("src/results/{qwq32,mistral24}/*/{baseline,cot}/run_metrics.csv")):
    df = pd.read_csv(f)
    n_inst = df["instance"].nunique()
    n_solv = df.groupby("instance")["solves_problem"].any().sum()
    print(f"{f}: {len(df)} rows, {n_inst} instances, {n_solv} solved")
PY
```

### 12.5 Ingest into the analysis notebook

`notebooks/results_analysis.ipynb` reads from `src/results/**/run_metrics.csv` via a glob, so the wave-3 cells appear automatically once present. Re-run the notebook end-to-end. Two new comparisons fall out of the wave-3 data and should be added as report figures:

1. **`qwq32` vs `qwen25`** at matched (domain, condition) — isolates the reasoning-post-training effect on the same base. Plot solve-rate Δ + mean-vap Δ with paired-by-instance 95% CIs.
2. **`mistral24` vs `qwen25`** at matched (domain, condition) — cross-family comparison at the same parameter band. Plot the same two deltas.

If `qwq32` does not lift solve rate over `qwen25` on blocksworld, the discussion should note that reasoning post-training does not transfer to PDDL planning under our prompting setup — a result worth reporting either way.

### 12.6 Risks specific to wave 3

| Risk | Fallback |
|------|----------|
| `qwq32` think-trace blows past 8192-token cap and the harness extracts an incomplete plan | Bump `--max_tokens 12288` in the wave-3 sbatch flags, or in `config.yml > generation.max_new_tokens` (pre-cleared to differ from waves 1–2 since this is exploratory, not part of the proposal's controlled study). Document the per-wave cap in the report's reproducibility section. |
| `Mistral-Small-24B-Instruct-2501` chat template not auto-detected by the tokenizer | `model_manager.py._format_messages` already falls back to a minimal template; verify on a single instance via the smoke test before launching all 12 cells. |
| Leonardo queue saturated with wave 2 leftovers | Run wave 3 sequentially per model (`MODELS_OVERRIDE="qwq32"` then `MODELS_OVERRIDE="mistral24"`) instead of both at once. |
| Wave 3 results contradict wave 1's "qwen25 is the only solver" finding in a way that undermines the headline | Add to limitations rather than re-running wave 1; the controlled study's claim is bounded to its slate by design. |

### 12.7 Reporting

Wave 3 lives in a dedicated **§Exploratory Extensions** subsection in the report, *not* the headline §Results. Phrasing pattern: "Beyond the proposal's three-model slate, we ran two additional models (`qwq32`, `mistral24`) on the same 6 (domain, condition) cells to probe two specific hypotheses [reasoning post-training; family-band invariance]. Findings extend, but do not replace, the controlled three-family comparison."

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
