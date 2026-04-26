**To:** Prof.\ Abdulrahman Mahmoud
**Cc:** Dongning Ma
**From:** Rassul Magauin
**Subject:** AI Systems final project — individual contribution (Qwen2.5-Coder on Blackhole)

Hi Prof. Mahmoud,

Here is my contribution writeup for the final project, with a short note on each teammate.

**My contribution.** I set up the profiling pipeline at the start of the project: built `tt-metal` with `ENABLE_TRACY=ON`, wrote the wrapper command we used for every run (`python -m tracy -p -r ... pytest models/tt_transformers/demo/simple_text_demo.py ...`), and produced the first end-to-end profile that surfaced TopK and the MLP block as the two largest kernel-time consumers. After we finished the TopK and HiFi2 attempts, I implemented the third optimization — fusing the MLP gate and up projections — directly in `models/tt_transformers/tt/mlp.py`. The non-trivial parts were: (1) building the per-device fused weight `w_gate_up` with the right column layout so `ShardTensor2dMesh` produces the expected stripe; (2) gating the fused path on `Mode.DECODE` so prefill and Galaxy configs keep the original two-linear flow (we found this out the hard way when prefill blew up with an `Invalid subtile broadcast type` error in `binary_ng`); and (3) figuring out that converting the fused output to `L1_MEMORY_CONFIG` before the slice was what made the downstream eltwise multiply 58% cheaper. I committed the fusion as `e05a044c4f`. In the report I wrote Sections 5 (Fusion), 6 (End-to-End), and the Conclusion, and I did the integration pass over everyone else's sections. I also handled the team's git workflow (commit hygiene, pre-commit hook fixes when `black`/`autoflake` re-formatted things mid-commit).

**Assylzhan Khamiyev** led the HiFi4 $\to$ HiFi2 change, which was our biggest single win (matmul $-32.4\%$, end-to-end $-12.0\%$). He read through the `DecodersPrecision.from_json_file` loader to confirm the string actually reaches the FPU compute config, made the 56 per-layer edits across `performance_decoder_config.json`, and ran the in-tree `ci-token-matching` check to confirm we weren't degrading generation quality. He also took the lead on the presentation deck and wrote Section 4 of the report.

**Mohammed Rashed Ali Yahmoor Alshehhi** led the TopK investigation. He's the one who actually opened up `ttnn/cpp/ttnn/operations/reduction/topk/`, found the multi-core bitonic sort code path, and formed the hypothesis that padding the per-device vocab to a power of two would flip dispatch. He implemented the change in `model_config.py`, ran the failed experiment, and did the post-mortem — pulling the `CORE COUNT` column out of the CSV to prove the kernel never switched paths. He produced the revert (`f6de95bb02`) and wrote Section 3 of the report, including the part on why the negative result is worth reporting.

**Sultan Akimaliyev** owned the profile-analysis side. He drove `tt-perf-report` against every CSV we generated, built all four tables in the report (baseline, TopK, HiFi2, fusion), and chased down the compile-cache variance question we'd raised in the checkpoint — he's the reason the methodology section has a real answer about why our deltas are stable. He wrote the Methodology and Baseline sections.

**Hamad Khalifa Alyahyaee** did the hardware bring-up and the literature-review side. He brought up the 4-card mesh (`MESH_DEVICE=P150x4`, firmware 19.4.2.0), got the cards talking through `tt-ccl`, and investigated the tensor-parallel layout enough to explain to the rest of us how `ShardTensor2dMesh` lines up with the AllGather/ReduceScatter calls in the decoder. He wrote the Background section, the Related Work section, and assembled `refs.bib`.

**Collaborative work.** The five of us spent an afternoon in front of the baseline-profile spreadsheet ranking bottlenecks together — that's where the project plan came from. The `binary_ng` prefill bug during fusion was pair-programmed: Mohammed and I were at the keyboard, Assylzhan re-ran the smoke test on each iteration, and Sultan watched the next CSV as soon as it came out. Code review on each commit was a five-person thing.

Happy to answer any follow-ups.

Best,
Rassul
