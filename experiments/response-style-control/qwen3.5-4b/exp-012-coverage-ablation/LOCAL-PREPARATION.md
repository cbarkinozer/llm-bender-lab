# Local preparation record — 2026-10-03

No GPU contacted, weights downloaded, inference generated or W&B run created.
Existing dataset/annotation history is preserved. Argilla writes are limited to
the newly created exp-012-coverage-candidates-24 queue, 24 records verified against
their draft fields through the API. The annotation URL returned HTTP 200.

CPU environment: Windows, Python 3.12.3 (conda-forge), transformers 4.57.6,
tokenizers 0.22.2, huggingface-hub 0.36.2, Jinja2 3.1.6. No PyTorch in this
tokenizer-only venv. Argilla import used the existing SDK 2.8.0 annotation venv.
This CPU environment is deliberately not claimed to match the GPU training stack;
the GPU runner must reconstruct and compare every saved representation again.

Commands from repository root (PowerShell):

```powershell
& C:\Temp\llm-bender-exp009-preflight\Scripts\python.exe experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation/prepare_pair.py
& C:\Temp\llm-bender-exp009-preflight\Scripts\python.exe experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation/test_preparation.py
& experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.venv/Scripts/python.exe experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation/import_review.py
```

Preparation rerun passed without changing frozen artifacts. Fourteen CPU tests
passed, including controlled training-config differences, retained 56 rows,
validation preservation and missing/rejected/empty/tampered review rejection.
The real read-only export was also attempted before review: correctly failed on
bc-001 with no submitted response; no data-reviewed-v1 or trainable B preflight
was created. This failure is an intentional safety test, not a failed training run.

Local implementation fixes before completion:

- Fixed an unmatched parenthesis in the new builder before it could execute.
- Fixed a new EOS assertion: native template has a masked newline after EOS,
  so check the last supervised label, not the final array element. Existing
  encode_final, data and masking were unchanged; all A representations then
  matched the parent and B validation matched byte-equivalent token records.
- Preserve existing JSON bytes when regenerated content differs only in key order,
  since directory traversal after clone can differ. Real content changes still fail.

No overlap flags at the recorded thresholds; highest candidate-to-validation
lexical similarity was 0.4393 (bc-013/me-079), a shared announcement framing with
different tasks (explicit cancellation cause versus veri/vergi extraction).
Other nearest pairs and complete source hashes are in data-draft-v1/leakage-report.json.
Shared behavior categories are intentional, not proof of scenario leakage.

## Review finalization follow-up

User approved the 24 drafts as-is: "i checked them, they seem fine". Read-only
Argilla inspection found zero submitted responses. A separate conversational
approval record binds the exact candidate hash and IDs; raw snapshot is preserved
without manufacturing annotation responses. The explicit approval-file exporter
rejects wrong hashes, missing IDs and conflicting existing responses. Eighteen
tests passed after adding these checks. Normal export still rejects missing reviews.

The reviewed dataset, config and tokenizer preflight were frozen with:

```powershell
& C:\Temp\llm-bender-exp009-preflight\Scripts\python.exe experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation/export_review.py --approval-file experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation/user-approval.json
& C:\Temp\llm-bender-exp009-preflight\Scripts\python.exe experiments/response-style-control/qwen3.5-4b/exp-012-coverage-ablation/verify_ready.py
```

All 24 answers and prompts remain as proposed. The 56 original rows, original
80-row source and 20 validation rows/tokens are unchanged. B target tokens remain
6,594 per epoch. Active config-reviewed-v1.yaml matches the trainable preflight
config; draft artifacts remain historical and deliberately non-trainable.

Next stop is GPU access and real GPU gates. No additional review required.
Never describe these CPU checks as GPU evidence or completed training.
