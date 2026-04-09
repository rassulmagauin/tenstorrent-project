# ASPLOS 2026 Project Checkpoint

Qwen2.5-Coder on Tenstorrent Blackhole — 15% of project grade. Due **2026-04-10 @ 5:00 PM**.

## Template

Per the ASPLOS 2026 CFP (https://www.asplos-conference.org/asplos2026/cfp/):

- Class: `acmart` with `sigplan,nonacm` options (we also add `review,anonymous` for the checkpoint — remove `anonymous` if the course wants names visible).
- Body: 10 pt.
- Page numbers via `\settopmatter{printfolios=true}`.
- Bibliography style: `ACM-Reference-Format`.
- Target length for the checkpoint: 2–3 pages (full ASPLOS submissions are 11 pages; the checkpoint is shorter per course instructions).

## Files

- `main.tex` — the checkpoint document.
- `refs.bib` — bibliography (Qwen2.5-Coder tech report, tt-metal, tt-perf-report).
- `figures/` — drop any plots/diagrams here and `\includegraphics` them from `main.tex`.

## Compiling

**No TeX Live is installed on this machine.** Two easy options:

### Option A — Overleaf (recommended)
1. Overleaf → New Project → Upload Project → drop `main.tex`, `refs.bib`, `figures/`.
2. Menu → Settings → Compiler: `pdfLaTeX` (acmart works with pdfLaTeX).
3. Hit Recompile. Overleaf already has `acmart` preinstalled.

### Option B — local TeX Live
```bash
sudo apt install texlive-full      # large, ~5 GB
cd project/checkpoint
latexmk -pdf main.tex
```

## Removing `anonymous` for the course submission

The course checkpoint is probably not double-blind (check with Prof. Mahmoud / TA Dongning if unclear). To show author names in the compiled PDF, change:

```latex
\documentclass[sigplan,nonacm,review,anonymous]{acmart}
```

to:

```latex
\documentclass[sigplan,nonacm,review]{acmart}
```

## Notes on numbers

All numerical claims in `main.tex` are drawn from the tracy profile at
`tt-metal/generated/profiler/reports/qwen25_7b_decode/reports/2026_04_09_16_05_41/ops_perf_results_2026_04_09_16_05_41.csv`
and cross-checked against the Coder-7B rerun at
`tt-metal/generated/profiler/reports/qwen25_coder_7b_decode/reports/2026_04_09_16_53_18/`.
Matmul absolute times differ between the two runs due to compile-cache state;
the reported breakdown uses the 7B-Instruct run because its MLP times are
cache-cold and therefore conservative (i.e., we're not undercounting the
bottleneck we want to claim).
