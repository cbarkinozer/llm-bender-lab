# Occam 2: failure-guided selection — 2026-10-29

## Owner review workflow

When the owner needs to review or annotate examples or results, start Docker
Desktop and the existing local Argilla deployment, preserving its existing
datasets and responses. Prepare the appropriate review records and provide the
owner a direct local Argilla UI link. Do not ask the owner to review raw TSV or
JSON as the default. The revised failure-guided dataset has not yet been prepared.

This decision supersedes the balanced generic-task dataset plan. Preserve data-v1
as an infrastructure/authoring draft, not the selected training or final test set.
Do not begin held-out baseline or full training against that draft.

## Benchmark retention clarification — 2026-10-29

Retain the original Occam benchmark, exact item IDs, reference/scoring rules and
per-item outputs as the primary historical regression anchor. Do not replace it
with the newly authored generic20. Preserve historical measurements unchanged;
rerun matched conditions where necessary rather than mixing old/new runtime
settings into a purported controlled comparison.

Evaluate the same benchmark under five clearly labeled conditions:

1. Untouched Qwen3.5-4B, thinking off.
2. Untouched Qwen3.5-4B, thinking on.
3. Released Occam/F, thinking off.
4. Released Occam/F, thinking on.
5. Reasoning-SFT Occam2, thinking on.

Within comparisons retain the same semantic task prompts, scoring and compatible
runtime/artifact representation. Match inference settings and total output
allowance across thinking-on models; record tokens and termination for every
condition. Do not infer a weight-training gain from switching thinking on alone.

This separates the effect of the thinking switch, the previous answer-only SFT,
and the new reasoning-inclusive recipe. Inspect item-level fixes and regressions,
not only aggregate accuracy. Choose untouched-base versus released-Occam
initialization after inspecting the first four conditions, and record that choice
before the new run; do not silently change the current fresh-base proposal.

Historical benchmark feedback already influenced prior work and will guide new
task selection, so label it development/regression evidence rather than a pristine
final holdout. Keep exact benchmark questions, answers and close paraphrases out
of training. Add reasoning to suitable original TRAINING problems, and author
independent examples of the diagnosed failure skills. An optional fresh20
supplement provides independent generalization evidence without replacing the
original regression anchor. Re-evaluate all relevant model conditions on that
supplement if using it for a comparative claim.

The matrix measures the new recipe's practical value. Isolating reasoning-target
supervision itself would additionally require an answer-only adapter trained on
the same examples and recipe; this ablation is optional for the breadth pilot.

## Evidence and decision

The historical Turkish Belebele paired evaluation found no statistically
significant accuracy difference across700 items: direct572/700, thinking559/700,
McNemar1.43. This supports investigating thinking as an intervention. It is not
a demonstrated accuracy gain or an equivalence/noninferiority test, and the
unequal output allowances plus truncation limit causal interpretation.
Item-level changes still occurred:44 thinking-only correct and57 direct-only
correct. Measure fixes and regressions separately rather than assuming either
universal benefit or universal harm.

Choose useful failure families using existing development evidence. Do not add
long worked reasoning indiscriminately to easy Occam training examples. Use
already-successful behaviors as retention controls; include brief/direct training
examples only if diagnosis indicates a retention need. Final composition is not
fixed at20 examples per generic category.

## Initial failure anchors (diagnostics only)

Source: exp015/human-review-v3/per-item-review.json, prior human judgments.

- me-009 and me-010: missed combined grammar corrections and subject/verb agreement.
- me-039: source says action will be taken, but summaries assert fees will change.
- me-049: explanation misses time underestimation and adds unsupported mechanism.
- me-050: superficially plausible advice omits concrete trade-offs and diagnosis.
- me-089: preference/interaction judgment is nuanced; do not treat it as a clean
  reasoning failure without adjudicating the rubric.

Source: CETVEL500 human-review-v1/labels.json and REPORT.md.

- Reviewed QA12/12 passed for base and F; large automatic score changes mainly
  concern output compliance, so these are not established reasoning gaps.
- Reviewed summaries: F2/6 passes versus base4/6. Prioritize source-faithfulness
  analysis. Labels alone do not identify exact causes; inspect source and outputs.
- GEC: F4/6 versus base0/6; remaining failures merit analysis, not blanket grammar training.

These observed items are development diagnostics, not new pristine tests. Do not
copy benchmark items, answers or close paraphrases into training. Author fresh
independent scenarios teaching the underlying skill. Reuse suitable original
training items only after provenance/split checks; not every original target is
automatically suitable for an added reasoning trace.

## Next execution order

1. Inspect and adjudicate historical failures and successful controls.
2. Probe their families with thinking off/on on development-only examples using
   the exact intended starting model. Separate incorrect reasoning from parser,
   termination, output-format and task-ambiguity problems.
3. Select failure families plausibly addressed by supervised reasoning. Preserve
   concise behavior; more explanation is not automatically an improvement.
4. Assemble revised80 training examples with verified Turkish reasoning/finals;
   retain the original Occam benchmark as the regression anchor. If adding fresh20
   tests, keep them separate, grouped by source, and do not pre-screen them to
   retain only base failures.
5. Freeze prompts, scoring, budget and recipe; record the matched untouched-model
   thinking-on baseline, then diagnostics, fresh SFT and candidate evaluation.
6. Report both repaired failures and newly introduced errors, plus final accuracy,
   Turkish reasoning adherence and cost. Historical development items remain separate.

The starting checkpoint remains untouched Qwen3.5-4B unless a separately
documented decision changes it. Historical F failures are clues, not proof that
the current untouched model in thinking mode has the identical deficit. Released
Occam remains a practical retention/product comparator.
