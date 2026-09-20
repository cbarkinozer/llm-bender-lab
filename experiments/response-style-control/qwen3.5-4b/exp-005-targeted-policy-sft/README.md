# exp-005-targeted-policy-sft

## Status

Dataset frozen after human review. The broad original precision tranche was
replaced by 20 reviewed precision-v2 near-term contrasts. The resulting
858-row artifact passed the development and final-holdout exact-overlap gates.

## Goal and hypothesis

Test whether a small, separately identifiable 60-example policy tranche closes
the three failure modes found after `exp-004` while preserving the behavior of
the 800-example clean-v2 core.

The three targeted categories contain 20 human-reviewed examples each:

- missing-context clarification,
- lexical/entity precision,
- natural non-anthropomorphic responses.

## Parent and main change

Parent: `exp-004-unsloth-sft`.

The only intended experimental change is the training artifact: 58 of the 60
reviewed targeted examples are appended to the same 800-row clean-v2 core,
producing 858 training rows. Two reviewed records are preserved in the review
export but excluded because their prompts exactly match the sealed benchmark.
Training hyperparameters and evaluation must remain unchanged
when the experiment configuration is prepared.

## Dataset artifacts

- `data/targeted-reviewed-60.jsonl`: lossless Argilla review export containing
  candidate and reviewed targets, notes, record IDs, and reviewer IDs.
- `data/sft-clean-v3-targeted-858.csv`: next conversational SFT artifact.
- `data/manifest.json`: counts, hashes, validation results, and provenance
  limitations.

Rebuild while the local Argilla stack is running, after precision-v2 review:

```powershell
& '..\exp-001-sft-dataset\annotation\argilla\.venv\Scripts\python.exe' .\export_and_build.py
& '..\exp-001-sft-dataset\annotation\argilla\.venv\Scripts\python.exe' .\finalize_experiment.py
```

`finalize_experiment.py` refuses to create `config.yaml` unless the rebuilt
dataset manifest is explicitly `frozen-reviewed` and all hashes match. Training
reuses the validated exp-004 entrypoint with the exp-005 config; it starts from
the pinned base model, not from the exp-004 adapter.

## Known limitation

The original broad precision tranche was superseded. Precision-v2 contains 20
distinct, human-reviewed contrasts such as `doktora/doktor`, `öneri/öngörü`,
and `etki/tepki`. Two original non-anthropomorphism records exactly matched the
development benchmark and are preserved in the review export but excluded from
training; the effective targeted distribution is therefore 20/20/18.

The original clarification and non-anthropomorphism source artifacts did not
record their generator model/provider. The manifest preserves this limitation
instead of inferring one.

The clean-v2 manifest's recorded SHA-256 does not match the tracked 800-row
core file's actual bytes. This build records the actual input hash and preserves
the discrepancy in its manifest rather than silently copying the stale value.

## Preflight and run order

Run from a clean committed checkout on the GPU machine. Generate the untouched
base-model output on the new final holdout before training, but do not inspect
or use it to modify this experiment:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/evaluate.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/config.yaml \
  --role base \
  --output experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/results/final-base.jsonl
```

Then run representation, smoke, and stratified tiny-overfit gates:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/config.yaml \
  --mode representation-check \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/results/representation-check

python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/config.yaml \
  --mode smoke \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/results/smoke

python experiments/response-style-control/qwen3.5-4b/exp-004-unsloth-sft/train.py \
  --config experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/config.yaml \
  --mode tiny-overfit \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-005-targeted-policy-sft/results/tiny-overfit
```

Only after all three gates pass, run full training with the smoke and
tiny-overfit evidence paths. Do not continue from the exp-004 adapter.
