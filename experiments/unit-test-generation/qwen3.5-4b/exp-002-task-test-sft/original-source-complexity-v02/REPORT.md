# Original source cyclomatic complexity

Original pinned source repositories backing the active dataset. No implementation bodies were exported or used for training. Non-test includes scripts, examples and benchmarks. CC is measured per function/method/closure; class aggregates are excluded. Standard deviation is population std.

| Repository | Non-test files | Functions | CC mean | CC std | Median | Max |
|---|---:|---:|---:|---:|---:|---:|
| ReflexModels | 58 | 217 | 7.41 | 8.33 | 5 | 49 |
| codelang-detect | 7 | 11 | 6.09 | 3.18 | 5 | 12 |
| cryptocurrency-analyser | 10 | 86 | 5.22 | 6.54 | 3 | 35 |
| darrenburns/posting | 82 | 692 | 2.86 | 3.52 | 2 | 38 |
| dbcli/litecli | 24 | 197 | 4.26 | 5.51 | 3 | 50 |
| ghost-box | 38 | 259 | 5.43 | 7.02 | 3 | 51 |
| jarun/ddgr | 2 | 109 | 3.59 | 4.28 | 2 | 28 |
| llm-bender-lab | 223 | 710 | 8.27 | 10.93 | 3 | 96 |
| miniature-llms | 34 | 78 | 2.04 | 1.09 | 2 | 6 |
| repo-context | 8 | 28 | 5.93 | 6.33 | 3.5 | 32 |
| tldr-pages/tldr-python-client | 2 | 25 | 7.08 | 8.07 | 4 | 35 |

Pooled non-test source: 2412 functions, mean **5.44**, std **7.85**, median 2, max 96.
With assertions excluded: mean 5.11, std 7.16.
Original repository tests, separately: 1596 functions, mean 2.56, std 2.42.

Skipped/missing/unparseable files: 0. See summary.json for details.

Large functions and skew make mean/std alone incomplete. This describes code structure, not correctness, maintainability by itself, or the complexity of each requirement. Module-level code outside functions is not part of function CC. The two historical reserved evaluation repositories are outside these 11 active source families.
