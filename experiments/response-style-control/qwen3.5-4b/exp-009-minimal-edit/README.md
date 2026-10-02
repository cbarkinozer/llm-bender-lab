# exp-009-minimal-edit

## Status

Local training preparation completed: see [TRAINING-HANDOFF.md](TRAINING-HANDOFF.md)
and training-preflight-v1/report.json. Pinned tokenizer/masks and 80/20 separation
verified, zero truncations. Initial 2-epoch, LR 5e-5 LoRA recipe prepared.
GPU runner integration/smoke/reload/tiny-overfit/W&B checks remain pending;
no GPU training started.

2026-10-02 review update: all 100 records submitted and exported to `reviewed-v1/`.
User subsequently authorized direct scoped QA fixes (no Argilla UI): active
corrected targets are in `reviewed-v2/`, 9 train fixes and 1 validation-reference
fix; remaining 90 answers unchanged. Original annotations and reviewed-v1 remain
untouched. See reviewed-v2/REVIEW.md for the change log. Training has not begun.
See [REVIEW-QA.md](REVIEW-QA.md): targeted corrections still need approval before
training preparation. Original drafts/annotations preserved; me-088 wording
change exists only in the new exported version. Historical status below predates
human review.

Base generation completed. **Active prompt selection v2: 100 rows, 80 train / 20 validation**.
V1 is retained unchanged as history. See [coverage-v2.md](coverage-v2.md) for
the full behavior mapping, similar-word priorities, new character contrasts,
multi-turn clarification resolution, provenance changes and refreshed overlap audit.
vLLM generated and verified 100 naturally stopped answers with the user-approved
repetition penalty 1.05. Separate 80-row train and 20-row validation queues are
in Argilla. No human answer editing or training has started. Historical assistant
targets are excluded. See [BASE-RUN-REPORT.md](BASE-RUN-REPORT.md).

## Goal and hypothesis

Start a new phase from the unadapted Qwen3.5-4B, not any historical adapter.
Use the model's own answers as drafts, then minimally edit training answers to
make them direct, concise, grounded, and non-anthropomorphic while preserving
natural Turkish and useful substance. This may reduce disruptive style mismatch;
it does not guarantee probability preservation or absence of forgetting.

The user explicitly chose reuse of historical prompts for both splits. Novelty
against old adapters is not required, and this dataset must not later be claimed
to be unseen by those adapters. V2 has 91 verbatim historical prompts, five
disclosed transformations and four disclosed new prompts, never benchmark
sources. Broad behavior requirements are in
[`../next-dataset-spec.md`](../next-dataset-spec.md).

## Curated coverage (same family counts in v1 and v2)

| Family | Train | Validation |
| --- | ---: | ---: |
| Grammar correction | 8 | 2 |
| Source-bound answer extraction | 8 | 2 |
| Numeric/entity precision | 8 | 2 |
| Faithful summarization | 8 | 2 |
| Useful explanation | 8 | 2 |
| Selective clarification | 8 | 2 |
| Grounded completion | 8 | 2 |
| Turkish lexical/semantic precision | 8 | 2 |
| Non-anthropomorphic interaction | 8 | 2 |
| Consistency and semantic integrity | 8 | 2 |
| Total | 80 | 20 |

The even allocation is an explicit initial coverage decision, not a claim about
deployment frequencies. Subtypes vary inside each family. It is a hand-curated
selection, not proof that these are objectively the best 100 available prompts.

Historical v1: 45 rows come from the original 2,442-row reviewed-v3 pool, 10 from the 958-row
exp-006 artifact, and 45 from the corrected 100-row exp-008 artifact. These pools
overlap historically; their sizes must not be added to claim a unique pool size.
Original source IDs, category, source file, exact prompt hash, expected response
mode, scenario group, subtype, and evaluation criteria are retained per row.
Prompt wording is unchanged, including intentionally erroneous correction inputs.

## Active v2 files

- [`data-v2/prompts-100.csv`](data-v2/prompts-100.csv): 100 active prompts, actual messages and provenance.
- [`data-v2/train-prompts-80.csv`](data-v2/train-prompts-80.csv): future training-answer edit pool.
- [`data-v2/validation-prompts-20.csv`](data-v2/validation-prompts-20.csv): held-out development pool.
- `data-v2/coverage-map.json`: every requirement linked to train/validation IDs.
- `data-v2/selection-manifest.json`, `overlap-report.json`, `audit-report.json`: hashes and audited split.
- [`generation-config.json`](generation-config.json), [`generate_base.py`](generate_base.py): pinned GPU generation preparation.

V2 has 91 entirely historical/verbatim prompts, 5 historical transformations
(2 format instructions and 3 conversations with authored context), and 4 disclosed
new prompts. It has 97 scenario groups; no group spans the split. Historical final
assistant targets are never copied. Prior assistant clarification turns are input
context only, requiring final-response-only loss masking in future training.

## Historical v1 files (not the active generation input)

- [`data/prompts-100.csv`](data/prompts-100.csv): all selected prompts and metadata.
- [`data/train-prompts-80.csv`](data/train-prompts-80.csv): future answer-editing pool.
- [`data/validation-prompts-20.csv`](data/validation-prompts-20.csv): held-out development pool.
- Matching JSONL files contain user-only semantic `messages`, with no assistant targets.
- `data/selection-manifest.json`: source hashes, artifact hashes, counts, and provenance.
- `data/overlap-report.json` and `data/audit-report.json`: automated overlap/identity evidence.
- [`manual-audit.md`](manual-audit.md): curation resolutions, semantic review and limitations.

The split is an explicit scenario-aware assignment, not random sampling. No split
seed applies. There are 99 declared scenario groups: two product-action matching
examples share a conservative group and are both validation. Every category has
8 training and 2 validation rows; no group spans both sides.

Reproduce locally from the repository root with standard-library Python:

```powershell
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/build_selection.py
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/audit_selection.py
```

Builders refuse to overwrite differing frozen artifacts. A future prompt or
split change requires a new version and new audit, not removing the freeze marker.
The `--refresh-draft` option was used only for corrections before freezing.

## Historical v1 checks

- 100 distinct normalized prompts; 80/20 exact split.
- 1,600 train/validation pairs checked; zero exact overlaps or flagged near pairs
  at sequence similarity >= 0.60 or token Jaccard >= 0.45.
- Zero shared scenario groups or source identities across train and validation.
- One within-training lexical flag reviewed; different tasks share a planning phrase.
- 348 historical project benchmark rows scanned (including duplicated versions):
  zero exact matches and zero near matches at sequence similarity >= 0.78 after
  replacing a flagged favourite-colour prompt.
- Frozen file hashes, exact source prompt binding, and split subset identities verified.
- Zero historical assistant targets copied.

Lexical thresholds are review heuristics, not proof of semantic independence.
The audit covers the listed local project benchmarks, not every external benchmark.
No benchmark output or sealed A/B mapping was opened.

## Later GPU generation and review (active v2)

Use `unsloth/Qwen3.5-4B` and tokenizer revision
`3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`, without an adapter. The prepared
configuration starts at 4,096 new tokens and retries length-limited inputs at
8,192 then 16,384, with a 32,768-token context allowance and no input truncation.
No added system/style instruction, non-thinking mode and greedy decoding are
explicitly recorded. Actual native EOS/end-of-turn IDs are discovered and saved
on GPU; forced EOS is disabled. Every attempt and stop reason is preserved.
Keep the same prompt policy/settings across both splits. Preserve complete raw
drafts, termination status, token counts, model/template identities and run metadata.
A generous limit is not infinite: detect and resolve truncation instead of silently
accepting it. The user subsequently supplied a new Vast.ai GPU and authorized
inference through vLLM, without W&B logging or training. `generate_vllm.py` is
the active generation entrypoint; `generate_base.py` remains historical and
provides shared CPU input validation only.

Review all 100 drafts, keeping the 80 training and 20 validation queues separate.
Validation edits are evaluation references only and must never enter training.
The reviewer
may accept unchanged, minimally edit, or reject. Keep original drafts immutable.
Remove filler and fabricated self-experience; retain correct wording, necessary
explanation, uncertainty, quantities, and Turkish meaning. Fix incorrect content
even when a larger edit is required. No universal answer-length cap applies.

The 20 validation prompts are excluded from gradient updates and training QA.
Score base/candidate generations using the preserved rubrics, with independent
reference approval if validation loss is wanted. Unedited base answers are not
gold targets. This is development validation, not an independent final test.

## Known coverage limits (v2)

This small selection is not an exhaustive capability suite. V2 contains two
train and one validation clarification-resolution conversations, plus explicit
i/ı and circumflex probes. That makes the checks possible, not proof the model
passes them. Near-word distinctions are prioritized over exhaustive character
coverage; systematic coverage of every Turkish contrast is not claimed.
Only two validation questions per family makes per-family estimates very coarse.
No approved training targets, token-length/masking checks, or training configuration
exist yet; these are later gates, not silently satisfied by prompt curation.

## Next step

Human review: edit the separate 80-row training and 20-row evaluation-only
minimal-edit queues. Base drafts and logs have been backed up. No automatic
full-data merge or continuation of an old adapter is planned.

CPU checks from the repository root:

```powershell
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/build_v2.py
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/audit_v2.py
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/test_v2.py
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/generate_base.py --dry-run
```

GPU commands from the repository root in the validated persistent venv:

```bash
python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/generate_vllm.py \
  --repetition-penalty 1.05 --ids me-001,me-021,me-073,me-079,me-081 \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/results/base-v2-smoke

python experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/generate_vllm.py \
  --repetition-penalty 1.05 \
  --output-dir experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/results/base-v2-full
```

Capture stdout/stderr to logs on the host, preserve the code/config snapshot and
download all run artifacts before stopping the instance. Refuse to overwrite
old run directories. The smoke must pass before the full command is launched.
The runner never invokes training or imports uncompleted answers into Argilla.
