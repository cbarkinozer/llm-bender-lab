# Compact app core suites — revision 02

## Current owner review

The owner now requests explicit human approval of all nine candidates. Use:
http://127.0.0.1:7900/dataset/6c3873ef-03f5-45d4-bafb-3dec9dda268f/annotation-mode

Each record includes seven required decisions: source relevance, input
sufficiency, coverage, expectation correctness, assertion quality, contextual
smells and overall approve/revise/reject/uncertain. Missing-context, missing-test
and evidence notes are available. No ratings are prefilled. Previous assistant
review and earlier datasets remain preserved; they are not human approvals.
See human-review-v01/GUIDELINES.md for the review instructions.


The wide requirement table has been replaced by stacked sections in the new Argilla result view. The owner waived mandatory review; assistant decisions and remaining gaps are recorded in REVIEW.md. No human annotations were submitted.

Review/result view: http://127.0.0.1:7900/dataset/9eec1313-018c-4885-aa7a-7f7dc38b5110/annotation-mode

## Executed test output sizes

- **GitHub-insignia**: 4,649 Qwen tokens; source files in `github-insignia/tests/`.
- **ghost-box**: 833 Qwen tokens; source files in `ghost-box/tests/`.
- **slm_test_generation**: 692 Qwen tokens; source files in `slm_test_generation/tests/`.
- **llm-bender-lab**: 1,019 Qwen tokens; source files in `llm-bender-lab/tests/`.
- **ReflexModels**: 847 Qwen tokens; source files in `reflexmodels/tests/`.
- **codelang-detect**: 743 Qwen tokens; source files in `codelang-detect/tests/`.
- **repo-context**: 1,154 Qwen tokens; source files in `repo-context/tests/`.
- **cryptocurrency-analyser**: 1,136 Qwen tokens; source files in `cryptocurrency-analyser/tests/`.
- **miniature-llms**: 692 Qwen tokens; source files in `miniature-llms/tests/`.

**Total: 11,765 tokens across nine separate outputs; 108 passing parametrized cases.** Counts include all test files, fixtures and pytest configuration in the output payload. They exclude request, clarification/interface, teacher reasoning and native chat framing. Largest output is 4,649 tokens. Do not choose a training maximum until complete messages are serialized. 16K appears ample for these current suites; 8K may fit after measuring actual reasoning and interfaces.

## What is complete

- Nine executable compact candidate suites and precise token measurements.
- Concrete numeric/result/state/exception oracles; fresh examples exclude retained paper/codelang benchmark fixtures.
- Short reviews of ambiguous scope, missing context, unsupported promises and requirements still lacking tests.
- Table-free Argilla display with plain-text test files and actual execution logs.

## What is NOT complete

These are not nine certified whole-app acceptance suites. The largest gaps are provider/lifecycle integration in Ghost-box; execution/aggregation in the study pipeline; generic run orchestration in the fine-tuning lab; CLI/UI privacy behavior in repo-context; offline/error handling in the crypto app; and composed causal-model/checkpoint/training behavior in miniature-llms. See each review.md for coverage by requirement. The miniature causal-attention/RoPE axis mismatch is an implementation issue, not a failed current RMSNorm/RoPE suite. No application source was changed by this bundle step.

Passing compact suites must not be relabeled all-requirements coverage. Assistant-selected defaults are review decisions, not historical owner answers; they must be visible in finalized model inputs. Existing public API names need an explicit interface agreement. No teacher reasoning or final SFT records are approved yet, and train/evaluation app roles remain unassigned.

## Quality review

Core oracles check expected values, full tensor/data-frame results, state preservation, error contracts and real instrumented reachability. Missingness checks appropriately use None/empty-state checks; a suite should not be judged strong merely because every syntactic assert is equality. Multiple assertions in a coherent scenario are not automatically Assertion Roulette. No external service is contacted by the core fixtures; the lab uses a cached local tokenizer. Helpers such as torch.testing.assert_close and assert_frame_equal are meaningful numeric oracles even when a static classifier reports UNKNOWN.

The GitHub suite includes both initial and follow-up regression tests; more deduplication may be possible before selecting its final teaching target. Some copied context/comparator checks use existing helper boundaries and textual formatting; these are candidate tests, not evidence that we have already achieved implementation-independent whole-app TDD. App-level gaps and smell/semantic reviews remain explicit rather than hidden by a passing suite.

## Run

```sh
/Users/cbarkinozer/Documents/llm-bender-artifacts/occam-gguf-20261026/.venv/bin/python scripts/evaluation/run_tdd_core_suites.py
```

Run from the llm-bender-lab repo. The runner sets per-repo imports, offline flags, removes credentials, preserves execution logs outside Git, and leaves app source untouched. It uses already prepared local environments and the isolated audit dependency directory; this is not a lockfile replication of every historical app environment.

Execution receipt and hashes: `token-and-execution-report.json`. Raw run history remains under `/Users/cbarkinozer/Documents/llm-bender-artifacts/thinking-tdd/core-suites-v02/`. Do not execute model-generated tests through this trusted-suite runner; those still require sandboxed execution.
