**To:** Prof.\ Abdulrahman Mahmoud
**Cc:** Dongning Ma
**From:** Assylzhan Khamiyev
**Subject:** Final project contribution writeup — Qwen2.5-Coder optimization

Dear Prof. Mahmoud,

Below is what I worked on for the project and what each of my teammates did.

**My contribution.** I led the math-fidelity optimization (HiFi4 $\to$ HiFi2 on the MLP matmuls), which ended up being the largest single performance win in the project: total matmul kernel time dropped from 15.46 ms to 10.45 ms across the profile, and end-to-end device kernel time went from 41.77 ms to 36.75 ms ($-12.0\%$).

The change itself sounds trivial — flip two strings per layer in `performance_decoder_config.json` — but I had to be careful because it could have silently broken accuracy. I started by tracing how the JSON values actually reach the FPU. They go through `DecodersPrecision.from_json_file` in `model_config.py`, then into the `OpGroup` enum, then into the `li_ff1_3_compute_kernel_cfg` and `li_ff2_compute_kernel_cfg` fields that `mlp.py` consumes when building `ttnn.linear` calls. Once I was sure the string actually reaches the matmul compute config, I worked through the math: HiFi2 drops mantissa bits during the dot product, but Qwen's MLP weights are already BFP8 (the decoder config says so), and BFP8 has fewer mantissa bits than HiFi2 retains, so the precision drop is provably zero. I made the 56 per-layer edits, re-ran the in-tree `ci-token-matching` parameterization to confirm generation matches the HiFi4 reference, and re-profiled. The matmul speedup (~32%) lined up almost exactly with the predicted 2$\times$ FPU throughput scaled by the fraction of matmul time that's MLP. I committed it as `965e0f4622`.

In the report I wrote Section 4 (Attempt 2: HiFi2). I also took the lead on the presentation: built the slide deck (`presentation/slides.tex`, Beamer + metropolis), did the talk-timing pass, and rehearsed.

**Rassul Magauin** set up the Tracy profiling pipeline and produced the first baseline profile, which is what told us where to look. He also implemented the third optimization — gate/up projection fusion in `mlp.py` — which involved building a fused weight tensor, gating the new path on decode mode so prefill and Galaxy configs still work, and chasing down a tricky `binary_ng` interaction with width-sharded inputs. He committed the fusion (`e05a044c4f`) and wrote Sections 5, 6, and the Conclusion of the report.

**Mohammed Rashed Ali Yahmoor Alshehhi** took on the TopK investigation. He went into the C++ kernel code under `reduction/topk/`, hypothesized the multi-core bitonic sort path, implemented the per-device vocab padding in `model_config.py`, and then did the careful post-mortem when it slowed the model down by 36%. He's the one who pulled the `CORE COUNT` column to prove the kernel never switched paths. The negative result + diagnosis is his work; he wrote Section 3.

**Sultan Akimaliyev** did all the heavy lifting on profile analysis. Running `tt-perf-report` correctly is non-trivial (filtering trace-replay rows, separating compile rows, aggregating per device 0), and he produced the cleaned numbers we used in every table. He wrote Section 2 (Methodology) and the Baseline section, and he resolved the compile-cache variance question we'd flagged at the checkpoint.

**Hamad Khalifa Alyahyaee** brought up the four-card hardware mesh, got firmware 19.4.2.0 working with `MESH_DEVICE=P150x4`, and investigated the tensor-parallel sharding so we understood why CCL was 4.8% of the profile and not larger. He wrote Section 1 (Background) and Related Work, and he assembled `refs.bib`.

**Collaborative work.** We pair-programmed the prefill bug during the fusion attempt — Rassul and Mohammed at the keyboard, with Sultan and me running the smoke test and the profile in parallel as fixes landed. The bottleneck-ranking session at the start of the project was a whiteboard discussion with all five of us. Each commit went through team code review.

Best regards,
Assylzhan Khamiyev
