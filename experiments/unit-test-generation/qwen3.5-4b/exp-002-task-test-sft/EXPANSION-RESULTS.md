# Existing-repository expansion results

38 task-to-tests teaching candidates from all seven training families. This is
38 total, including the eight v01 behaviors; the versions are not additive.
The nine old whole-app records remain separate. Seven planning contexts remain
outside the SFT targets. GitHub-insignia and slm_test_generation were excluded.

| Training family | Task examples |
|---|---:|
| ReflexModels | 6 |
| codelang-detect | 4 |
| cryptocurrency-analyser | 4 |
| ghost-box | 8 |
| llm-bender-lab | 4 |
| miniature-llms | 6 |
| repo-context | 6 |

## Measured validation

- 96 reference test cases pass across the 38 artifacts.
- All 46 targeted faults are detected by the relevant task artifacts alone.
- Three seeded runs per task pass. Single-case tasks do not have distinct
  permutations; actual collected orders are saved, without claiming otherwise.
- Complete native thinking-inclusive conversations total 82,468 tokens.
- Maximum sequence length is 2,873 tokens; no truncation, all below 8,192.
- Tests, rationale and exact target file paths are present in every conversation.
- Planning, implementation and tool-call training remain outside this experiment.

A missing helper in the extracted generation-test artifact initially failed.
The extractor now retains transitively called helpers and fixtures, with a
regression test. The failed row/old test and original logs are retained under
pilot-v02/repairs and timestamped evidence. The affected row was rebuilt and rerun;
other artifacts/messages were checked for exact equality and retained their
passing evidence. No failure was discarded or counted as a successful baseline.

## Remaining work

expansion-catalog.json contains these 38 built artifacts and 62 additional
source-backed proposals, not 100 ready training rows. Each proposal identifies an
existing source module, its hash and callable inventory. Those entries still need
explicit task contracts, teacher test files, deduplication/scope review, execution
and fault checks. Advanced architecture/provider/UI proposals may need separate
fixture environments or exclusion after inspection.

No outside repositories were needed for this expansion. Candidate leads remain
optional for genuine gaps. The seven families remain training-side; related
modules never become final holdout examples. Training-only task count is not a
measure of independent application diversity. No Qwen baseline or SFT has run.

## Files

- pilot-v02/records.jsonl: exact task conversations and metadata (not approved SFT export).
- pilot-v02/planning-contexts.jsonl: seven separate, authored application plans.
- pilot-v02/share/task-test-pilot-v02.txt: all 38 examples separated by ----.
- expansion-spec.json: reproducible task selection, contracts and fault definitions.
- expansion-catalog.json: 38 built examples plus 62 unbuilt source-backed proposals.

## Reproduce

Use the pinned sources and tokenizer described by the initial README. From repo root:

```powershell
python scripts/evaluation/task_test_pilot.py build --spec expansion-spec.json --bundle pilot-v02 --tokenizer <pinned-tokenizer-directory>
python scripts/evaluation/task_test_pilot.py validate --spec expansion-spec.json --bundle pilot-v02 --workers 2 --python <validation-python> --source-root <pinned-sources-directory>
python scripts/evaluation/task_test_pilot.py export --spec expansion-spec.json --bundle pilot-v02
```

Build refuses to overwrite existing records. The explicit --repair-task escape
only permits repair of a failed, unreleased draft and preserves its previous row;
unchanged tasks must retain identical model messages/artifacts. A fresh revision
is required for changing reviewed or passing targets.
