# Environment & Pod Setup Gotchas

Concrete mistakes hit while standing up the CETVEL/vLLM environments on
RunPod, kept here so they aren't silently repeated on the next fresh pod.
Read this before re-running any `setup_*.sh` script on a new pod, or before
debugging a setup script that "used to work."

## 1. Windows git checkout silently reintroduces CRLF

Even with `.gitattributes` set to `* text=auto eol=lf`, files checked out on
this Windows/Git-Bash setup can still end up with CRLF line endings in the
working tree -- independent of what's actually stored in the git blob. This
is not a one-time fluke: it hit 70+ tracked files across a single session,
including patch files and shell scripts, sometimes from the original commit
and sometimes reintroduced by an ordinary checkout.

**Symptoms this causes on the Linux remote:**
- `bash: line 2: set: pipefail: invalid option name` (a stray `\r` glued
  onto the end of `pipefail`, which bash 5.1+ genuinely supports otherwise).
- `error: corrupt patch at line N` or `patch does not apply` on a `.patch`
  file whose actual diff content is correct -- CRLF corrupts unified-diff
  line matching.

**Cannot fix via `git config`** (core.autocrlf, etc.) -- the standing rule
in this environment is to never modify git config, even scoped to one repo.

**What actually works:** before syncing anything to a remote, or before
trusting a script/patch just edited locally, run:

```bash
for f in $(git ls-files); do
  if [ -f "$f" ] && file "$f" 2>/dev/null | grep -q CRLF; then
    sed -i 's/\r$//' "$f"
  fi
done
```

Then `git add -A && git commit` if `git status` shows the strip produced
real changes (it will for anything that was CRLF in the actual stored blob,
not just the working-tree checkout).

## 2. Patch files are line-count-sensitive -- verify hunk headers by hand

A unified diff hunk header `@@ -X,N +Y,M @@` must exactly match the number
of context+removed lines (N) and context+added lines (M) in the hunk body.
If you hand-edit a `.patch` file (not regenerate it fresh with `git diff`),
it is very easy to get this count wrong by one -- `git apply` then fails
with "corrupt patch," which looks like file corruption but is actually just
wrong header arithmetic.

Before trusting a hand-edited patch: count context lines (` ` prefix) and
add removed (`-`) for the old side, add added (`+`) for the new side, and
confirm both match the header numbers. Same goes for copy/paste transcription
of a real file's content into a new hunk -- verify every context line against
the actual current file content, not memory. (Hit this twice in one session:
once from a genuine off-by-one, once from mistyping `test_split: train`
instead of the file's actual `test_split: test`.)

**After any patch edit, do a fully clean re-test** (wipe the cloned repo,
re-clone, re-apply from scratch) rather than trusting a partially-patched
working tree that was fixed via manual `sed`/`git apply` iteration. Several
bugs in this session were only caught because of this -- an already-mutated
working tree can mask a patch that doesn't actually apply cleanly on its own.

## 3. Setup scripts must create a real venv under `/workspace`, not rely on ambient Python

`/workspace` (or whatever the pod's persistent volume is) is the *only*
thing that survives a container restart. If a setup script runs
`pip install` without first creating and activating
`python3 -m venv /workspace/.venvs/<name>`, everything installs into the
container's system Python -- which works fine right up until the next
restart, silently wipes the whole environment, and looks like it "used to
work" for no reason.

**Red flag to watch for:** `WARNING: Running pip as the 'root' user...` --
if you see this during what's supposed to be an isolated-venv setup, the
venv was never actually created/activated.

## 4. Redirect `HF_HOME` (and ideally pip's cache) to `/workspace` too

Same failure class as #3, one level deeper: even with a correct persistent
venv, `transformers`/`datasets` will default to caching models and datasets
under `~/.cache/huggingface`, which lives on the container's small,
ephemeral root filesystem (observed: 20GB total) -- not the large,
persistent `/workspace` volume. This **actually happened**: HF cache
(9.6GB) + pip cache (2.4GB) filled the root disk mid-setup with
`/workspace` sitting at 1% usage the entire time, and the setup script
failed with `OSError: [Errno 28] No space left on device`.

Every script that can trigger a model or dataset download must set:

```bash
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
```

before any `python`/`lm_eval`/`transformers` invocation. Check for this
explicitly when writing or reviewing a new setup/run script -- it's easy to
forget since everything works fine on a pod that hasn't filled up yet.

## 5. CETVEL's pinned task configs reference several HF datasets by bare (non-namespaced) repo IDs

The installed `huggingface_hub` version enforces `namespace/name` for
dataset repo ids and rejects a bare name with
`Repository id must be 'namespace/name', got '<name>'`. CETVEL's pinned
revision predates this enforcement, so several of its task YAMLs still use
the old bare-name convention. Found and fixed so far (see
`patches/cetvel-canonical-dataset-ids.patch` and
`patches/cetvel-harness-canonical-dataset-ids.patch`):

| Bare name | Canonical fix |
|---|---|
| `exams` | `mhardalov/exams` |
| `nli_tr` (mnli_tr.yaml, snli_tr.yaml) | `boun-tabi/nli_tr` |
| `xnli` (nli_tr/xnli_tr.yaml **and** the harness's own built-in `xnli/xnli_common_yaml`) | `facebook/xnli` |
| `mlsum` | `reciTAL/mlsum` |
| `offenseval2020_tr` | `coltekin/offenseval2020_tr` |
| `wmt16` (all 4 files under `tasks/wmt2016/`) | `wmt/wmt16` |
| `xcopa` (`tasks/xcopa/default_et.yaml`, inherited by `default_tr.yaml`) | `cambridgeltl/xcopa` |

**Non-obvious trap:** `lm-evaluation-harness` ships its own built-in
`xnli`/`xnli_tr` task that shares a task *name* with CETVEL's custom
`nli_tr`/`xnli_tr` task. The built-in one (with the stale bare path) is
what actually resolves when the `nli_tr` group is evaluated -- fixing only
CETVEL's own `tasks/nli_tr/xnli_tr.yaml` was not enough.

**If a new task hits this same error:** don't fix it one at a time --
`grep -rn '^dataset_path:' <cetvel_dir>/tasks/ | grep -vP 'dataset_path: \S+/\S+'`
(bare names, no `/`) across every task config first, since this bug tends
to cluster (found 8 instances total across one sweep, several only surfaced
after fixing the first one and moving further into the task list).

## 6. RunPod restarts reassign the public IP/port; SSH keys need to land inside the container

- A pod restart (e.g. after a volume resize) gets a new public IP and/or
  port -- don't assume a previous SSH connection string still works.
- Adding a key to RunPod's account-level SSH settings does **not**
  retroactively inject it into an already-running pod; either restart the
  pod after adding it, or append directly via the pod's own web
  console/terminal: `echo "<pubkey>" >> ~/.ssh/authorized_keys`.
- A pod's persistent volume can also come back **completely empty** on a
  fresh pod allocation (not just a restart of the same pod) -- don't assume
  `/workspace` from a previous session is still there. Check
  (`ls /workspace`) before assuming any prior setup (venvs, caches, synced
  repo) survived; if empty, everything needs to be rebuilt from scratch.

## 7. vLLM nightly wheels can require a newer CUDA driver than the pod has -- and `--torch-backend=auto`/explicit backend selection does not fix it

`uv pip install vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly`
resolved `torch==2.13.0+cu129` plus a vLLM-built C extension
(`vllm._C_stable_libtorch`) that dynamically links `libcudart.so.13` --
**a CUDA 13 runtime**, independent of which CUDA version torch itself was
built against. This extension is a prebuilt binary baked into the vLLM wheel
at CI build time, not something `--torch-backend` controls.

**Symptom:** vLLM installs and even `import vllm` succeeds (the import
itself doesn't touch the GPU), but the server crashes on model load with:

```
RuntimeError: get_cuda_view_from_cpu_tensor, .../cuda_view.cu:38,
cudaHostGetDevicePointer failed: CUDA driver version is insufficient for
CUDA runtime version
```

Check `nvidia-smi`'s reported `CUDA Version:` (its max-supported CUDA, based
on the installed driver) against what the *vLLM build* actually links, not
just what `torch.version.cuda` reports -- torch's own cu129 libs may be
forward-compatible while vLLM's separately-built extension is not.
`find / -name 'libcudart.so*'` and `ldd` on
`vllm/_C_stable_libtorch*.so` shows which CUDA major version it actually
needs.

**Things that do NOT fix this:**
- Adding the missing `libcudart.so.13`'s directory to `LD_LIBRARY_PATH`
  fixes `import vllm` (a separate, real bug -- see below) but does not fix
  this error, since the library loads fine, it's the *driver* that's too
  old for what the library requires.
- `uv pip install --reinstall-package torch ... --torch-backend=cu124` fails
  outright: `torch==2.13.0` (the version this vLLM release pins) simply has
  no cu124/cu121/cu128 build on PyPI's torch index, only cu129 -- there is no
  "pick an older CUDA torch" escape hatch once vLLM has pinned a torch
  version that only ships for newer CUDA.
- The `nightly` alias on `wheels.vllm.ai` always resolves to the single
  latest commit -- there is no index of older nightly builds to fall back to
  through the normal `--extra-index-url` mechanism. (In principle a specific
  older commit's wheel can be fetched directly if you know its exact
  post-tag version string and full commit SHA, but this could not be
  resolved without a working listing endpoint and was not pursued further --
  don't sink time into bisecting commits under time pressure.)

**What actually worked:** skip vLLM entirely for this pod/driver
combination and fall back to `transformers`-based direct generation instead.
Check first whether the installed `transformers` version recognizes the
target model's architecture natively (`AutoConfig.from_pretrained(...)` --
for Qwen3.5 this showed up as `Qwen3_5ForConditionalGeneration` in
`transformers==5.17.0`, so no custom modeling code was needed). This is
slower (no continuous batching / paged attention) but produces identical
outputs given greedy decoding, and this project's protocol already ran at
concurrency=1 regardless of backend, so there is no speed loss from
batching to give up. See `scripts/evaluation/evaluate_cetvel_generation_transformers.py`.

**Separate, real, and independently worth fixing:** even when the driver
*does* support CUDA 13, `import vllm` on this vLLM build fails with
`ImportError: libcudart.so.13: cannot open shared object file` because the
`nvidia-cu13` wheel that ships `libcudart.so.13` lands in site-packages but
its `lib/` dir is never added to the dynamic linker search path. Fix:

```bash
export LD_LIBRARY_PATH="<venv>/lib/python3.11/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}"
```

(persist this into the venv's `bin/activate` so it survives every future
`source .../activate`, not just the current shell).

## 8. `mcemilg/tquad` (and possibly other community dataset repos) needs `trust_remote_code=True`

`load_dataset("mcemilg/tquad", ...)` fails with `ValueError: The repository
... contains custom code which must be executed to correctly load the
dataset` unless `trust_remote_code=True` is passed explicitly -- this
repo ships a loading script rather than plain data files. Unlike the bare
dataset-ID issue (#5), this isn't fixable by changing the path; it's a
property of that specific repo. Cost this session a full task's worth of
model-load time when it surfaced mid-run after `gecturk` had already
finished -- check every `load_dataset()` call added for a new task against
this before a long run, not after.

## 9. Do not let current Unsloth resolve a CUDA 13 Torch stack on a CUDA 12.8 driver

On the `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` image,
the system stack is `torch==2.4.1+cu124` while the RTX 4090 driver reports a
maximum CUDA version of 12.8. A plain `pip install --upgrade unsloth
unsloth_zoo ...` attempted to replace this with `torch==2.12.1`, CUDA 13
libraries, and matching xFormers. That would recreate the driver/runtime
incompatibility documented above for vLLM.

Before downloading a model or running GPU code, create the persistent venv
with `--system-site-packages`, do not use unconstrained `--upgrade`, and
confirm `torch==2.4.1+cu124`, `torch.version.cuda == "12.4"`, and
`torch.cuda.is_available()`.

## 10. Newest `torchao` is incompatible with the CUDA-12.4 Torch 2.4 path

`torchao==0.18.0` imports `torch.int1`, absent from `torch==2.4.1+cu124`.
Unsloth then fails at import time with `UnslothTorchTooOldError`, before a
model is loaded. Pin `torchao==0.5.0` for this pod path and repeat an actual
`import unsloth` test. A successful pip install alone is not evidence that
the environment works.

## 11. Unsloth must be imported before `trl` in the same file/module

`from trl import SFTConfig, SFTTrainer` followed later by
`from unsloth import FastLanguageModel` (wrong order) silently breaks any
`SFTConfig` kwarg that Unsloth's patch relies on, e.g. `eos_token`. Unsloth
patches `trl.trainer.sft_trainer.SFTConfig`/`SFTTrainer` at import time. If
`trl` is imported first, local names bind to the *pre-patch* classes; when
`SFTTrainer(args=trainer_args)` later runs, its `isinstance(args, SFTConfig)`
check compares against the *post-patch* class, fails, and silently rebuilds
`args` via `args.to_dict()` -- which drops fields like `eos_token`, resetting
it to Unsloth's internal placeholder default (`'<EOS_TOKEN>'`, not in the
tokenizer vocabulary). This produced a `ValueError: The specified eos_token
('<EOS_TOKEN>') is not found in the vocabulary...` that looked like a
tokenizer/model bug but was purely an import-order bug -- confirmed by
comparing `id(trainer_args)` (what we built) against `id(args)` (what
`SFTTrainer.__init__` actually received): different objects. Unsloth's own
runtime warning states this exact requirement ("Unsloth should be imported
before [trl, transformers, peft]") -- treat it as load-bearing, not
cosmetic.

## 12. This Unsloth version's patched `SFTTrainer._prepare_dataset` does not support the `messages` conversational format

Vanilla TRL 0.24's `SFTTrainer` accepts a dataset with a `messages` column
(list of `{"role", "content"}` dicts) and does its own chat-template
rendering + assistant-turn boundary detection, which `assistant_only_loss`
needs. Unsloth's patched trainer (`/tmp/unsloth_compiled_cache/
UnslothSFTTrainer.py`, `_prepare_dataset`) only recognizes `input_ids`,
`labels`, `prompt`+`completion`, or a pre-rendered `dataset_text_field`
(default `"text"`) column; anything else raises `RuntimeError: Unsloth: You
must specify a formatting_func`. Passing a `formatting_func` that returns a
flat string would bypass TRL's own assistant-only masking logic entirely,
which is not equivalent to a correctness no-op -- it would silently mask
loss differently than intended. **Not yet resolved.** Options to evaluate
next: (a) check the installed `trl`/`unsloth` versions for a documented
combination that does support conversational `assistant_only_loss` under
Unsloth's patch, (b) render to `text` ourselves and implement assistant-only
masking by hand (locate the last `<|im_start|>assistant\n` span per example
and set labels before it to -100), verified against
`label-mask-inspection.json`, or (c) pin an Unsloth version whose patched
trainer supports the conversational path. Do not proceed to `--mode smoke`
until one of these is chosen and the representation-check passes with
`label-mask-inspection.json` showing correct assistant-only spans (not "all
tokens are labels" or "all tokens are masked").

## 13. Fresh-pod setup gate order

```text
persistent venv + persistent HF/pip caches
    -> Torch/CUDA availability check
    -> import Unsloth check
    -> import TRL/Transformers/W&B check
    -> tiny local template check
    -> only then download Qwen3.5 weights
```

Preserve failed resolver attempts and final versions in the experiment
environment artifact: setup failures are reproducibility evidence.

## 14. Vast.ai first-boot and SSH environment behavior

The `vastai/pytorch:cuda-12.4.1-auto` image was about 9 GB compressed but took
15 minutes to become SSH-ready on one verified Denmark RTX 4090 host and 45
minutes on a Bulgaria host. Daemon logs showed that network downloads had
completed while Docker was still extracting large layers; advertised network
speed therefore did not predict boot time. Prefer hosts with high disk
bandwidth, impose a time limit on loading, and destroy rather than merely stop
an abandoned instance because storage billing continues while it exists.

On the tested 2026-09-26 image, the name `vastai/pytorch` did not mean that
PyTorch was installed: system Python was 3.12 and `import torch` failed. The
reportable environment was instead recreated under `/workspace` with uv-managed
Python 3.11 and `/workspace/.venvs/qwen-fast`, then pinned to the previously
validated Torch 2.7.1+cu128 / Triton 3.3.1 / Unsloth 2026.9.6 stack.

Vast template environment variables are visible to the on-start script but are
not all inherited by later SSH sessions. In this run only `DATA_DIRECTORY` and
`LANG` survived. Export `HF_HOME`, `PIP_CACHE_DIR`, `WANDB_DIR`, and related
cache variables explicitly for every non-interactive SSH command, or write
non-secret values to `/etc/environment` and verify them in a fresh SSH session.

When invoking Linux commands through Windows PowerShell and `ssh`, unescaped
remote shell variables such as `$UV` and command substitutions such as `$(...)`
may be expanded or corrupted by the local shell before reaching the pod. For
automation, prefer literal absolute remote paths and simple commands; test
quoting with a read-only probe before starting a long installation or run.

Finally, add each experiment's generated `results/` directory to `.gitignore`
before producing the required pre-training base output. Otherwise the
subsequent representation check correctly refuses to run from the newly dirty
worktree even though the only untracked file is the base result.

Unsloth 2026.9.6 may also create `unsloth_compiled_cache/` in the current
working directory during import. Keep that generated directory outside Git (or
ignore it explicitly) before enforcing the clean-worktree training gate.
