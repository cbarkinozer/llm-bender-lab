# Pod-2 environment setup debug session logs

Raw stdout/stderr logs from every setup/spot-check attempt while standing up
the CETVEL environment on the second pod (`47.47.180.126:17120`, fresh
60GB volume). Kept for the reproducibility record even though most of these
are failures -- each one documents a real bug that was found and fixed, not
noise. See `docs/environment-setup-gotchas.md` for the general lessons and
`protocol-notes.md`'s "Two more harness/CETVEL task-name collisions" section
for the spot-check-specific findings. Exact fix-by-fix detail is in the git
log (search for "CRLF", "canonical dataset-ids", "venv", "HF_HOME").

## Setup attempts (`setup_*.log`)

| File | Outcome |
|---|---|
| `setup_cetvel.log` | Failed -- `set: pipefail: invalid option name` (CRLF corrupting the script itself) |
| `setup_final.log` | Failed -- `error: corrupt patch at line 19` (patch files also had CRLF) |
| `setup_final2.log` | Failed -- patch context mismatch / corrupt patch (a genuine off-by-one hunk header in `cetvel-harness-chat-template-cache.patch`) |
| `setup_final3.log` | Failed -- `OSError: [Errno 28] No space left on device` (HF/pip caches defaulting to the small root overlay instead of `/workspace`) |
| `setup_v5.log` | **Succeeded** (exit 0) -- fully clean re-test after all fixes above |

## Bias spot-check attempts (`spotcheck*.log`)

| File | Outcome |
|---|---|
| `spotcheck.log` | Failed -- `nli_tr` bare dataset id (`HfUriError`) |
| `spotcheck2.log` | Failed -- `xnli` bare dataset id (CETVEL's own `xnli_tr.yaml`, plus a proactive sweep found `mlsum`/`offenseval2020_tr`/`wmt16`/`xcopa` also bare) |
| `spotcheck3.log` | Failed -- `xnli` bare dataset id *again*, from a **different** file this time: the harness's own built-in `xnli_common_yaml`, which collides by task name with CETVEL's custom `xnli_tr` |
| `spotcheck4.log` | Failed -- same class of collision, this time `xcopa`/`xcopa_tr` |
| `spotcheck5.log` | **Succeeded** (exit 0) -- the actual bias-check result reported in `protocol-notes.md`, artifacts in `../mc-bias-spotcheck/20260913T201657Z/` |

The four earlier (failed) spot-check result directories
(`../mc-bias-spotcheck/20260913T193634Z/`, `.../193832Z/`, `.../194312Z/`,
`.../200958Z/`) contain only manifests/logs/GPU telemetry -- no samples were
ever produced since each failed before evaluation started.
