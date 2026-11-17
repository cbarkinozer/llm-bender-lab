# Turkish initialization ablation

Status: training, all inference, four-way Argilla upload and adapter-only local recovery completed. All six old/new LoRA checkpoints and required logs are verified locally; see BASE-SFT160-BACKUP.json. The pod can be closed; the agent has not shut it down.

Owner authorized the diagnostic on2026-11-17 after reviewing all20 pilot160 development rankings. The previous relative winner is exp007 LR1e-4 step60; those reviews do not establish production readiness.

Question: does the existing Turkish CPT stage help or hurt the same160-row SFT recipe?

| Arm | Initialization | SFT | Primary output |
|---|---|---|---|
| Base | Pinned untouched LiquidAI/LFM3-1.7B | None | Existing matched pilot160 output |
| CPT | Same pinned base plus pinned published CPT | None | New matched output |
| Base-SFT | Pinned untouched base | Frozen160, LR1e-4 | exp009 step60 |
| CPT-SFT | Same base plus CPT | Identical frozen160 recipe | Existing exp007 step60 |

All SFT settings remain identical:100-step cosine horizon, warmup6, seed3407, microbatch2/accum4, rank32/alpha64/dropout0, same nine modules, BF16 and max4096, no packing. Both new checkpoints60/100 are saved; step60 is preselected before seeing its output. Do not shorten the scheduler horizon to60 steps. The tokenized dataset and first full training batch match the original run byte for byte. Effective TrainingArguments differ only in output_dir.

Fresh untouched-base preflight passed native-label parity, initialization save/reload, three-step smoke/save/reload, train-only tiny-overfit, and vLLM smoke generation. No benchmark or owner reference answer enters training. Smoke and tiny-overfit adapters are disposable, never production initialization.

Inference uses unchanged frozen scripts, packets and matching settings: vLLM BF16/eager/batch4, context8192, output4096, temperature0.1, topk50, topp1, repetition penalty1.1, seed3407, thinking disabled, explicit EOT and historical exact-loop guard. Reuse the existing base and exp007step60 artifacts after checking stage receipts. Generate dev20, CETVEL100 and grammar1600 for the two missing arms, plus separate reasoning4 off/on probes. Raw answers, token IDs and logs must be recovered locally.

This is a diagnostic on development data already examined by the owner. Relative preferences cannot establish an absolute pass rate. A new blind four-way Argilla queue keeps only ranking and reasoning textboxes, with each identity appearing in each A-D position five times. Previous annotations remain untouched. An independent final evaluation is needed for general quality claims.

Remote pipeline: /workspace/base-sft160-ablation.log. Isolated runtime: base-sft160-runtime-local. Exact uploaded source hashes: preparation-local/base-sft160-source-manifest.json. Source and input freeze is also recorded in the new runtime. Original pilot160 sources/gates/runtime remain unchanged.

Recovery scope: adapters/tokenizers/configuration, small training metadata and complete inference/log artifacts only. No full/merged model weights or optimizer states downloaded. Keep the pod available until both old and new adapter recovery and all evaluation recovery are verified. No automatic pod shutdown, publication, deployment, commit or push.

See BASE-SFT160-INFERENCE-RESULTS.md, BASE-SFT160-INFERENCE-METRICS.json and BASE-SFT160-QUALITATIVE-NOTES.md for measured results and bounded interpretation.

Owner review completed: all20 valid rankings. CPT-initialized exp007 step60 remains preferred over direct-base exp009 step60:12 wins,3 losses,5 ties. See BASE-SFT160-OWNER-REVIEW.md and its JSON for all verbatim reasoning, pairwise outcomes and limitations. This is a development result, not production readiness.
