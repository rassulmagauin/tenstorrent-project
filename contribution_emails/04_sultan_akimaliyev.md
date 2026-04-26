**To:** Prof.\ Abdulrahman Mahmoud
**Cc:** Dongning Ma
**From:** Sultan Akimaliyev
**Subject:** Final project — individual contribution (Qwen2.5-Coder, Blackhole)

Hi Prof. Mahmoud,

Below is my contribution to the project and what each teammate did.

**My contribution.** I owned the profile-analysis side of the project — basically, every number that appears in the report came through me. Tracy emits a CSV (~4,900 rows per run, two trace-replay sessions) and the raw output is not easy to read: it mixes compile rows with steady-state rows, includes per-device and per-trace duplicates, and has 30+ columns including the `DEVICE KERNEL DURATION [ns]` we care about and the `CORE COUNT` column we ended up using to diagnose the TopK failure. I ran `tt-perf-report` against each CSV, wrote a small post-processing script to filter to device 0 and group by op type, and produced the cleaned per-operator totals. All four tables in the report (Baseline in Section 2, TopK in Section 3, HiFi2 in Section 4, Fusion in Section 5) are mine.

I also resolved the compile-cache variance question we'd flagged in the checkpoint. We had noticed back-to-back runs of architecturally identical models showing ~44% variation in matmul mean time, and we'd attributed it loosely to compile-cache state. For the final report I designed the run methodology that makes the deltas reproducible: warm caches inside the same shell session, identical `pytest` arguments, two trace-replay sessions per run, and totals (not means) reported across the full profile. The compile-cache-variance paragraph in the report is mine, and the methodology section explains why our deltas are stable under repeated measurement.

In the report I wrote Section 2 (Methodology) and the Baseline section that reads the table. I also did the cross-checking when teammates produced numbers — every speedup claim in the report has a CSV behind it that I can point to.

**Rassul Magauin** set up the Tracy profiling pipeline (this is what made my analysis work possible), produced the first baseline profile, implemented the gate/up MLP fusion in `mlp.py`, and wrote Sections 5, 6, and the Conclusion. He also did the integration pass on the document.

**Assylzhan Khamiyev** led the HiFi2 work, which was our biggest win. He traced the JSON config through `DecodersPrecision.from_json_file` to confirm the HiFi2 string actually reaches the FPU compute config, made the 56 edits across `performance_decoder_config.json`, and validated accuracy with `ci-token-matching`. The matmul-time reduction we measured (15.46 ms $\to$ 10.45 ms) came from his change. He took the lead on the presentation and wrote Section 4.

**Mohammed Rashed Ali Yahmoor Alshehhi** investigated TopK end-to-end. He read the C++ kernel under `reduction/topk/`, formed the multi-core bitonic-sort hypothesis, implemented the vocab padding in `model_config.py`, ran the experiment, and did the careful diagnosis when it slowed everything down by 36%. The `CORE COUNT` evidence that the kernel never switched paths is his finding. He wrote Section 3.

**Hamad Khalifa Alyahyaee** brought up the hardware (four p150 cards, firmware 19.4.2.0, the four-way TP mesh) and got the software stack to where the rest of us could actually run experiments. He also did the literature review, wrote the Background and Related Work sections, and built `refs.bib`.

**Collaborative work.** The bottleneck-ranking session that produced the project plan was all five of us in front of a baseline-profile spreadsheet — I had pulled the cleaned numbers and we ranked together. The fusion-broke-prefill debugging was pair-programmed (Rassul and Mohammed at the keyboard, Assylzhan and I running smoke tests and re-profiling between fixes). Each commit went through team review.

Best,
Sultan Akimaliyev
