# Final Presentation

Qwen2.5-Coder on Tenstorrent Blackhole — ~15 min talk, 35% of the
project grade. Scheduled **2026-04-28 to 2026-04-30**.

## Format

- Beamer, `metropolis` theme, 16:9 aspect ratio.
- ~17 content slides + standout closing + 3 backup slides.
- Timing target: ~15 minutes for content, extra couple of minutes for
  Q&A backup slides.

## Files

- `slides.tex` — the deck.
- `figures/` — drop any images here and `\includegraphics` them. Currently empty.

## Compiling

### Option A — Overleaf
1. New Project → Upload Project → drop `slides.tex` and `figures/`.
2. Compiler: `XeLaTeX` (metropolis theme renders more cleanly there than under pdfLaTeX; pdfLaTeX still works but font metrics look slightly off).
3. Recompile.

### Option B — local TeX Live
```bash
sudo apt install texlive-full
cd project/presentation
latexmk -xelatex slides.tex
```

## Talk outline (with rough timings)

| # | Section                              | Minutes |
|---|--------------------------------------|---------|
| 1 | Title + spoiler                      | 1       |
| 2 | Blackhole + tt-metal programming model | 2     |
| 3 | Workload + methodology               | 1       |
| 4 | Baseline profile + "two things jump out" | 2   |
| 5 | Attempt 1: TopK padding (failure)    | 3       |
| 6 | Attempt 2: HiFi2                     | 2       |
| 7 | Attempt 3: gate/up fusion            | 3       |
| 8 | End-to-end + lessons                 | 1       |
|   | **Total**                            | **~15** |

Backup slides cover: reproduction command, commit SHAs, and the
compile-cache variance methodology note. Keep them in reserve for Q&A.

## Notes on delivery

- Spend real time on the \textbf{TopK failure}. That slide is the
  pedagogical payload of the talk and it is the one the course
  instructor is most likely to push back on.
- The fusion slide has a six-line code snippet. Don't read it; point at
  `use_fused = self.fuse_gate_up and mode == Mode.DECODE` and move on.
- The end-to-end table has four rows. Read them top to bottom, pause
  on 36.38~ms, then reveal the failure row at the bottom.
