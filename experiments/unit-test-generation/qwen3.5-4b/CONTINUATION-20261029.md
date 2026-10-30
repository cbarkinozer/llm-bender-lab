> Active scope update, 2026-10-29: paper continuation paused. Complete the
> [quick ten-example thinking-SFT demo](exp-001-local-thinking-10/README.md),
> then reuse the task setup for GRPO. Historical research plans below are deferred.

# Requirements-to-tests: continuation initialization

Status: planned, 2026-10-29. This is a research branch of the owner's function-to-test study, not a claim that a second paper is complete or that novelty is established.

## Lineage and question

The earlier study asks whether tests generated from existing functions execute and meaningfully test behavior. This continuation changes the available evidence: an English requirement and approved public API replace the implementation. Retain the oracle/quality/smell taxonomy and failure accounting; establish a new baseline because the task distribution changed.

Immediate question: where does untouched Qwen3.5-4B produce incorrect, weak or incomplete tests from requirements? Training hypothesis, tested later: verified thinking-plus-pytest SFT improves requirement-faithful fault detection on separate task families. Downstream question, tested separately: do frozen generated tests improve independently graded code generation?

The existing paper repo remains read-only. Its single-step/two-step conditions are not thinking-off/on conditions. Low function-to-test scores motivate diagnosis but are not requirements-to-test baseline scores.

## Ordered work

1. Audit the ten draft contracts before observing Qwen outcomes. Record domain, dependency level, contract detail, target behaviors and ambiguity. These are synthetic development tasks, not a representative replication of the paper's library/repository distribution.
2. For each task, write a reference and independent contract checks, plus realistic faulty variants with concrete witnesses. Adjudicate disputed behavior before freezing inputs. Keep reference/grading material out of generation context.
3. Freeze task hashes, exact model/GGUF/runtime identities, prompt, thinking-on sampling and fixed token/time allowances. Run a bounded local smoke, then one unchanged attempt on each of ten tasks. No automatic repair or task replacement after observing failure.
4. Preserve every output, truncation and failure. Grade in the existing isolated Docker verifier. Present original suites in Argilla for owner review, then separately reveal execution evidence for adjudication.
5. Diagnose failures by family. Prepare separate training demonstrations targeting those families; include validated reasoning and pytest output. Do not train on the ten pilot tasks or near-duplicate variants. Maintain regression coverage for previously successful behavior.
6. Establish an independent family/repository-disjoint holdout before checkpoint selection. Run the unchanged baseline and SFT candidate with matched deployment settings. Ten development tasks alone support an engineering pilot, not broad statistical claims.
7. Only after Stage A is useful, compare direct code generation against requirements → frozen tests → code with matched total inference budgets and independent hidden implementation tests.

## Evaluation contract

Report counts with all ten attempted tasks as denominator: syntax/collection, correct-reference passing, requirement-faithful meaningful assertions, and detection of independently verified faulty variants. A suite rejecting the correct reference cannot earn usable fault-detection credit. Publish both unconditional detection (invalid suites contribute zero) and detection conditional on reference passing, with explicit variant and task denominators. Keep infrastructure failures distinct and visible.

Review expectation correctness, important behavior coverage, robustness, assertion strength, readability, conciseness and contextual smells using the earlier taxonomy. Static smells are review suggestions. More assertions or fewer smells alone do not establish useful tests. Paired task-level results matter more than a single aggregate on this tiny pilot.

For downstream implementation, frozen generated-test passing is diagnostic; hidden functional/regression tests determine code correctness. Report autonomous original suites separately from human-corrected suites and account for human review cost. Do not rewrite failing tests merely to accept generated code.

## Scope decisions

- Untouched Qwen3.5-4B, local Mac deployment, thinking enabled only for this pilot. Thinking off is optional later; this scope makes no universal superiority claim.
- Requirements → pytest is the immediate target. Full repository agents, downstream TDD, SFT and GRPO are later stages.
- Ten existing assistant-authored contracts remain drafts. Resolve ambiguity before final selection; do not describe them as validated or contamination-free.
- Keep Occam2 deferred. No GPU rental or training starts from this initialization.

## Completion evidence

Initialization is complete when the active README, pilot scope and task audit agree. Baseline readiness additionally requires executable reference/fault preflight and a frozen run manifest. No new inference or training result exists at initialization.
