# Eval v2 GPU runbook (baselines for base, CPT, exp014, exp015)

Prepared 2026-11-21 on CPU. Nothing here has run on a GPU yet. Expected total: under 2 hours on one RTX 4090
(about $1), no training. Read `docs/environment-setup-gotchas.md` first (sections 7 and the vLLM notes).

## Pod requirements

- RTX 4090 24 GB, Python 3.12 available, 60 GB free disk, persistent `/workspace`.
- **NVIDIA driver with CUDA 13.0 or newer** (`nvidia-smi` header). The pinned vLLM wheel needs it and
  `setup_lfm3_stage_diagnostic.sh` asserts it. If the pod has an older driver, stop and pick another offer; do not
  search for other wheels on the pod (gotchas section 7).
- SSH key already registered in Vast (default `~/.ssh/id_ed25519_lfm3_bilingual`, override with `LFM3_POD_KEY`).
- Hugging Face access: the base model and the CPT adapter are public; no token is needed on the pod.

## Steps (from the local repo; set `LFM3_POD_HOST` and `LFM3_POD_PORT` first)

```text
python scripts/training/eval_v2_pod.py sync                       # scripts, eval-v2 packets, 2 adapters (about 190 MB)
python scripts/training/eval_v2_pod.py shell --command "cd /workspace/lfm3-evalv2/repo && bash scripts/training/setup_lfm3_stage_diagnostic.sh"
python scripts/training/eval_v2_pod.py shell --command "cd /workspace/lfm3-evalv2/repo && bash scripts/evaluation/run_lfm3_eval_v2_session.sh smoke"
```

Stop after the smoke and read its output. Gates before the full run:

1. Tool-call rows for the base model parse (`fmt` is `xml` or `json`, `errors` lacks a dominant `no_tool_call` or
   `parse_error`). If the model emits another format, add a parser to `lfm3_eval_v2_scoring.py`, rebuild nothing
   else, and rerun the smoke.
2. Thinking-on runs show a high `thinking_closure_rate` and few `hit_max` rows; thinking-off rows end with `eos`.
3. Symbolic thinking-off for the base model is near 100% (our earlier 8/8) and the answer is the bare number.
4. Merges report `reload_exact` true. `matches_expected` for the CPT merge compares against the historical weight
   hash; a mismatch is recorded, not fatal (BF16 bytes can change with the torch version).

```text
python scripts/training/eval_v2_pod.py shell --command "cd /workspace/lfm3-evalv2/repo && bash scripts/evaluation/run_lfm3_eval_v2_session.sh merge"
python scripts/training/eval_v2_pod.py shell --command "cd /workspace/lfm3-evalv2/repo && bash scripts/evaluation/run_lfm3_eval_v2_session.sh baselines"
python scripts/training/eval_v2_pod.py download                   # checksummed tarball into eval-v2/runs-local/
```

Run long steps with `nohup ... &` plus a log tail if the SSH session is unreliable; the driver is idempotent and skips
finished runs. After `download` verifies, the pod can be stopped.

## What comes back

`runs-local/runs/<model>-think-<on|off>/` with `run-manifest.json`, raw `answers-seed3407.jsonl`, per-item
`scores-seed3407.jsonl`, `summary.json`; `merge-receipts/`, and `logs/`. No weights. Then compare locally:

```text
python scripts/evaluation/score_lfm3_eval_v2.py compare --base runs-local/runs/base-think-off --candidate runs-local/runs/exp014-think-off
```

## Stop and report instead of continuing if

- the smoke shows a runner or vLLM error (preserve the log; do not change versions on the pod),
- the base model fails gate 3 (the scorer or prompt is wrong, not the model; inspect raw outputs first),
- any packet checksum mismatch appears.
