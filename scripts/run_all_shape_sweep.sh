#!/usr/bin/env bash
# Drive the full input-shape sweep: 3 configs x 3 seq lens x 2 runs each.

set -euo pipefail

LOG=/home/rassulmagauin/project/shape_sweep_results/run.log
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1

echo "============================================================"
echo "Shape sweep starting at $(date -Iseconds)"
echo "============================================================"

START_HEAD=$(git -C /home/rassulmagauin/tt-metal rev-parse HEAD)
trap 'echo "[trap] restoring tt-metal HEAD to $START_HEAD"; git -C /home/rassulmagauin/tt-metal checkout "$START_HEAD" || true' EXIT

run_config() {
  local name="$1" sha="$2"
  echo
  echo "------------------------------------------------------------"
  echo "[$(date +%H:%M:%S)] config=$name -> tt-metal $sha"
  echo "------------------------------------------------------------"
  git -C /home/rassulmagauin/tt-metal checkout "$sha"
  /home/rassulmagauin/project/scripts/run_shape_sweep.sh "$name" 2
}

run_config baseline a4d8480d3e
run_config hifi2    f6de95bb02
run_config fusion   e05a044c4f

echo
echo "------------------------------------------------------------"
echo "[$(date +%H:%M:%S)] aggregating"
echo "------------------------------------------------------------"
python3 /home/rassulmagauin/project/scripts/aggregate_shape_sweep.py

echo
echo "============================================================"
echo "Shape sweep complete at $(date -Iseconds)"
echo "============================================================"
