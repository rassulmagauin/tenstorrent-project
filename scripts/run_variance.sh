#!/usr/bin/env bash
# Run N profile iterations of the current tt-metal state and stash the CSVs
# under variance_results/<config_name>/run_<i>/.
#
# Usage:
#   ./run_variance.sh <config_name> [N=5]
#
# Example:
#   cd ~/tt-metal && git checkout a4d8480d3e   # baseline
#   ./run_variance.sh baseline 5
#   cd ~/tt-metal && git checkout 965e0f4622   # +HiFi2
#   ./run_variance.sh hifi2 5
#   cd ~/tt-metal && git checkout e05a044c4f   # +HiFi2 +fusion
#   ./run_variance.sh fusion 5
#
# Notes:
# - First profile run is a warm-up (kept but flagged), so do at least N=4 if
#   you want 3 timed runs.
# - Don't restart the shell between configs if you want comparable cache state.

set -euo pipefail

CONFIG="${1:?config name required (baseline|hifi2|fusion|whatever)}"
N="${2:-5}"

# Resolve paths
TT_METAL_HOME="${TT_METAL_HOME:-$HOME/tt-metal}"
HF_MODEL="${HF_MODEL:-$HOME/models/Qwen2.5-7B-Instruct}"
OUT_ROOT="$HOME/project/variance_results/$CONFIG"

if [[ ! -d "$TT_METAL_HOME" ]]; then
  echo "TT_METAL_HOME=$TT_METAL_HOME not found." >&2
  exit 1
fi
if [[ ! -d "$HF_MODEL" ]]; then
  echo "HF_MODEL=$HF_MODEL not found." >&2
  exit 1
fi

mkdir -p "$OUT_ROOT"

cd "$TT_METAL_HOME"
# shellcheck disable=SC1091
source python_env/bin/activate

export HF_MODEL TT_METAL_HOME
export MESH_DEVICE="${MESH_DEVICE:-P150x4}"

# Record what tt-metal commit we're on, so the variance dir is self-describing.
{
  echo "config=$CONFIG"
  echo "tt_metal_commit=$(git -C "$TT_METAL_HOME" rev-parse HEAD)"
  echo "tt_metal_status=$(git -C "$TT_METAL_HOME" status --porcelain | wc -l) files dirty"
  echo "host=$(hostname)"
  echo "started=$(date -Iseconds)"
} > "$OUT_ROOT/manifest.txt"

for i in $(seq 1 "$N"); do
  RUN_DIR="$OUT_ROOT/run_$i"
  if [[ -d "$RUN_DIR" ]]; then
    echo "[$CONFIG] run_$i already exists, skipping."
    continue
  fi
  echo "[$CONFIG] run $i / $N starting at $(date +%H:%M:%S)"
  python3 -m tracy -p -r \
    -o "$RUN_DIR" \
    --check-exit-code -a device_kernel_duration -t 5000 \
    -m 'pytest models/tt_transformers/demo/simple_text_demo.py \
        -k "device-perf and performance" \
        --num_layers 10 --batch_size 1 --max_seq_len 1024 \
        --max_generated_tokens 2 --mode decode --paged_attention 1 -x'
  echo "[$CONFIG] run $i done at $(date +%H:%M:%S)"
done

echo "ended=$(date -Iseconds)" >> "$OUT_ROOT/manifest.txt"

echo
echo "Done. CSVs are under $OUT_ROOT/run_*/reports/<timestamp>/ops_perf_results_*.csv"
echo "Next: python3 ~/project/scripts/aggregate_variance.py"
