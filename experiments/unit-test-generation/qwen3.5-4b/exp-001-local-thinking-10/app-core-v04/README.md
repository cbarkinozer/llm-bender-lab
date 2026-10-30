# Shared example format — revision 04

Current Argilla review: http://127.0.0.1:7900/dataset/7500c36b-0971-41bd-91c5-765d6e7add5e/annotation-mode

This revision fixes the shared input/output format across nine candidates.
See [the format contract](../../../../../docs/tdd-example-format.md).

- System: common Python/pytest instructions and genuine task constraints.
- User: the unchanged natural application paragraph, with no dataset notes appended.
- Assistant: concise rationale plus decisions/open questions, proposed interface,
  requirement map, complete tests and manual checks, in a fixed order.
- Review-only metadata: source/provenance, validation, token counts and annotations.

Construction/history/reviewer commentary was removed from the model messages.
Functional requirements, including email source references, were retained.
`scan_tdd_model_text.py` checks these boundaries and flags ambiguous keywords
rather than deleting them indiscriminately.

## Scope and evidence

Test executable ASTs and application reference implementations are unchanged from
v03; only copied test module descriptions were cleaned. See
format-change-receipt.json. Record-specific executor/test work is preserved in
../app-core-v04-record-specific-draft, outside these active records. Individual
content/annotation issues remain separate from this format correction.

Rechecked: 142 passing cases, 57
killed targeted variants covering 53 automated core
requirements, and three seeded collection orders per suite. Complete native
sequences fit 8,192 tokens: maximum 6,769, total
30,397 across nine separate examples. These checks do not
certify original UI/CLI wiring or every aspect of semantic quality.

The seven proposed training repos and two held-out repos are unchanged;
GitHub-insignia and slm_test_generation remain excluded from training. All records
remain training_eligible=false pending human approval. No new baseline or SFT ran.

Earlier Argilla reviews are preserved. This dataset has the same annotation form;
this step does not re-annotate examples or submit human responses. See
human-review-v03/receipt.json and immutable packets.jsonl.

## Trusted validation

From the repository, using the prepared local tokenizer/Torch Python:

```sh
python scripts/evaluation/run_tdd_core_suites.py --revision app-core-v04
python scripts/evaluation/check_tdd_revision_faults.py --revision app-core-v04
python scripts/evaluation/check_tdd_revision_stability.py --revision app-core-v04
python scripts/evaluation/build_tdd_app_revision.py --revision app-core-v04
python scripts/evaluation/scan_tdd_model_text.py experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v04/records.jsonl
```

Publish with lab `.venv/bin/python scripts/evaluation/publish_tdd_app_revision.py --revision app-core-v04`.
The host suite runner is for trusted authored tests only; generated code still
requires isolated execution. Original validation artifacts remain under llm-bender-artifacts. Portable copies
of the execution/fault/stability logs and their hashes are versioned in evidence/.
