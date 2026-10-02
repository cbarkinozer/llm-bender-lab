# Base draft generation completed

2026-10-02, exp-009 minimal-edit prompt selection v2.

- 100 complete answers; fixed 80 train / 20 validation split unchanged.
- 100 native EOS/end-of-turn stops; zero length-limit retries or truncations.
- Output tokens: total 41,142; mean 411.42; maximum 1,735 (initial cap 4,096).
- Model/tokenizer: unsloth/Qwen3.5-4B,
  revision 3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636; no adapter, BF16.
- vLLM 0.20.1; Torch 2.11.0 / CUDA 13.0; Transformers 4.57.6;
  tokenizers 0.22.2; RTX 4090 24 GB, driver 580.95.05.
- Greedy, repetition penalty 1.05, seed 3407, native chat template,
  non-thinking, no added system prompt; context 32,768, no input truncation.
- Serial requests, max_num_seqs=1, eager mode, prefix caching disabled,
  text-only, GPU memory utilization 0.85. This is not a throughput benchmark.
- UTC run interval: 13:02:36.796710 to 13:27:20.474267.
- Clean generation source: 6ba79eb8ff1a006c6a06b10ebfa4ff875158c6f5.
- No fine-tuning and no W&B logging. GPU idle after engine shutdown.

## Artifact identity and backup

Dataset SHA256:
`c4a770780949c2508d5947c881b0f3834b75941674ccac6c5191d5895a0d3713`

Drafts SHA256:
`5acadb04efa666019bbdabfa6caf20fe8caa4b7b941dea54301946488f41b4cd`

Attempts SHA256:
`66ceb0018e2303dc43c720bddb9a50e6f09c7e957b04dfc207fd4c88585070cd`

Verified local backup root:
`C:\Users\cbark\Documents\llm-bender-artifacts\exp-009-minimal-edit`

Final raw outputs/configs/manifests are in
`exp009-artifacts/penalty105-full/`. The backup also contains source Git
bundles, environment freeze, setup/repair logs, failed startup manifests,
the failed greedy attempt, successful smoke outputs, and final inference log.
`review/` contains separate editable CSVs, verification.json and Argilla links.
Weights are not copied or committed; the exact public checkpoint is pinned.

## Human review

- [Train: 80 records](http://127.0.0.1:6900/dataset/6e0e8b05-c083-4945-815b-d38b372d5cb5/annotation-mode?page=1&status=pending)
- [Validation: 20 records](http://127.0.0.1:6900/dataset/6be3e4a7-a5c0-4ab0-9b05-ea56ae3b2566/annotation-mode?page=1&status=pending)

Both datasets were retrieved through the Argilla API and their record counts
checked after import. Preserve original drafts; accept unchanged, provide a
complete replacement, or reject. Correct factual and Turkish errors before
shortening. Retain useful wording where possible, but do not preserve incorrect
content merely to minimize edit distance. Validation edits are evaluation
references only, never training data. These are unapproved drafts, not gold
answers; natural stopping is not a quality score.

Next: user review, export approved targets, recheck leakage/identity, design and
verify training/masking, then explicitly authorized training and comparable
base/adapter evaluation. No training has been started automatically.
