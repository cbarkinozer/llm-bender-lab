# Language-detector example correction — revision 06

Review: http://127.0.0.1:7900/dataset/b3adc9b0-a181-4c1f-9c51-d7e4512b677e/annotation-mode
Share one complete example: share/codelang-detect-v06-input-output-annotations.txt.

The supplied review identified two real weak fixtures: declaration order agreed
with alphabetical order, and the CLI input suffix already revealed its contents.
The corrected tie chooses zeta before alpha; the Python snippet is stored in
snippet.txt. Invalid UTF-8 now tests exit 1, empty stdout and the processing-error
prefix. Runtime configuration replacement and a single positive rule score also
have direct tests.

Decisions explicitly state the positive-score policy and initial Python/JavaScript
targets. The interface declares PATTERNS as a public call-time configuration map
whose keys are output labels, and includes it in the API/configuration inventory.
Additional languages remain open under M2. No library API or implementation was
changed; a rules parameter remains a possible later design change.

The no-Traceback stderr assertion is retained with a clarifying comment: it can
catch an explicitly printed traceback even when SystemExit is raised correctly.
A dedicated printed-traceback mutant demonstrates this, so that specific review
claim was qualified rather than followed blindly.

This example has 15 passing cases, 11 detected targeted faults and passing order
seeds 17/43/91. The full native sequence is 2,466 tokens.
Evidence for R1–R5 is included in both Argilla and the TXT export. The exporter
refuses empty per-core kill lists and is covered by two regression tests.

The other eight model conversations are byte-identical to v05; their unchanged
validation snapshots are reused. Whole-bundle accounting is 147
cases / 71 fault probes, not a claim that all siblings were rerun
in this correction. Changed-example logs are committed under evidence/; older
portable evidence remains in v05. All nine fit 8K, maximum 7,168.

No ratings are prefilled or submitted. Existing review datasets remain intact.
No baseline inference or SFT ran; train/eval roles are unchanged and human approval
is still pending. The configured module-global seam is intentional for this demo.

## Reproduce this correction

Using the prepared local Torch/tokenizer Python from the parent experiment:

```sh
python scripts/evaluation/run_tdd_core_suites.py --revision app-core-v06 --repo codelang-detect
python scripts/evaluation/check_tdd_revision_faults.py --revision app-core-v06 --repo codelang-detect
python scripts/evaluation/check_tdd_revision_stability.py --revision app-core-v06 --repo codelang-detect
python scripts/evaluation/build_tdd_app_revision.py --revision app-core-v06
```

Publish with lab `.venv/bin/python scripts/evaluation/publish_tdd_app_revision.py --revision app-core-v06`.
Export with `.venv/bin/python scripts/evaluation/export_tdd_review_example.py --output <path.txt>`.
The canonical model content stays raw; HTML escaping remains display-only.
