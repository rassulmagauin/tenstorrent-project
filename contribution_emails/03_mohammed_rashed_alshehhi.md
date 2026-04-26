**To:** Prof.\ Abdulrahman Mahmoud
**Cc:** Dongning Ma
**From:** Mohammed Rashed Ali Yahmoor Alshehhi
**Subject:** Individual contribution — final project (Qwen2.5-Coder on Blackhole)

Hi Professor,

Here is my contribution writeup, and what each of my teammates did.

**My contribution.** I led the TopK investigation, which is the part of the project that produced our negative result. The TopK op was the largest single number in the baseline profile (52% of device kernel time on a single Tensix core out of 130) and it didn't make sense to me, so I went and read the kernel source. I worked through `ttnn/cpp/ttnn/operations/reduction/topk/`, found the multi-core bitonic-sort code path, and noticed that bitonic sort prefers power-of-two widths. Our per-device TopK input was 38016 wide (Qwen vocab divided across 4 devices), which isn't a power of two. So the hypothesis was: pad the per-device vocab up to 65536, the kernel will pick its multi-core path, and TopK will stop being the bottleneck. I implemented this in `model_config.py` (it's a one-line change to `padded_vocab_size`), regenerated the LM-head tensor cache, and re-profiled.

The result was that TopK got 84% slower (5,455 µs $\to$ 10,039 µs per call) and end-to-end device time went up by 36%. So I had to do the post-mortem. I pulled the raw `ops_perf_results_*.csv` from the failed run, looked at the `CORE COUNT` column for the TopK rows, and confirmed it stayed at 1 in both the baseline and the padded run. The kernel never switched paths — we'd just fed the same single-core kernel 1.72$\times$ more data. The lesson is that on `tt-metal`, kernel dispatch is decided inside the device-operation class based on the full tensor spec, not on input shape alone, so the GPU-style "round up to a friendlier shape" reflex doesn't transfer. I produced the revert commit (`f6de95bb02`), cleared the stale `output_lm_head_*` cache files, and re-profiled to confirm the revert was clean. In the report I wrote Section 3 (Attempt 1: TopK), including the part on why we think the negative result is worth reporting. The deeper TopK fix — parallelize the kernel itself, or fuse it into `SamplingDeviceOperation` — is C++ kernel work and I documented it as future work in the report.

**Rassul Magauin** set up the profiling infrastructure (Tracy build, the wrapper command we used for every run, the device-perf pytest variant) and produced our first baseline profile. He then implemented the gate/up projection fusion in `mlp.py`, including the fused weight construction with the right per-device layout for `ShardTensor2dMesh`. He wrote Sections 5, 6, and the Conclusion, and integrated everyone's contributions into the final document.

**Assylzhan Khamiyev** led the HiFi2 work. He traced the loader path from JSON config through `DecodersPrecision.from_json_file` and `OpGroup` into the matmul compute config, made the 56 per-layer edits to `performance_decoder_config.json`, and ran the `ci-token-matching` accuracy check. The HiFi2 change is what made the biggest dent in our numbers. He took the lead on the presentation deck and wrote Section 4.

**Sultan Akimaliyev** owned the profile-analysis pipeline. He ran `tt-perf-report` against every CSV, built every table in the paper, and figured out the compile-cache variance issue (which we'd raised in the checkpoint without resolving). He wrote Section 2 (Methodology) and the Baseline section.

**Hamad Khalifa Alyahyaee** brought up the four-card Blackhole mesh and the surrounding software stack — firmware bundle 19.4.2.0, `MESH_DEVICE=P150x4`, the TT-CCL configuration that lets the four cards talk. He also wrote the Background and Related Work sections, and built the bibliography.

**Collaborative work.** When the gate/up fusion broke prefill (the `binary_ng` `Invalid subtile broadcast` error), Rassul and I pair-programmed the fix while Assylzhan re-ran smoke tests and Sultan watched the profiler output. The TopK source-code reading was technically my lead, but Rassul and Hamad sat with me through the kernel-walkthrough so we'd agree on the dispatch logic. The initial bottleneck-ranking session was a whiteboard discussion with all five of us.

Thank you for the project — the negative TopK result is honestly what I learned the most from.

Regards,
Mohammed Rashed Ali Yahmoor Alshehhi
