# Pilot160 results

Status: both SFT runs and all planned inference completed on2026-11-17; pod pipeline exit0. Owner blind review is complete: selected exp-007-sft160-lr1e4-step60 (LR1e-4, epoch3); see PILOT160-OWNER-REVIEW.md and JSON for all20 verbatim reviews and pairwise counts. No model was published or deployed.

Both runs used the frozen reviewed160, fresh rank32 LoRA on the same pinned CPT merge, five epochs/100 updates, six warmup steps, microbatch2/accumulation4, effective batch8, same seed/order, BF16 and max4096 without packing. Only peak LR differs between jobs. Checkpoints60/100 represent epochs3/5 of the same100-step cosine horizon. All four adapter, optimizer, scheduler, RNG and trainer-state checkpoints exist remotely. Merge/save/reload checks passed.

| Run | LR | Mean training loss | Training seconds | Tracking |
|---|---:|---:|---:|---|
| exp-007-sft160-lr1e4 | 1e-4 | 1.6826 | 76.2 | [W&B](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/7xwpzc8v) |
| exp-008-sft160-lr2e4 | 2e-4 | 1.3961 | 76.3 | [W&B](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/fmg9xcuf) |

Training loss is not a selection metric. Native labels passed for160 rows including30 nonempty reasoning traces; longest2289 tokens, no truncation, no zero targets. Tiny-overfit NLL fell from2.2545 to0.2693 on20 new training-only examples. Diagnostics were disposable and neither production run resumed them. Smoke generation validated the save/reload/inference path, not answer quality: the three-update disposable adapter hit the4096-token cap on one trivial query. Production dev stopping results are reported separately below. An allocator warning appeared in exp007 logs; the run continued and completed all100 updates with finite-loss/gradient checks, without a microbatch or recipe fallback.

The comparator is untouched LiquidAI/LFM3-1.7B at the pinned parent revision, generated before SFT. CPT remains initialization, not the primary inference comparator. New dev20, CETVEL100 and TurBLiMP1600 were identical for all five candidates. Primary generation used BF16/eager/batch4,context8192,new4096,temp0.1,topk50,topp1,repetition1.1,seed3407,explicit EOT and historical exact-loop guard, thinking disabled.

| Model/checkpoint | Grammar macro accuracy | Dev20 normal EOS | Thinking-on reasoning4 normal EOS |
|---|---:|---:|---:|
| base | 71.7500% | 20/20 | 3/4 |
| exp-007-sft160-lr1e4-step60 | 86.6250% | 20/20 | 4/4 |
| exp-007-sft160-lr1e4-step100 | 86.2500% | 20/20 | 4/4 |
| exp-008-sft160-lr2e4-step60 | 86.1250% | 20/20 | 4/4 |
| exp-008-sft160-lr2e4-step100 | 85.6875% | 20/20 | 4/4 |

These grammar scores refer to the pinned1600-pair subset under strict BOS+summed sentence-likelihood scoring, not the full official benchmark. Stopping and grammar do not establish answer correctness or naturalness. Task-specific CETVEL overlap metrics, per-phenomenon grammar counts and generation lengths/timing are in `PILOT160-INFERENCE-METRICS.json`. Do not pool unrelated task scores into one accuracy or infer a general quality winner from this table.

Separate reasoning4 off/on runs completed for base and all four checkpoints at the same4096 generated-token cap. Base thinking-on reached the cap on one item; all SFT thinking-on responses ended with EOS. Final correctness and rationale consistency still require grading; equal caps are not equal compute. Raw thinking and token IDs are preserved. Original protected20 were not trained on, used for checkpoint selection or regenerated here. Separate authored dev20 is small and not owner-adjudicated; follow its frozen rubric before choosing a checkpoint.

## Recovery

All four pilot160 LoRAs/tokenizers/configs,161 inference snapshot members, both SFT logs and small training metadata are locally hash-verified. The later direct-base control's two adapters and82 result members are also verified: see `BASE-SFT160-BACKUP.json`. Pod closure is safe for the owner-approved adapter-only scope. No full/merged model weights or complete optimizer/resume states were downloaded. Temporary transfer services were stopped; the agent has not shut down the pod.
