#!/bin/bash
# =====================================================================
# Parametric SLURM entrypoint for the 18-cell experiment.
# STEPS.md §1.4 — one script, three SBATCH profiles, branched on $MODEL.
#
# Inputs (environment variables, set by submit_all.sh):
#   MODEL       one of: llama8 | qwen25 | llama33
#   DOMAIN      one of: blocksworld | citycar | tetris
#   CONDITION   one of: baseline | cot
#
# Submit manually with, e.g.:
#   MODEL=llama8 DOMAIN=tetris CONDITION=cot sbatch scripts/slurm/run.sh
#
# Profiles (branched inside the job header by reading $MODEL at submit
# time via the wrapper in submit_all.sh — this script only carries the
# maximum envelope; submit_all.sh overrides --time / --gres per profile).
# =====================================================================

#SBATCH --account=IscrC_VisLLMs
#SBATCH --partition=boost_usr_prod
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:2
#SBATCH --time=14:00:00
#SBATCH --output=scripts/slurm/logs/%x_%j.out
#SBATCH --error=scripts/slurm/logs/%x_%j.err

set -euo pipefail

: "${MODEL:?MODEL env var is required (llama8|qwen25|llama33)}"
: "${DOMAIN:?DOMAIN env var is required (blocksworld|citycar|tetris)}"
: "${CONDITION:?CONDITION env var is required (baseline|cot)}"

mkdir -p scripts/slurm/logs

echo "=========================================="
echo " LLM Planning Bench — 18-cell experiment"
echo "=========================================="
echo "Job ID:        ${SLURM_JOB_ID:-<interactive>}"
echo "Job Name:      ${SLURM_JOB_NAME:-run.sh}"
echo "Node:          ${SLURM_NODELIST:-local}"
echo "CPUs:          ${SLURM_CPUS_PER_TASK:-?}"
echo "Memory:        ${SLURM_MEM_PER_NODE:-?} MB"
echo "GPUs:          ${SLURM_GPUS:-?}"
echo "Start Time:    $(date -u +%FT%TZ)"
echo "MODEL:         ${MODEL}"
echo "DOMAIN:        ${DOMAIN}"
echo "CONDITION:     ${CONDITION}"
echo "=========================================="

# -------------------------------------------------
# Profile branch — derived from $MODEL.
# submit_all.sh already picked --time/--gres for us;
# these values drive the in-job vLLM launch config.
# -------------------------------------------------
case "${MODEL}" in
  llama8)
    PROFILE="small"
    HF_REPO="meta-llama/Llama-3.1-8B-Instruct"
    TP_SIZE=1
    DTYPE="bfloat16"
    QUANTIZATION=""
    ;;
  qwen25)
    PROFILE="mid"
    HF_REPO="Qwen/Qwen2.5-32B-Instruct"
    TP_SIZE=2
    DTYPE="bfloat16"
    QUANTIZATION=""
    ;;
  llama33)
    PROFILE="large"
    HF_REPO="meta-llama/Llama-3.3-70B-Instruct"
    TP_SIZE=2
    DTYPE="auto"
    QUANTIZATION="fp8"
    ;;
  *)
    echo "ERROR: unknown MODEL='${MODEL}' (expected llama8|qwen25|llama33)" >&2
    exit 2
    ;;
esac

echo "Profile:       ${PROFILE}"
echo "HF repo:       ${HF_REPO}"
echo "TP size:       ${TP_SIZE}"
echo "dtype:         ${DTYPE}"
echo "quantization:  ${QUANTIZATION:-<none>}"
echo "=========================================="

# -------------------------------------------------
# Environment
# -------------------------------------------------
module load python/3.11.7 2>/dev/null || true

if [ ! -f "config.yml" ] || [ ! -d "src" ]; then
  echo "ERROR: run from the llm-planning-bench project root" >&2
  pwd
  exit 1
fi

if   [ -d "project_venv" ]; then VENV_DIR="project_venv"
elif [ -d "venv" ];         then VENV_DIR="venv"
elif [ -d ".venv" ];        then VENV_DIR=".venv"
else
  echo "ERROR: no virtualenv found (project_venv / venv / .venv)" >&2
  exit 1
fi
echo "Activating ${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"
export LLM_PROJECT_ROOT="$(pwd)"
export HF_MODEL_REPO="${HF_REPO}"
export VLLM_TP_SIZE="${TP_SIZE}"
export VLLM_DTYPE="${DTYPE}"
export VLLM_QUANTIZATION="${QUANTIZATION}"

echo "Python:        $(python --version 2>&1)"
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
fi

# -------------------------------------------------
# Generation config identity log (STEPS.md §2.4).
# Dumps config.yml[generation] + config.yml[iteration] as a single
# canonical JSON line so `grep "Generation config:"` across all 18
# job stdouts can be diffed byte-for-byte.
# -------------------------------------------------
echo "=========================================="
echo " Generation config (STEPS.md §2.4 check)"
echo "=========================================="
python - <<'PY'
import json, sys, yaml
with open("config.yml", "r", encoding="utf-8") as fh:
    cfg = yaml.safe_load(fh)
payload = {
    "generation": cfg.get("generation") or {},
    "iteration":  cfg.get("iteration")  or {},
    "conditions": cfg.get("conditions") or [],
}
print("Generation config: " + json.dumps(payload, sort_keys=True, separators=(",", ":")))
PY
echo "=========================================="

# -------------------------------------------------
# Run the experiment for this (model, domain, condition) cell.
# One job == one cell (20 instances × up to 4 iterations).
# -------------------------------------------------
PROBLEMS_PATH="src/data/${DOMAIN}"
OUTPUT_DIR="src/results"

MAIN_ARGS=(
  --problems_path "${PROBLEMS_PATH}"
  --weights_path  "src/models"
  --output_dir    "${OUTPUT_DIR}"
  --model         "${MODEL}"
  --domain        "${DOMAIN}"
  --condition     "${CONDITION}"
  --cluster       leonardo
  --log-level     INFO
  --verbose
)

echo "Command: python src/main.py ${MAIN_ARGS[*]}"
echo "=========================================="

EXPERIMENT_START=$(date +%s)
set +e
python src/main.py "${MAIN_ARGS[@]}"
EXIT_CODE=$?
set -e
EXPERIMENT_END=$(date +%s)
DURATION=$((EXPERIMENT_END - EXPERIMENT_START))

echo "=========================================="
echo " Results"
echo "=========================================="
echo "Exit code: ${EXIT_CODE}"
echo "Duration:  ${DURATION}s ($((DURATION / 60))m $((DURATION % 60))s)"
echo "End time:  $(date -u +%FT%TZ)"

RESULT_DIR="${OUTPUT_DIR}/${MODEL}/${DOMAIN}/${CONDITION}"
if [ -d "${RESULT_DIR}" ]; then
  echo "Result dir: ${RESULT_DIR}"
  ls -la "${RESULT_DIR}" | head -30
fi

exit ${EXIT_CODE}
