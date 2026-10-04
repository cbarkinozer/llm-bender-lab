# Turkish Capability — Qwen3.5-4B

2026-10-04: [exp002 CETVEL-tiny100](exp-002-cetvel-tiny/README.md) adds an
evaluation-only base versus final exp016/F retention pilot.200 outputs recovered,
human20 completed: F12 preferences versus base2, tie4/neither2; passes13 versus12.
[exp003 CETVEL500](exp-003-cetvel-500/README.md) prepared with500 NEW questions,
historical source groups excluded;1000 outputs recovered, blind human30 completed.
F QA/correction reference scores rise; summary ROUGE-L18.45 to20.93,
translation essentially unchanged. Human preferences F19/base6/tie2/neither3,
passes F23/base21; reviewed QA12/12 both pass, summary pass F2/6 vs base4/6.
No general semantic-superiority claim. Evaluation phase closed2026-10-04;
F selected as an experimental style adapter, not a universal Turkish upgrade.
No new training. See exp003 REPORT.md for limits and per-task evidence.
Original baseline conclusions below are
historical observations, not assumptions about this adapter or its pinned base.

**Status: closed.** This experiment line's question has been answered:
Qwen3.5-4B's baseline Turkish is not the bottleneck. See "Outcome" below.
Do not add new training experiments here — the follow-up work lives in
[`experiments/response-style-control/`](../../response-style-control/).

## Original target capability

Improve Turkish language understanding and generation while preserving the
starting model's instruction-following and general reasoning behavior.

## Outcome

`exp-000-baseline`'s Phase 2 diagnostic (700 generation items across GEC, QA
x2, translation, summarization — see `exp-000-baseline/protocol-notes.md`,
"Phase 2: generation-task diagnostic suite") found that the model's raw
Turkish is consistently fluent and grammatically correct across every task.
The near-zero exact-match scores on GEC/QA and depressed ROUGE on
summarization are explained almost entirely by a different behavior: the
model answers structured-task prompts like a chat assistant explaining
itself (diagnostic prose, restated full sentences, bulleted breakdowns)
instead of emitting the bare/terse output the task format calls for.

Also established earlier in `exp-000-baseline`: several of CETVEL's
likelihood-scored multiple-choice tasks (`belebele_tr`, all of `nli_tr`'s
subtasks) are measurement artifacts from position-bias collapse in raw-logprob
scoring, not real capability signal — see the MC bias spot-check finding in
`exp-000-baseline/protocol-notes.md`. `turkish_plu` and `xcopa_tr` were not
affected.

**Conclusion: no evidence of a Turkish-fluency capability gap.** The actual
weakness — instruction-following / output-format discipline under
structured-task prompts — is not a language capability at all, so continuing
to frame the next fine-tuning experiment as "Turkish improvement" would be
chasing the wrong target. That work continues under
[`experiments/response-style-control/`](../../response-style-control/), which
reuses this experiment's diagnostic evidence as its starting baseline rather
than re-running it.

## Starting model

- Repository: `Qwen/Qwen3.5-4B`
- Revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- Type: post-trained multimodal model, evaluated with text-only inputs

## Evaluation suite

- Target: CETVEL, pinned by Git commit in the evaluation configuration, plus
  the Phase 2 generation-task diagnostic suite (`gecturk`, `tquad`,
  `xquad_tr`, `wmt_en_tr`, `mlsum_tr`)
- Supporting: Turkish output quality and correct stopping, sampled manually
- Regression: instruction following and general reasoning, benchmark not
  selected (moot now that this line is closed without a fine-tune)

The target protocol is defined in
[`configs/evaluation/turkish-cetvel-v1.yaml`](../../../configs/evaluation/turkish-cetvel-v1.yaml).

## Superseded dataset draft

`exp-001-sft-dataset/` contains a draft taxonomy for a broad 10-task/20-domain
general-Turkish-capability SFT dataset, written before the Phase 2 diagnostic.
It is superseded by the narrower taxonomy in
`experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/` and kept
here only for reference — do not build from it.

## Experiment registry

| ID | Status | Main change | Target score | Notes |
| --- | --- | --- | ---: | --- |
| `exp-000-baseline` | done | Untouched starting model, CETVEL + Phase 2 generation diagnostic | n/a | Found no Turkish-fluency gap; found the real weakness is format/instruction-following. Also found and fixed several CETVEL MC-scoring artifacts. |
| `exp-001-sft-dataset` | superseded | Broad Turkish-capability SFT dataset draft | — | Written before Phase 2 diagnostic; premise no longer supported. See `experiments/response-style-control/`. |
| `exp-002-cetvel-tiny` | completed | Matched base/F100 pilot +blind20 | task-specific | Historical prefix pools; development evidence, not pristine final test |
| `exp-003-cetvel-500` | completed; phase closed | New source-group500 +blind30 | task-specific | F preference19/base6; QA style gain, summary limitation; see REPORT.md |
