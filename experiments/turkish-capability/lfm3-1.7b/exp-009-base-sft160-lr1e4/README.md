# exp-009-base-sft160-lr1e4

Status: GPU gates,100-step training, all matched inference and adapter-only local recovery completed; four-way owner review ready. See ../BASE-SFT160-ABLATION.md.

Hypothesis: CPT initialization contributes to poor Turkish expression. Change only initialization relative to exp007: train fresh LoRA directly on the same pinned untouched LiquidAI/LFM3-1.7B. Keep all160 frozen training rows, native labels, seed/order, LR1e-4, rank32/alpha64, batch8, warmup6 and100-step cosine horizon unchanged. Train100 steps and save60/100; preselect step60 (epoch3) for the matched comparison. Never substitute a shorter60-step cosine schedule.

Compare base, CPT-only, base?SFT step60 and CPT?SFT exp007 step60 on the same frozen dev20, CETVEL100 and grammar1600. Reuse hash-checked existing base/CPT?SFT outputs; generate the missing two arms. Keep separate reasoning4 off/on probes. Owner dev20 was already examined, so this is a diagnostic ablation, not a fresh unbiased quality estimate. No training data expansion or evaluation-derived targets.

Separate runner/runtime preserve the original pair's code, gates and outputs. Require native-label parity, fresh smoke/save/reload/generation and tiny-overfit before full training. Store exact source/config/input hashes, W&B tracking and raw outputs. Download adapters and small logs only, never full/merged weights. No automatic publication or deployment.

Owner review completed: all20 valid rankings. CPT-initialized exp007 step60 remains preferred over direct-base exp009 step60:12 wins,3 losses,5 ties. See ../BASE-SFT160-OWNER-REVIEW.md and its JSON for all verbatim reasoning, pairwise outcomes and limitations. This is a development result, not production readiness.
