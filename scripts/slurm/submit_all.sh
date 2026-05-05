#!/usr/bin/env bash
# =====================================================================
# STEPS.md §1.5 — submit all 18 cells (3 models × 3 domains × 2 conditions).
# Each sbatch call:
#   - exports MODEL / DOMAIN / CONDITION into the job environment
#   - overrides --time / --gres according to the profile tied to $MODEL
#   - names the job <model>_<domain>_<condition> so logs are greppable
#   - appends a row to scripts/slurm/SUBMITTED.md
#
# Run from the project root:
#   bash scripts/slurm/submit_all.sh
#
# Dry run (print what *would* be submitted, touching nothing):
#   DRY_RUN=1 bash scripts/slurm/submit_all.sh
# =====================================================================
set -euo pipefail

cd "$(dirname "$0")/../.."

# Override model list for staged submission, e.g. for three-wave rollouts:
#   MODELS_OVERRIDE="llama8 qwen25"     bash scripts/slurm/submit_all.sh   # wave 1
#   MODELS_OVERRIDE="llama33"           bash scripts/slurm/submit_all.sh   # wave 2
#   MODELS_OVERRIDE="qwq32 mistral24"   bash scripts/slurm/submit_all.sh   # wave 3 (post wave 2)
# Wave 3 is the exploratory comparison set — see glowing-baking-turing.md §2b/§12.
if [ -n "${MODELS_OVERRIDE:-}" ]; then
  # shellcheck disable=SC2206
  MODELS=( ${MODELS_OVERRIDE} )
else
  MODELS=(llama8 qwen25 llama33)
fi
DOMAINS=(blocksworld citycar tetris)
CONDITIONS=(baseline cot)

RUN_SCRIPT="scripts/slurm/run.sh"
TRACKER="scripts/slurm/SUBMITTED.md"
LOG_DIR="scripts/slurm/logs"
mkdir -p "${LOG_DIR}"

if [ ! -f "${RUN_SCRIPT}" ]; then
  echo "ERROR: ${RUN_SCRIPT} not found" >&2
  exit 1
fi

DRY_RUN="${DRY_RUN:-0}"

# -------------------------------------------------
# Profile table — keeps walltime / GPU count coupled to the model.
# Must match the profile branch in run.sh.
# -------------------------------------------------
profile_for() {
  case "$1" in
    llama8)    echo "small"  ;;
    qwen25)    echo "mid"    ;;
    llama33)   echo "large"  ;;
    qwq32)     echo "mid"    ;;  # wave 3: same base as qwen25
    mistral24) echo "mid"    ;;  # wave 3: 24B dense, fits the qwen25 envelope
    *) echo "unknown"; return 1 ;;
  esac
}

sbatch_flags_for() {
  # Echoes the sbatch overrides for a given profile.
  case "$1" in
    small) echo "--time=03:00:00 --gres=gpu:1" ;;
    mid)   echo "--time=10:00:00 --gres=gpu:2" ;;
    large) echo "--time=14:00:00 --gres=gpu:2" ;;
    *) echo "ERROR: unknown profile $1" >&2; return 1 ;;
  esac
}

# -------------------------------------------------
# Prepare the tracker. Keep any prior header intact;
# append a fresh dated run block underneath.
# -------------------------------------------------
if [ "${DRY_RUN}" != "1" ]; then
  RUN_STAMP="$(date -u +%FT%TZ)"
  {
    echo ""
    echo "### Submission run — ${RUN_STAMP}"
    echo ""
    echo "| job_id | model | domain | condition | profile | submitted_at | status |"
    echo "|--------|-------|--------|-----------|---------|--------------|--------|"
  } >> "${TRACKER}"
fi

submitted=0
failed=0
for MODEL in "${MODELS[@]}"; do
  PROFILE="$(profile_for "${MODEL}")"
  FLAGS="$(sbatch_flags_for "${PROFILE}")"
  for DOMAIN in "${DOMAINS[@]}"; do
    for CONDITION in "${CONDITIONS[@]}"; do
      JOB_NAME="${MODEL}_${DOMAIN}_${CONDITION}"
      TS="$(date -u +%FT%TZ)"

      # 70B in bf16 needs ~140 GB; 2× A100-64GB only gives 128 GB.
      # Force 4-bit (NF4) loading via the env hook in model_manager.py
      # — fits 70B in ~35 GB on a single GPU, plenty of room for 2× A100.
      EXPORT_VARS="ALL,MODEL=${MODEL},DOMAIN=${DOMAIN},CONDITION=${CONDITION}"
      if [ "${MODEL}" = "llama33" ]; then
        EXPORT_VARS="${EXPORT_VARS},LLM_LOAD_IN_4BIT=1"
      fi

      # shellcheck disable=SC2086
      CMD=(sbatch
          --job-name="${JOB_NAME}"
          --output="${LOG_DIR}/${JOB_NAME}_%j.out"
          --error="${LOG_DIR}/${JOB_NAME}_%j.err"
          ${FLAGS}
          --export="${EXPORT_VARS}"
          "${RUN_SCRIPT}")

      if [ "${DRY_RUN}" = "1" ]; then
        echo "DRY_RUN: ${CMD[*]}"
        continue
      fi

      echo "Submitting ${JOB_NAME} (profile=${PROFILE})..."
      if ! OUT="$("${CMD[@]}" 2>&1)"; then
        echo "  FAILED: ${OUT}" >&2
        echo "|  FAIL  | ${MODEL} | ${DOMAIN} | ${CONDITION} | ${PROFILE} | ${TS} | submit_error |" >> "${TRACKER}"
        failed=$((failed + 1))
        continue
      fi

      # sbatch prints "Submitted batch job <id>"
      JOB_ID="$(echo "${OUT}" | awk '/Submitted batch job/ {print $NF}')"
      if [ -z "${JOB_ID}" ]; then
        JOB_ID="unknown"
      fi
      echo "  -> job_id=${JOB_ID}"
      echo "| ${JOB_ID} | ${MODEL} | ${DOMAIN} | ${CONDITION} | ${PROFILE} | ${TS} | submitted |" >> "${TRACKER}"
      submitted=$((submitted + 1))
    done
  done
done

echo ""
echo "=========================================="
echo " submit_all summary"
echo "=========================================="
EXPECTED=$(( ${#MODELS[@]} * ${#DOMAINS[@]} * ${#CONDITIONS[@]} ))
if [ "${DRY_RUN}" = "1" ]; then
  echo "  DRY_RUN (no sbatch calls made, would submit ${EXPECTED})"
else
  echo "  submitted: ${submitted} / ${EXPECTED}"
  echo "  failed:    ${failed}"
  echo "  tracker:   ${TRACKER}"
fi

if [ "${failed}" -gt 0 ]; then
  exit 1
fi
