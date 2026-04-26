**To:** Prof.\ Abdulrahman Mahmoud
**Cc:** Dongning Ma
**From:** Hamad Khalifa Alyahyaee
**Subject:** Final project contribution — Qwen2.5-Coder on Blackhole

Dear Professor,

Here is my contribution writeup, with a short note on each of my teammates.

**My contribution.** I focused on two things: hardware/software bring-up at the start of the project, and the literature/background side at the end.

On the systems side: I brought up the four-Blackhole-p150 mesh that the rest of the project ran on. That meant getting firmware bundle 19.4.2.0 onto all four cards, configuring the host so `/dev/tenstorrent/{0..3}` were visible, building `tt-metal` from source with `ENABLE_TRACY=ON` so we could profile, and then getting the four cards to actually talk to each other through `tt-ccl`. The `MESH_DEVICE=P150x4` and `cluster_shape=(1,4)` configuration we used in every experiment is what came out of this. I also investigated the tensor-parallel layout enough to explain to the team why CCL was 4.8% of our profile and not larger: weights are sharded along the output dimension via `ShardTensor2dMesh`, which produces an AllGather after attention and a ReduceScatter after the MLP. Once I'd traced this, the team could focus on the MLP bottleneck without worrying about TP overhead being hidden somewhere.

On the writing side, I wrote the Background section in the report (Section 1: the Blackhole architecture overview, the `tt-metal` programming model, the Qwen2.5-Coder architectural specs, and the four-device TP layout). I also wrote the Related Work section, which meant going through the vLLM paper and the FasterTransformer documentation to confirm that gate/up projection fusion is a standard SwiGLU optimization elsewhere — so we could be honest in the paper that the algorithmic idea isn't novel and the contribution is the `tt-metal`-specific implementation observation (cheaper `binary_ng` on interleaved inputs). I assembled `refs.bib` (`qwen25coder`, `ttmetal`, `ttperfreport`, `vllm`).

**Rassul Magauin** set up the Tracy profiling pipeline on top of the `tt-metal` build I'd produced, and ran the first baseline profile that surfaced TopK and the MLP block as the two biggest bottlenecks. He then implemented the gate/up MLP fusion in `mlp.py` — building a fused weight tensor, gating it on decode mode so prefill paths stay intact, and chasing down a `binary_ng` interaction with width-sharded inputs that broke prefill the first time. He wrote Sections 5, 6, and the Conclusion, and did the integration pass on the document.

**Assylzhan Khamiyev** led the HiFi2 change, which gave us the largest single optimization win in the project ($-32\%$ matmul, $-12\%$ end-to-end). He traced the JSON config through the `DecodersPrecision` loader, confirmed that BFP8 weights make HiFi2 lossless on the dot product, made the per-layer edits across `performance_decoder_config.json`, and validated with `ci-token-matching`. He took the lead on the presentation deck.

**Mohammed Rashed Ali Yahmoor Alshehhi** investigated TopK. He read the C++ kernel source under `reduction/topk/`, hypothesized that vocab padding would unlock the multi-core bitonic-sort path, implemented and ran the experiment, and then did the post-mortem when the experiment slowed the model down by 36% — the `CORE COUNT` analysis is his. The negative-result section of the report (Section 3) is his work, and the future-work TopK item is documented from his investigation.

**Sultan Akimaliyev** owned profile analysis. He drove `tt-perf-report` against every CSV we generated, built every table in the report, and resolved the compile-cache variance question we'd raised at the checkpoint. The Methodology and Baseline sections are his work.

**Collaborative work.** The bottleneck-ranking discussion at the start of the project — when we sat with Sultan's cleaned baseline numbers and decided what to attempt in what order — was all five of us. When the fusion attempt broke prefill, Rassul and Mohammed pair-programmed the fix while Assylzhan and Sultan re-ran the smoke and the full profile in parallel. I reviewed Assylzhan's first presentation draft together with Sultan; the deck shape we ended up with came out of that round.

Thank you for the project.

Best regards,
Hamad Khalifa Alyahyaee
