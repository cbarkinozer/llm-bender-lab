# exp-003 handoff

The full SFT finished successfully on 2026-09-19.

| Field | Value |
| --- | --- |
| Model | `unsloth/Qwen3.5-4B` at revision `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636` |
| Data | 2,442 rows; SHA-256 is recorded in `config.yaml` and manifests |
| Training | bf16 LoRA, rank 16, alpha 16, 2 epochs, seed 3407 |
| Runtime | 1,397.7 seconds; 612 steps |
| Mean train loss | 0.731044 |
| GPU memory | 8.851 GB allocated, 8.934 GB reserved |
| Tracking | W&B run `w87rvm0r` in project `llm-bender-lab-response-style-control` |

The last logged loss is a batch/window measurement, not the mean training loss;
therefore a lower value near the end followed by a higher final logged value is
normal and is not evidence of regression. No validation loss was used. The
frozen 100-item benchmark and blind human rubric are the quality gate.

## Blind evaluation

Both base and adapter outputs were generated for all 100 test prompts with
thinking disabled, greedy decoding, temperature 0, and max 256 new tokens.
`results/blind-review/blind-review.csv` is the only file to import into Argilla.
It contains anonymous `output_a` and `output_b` columns. The identity map is in
`blind-mapping-sealed.json` and must remain hidden until scoring is complete.

## Reproducibility

The local `exp-003-repro-bundle.tar.gz` contains the final adapter, manifests,
raw outputs, blind files, W&B files, and environment snapshots. The verified
SHA-256 is:

```text
edfa00fbc47f03b4c79428991f1d51c9feb4ca688b3f27e9c843200de4e76fd9
```

For a fresh pod, follow `POD-RECOVERY.md`. The critical fix is Torch 2.7.1 +
CUDA 12.8 + Triton 3.3.1 + flash-linear-attention 0.5.2; Torch 2.4/Triton 3.0
caused the slow fallback.
