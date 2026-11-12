# CPT pair: completed fast100 screening

Both independent one-epoch CPT adapters completed, and W&B confirms finished training runs with committed adapter artifacts. Both adapters, tokenizers, optimizer/scheduler/RNG states, training and diagnostic logs, data and provenance are recovered locally. No GPU workload remains active.

| Metric | Base | A: Wiki 2.2M | B: Mixed 10M |
|---|---:|---:|---:|
| Wiki NLL (lower better) | 3.262 | 2.491 | 2.386 |
| Web NLL (lower better) | 3.889 | 3.310 | 2.985 |
| Grammar accuracy (%) | 71.750 | 73.188 | 80.312 |
| TQUAD F1 (%) | 9.960 | 2.438 | 0.752 |
| XQuAD F1 (%) | 7.870 | 0.700 | 0.242 |
| EN to TR BLEU | 1.510 | 0.380 | 1.164 |
| EN to TR chrF | 30.540 | 15.154 | 27.706 |
| MLSum ROUGE-L (%) | 12.225 | 5.842 | 3.840 |

All GEC exact-match scores are zero. The small screening has only 20 examples per task; overlap metrics are sensitive to verbosity and are not human factual accuracy.

| Generation health | Base | A | B |
|---|---:|---:|---:|
| eos | 100 | 58 | 56 |
| length | 0 | 27 | 40 |
| exact_loop | 0 | 15 | 4 |
| Generation wall minutes | 0.85 | 5.27 | 5.38 |

The three passes total about 11.5 minutes of generation, excluding model load/setup and likelihood scoring. Request latencies overlap and must not be summed as elapsed time. All 300 unique answers are retained, including guarded/length cases. No empty predictions or timeout cases.

Interpretation: B is stronger than A on held-out text likelihood and grammar. Both CPT models show worse instruction-task scores and termination than the newly matched base. A seeded translation example changes from an attempted translation in base to invented film descriptions in A/B, so at least some regression is substantive instruction following, not just answer length. This is a raw CPT versus post-trained model trade-off; greater language-model likelihood does not imply better chat answers. No superiority or causal data-size claim is supported by this single-seed, mixed-source comparison.

Protocol: frozen balanced 100 IDs, 20 per task, batch4, greedy, repetition penalty1.15, 4096 output/8192 context, same native vLLM nightly and BF16. The old sequential rp1.05 run was interrupted by the owner and its partial answers are preserved, not mixed into new scores. Full 500 is reserved for finalists. Expand the frozen 100 to 200 by adding IDs rather than resampling. This historical comparison cohort is not a pristine final test.

The official model card general preset is temperature0.1, top_k50, repetition_penalty1.1. It was verified but NOT applied mid-run; treat it as a separately matched future protocol. Penalty1.15 did not eliminate repetition or long outputs. Do not claim batching preserves exact answers: pilot token sequences matched only1/5, with 11.58s sequential versus3.73s batched. Failed pilot and successful fix/retry logs are retained.

Next: review full seeded answers; test the official decoding preset if needed; audit Occam data before SFT and compare original+same SFT versus CPT+same SFT. No SFT, 50M or 100M run was started.

## Recovery

- C:\Users\barkin\Downloads\lfm3-cpt-ab-trained-20261112.tar.gz ? 416 verified members; SHA256 58979c044534484e4de851b12588e2e5d7b4de23a5b8111939ced5be5148969d
- C:\Users\barkin\Downloads\lfm3-fast100-results-20261112.tar.gz ? 126 verified members; SHA256 2c8e9833a65d494e1bd5c4c48aa061bce02df8899cec2e8d45430cd2b3a22add

Trained archive:416 files. Fast100 results/source/log/likelihood archive:126 files. Saved adapters and optimizer states were also rehashed after extraction. Regenerable merged weights are omitted; pinned original base, saved adapter, exact merge source, environment and merged-file hashes are preserved. Both adapters were successfully reloaded for merging; B was also reloaded for unmerged text/grammar scoring.

Readable full-answer reports: Downloads/LFM3-CPT-FAST100-20261112.html and .txt. No secrets are included. Raw data/results remain ignored. Current working changes are not committed.
