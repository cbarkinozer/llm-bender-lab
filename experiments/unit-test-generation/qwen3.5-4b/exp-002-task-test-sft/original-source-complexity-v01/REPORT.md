# Original source cyclomatic complexity

Original pinned source repositories backing the active dataset. No implementation bodies were exported or used for training. Non-test includes scripts, examples and benchmarks. CC is measured per function/method/closure; class aggregates are excluded. Standard deviation is population std.

| Repository | Non-test files | Functions | CC mean | CC std | Median | Max |
|---|---:|---:|---:|---:|---:|---:|
| ReflexModels | 58 | 232 | 7.08 | 8.16 | 4 | 49 |
| codelang-detect | 7 | 11 | 6.09 | 3.18 | 5 | 12 |
| cryptocurrency-analyser | 10 | 86 | 5.22 | 6.54 | 3 | 35 |
| darrenburns/posting | 82 | 1256 | 2.82 | 3.42 | 2 | 38 |
| dbcli/litecli | 24 | 273 | 4.32 | 5.45 | 3 | 50 |
| ghost-box | 38 | 413 | 5.01 | 6.51 | 3 | 51 |
| jarun/ddgr | 2 | 192 | 3.51 | 4.13 | 2 | 28 |
| llm-bender-lab | 223 | 769 | 7.82 | 10.63 | 3 | 96 |
| miniature-llms | 34 | 152 | 2.05 | 1.10 | 2 | 6 |
| repo-context | 8 | 28 | 5.93 | 6.33 | 3.5 | 32 |
| tldr-pages/tldr-python-client | 2 | 25 | 7.08 | 8.07 | 4 | 35 |

Pooled non-test source: 3437 functions, mean **4.74**, std **6.98**, median 2, max 96.
With assertions excluded: mean 4.50, std 6.41.
Original repository tests, separately: 2244 functions, mean 2.41, std 2.28.

Skipped/missing/unparseable files: 0. See summary.json for details.

Large functions and skew make mean/std alone incomplete. This describes code structure, not correctness, maintainability by itself, or the complexity of each requirement. Module-level code outside functions is not part of function CC. The two historical reserved evaluation repositories are outside these 11 active source families.
