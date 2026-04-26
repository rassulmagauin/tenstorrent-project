# ASPLOS 2026 Final Project Report

Qwen2.5-Coder on Tenstorrent Blackhole — 45% of the project grade. Due **2026-05-01**.

## Template

Same as the checkpoint:

- Class: `acmart` with `sigplan,nonacm` options. The checkpoint had `review,anonymous` on top of this; the final report drops both so author names show up in the compiled PDF.
- Body: 10 pt.
- Page numbers via `\settopmatter{printfolios=true}`.
- Bibliography style: `ACM-Reference-Format`.
- Target length: no hard page cap per the course instructions. The report currently runs ~8–10 pages with figures and tables.

## Files

- `main.tex` — the final report.
- `refs.bib` — bibliography. Carries the three entries from the checkpoint (`qwen25coder`, `ttmetal`, `ttperfreport`) plus `vllm` for the Related Work section.
- `figures/` — drop plots/diagrams here and `\includegraphics` them from `main.tex`. Currently empty; all quantitative results are in-line tables rather than figures.

## Compiling

**No TeX Live is installed on this machine.** Two options:

### Option A — Overleaf (recommended)
1. Overleaf → New Project → Upload Project → drop `main.tex`, `refs.bib`, `figures/`.
2. Menu → Settings → Compiler: `pdfLaTeX`.
3. Hit Recompile.

### Option B — local TeX Live
```bash
sudo apt install texlive-full      # ~5 GB
cd project/final_report
latexmk -pdf main.tex
```

## Where the numbers come from

All numerical claims are drawn from four Tracy profiles under
`tt-metal/generated/profiler/reports/`:

- `qwen25_7b_decode/reports/2026_04_09_16_05_41/` — the baseline profile, also used for the checkpoint.
- `qwen25_7b_decode_topk_pad/reports/2026_04_14_*/` — the failed TopK padding run (for Table 2).
- `qwen25_7b_decode_hifi2/reports/2026_04_16_*/` — after the HiFi4→HiFi2 change (Table 3).
- `qwen25_7b_decode_fusion/reports/2026_04_18_*/` — after the gate/up projection fusion (Table 4).

All four runs use the same hardware, firmware, pytest command, `num_layers=10`,
`max_seq_len=1024`, `max_generated_tokens=2`, and `MESH_DEVICE=P150x4`.
Reported totals are across both trace-replay sessions in each run,
device~0 only.

The commit SHAs cited in the final section of the report
(`a4d8480d3e`, `965e0f4622`, `e05a044c4f`, `f6de95bb02`) are on the
`main` branch of our local tt-metal fork.

## If you need to re-run a profile

```bash
cd /home/rassulmagauin/tt-metal && source python_env/bin/activate
export HF_MODEL=/home/rassulmagauin/models/Qwen2.5-7B-Instruct
export TT_METAL_HOME=/home/rassulmagauin/tt-metal
export MESH_DEVICE=P150x4

python3 -m tracy -p -r \
  -o generated/profiler/reports/<name> \
  --check-exit-code -a device_kernel_duration -t 5000 \
  -m 'pytest models/tt_transformers/demo/simple_text_demo.py \
      -k "device-perf and performance" \
      --num_layers 10 --batch_size 1 --max_seq_len 1024 \
      --max_generated_tokens 2 --mode decode --paged_attention 1 -x'
```

Expect ~90 s wall time per run on a warm cache.
