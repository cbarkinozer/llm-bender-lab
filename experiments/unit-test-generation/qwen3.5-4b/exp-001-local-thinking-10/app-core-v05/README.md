# TDD review hardening — revision 05

Current review: http://127.0.0.1:7900/dataset/ae9c43c9-54ea-4602-9d4d-56741869b59a/annotation-mode

- Argilla code fields escape HTML only for display. Angle-bracket placeholders,
  comparison operators and ampersands remain visible; decoding the stored display
  reproduces all nine raw test payloads exactly. Training messages are not escaped.
- Added defect category: Review/meta text leaked into input or target.
- Pre-checks inspect process words (revision, reference, paper, review), repo/lab
  names and local source paths. Functional provenance fields and declared public
  API identifiers receive explicit explanations rather than indiscriminate deletion.
- The leaked filename test_revisions.py is now test_snapshot_contract.py in the
  copied GitHub suite. Numbered test_rN_ names must include R-N in the map.
- Failure-state assertions use deep snapshots, advanced clocks and exact durable
  bytes. A separate success test requires new contents and timestamp. Original
  application code is unchanged.
- Preservation contracts are declared in model-config.json and verified against
  targeted killed mutants in record metadata. They cover stale/current snapshots,
  raw generations, previous artifacts, provenance, input immutability, isolation,
  missingness and checkpoint predictions. These checks are not exhaustive proof.

Validation: 143 passing app cases, 65 detected
fault variants, 17 declared preservation contracts,
three passing collection orders per suite and five display/pre-check regression
tests. All numbered names agree with the map. No unresolved process-text findings.
All full native examples fit 8K; maximum 7,168 tokens.

The v04 Argilla view was repaired in place first; annotations and original
presentation snapshots were preserved. Its published label count could not be
extended, so this new review dataset contains the additional category. Earlier
views remain available; no annotations were fabricated or copied to changed
records. Packet/display history is in human-review-v04/presentation-v02.

No baseline inference or SFT ran. The seven training/two held-out repo split is
unchanged; the paper repo stays excluded from training. All records still require
human approval. Deferred executor changes remain outside the active examples.

## Reproduce

Use the prepared local Torch/tokenizer interpreter from the parent experiment:

```sh
python scripts/evaluation/run_tdd_core_suites.py --revision app-core-v05
python scripts/evaluation/check_tdd_revision_faults.py --revision app-core-v05
python scripts/evaluation/check_tdd_revision_stability.py --revision app-core-v05
python scripts/evaluation/build_tdd_app_revision.py --revision app-core-v05
python -m unittest discover -s scripts/evaluation/tests -p test_tdd_review_prechecks.py
```

Publish with lab `.venv/bin/python scripts/evaluation/publish_tdd_app_revision.py --revision app-core-v05`.
The host runner accepts trusted authored tests only. Generated code still requires
isolation. Original external logs are retained; portable copies and their hashes
are in evidence/index.json.
