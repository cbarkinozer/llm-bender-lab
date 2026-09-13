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
