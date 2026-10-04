# exp-003-cetvel-500: independent-source base versus F confirmation

Status:1000 outputs/scoring/paired analysis complete and45-file local recovery
verified; GPU safe to close. Blind human30 completed/exported; phase closed.
Preferences F19/base6/tie2/neither3; passes F23/base21. Reviewed QA12/12 both
pass; summary pass F2/6 vs base4/6. Selected F for style, not global superiority.
See `REPORT.md` and `results-v1/`. No new training or W&B.
Parent exp002 pilot and its20 human reviews are preserved separately.

Source-bearing questions/generations remain locally preserved but Git-ignored
pending source-specific redistribution rights. Full review receipts/notes remain
local; public source-ID keyed labels omit private review metadata. Builder/pins,
hashes, metrics, labels and grade summaries preserve traceability. Rebuild question files
with prepare.py/source cache before CPU tests; full recovered raw evidence remains
at the documented local recovery path. SFT publishing does not include CETVEL text.

Question: do F's compliance/preference gains persist on new source groups without
concerning factual, correction or translation regressions? Keep final exp016/F
fixed. Only evaluation population/size changes; no adapter update for de/da yet.

## Frozen cohort and limitations

500 NEW questions,100 per task: GECTurk correction, TQUAD QA, XQuAD-TR QA,
WMT EN-to-TR translation, MLSum-TR summary. Not the old100 plus400 more.
Full pinned evaluation splits, not the historical700 prefix pool. Exclude all
historical700 rows AND their exact normalized source groups, including pilot100.
One question per distinct source group: GEC intended target sentence, QA context,
English translation source, summary article text. Summary URLs also excluded when
seen historically. This does not establish independence of articles about the
same event, QA topics, or cross-language/pretraining provenance.

Seed3407 shuffles source groups then picks one row uniformly within each group.
Before accepting, withhold conservative near-source candidates (five-word
containment>=.8), training similarity candidates (character>=.75 or five-word
containment>=.5, exact normalized strings), and inputs outside the original
8192-context/4096-output budget. Selection does not use model outputs or scores.
Group-balanced sampling is not uniform row sampling; results describe this cohort,
not the whole dataset. No blanket redistribution license asserted; local eval only.

Frozen SHA256: `2ccd068e8f95259083f0f5c30853d414801b9e06e9790bcf936b471467c46b93`.
Input maximum3410, no input truncated or selected input over budget. No selected
training similarity candidates. Data manifest records full split counts, source
pins/file hashes, eligible groups and exclusions. Some upstream QA text/reference
encoding is imperfect; preserve source data rather than silently repairing targets.

TQUAD raw upstream GitHub pinned to3bece60f62569182476fe00683793745ba92c32e;
cast ID to string and answer offsets to integers, matching historical HF schema.
MLSum uses separately pinned official HF converted-Parquet snapshot
0064616e75e0645465d07e98c1447ee6613f61e8, not the original script-only commit.
ALL700 historical documents and prompts/targets matched at their source indices
before selection. Actual source bytes pinned/hashed independently of builder pins.

30 human-review IDs selected before outputs,6/task; after inference prepare blind
P/Q queue with preference and pass/partial/fail for each. Diagnose suspicious
metric misses/terminations separately; do not replace random sample with failures.
If500 later informs training choices, it becomes development, not a final test.
Never train these questions, targets or paraphrases. Fresh test needed afterward.

## Fixed execution and analysis

Reuse exp002 vLLM runner with explicit --experiment-dir; same base revision/F
hashes, BF16, greedy, rep1.05, output4096/context8192, batch cap8, eager,
prefix cache off, model EOS248044 (not tokenizer EOS248046). No system prompt,
thinking off, no newline stop. Preserve every incomplete output; no silent retry.
1000 outputs, prompt/config/token/backend parity; no W&B or fine-tune.

Task-native metrics unchanged. Separate per-task comparisons, no pooled accuracy.
5000 paired bootstrap resamples produce exploratory95% intervals for GEC EM,
QA EM/F1, mean sentence chrF and summary ROUGE; translation corpus BLEU/chrF
still reported separately. No inference of semantic faithfulness from overlap,
or formal multiple-testing-adjusted superiority. No human judgments by agent.

GPU setup/runner executed successfully; runtime evidence is preserved.
The prior validated backend is reused. Setup import/CUDA checks passed on new
RTX4090/driver590.48.01, Python3.12.3; vLLM0.30.0/Torch2.13.0+cu130/Transformers5.18.0.
no extra training smoke or tiny-overfit run. Both old GPU routes were unavailable
on2026-10-04: direct timed out, proxy refused. New direct143.131.225.132:41841
and proxyssh9.vast.ai:19562 both authenticated to containerc9995edb168b with the
existing key; no key content recorded. Source transfer SHA verified. Early
extraction of incomplete adapter upload failed; after SCP exit0 full archive
SHA and adapter weight/config hashes passed, re-extracted before any generation.
Standalone launch_remote.py detaches coordinator without retaining SSH pipes;
its source will be included in recovery. No extra smoke or overfit.

## Commands

CPU preparation/tests:

```powershell
& C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500/prepare.py --cache-root C:/Users/cbark/Documents/llm-bender-artifacts/cetvel-fresh500-source-cache
& C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500/test_preparation.py
```

GPU (after narrow source/F transfer):

```bash
bash experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500/setup_vllm.sh
export HF_HOME=/workspace/.cache/huggingface
export LD_LIBRARY_PATH=/workspace/.venvs/cetvel-vllm/lib/python3.12/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}
/workspace/.venvs/cetvel-vllm/bin/python experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500/run_gpu.py --adapter /workspace/F-adapter
```

Coordinator saves benchmark/scoring/paired-analysis logs, versions, invocation,
actual source/config/data and both outputs. On failure, archives available evidence
with explicit failed status; do not declare recovered benchmark success. Before
GPU disposal download /workspace/cetvel-500-backup.tar.gz AND metadata JSON;
use shared verify_recovery.py with --bundle-prefix cetvel-500 to verify hashes,
1000 completed outputs and prompt parity. F weights already recovered locally;
base9GB weights pinned/downloadable, not a required recovery download.

After verified recovery, use shared import_human_review.py with --experiment-dir
pointing here and --results-root pointing to recovered cetvel-500-runs. Do not
create an empty review queue before outputs exist.
