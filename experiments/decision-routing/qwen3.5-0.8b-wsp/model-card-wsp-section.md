## WSP base substitution experiment

We tested whether replacing the original Qwen3.5-0.8B starting weights with [RikiyaT/Qwen3.5-0.8B-weight-space-programming](https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming/tree/d1671a178705bcab7644806d23c535517f35723b) improves Reflex routing. The resulting **Reflex-1-WSP-experimental** candidate is a separate experiment, not a Reflex-1.5 release. Reflex-1 remains the recommended artifact in this repository.

Accuracy (%), on the same frozen evaluation cohorts:

| Benchmark | Cases / decisions | Qwen parent (new run) | WSP base | Reflex-1 (reproduced) | Reflex-1-WSP-experimental (trained) |
| --- | ---: | ---: | ---: | ---: | ---: |
| MOBILE_ROUTING9 | 180 / 180 | 66.67 | 63.89 | 91.11 | 90.56 |
| typed-decisions | 400 / 2000 | 34.10 | 33.65 | 60.70 | 57.35 |
| BANKING77 | 462 / 462 | 8.44 | 6.71 | 74.89 | 70.13 |
| CLINC150 | 450 / 450 | 4.44 | 1.56 | 81.11 | 81.33 |

**Readout differences:** Parent/WSP phone scores use matched BF16 vLLM GPU generation with identical schema prompts, thinking disabled, greedy constrained JSON and a 128-token output cap (zero errors or capped outputs). They differ from the historical A32 app-router profile that scored 54.44%; compare 66.67 with 63.89 within this new profile. Trained phone models use native 4-bit decision-head inference. General parent/WSP scores use identically seeded fresh decision heads, not generative zero-shot classification. Released/candidate general scores restore trained heads. All four released Reflex-1 accuracy scores were reproduced; historical Laya and A32 resource measurements were not repeated.

**Training:** The WSP candidate was initialized fresh and trained with the recovered original recipe and ordered 1,562-row mixture: 781 phone, 391 typed-decisions, 195 BANKING77 and 195 CLINC150. It used the original tokenizer/config metadata with WSP weights, 4-bit loading, BF16 computation, LoRA rank/alpha 16, seed 3407, backbone LR 2e-4, head LR 1e-4, effective batch 32, sequence length 4096 and 120 optimizer steps. Checkpoint selection used the equal mean of phone/general validation accuracy, with independent calibration; test cohorts did not select checkpoints or calibration. The two WSP-edited tensors remained different from the parent after 4-bit loading. Training and inference ran on an RTX 4090.

**Outcome:** Compared with reproduced Reflex-1, the trained WSP candidate changed accuracy by -0.56, -3.35, -4.76 and +0.22 percentage points respectively. CLINC150 gained one correct case out of 450. This single-seed experiment did not demonstrate an overall improvement; it does not establish that WSP is generally worse or better. No new release or mobile-runtime performance claim follows from this result.

The original release weights are unchanged. [Experiment results](experiments/wsp/RESULTS.md) and [training manifest](experiments/wsp/candidate-training-manifest.json) document this follow-up. Raw predictions, logs, the experimental adapter and checkpoints are preserved locally; the experimental weights are not part of the recommended release.

