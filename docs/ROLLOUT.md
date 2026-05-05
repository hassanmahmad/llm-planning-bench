# Rollout guide — from laptop to Leonardo

Operational companion to [STEPS.md](../STEPS.md). Covers how to stage the
18-cell experiment (STEPS.md §1.5) in four shrinking-risk steps so that
every bug is caught on the cheapest possible hardware.

| Stage | What it is | Where it runs | Catches |
|-------|------------|---------------|---------|
| 1. Stub smoke     | STEPS.md §0.7, `--model stub`                                  | laptop, CPU           | pipeline plumbing (prompt → VAL → CSV writers, iteration loop) |
| 2. Local real LLM | a small HF model loaded via `transformers`, optional 4-bit     | laptop, RTX 2060 6 GB | real generation behaviour (postprocessor, VAL on real plans, early-stop logic) |
| 3. HPC shakedown  | one SLURM cell, one instance                                   | Leonardo, small profile | Leonardo infra (modules, venv, HF cache, gated weights) |
| 4. Full 18-cell   | `submit_all.sh`                                                | Leonardo, all 3 profiles | the actual experiment |

Do not skip a stage just because the previous one passed. The failure
modes each stage catches are almost disjoint.

---

## Stage 1 — Stub smoke test (laptop, CPU)

Already wired end-to-end. Exercises every pipeline component except the
LLM itself.

```bash
cd llm-planning-bench/
python -m venv .venv && source .venv/Scripts/activate   # Windows-bash
pip install -r requirements.txt
bash scripts/local/smoke_test.sh
```

Success criteria (script checks these automatically):

- All 6 `(domain × condition)` combinations exit 0.
- `src/results/stub/<domain>/<condition>/instance-01_plan.txt` exists for each.

### Debugging

| Symptom | Fix |
|---------|-----|
| `VAL/Validate --help` fails | On Windows use `VAL/Validate.exe` (matches `VAL_EXECUTABLE` in `config.yml`); on Linux drop a Linux build into `VAL/` and set `VAL_EXECUTABLE: Validate`. |
| `ModuleNotFoundError: prompts` | Run from project root, or `export PYTHONPATH=$(pwd)/src` before `python src/main.py`. |
| Empty `run_metrics.csv` | The stub didn't fire a generation — check `src/data/<domain>/stub_plans/instance-01.txt` exists. |

---

## Stage 2 — Local small model on RTX 2060 (6 GB)

### 2.1 Pick a model

RTX 2060 is Turing (compute 7.5), so **no bf16** — the model manager
auto-selects fp16 on this GPU. Realistic options:

| Model | fp16 VRAM | 4-bit VRAM | Notes |
|-------|-----------|------------|-------|
| `Qwen/Qwen2.5-1.5B-Instruct` | ~3.2 GB | ~1.2 GB | comfortable; easiest |
| `Qwen/Qwen2.5-3B-Instruct`   | ~6.5 GB (tight/OOM) | ~2.4 GB | prefer 4-bit |
| `Qwen/Qwen2.5-7B-Instruct`   | ~15 GB (no) | ~4.8 GB  | only with 4-bit, tight |

Recommended: **Qwen 2.5-3B-Instruct + 4-bit** — biggest model that
leaves real headroom for activations and KV cache, and similar
generation feel to the Leonardo slate.

### 2.2 Install the extra dep

4-bit loading needs `bitsandbytes`. On Windows CUDA you need the
Windows fork:

```bash
pip install bitsandbytes           # Linux
pip install bitsandbytes-windows   # Windows (not officially released — pin the latest 0.41.x wheel)
```

On Linux with CUDA 12.x you also need `accelerate` (already in
`requirements.txt`).

Skip this if you go with Qwen 2.5-1.5B at fp16 — no quantization
needed.

### 2.3 Download the weights

The `transformers` loader expects a local directory. One-time download:

```bash
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='Qwen/Qwen2.5-3B-Instruct',
    local_dir='src/models/qwen25-3b-local',
    local_dir_use_symlinks=False,
)"
```

Add `token='hf_xxx'` inside the call if the model is gated (Qwen 2.5
isn't; Llama 3.x is).

### 2.4 Register the alias (optional)

`config.yml` currently has `models.active: [llama8, qwen25, llama33]`.
The CLI choices come from that list plus `stub` and `auto`. Easiest is
to use `--model auto`, which derives the alias from the weights dir
basename (`qwen25-3b-local` → `qwen25-3b-local`). If you prefer a clean
`qwen25-3b` alias, add it to `models.active` temporarily.

### 2.5 Run

```bash
# 4-bit (recommended for Qwen 2.5-3B on 6 GB VRAM)
LLM_LOAD_IN_4BIT=1 python src/main.py \
  --model auto \
  --weights_path src/models/qwen25-3b-local \
  --domain blocksworld --condition baseline \
  --instance instance-01 --iterations 4 --cluster local

# fp16 (Qwen 2.5-1.5B — no env var needed)
python src/main.py \
  --model auto \
  --weights_path src/models/qwen25-1.5b-local \
  --domain blocksworld --condition baseline \
  --instance instance-01 --iterations 4 --cluster local
```

Expected: ~30-90 s of model load, then one problem generated + validated
up to 4 times. Outputs land at
`src/results/<alias>/blocksworld/baseline/instance-01_*`.

Run all 6 (domain × condition) combinations to match the stub
smoke test's coverage:

```bash
for domain in blocksworld citycar tetris; do
  for cond in baseline cot; do
    LLM_LOAD_IN_4BIT=1 python src/main.py \
      --model auto \
      --weights_path src/models/qwen25-3b-local \
      --domain $domain --condition $cond \
      --instance instance-01 --iterations 4 --cluster local
  done
done
```

### 2.6 Debugging

| Symptom | Likely cause / fix |
|---------|--------------------|
| `RuntimeError: cutlassF: no kernel found ...` or bf16-related error | `_pick_dtype()` should auto-fall-back; confirm GPU detected (`python -c "import torch; print(torch.cuda.get_device_name())"`). Manual override: edit `_pick_dtype` to return `torch.float16`. |
| `torch.cuda.OutOfMemoryError` | Drop to 4-bit (`LLM_LOAD_IN_4BIT=1`); if already 4-bit, drop to Qwen 2.5-1.5B; reduce `--max_tokens`. |
| `ImportError: bitsandbytes` | See 2.2 — install or pick an fp16-sized model. |
| Plan is garbled / VAL rejects nonsense | Small models don't always produce valid PDDL. Confirm structure (one action per line, valid predicates) — the prompt works; small models are legitimately weaker. You're validating the pipeline, not the model. |
| `valid_action_percent` always 0 | Check `src/utils/answer_postprocessor.py` is stripping `<think>` blocks; verify VAL path matches OS (`.exe` on Windows). |
| `OSError: Can't load tokenizer` | Re-download the snapshot; ensure the `local_dir` actually contains `tokenizer.json` + `config.json`. |

When all 6 combinations produce a plan file (valid or not) and
`run_metrics.csv` has between 1 and 4 rows per combination, Stage 2 is
green.

---

## Stage 3 — Leonardo shakedown (single cell, single instance)

The goal is to surface Leonardo-specific failures *before* burning
queue time on 18 jobs.

### 3.1 One-time Leonardo setup

Assumes SSH access already provisioned (STEPS.md open items §1).

```bash
# login
ssh user@login.leonardo.cineca.it
cd $SCRATCH
git clone <this repo> llm-planning-bench
cd llm-planning-bench

# Python env
module load python/3.11.7
python -m venv project_venv
source project_venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Linux VAL binary (Windows .exe won't run here)
#   Drop the Linux build into VAL/ and flip config.yml:
#     VAL_EXECUTABLE: Validate
# Quick sanity:
./VAL/Validate --help

# HF auth for gated weights (Llama 3.x)
export HF_TOKEN=hf_xxxxxxxx
# persist it:
echo "export HF_TOKEN=hf_xxxxxxxx" >> ~/.bashrc

# HF cache on a big filesystem, not home (home quotas are tight)
echo "export HF_HOME=$SCRATCH/hf_cache" >> ~/.bashrc
source ~/.bashrc
```

### 3.2 Sync local fixtures up

The shakedown cell reads the same `src/data/blocksworld/instance-01.pddl`
you already copied locally in STEPS.md §0.3. Make sure the `src/data/`
tree is on Leonardo too (rsync, git, or scp).

### 3.3 Submit the shakedown

```bash
bash scripts/slurm/shakedown.sh
```

The wrapper submits one SBATCH: `llama8 × blocksworld × baseline ×
instance-01`, small profile (1 × A100-80 GB), 1 h walltime. It prints
the job id plus the four verification commands.

### 3.4 Watch it

```bash
squeue -u $USER                                    # queued / running / finished
scontrol show job <JOBID> | grep -E "JobState|Reason|NodeList"   # why is it pending
tail -f scripts/slurm/logs/shakedown_llama8_blocksworld_baseline_<JOBID>.out
```

Typical timeline: ~1-2 min pending → ~3-5 min module/venv/weights →
~2-10 min generation of 4 iterations → finish.

### 3.5 Post-job checks

```bash
# Exit code
sacct -j <JOBID> --format=JobID,State,ExitCode,Elapsed

# Generation-config line is present (required for §2.4)
grep "Generation config:" scripts/slurm/logs/shakedown_*.out

# Plan written
ls src/results/llama8/blocksworld/baseline/
# should contain: instance-01_iter_1.txt [... iter_N ...] instance-01_plan.txt run_metrics.csv

# Row count sane (1–4)
wc -l src/results/llama8/blocksworld/baseline/run_metrics.csv
```

All four pass → Stage 3 green.

### 3.6 Debugging

| Symptom | Likely cause / fix |
|---------|--------------------|
| Pending forever, `Reason=Priority` | Normal queue wait; check `sinfo -p boost_usr_prod`. |
| Pending with `Reason=AssocMaxJobsLimit` | Cancel stray jobs: `scancel -u $USER --state=PD`. |
| `sbatch: error: invalid account` | Confirm `--account` in `run.sh` matches your project allocation; `sacctmgr show assoc where user=$USER`. |
| `module: command not found` | Add `source /etc/profile.d/modules.sh` before `module load`. |
| `ERROR: Virtual environment not found!` | `run.sh` checks `project_venv` → `venv` → `.venv`; name your venv accordingly or create a symlink. |
| `ERROR: Not in LLM-Needs-a-Plan project directory!` | `sbatch` inherits the submitting cwd; submit from the project root (not from `scripts/slurm/`). |
| `transformers` / torch CUDA ABI mismatch on first import | The pinned `torch==2.7.0` + `transformers==4.51.3` in `requirements.txt` are tested together; if `pip` resolved a different torch on Leonardo, reinstall: `pip install --force-reinstall torch==2.7.0 transformers==4.51.3`. |
| `OSError: You are trying to access a gated repo` | `HF_TOKEN` not exported on the *compute* node. `--export=ALL` in `run.sh` carries it, but only if it's set in your login shell at sbatch time. |
| Weights download hangs | Compute node firewalled — prefetch on login node: `huggingface-cli download meta-llama/Llama-3.1-8B-Instruct`. |
| Out-of-memory on 1 × A100-80 GB | llama8 at FP16 uses ~16 GB; if OOM, suspect leaked context or too-high `max_new_tokens` — check config.yml. |
| `run_metrics.csv` has 0 rows | Generation succeeded but extractor/writer crashed — look for a Python traceback in the `.err` file. |
| `first_valid_iter` always null | Either the model genuinely failed 4 times (plausible for llama8 on blocksworld) or the validator rejected the plan format — inspect `instance-01_iter_1.txt` manually and run `Validate -v` on it by hand. |

---

## Stage 4 — Full 18-cell submission (STEPS.md §1.5)

Once Stage 3 is green, you're cleared.

```bash
# Dry-run first — prints the 18 sbatch commands without submitting
DRY_RUN=1 bash scripts/slurm/submit_all.sh

# For real
bash scripts/slurm/submit_all.sh
```

`submit_all.sh` appends job ids into
[`scripts/slurm/SUBMITTED.md`](../scripts/slurm/SUBMITTED.md) with
submission timestamps.

### 4.1 Monitor (STEPS.md §2.1)

```bash
squeue -u $USER                  # ~every 2 h
sacct --format=JobID,JobName,State,Elapsed,ExitCode -S $(date +%Y-%m-%d)
```

Expected timing per STEPS.md §2:

| Model    | Cells | Profile | Wall-clock | Finish ETA |
|----------|-------|---------|------------|------------|
| llama8   | 6     | small   | ~3 h each  | Day 2 noon |
| qwen25   | 6     | mid     | ~10 h each | Day 2 EOD  |
| llama33  | 6     | large   | ~14 h each | Day 3 AM   |

### 4.2 If a cell fails

| Failure | Action |
|---------|--------|
| OOM (especially llama33 + Blocksworld largest instance) | Resubmit just that cell with a bump: `MODEL=llama33 DOMAIN=blocksworld CONDITION=cot sbatch --time=18:00:00 --gres=gpu:4 scripts/slurm/run.sh` |
| Timeout | Same — bump `--time`. |
| Anything else | Check `scripts/slurm/logs/<jobname>_<jobid>.err`; fix root cause; resubmit. |

### 4.3 Generation-config identity (STEPS.md §2.4)

After all 18 finish:

```bash
grep -h "Generation config:" scripts/slurm/logs/*_*.out | sort -u | wc -l
# must print "1"
```

If it prints anything other than 1, some cell ran under a different
config — halt analysis, find the drift, rerun the affected cells.

---

## Appendix — failure-mode cheat sheet

| Where | Smell | Fix |
|-------|-------|-----|
| Any | `ModuleNotFoundError: prompts` | Forgot `PYTHONPATH=$(pwd)/src`. |
| Local | bf16 errors on RTX 20xx | `_pick_dtype()` should handle it; if you edit the file, keep the Turing path on fp16. |
| Local | bitsandbytes on Windows | Install `bitsandbytes-windows`; fall back to fp16 on a 1.5B model if it won't install. |
| Leonardo | First job queues forever | Confirm account/partition; `sinfo -p boost_usr_prod`. |
| Leonardo | Gated-model 401/403 | `HF_TOKEN` must be in the **submitting shell** — `--export=ALL` copies envvars at submit time. |
| Leonardo | Plans invalid but pipeline fine | Expected for llama8; real experiment signal. Don't "fix" the prompt. |
| Analysis | Missing cell in the 18 | `python scripts/verify/cell_count.py` (STEPS.md §3.1) — any zero → resubmit. |
