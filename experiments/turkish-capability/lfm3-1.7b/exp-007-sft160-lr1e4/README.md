# exp-007-sft160-lr1e4

Status: training and all planned matched inference completed; development grading pending. See [results](../PILOT160-RESULTS.md).

Fresh LoRA on pinned CPT-merged parent,160 reviewed training examples, peak LR0.0001, five epochs/100 updates, six warmup steps, rank32. Save complete resumable checkpoints at60 and100 updates (epochs3/5). Same100-step cosine schedule.

See [pair plan](../PILOT160-PAIR-PLAN.md) and [launch handoff](../SFT160-POD-HANDOFF.md). Untouched LiquidAI is the evaluation baseline; select using separate dev20, never old20.
