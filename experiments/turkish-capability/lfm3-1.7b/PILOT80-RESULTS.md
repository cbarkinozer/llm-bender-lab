# Pilot80 SFT pair results

Both predeclared final checkpoints completed 50 optimizer updates on the same 80 training rows. Only learning rate differed (1e-4 vs 2e-4). Five epochs; LoRA rank32, alpha64; 3 warmup updates; cosine; effective batch8; seed3407. Independent initialization from pinned CPT.

| Measure | CPT | SFT 1e-4 | SFT 2e-4 |
|---|---:|---:|---:|
| Holdout natural EOS /20 | 3 | 20 | 19 |
| Holdout median generated tokens | 4096.0 | 176.0 | 229.5 |
| CETVEL natural EOS /100 | 22 | 100 | 100 |
| TQuAD F1 (0-1) | 0.0040 | 0.2019 | 0.2350 |
| XQuAD TR F1 (0-1) | 0.0006 | 0.2479 | 0.2615 |
| EN-to-TR chrF (0-100) | 2.79 | 41.82 | 41.36 |
| MLSUM ROUGE-L (0-1) | 0.0182 | 0.1847 | 0.1736 |
| GECTurk exact match /20 | 0 | 0 | 0 |
| TurBLiMP1600 accuracy | 86.9375% | 87.0625% | 86.6250% |

The clearest measured gain is instruction-format/stopping recovery. Both SFTs finish all 100 CETVEL outputs naturally; CPT finishes22, hits length66, loops12. Higher overlap scores are partly explained by removing runaway output and do not establish broad reasoning gains. All GECTurk exact matches remain zero.

Representative holdout inspection reveals material unresolved errors: both fabricate table contents when a reservation text is missing; both change words/meaning in character restoration; both fail the separate-sentence constraints in the risks/actions prompt. The bread arithmetic reaches120TL, but 2e-4 emits a stray closing reasoning tag despite thinking-disabled inference. In the chemistry MCQ both select A but explanations contain unsupported or confused claims. These are qualitative observations, not completed human grades.

Grammar differs by only +2 and -5 net correct pairs versus CPT over1600. No significance or population-quality claim is made; phenomena are grouped. Both checkpoints and the full raw predictions are retained.

Primary human pass counts remain pending owner review. Use the local `pilot80-runtime-local/blind-review.html` and the predeclared review rubric. Do not choose a production winner solely from20 examples; no validation set exists. Shared task templates remain across train/test, so this is not a family-disjoint final test. CETVEL100 is development-only (20/task), not the official full benchmark.

Primary inference matched historical settings: vLLM BF16, eager, batch4, context8192, max4096 new tokens, temperature0.1, top-k50, top-p1, repetition penalty1.1, seed3407, explicit stop124900 and exact-loop guard. Thinking disabled across all three; this does not evaluate thinking-enabled benefits. Optional reasoning remained in training; no tag was forced onto direct-answer examples.

Training runtime: 61.64s (1e-4),63.15s (2e-4); average training loss1.8161 and1.5715, respectively (not validation quality). Both merged checkpoints passed exact save/reload parity. Merge versus unmerged BF16 logits can differ; each manifest records the observed maximum.

W&B: [1e-4](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/svtga9iu), [2e-4](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/47mlr39k).

Next: owner grades blind outputs; classify errors; add reviewed, diverse examples targeting missing-context clarification, faithful edits/extraction, constraints and factual explanations. Introduce a separate development set before further tuning. Keep final holdout out of training. Thinking-enabled comparison needs its own fixed matched protocol. Larger reusable dataset remains the priority before DPO.

Artifact recovery: each saved SFT adapter must be applied to the pinned CPT-merged
parent, not directly to untouched LiquidAI weights. First merge CPT revision
`6f213ec25a944dab2fbdeb6d337deb0e0442e638` into LiquidAI parent revision
`0dc4268b561499c648c7ba7c9466bf3d8d01517a` in BF16, then load the respective SFT
adapter and its saved tokenizer. The exact frozen code/config and model file hashes
are retained in the backup. Complete merged BF16 models remain on the pod.

Local backup completed: archive SHA256 and all352 manifest file hashes verified; both SFT adapters/tokenizers and raw outputs recovered. Four external W&B diagnostic log links were resolved and independently hash-verified. See `PILOT80-BACKUP.json`. The pod remains running; no model publication or Git push occurred.
