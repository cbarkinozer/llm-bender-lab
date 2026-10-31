# Dataset profile and semantic-overlap review

Open [the interactive offline dashboard](dataset-profile-v02/dashboard.html) to filter records by track, split, family or domain. [The figure](dataset-profile-v02/dataset-overview.svg), [per-record CSV](dataset-profile-v02/records.csv), and [full statistics JSON](dataset-profile-v02/summary.json) are also available. No training data, splits or capability mixture changed.

## Inventory and scope

95 candidates: 58 test generation, 15 app planning, 22 clarification/integrity. Training-family candidates are 50 / 13 / 15 = 78; development has 9 and final holdout 8 across tracks. These are not 95 independent applications: there are 11 source families, 9 training families and just one development family (Posting) and one final holdout family (ddgr). Four planning records are narrower variants of an existing family.

All generated test artifacts are Python. Planning/decision records are structured text, so cyclomatic complexity is **not applicable** to them. Repository implementation is never a model input or target. A separate, optional reference-module profile is audit-only and saves metrics/hashes, not implementation bodies.

## Token lengths: current native template and audited loss mask

Mean +/- population standard deviation. Full tokens include prompt and target; supervised tokens are positions actually included in the audited assistant loss. Percentiles and sample standard deviation are saved in summary.json.

| Training-candidate track | Rows | Full tokens mean +/- std | Supervised tokens mean +/- std | Full max |
|---|---:|---:|---:|---:|
| Test generation | 50 | 1837.2 +/- 669.9 | 345.3 +/- 158.1 | 2873 |
| Planning | 13 | 3757.8 +/- 794.2 | 3522.0 +/- 783.8 | 5328 |
| Clarification/integrity | 15 | 245.6 +/- 18.5 | 122.2 +/- 7.1 | 284 |
| All training candidates | 78 | 1851.2 +/- 1222.6 | 831.9 +/- 1254.3 | 5328 |

Across **all 95 candidates**, full mean/std is 1657.0 +/- 1234.3 and supervised mean/std is 771.7 +/- 1199.4. Evaluation target tokens are measured for this audit only; they do not enter training exports.

Training totals: 144394 full tokens, 64885 supervised and 79509 ignored. Median training sequence length is 1972; p95 is 3962. Median supervised length is 292.5; p95 is 3802.4. The mixture is strongly skewed, so the combined average hides three different distributions.

If every training row is used once, supervised exposure is **70.6% planning, 26.6% tests, 2.8% decisions**. Merely concatenating 78 records would prioritize planning even though test rows are most numerous. Keep streams separate and choose token budgets based on the hypothesis; do not blindly repeat the short decision set to equalize counts.

50 test rows contain authored rationale, totaling 1419 rationale tokens (28.4 per such row). Planning and decisions have no rationale text and retain native empty think blocks. This is a concise test-rationale dataset, not a large collection of long reasoning trajectories.

## Cyclomatic complexity

Measured with installed Radon 6.0.1. Default Radon counts assertions as decisions; both default and assert-excluded values are reported so assertion-rich tests are not mistaken for difficult branching code. Primary summaries count test functions; helper/method details remain in per-record data.

| Generated test metric | Result |
|---|---:|
| Test files | 58 |
| Test functions | 123 |
| Executed cases in existing reference evidence | 164 |
| Targeted faults detected in existing evidence | 87 |
| Source lines in generated tests | 1143 |
| SLOC per file mean +/- std | 19.7 +/- 10.8 |
| Default function CC mean +/- std | 3.20 +/- 2.19 |
| Default function CC median / max | 3 / 13 |
| Assert-excluded function CC mean +/- std | 1.16 +/- 0.53 |
| Assert-excluded function CC median / max | 1 / 4 |

110 of 123 test functions have assert-excluded CC=1; eight have CC=2, three CC=3 and two CC=4. Default ranks: 106 A, 15 B, 2 C. Straight-line tests are desirable; increasing branching merely to raise CC would reduce clarity. Parameterized inputs can exercise multiple cases without increasing syntax-level CC. This metric does not measure requirement difficulty, oracle quality, coverage, or model success.

Reference-module audit: 30 distinct directly mapped files, with 282 function/method/closure blocks, default CC mean 4.83 +/- 6.78, median 2, max 51. Scope is mixed: 15 pinned original modules, 9 pinned external modules, 6 authored reference modules. The maximum is in Ghost-box mail summary validation. Full modules include behavior outside the selected task, so **do not interpret these as per-example solution complexity** or proof the student can implement complex applications. Modules are counted once rather than once per test row. No source bodies are exported. See audit-only-reference-complexity.json for mappings and hashes.

## Domains and task diversity

An explicit analyst taxonomy maps 11 specific application families into six broad domains; labels are descriptive choices, not a learned classifier or quality score.

| Broad domain | All rows | Train-family rows |
|---|---:|---:|
| Developer tooling: detection, repo context, documentation | 27 | 27 |
| AI/ML tooling: decisions, experiments, tensor components | 22 | 22 |
| Productivity: local mail assistant | 12 | 12 |
| Databases: SQLite client | 9 | 9 |
| Finance: cryptocurrency analysis | 8 | 8 |
| Network clients: HTTP client and terminal search | 17 | 0 |

Network-client applications are evaluation-only under this taxonomy; training still has network-related adapters in documentation/mail/price tasks. Domain assignment does not imply every networking skill is absent from training. Development and holdout each cover a single family, so they cannot establish broad cross-app generalization on their own.

The 58 test artifacts span 11 behavioral categories:

| Behavior | Rows |
|---|---:|
| Parsing and serialization | 10 |
| State and lifecycle | 8 |
| Workflow composition | 8 |
| Numeric transformation | 5 |
| Filesystem/artifact handling | 5 |
| Numeric model behavior | 5 |
| Validation/errors | 4 |
| Text search/transformation | 4 |
| Routing/selection | 4 |
| Classification | 3 |
| Input/output adapter | 2 |

Decision balance: 6 ask, 6 proceed, 8 preserve-contract-and-repair, 2 correct-inconsistent-test. Plans contain 15 integration todos, but those are proposed future checks, not captured successful app execution. Actual agent-execution trajectories and implementation-generation targets are both zero.

Direct generated-test imports include torch in 6 files and pandas in 4, plus pytest/standard-library facilities and the named application modules. This import inventory is a lower bound on exercised dependencies: tests can exercise a library through an application module without importing it directly. It is not evidence of broad coverage of popular Python frameworks. Real HTTP service delivery, authentication workflows, dependency/environment repair and executed replanning are sparse or absent as teaching trajectories.

## Semantic near-duplicate review

Artifacts: all-pair-similarities.json, review-candidates.json, semantic-review-packet.txt and [semantic-review.json](dataset-profile-v02/semantic-review.json).

Method: 4485 pairs considered for lexical candidate retrieval, including 1398 cross-split pairs. Retrieval uses Unicode words/bigrams and sublinear TF-IDF cosine over task purpose/acceptance, excluding shared system instructions and repeated full interfaces. It is **not an embedding model**, and a low score does not prove semantic independence. Twenty-two explicit pair-level semantic adjudications are recorded. This is targeted assistant review, not exhaustive human inspection of all 4485 pair combinations or independent external evaluation.

Exact checks found **zero duplicate conversations, zero identical normalized test artifacts and zero identical normalized test-function bodies** across the active records. This does not establish that every row teaches a new skill.

Four planning variants have the strongest similarities (roughly 0.75-0.77): tldr offline-cache, repo snapshot-core, Ghost-box first-memory and LiteCLI SQL-core versus their parent plans. Each explicitly requests a narrower milestone and stays in the parent's split. Keep them labeled as correlated variants; consider weighting or selecting among them when comparing independent-app exposure.

Plan/child-task and decision/test overlaps inside a family are expected across tracks. For example, a ddgr serialization test and its proceed-with-clear-contract decision test different outputs from the same scenario. They must stay in the same split, as they do now.

### Cross-split taught-principle overlap

Three pairs deserve explicit evaluation interpretation rather than a blanket no-overlap claim:

1. `mail-fast` (train) versus `posting-latency` (development): both turn vague speed requirements into objective limits. Posting adds UI acknowledgement versus remote completion, but reuses the latency-clarification principle.
2. `mock-away-classifier` (train) versus `mock-all-network` (holdout): both reject a mock replacing core tested behavior; the holdout adds adapter/parser composition.
3. `missing-integration` (train) versus `mock-all-network` (holdout): both reject a whole-app/e2e claim based on isolated unit success and request a real composed-path check.

These are not copied source or reference-answer leakage. They make the relevant decision evaluation items **transfer tests of principles already taught**, rather than entirely unseen reasoning families. That can be a valid evaluation goal. Before freezing the protocol, state that goal explicitly; if strict unseen-problem-family evaluation is required, expand or replace those evaluation scenarios. No automatic row removal or source-family reassignment was made.

Other inspected cross-split similarities?page URL construction versus arbitrary URL safety, repository URL routing versus colon-path parameters, checkpoint reload versus result JSON, cancellation versus undo history, completion paths versus request filenames?have different observable contracts. Sharing a primitive such as Unicode or serialization is not alone a duplicate task.

## Implications

This is a small, diverse-enough format/demo collection with correlated families and substantial template reuse; its model utility is still unmeasured. Preserve the test-only hypothesis or explicitly define a separate mixture. Prioritize new distinct behaviors and composed-path examples over more scope variants. Broaden evaluation families before strong generalization claims. Do not make generated tests more complicated just to increase CC.

All metadata, figures and similarity artifacts are audit outputs. Repository implementation remains excluded from model inputs/targets. Training and baseline inference have not run. Semantic novelty is not certified as globally clean: this review records overlap and a protocol choice still to make.

## Reproducibility

`profile_tdd_dataset.py` resolves the active config and records input hashes, tokenizer identity checks, package versions, methods and per-record data. `review_dataset_similarity.py` saves the explicit semantic judgments and supporting purpose text. Six focused profile tests pass, including method/closure deduplication. Native train-token counts were cross-checked against the prior label-audit output. See manifest.json, verification.json and integrity.json in dataset-profile-v01.
