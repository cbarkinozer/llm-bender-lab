# Occam Q4_K_M GGUF export — 2026-10-26

The owner requested a merged, quantized GGUF in the existing Hugging Face model
repository `cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora`. This is an export of the
selected F adapter, not new training or a new experimental claim. Existing adapter
weights, license, historical results and repository visibility are preserved.

## Sources and procedure

- Base/tokenizer: `unsloth/Qwen3.5-4B` at
  `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`.
- Adapter: `cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora` at
  `1a8a07ff2a29f51a2b6a635a8c219191a7377996`.
- BF16 merge with PEFT, after verifying published source hashes. Native BF16
  weights are the input, not the existing 4-bit MLX/GGUF preset.
- llama.cpp converter / Homebrew quantizer commit:
  `7fe450e19305b828c199d602c23a8337aaa1f03b` (build 11146).
- Text-only BF16 GGUF, then `Q4_K_M` mixed quantization. No vision projector,
  attachment support, training data or private mail is included.
- Preserve original tokenizer/template files. Validate EOS handling in the actual
  Ghost-box runtime instead of changing the application's global EOS policy.

Weights, temporary exports, dependency environment, command logs and receipts live
outside Git in `~/Documents/llm-bender-artifacts/occam-gguf-20261026`.
The resolved preparation environment is saved there as `requirements.lock.txt`.
No Ghost-box or lab application dependencies are changed.

## MTP compatibility finding

The pinned base contains 32 decoder layers plus optional speculative MTP tensors.
The Transformers inference class used for PEFT merging omits those 15 unused MTP
tensors, while its saved config still declares one MTP layer. A default conversion
therefore advertised 33 layers but contained 32, and the runtime correctly rejected
it. Export explicitly with `--no-mtp` to omit speculative-layer metadata/tensors.
This does not remove a trained main decoder layer or change ordinary generation.
The first candidate and logs are preserved under the external `failed-mtp/` folder;
it was never uploaded. The corrected artifact must pass actual deployment checks.

## Scripts

Use Python 3.11+ (`hashlib.file_digest` is required) and the preparation environment
recorded in `WORK/requirements.lock.txt`. Upload/preflight tests require
`python-dotenv` and `huggingface-hub`; merging also requires the recorded model
dependencies. Run the offline preflight tests from the repository root with:

```sh
PREPARATION_PYTHON -m unittest discover -s docs/publication -p test_gguf_export.py -v
```

`export_occam_gguf.py --work WORK` verifies adapter hashes, loads the pinned local
base and adapter, performs one pre/post-merge last-logit sanity check, merges with
`safe_merge=True`, preserves tokenizer files and hashes the merged checkpoint.
The one-prompt numerical check is not a general equivalence evaluation.

Convert and quantize with the pinned llama.cpp source/binary:

```sh
PREPARATION_PYTHON export_occam_gguf.py --work WORK
PREPARATION_PYTHON LLAMA_CPP/convert_hf_to_gguf.py WORK/merged \
  --outtype bf16 --no-mtp --model-name 'Occam Qwen3.5 4B Turkish Concise' \
  --outfile WORK/occam-bf16.gguf
llama-quantize WORK/occam-bf16.gguf \
  WORK/Qwen3.5-4B-Turkish-Concise-Q4_K_M.gguf Q4_K_M 4
```

`validate_occam_gguf.py --work WORK --app-root GHOST_BOX` runs six synthetic
samples through Ghost-box's actual `GGUFBackend`: uncertainty, invoice facts,
revised deadline, malicious source instructions and Turkish/English email drafts.
Record natural termination, output, timing, runtime counters and peak RAM. Inspect
answers for obvious failures. These are deployment smoke samples, not a full
accuracy benchmark; the original adapter's summarization limitations remain.
Native Windows validation and the separate 20-question email benchmark remain pending.

`upload_occam_gguf.py --work WORK` is an external write, authorized for this export.
It reads `HF_API_KEY` directly from the ignored lab `.env` without printing it.
Only four exact staged files may be uploaded: GGUF, export manifest, GGUF usage
document and updated model card. It refuses unvalidated weights, hash mismatch,
unexpected files, changed remote parent/visibility and blind repeat uploads.
No directory-wide workspace upload or visibility mutation is performed.
After commit, verify GGUF against Hub LFS SHA256/size and re-download/hash the
three small files. This is not a second full download of the GGUF. Preserve the
commit receipt locally even if post-upload verification fails.

## Status

Published and verified: [GGUF release](https://huggingface.co/cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora/commit/52d34aa4b74ed0241e67a103be3413c0a34373f5).
The 2,708,804,224-byte artifact has SHA-256
`e640ec52d141138a1ee568421c821a9308eb5cdbb94112f3d3f2f77418069857`.
Remote LFS hash/size and downloaded small-file hashes match the release.
Original adapter weights and public visibility were preserved.

Six native deployment samples terminated successfully; semantic review found draft
errors. The 20-question synthetic benchmark ran twice (40 executions), with factual
errors including dates and ambiguous sender selection. Runtime success is not accuracy.
Three paired BF16 cases were also run twice: both variants failed one year question,
and Q4 changed November to April in two cases where BF16 preserved November.
Search routes may differ, so these samples do not isolate quantization causally.
Full synthetic inputs, actual outputs, settings and limitations are in the public
manifest/report. Human accuracy scoring is pending; Windows was not tested.

Local readable review: `WORK/benchmarks/occam-20-review.md`.
Receipts: `WORK/gguf-upload-receipt.json` and `WORK/gguf-evidence-receipt.json`.
