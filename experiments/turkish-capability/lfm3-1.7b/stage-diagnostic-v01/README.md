# Base -> CPT -> SFT diagnosis

GPU run completed and local backup verified, 2026-11-20 Istanbul. All264
diagnostic outputs plus two smoke outputs are saved, with an additional Git
evidence snapshot. See [results and scoring correction](../STAGE-DIAGNOSTIC-RESULTS.md).
The preparation description below records the frozen pre-run plan; references
to pending GPU checks describe that historical preparation state. No training
was performed. Prose correctness review remains open.

Goal: teach Turkish to LFM3-1.7B while preserving existing capabilities. Model
replacement and production readiness are not the research objective. Locate
Turkish gains and capability losses along the same parent chain BEFORE choosing
another training recipe. No training, GPU connection or publication is performed
by local preparation.

Models, fixed before inference:

1. Original LiquidAI/LFM3-1.7B, revision0dc4268b561499c648c7ba7c9466bf3d8d01517a.
2. Original base plus the published CPT adapter, revision6f213ec25a944dab2fbdeb6d337deb0e0442e638.
3. Exactly that CPT parent plus exp011 bilingual checkpoint69, adapter SHA256
   580b7a5392475a5821e415f118913dd7125de832bc302d83f1d8d700dbf7a974.

Exp013 leads the latest relative preferences, but is an original-base SFT branch;
it cannot isolate CPT -> SFT. This packet tests the actual chain, not a new
overall model selection contest. All three will run on the same pod/backend.

Main72, thinking disabled:

-52 prompts: all eight previous arithmetic groups and one seed3407-selected
  group from each of the other five categories, each in all four directions.
-8 symbolic controls, reported separately.
-12 exact seen-training probes: groups014 (margin/VAT),116 (cake allocation),
  131 (distance/time), in all four directions. These measure fitting/retention;
  exclude them from any generalization or unseen-task score.

Secondary16, thinking enabled: the same eight symbolic controls and all eight
TR/TR arithmetic questions. Compare corresponding main-off rows where available;
never mix on/off modes into a single score.264 evaluated outputs plus two smoke
outputs. Existing evaluation is already consumed: this is diagnosis, not a fresh
final test. Future training needs a distinct final holdout; no holdout is added
to training here.

Decoder remains historical BF16 vLLM0.34.0rc1.dev251+g7cc0a8a2b, seed3407,
temperature0.1, top_k50, top_p1, repetition penalty1.1, context8192,
maximum4096 new tokens, batch4, eager, prefix cache off, GPU fraction0.75,
ignore implicit EOS, explicit native EOT124900, existing exact-loop/180-second
request guards. Capture raw output/token IDs/prompts and real stop reasons.
Do not repair output text or change stops per model. GPU checks must prove
native rendering/IDs and exact merge/save/reload parity before inference.
Python3.12 is explicit; package/runtime versions and driver are captured.

## Completed CPU audit

640 rows /160 groups, four directions each; no empty answers or raw think tags;
answer/reasoning identity holds between directions sharing the output language.
120 separate nonempty worked solutions,520 direct rows. Max native-rendered
training sequence1602 tokens; no4096 truncation. Explicit worked-solution tokens
are16494 of146282 one-pass supervised tokens. At selected step69:14338 of125664
(11.41%). This is ONLY the separate thinking field: many direct rows already
explain their calculations in the final answer. Blank fields are intentional,
not automatically errors.14 of29 arithmetic-category groups have blank separate
thinking but often contain worked calculations in the answer.

Recomputed32 groups' quantitative references with the existing deterministic
reference functions, then checked numeric-marker coverage in all four directions.
One group (g104) has four optional-marker findings: yearly allowance18000 is not
stated. Reviewed original target correctly gives7200/year subscription expense,
600/month,1500/month allowance and900 remaining. No correction needed. Numeric
presence is NOT verification of full prose, units or constraints. Existing
correction02 already qualified ambiguous g035 and contradictory g153; no targets
or owner annotations were changed. This audit does not independently fact-check
every legal/historical assertion or establish a dataset error rate.

English-output metadata marks24 rows as preserving a Turkish linguistic object
and6 as language-neutral; this is not automatically wrong-language output.
Source/translation judgments and past repairs remain in bilingual-pilot-v01.
No evidence here supports 'all thinking was accidentally dropped'. It also does
not prove that the learned immediate-answer policy caused arithmetic failures.

## How results guide the next action

- Base -> CPT loses English/symbolic correctness: investigate CPT token mix,
  exposure and retention; do not blame later SFT alone.
- CPT retains skills but CPT -> SFT loses them: investigate SFT update strength,
  target quality and answer/reasoning distribution.
- Correct on seen probes but wrong on unseen analogues: evidence of limited
  transfer/generalization, not a claim that pipeline labels are broken.
- Wrong on seen probes too: fitting/retention or task difficulty requires closer
  examination; three probes alone do not identify the mechanism.
- TR input fails while matched EN input works: Turkish understanding/transfer
  remains weak; English-output preference cannot substitute for that measurement.

Measure correctness, units/contradictions, requested language, natural Turkish,
format compliance and stopping separately. Avoid an 'overall best letter'.
Keep teacher references local and hidden from inference/annotation. Rank
preferences only after correctness inspection; no need to re-annotate264 outputs.

## Next GPU handoff

Local interpreter: `C:\Users\cbark\miniconda3\python.exe`. Run commands from
`C:\Repos\llm-bender-lab`. Do NOT use the old hardcoded-pod transport directly.
Use the endpoint-parameterized wrapper, replacing HOST/PORT with the new SSH:

```text
python scripts/training/lfm3_stage_pod.py upload --host HOST --port PORT
python scripts/training/lfm3_stage_pod.py start --host HOST --port PORT
python scripts/training/lfm3_stage_pod.py status --host HOST --port PORT
python scripts/training/lfm3_stage_pod.py download --host HOST --port PORT
python scripts/evaluation/summarize_lfm3_stage_diagnostic.py
```

The wrapper uses the existing instance key outside Git, validates new host keys
with accept-new, sends LF bytes from Windows and verifies the complete upload
before extraction. Existing completed stages are reusable only if fingerprints,
counts and modes match. Interrupted outputs are preserved and require inspection;
do not overwrite or silently restart them. Controller logs stay outside the
packaged tree to avoid hashing a moving log. The downloader checks archive SHA,
all member hashes,264 output rows and completion before declaring pod-safe.

Use a24GB RTX4090-class GPU with a CUDA13-capable driver and at least40GB free
disk. Shared setup/download cache; only the minimal pinned base and root CPT
adapter download on the pod. No archived CPT checkpoints are required. A GPU
session will take setup/download time plus decoding; no one-minute promise.
No new adapters are trained. Download raw results, logs, manifests and merge
receipts; NEVER full base/merged weights. Only close after local backup receipt
says verified. GPU model/driver compatibility is still untested for the next pod.

## Reproduce local preparation and checks

```text
python scripts/datasets/prepare_lfm3_stage_diagnostic.py
python scripts/evaluation/run_lfm3_stage_diagnostic.py verify
python scripts/evaluation/test_lfm3_stage_diagnostic_cpu.py
```

Build is idempotent, preserves frozen files and fails on changed inputs. Original
local tokenizers/adapters from verified prior backups are prerequisites. CPU
tests emulate subprocess outputs to validate orchestration, counts, resume/mode
guards and upload boundaries; they do NOT validate GPU inference or model quality.
Actual smoke, EOS, native prompt and merge parity gates remain for the new pod.
An unused preparation attempt with a numeric-normalization bug was preserved in
an ignored directory; it was corrected before this active freeze. No GPU run or
dataset correction occurred during that draft.

Active freeze SHA25699ff9364882c21b68c623699ae9d1c59862d090a804da80a64a5c2f131551a1e.
Input119030510 bytes, SHA2560f1246b3498b0b1e57bf4970118b82cf3408b09711aa7d30612acd55d6841eb4.
The119MB input contains only the existing SFT adapter and required code/prompts;
no reference answers, full weights, credentials or training runner.
