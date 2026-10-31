# Dataset and evaluation plan

## Capability boundary

First train task-to-tests, not simultaneous planning, coding and tool use.
The planner is prompted or externally provided. Its explicit artifact contains
task IDs, dependencies, public interfaces, expected production files, target test
files, acceptance criteria and unresolved choices. One task can require several
production files while its teaching target is one complete pytest file.

Public company harness write-ups motivate explicit state and execution feedback;
they do not disclose a universal proprietary training recipe. Relevant sources:

- Anthropic, March 2026, planner/generator/evaluator and capability-dependent
  decomposition: https://www.anthropic.com/research/harness-design-long-running-apps
- OpenAI, structured review/repair/execution loop:
  https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- UTRL, revised March 2026, instruction-conditioned test generation and
  discrimination rewards, including Qwen3-4B experiments:
  https://arxiv.org/abs/2508.21107
- SWE-Stream, October 2026, executable task construction and successful trajectories:
  https://arxiv.org/abs/2610.20193

These motivate our design choices; they do not establish that 100 examples are
sufficient, that all work must use exactly one file, or that authored rationale is
equivalent to a frontier model's private reasoning.

## Diversity dimensions

| Dimension | Target coverage | Initial pilot |
|---|---|---|
| Surface | Pure library, CLI, HTTP API, worker/service | Library, CLI, analysis service |
| Behavior | Parsing, transformation, validation, querying, orchestration | Classification, weighted rules, numeric transformation, adapters, orchestration |
| State | Stateless, mutable state, filesystem, database | Configuration replacement, input preservation, temporary files |
| Dependency | None, injected collaborator, network mock, fake clock | None, provider mock, pandas/Plotly |
| Failure | Invalid input, missing data, timeout, partial failure | Invalid input/UTF-8, missing data, provider failure |
| Oracle | Concrete values, exceptions, state, interactions, invariants | Values, exceptions, input preservation, provider calls |
| Boundary | Empty/Unicode/date/numeric/order/size | Empty/Unicode/date/numeric/ties/order |
| Context | New module, feature extension, regression repair | New module against agreed contract |
| Depth | Isolated logic, module collaboration, HTTP/database integration | Unit and module/CLI integration |
| Feedback | Initial generation, actual failure diagnosis and repair | Initial generation only |

Gaps to prioritize next: HTTP contracts, database transactions, mutable-state
transitions, fake-clock scheduling/timeouts, async cancellation, feature extensions
and real repair feedback. Do not fill the dataset solely with more numeric or
regex variants because those are easy to generate.

## Size, grouping and source selection

- Target 100 distinct training contracts, approximately 15 development and 25 final
  evaluation tasks, with exact group counts frozen after source audit. These are
  planning targets, not already available data or a universal minimum for SFT.
- Inventory the existing seven training families first; there is no minimum
  repository count or ten-task-per-family cap. Those earlier numbers were planning
  preferences, not requirements. Keep repository, fork/upstream and near-duplicate
  behavior families in one role. Balance sampling so a large repository does not
  dominate. Add external projects only for actual behavior/context gaps.
- Existing pilot families (codelang-detect and cryptocurrency-analyser) remain on
  the training side; their use to design the format disqualifies them as a fresh
  independent holdout. Existing GitHub-insignia and slm_test_generation exclusions
  remain in force. Do not reuse previous benchmark instances as training targets.
- Use popularity/maintenance as discovery signals, not evidence of clear contracts,
  freshness or clean licenses. Pin actual revisions, dependency environments,
  source licenses and source-file hashes before authoring demonstrations.
- Candidate sources from the earlier search include schedule, python-dotenv,
  python-slugify and TinyDB. They are unselected leads, not audited or approved
  training sources. Avoid redistributing source-derived text before rights review.
- Extract behavior from public documentation/contracts; preserve transformations
  and authorship. For requirements-first tasks, do not reveal the implementation
  under test or existing solution tests in the model input.

## Acceptance and feedback

1. Validate the task contract and reference independently of model predictions.
2. Check target syntax, collection, meaningful successful and failing controls,
   passing reference execution and task-specific faulty-variant discrimination.
3. Run seeded orders where useful; a single-case suite cannot have distinct
   permutations and must not be claimed to have them.
4. Review expectations and useful behavior coverage; passing against one reference
   and killing targeted faults are supporting evidence, not semantic proof.
5. Measure complete native conversations, including reasoning and EOS, with no
   truncation. Also report actual supervised tokens and group diversity.
6. Preserve original model output and actual execution feedback before any repair.
   A repair turn inherits its source split and task identity. Never fabricate a
   tool trace to make a trajectory look realistic.
7. Do not teach weakening correct tests to accept incorrect code. Classify contract,
   fixture, infrastructure and implementation failures separately.

## Evaluation

Use a new baseline for the selected task contracts and final interface protocol.
Primary outcomes: requirement-correct expectations and useful discrimination of
verified faulty implementations, with invalid suites contributing zero usable
detection credit. Report reference passing, faults, failure categories, tokens and
latency separately. Preserve human/AI review provenance and all attempted tasks.

For downstream utility, keep the code generator unchanged. Compare requirements
alone with requirements plus frozen generated tests under a specified total
budget, and grade code with independent hidden checks. Report review and inference
cost; do not call self-generated-test passing sufficient correctness.

## Current todo

- [x] Freeze the initial task/artifact schema and first narrow training objective.
- [x] Reframe two existing training applications into eight task candidates.
- [x] Complete execution/fault/order checks and native token measurements.
- [ ] Semantically inspect the new task framing (AI-assisted review accepted).
- [x] Record GitHub metadata, pinned heads and declared license identifiers for eight source leads.
- [ ] Audit actual task suitability, environments/licenses and assign source-family roles before expansion.
- [ ] Expand task coverage and reach the selected train/dev/evaluation targets.
- [ ] Freeze inference/grading and run the untouched baseline.
- [ ] Verify labels and smoke/tiny diagnostics, then SFT and matched evaluation.

Source metadata snapshot: source-candidates.json. Seven of the eight leads have October 2026 head commits; schedule's recorded head is May 2024 and does not meet the current recency preference. This is repository-level activity only, not function creation or contamination evidence. No external lead has yet been assigned a split or yielded training examples.
