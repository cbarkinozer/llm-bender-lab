# Turkish SFT pilot: two learning rates

Status: pod connected; environment and native-format preflight in progress.
No production SFT or reportable inference result exists yet.

Owner-confirmed pilot evaluation scope: protected20 + fixed stratified CETVEL100
from the historical500 + TurBLiMP1600, identically for CPT and both SFT models.
This narrows the cohort size to bound pilot cost; the matched decoding settings
below remain fixed. Full historical CPT500 is context only, not a paired100 score.

## Purpose and fixed comparison

Restore Turkish instruction following, useful answer length and stopping on the
published CPT model. This 80-example run is a pipeline and adaptation pilot;
general coverage expansion remains the main dataset project.

| Setting | exp-005-sft-lr1e4 | exp-006-sft-lr2e4 |
|---|---:|---:|
| Peak learning rate | 1e-4 | 2e-4 |
| Training examples | 80 | 80 |
| Epochs / optimizer updates | 5 / 50 | 5 / 50 |
| Micro batch / accumulation / effective batch | 2 / 4 / 8 | 2 / 4 / 8 |
| Warmup updates / scheduler | 3 / cosine | 3 / cosine |
| LoRA rank / alpha / dropout | 32 / 64 / 0 | 32 / 64 / 0 |
| Maximum training sequence / packing | 4096 / off | 4096 / off |
| Seed | 3407 | 3407 |

Learning rate is the only experimental training-setting difference. Larger LR
may restore behavior faster but overfit or erode CPT gains. Five epochs is a
predeclared short pilot budget, not an optimal duration established from data.
Use the final checkpoint from each run, with no test-based early stopping.

Both runs independently initialize fresh adapters on the same merged BF16
`cbarkinozer/LFM3-1.7B-Turkish-CPT` revision
`6f213ec25a944dab2fbdeb6d337deb0e0442e638`, over the pinned parent in configs.
Run B does not continue run A. Embeddings remain frozen. Target projection
names follow the previously validated LFM recipe, subject to actual module audit.

## Todo and execution order

1. Preserve the reviewed export; apply the three owner-authorized content repairs
   and normalize inherited system instructions in `sft-pilot80-v01`. These semantic
   copies retain the exact original reviewed text and split assignments.
2. Finish semantic leakage checks and freeze the training-ready tokenized manifest.
   Inspect native chat/reasoning serialization, all sequence lengths, assistant-only
   labels and supervised end-of-turn tokens. No silent truncation or target duplication.
   Optional reasoning is included once when supplied; simple direct answers remain
   direct. Reasoning support is shared by both runs, not the ablated variable.
3. Connect the GPU pod; reuse persistent caches and the prior pinned recipe after
   compatibility checks. Keep training and vLLM in separate environments. Verify
   the published CPT adapter merge and reload against the pinned parent.
4. Generate untouched CPT baseline outputs before any SFT; freeze prompt IDs,
   rendered prompts, token IDs, model hashes and generation settings.
5. Run finite-loss training/save/reload/generation smoke and a train-only tiny-overfit
   diagnostic. Verify nonzero correct labels, trainable modules and learning signal.
   Reset all diagnostic weights and optimizer state before either experiment.
6. Train A and B sequentially on the same pod and cached weights; record full
   effective configs, versions, hardware, loss/gradient curves and resource timing.
   Save adapters and tokenizers and verify both final checkpoints reload.
7. Run vLLM inference for both final models. Report the same frozen CETVEL500
   development cohort and TurBLiMP grammar regression suite. Run the protected
   reviewed 20 for final reporting once per model; never train or select checkpoints
   on them. Baseline results stay hidden from optimization decisions for those 20.
8. Provide blind A/B/C outputs for owner review, plus paired correctness/instruction
   outcomes, Turkish quality, requested format, response lengths, repetition and
   EOS/length/loop counts. Report raw counts on the tiny holdout, not broad claims.
9. Back up weights and logs outside Git; preserve small manifests and reports in Git.
   Expand reviewed coverage based on findings, especially multi-turn, coding and
   translation. Create separate development data before further tuning. Later:
   larger SFT, DPO, bounded MoE/diffusion trials, then Reflex-1 decision models.

## Matched inference protocol

Reuse the actual final CPT500 manifest rather than the earlier fast100 greedy
protocol: vLLM `0.34.0rc1.dev251+g7cc0a8a2b`, BF16, eager, batch4, prefix caching
off, GPU memory utilization0.75, context8192, output4096, temperature0.1,
top-k50, top-p1, repetition penalty1.1, seed3407. Retain historical explicit
stop token124900 (`ignore_eos=true` plus explicit stop IDs) and exact-loop guard,
including raw outputs and termination reasons. `ignore_eos=true` here does not
mean removing the explicit EOS stop rule.

The historical matched protocol uses `enable_thinking=false`. Training may include
optional reasoning, but a reasoning-enabled inference comparison is a separate
protocol that must be frozen and run on all three models if added. It must not be
mixed into the matched results. Use identical systems/template for each model
within each cohort; reviewed holdout uses the normalized system, historical
CETVEL uses its frozen historical prompts. Confirm the engine preserves template
and token parity before inference. Any runtime or stop-rule change requires a
fresh matched CPT baseline and explicit protocol version.

The existing 500 examples are repeatedly inspected development evidence, not a
pristine final benchmark. The 20 reviewed examples are too small and uneven by
capability for a reliable hyperparameter winner or release claim. Report both
predeclared runs; further tuning requires separate development examples.

## Pod handoff

An instance-specific Ed25519 key is stored under the owner's `.ssh` directory,
outside Git. Supply only its public key to the pod provider. After the pod exists,
the remaining connection input is its SSH command/address and port. No pod was
provisioned by this planning step. GPU runtime implementations and gates remain
to be completed; config status stays planned until they pass.
