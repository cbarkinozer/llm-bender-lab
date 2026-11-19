# Frozen final inference session — 2026-11-18

Candidates are original LiquidAI/LFM3-1.7B, exp-010 checkpoint60 and exp-011
checkpoint69. No training is authorized or performed in this session.

The immutable local freeze is `final-eval-v01-local/freeze.json`, SHA256
`db90380f63eea4a4ccd7b02a5068644bc78f4306cb8bcbbc11c04b09c122686b`.
Input archive SHA256 is
`05aa84b488ac96a17bd39ec3e22f5dd8ac847f7895389fc385c9cf79c4fb3c61`.
All bundled file hashes have been verified locally. No reference files enter
the input archive. It contains only the selected adapters, code, configuration,
prompt packets and provenance needed to restore inference.

The new endpoint was reachable initially: `ssh8.vast.ai:17228`, RTX 4090,
driver 580.126.09, CUDA 13.0. Host verification used accept-new and the existing
instance key; private material stays outside the repository. Python 3.12 and
the pinned vLLM installation were launched under `/workspace`. Subsequent SSH
connections timed out during banner exchange, before authentication. The
adapter transfer was incomplete. The owner then supplied direct endpoint
`1.193.138.121:35176`, which authenticates successfully. Pinned installation
completed and torch reports CUDA available. Bulk SCP/SFTP transfers were slow;
a resumable parallel chunk transfer is in progress, with final archive checksum
required before extraction. Base/CPT downloads are running concurrently.
A detached controller waits for that checksum, prepares verified merges, runs
a separate two-prompt non-test stopping smoke, then runs the frozen final
packet and packages small artifacts. Logs: `/workspace/final-controller.log`;
installation/download logs: `/workspace/setup-logs`. No final generation has
started at this status update. No model weights are downloaded locally.

## Resume after connectivity recovers

1. Check `/workspace/setup-logs/final-inference-install.log`, Python imports,
   available storage and GPU. Preserve failed setup logs.
2. Finish uploading `pod-input.tar.gz`; verify its SHA256 before extracting
   under `/workspace/repos/llm-bender-lab`.
3. Set `HF_HOME=/workspace/.cache/huggingface` and add bundled NVIDIA library
   directories to `LD_LIBRARY_PATH` as in `setup_lfm3_sft160.sh`. Use the pinned
   `/workspace/.venvs/lfm3-vllm/bin/python` for inference and PEFT merges.
4. Run `scripts/evaluation/run_lfm3_bilingual_final.py prepare`. This checks the
   native thinking-disabled prompt tokenization, restores the CPT parent and
   requires its weights to match the historical training-parent hash, then
   merges the two frozen adapters and checks exact save/reload logits.
5. Run a separate non-test generation smoke using an independently authored
   short prompt before launching the final packet. Preserve its logs.
6. Run `scripts/evaluation/run_lfm3_bilingual_final.py run` detached with logs.
   It produces 148 outputs per model, 444 total, retaining raw output, token IDs,
   token counts and termination reasons. Completed model stages are reusable;
   interrupted stages require explicit inspection and must not be overwritten.
7. Run its `package` phase. Download only the small artifact archive, verify
   the archive and every member hash against `backup-manifest.json`, restore
   under the local corresponding paths and retain logs. Do not download merged
   weights. Tell the owner when the pod is safe to close.
8. Locally run `publish_lfm3_bilingual_final_argilla.py`: 35 grouped tasks,
   four directions each, three anonymous candidates, ranking and reasoning
   only. References stay hidden; model identity is consistent within each task
   and randomized across tasks. Do not overwrite existing owner responses.

Analyze answer correctness separately from output language, naturalness,
repetition, length limits and think-tag exposure. Group uncertainty by the 35
underlying tasks rather than counting their translations as independent tasks.
The decision policy remains `BILINGUAL-NEXT-STEPS.md`; no new training should
start before the final comparison and owner discussion.

Download recovery: the pinned base weight was reconstructed from validated HTTP
Range responses and its SHA256 matched Hub metadata
`135922caef64e81e52af88ede8b7c3ddaa9d6da220a9737fb3065275dbfb4330`.
Only the pinned root CPT adapter/config are used for merging. The Hub client
still enumerated archived checkpoints in offline mode from cached repository
metadata, so those files are being cached too to keep frozen code unchanged.
The initial offline-cache failure is preserved in setup logs. After cache verification,
`HF_HUB_OFFLINE=1` keeps preparation and generation on those pinned cached files.
This changes transport only, not candidates, rendering or decoding.

## Verified launch

All merged models passed exact save/reload logits. CPT weight SHA matches
the historical parent. Final archive SHA passed on the remote host.
The two independently authored smoke prompts both terminated with native EOS.
The frozen final run started at approximately 12:37 UTC (15:37 Istanbul).
Controller: `/workspace/final-controller.log`. Candidate logs and incremental
per-item outputs are under `final-eval-v01-local/logs` and `inference`.
No final-test retry, protocol change or training has occurred.

## Completed and backed up

All three candidates completed 148/148 prompts, 444 outputs total; no final
generation retries or overwritten outputs. All answers are nonempty.
The final archive SHA256 is
`ed5b9b01e1d11302f63efc8b9eaed61a6ec6e80422c29b2e3041051d9126f757`
(279,958 bytes); every one of its 45 manifest-listed files passed local hash
verification. Merge receipts, prompt audit, smoke outputs, per-item outputs,
logs and environment are restored locally. The separate controller log is
also downloaded and hashed. Existing LoRAs remain preserved locally; merged
weights were not downloaded. The pod is safe to close.

Blind review: http://127.0.0.1:6900/dataset/f560aa7a-b7a9-486c-9c5e-68236f4e4083/annotation-mode

35 groups, four directions and three anonymous answers per direction.
Only overall ranking and free-text reasoning are required. All 35 uploaded
payloads were read back and verified against local raw outputs. Model keys
and automatic diagnostics remain local under the ignored runtime directory.
No winner is declared before owner review. Use
`scripts/evaluation/export_lfm3_bilingual_final_review.py` after submission.

Automatic diagnostics separate final numeric control answers from strict
value-only formatting, and retain per-direction length, stopping and thinking
tag exposure. The 120 arithmetic/control answers are available locally in
`analysis/arithmetic-review.csv` for adjudication against frozen rubrics.
A numerical match alone does not cover all arithmetic rubrics (for example,
two required values or an explicit comparison). No new training is scheduled.

Owner review completed 2026-11-19: all 35 submissions exported without parsing
failures. See `BILINGUAL-FINAL-REVIEW.md` for decoded results, arithmetic audits
and recommended next steps. No new training or GPU diagnostic started.
