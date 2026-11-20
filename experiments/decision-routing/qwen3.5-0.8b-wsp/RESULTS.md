# Reflex WSP routing comparison

## Published reference (unchanged)

| Benchmark | Cases / decisions | Base Qwen3.5-0.8B | Reflex-1 | Laya English |
|---|---:|---:|---:|---:|
| MOBILE_ROUTING9 | 180 / 180 | 54.44 | 91.11 | 47.22 |
| typed-decisions | 400 / 2000 | 34.10 | 60.70 | 36.30 |
| BANKING77 | 462 / 462 | 8.44 | 74.89 | 36.36 |
| CLINC150 | 450 / 450 | 4.44 | 81.11 | 55.33 |

## Current measurements

| Benchmark | Cases / decisions | Qwen parent | WSP base | Released Reflex-1 | WSP Reflex-1.5 candidate |
|---|---:|---:|---:|---:|---:|
| MOBILE_ROUTING9 | 180 / 180 | 66.67 | 63.89 | 91.11 | 90.56 |
| typed-decisions | 400 / 2000 | 34.10 | 33.65 | 60.70 | 57.35 |
| BANKING77 | 462 / 462 | 8.44 | 6.71 | 74.89 | 70.13 |
| CLINC150 | 450 / 450 | 4.44 | 1.56 | 81.11 | 81.33 |

All current runs use the exact frozen published cohorts. Phone parent/WSP use a matched BF16 GPU schema-based non-thinking JSON router, so their scores must be compared with each other; they are a distinct profile from the historical A32 raw-HTTP base router. Released/candidate phone runs use native 4-bit decision-head inference. General parent/WSP runs use identically seeded fresh decision heads, matching the published general reference profile; these are not generative zero-shot classification scores. Adapter runs restore trained heads. Historical Laya and A32 latency are not remeasured here.

Training/checkpoint choice uses recovered training/validation/calibration splits only. Test cohorts never select checkpoints or calibration. A candidate designation is not a release or an improvement claim. Raw per-decision logits/predictions, source hashes, precision and runner manifests accompany each run.
