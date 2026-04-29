#!/usr/bin/env bash
# Drive the full Priority-1 variance study end to end.
# Runs 5 iterations of each of {baseline, hifi2, fusion}, then aggregates.

set -euo pipefail

LOG=/home/rassulmagauin/project/variance_results/run.log
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1

echo "============================================================"
echo "Variance study starting at $(date -Iseconds)"
echo "============================================================"

START_HEAD=$(git -C /home/rassulmagauin/tt-metal rev-parse HEAD)
echo "Will restore tt-metal HEAD to $START_HEAD when done."

run_config() {
  local name="$1" sha="$2"
  echo
  echo "------------------------------------------------------------"
  echo "[$(date +%H:%M:%S)] config=$name -> tt-metal $sha"
  echo "------------------------------------------------------------"
  git -C /home/rassulmagauin/tt-metal checkout "$sha"
  /home/rassulmagauin/project/scripts/run_variance.sh "$name" 5
}

trap 'echo "[trap] restoring tt-metal HEAD to $START_HEAD"; git -C /home/rassulmagauin/tt-metal checkout "$START_HEAD" || true' EXIT

run_config baseline a4d8480d3e
run_config hifi2    965e0f4622
run_config fusion   e05a044c4f

echo
echo "------------------------------------------------------------"
echo "[$(date +%H:%M:%S)] aggregating"
echo "------------------------------------------------------------"
python3 /home/rassulmagauin/project/scripts/aggregate_variance.py

echo
echo "============================================================"
echo "Variance study complete at $(date -Iseconds)"
echo "Summary at /home/rassulmagauin/project/variance_results/summary.txt"
echo "============================================================"
