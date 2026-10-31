> Active review fixes: [REVIEW-FIXES.md](REVIEW-FIXES.md). Planning v04 fixes shared-file ordering; current preview is intent-only-preview-v02 and baseline packet is baseline-reliability-v03. Counts are unchanged. Older revision descriptions below are preserved history.

> Current content review: [CONTENT-REVIEW.md](CONTENT-REVIEW.md). Active planning/decision revisions are v03. Source implementation is excluded from model inputs and targets; audit columns are excluded by an explicit export allowlist. Counts remain 95 total / 78 train-family candidates. Training and inference have not run.

# Reliability preparation and quality audit

## Completed preparation

- Statically inspected all 58 test candidates for recognizable oracles, disabling markers, broad expected exceptions, tautologies, real sleeps and patch sites. Flags are triage, not automatic semantic judgments. Numeric and interaction assertions count as real oracles.
- Confirmed one concrete weakness: the preflight task accepted an implementation that rejects every input. The original four cases passed that fault. Added a valid-data/backend control in a new revision: five reference cases pass, both targeted faults are detected, and three shuffled orders pass. Original records/logs remain intact.
- `candidate-index-v02.json` activates the replacement. The current set remains **58 test candidates (50 train / 5 development / 3 holdout)**; the revised row does not increase the count. `quality-audit-v01/current-test-candidates.jsonl` is the materialized current selection. Earlier audit inputs remain unchanged.
- Authored 22 separate reliability decision drafts: **12 clarification and 10 test-integrity cases**, split **15 train / 3 development / 4 holdout**, inheriting existing source-family roles. These are not additional pytest tasks or new independent repositories. All fit 8192 native tokens (maximum 261). Training eligibility remains false pending review.
- Prepared 17 baseline requests: 8 test-generation, 2 planning, 4 clarification and 3 integrity decisions. Model-facing files exclude target answers. Scoring references and a proposed rubric are separate. Development and final holdout results must remain separate.
- Six new regression tests pass: assertion-audit behavior, held-out request isolation, ask/proceed and legitimate-test-correction controls, and replacement without row-count inflation. The revised preflight reference and fault checks also pass.

## What the decision examples teach

Ask when an unresolved choice changes observable behavior: return baselines, fallback conditions, secret/inclusion conflicts, or an undefined latency target. Proceed when the contract already specifies behavior; fixture names and internal implementation preferences do not require user approval. Questions should be targeted, answerable and tied to a downstream acceptance decision.

Preserve agreed behavior under pressure to make tests green. Cases address weakened assertions, mocking away tested logic, skipped tests with false success reports, fixture-name hardcoding, unit success despite integration failure, and confusing a clean linter with functional correctness. Two positive counterexamples explicitly correct wrong test expectations, preventing a blanket rule that tests can never change.

These are authored decision demonstrations, not real tool-use traces, proof of resistance to cheating, or evidence that the starting model lacks these abilities. They stay outside the test-only SFT recipe.

## Scope and integration

The existing controller-routing and cache-routing tests use injected collaborators appropriately for their selected contracts. They do not verify a composed application. Add component integration at real module boundaries and user-facing acceptance checks: parse CLI arguments through actual controllers; compose repository reading/filtering/rendering with a temporary checkout; compose cache filesystem behavior with a controlled transport; compose HTTP request building with a local/mock transport. Keep remote-service smoke tests separate from deterministic integration.

Execution/tool training is a later track. Retain actual command, exit code, output, environment identity, proposed diagnosis, justified patch and rerun results. Never invent execution traces. Environment repair, dependency conflicts, replanning, refactoring and latency checks should be added when measured baseline failures justify them. Performance requirements must specify workload, environment, metric and bound; avoid arbitrary wall-clock unit thresholds.

A linter or SonarQube contributes quality signals but is not the functional grader. Do not auto-fix by suppressing tests, changing public contracts, or excluding failing files. Protected acceptance tests and fault probes remain independently maintained. Legitimate oracle changes require evidence against the agreed requirement and a recorded reason.

## Baseline status

**Not run.** `baseline-reliability-v01` contains the requests, references, response template and rubric. Its protocol deliberately leaves backend, decoding, precision, batching and seeds unset until a runtime is configured and the protocol is frozen. The workspace has tokenizer assets but no downloaded model weights; the machine reports a GTX 1650 with about 4 GB VRAM. No weights were downloaded and no inference or training was started. The packet can be taken to the model runtime without sending reference answers to the model.

Use the pinned starting model and native thinking template. Record effective generation settings, backend, raw outputs and environment. Execute generated code only through the protected untrusted-code path, not the trusted host fixture runner. Score correctness and format separately; require evidence for AI-judge ratings and report critical integrity failures separately rather than hiding them in an average.

## Review files

- [22 reliability drafts](reliability-pilot-v02/review-examples.txt), separated by ----.
- [Proposed baseline rubric](baseline-reliability-v01/rubric.json).
- [Baseline requests without reference answers](baseline-reliability-v01/requests-for-model.txt).
- [Concrete audit findings and evidence](quality-audit-v01/adjudication.json).
- [Revised preflight example](quality-preflight-v01/share/task-test-quality-preflight-v01.txt).

Next: AI-assisted review of the new decisions/plans and remaining test semantics, native-label audit, protocol freeze, then real starting-model evaluation. Keep planning/reliability additions as separate candidate tracks and compare mixtures only in a separately defined experiment.
