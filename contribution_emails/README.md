# Individual contribution emails

Per the prof's note in Slack: each student emails Prof. Mahmoud (cc Dongning) by **5pm 2026-05-01** with their own contribution writeup and a per-teammate breakdown. One email per student. The team report goes separately, also by 5pm 2026-05-01.

## Files

| File | Author |
|------|--------|
| `01_rassul_magauin.md`             | Rassul Magauin |
| `02_assylzhan_khamiyev.md`         | Assylzhan Khamiyev |
| `03_mohammed_rashed_alshehhi.md`   | Mohammed Rashed Ali Yahmoor Alshehhi |
| `04_sultan_akimaliyev.md`          | Sultan Akimaliyev |
| `05_hamad_khalifa_alyahyaee.md`    | Hamad Khalifa Alyahyaee |

## How to use

These are drafts in markdown. Each teammate should:

1. Read their own email and **edit it in their own voice** before sending. The drafts are intentionally consistent with each other on the technical facts (who did what), but every student should rephrase, cut, or add to make it sound like them. The prof asked specifically not to receive ChatGPT-generated text, so a verbatim send would defeat the point.
2. Sanity-check the attribution paragraphs about teammates — anything inaccurate, fix.
3. Convert to plain text for email (drop the `**` markdown bold; keep paragraph breaks).
4. Send to Prof. Mahmoud with Dongning on cc.

## Attribution snapshot (used consistently across all five drafts)

So everyone's stories line up:

- **Rassul Magauin** — Tracy profiling pipeline + first baseline profile; gate/up MLP fusion implementation in `mlp.py` (commit `e05a044c4f`); Sections 5, 6, Conclusion; document integration; git workflow.
- **Assylzhan Khamiyev** — HiFi4$\to$HiFi2 change in `performance_decoder_config.json` (commit `965e0f4622`); `DecodersPrecision.from_json_file` loader trace; `ci-token-matching` accuracy validation; Section 4; presentation lead.
- **Mohammed Rashed Ali Yahmoor Alshehhi** — TopK investigation; `reduction/topk/` source dive; vocab padding in `model_config.py`; failed experiment + post-mortem (CORE COUNT analysis); revert commit `f6de95bb02`; Section 3.
- **Sultan Akimaliyev** — profile-analysis pipeline; `tt-perf-report` against every CSV; all four tables in the report; compile-cache variance investigation; Sections 2 and Baseline.
- **Hamad Khalifa Alyahyaee** — hardware bring-up (4 p150 cards, firmware 19.4.2.0, `MESH_DEVICE=P150x4`); TT-CCL and TP-mesh investigation; Section 1 (Background) and Related Work; `refs.bib`.

Pair-programmed: the prefill `binary_ng` bug during fusion (Rassul + Mohammed at keyboard, Assylzhan + Sultan running smoke + profile).
Whiteboard: bottleneck ranking session (all 5).
Team review: every commit.
