# Response Style Control — Qwen3.5-4B

## Origin

Split out of `experiments/turkish-capability/` after that line's Phase 2
diagnostic (`turkish-capability/qwen3.5-4b/exp-000-baseline/protocol-notes.md`)
found no Turkish-fluency gap. The actual, reproducible weakness found there
is not language-specific: the model answers structured-task prompts
(grammar correction, extractive QA, summarization) like a chat assistant
explaining itself — diagnostic prose, restated full sentences, bulleted
breakdowns — instead of emitting the bare/terse output the task format
calls for. This is a response-policy/style problem (directness, brevity,
format obedience, verbosity switching), evaluated through a Turkish lens
because that's where it was found, not a Turkish-capability problem.

## Target capability

Instruction-following / output-format discipline and conciseness under
structured-task prompts, **without** losing the model's ability to be
discursive when a prompt actually calls for it (open-ended questions,
explicitly requested explanations). The failure mode to avoid is trading
one uncontrolled default (always verbose) for another (always terse).

## Baseline (reused, not re-run)

This experiment reuses `turkish-capability/qwen3.5-4b/exp-000-baseline`'s
Phase 2 generation results as its baseline — see that experiment's
`protocol-notes.md` for the full evidence (raw scores + manual review
samples). No need to re-run the untouched-model measurement.

| Task | Metric | Baseline score |
| --- | --- | --- |
| `gecturk` | exact match | 1.0% (63% flagged verbose) |
| `tquad` | EM / F1 | 0.7% / 19.4% |
| `xquad_tr` | EM / F1 | 0.7% / 15.7% |
| `wmt_en_tr` (EN→TR) | BLEU / chrF | 13.0 / 52.6 (not a target — already fine) |
| `mlsum_tr` | ROUGE-L | 20.5% |

## Data generation focus

See `exp-001-sft-dataset/` for the taxonomy. Summary of what to build:

1. **Bare-output GEC pairs** — target is only the corrected sentence, no
   explanation or framing text left in.
2. **Bare-span QA pairs** — target is the minimal answer span, not a full
   restated sentence.
3. **Terse single-sentence summaries** — one sentence capturing the core
   fact, not a structured/bulleted breakdown.
4. **No translation examples** — `wmt_en_tr` is already fine; don't spend
   data budget there.
5. **A counter-set of genuinely open-ended prompts with discursive expected
   answers** — so the model learns *when* terseness applies, not blanket
   terseness. This is the guard against Case E/overcorrection.
6. **A small numeric/entity-precision QA set** — targets the secondary
   finding (occasional wrong-number/wrong-entity extraction), lower
   priority than 1-3.

## Capability budget

| Capability | Requirement |
| --- | --- |
| `gecturk` exact match | Improve over reused baseline (1.0%) |
| `tquad`/`xquad_tr` exact match | Improve over reused baseline (0.7% / 0.7%) without F1 dropping (19.4% / 15.7%) |
| `mlsum_tr` ROUGE-L | Improve over reused baseline (20.5%) without collapsing into under-informative one-liners |
| `wmt_en_tr` BLEU/chrF | No regression below reused baseline (13.0 / 52.6) |
| Instruction following on open-ended prompts | Maximum 2-point absolute regression |
| General reasoning | Maximum 5-point absolute regression |
| Invalid or non-terminating outputs | No increase |

The regression benchmark for open-ended instruction-following/reasoning is
not yet selected.

## Relationship to the project roadmap / 0.8B

This experiment *is* the root README's roadmap item 3, "Efficient Tiny
Assistant" — retargeted to start on `Qwen3.5-4B` instead of `Qwen3.5-0.8B`
(see the root `README.md`'s model-choice note under that section). Decision:
stay on 4B for now, don't drop to 0.8B yet. Two reasons: 0.8B genuinely risks
being too weak to reliably learn a new communication policy, and this
project is still new enough that proving the dataset/method on the more
capable model first is the safer sequencing — debugging a new dataset and a
much weaker model at the same time is a harder problem to take on right now.
`0.8B` is deferred, not abandoned: it's the harder/later step, to be
attempted once this experiment's dataset and method are validated here.

## Current selection

None yet. Dataset construction (`exp-001-sft-dataset/`) is the next step.

## Experiment registry

| ID | Status | Main change | Notes |
| --- | --- | --- | --- |
| `exp-000-baseline` | reused | N/A — reuses `turkish-capability/qwen3.5-4b/exp-000-baseline` | No re-run needed |
| `exp-001-sft-dataset` | planned | Narrow style-control dataset (GEC/QA/summarization bare-output + open-ended counter-set) | Taxonomy draft in progress |
