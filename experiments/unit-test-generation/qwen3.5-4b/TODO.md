> Current, 2026-10-31: review revision 05 at http://127.0.0.1:7900/dataset/ae9c43c9-54ea-4602-9d4d-56741869b59a/annotation-mode.
> HTML display, meta category, process/name/numbering checks and preservation
> probes are complete. Human approval and the unchanged next-step baseline/SFT
> workflow remain pending. Older status blocks below are historical.

> Current, 2026-10-31: shared-format cleanup complete in app-core-v04.
> Review http://127.0.0.1:7900/dataset/7500c36b-0971-41bd-91c5-765d6e7add5e/annotation-mode; prior annotations are preserved.
> Record-specific data annotation is separate. Freeze approved data, then run the
> untouched thinking-on baseline before short SFT. No training has started.

> Active scope update, 2026-10-29: paper continuation paused. Complete the
> [quick ten-example thinking-SFT demo](exp-001-local-thinking-10/README.md),
> then reuse the task setup for GRPO. Historical research plans below are deferred.

# Active whole-app thinking-SFT demo — 2026-10-30

- [x] Preserve old ten-task function pilots and all previous reviews/results.
- [x] Create framing-B v03 targets with fixed decisions/interface/map/tests/manual sections and separate concise rationale.
- [x] Add missing backend acceptance contracts with separately disclosed reference facades; keep original apps unchanged.
- [x] Validate 142 cases and 57 targeted faults covering all 53 core requirements.
- [x] Run three distinct seeded test orders per suite and verify full sequences <=8K (max 6,934).
- [x] Reserve GitHub-insignia and the entire paper repo from training; propose seven disjoint training repos.
- [x] Separate AI reviewer audits two records; preserve revise findings and resolved re-review. This is not human agreement.
- [x] Publish anchored Q1–Q8 form, split Q4, fixed defects, confidence, blocking issues and decision rules.
- [ ] Owner reviews nine in [current Argilla](http://127.0.0.1:7900/dataset/f7c79cb7-8943-4281-98d1-4e9128a2b529/annotation-mode); resolve actual blockers before exporting training rows.
- [ ] Complete/disclose pending app delivery/live checks in each record; backend passes do not certify original UI/CLI wiring.
- [ ] Obtain a second human rating on two records if independent human agreement is wanted; currently no paired human labels.
- [ ] Freeze approved pilot/split and check provenance/near-duplicates; paper benchmark instances stay outside training.
- [ ] Run untouched thinking-on baseline with grading aligned to each emitted interface; freeze same policy/budgets before and after SFT.
- [ ] Verify native labels and loss masking, run short SFT, repeat held-out app and fixed paper transfer evaluation.
- [ ] Save adapter/results/lessons and move to GRPO. Do not scale data before the approved pilot and baseline.

Historical checklist follows; checked historical items do not imply pilot readiness.

# Python unit-test generation TODO

## Active next steps — requirements-first owner refinement

- [ ] Revise the review display to explicitly show Python, pytest, the original
  generation instructions and tool permissions; preserve current records/responses.
  The existing model already received Python/pytest in both system and task prompts.
- [ ] Version a structured review schema separating requirement text, clause IDs,
  known ambiguities, verified API facts and generation instructions. Keep model
  identity and execution evidence outside the initial review view.
- [ ] Add per-test requirement alignment/ambiguity, clause links and oracle-site
  evidence alongside suite ratings; preserve the owner's existing smell taxonomy.
  Add concrete rubric calibration examples and a separately saved repaired suite.
- [ ] Record owner-plus-assistant review as assisted human adjudication. Preserve
  initial owner judgments where available; do not claim independent inter-rater
  agreement from collaborative review. This sample has now had external feedback.
- [x] Download/hash DeepSWE using project `.env` credentials; complete descriptive EDA.
- [x] Record [requirements-first protocol](REQUIREMENTS-FIRST-PROTOCOL.md) and
  direct-code / prompted-TDD / SFT-TDD / SFT+GRPO comparison order.
- [x] Prepare 20 provisional task packets from distinct repositories, excluding
  the mislabeled TypeScript task and keeping hidden artifacts out of prompts.
- [x] Restart local runtimes and recheck the trusted Docker isolation probe.
- [x] Run and inspect one bounded requirements-to-tests Pi generation smoke;
  original TOML suite failed collection and contains requirement contradictions.
- [x] Validate public fixture examples on the pinned original source and calibrate
  reference grading: 60 hidden + 964 regression tests pass.
- [x] Confirm the TOML reference defect using equivalent inputs and a minimized
  counterexample; quarantine reference-based scoring without changing the dataset.
- [x] Freeze [Stage A v01](exp-000-baseline/requirements-pilot/STAGE-A-V01.md)
  settings and per-task readiness/hash checks; capture actual inference requests.
- [x] Validate Mashumaro reference (72 feature + 30,008 regression tests), freeze
  public context, and run the first single-attempt v01 generation.
- [x] Prepare initial Argilla quality review without model/execution hints;
  verify repeated import preserves the record.
- [ ] Obtain owner's initial quality/importance/smell annotations; preserve them
  before separate evidence-assisted adjudication.
- [x] Add guarded implementation emission and independent hidden/regression grading;
  direct model implementation passed 4/60 feature and 964/964 regression tests.
- [x] Fix Pi/server context mismatch and document Pi's 4,096-token reserve.
- [ ] Obtain an accepted original generated suite; latest thinking diagnostic is 16/20
  passing, rejected at Stage A, with owner quality ratings still pending.
- [ ] Review requirement alignment/importance and prior quality taxonomy; freeze tests.
- [ ] Implement protected Stage B with immutable tests and independent hidden grading.
- [ ] Run paired direct-code and prompted-TDD development episodes before SFT.
- [ ] Prepare separate validated SFT training demonstrations; DeepSWE is evaluation only.

Earlier staged entries below remain background; the current protocol supersedes
old test-only permissions, 10-task counts and GRPO-before-SFT sequencing.

Updated 2026-10-17. This is a staged work plan, not an executable training
configuration. Benchmark, reward, budgets and training method remain undecided.
See [design notes](DESIGN-NOTES-20261005.md) for owner decisions and sources.

Current direction: [20-task baseline → GRPO → independent SWE transfer](RESEARCH-PLAN-20261017.md).
The first 20 ordinary unit-test tasks are development data. Older 10-task pilot
entries below now refer to this 20-task pilot. Historical fixtures remain diagnostics.
Task-level freshness and source selection remain open. Freeze and measure a
separate broader-SWE baseline before training. Broader SWE is now in scope for
transfer evaluation; broad coding-agent training remains deferred.

Accepted [improvement priorities](IMPROVEMENT-PLAN-20261010.md): next verify
smoke-task contracts, finish protected per-task Pi execution, then generate a
development pilot and import original outputs/evidence into Argilla. Follow
this order autonomously; request input only for decisions requiring the owner.

## 0. Decisions and experiment boundaries

- [x] Select Python/pytest test generation; production code remains read-only.
- [x] Select Mac mini M4/24 GB, Pi and llama.cpp with 4-bit GGUF deployment.
- [x] Close Occam/Turkish SFT as the previous project; use untouched Qwen3.5-4B.
- [x] Locate owner's newer paper and early thesis containing rubric and smells.
- [x] Record that pytest success alone is insufficient; human-reviewed quality is central.
- [x] Update domain README, baseline README/config and Mac handoff to match these refinements.
- [ ] Define primary research question: can quality-focused post-training improve
  assertion quality and test usefulness on unseen tasks in the actual Q4 deployment?
- [ ] Separate ordinary unit-test generation from issue-reproduction testing;
  document which task mode each benchmark measures and avoid pooling unlike scores.
- [ ] Keep each training hypothesis in its own experiment; preserve baseline artifacts.

## 1. Reproducible Mac environment

- [x] Observe M4/24 GB, macOS 26.5.1/build 25F80 and Node v26.3.1.
- [x] Observe installed Pi 0.80.1; npm latest was 1.0.3 on 2026-10-05.
- [x] Recheck latest stable Pi when installing; install an explicit version,
  then record installed version, package integrity, dependency lock and Node version.
- [ ] Inspect existing Pi configuration/extensions without exporting credentials.
- [x] Locate existing model artifacts and llama.cpp installations before downloading.
- [x] Install Homebrew llama.cpp with Metal; record commit, bottle and binary identity.
- [x] Create project Python environment; pin Python 3.11.15, pytest 8.4.2 and initial dependencies.
- [x] Check available RAM, disk capacity and Docker ARM64 support; Docker Desktop started.
- [x] Write an environment manifest and commands to recreate the setup.

Deliverable: environment manifest plus verified Pi and llama-server executables.

## 2. Model artifact and Pi integration

- [ ] Pin the exact original Qwen3.5-4B model/tokenizer revision; use the
  instruction/thinking checkpoint, not a raw Base checkpoint or Occam adapter.
- [ ] Select a trusted Q4 GGUF artifact; identify exact variant rather than
  treating all 4-bit quantizations as equivalent.
- [ ] Record GGUF repository, file, revision, SHA256, source model revision,
  conversion/quantization provenance and license.
- [ ] Record effective chat template, tool schema and tool-call parser.
- [ ] Configure Pi's local provider for llama-server; preserve redacted config.
- [ ] Verify read, test-file write and pytest execution tool calls end to end.
- [ ] Verify thinking off/on at server/template level using raw requests and outputs.
- [ ] Check reasoning handling across tool turns, EOS, malformed tool calls,
  truncation and repeated actions.
- [ ] Measure bounded-context memory, prompt latency and generation throughput.
- [ ] Select context and total episode budgets from measurements, leaving memory
  for execution and Argilla; initially load one model at a time.
- [ ] Pin the working deployment recipe before benchmark generation.

Deliverable: reproducible model/server/Pi config and integration smoke traces.

## 3. External benchmark selection and freshness audit

- [x] Inspect the author's local paper repository and pin reuse audit commit;
  oracle regression suite: 100 passed. See [reuse audit](PAPER-PIPELINE-REUSE.md).
- [ ] Adapt paper collection/extraction/oracle helpers through pinned lab adapters,
  preserving the paper's frozen outputs and correcting function freshness checks.
- [x] Build read-only pinned paper adapter, audit 300 rows and export ten
  historical smoke fixtures with preserved interfaces/content-based IDs.
- [x] Verify all ten smoke references import in bounded containers; behavioral
  contracts remain to be independently verified. Twelve adapter tests passed.

- [ ] Compare SWT-Bench, newer test-generation benchmarks and dated external
  task sources such as SWE-rebench; record fit, maturity, access, license and costs.
- [ ] Verify whether any external benchmark meets all requirements:
  Python tests, trustworthy reference evidence and genuinely fresh source tasks.
- [ ] Seek an official Qwen3.5-4B training cutoff; record evidence or explicitly
  mark it unknown. Do not invent a cutoff from model self-report.
- [ ] Pin original model release/revision date as a fallback temporal boundary.
- [ ] Audit actual issue, PR and relevant code creation/history dates;
  dataset publication dates alone do not establish freshness.
- [ ] Check older versions, copied problems, fixes and near-duplicate families.
- [ ] Preserve source IDs, repository commits, dates, URLs and per-source licenses.
- [ ] Determine whether to use an unchanged external benchmark for comparability
  plus a separately labeled fresh-task adaptation for temporal evidence.
- [ ] For repair-to-test adaptations, define visible inputs and private grading
  code; hide gold tests/fixes and solution-bearing issue text from model prompts.
- [ ] Keep original benchmark scores separate from custom rubric scores and adaptations.
- [ ] Audit environment compatibility on ARM64; record emulation or remote
  execution if required and keep execution conditions stable across models.
- [ ] Publish a benchmark-selection rationale before looking at model outcomes.

Deliverable: benchmark decision and provenance/freshness manifest; no unsupported
claim that a dataset is contamination-free.

## 4. Task validation and grouped splits

- [ ] Define inclusion rules: deterministic, clear contract, bounded dependencies,
  executable reference implementation and inspectable expected behavior.
- [ ] Independently verify each task/environment and developer reference tests.
- [ ] Define exclusion rules and record exclusions before model generation.
- [ ] Stratify difficulty, dependency level and behavior categories without
  changing the task distribution after seeing model results.
- [ ] Allocate proposed 10 pilot tasks and 20 separate development tasks;
  decide final holdout size, potentially 100, based on review capacity.
- [ ] Create a separate training pool; holdout examples must not seed training,
  teacher generation, reward calibration or hyperparameter decisions.
- [ ] Split by repository/source/problem family and near-duplicate group;
  record split seed, membership, grouping rules and dataset hashes.
- [ ] Freeze task contracts, approved context, reference code and grading variants.
- [ ] Store gold tests, buggy variants and grading identities outside agent access.
- [ ] Document that frozen holdout baseline outputs are sealed from method
  development; inspect development results first. If holdout feedback steers
  changes, introduce a fresh final holdout or label the old one development.

Deliverable: versioned pilot/dev/train/holdout manifests and validated environments.

## 5. Protected execution and verifier

- [ ] Build isolated per-episode workspaces with writable generated-test directory,
  read-only production code and protected grading data.
- [ ] Enforce no network, secrets or home mounts; allowlist tools and test commands.
- [ ] Apply CPU, memory, process, filesystem and wall-time limits; terminate
  descendants and clean workspaces after each episode.
- [ ] Independently verify production hashes and permitted file diffs.
- [ ] Check syntax, imports, collection, non-empty tests and actual assertions.
- [ ] Instrument oracle reachability for bare assert, unittest methods,
  exception/warning contexts and mock interaction checks.
- [ ] Preserve separate execution, runtime non-trivial gate and human quality outcomes.
- [ ] For reproduction tasks, verify meaningful failure on buggy code and success
  on fixed code; distinguish assertion failures from import/environment failures.
- [ ] For mutation analysis, validate behavior-changing mutants and freeze
  equivalent/invalid-mutant exclusions, timeout policy and denominators.
- [ ] Report mutation evidence across all tasks as well as passing suites to
  expose survivorship bias; keep coverage a supporting diagnostic.
- [ ] Test verifier against empty tests, skipped/xfail tests, dead assertions,
  assert True, wrong strong assertions, swallowed errors and unconditional failure.
- [ ] Test source edits, grader access, forged exit reports, target monkeypatching,
  mutant-specific checks and deliberate resource exhaustion.
- [ ] Ensure grading uses independently observed execution rather than agent claims.

Deliverable: verifier with adversarial fixtures, reports and documented limitations.

## 6. Paper-derived rubric and test smells

- [x] Extract a development rubric from the newer paper with source file hashes
  and provenance; retain the early thesis as supplementary historical material.
- [ ] Define TRIVIAL, WEAK, STRONG and UNKNOWN with examples and SUT provenance.
- [ ] Separate oracle specificity, semantic correctness and runtime reachability.
- [ ] Preserve 1–5 dimensions: robustness, assertion strength, readability,
  conciseness; specify not-rateable and confidence fields.
- [ ] Clarify robustness relative to the valid contract: do not reward arbitrary
  None/type-error cases when the specification does not require them.
- [ ] Document smell definitions: Assertion Roulette, Eager Test, Mystery Guest,
  Magic Number Test, Obscure Test, Lack of Cohesion, Conditional Test Logic,
  External Dependency, Unverified Action, Trivial Assertion, Duplicated Setup.
- [ ] Add examples of false positives: pytest diagnostics without custom messages,
  coherent multi-call tests, controlled fixtures, useful parameterization and loops.
- [ ] Treat static smell detections as suggestions requiring contextual review.
- [ ] Define overall acceptance/preference rules and any severe-defect gates;
  do not silently equate a clean-looking suite with useful behavior coverage.
- [ ] Decide primary quality outcome and aggregation before final evaluation;
  keep rubric dimensions and execution rates visible even if using a composite.
- [ ] Recalibrate classifiers and judge on development data; historical paper
  validation is not automatic validation for new tasks or new model outputs.

Deliverable: frozen rubric, annotation instructions and calibration evidence.

## 7. Argilla human review and LLM collaboration

- [x] Create separate local Argilla deployment; pin server/client 2.8.0 and image digests
  and establish a Mac-compatible startup workflow without overwriting old reviews.
- [ ] Build records showing task contract, source context, generated suite,
  oracle locations/reachability, execution results and optional grader evidence.
- [x] Create empty development schema with rubric scores, oracle labels, smell evidence,
  correctness, overall preference, confidence and review notes.
- [ ] Hide model condition/identity and judge suggestions during initial review;
  randomize order reproducibly and reveal suggestions after independent rating.
- [ ] Preserve failed and empty outputs as reviewable outcomes; use appropriate
  not-rateable labels rather than silently discarding them.
- [ ] Keep original model output, judge proposals, initial human judgment,
  adjudication and human repairs in separate fields/artifacts.
- [ ] Pin judge model/version, prompts, sampling and code context; record token/cost use.
- [ ] Use swapped pair order and repeated controls to check position bias and
  reviewer/judge self-consistency; inspect verbosity and style preference.
- [ ] Personally review every evaluation output; estimate workload before freezing
  task count (100 tasks × two thinking conditions = 200 baseline suites).
- [ ] Calibrate judge against human development ratings and analyze disagreements.
- [ ] Report single-reviewer limitations; optionally seek independent ratings
  if making broader inter-rater reliability claims.
- [ ] Export ID-keyed snapshots with hashes and back up database/annotations.
- [ ] Separate train/development review datasets from sealed final evaluation.

Deliverable: usable Argilla dataset, durable review exports and judge calibration.

## 8. Freeze inference protocol and run baseline

- [ ] Freeze semantic prompts, native templates, Pi system instructions and tools.
- [ ] Freeze sampling, seeds, context, per-turn and total episode token budgets,
  wall-time, tool-call and repair limits; thinking tokens count toward allowance.
- [ ] Define one-shot generation versus one agent episode with repairs. Label
  episode success explicitly rather than conflating it with single-shot Pass@1.
- [ ] Define invalid output, timeout, infrastructure failure and rerun policies.
- [ ] Freeze primary matched-budget thinking off/on comparison; larger-budget
  reasoning runs are separate conditions.
- [ ] Run 10-task pilot; fix infrastructure and grading faults on pilot data only.
- [ ] Run development comparison, review trajectories and calibrate rubric/judge.
- [ ] Freeze final config and hashes; run paired holdout baseline when ready,
  preserving outputs without using them to develop the training recipe.
- [ ] Save raw requests/responses, rendered prompts, tool traces, code diffs,
  grader reports, tokens, memory, latency, termination and every failure.
- [ ] Optionally add a pinned 9B Q4 reference or non-LLM comparator in a separate
  condition if cost/review capacity permit.
- [ ] Analyze development correctness, quality dimensions, smells, detection,
  tool reliability and resource use; use grouped paired uncertainty estimates.

Deliverable: immutable baseline artifacts and development diagnosis; sealed
holdout baseline evidence for the eventual final comparison.

## 9. Choose training method and reward

- [ ] Inspect training/development success rates and within-task reward variation.
- [ ] Decide direct GRPO versus a small SFT warm-up for demonstrated tool/format
  deficits; SFT is not an automatic prerequisite.
- [ ] Consider DPO if reviewed preference pairs offer a cleaner initial learning
  signal; keep it a separate experiment from GRPO.
- [ ] State the GRPO hypothesis and intended quality improvement explicitly.
- [ ] Define trusted execution gates plus human-calibrated quality reward;
  avoid pytest-pass-only rewards and arbitrary smell-count penalties.
- [ ] Select reward components/weights on train/dev data, with versioned rationale.
- [ ] Validate reward ordering on intentionally strong, weak, misleading and
  smelly suites; inspect judge exploitation and reward disagreement.
- [ ] Specify whether reward is a calibrated LLM judge, learned reward model or
  other mechanism; human evaluation need not occur inside every training rollout.
- [ ] Separate training reward judge from final human evaluation; consider an
  independent final judge to reduce evaluator-specific optimization.
- [ ] Freeze reward thresholds, missing/unknown-label handling and termination rules.

Deliverable: training-method decision and validated reward specification.

## 10. GRPO stack feasibility and small pilot

- [ ] Verify current framework support for Qwen3.5 architecture, native thinking,
  multi-turn tools, LoRA and deployment export; pin compatible dependencies.
- [ ] Verify training uses the intended original model revision. Local frozen
  GGUF rollouts are not automatically on-policy GRPO training samples.
- [ ] Reproduce the task/tool contract in training runtime; document unavoidable
  differences from Pi and verify Pi deployment behavior after training.
- [ ] Inspect action masks so tool results/environment text are context,
  not supervised or optimized assistant actions.
- [ ] Validate old-policy log probabilities, rollout/update linkage, group
  advantages, variable lengths, truncation and reasoning/action token accounting.
- [ ] Estimate GPU memory, rollout/update throughput, judge expense and total cost.
- [ ] Set compute, regression and stop budgets before selecting/renting hardware.
- [ ] Create complete experiment config, seed/version manifest and recovery plan.
- [ ] Run reward and trajectory smoke checks, then a tiny training diagnostic;
  investigate all-zero/identical rewards before a longer run.
- [ ] Train one conservative LoRA GRPO pilot; monitor quality components,
  execution validity, KL/drift, repetition, entropy, tool errors and actual cost.
- [ ] Select checkpoint on development results only; preserve negative results.

Deliverable: recoverable pilot, development comparison and selected checkpoint.

## 11. Export and final Mac evaluation

- [ ] Validate adapter behavior against the correct original revision.
- [ ] Merge/export with pinned tools; validate before quantizing.
- [ ] Convert to GGUF using the same intended Q4 recipe as baseline and record hashes.
- [ ] Verify chat template, thinking mode, tool parser and numerical/export behavior.
- [ ] Re-measure Mac memory, latency and throughput on the exported artifact.
- [ ] Run selected candidate on unchanged holdout under frozen Pi protocol.
- [ ] Review all candidate outputs in Argilla blind alongside preserved baseline
  outputs; keep this review out of further recipe/checkpoint selection.
- [ ] Report paired quality improvements, execution/runtime-oracle rates,
  smells, detection, resources, uncertainty and regressions on all tasks.
- [ ] Distinguish training gains from thinking budget, model size, runtime or
  quantization changes; do not claim broader gains from a changed protocol.
- [ ] If final results motivate another experiment, use development evidence
  and a fresh final holdout when prior test feedback has influenced decisions.

Deliverable: actual Q4 deployment evaluation and defensible answer to the hypothesis.

## 12. Reproducibility and publication

- [ ] Update experiment README/config/results, domain registry and handoff consistently.
- [ ] Archive manifests, rubric, dataset provenance, review snapshots, raw counts,
  failures and scripts; keep large weights outside Git and credentials out of artifacts.
- [ ] Record model, benchmark, runtime, judge and training revisions and file hashes.
- [ ] Publish comparisons with explicit task modes and contamination limitations.
- [ ] Separate observed measurements from proposed steps and exploratory analyses.
- [ ] Check source/provider redistribution and training permissions before releasing data.
- [ ] Publish selected adapter/GGUF and cards only after export/deployment verification.
- [ ] Finish the Turkish blog separately; it is not a prerequisite or RL data source.

## Deferred

Owner learning sequence (2026-10-17): complete the current unit-test/TDD study
through an actual GRPO/RL training and evaluation cycle, then gain practical
experience with MoE and text-diffusion fine-tuning. Only after these stages,
consider spatial reasoning or further phases of earlier model projects. Spatial
reasoning is an idea backlog item, not authorized active implementation.

- [ ] After GRPO, MoE and text-diffusion practice, revisit text-based spatial
  reasoning benchmarks and small-model post-training. Investigate the reported
  Astra ARC-AGI-3 result and special harness: verify the exact score, evaluation
  conditions, tool access and inference budget before drawing conclusions about
  model-only spatial ability. Consider harness experiments as a separate variable.
- [ ] MLX local training/runtime comparison as a separate learning exercise.
- [ ] After the current GRPO/RL study, try local 4B parameter-efficient fine-tuning
  on the Mac mini M4/24 GB. Check current official Unsloth Apple Silicon support
  separately from MLX/third-party integrations; measure memory, speed and export.
  Train using a supported training representation, then test MLX and GGUF deployment.
- [ ] Identify the exact model/release meant by the owner's "reflex models new
  version" before selecting it for a simpler local fine-tuning exercise.
- [ ] After GRPO/RL, explore text-diffusion fine-tuning as a separate experiment.
- [ ] After GRPO/RL, explore mixture-of-experts fine-tuning as a separate experiment;
  check total parameter memory and architecture support, not just active parameters.
- [ ] 9B-to-4B verified trajectory distillation as separate SFT research.
- [ ] Multi-language/multi-harness transfer after one validated Python workflow.
- [ ] Full coding/bug-fixing agents, production edits and Occam v2.

## Review v0.3 implementation (2026-10-17)

- [x] Publish a separate review format showing Python/pytest, exact generation instructions, clause IDs, ambiguities, per-test templates and rubric examples; preserve older reviews.
- [x] Select single-generation Pass@1; preserve original outputs and report execution and runtime non-trivial gates separately.
- [ ] Collect owner-assisted calibration in v0.3 and separately archive any repaired suite and evidence-assisted decisions.
