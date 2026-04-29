#!/usr/bin/env python3
"""
Aggregate Tracy shape-sweep runs and emit a config x seq_len matrix of
total device kernel time (mean of N runs, ms).

Inputs:  shape_sweep_results/<config>/seq<N>/run_<i>/.../ops_perf_results_*.csv
Outputs: shape_sweep_results/summary.txt
         shape_sweep_results/summary.csv
         shape_sweep_results/summary.tex
"""

import argparse
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

DEVICE_KERNEL_DURATION_COL = "DEVICE KERNEL DURATION [ns]"
DEVICE_ID_COL = "DEVICE ID"


def find_csv(run_dir: Path) -> Path | None:
    if (run_dir / "FAILED.txt").exists():
        return None
    matches = list(run_dir.rglob("ops_perf_results_*.csv"))
    if not matches:
        return None
    plain = [m for m in matches if "with_signposts" not in m.name]
    return (plain or matches)[0]


def total_ms(csv_path: Path) -> float:
    total = 0.0
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            if row.get(DEVICE_ID_COL, "0") != "0":
                continue
            dur = row.get(DEVICE_KERNEL_DURATION_COL, "")
            if dur and dur.replace(".", "", 1).isdigit():
                total += float(dur)
    return total / 1e6


def collect(root: Path) -> dict[tuple[str, int], list[float]]:
    """Returns {(config, seq_len): [run_totals_ms]}"""
    out: dict[tuple[str, int], list[float]] = defaultdict(list)
    for cfg_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for seq_dir in sorted(cfg_dir.glob("seq*")):
            m = re.match(r"seq(\d+)", seq_dir.name)
            if not m:
                continue
            seq = int(m.group(1))
            for run_dir in sorted(seq_dir.glob("run_*")):
                csv_path = find_csv(run_dir)
                if csv_path is None:
                    continue
                out[(cfg_dir.name, seq)].append(total_ms(csv_path))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path,
                    default=Path.home() / "project" / "shape_sweep_results")
    args = ap.parse_args()

    if not args.root.is_dir():
        ap.error(f"--root {args.root} not found")

    data = collect(args.root)
    if not data:
        ap.error(f"No CSVs found under {args.root}")

    # Pull configs and seq lens
    preferred = ["baseline", "hifi2", "fusion"]
    configs = sorted({c for c, _ in data.keys()},
                     key=lambda c: preferred.index(c) if c in preferred else 99)
    seqs = sorted({s for _, s in data.keys()})

    # ----- summary.txt -----
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append("Shape sweep — total device kernel time, mean of N runs (ms)")
    lines.append(f"Configs: {', '.join(configs)}")
    lines.append(f"Seq lens: {', '.join(str(s) for s in seqs)}")
    lines.append("=" * 78)
    lines.append("")

    header = f"{'Config':<12}" + "".join(f"  seq={s:<6}" for s in seqs)
    lines.append(header)
    lines.append("-" * len(header))
    means: dict[tuple[str, int], float] = {}
    for c in configs:
        row = f"{c:<12}"
        for s in seqs:
            vals = data.get((c, s), [])
            if not vals:
                row += f"  {'--':<8}"
                continue
            m = statistics.mean(vals)
            means[(c, s)] = m
            std = statistics.stdev(vals) if len(vals) > 1 else 0.0
            row += f"  {m:6.2f}±{std:.3f}"
        lines.append(row)
    lines.append("")

    if "baseline" in configs:
        lines.append("Speedup vs baseline (%):")
        header2 = f"{'Config':<12}" + "".join(f"  seq={s:<6}" for s in seqs)
        lines.append(header2)
        lines.append("-" * len(header2))
        for c in [x for x in configs if x != "baseline"]:
            row = f"{c:<12}"
            for s in seqs:
                if (c, s) not in means or ("baseline", s) not in means:
                    row += f"  {'--':<8}"
                    continue
                base = means[("baseline", s)]
                cur = means[(c, s)]
                pct = 100 * (cur - base) / base
                row += f"  {pct:+6.2f}%   "
            lines.append(row)
        lines.append("")

    summary_txt = "\n".join(lines)
    (args.root / "summary.txt").write_text(summary_txt + "\n")
    print(summary_txt)
    print(f"\nWrote {args.root / 'summary.txt'}")

    # ----- summary.csv -----
    csv_path = args.root / "summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "seq_len", "run", "total_ms"])
        for (c, s), vals in sorted(data.items()):
            for i, v in enumerate(vals, start=1):
                w.writerow([c, s, i, f"{v:.4f}"])
    print(f"Wrote {csv_path}")

    # ----- summary.tex -----
    if "baseline" in configs:
        tex = []
        tex.append(r"\begin{table}[h]")
        tex.append(r"\centering")
        tex.append(r"\small")
        cols = "l" + "r" * len(seqs)
        tex.append(r"\caption{Total device kernel time (ms) across input "
                   "shapes, mean of N runs per cell. Speedup percentages "
                   "are versus the baseline at the same sequence length.}")
        tex.append(r"\label{tab:shape-sweep}")
        tex.append(r"\begin{tabular}{" + cols + "}")
        tex.append(r"\toprule")
        tex.append("Config & " + " & ".join(f"seq={s}" for s in seqs) + r" \\")
        tex.append(r"\midrule")
        for c in configs:
            row = c
            for s in seqs:
                if (c, s) in means:
                    m = means[(c, s)]
                    if c == "baseline":
                        row += f" & {m:.2f}"
                    else:
                        base = means.get(("baseline", s))
                        if base:
                            pct = 100 * (m - base) / base
                            row += f" & {m:.2f} ({pct:+.1f}\\%)"
                        else:
                            row += f" & {m:.2f}"
                else:
                    row += " & ---"
            tex.append(row + r" \\")
        tex.append(r"\bottomrule")
        tex.append(r"\end{tabular}")
        tex.append(r"\end{table}")
        (args.root / "summary.tex").write_text("\n".join(tex) + "\n")
        print(f"Wrote {args.root / 'summary.tex'}")


if __name__ == "__main__":
    main()
