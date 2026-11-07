# Local anonymous comparison UI

Argilla is running at http://127.0.0.1:7900 using the existing local server and
its existing login. Workspace: `tdd-blind-comparison`. Existing ReflexModels and
other workspaces/datasets were preserved; no volumes or reviews were replaced.

Start with five primary test comparisons:
http://127.0.0.1:7900/dataset/38871af8-c5fa-462c-b132-e57d23246d22/annotation-mode

Then review four supporting planning/clarification/integrity probes separately:
http://127.0.0.1:7900/dataset/5d13e6ae-4cc5-4054-b65e-9cb502ab0a43/annotation-mode

Each record shows the supplied requirement and anonymous X/Y/Z outputs. Initial
ratings hide model labels, rationale traces, runtime scores and machine judgments.
Labels are randomized separately per case using the preserved blind packet.
No PRIVATE identity file is uploaded. Do not consult run summaries or mappings
until initial judgments are submitted.

Rank X/Y/Z with ties allowed, assess each output (retain/repair/reject/uncertain
for tests), optionally rate assertion strength, and provide evidence. All-reject
and uncertainty are valid. Click Submit to save each record. Full code is shown
even if its filename header or pytest naming is wrong; automated strict format
and runtime counts stay separate. Supporting probes are not pooled into test
quality scores. No human judgments were prefilled or submitted by the importer.

The import was run twice: same dataset/record IDs, exact display-field roundtrip,
5+4 records, no suggestions. Initial read-only export confirmed0 submissions.
Labels submitted later live in the existing local Docker database volumes.

## Recreate and export

Importer/exporter: `scripts/evaluation/publish_tdd_threeway_argilla.py`.
Dedicated SDK environment (separate from training):
`C:/Users/barkin/Documents/llm-bender-artifacts/argilla-tdd-review/.venv`.
SDK Argilla2.8.0 plus requests2.32.5; full freeze is beside the import receipt.
The current server's ignored credential file is in the ReflexModels repository:
`experiments/decision-followups/review-ui/.env`. No credentials are committed.

```powershell
$reviewPython = 'C:/Users/barkin/Documents/llm-bender-artifacts/argilla-tdd-review/.venv/Scripts/python.exe'
$credentialFile = 'C:/Users/barkin/Documents/GitHub/ReflexModels/experiments/decision-followups/review-ui/.env'
& $reviewPython scripts/evaluation/publish_tdd_threeway_argilla.py publish --credential-env $credentialFile
& $reviewPython scripts/evaluation/publish_tdd_threeway_argilla.py export --credential-env $credentialFile --output C:/Users/barkin/Documents/llm-bender-artifacts/tdd-gpu-20261107/argilla-exports/session-02
```

Use a new export path each session; previous snapshots are preserved. Import
refuses content conflicts and appends only missing stable IDs. It never deletes
datasets, edits review responses, or submits fabricated annotations. The receipt
is `gpu-results-20261107/argilla-review-v01/receipt.json`. Keep the external
`blind-three-way-v02/PRIVATE-identities.json` for later unblinding; never upload it
to the reviewer UI. After ratings are saved, export them before any schema change
or unblinding, then combine evidence with the execution results to plan Exp3/4.
