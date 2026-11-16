# Turkish post-training and Reflex roadmap

## Latest handoff: reviewed160 frozen

All80 new Argilla text reviews are submitted and exported. The combined160 training rows and unchanged protected20 are versioned in [pilot160](../experiments/turkish-capability/lfm3-1.7b/sft-pilot160-v01/README.md). Owner requested training tomorrow; no training launched. Next: separate dev packet,160-compatible recipe and real-model preflight, then the planned LR1e-4/2e-4 pair with epoch3/5 checkpoints. This update supersedes earlier pending-review counts.

Requested: 2026-11-14. Status: plan; no new training or data generation launched.

## Direction

Build a broadly reusable, reviewed Turkish SFT core first, with separate direct
and reasoning configurations. Then train/evaluate LFM3-1.7B-Turkish-SFT and create
a separately versioned model-specific selection if evidence warrants it. DPO
follows stable SFT. Reuse semantic data for bounded MoE/text-diffusion learning
projects, then focus deeply on Reflex-1 decision models.

The corpus design and growth gates are in [turkish-sft-corpus-design-v01.md](turkish-sft-corpus-design-v01.md).
The working loop is diagnose -> coverage contract -> source audit -> curate ->
review -> freeze dataset -> controlled training/evaluation -> versioned iteration.

## 0. Establish the actual starting checkpoint — complete

- [x] Published CPT revision: 6f213ec25a944dab2fbdeb6d337deb0e0442e638;
  root adapter is cumulative 100M, backed by the publication receipt.
- [x] Recovered all 500 raw/scored outputs, manifest and original scores at commit
  09390ad20175b4ac548129723119ae1cd52e944c; hashes verified against recovery receipt.
- [x] Use NEXT-SESSION-20261112.md and model-release/README.md for completed CPT
  evidence; earlier pending-status config/README text is historical.
- [x] Distinguish matched 100-item screening from 100M-only full500. There is no
  newly matched original-model full500 baseline. Sequential CPT/SFT/DPO product
  work remains separate from the older independent-method study.

## 1. Diagnose weaknesses and freeze evaluation

- [ ] Inspect all 500 outputs with task-level scores and representative human review.
  Separate wrong answers from correct-but-verbose answers, formatting/parser errors,
  over/under-correction, unsupported claims, truncation, and failure to terminate.
- [ ] Produce a capability table: examples inspected, failure frequency, confidence,
  severity, suspected cause, and proposed training behavior. Mark uncovered areas
  as untested rather than weak.
- [ ] Treat the existing 500 rows as historical development/comparison evidence.
  Exclude their questions, answers, source documents, paraphrases, translations,
  and item-derived synthetic examples from training.
- [ ] Generate from abstract failure categories using independently authored contexts;
  do not ask a teacher to rewrite failed benchmark questions.
- [ ] Add separate development probes for instruction following, JSON/schema output,
  unanswerable grounded QA, multi-turn context, Turkish naturalness, and reasoning.
  The historical QA cohort has no unanswerable examples.
- [ ] Create a separate final test, held out from generation and recipe selection,
  split by source/document/template family. Include English/general regressions.
- [ ] Define primary metrics and acceptable regressions before runs. Report each task,
  blinded human correctness/preferences, format compliance, output tokens, termination,
  latency and memory separately. Use paired uncertainty estimates where appropriate.

Current CPT evidence and row-level diagnostic limitations are recorded in
[response-analysis-v01](../experiments/turkish-capability/lfm3-1.7b/response-analysis-v01/README.md).
All 500 have deterministic diagnostics; agent qualitative triage is explicitly
separate from owner review. The cohort covers five tasks, not general assistant
or reasoning capability.

Done when: prioritized deficits and a frozen evaluation manifest exist.

## 2. Audit candidate sources

2026-11-14 intake audit completed at
[`source-audit-v01`](../experiments/turkish-capability/lfm3-1.7b/source-audit-v01/README.md):
four pinned downloads, 346,717 structural records, 142 purposive full-record
agent reviews, and 60 unapproved source-review candidates now in local Argilla.
This completes the bounded source comparison, not final rights/contamination
clearance or owner acceptance. Occam uses only its pinned public HF release.

| Source | Proposed role | First check |
| --- | --- | --- |
| Occam-Turkish-Response-SFT | Preserve reviewed concise-response seed | Recover original provenance and train/development assignments; old development stays development |
| AlicanKiraz0/Turkish-SFT-Dataset-v1.0 | Selective domain/response diversity | Card shows ~5.58k rows, MIT; inspect correctness and long academic answer style |
| AlicanKiraz0/Turkce-Atlas-Instruct | Broad candidate pool, selectively sampled | Card shows ~336k rows, MIT; audit coverage, duplication and target reliability |
| AlicanKiraz0/Turkish-CoT-Instruct-Dataset | Planned verified reasoning configuration | Card shows ~4.87k rows, Apache-2.0 and think-tagged responses; verify solutions and native model compatibility |

- [x] Pin source revisions and inspect stratified samples by topic, difficulty,
  response length and source. Dataset cards are declarations, not quality audits.
- [ ] Record source IDs, original licenses/terms, upstream origins, transformations,
  attribution/NOTICE requirements, and synthetic teacher provenance where available.
- [ ] Resolve training and redistribution eligibility before admitting a source.
  Credit alone does not resolve licensing or upstream restrictions.
- [ ] Audit benchmark overlap, including translated problems, and cross-source duplicates.
- [ ] Compare token distributions using the actual LFM tokenizer; reject broken,
  unsupported, wrong-language, repetitive or truncated records. Review similarity
  candidates before removing meaningful near-neighbors.

Done when: each source has an admit/select/reject decision and a retained audit.

## 3. Build and freeze the reusable reviewed corpus first

- [ ] Preserve Occam v1; create a new version or distinctly named curated derivative.
  A unified release can have separate direct-response and reasoning configurations
  plus a separate preference companion. Do not force all objectives into one schema.
- [ ] Define a capability/source/difficulty/length allocation from Phase 1. Use
  targeted repairs plus broad coverage; cap repetitive families and large sources.
- [ ] Normalize to model-independent messages with stable ID, capability, source ID
  and revision, license, group ID, generation/transformation metadata, review state,
  and split. Keep rationale/answer separable when present.
- [ ] Select from audited sources first, then author independent synthetic records
  for uncovered capabilities. Calibrate on 60 candidates, freeze an initial ~300
  accepted snapshot, then expand in reviewed batches of 200-300. Record teacher,
  prompts, model version/date/settings and applicable output-use terms.
- [ ] Independently verify targets: calculators/tests/schema checks when possible,
  otherwise evidence-based review. Teacher agreement alone is insufficient.
- [ ] Reserve source/template/problem families before authoring variants; withhold
  final families from generation and tuning. Deduplicate across splits before
  training. Never absorb old Occam development records into training.
- [ ] Build toward ~1k accepted records; expand toward 2k-3k only for remaining
  coverage/diversity gaps. Freeze reviewed general v01 before LoRA; use later
  held-out experiments to inform v02 and model-specific selection.

Done when: the general-coverage corpus passes the design coverage/review gates, with a versioned snapshot, quality report and split manifest.

## 4. Argilla review workflow

- [ ] Reuse existing repository Argilla scripts and inspect the available instance
  before implementing new infrastructure. Use standard Argilla UI, not a custom site.
- [ ] Create a versioned candidate-review dataset with prompt, proposed answer,
  optional editable correction, source/capability/difficulty/length metadata and IDs.
- [ ] Collect accept/edit/reject, correctness, Turkish naturalness, instruction
  compliance, appropriate detail, ambiguity, and error labels with reviewer notes.
- [ ] Calibrate the rubric together on 60 diverse candidates, then have the owner
  review every row released in v01. Prioritize uncertain and risky candidates;
  retain a stratified independent quality audit as a separate check.
- [ ] Export accepted/corrected targets with annotation snapshot and revision;
  keep notes, model scores and review instructions out of training messages.
- [ ] Create a separate blinded A/B evaluation view for model comparisons, and later
  a preference collection view with ties/neither acceptable options.

Done when: you can review, edit, reject and export a reproducible training snapshot.

## 5. Direct-response SFT and release

- [ ] Freeze one primary hypothesis: frozen reusable-core v01 SFT improves general
  Turkish task performance while preserving predefined language capabilities.
  Targeted LFM3 selection is a separate subsequent experiment.
- [ ] Validate native chat template, assistant-only labels, EOS/stop behavior,
  truncation, packing, nonempty targets, and adapter initialization. Verify whether
  CPT is merged or adapted; do not accidentally discard the CPT weights.
- [ ] Run real-model smoke and tiny-overfit gates before a full run, following the
  repository finetuning playbook. Set token/compute budget and record hardware.
- [ ] First compare CPT unchanged vs CPT + frozen reusable-core v01. Original
  model + identical v01 tests CPT's contribution if budget permits. Occam-only
  is an optional comparator, not the primary dataset. Track assistant tokens,
  updates, wall time and compute; separate recipe comparisons from causal claims.
- [ ] Select using development evidence, inspect blinded outputs, and repeat promising
  results when needed before making robust improvement claims. Loss alone is insufficient.
- [ ] Evaluate the selected artifact once on the reserved final test, then verify
  merged/quantized deployment artifacts separately if releasing them.
- [ ] Release dataset card, model card, credits, source revisions, data composition,
  training config, per-task results, limitations and reproducibility manifest under
  `cbarkinozer/LFM3-1.7B-Turkish-SFT` once supported by evidence.

Gate: improved targeted behavior with acceptable regressions; otherwise revise data.

## 6. Planned reasoning SFT experiment

Owner clarification: reasoning SFT is an intended learning and capability goal,
especially for tasks where the 1.7B model benefits from additional inference
computation. Plan and evaluate it explicitly; shipping a reasoning derivative
depends on measured results, but running the experiment is part of the roadmap.

- [ ] Inspect the pinned LFM model/template for its native reasoning behavior and
  supported controls. Do not assume foreign `<think>` tags create a functioning mode.
- [ ] Curate a small verified subset of arithmetic, logic, constraint-following and
  multistep grounded problems; check intermediate steps and final answers separately.
- [ ] Compare the same problems as final-answer-only, concise worked solutions,
  and native explicit reasoning where supported. Start with hundreds of examples.
- [ ] Keep ordinary direct-response examples in the mix and evaluate simple-query
  verbosity, reasoning accuracy, token budgets, latency and termination.
- [ ] Measure accuracy at matched inference budgets plus practical accuracy/cost
  tradeoffs. More generated explanation is not proof of better reasoning.
- [ ] Promote only if held-out reasoning improves enough to justify extra compute;
  otherwise keep it as a documented experimental branch.

## 7. DPO after a stable SFT checkpoint

- [ ] Generate multiple outputs from the selected SFT checkpoint on fresh training
  prompts; collect judged and human-reviewed preferences in Argilla.
- [ ] Store shared prompt, chosen and rejected completions, source/group IDs,
  rubric and preference reason. Exclude ties, both-bad and uncertain pairs.
- [ ] Start with roughly 500-1,500 reliable pairs if review capacity allows. Cover
  real residual failures and avoid making brevity or source identity the shortcut.
- [ ] Freeze disjoint development/test prompts, SFT initialization/reference policy,
  template and objective configuration; run smoke and a small controlled pilot.
- [ ] Compare SFT vs SFT+DPO for correctness, calibrated uncertainty, unnecessary
  refusals, format compliance, length and blinded preference. Monitor degradation.
- [ ] Publish a DPO derivative only if it adds demonstrable value. Keep the older
  independent original-model DPO arm conceptually separate.

## 8. Bounded architecture learning projects

- [ ] MoE SFT: choose a supported checkpoint when starting; verify total versus active
  parameters, actual VRAM and training stack. Run a small curated subset, inspect
  router/expert training choices and routing diagnostics, then compare quality/cost.
- [ ] Text diffusion SFT: choose an openly trainable checkpoint and supported recipe
  when starting. Verify its masking/noising objective, completion conditioning,
  loss masking, sampler and denoising steps. Do not reuse autoregressive SFT blindly.
- [ ] Reuse semantic data and evaluation concepts, but validate architecture-specific
  trainers. Bound each project to one hypothesis, a budget and a short findings report.

These are learning milestones, not prerequisites for Reflex. If they delay the main
research direction, return to Reflex after the dense-model SFT/DPO work.

## 9. Return to Reflex-1: local agent decisions under 1B parameters

- [ ] Inspect the existing Reflex-1 artifacts and define one narrow first task:
  tool selection, retry/stop, or clarification routing, with explicit output schema.
- [ ] Build labeled state -> decision examples with tool schemas, execution outcomes,
  missing-information cases, no-tool cases, failures, recovery and stopping conditions.
- [ ] Split by workflow/scenario/tool family; hold out unfamiliar tools and realistic
  state distributions rather than random near-duplicate rows.
- [ ] Establish rules/heuristics, a simple classifier, a sub-1B model and larger-LLM
  baselines. Measure task outcomes as well as decision accuracy.
- [ ] Report invalid actions, unnecessary tool calls, premature stops, missed
  clarifications, calibration/abstention, end-to-end success, p50/p95 latency,
  throughput and peak memory on named consumer hardware and runtime.
- [ ] Measure deployment precision/quantization and complete workflow cost; claims
  of matching larger LLMs must name tasks, baselines, hardware and evaluation scope.
- [ ] Release a reproducible benchmark, dataset, model and local runnable example.

## Immediate next work

Owner decisions, 2026-11-16 (supersede older comparison plans below):

- Completed20 owner comparisons: working pilot winner exp-006, LR2e-4
  (10 wins,6 losses,4 ties versus1e-4). Preferences are not production acceptance.
  See [final review](../experiments/turkish-capability/lfm3-1.7b/PILOT80-OWNER-REVIEW-FINAL.md).
- [Batch02 text editor](http://127.0.0.1:6900/dataset/2622bd70-e5e5-48af-8905-91a4ea47032f/annotation-mode)
  has exactly Input / optional Thinking / Output textboxes, prefilled; no ratings.
  Migration retained20 Occam approvals and14 owner edits;46 remain drafts. Submit
  final text only; blank Thinking means none and must not restore source reasoning.
- Two-job design: LR1e-4 vs2e-4, epoch3/5 checkpoints in each (four candidates).
  See [pilot160 plan](../experiments/turkish-capability/lfm3-1.7b/PILOT160-PAIR-PLAN.md).
  Freeze reviewed160 and separate development data first. No new training launched.

- Use the untouched, pinned LiquidAI/LFM3-1.7B as the primary baseline for future
  comparisons, replacing CPT as the primary comparator. Preserve historical CPT
  results. This changes evaluation, not the training parent; no switch away from
  CPT-initialized SFT has been authorized or tested by this decision.
- Next intake is 80 NEW training candidates from the same four pinned sources:
  public cbarkinozer/Occam-Turkish-Response-SFT and the three AlicanKiraz datasets.
  Aim for 20 per source where eligible diverse examples exist, with capability
  and token-length balance checked separately. Owner edits/reviews AlicanKiraz
  candidates; retain the standing owner acceptance of public Occam records.
  Preserve original targets and provenance alongside edits. Do not duplicate the
  existing80 or import any held-out/benchmark items or their rewrites.
- Target160 accepted training examples, pending review. Prioritize natural Turkish,
  meaning-preserving correction, grounded explanations, clarification and exact
  constraints. Reasoning remains optional for tasks that warrant it; do not add
  empty or artificial reasoning to simple questions. Establish separate development
  examples before another training comparison; keep the existing20 evaluation-only.
- Owner need not finish the remaining blind comparisons. Export the submitted
  subset and notes as partial diagnostic evidence; no forced additional annotation.
  See the dated [partial review report](../experiments/turkish-capability/lfm3-1.7b/PILOT80-OWNER-REVIEW.md).

Completed pilot milestones (2026-11-16): all100 owner reviews exported with edits,
80/20 split frozen, three authorized training corrections applied, native assistant
labels and optional reasoning verified, smoke/tiny-overfit passed, two independent
50-update SFT runs completed (only LR1e-4 vs2e-4 differs), and matched CPT/SFT
inference completed on holdout20, CETVEL100 and TurBLiMP1600.
See [pilot results](../experiments/turkish-capability/lfm3-1.7b/PILOT80-RESULTS.md).
This80-row pilot is not the final reusable general-coverage dataset or a release.

1. Owner grades the20 blind comparisons using correctness and instruction-following
   rubric; preserve both checkpoints and report paired outcomes. Automatic metrics
   show stopping recovery, while inspected answers still contain material errors.
2. Expand the reusable corpus in manageable reviewed batches targeting faithful
   edits/extraction, missing-context clarification, exact constraints, grounded
   explanations, and the previously missing coding/translation/multiturn coverage.
   Keep source provenance and resolve publication eligibility; no benchmark answers
   or test-derived rewrites enter training.
3. Establish a separate development set before more tuning; retain a fresh final
   test for the larger dataset. The existing20 must not become training data.
4. Freeze the broader reviewed dataset, then run the larger LFM3 SFT comparison.
   Evaluate a separately frozen thinking-enabled protocol; current inference
   disabled thinking and cannot answer whether it improves accuracy.
5. After stable SFT quality, collect DPO preferences. Keep MoE/text-diffusion pilots
   bounded, then prioritize Reflex-1 local decision models as planned.

## Sources checked for this plan

- https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT
- https://huggingface.co/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0
- https://huggingface.co/datasets/AlicanKiraz0/Turkce-Atlas-Instruct
- https://huggingface.co/datasets/AlicanKiraz0/Turkish-CoT-Instruct-Dataset
- https://huggingface.co/docs/trl/sft_trainer
- https://huggingface.co/docs/trl/dpo_trainer

Initial planning used source pages and repository guidance. CPT lineage and
full500 recovery are now established from local publication/recovery receipts.
Source quality and eligibility still require the next pinned audit.
Implementation follows dataset-guide.md, evaluation-guide.md, experiment-guide.md,
finetuning-playbook.md and reproducibility.md in this repository.
