# SLURM job tracker

Records every `sbatch` submission for the 18-cell experiment (3 models × 3 domains × 2 conditions).

## Third-model decision

- **Pick**: `Qwen/Qwen2.5-32B-Instruct` — confirmed available on Leonardo / HF mirror.
- **Fallback (not activated)**: `mistralai/Mistral-Small-24B-Instruct-2501`.
- **Decided**: 2026-04-15.

## Model aliases (config.yml `models.active`)

| Alias    | HF repo                                  | Profile | GPUs            |
|----------|------------------------------------------|---------|-----------------|
| llama8   | meta-llama/Llama-3.1-8B-Instruct         | small   | 1× A100-80GB    |
| qwen25   | Qwen/Qwen2.5-32B-Instruct                | mid     | 2× A100-80GB TP=2 |
| llama33  | meta-llama/Llama-3.3-70B-Instruct        | large   | 2× A100-80GB TP=2 FP8 |

## Submission log

| job_id | model | domain | condition | profile | submitted_at | status |
|--------|-------|--------|-----------|---------|--------------|--------|
|        |       |        |           |         |              |        |

Populated by `scripts/slurm/submit_all.sh` on Day 1.
