# STEPS — Controlled Comparative Study of LLM Planning

Step-by-step execution guide for [`../../../.claude/plans/glowing-baking-turing.md`](../../../.claude/plans/glowing-baking-turing.md) — the rigor-first plan aligned with the official course proposal.

**Team**: Usama Shabbir Satti, Muhammad Fahim Asim, Hassan Ahmed Mujtaba (3 people).
**Schedule**: Day 0 local shake-out (½ day) + 4 working days.
**Target**: 3 models × 3 domains × 2 prompting conditions = 18 cells, stop-on-success up to 4 iterations.

Attribution (matches proposal, **opposite** of how prior plans labeled these):
- **Project A = Merola et al.** → `merolasinghdardouri2425-master/` → Blocksworld + meta-networks.
- **Project B = D'Ascenzo & Gentili** → `dascenzogentili2425-master/` → City Car + Tetris, modular codebase.

Legend:
- **[P1]** = Pipeline + HPC (core ports, SLURM, monitoring)
- **[P2]** = Prompts + Methodology (harmonization, uniformity checks, methodology writeup)
- **[P3]** = Analysis + Reporting (notebook, plots, report, slides)
- **[ALL]** = joint
- Check off each box as you go. **Do not skip Day 0.**

---

## Day 0 — Local shake-out (½ day, MANDATORY before any SLURM)

Every bug caught locally is a SLURM queue slot saved.

### 0.1 Environment setup [P1]
- [ ] `cd llm-planning-bench/`
- [ ] Create venv: `python -m venv .venv && source .venv/Scripts/activate`
- [ ] `pip install -r requirements.txt`
- [ ] Install VAL locally — confirm `VAL/Validate --help` runs
- [ ] Local model backend for smoke tests (priority order):
  1. Stub model: `src/models/stub.py` returns a canned plan from disk (fastest, no GPU)
  2. `ollama pull qwen2.5:1.5b` + `ollama serve` (CPU, ~2 GB RAM)
  3. llama.cpp with a Q4 GGUF
- [ ] Create `config.local.yml`:
  - `cluster: local`
  - `val_path: ./VAL/Validate`
  - `model_backend: stub`

### 0.2 Config — domains, models, conditions, generation [P1]
- [ ] Add to `config.yml`:
  ```yaml
  domains:
    active: [blocksworld, citycar, tetris]
    available: [blocksworld, citycar, tetris, basic_move, folding, gripper, hanoi, labyrinth, logistics, monkey, shoe-sock, travel]
  models:
    active: [llama8, qwen25, llama33]
  conditions: [baseline, cot]
  generation:
    temperature: 0.6
    top_p: 0.95
    max_new_tokens: 4096
    stop: null
    seed: 42
  iteration:
    policy: stop_on_success
    max_iterations: 4
  ```
- [ ] In `src/main.py`: `--domain` choices from `config['domains']['available']`; `--model` choices `['llama8', 'qwen25', 'llama33', 'stub']`; add `--condition ∈ {baseline, cot}`.

### 0.3 Copy domain/instance files [P1]
- [ ] Active domains:
  ```
  cp -r ../merolasinghdardouri2425-master/problem_dataset/problems_all/blocksworld  src/data/blocksworld/
  cp -r ../dascenzogentili2425-master/src/data/citycar                              src/data/citycar/
  cp -r ../dascenzogentili2425-master/src/data/tetris                               src/data/tetris/
  ```
- [ ] Blocksworld only: pick 20 across difficulty tiers, rename to `instance-01.pddl` … `instance-20.pddl`, keep `INSTANCE_MAP.csv` mapping back to Project A's original names.
- [ ] CityCar + Tetris: already in the 20-instance format from Project B — keep as-is.
- [ ] Also copy the 9 additional Project A domains into `src/data/` for the `available` registry (native names intact, dormant):
  ```
  cp -r ../merolasinghdardouri2425-master/problem_dataset/problems_all/{basic_move,folding,gripper,hanoi,labyrithn,logistics,monkey,shoe-sock,travel} src/data/
  ```

### 0.4 Harmonized prompts [P2]
Replace Project B's monolithic `src/prompts/prompts.py` with a 3-file module:

- [ ] `src/prompts/shell.py`:
  - `SYSTEM_PROMPT_PDDL` (single string; generalize Project B's [prompts.py:23-36](../dascenzogentili2425-master/src/prompts/prompts.py#L23-L36) so it works for all 3 domains)
  - `COT_SCAFFOLD(description, problem)` → returns the "think step by step before answering" preamble block
  - `VALIDATION_FEEDBACK_TEMPLATE(val_output, previous_plan)` → single template shape for all domains
- [ ] `src/prompts/descriptions.py`:
  - `BLOCKSWORLD_DESCRIPTION` — verbatim from Project A's [prompts.py](../merolasinghdardouri2425-master/llama_planning_framework/prompts.py)
  - `CITYCAR_DESCRIPTION` — verbatim from Project B's [prompts.py:267-308](../dascenzogentili2425-master/src/prompts/prompts.py#L267-L308)
  - `TETRIS_DESCRIPTION` — verbatim from Project B's [prompts.py:128-171](../dascenzogentili2425-master/src/prompts/prompts.py#L128-L171)
  - Also add `None` placeholders for the 9 dormant domains with `# TODO: port if activated`
- [ ] `src/prompts/compose.py`:
  ```python
  def build_problem_prompt(domain, condition, pddl_domain, pddl_problem):
      desc = DOMAIN_DESCRIPTIONS[domain]
      if condition == "baseline":
          return f"{SYSTEM_PROMPT_PDDL}\n\n{desc}\n\n{pddl_domain}\n\n{pddl_problem}"
      elif condition == "cot":
          return f"{SYSTEM_PROMPT_PDDL}\n\n{COT_SCAFFOLD(desc, pddl_problem)}\n\n{pddl_domain}\n\n{pddl_problem}"

  def build_feedback_prompt(val_output, previous_plan):
      return VALIDATION_FEEDBACK_TEMPLATE(val_output, previous_plan)
  ```
- [ ] Extend `src/core/pddl_processor.py` prompt router to take `(domain, condition)` and call `compose.build_problem_prompt`. Raise `NotImplementedError` for any dormant domain whose description is `None`.

### 0.5 Stub model backend [P1]
- [ ] `src/models/stub.py`: same interface as `ModelManager` but `generate()` returns a fixed plan from `src/data/<domain>/stub_plans/<instance>.txt`
- [ ] Pre-populate `stub_plans/instance-01.txt` with a known-valid plan per active domain
- [ ] Exercises full pipeline (VAL, iteration loop, CSV writer, disk writes) without LLM compute

### 0.6 Notebook skeleton [P3]
- [ ] Copy `../dascenzogentili2425-master/Results Analysis.ipynb` → `notebooks/results_analysis.ipynb`
- [ ] Point input paths at `src/results/{model}/{domain}/{condition}/`
- [ ] Stub out all 10 plot cells with dummy 18-cell DataFrames so plots render before real data lands
- [ ] Preserve the existing cells from Project B's notebook — confirm they still run on dummy data

### 0.7 Smoke test [P1]
- [ ] `scripts/local/smoke_test.sh`:
  ```bash
  #!/bin/bash
  set -e
  for domain in blocksworld citycar tetris; do
    for condition in baseline cot; do
      python src/main.py --model stub --domain $domain --condition $condition \
        --instance instance-01 --iterations 4 --cluster local
    done
  done
  ```
- [ ] Run it. For each of the 6 (domain, condition) combinations confirm:
  - [ ] 1–4 files `src/results/stub/<domain>/<condition>/instance-01_iter_{k}.txt` exist (1 if stub plan is valid → stopped early; 4 if always invalid)
  - [ ] `run_metrics.csv` has matching row count, every row has non-null `valid_action_percent`, `prompting_condition` column populated
  - [ ] Final `instance-01_plan.txt` has Project B's `--- Processing Metadata ---` block
  - [ ] Project B's notebook `parse_result_file()` parses it cleanly

### 0.8 Third-model final pick [P1]
- [ ] Confirm `Qwen/Qwen2.5-32B-Instruct` is available on the HF mirror accessible from Leonardo
- [ ] If not: fall back to `mistralai/Mistral-Small-24B-Instruct-2501` — update `config.yml` `models.active`
- [ ] Decision documented in `scripts/slurm/SUBMITTED.md`

**Gate**: do NOT proceed to Day 1 until 0.7 passes for all 6 (domain, condition) combinations AND the third model is locked.

---

## Day 1 — Port, patch, submit all 18

### 1.1 Port VAL-verbose metrics extractor [P1, 0–1.5h]
- [x] Create `src/utils/metrics_extractor.py`
- [x] Lift `run_val_verbose` + `parse_val_output` from [../merolasinghdardouri2425-master/utils/dataset_generator.py L23–63](../merolasinghdardouri2425-master/utils/dataset_generator.py#L23-L63)
- [x] Strip every meta-network line. Pure function returning:
  ```python
  {"valid_action_percent": float, "consecutive_valid_steps": int,
   "logical_violations": int, "plan_length": int, "solves_problem": bool}
  ```
- [x] Unit test: one known-valid + one known-invalid plan from Project A's `generated_plans/` — outputs must match Project A's CSV entries

### 1.2 Patch the iteration loop for stop-on-success + per-iter logging [P1, 1.5–3h]
- [x] Open [`../dascenzogentili2425-master/src/core/model_manager.py`](../dascenzogentili2425-master/src/core/model_manager.py) → find `iterative_planning_with_validation` (~L189–263)
- [x] **Keep** the early-return at L247–249 — stop-on-success is the desired behavior
- [x] **Inside** the loop, **before** the validity check, add:
  - Write `instance-XX_iter_{k}.txt` to disk
  - Call `metrics_extractor.extract(...)` and append a row to `run_metrics.csv` with columns:
    `model, domain, prompting_condition, instance, iteration, plan_text, plan_len, solves_problem, valid_action_percent, consecutive_valid_steps, logical_violations, wallclock_s, prompt_tokens, completion_tokens`
- [x] Track `first_valid_iter` — set to current iter when validation passes, remain `null` if loop exhausts
- [x] On successful iteration: write final `instance-XX_plan.txt` with Project B's `--- Processing Metadata ---` block (include `first_valid_iter` in metadata), then break
- [x] On loop exhaustion (all 4 failed): write `instance-XX_plan.txt` using iter-4's plan text with `first_valid_iter = null` in metadata
- [x] Re-run `scripts/local/smoke_test.sh` — confirm stop-on-success path and 4-iter-fail path both write expected files

### 1.3 Unify the validator [P1, 3–4h]
- [x] In [`../dascenzogentili2425-master/src/utils/validator.py`](../dascenzogentili2425-master/src/utils/validator.py), add:
  ```python
  def validate_plan_verbose(domain_path, problem_path, plan_text) -> tuple[bool, str]:
      """Run VAL with -v, return (is_valid, raw_stdout)."""
  ```
- [x] `metrics_extractor` calls this helper
- [x] Delete any legacy validator call sites from Project A's code that got copied in

### 1.4 Parametric SLURM script [P1, 4–5.5h]
Base template: [`../dascenzogentili2425-master/scripts/gemma3_iters_4_tetris.sh`](../dascenzogentili2425-master/scripts/gemma3_iters_4_tetris.sh)

- [x] `scripts/slurm/run.sh` parameterized by `$MODEL`, `$DOMAIN`, `$CONDITION` env vars
- [x] Three SBATCH profiles (branch on `$MODEL`):
  - `small`: 1× A100-80GB, 3h walltime — for `llama8`
  - `mid`: 2× A100-80GB TP=2, 10h walltime — for `qwen25`
  - `large`: 2× A100-80GB TP=2 FP8 via vLLM, 14h walltime — for `llama33`
- [x] Inside the job: load generation config from `config.yml`; log it to the job stdout **at job start** for §2.4 verification
- [x] `scripts/slurm/submit_all.sh` iterates 3 models × 3 domains × 2 conditions and submits 18 `sbatch` jobs
- [x] Output paths: `src/results/{model}/{domain}/{condition}/`

### 1.5 Submit all 18 jobs [P1, 5.5–7h]
- [ ] `bash scripts/slurm/submit_all.sh`
- [ ] Record all 18 JobIDs in `scripts/slurm/SUBMITTED.md` with columns: `job_id, model, domain, condition, profile, submitted_at, status`

### 1.6 Prompt uniformity verification [P2, parallel 0–3h]
- [x] For each of 6 (domain, condition) combinations, dump the full prompt string for `instance-01` with each of the 3 models: `scripts/verify/dump_prompts.py --instance instance-01`
- [x] Diff pairwise across models → must be **byte-identical**. Save 6 reference prompts as `src/tests/fixtures/prompts/{domain}_{condition}.txt`
- [x] Diff `baseline` vs `cot` for same (domain, instance) → must differ **only** in the CoT scaffold block (regex assert)
- [x] Commit fixtures + diff script. This is the evidence for the methodology section's prompt-bias claim.

### 1.7 Methodology writeup — first draft [P2, 3–7h]
- [x] Report §Methodology draft: pipeline diagram, prompt harmonization design (shell + descriptions + compose), the two prompting conditions, generation-config uniformity, stop-on-success iteration policy, validator setup
- [x] Include the 6 reference prompts as appendix material

### 1.8 Notebook plot cells 1–4 [P3, 0–7h]
- [ ] Cell 1: Success-rate matrix (model × domain × condition)
- [ ] Cell 2: Iteration-gain curve (cumulative % solved at iter 1, 2, 3, 4)
- [ ] Cell 3: Avg iterations to convergence (solved only)
- [ ] Cell 4: Per-problem feature distributions
- [ ] All driven by dummy DataFrames with the 18-cell schema
- [ ] Outline report intro + background sections (LaTeX)

---

## Day 2 — Monitor + ingest llama8 & qwen25

### 2.1 Job monitoring [P1, ongoing]
- [ ] `squeue -u $USER` every ~2h
- [ ] llama8 cells (6) should finish by ~noon
- [ ] qwen25 cells (6) should finish by EOD
- [ ] For OOM / timeout: investigate, resubmit with adjusted params (bump walltime, reduce batch, or drop to smaller instance count)

### 2.2 Ingest as results land [P3, continuous]
- [ ] Load every `run_metrics.csv` under `src/results/{model}/{domain}/{condition}/` into a single pooled DataFrame keyed on `(model, domain, condition, instance, iteration)`
- [ ] Rerun notebook plots 1–4 on the 12 populated cells (llama8 + qwen25, both conditions)
- [ ] First draft of Results section — report what the 12-cell partial view shows

### 2.3 Post-hoc VAL replay on corner cases [P1, parallel]
- [ ] For any instance where `solves_problem=True` but `valid_action_percent<100` → possible extractor bug → re-run `metrics_extractor` manually on that plan
- [ ] For any (model, domain, condition) with 0% success at iter 1 but >0% at iter 4 → sanity check the iteration loop isn't dropping the first valid plan

### 2.4 Generation-config identity check [P2]
- [ ] Grep all 18 job stdouts for the "Generation config:" log line
- [ ] All 18 must be byte-identical. If any differ → halt, fix, rerun the affected cells before proceeding

### 2.5 Git checkpoint [ALL, EOD]
- [ ] Tag `v0.5-partial-data` before any further changes

---

## Day 3 — llama33 finishes, full analysis

### 3.1 llama33 wrap-up [P1, morning]
- [ ] llama33 FP8 cells (6) finish overnight Day 2 → Day 3 morning
- [ ] Handle any reruns (OOM likely candidate for the largest-instance Blocksworld problems)
- [ ] Confirm all 18 cells populated: `python scripts/verify/cell_count.py` → 18/18

### 3.2 Row-count sanity [P1]
- [ ] Per (model, domain, condition, instance): 1–4 rows in `run_metrics.csv`
- [ ] If last row's `solves_problem` is `True` → stopped early; if `False` → all 4 attempted
- [ ] Any instance with >4 rows or 0 rows → bug, investigate

### 3.3 All 10 plots finalized [P3]
**Primary (proposal §3.4)**:
- [ ] Plot 1: Success-rate matrix (18 cells) with 95% CIs
- [ ] Plot 2: Iteration-gain curve per (model, domain, condition)
- [ ] Plot 3: Avg iterations to convergence
- [ ] Plot 4: Per-problem feature distributions

**Secondary (extends prior work)**:
- [ ] Plot 5: **Baseline-vs-CoT delta** — success Δ = CoT − Baseline per (model, domain). **Headline finding**.
- [ ] Plot 6: Intra-family scale scatter — llama8 vs llama33 on matched (domain, condition) cells
- [ ] Plot 7: Cross-family — Meta (pooled 8B+70B) vs Alibaba (32B)
- [ ] Plot 8: First-valid-iteration distribution (stacked bar)
- [ ] Plot 9: Partial-credit boxplot on failed plans
- [ ] Plot 10: Domain-difficulty ranking

For plots that show a per-iteration metric: add caption note about the **stop-on-success selection bias** (later iterations contain only instances that failed earlier, so residuals are harder).

### 3.4 Results + Discussion writeup [P3, parallel]
- [ ] Report §Results: walk through the 18-cell matrix, the CoT delta, the intra-family scale effect, domain difficulty
- [ ] Report §Discussion: what does this tell us about LLM planning capability? Compare against prior-project findings
- [ ] Tables: 18-cell success matrix with CIs; CoT-effect per (model, domain); median iterations-to-first-valid (IQR); family-level summary

### 3.5 Methodology final pass [P2]
- [ ] Re-run prompt-identity verification over actual job logs (prompts reconstructed from logs vs. fixtures) → must match
- [ ] Add the "defending the uniformity claim" paragraph citing §8.2, §8.3, §8.4 of the plan
- [ ] Limitations section: stop-on-success selection bias, single temperature, 20 instances per domain (small-N), 3 models only

---

## Day 4 — Polish, ship

### 4.1 Repo cleanup [P1]
- [ ] `README.md`: quickstart (clone → Day 0 smoke test → submit_all → notebook)
- [ ] Document every env var and config knob
- [ ] Reproduction walkthrough: "from scratch to populated 10 plots in N commands"
- [ ] Remove `__pycache__`, stale logs, unused scripts
- [ ] Archive SLURM stdouts under `scripts/slurm/logs/`

### 4.2 Report PDF [P3]
- [ ] Final LaTeX pass (sections: Context / Methodology / Experimental Design / Results / Discussion / Limitations / Conclusions / References / Appendix with prompts)
- [ ] Every figure captioned, referenced from prose, numbered
- [ ] Every table has a caption and is referenced

### 4.3 Slide deck [P3, with P2 review]
- [ ] 10–12 slides:
  1. Title + team
  2. Motivation (merge A + B into a controlled study)
  3. Objectives (verbatim from proposal)
  4. Pipeline diagram
  5. Model slate (intra-family scale: llama 8B vs 70B)
  6. Domains (3 reasoning challenges)
  7. Prompt harmonization (shell + descriptions + compose)
  8. Baseline vs CoT — **headline delta plot**
  9. 18-cell success matrix
  10. Intra-family scale + cross-family
  11. Iteration-gain + domain-difficulty
  12. Limitations + next steps
- [ ] Dry-run presentation out loud with all 3 team members

### 4.4 Final verification [ALL]
- [ ] All 6 prompt fixtures match job-log reconstructions
- [ ] All 18 generation-config logs byte-identical
- [ ] Notebook runs top-to-bottom on final data, no errors
- [ ] Report PDF compiles cleanly
- [ ] `git tag v1.0-submission`

---

## Quick reference — where things live

| Thing | Path |
|---|---|
| Iteration policy | `config.yml` → `iteration.policy = stop_on_success` |
| Domain registry (active/available) | `config.yml` → `domains:` |
| Model list (active) | `config.yml` → `models.active` |
| Prompting conditions | `config.yml` → `conditions: [baseline, cot]` |
| Generation config | `config.yml` → `generation:` |
| Harmonized prompt shell | `src/prompts/shell.py` |
| Domain descriptions (verbatim) | `src/prompts/descriptions.py` |
| Prompt composer (baseline vs cot) | `src/prompts/compose.py` |
| Prompt router | `src/core/pddl_processor.py::_create_domain_prompt` |
| Iteration loop patch site | `src/core/model_manager.py` L247–249 (keep early-return, add per-iter writes) |
| Metrics extractor | `src/utils/metrics_extractor.py` |
| VAL-verbose helper | `src/utils/validator.py::validate_plan_verbose` |
| SLURM entrypoint | `scripts/slurm/run.sh` |
| Submit-all | `scripts/slurm/submit_all.sh` |
| Local smoke test | `scripts/local/smoke_test.sh` |
| Results | `src/results/{model}/{domain}/{condition}/` |
| Prompt identity fixtures | `src/tests/fixtures/prompts/{domain}_{condition}.txt` |
| Analysis notebook | `notebooks/results_analysis.ipynb` |
| Project A source (Merola, Blocksworld) | `../merolasinghdardouri2425-master/` |
| Project B source (D'Ascenzo, Tetris/CityCar) | `../dascenzogentili2425-master/` |

---

## Open items (confirm with supervisor before Day 1)

- [ ] **Compute access** — HPC confirmed, but confirm queue limits (can 18 jobs run simultaneously on Leonardo?)
- [ ] **Data reuse** (proposal §4.2) — current default is "no reuse"; if supervisor allows, the Day 1 Llama 3.3 70B × Blocksworld cell can be replaced by Project A's existing plans (saves ~5h wall-clock on the critical path)
- [ ] **Deliverable format** (proposal §4.3) — Day 4 produces report + slides + repo; drop any that aren't needed
