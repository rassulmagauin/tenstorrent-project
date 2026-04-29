# Variance / noise study

Per the prof's request: "test on many runs to see if the speedups are real or noise."

Two scripts:
- `run_variance.sh <config> [N=5]` — runs N timed profile iterations of whatever
  tt-metal commit is currently checked out, stashing the CSVs under
  `~/project/variance_results/<config>/run_*/`.
- `aggregate_variance.py` — reads every CSV under `variance_results/`, prints
  per-config mean ± std, computes Welch's t-test 95% CI on the delta vs
  baseline, and writes `summary.txt`, `summary.csv`, `summary.tex`.

## How to run

In **one shell session** (cache state matters), with `~/tt-metal` already built
with `ENABLE_TRACY=ON`:

```bash
cd ~/tt-metal

# 1) Baseline (5 runs, ~8 minutes)
git checkout a4d8480d3e          # baseline commit
~/project/scripts/run_variance.sh baseline 5

# 2) +HiFi2 (5 runs, ~8 minutes)
git checkout 965e0f4622          # baseline + HiFi2 change
~/project/scripts/run_variance.sh hifi2 5

# 3) +HiFi2 +fusion (5 runs, ~8 minutes)
git checkout e05a044c4f          # baseline + HiFi2 + fusion
~/project/scripts/run_variance.sh fusion 5

# 4) Aggregate
python3 ~/project/scripts/aggregate_variance.py
```

Total time: ~25 minutes hardware + 5 seconds aggregation.

## Output

`aggregate_variance.py` prints to stdout and writes three files:

- `~/project/variance_results/summary.txt` — paste this into your reply to
  the prof, or into the report.
- `~/project/variance_results/summary.csv` — flat (config, run, op, ms) for
  any further plotting / analysis.
- `~/project/variance_results/summary.tex` — drop-in LaTeX table for the
  report's variance subsection.

## What "noise" looks like in the output

For each config the script prints `std = X ms`. That's your noise floor.
Compare against the `Δ` line:

- If `|Δ| ≫ std` (e.g. Δ = -5 ms, std = 0.2 ms) → **real, not noise**.
- If `|Δ| ≈ std` → noise. The headline number doesn't survive.
- The 95% CI on the delta tells you the same thing more directly: if
  the CI doesn't include 0, the change is statistically significant.

## Caveats

- 5 runs is the minimum for a meaningful std. If you have time, do 10.
- Don't restart the shell between configs — keeping the python_env active
  and the OS file cache warm cuts variance.
- The first iteration of every config is implicitly a re-warm of the
  compile cache; the script keeps it for transparency. If results look
  weird, you can drop run 1 and re-aggregate.
- This study uses the same fixed prompt and shape as the rest of the
  report. To address "many applications" you'd add an input-shape sweep
  on top (Priority 2 in the plan).
