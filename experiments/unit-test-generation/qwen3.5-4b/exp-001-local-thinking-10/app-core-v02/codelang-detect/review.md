# codelang-detect — assistant review

## Whole-app request

Make me a small zero-dependency Python tool that guesses the programming language of a code snippet without loading a model or using the network. I want both a callable library and a CLI that reads a UTF-8 file or piped text and prints the detected lowercase file extension, with unknown for empty input, whitespace or ordinary prose with no convincing code markers. Use a configurable set of weighted regex rules so stronger evidence wins rather than just the first matching language, support a documented starter set of common languages, and make ties deterministic. The CLI should give useful errors and a nonzero exit code when it cannot read its input without dumping a traceback in normal use. Include a few clear examples and install/run instructions, keep the code easy to extend, and don't promise perfect detection of inherently ambiguous snippets or tune the tests to a huge hidden benchmark.

## Decisions and corrections

- Choose Python and JavaScript as explicit starter examples; extending language coverage is a later agreed requirement.
- Equal weighted scores choose the first declared language; rules are developer configuration, not a new runtime configuration service.
- File-open CLI usage failures exit 2; processing failures exit 1. Both are nonzero and use stderr. The first draft wrongly assumed all errors exit 1.

## Important limits / missing acceptance checks

- No retained benchmark corpus included in these fresh cases.
- Throughput and broad language accuracy need separate evaluation; strong tests are not a perfect detection guarantee.

## Requirement-to-test review

### R1 — Return unknown for input without supported evidence.

**Core check:** Empty string, whitespace-only text and an ordinary prose fixture return exactly unknown.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Use weighted evidence and deterministic ties.

**Core check:** With an explicitly injected small rule table, one higher-weight match defeats two lower-total matches; equal totals follow the agreed tie rule.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Recognize approved unambiguous starter-language examples.

**Core check:** Fresh short Python/JavaScript/SQL examples map to the agreed extensions; examples are not copied from retained benchmark fixtures.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — File and stdin CLI routes match the library.

**Core check:** The same snippet through UTF-8 temp file and stdin prints one identical label followed by newline with empty stderr.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Input failures use nonzero exit and useful diagnostics.

**Core check:** Missing file or closed stdin produces agreed error/exit code and no successful language label; stderr does not contain a traceback.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_core.py::test_unknown_without_code_evidence`
- `tests/test_core.py::test_clear_language_markers`
- `tests/test_core.py::test_weighted_evidence_not_match_count`
- `tests/test_core.py::test_equal_scores_use_first_declared_language`
- `tests/test_core.py::test_cli_file_prints_one_label`
- `tests/test_core.py::test_cli_stdin_prints_one_label`
- `tests/test_core.py::test_missing_file_returns_error`
- `tests/test_core.py::test_closed_stdin_returns_processing_error`

## Manual checks

- Responsiveness on representative file sizes and real-world accuracy require separate benchmarks.
