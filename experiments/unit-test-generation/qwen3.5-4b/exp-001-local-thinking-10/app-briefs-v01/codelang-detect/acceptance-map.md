# codelang-detect — draft core acceptance map

Whole small library/CLI. Do not train on benchmark/test_data.json while claiming held-out accuracy on that fixture set.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Return unknown for input without supported evidence. | Empty string, whitespace-only text and an ordinary prose fixture return exactly unknown. | unit |
| R2 | Use weighted evidence and deterministic ties. | With an explicitly injected small rule table, one higher-weight match defeats two lower-total matches; equal totals follow the agreed tie rule. | unit |
| R3 | Recognize approved unambiguous starter-language examples. | Fresh short Python/JavaScript/SQL examples map to the agreed extensions; examples are not copied from retained benchmark fixtures. | unit |
| R4 | File and stdin CLI routes match the library. | The same snippet through UTF-8 temp file and stdin prints one identical label followed by newline with empty stderr. | integration |
| R5 | Input failures use nonzero exit and useful diagnostics. | Missing file or closed stdin produces agreed error/exit code and no successful language label; stderr does not contain a traceback. | integration |

## Public test boundary (proposal)

Library detect operation and CLI stdin/stdout/stderr/exit code; controlled rule table for algorithm oracles, fresh real snippets for behavior.

## Decisions still needing agreement

- Choose starter languages, exact output extensions and tie/ambiguity policy.
- Agree whether exposing configurable rules is public API or configuration loaded at startup.

## Manual / live checks

- Responsiveness on representative file sizes and real-world accuracy require separate benchmarks.

## Candidate existing evidence — not automatically selected

- `tests/test_detector.py`
- `tests/test_cli.py`

Source revision: `14fc6b772808b9e8158d62b649a043b14c8df6fb`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
