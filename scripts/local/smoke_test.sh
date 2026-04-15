#!/usr/bin/env bash
# Day 0 smoke test — exercises the stub pipeline across 3 domains x 2 conditions.
# Run from the llm-planning-bench/ directory:
#     bash scripts/local/smoke_test.sh
# Requires VAL installed at the path in config.local.yml (val_path: ./VAL/Validate).
set -euo pipefail

cd "$(dirname "$0")/../.."

export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

domains=(blocksworld citycar tetris)
conditions=(baseline cot)

failures=0
for domain in "${domains[@]}"; do
  for condition in "${conditions[@]}"; do
    echo
    echo "=============================================================="
    echo " smoke: domain=${domain}  condition=${condition}"
    echo "=============================================================="
    if ! python src/main.py \
        --model stub \
        --domain "${domain}" \
        --condition "${condition}" \
        --instance instance-01 \
        --iterations 4 \
        --cluster local; then
      echo "  -> FAILED (domain=${domain} condition=${condition})"
      failures=$((failures + 1))
    fi
  done
done

echo
echo "=============================================================="
echo " smoke test summary"
echo "=============================================================="
echo "  combinations run:    ${#domains[@]} x ${#conditions[@]} = $(( ${#domains[@]} * ${#conditions[@]} ))"
echo "  failing combinations: ${failures}"

if [ "${failures}" -gt 0 ]; then
  exit 1
fi

echo
echo "Verifying outputs under src/results/stub/..."
for domain in "${domains[@]}"; do
  for condition in "${conditions[@]}"; do
    plan="src/results/stub/${domain}/${condition}/instance-01_plan.txt"
    if [ ! -f "${plan}" ]; then
      echo "  MISSING: ${plan}"
      failures=$((failures + 1))
    else
      echo "  ok: ${plan}"
    fi
  done
done

if [ "${failures}" -gt 0 ]; then
  exit 1
fi

echo
echo "Day 0 smoke test PASSED."
