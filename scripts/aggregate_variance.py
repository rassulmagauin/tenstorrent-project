#!/usr/bin/env python3
"""
Aggregate Tracy variance runs and emit:
  1. A per-config table (mean ± std of total device kernel time + headline ops)
  2. A pairwise comparison (Welch's t-test, 95% CI on the delta)
  3. A LaTeX-ready table you can paste into the report

Inputs:  variance_results/<config>/run_<i>/reports/<ts>/ops_perf_results_*.csv
Outputs: variance_results/summary.csv     (machine-readable)
         variance_results/summary.txt     (human-readable, paste into chat)
         variance_results/summary.tex     (LaTeX table fragment)

Usage:   python3 aggregate_variance.py
         python3 aggregate_variance.py --root /custom/path/variance_results
"""

import argparse
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

# Headline ops we track individually. Match against the OP CODE column.
# Anything else gets bucketed into "Other".
HEADLINE_OPS = {
    "Matmul":            ["Matmul"],
    "TopK":              ["TopK"],
    "BinaryNg":          ["BinaryNg", "BinaryDeviceOperation"],
    "ReduceScatter":     ["ReduceScatter"],
    "AllGather":         ["AllGather"],
    "RMSNorm/LayerNorm": ["LayerNorm", "RMSAllgatherNorm", "RMSNorm"],
    "SDPA decode":       ["ScaledDotProductAttentionDecode", "SDPA"],
    "Sampling":          ["Sampling"],
    "Slice":             ["Slice"],
    "ShardedToInterleaved": ["ShardedToInterleaved"],
}

DEVICE_KERNEL_DURATION_COL = "DEVICE KERNEL DURATION [ns]"
OP_CODE_COL = "OP CODE"
DEVICE_ID_COL = "DEVICE ID"


def find_csv(run_dir: Path) -> Path | None:
    """Find the ops_perf_results_*.csv inside run_dir/reports/<ts>/."""
    matches = list(run_dir.rglob("ops_perf_results_*.csv"))
    if not matches:
        return None
    # If multiple, prefer the one without "_with_signposts" suffix
    plain = [m for m in matches if "with_signposts" not in m.name]
    return (plain or matches)[0]


def bucket_op(op_code: str) -> str:
    for label, patterns in HEADLINE_OPS.items():
        for pat in patterns:
            if pat.lower() in op_code.lower():
                return label
    return "Other"


def parse_csv(csv_path: Path) -> dict[str, float]:
    """Return total ns per bucket for device 0, summed across the whole CSV."""
    totals: dict[str, float] = defaultdict(float)
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Some Tracy CSVs prefix columns with leading space; normalize.
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

            dev_id = row.get(DEVICE_ID_COL, "0")
            if dev_id != "0":
                continue
            dur_str = row.get(DEVICE_KERNEL_DURATION_COL, "")
            if not dur_str or not dur_str.replace(".", "", 1).isdigit():
                continue
            ns = float(dur_str)
            op_code = row.get(OP_CODE_COL, "Other")
            totals[bucket_op(op_code)] += ns
            totals["__TOTAL__"] += ns
    return totals


def collect(root: Path) -> dict[str, list[dict[str, float]]]:
    """Return {config_name: [run1_totals, run2_totals, ...]}"""
    out: dict[str, list[dict[str, float]]] = {}
    for cfg_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        runs = []
        for run_dir in sorted(cfg_dir.glob("run_*")):
            csv_path = find_csv(run_dir)
            if csv_path is None:
                continue
            runs.append(parse_csv(csv_path))
        if runs:
            out[cfg_dir.name] = runs
    return out


def mean_std(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (statistics.mean(values) if values else 0.0, 0.0)
    return statistics.mean(values), statistics.stdev(values)


def t_critical_95(df: int) -> float:
    """Two-sided 95% t critical for small df. Hardcoded for df 1..30; falls back to z."""
    table = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131,
        20: 2.086, 25: 2.060, 30: 2.042,
    }
    if df in table:
        return table[df]
    keys = sorted(table.keys())
    if df > max(keys):
        return 1.96
    # nearest lower df
    for k in reversed(keys):
        if k <= df:
            return table[k]
    return 1.96


def welch(a: list[float], b: list[float]) -> tuple[float, float, float, int]:
    """Welch's t-test for the difference of means (b - a). Returns (delta, se, ci95, df)."""
    ma, sa = mean_std(a)
    mb, sb = mean_std(b)
    na, nb = len(a), len(b)
    delta = mb - ma
    if na < 2 or nb < 2:
        return (delta, 0.0, 0.0, 0)
    va = sa**2 / na
    vb = sb**2 / nb
    se = math.sqrt(va + vb)
    if se == 0:
        return (delta, 0.0, 0.0, na + nb - 2)
    df_num = (va + vb) ** 2
    df_den = (va**2 / (na - 1)) + (vb**2 / (nb - 1))
    df = max(1, int(df_num / df_den))
    tcrit = t_critical_95(df)
    return delta, se, tcrit * se, df


def fmt_ms(ns: float) -> str:
    return f"{ns / 1e6:.2f}"


def write_summary(root: Path, data: dict[str, list[dict[str, float]]]):
    # Order configs sensibly if present
    preferred = ["baseline", "hifi2", "fusion"]
    cfgs = [c for c in preferred if c in data] + [c for c in data if c not in preferred]

    # ----- summary.txt -----
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("Variance summary (all times in ms, totals across full profile, device 0)")
    lines.append(f"Configs found: {', '.join(cfgs)}")
    for c in cfgs:
        lines.append(f"  {c}: N = {len(data[c])} runs")
    lines.append("=" * 78)
    lines.append("")

    # Per-config breakdown
    op_order = ["__TOTAL__"] + list(HEADLINE_OPS.keys()) + ["Other"]
    header = f"{'Op':<24}" + "".join(f"  {c:<18}" for c in cfgs)
    lines.append(header)
    lines.append("-" * len(header))
    for op in op_order:
        row = f"{('TOTAL' if op == '__TOTAL__' else op):<24}"
        for c in cfgs:
            vals_ms = [r.get(op, 0.0) / 1e6 for r in data[c]]
            m, s = mean_std(vals_ms)
            row += f"  {m:7.2f} ± {s:5.2f}    "
        lines.append(row)
    lines.append("")

    # Pairwise comparisons (relative to first config = baseline)
    if len(cfgs) >= 2:
        base = cfgs[0]
        lines.append(f"Deltas vs {base} (95% CI from Welch's t-test, ms):")
        for c in cfgs[1:]:
            a = [r.get("__TOTAL__", 0.0) / 1e6 for r in data[base]]
            b = [r.get("__TOTAL__", 0.0) / 1e6 for r in data[c]]
            delta, se, ci, df = welch(a, b)
            ma, _ = mean_std(a)
            mb, _ = mean_std(b)
            pct = 100 * (mb - ma) / ma if ma else 0
            lines.append(
                f"  {c:<10} -> Δ = {delta:+.2f} ms (±{ci:.2f}, 95% CI),  "
                f"{pct:+.1f}%,  df={df}"
            )
        lines.append("")

        # Verdict line: is the delta larger than the noise floor?
        lines.append("Noise-floor check:")
        for c in cfgs:
            vals = [r.get("__TOTAL__", 0.0) / 1e6 for r in data[c]]
            _, s = mean_std(vals)
            lines.append(f"  {c:<10} std = {s:.3f} ms  (treat as noise floor)")

    summary_txt = "\n".join(lines)
    (root / "summary.txt").write_text(summary_txt + "\n")
    print(summary_txt)
    print(f"\nWrote {root / 'summary.txt'}")

    # ----- summary.csv -----
    csv_path = root / "summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "run", "op", "ms"])
        for c in cfgs:
            for i, run in enumerate(data[c], start=1):
                for op, ns in run.items():
                    w.writerow([c, i, op, ns / 1e6])
    print(f"Wrote {csv_path}")

    # ----- summary.tex -----
    if len(cfgs) >= 2:
        tex = []
        tex.append(r"\begin{table}[h]")
        tex.append(r"\centering")
        tex.append(r"\small")
        tex.append(r"\caption{End-to-end device kernel time, mean $\pm$ std across "
                   f"{len(data[cfgs[0]])} repeated runs per config. "
                   r"95\% CI on $\Delta$ from Welch's $t$-test.}")
        tex.append(r"\label{tab:variance}")
        tex.append(r"\begin{tabular}{lrr}")
        tex.append(r"\toprule")
        tex.append(r"Config & Total (ms) & $\Delta$ vs.\ baseline (ms, 95\% CI) \\")
        tex.append(r"\midrule")
        base_vals = [r.get("__TOTAL__", 0.0) / 1e6 for r in data[cfgs[0]]]
        bm, bs = mean_std(base_vals)
        tex.append(f"{cfgs[0]} & {bm:.2f} $\\pm$ {bs:.2f} & --- \\\\")
        for c in cfgs[1:]:
            v = [r.get("__TOTAL__", 0.0) / 1e6 for r in data[c]]
            cm, cs = mean_std(v)
            delta, se, ci, df = welch(base_vals, v)
            tex.append(
                f"{c} & {cm:.2f} $\\pm$ {cs:.2f} & {delta:+.2f} $\\pm$ {ci:.2f} \\\\"
            )
        tex.append(r"\bottomrule")
        tex.append(r"\end{tabular}")
        tex.append(r"\end{table}")
        (root / "summary.tex").write_text("\n".join(tex) + "\n")
        print(f"Wrote {root / 'summary.tex'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path,
                    default=Path.home() / "project" / "variance_results")
    args = ap.parse_args()

    if not args.root.is_dir():
        ap.error(f"--root {args.root} not found")

    data = collect(args.root)
    if not data:
        ap.error(f"No CSVs found under {args.root}")

    write_summary(args.root, data)


if __name__ == "__main__":
    main()
