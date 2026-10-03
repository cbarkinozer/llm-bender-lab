# C/D execution — 2026-10-03

New user instruction explicitly waives smoke/tiny-overfit for this C/D pair and
requests uninterrupted SFT,20-question inference per arm, comparison and verified
recovery. Pre-SFT diagnostic adapter reload is waived with smoke, not passed.
Actual-batch masking and authenticated W&B remain mandatory. Saved adapter
reload will be verified by post-SFT inference. No diagnostic adapter initializes SFT.

Proxy ssh3.vast.ai:19764 accepted existing user key. Initial noninteractive host
trust check failed; first-contact accept-new recorded host key, then login worked.
Direct endpoint supplied:83.27.30.232:43254. Prior observation: RTX4090 24GB,
driver580.178.04,80GB available disk. Recheck at setup; no vLLM installation.

Reuse exp010/setup_training.sh and pinned requirements. Historical venv name
exp010-train is not the experiment identity. C4epochs/40steps, D6epochs/60steps,
same frozen80 rows, fresh pinned base independently. Descriptive W&B run names
come from reviewed configs, no full prefix. Secrets stay in stdin/process memory.

Current status: both SFT runs,40 primary outputs, comparison and durable recovery
complete. User can terminate GPU; no termination action performed by the agent.
Quality review remains pending; successful execution is not quality success.

## Actual environment and authority

Runtime training source:f47abd7fe84259cc242778af83100fa67ac4fc05.
RTX4090 24GB,driver580.178.04,Ubuntu24.04.4,Threadripper PRO5955WX.
Python3.11.16,Torch2.7.1+cu128,Transformers5.5.0,Unsloth2026.9.6,
Triton3.3.1. Exact102-package freeze matches completed A/B runtime.
Existing local user key works on direct and proxy; no extra public key needed.
No setup/training/inference failure observed. Ordinary package deprecation,
unauthenticated public-Hub and adapter-filter warnings are preserved in logs.

Setup reused the pinned exp010 recipe except hash-verified local CUDA wheel
reuse, avoiding another GitHub download. Copied196,353,608-byte wheel from prior
verified backup; SHA2566d04c5b9c675dd68aa4ece694d3c5d1d79b25326757bae567aeb2edfe1dd5cc2.
No dependency re-resolution, no vLLM, no additional data or hyperparameter change.

Each representation check verified all100 row labels/padding,21,233,664 trainable
parameters and actual nonempty assistant labels. W&B authenticated before SFT.
Scoped policy:explicit-user-approved-targeted-pair-waiver, only exp013/014.
Smoke/tiny-overfit/pre-SFT reload recorded false/waived, NOT passed. Training
result's adapter_reload_verified:false describes the initial pre-inference state;
separate post-sft-adapter-reload.json confirms saved adapters loaded for inference.
Diagnostic adapters did not exist and did not initialize scheduled SFT.

## Training and primary inference

| Quantity | C / exp013 | D / exp014 |
| --- | --- | --- |
| Epochs / final steps | 4 / 40 | 6 / 60 |
| Runtime seconds | 153.696 | 132.0165 |
| Mean training loss | 1.1909237187355757 | 0.9682095202306906 |
| Native EOS primary answers | 20/20 | 20/20 |
| Output tokens total / median / maximum | 1030 / 22 / 188 | 1569 / 37 / 619 |
| W&B run | f71c7df3 | 9e6ad1e3 |

W&B names:exp013-sft-targeted-80rows-4ep,exp014-sft-targeted-80rows-6ep.
Both finished; history and summary recovered. C's initial kernel work makes
runtime comparisons non-isolated. D's lower training loss is not proof of better
answers. Same80-row hash and5653 supervised tokens/epoch; longer cosine in D.
Final scheduled adapters preselected; retained C checkpoint30/40,D50/60 include
optimizer/scheduler/RNG/trainer state. No checkpoint cherry-picking or merging.

HF/Unsloth BF16 greedy,rep1.05,thinking off,no extra system prompt,batch1,
4096token cap,bounded exact-loop/180second guards. All40 native EOS; no length,
repeat-guard or time stops. Natural-language repetition can still occur without
an exact-loop guard firing. Same rendered input IDs/template/settings/references
between C/D and saved A verified. No new base inference or extra thinking probes.

## Preliminary substance inspection — NOT human grades

C improves me-029 exact entity output and me-079 veri/vergi category extraction;
both preserve expectation on me-099. Shared grammar failures009/010 persist.
Both049 answers still assert unsupported neurological explanations. C070 adds
illogical reasoning despite initially saying no. D050 grows to619tokens with
contradictory recommendations and repeated list content. D089 contains dubious
claims and advice about being alone; C089 is also awkward. D090 replaces the
invitation to vent with generic reassurance. Do not declare either better than A
from lower loss, EOS or brief excerpts. All raw answers are preserved for review.
Regex check:zero bold/headings or emoji-range flags in either20 outputs, but
numbered lists, verbosity and semantic repetition remain possible.

## Comparison and verified recovery

Argilla:exp-013-014-A-C-D-validation-20,dataset
e3b691cb-79fc-4bd8-a358-39f9a23770b5;20 fields read back,HTTP200 verified.
Desired/A/C/D columns strictly source-bound; old annotations untouched.
me-089 disputed reference flagged explicitly; original frozen reference unchanged.

Local root:C:/Users/cbark/Documents/llm-bender-artifacts/exp-013-014-paired.
Archive exp013-exp014-backup.tar.gz:847,921,015bytes; SHA256
7ec4c82c39f02a12583d5a885e60736252160872c4b395e4c964916b4bcfe864.
Digest verified; bounded extraction rejected links/escaping paths; all129 indexed
sizes/hashes verified, adapter digests matched inference manifests, both retained
checkpoint pairs and resume states complete. Saved raw outputs/attempts/configs,
actual masks/gates/effective args,source bundles,platform/package freeze/setup,
training/inference logs,CUDA wheel,W&B histories/local files and reload evidence.
The W&B credential used is absent from all recovered files,including source bundles.
Pinned public base weights remain an explicit download dependency,not offline backup.
Local comparison CSV/link and later repository recovery bundle supplement the archive.
