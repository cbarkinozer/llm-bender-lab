# Occam 2 execution plan — 2026-10-28

Superseded data-selection decision,2026-10-29: see
[failure-guided revision](FAILURE-GUIDED-REVISION.md). The authored generic data
is an infrastructure draft; select revised80/20 from diagnosed failure families
and retention needs before proceeding to held-out baseline or full training.

## Decision

Start a fresh LoRA from untouched Qwen/Qwen3.5-4B, revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. Occam 2 is a product/research
successor, not continued training of the released Occam adapter.

Supervise both Turkish reasoning and concise Turkish final answers using ordinary
next-token cross-entropy on assistant tokens. System/user/padding labels are
masked. There is no separate reasoning head or reasoning-only update; shared
LoRA parameters learn from both portions. Use normal token-level weighting for
the first pilot and record reasoning/final token counts to expose imbalance.

Hypothesis: checked Turkish worked solutions improve correctness on unseen
Turkish document-grounded reasoning tasks while retaining concise answers.
Language adherence and correctness are distinct outcomes. Turkish visible traces
do not establish an internal language of computation or reasoning faithfulness.

## 1. Freeze task and split design

- [x] Define source-contained problems with an explicit scoring key and acceptable alternatives.
- [x] Allocate four categories: updated facts/dates/attribution; rules/exceptions;
  quantities/costs/scheduling; evidence sufficiency/ambiguity/uncertainty.
- [x] Prepare 20 training cases and five test cases per category: 80/20 total.
- [x] Keep related source/scenario variants in one split. Include challenging
  combinations and changed decision conditions, not only renamed templates.
- [ ] Freeze scoring, failure rules, inference settings and final-checkpoint rule
  before collecting held-out baseline outputs. Do not select test items based
  on which ones the base fails.

## 2. Author and check data

- [x] Write natural Turkish inputs, Turkish worked reasoning, and concise Turkish answers.
- [x] Store reasoning and answer separately; native templating supplies delimiters.
- [x] Complete author semantic self-review and automated arithmetic checks.
- [ ] Independently review answers, dates, assumptions and ambiguous cases;
  independent human review has not occurred and is not implied by author checks.
- [x] Include answerable and insufficient-evidence cases; avoid teaching habitual refusal.
- [x] Record assistant-authored synthetic provenance and any external source permissions.
- [x] Audit exact/near duplicates and historical Occam/benchmark overlap; hash splits.
- [x] Prepare a few separate development probes for infrastructure/difficulty
  checks; they do not become held-out test cases or extra training examples.

## 3. Validate the actual representation

- [ ] Pin tokenizer, template and working library versions.
- [x] Render single-turn samples; inspect exactly one reasoning block and native end-of-turn.
- [x] Inspect actual labels: reasoning, answer and end-of-turn supervised;
  system/user/padding masked. Preserve EOS even when its ID is also used for padding.
- [x] Measure full/reasoning/final token-length distributions and choose context
  length. Reject unexpected truncation; packing starts disabled.
- [ ] Record adapter scope and trainable parameters; leave vision frozen.

## 4. Record baseline before training

- [ ] Primary baseline: untouched Qwen with thinking explicitly enabled.
- [ ] Primary candidate: Occam 2 with thinking explicitly enabled.
- [ ] Use identical semantic prompts, Turkish-language instructions, backend,
  sampling, seeds and total output allowance, including reasoning.
- [ ] Save raw reasoning, final answers, termination, tokens and latency.
- [ ] Optional contextual comparisons: untouched Qwen thinking-off and released
  Occam thinking-off. They do not replace the primary matched comparison.
- [ ] Preserve held-out baseline outputs without using errors to revise training data.
  If test feedback changes the recipe, label this set development and create a new test set.

## 5. Run one bounded SFT recipe

- [ ] Begin with proposed BF16 LoRA r/alpha16, dropout0, LR1e-4, effective batch8,
  seed3407, three epochs / 30 optimizer steps. Confirm on the selected host.
- [ ] Complete smoke and tiny-overfit diagnostics using training examples only.
- [ ] Start the actual run from fresh base/adapter initialization, not diagnostic weights.
- [ ] Freeze the full-run update count before test evaluation; save final adapter,
  manifest, loss logs, environment, resource use and hashes. No test-based selection.

## 6. Evaluate and decide

- [ ] Run frozen 20 tests on the selected final adapter with the matched protocol.
- [ ] Primary: final correctness/constraint satisfaction out of20, paired wins,
  losses and ties against base thinking-on. Separate formatting from semantic errors.
- [ ] Supporting: Turkish reasoning adherence (allow ordinary technical terms),
  concise final answers, unsupported facts, reasoning/answer consistency, truncation,
  natural termination, tokens and latency.
- [ ] Check a small separate frozen instruction-following/regression set.
- [ ] Manually review all20 paired outputs and report small-sample limitations;
  a one-question change equals five percentage points and is weak evidence alone.
- [ ] Record improvement, trade-off, or no improvement honestly and close the pilot.
  An 80-case specialization result does not establish broad Turkish improvement.

## 7. Deployment, if the pilot is useful

- [ ] Preserve adapter and recipe, merge/export with pinned tooling, then compare
  the deployed GGUF against the pre-export adapter on fixed checks.
- [ ] Confirm thinking switch/template/EOS and Mac resource use.
- [ ] Keep the original Occam release available; publish Occam 2 only with actual
  results and limitations. No deployment or publication has been executed.

## Interpretation limits

The primary comparison measures the whole reasoning-inclusive SFT recipe. It
does not isolate whether gains come from Turkish reasoning language, answer
supervision, or task examples. A separate answer-only adapter would test the
incremental value of reasoning supervision; a matched English-reasoning adapter
would test reasoning language. Both are deferred to keep this learning pilot small.
