# Execution order and GPU preparation — 2026-11-20

User explicitly confirmed that model-card benchmarks come before candidate training.

1. Reproduce MATH-500, GSM8K and IFEval on untouched WSP and the pinned original Qwen parent, using upstream think35 protocol: thinking on, temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5, 32768 generated tokens, seed 0. Upstream sample counts: MATH-500 4, GSM8K 2, IFEval 2. Preserve strict graders and termination statistics.
2. Train a fresh Reflex-1.5 candidate with WSP backbone and recovered Reflex data/recipe, following smoke and tiny-overfit gates. Train the matched original-base control.
3. Run candidate inference and compare decision routing with released Reflex-1 and matched control. Also measure generative benchmark retention where the trained artifact supports generation; distinguish backbone generation from decision-head inference.

Remote GPU confirmed RTX 4090, 24 GB, idle at connection. Work root /workspace/reflex-wsp; separate persistent environments /workspace/.venvs/reflex-wsp and /workspace/.venvs/reflex-eval. Credentials and keys are not recorded here.

Upstream evaluation repository cloned at 4d09ba6d6a7e891dd8063974dfe81b3d78e3494f. Its evaluate.py references unavailable weightenv modules and a placeholder data root; these need explicit adaptation with preserved protocol. The local mathqa.py is present, but IFEval checker dependencies still need recovery.

Initial training dependency resolution failed: pinned Unsloth zoo metadata excludes datasets 5.1.0 even though the recovered environment used that version. Initial setup log retained. A second install preserves the recovered explicit versions and installs pinned Unsloth packages without dependency resolution; imports and missing dependencies must be checked before use. Evaluation environment targets card versions vLLM 0.33.0, transformers 5.20.2 and math-verify 0.9.0.

Status: setup in progress; no model benchmark or training has started. This record is not a successful-run manifest.

## Verified progress

Both environments import successfully. All recovered dataset hashes match on the remote. The original weighted_mix function yields exactly 1,562 ordered rows with SHA-256 67a39340be87f2b2cf5a7a0c5407795bd5e6a0bf598ac1ce27677cdb1b629867 (781 phone, 391 typed-decisions, 195 BANKING77, 195 CLINC150).

All 488 tensor keys/values in the pinned original Unsloth training snapshot match the official Qwen parent. WSP differs in exactly layers 15 and 19 down_proj with advertised hashes. BF16 rounding means 130,188 values actually differ; the advertised 131,072 edited positions need not all change their stored value. Tokenizer/config parity remains to audit before training.

All 541 IFEval records can be constructed and graded with the pinned official Google code at c878a53ec1764bcb91a6178dc5c315202a3b5fa2. Benchmark dataset revisions and serialized hashes are in preflight/benchmark-manifest.json. IFEval's dataset split is named train by its publisher but is used exclusively for evaluation here.

WSP generation smoke passed: boxed answer 4, 221 generated tokens, normal stop, closed thinking block. The smoke cap is 256 and is diagnostic only; reported benchmark runs keep 32,768. vLLM initialized the full 34,816-token context and BF16 model on the RTX 4090. First-use CUDA/FlashInfer compilation takes several minutes.

The locked remote run_card_suite.sh queue has been launched, beginning with the original parent smoke and then WSP/parent model-card evaluations serially. Inspect suite-stage.txt, logs/card-suite.log, logs/card-wsp.log and logs/card-parent.log for live state. Benchmark outputs live in eval/card/<arm>, with atomic compressed batches and cumulative summaries. Counts per arm: 2,000 MATH-500, 2,638 GSM8K and 1,082 IFEval samples. Partial summaries are not final results.

Adaptations from the author's runner: explicit data root and local mathqa loading; unavailable unused mcqa loop-detector import raises if invoked; official Google IFEval module path; 32-problem resumable batches with max_num_seqs=128; every generated sample retained. These scheduling changes are matched across arms and mean this is a close protocol replication rather than identical author-hardware random draws.

Training has not started. Remaining gates include tokenizer/config parity, training smoke and reload, tiny overfit, and final frozen routing cohort/evaluator recovery. The training dependency metadata still conflicts with recovered datasets 5.1.0 and declares optional torchao absent from the recovered environment; do not treat imports alone as a training gate. Missing small dependencies were installed and the actual freeze is preserved. The FastDecisionModel plain-LM loader initializes its fresh head within a seed-3407 torch RNG context, confirmed in pinned source.
## Training metadata resolution

The tokenizer audit found identical vocabulary but different special-token metadata and chat template between the original Unsloth snapshot and official/WSP snapshots. WSP and official parent metadata match each other. An isolated symlink training view now pairs unmodified WSP safetensors with the recovered original Unsloth non-weight files. Both training arms therefore use the recovered metadata; untouched generation evaluation continues using each published snapshot. No downloaded snapshot was changed. The per-file training-view manifest records sources and hashes.

The pinned DecisionTrainer default head learning rate is 1e-4, separate from backbone LoRA LR 2e-4. Its fresh-head initialization is seeded. Confirm emitted LoRA targets and optimizer groups in the training smoke rather than inferring them from names alone. Also measure whether the WSP deltas survive the original 4-bit loading; BF16 generation success does not establish their retention under quantization.

The parent smoke also passed engine execution (256-token diagnostic cap); it reached the cap, so it is not a normal-stop/correctness success. The suite has advanced to the WSP model-card benchmark stage. Full parent benchmarks are queued afterwards.