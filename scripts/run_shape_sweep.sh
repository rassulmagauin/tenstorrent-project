#!/usr/bin/env bash
# Run profile iterations of the current tt-metal state across multiple
# max_seq_len values. Used for the input-shape sweep that complements
# the noise-floor variance study.
#
# Usage:
#   ./run_shape_sweep.sh <config_name> [N=2]
#
# Output:
#   ~/project/shape_sweep_results/<config>/seq<N>/run_<i>/...

set -euo pipefail

CONFIG="${1:?config name required (baseline|hifi2|fusion)}"
N="${2:-2}"
SEQ_LENS=(512 1024 2048)

TT_METAL_HOME="${TT_METAL_HOME:-$HOME/tt-metal}"
HF_MODEL="${HF_MODEL:-$HOME/models/Qwen2.5-7B-Instruct}"
OUT_ROOT="$HOME/project/shape_sweep_results/$CONFIG"

mkdir -p "$OUT_ROOT"

cd "$TT_METAL_HOME"
# shellcheck disable=SC1091
source python_env/bin/activate

export HF_MODEL TT_METAL_HOME
export MESH_DEVICE="${MESH_DEVICE:-P150x4}"

{
  echo "config=$CONFIG"
  echo "tt_metal_commit=$(git -C "$TT_METAL_HOME" rev-parse HEAD)"
  echo "seq_lens=${SEQ_LENS[*]}"
  echo "runs_per_shape=$N"
  echo "host=$(hostname)"
  echo "started=$(date -Iseconds)"
} > "$OUT_ROOT/manifest.txt"

for seq in "${SEQ_LENS[@]}"; do
  SEQ_DIR="$OUT_ROOT/seq${seq}"
  mkdir -p "$SEQ_DIR"
  for i in $(seq 1 "$N"); do
    RUN_DIR="$SEQ_DIR/run_$i"
    if [[ -d "$RUN_DIR" ]]; then
      echo "[$CONFIG seq=$seq] run_$i already exists, skipping."
      continue
    fi
    echo "[$CONFIG seq=$seq] run $i / $N at $(date +%H:%M:%S)"
    set +e
    python3 -m tracy -p -r \
      -o "$RUN_DIR" \
      --check-exit-code -a device_kernel_duration -t 5000 \
      -m "pytest models/tt_transformers/demo/simple_text_demo.py \
          -k 'device-perf and performance' \
          --num_layers 10 --batch_size 1 --max_seq_len $seq \
          --max_generated_tokens 2 --mode decode --paged_attention 1 -x"
    rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "[$CONFIG seq=$seq] run $i FAILED (exit $rc), continuing"
      echo "FAILED" > "$RUN_DIR/FAILED.txt"
    else
      echo "[$CONFIG seq=$seq] run $i done at $(date +%H:%M:%S)"
    fi
  done
done

echo "ended=$(date -Iseconds)" >> "$OUT_ROOT/manifest.txt"
