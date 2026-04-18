#!/usr/bin/env bash
# =====================================================================
# First-time Leonardo shakedown — ONE cell, ONE instance, small profile.
#
# Purpose: catch infra issues (account/partition, module load, venv,
# HF cache / network, vLLM+CUDA compat, gated-model auth) before
# submit_all.sh fires the full 18 jobs.
#
# What it runs:
#   model     = llama8       (smallest, 1× A100-80GB)
#   domain    = blocksworld  (smallest prompts)
#   condition = baseline     (no CoT scaffold — shortest completions)
#   instance  = instance-01  (single problem, not all 20)
#   walltime  = 01:00:00     (model load + 4 iters of one instance)
#
# Success criteria (verify before running submit_all.sh):
#   - job exits 0
#   - "Generation config:" line present in the stdout
#   - src/results/llama8/blocksworld/baseline/instance-01_plan.txt exists
#   - src/results/llama8/blocksworld/baseline/run_metrics.csv has 1–4 rows
#
# Usage:
#   bash scripts/slurm/shakedown.sh
#
# Gated-model note:
#   Llama 3.1 8B is HF-gated. If the job fails to fetch weights, export
#   HF_TOKEN in your login shell before sbatch (the --export=ALL flag
#   propagates it into the job environment):
#     export HF_TOKEN=hf_xxxxxxxxxxxx
# =====================================================================
set -euo pipefail

cd "$(dirname "$0")/../.."

MODEL="llama8"
DOMAIN="blocksworld"
CONDITION="baseline"
INSTANCE="instance-01"

JOB_NAME="shakedown_${MODEL}_${DOMAIN}_${CONDITION}"
LOG_DIR="scripts/slurm/logs"
mkdir -p "${LOG_DIR}"

RUN_SCRIPT="scripts/slurm/run.sh"
if [ ! -f "${RUN_SCRIPT}" ]; then
  echo "ERROR: ${RUN_SCRIPT} not found" >&2
  exit 1
fi

echo "Submitting shakedown: ${JOB_NAME}"
echo "  MODEL=${MODEL} DOMAIN=${DOMAIN} CONDITION=${CONDITION} INSTANCE=${INSTANCE}"

OUT="$(sbatch \
    --job-name="${JOB_NAME}" \
    --output="${LOG_DIR}/${JOB_NAME}_%j.out" \
    --error="${LOG_DIR}/${JOB_NAME}_%j.err" \
    --time=01:00:00 \
    --gres=gpu:1 \
    --export="ALL,MODEL=${MODEL},DOMAIN=${DOMAIN},CONDITION=${CONDITION},INSTANCE=${INSTANCE}" \
    "${RUN_SCRIPT}" 2>&1)"

echo "${OUT}"

JOB_ID="$(echo "${OUT}" | awk '/Submitted batch job/ {print $NF}')"
if [ -z "${JOB_ID}" ]; then
  echo "ERROR: sbatch did not return a job id" >&2
  exit 2
fi

cat <<EOF

Shakedown submitted — job id: ${JOB_ID}
Watch it:
  squeue -j ${JOB_ID}
  tail -f ${LOG_DIR}/${JOB_NAME}_${JOB_ID}.out

After it completes, verify:
  grep "Generation config:" ${LOG_DIR}/${JOB_NAME}_${JOB_ID}.out
  ls src/results/${MODEL}/${DOMAIN}/${CONDITION}/
  wc -l src/results/${MODEL}/${DOMAIN}/${CONDITION}/run_metrics.csv

If all four checks above pass, proceed to:
  bash scripts/slurm/submit_all.sh
EOF
