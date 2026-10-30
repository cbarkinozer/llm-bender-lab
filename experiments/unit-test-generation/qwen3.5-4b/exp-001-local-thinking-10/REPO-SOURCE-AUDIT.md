# Nine-repository test audit — 2026-10-30

One SFT run can train on examples from all repositories. It does not require
concatenating each repository into one sequence. Zero-shot evaluation means no
worked examples in the evaluation prompt, not one training example, one epoch or
training without demonstrations.

## Measured Qwen test-source lengths

| Repository | Test files | Static test functions | Characters | Qwen tokens | Largest file tokens |
|---|---:|---:|---:|---:|---:|
| GitHub-insignia | 2 | 20 | 14,584 | 3,850 | 2,025 |
| ghost-box | 28 | 94 | 147,237 | 32,541 | 3,330 |
| slm_test_generation | 15 | 142 | 112,981 | 29,628 | 6,036 |
| llm-bender-lab | 19 | 120 | 63,815 | 16,316 | 2,309 |
| ReflexModels | 36 | 198 | 121,712 | 30,505 | 3,294 |
| codelang-detect | 2 | 8 | 4,132 | 1,029 | 567 |
| repo-context | 1 | 9 | 3,407 | 913 | 913 |
| cryptocurrency-analyser | 1 | 7 | 3,596 | 1,140 | 1,140 |
| miniature-llms | 1 | 8 | 2,136 | 694 | 694 |

Measured with the saved Qwen3.5 tokenizer, identity/hash and per-file measurements
in repo-source-audit.json. These lengths exclude conftest fixtures (counted
separately in JSON), requirements, reasoning, public interface and chat formatting.
Static functions are not pytest parameterized cases. Historical experiment utility
files can be discovered by name without being dataset candidates. Length reports
must never be treated as blanket training approval.

## Context recommendation

Prepare feature-sized complete demonstrations: request and agreed interface ->
concise concrete reasoning -> complete executable test files, including required
fixtures. Use one mixed SFT run with explicit repo/domain sampling so the largest
repo does not dominate. Prefer self-contained examples around 2K–8K total tokens;
use 16K as a provisional maximum only if final serialized examples need it and
training smoke fits GPU memory. Count actual native-template tokens after teacher
reasoning exists, report min/median/p95/max and truncation (goal: zero). Never cut a
test module or reasoning/output pair to meet the limit. Packing, if used, must
preserve example boundaries and supported attention/loss semantics.

Whole-repo suites from Ghost-box, ReflexModels and the study exceed 29K–32K test
tokens before context/reasoning. 16K cannot accommodate them. A long full-app suite
could need 32K/64K, but expanding context is unnecessary for the first learning
run. Feature-level training does not establish full-app one-shot capability. If
we later evaluate an entire app in one response, preserve that as a separately
budgeted task rather than silently replacing it with a feature task.

## Execution and quality evidence

Verified 363 cases across the following checked scopes:
- GitHub-insignia: 36, full tests directory.
- Ghost-box: 94, full unittest discovery (offscreen Qt).
- slm_test_generation: 101, oracle-analysis and oracle-sampling utility tests only.
- llm-bender-lab: 13, paper-adapter and request-recorder tests only.
- ReflexModels: 28, nine core decision/scoring/calibration/routing test modules only.
- codelang-detect: 67, full tests directory (includes benchmark fixture cases).
- repo-context: 9 new tests.
- cryptocurrency-analyser: 7 new comparator tests.
- miniature-llms: 8 new RMSNorm/RoPE tests.

New tests cover exact numerical results, input preservation, error contracts and
mocked I/O interactions. All six deliberately faulty source variants were detected
(two per newly tested repo). This is diagnostic fault detection, not a general
mutation score. Assistant review found no actionable contextual smells in these
new focused suites; owner review remains pending. Do not impose the older static
rule that multiple assertions automatically imply Assertion Roulette. Tensor and
DataFrame comparison helpers are semantic numeric oracles even if a generic
classifier cannot classify them.

Measured combined statement/branch coverage: repo-context core.py 68.3% (CLI and
GPQS untested), coin_comparator.py 84.2%, RMSNorm/RoPE modules 100%, codelang detector
100% and CLI 90.9%. None of these figures mean full coverage of the corresponding
application. Exact missed lines and radon complexities are in the external audit.
Radon counts assert statements toward complexity, so assertion-rich tests can
have a high reported score without conditional control flow.

Audit dependencies were installed outside the source repos; these checks are not
replications of every historical project environment. Exact package versions,
checks.log, coverage JSON, fault edits/logs and run-checks.sh live at:
/Users/cbarkinozer/Documents/llm-bender-artifacts/thinking-tdd/repo-audit-20261030/
Known deprecation warnings: Starlette test client and pandas inplace dropna.

## Training/evaluation separation

Never train on the paper's frozen benchmark items/predictions, codelang's benchmark
snippets if retaining that benchmark for evaluation, or earlier lab evaluation
contracts. Study utility tests are distinct from benchmark task data. Audit any
fixtures/helpers embedded in a selected demonstration; the paper transfer subset
must remain disjoint from SFT tasks and their derived requirements. Existing tests
are implementation-informed candidates, not automatically approved requirements-
first demonstrations. Assign split roles before writing additional training data.

Next: choose complete feature contracts and split roles, review teacher tests and
write concise reasoning, tokenize the actual final messages, then freeze an SFT
configuration. No SFT or GPU run was started by this audit.
