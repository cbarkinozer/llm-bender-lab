# Whole-app thinking-SFT candidates — revision 03

Current human review: http://127.0.0.1:7900/dataset/f7c79cb7-8943-4281-98d1-4e9128a2b529/annotation-mode

Nine source-informed natural requests now use framing B: the model receives a
request and visible preparation constraints, then proposes decisions/open
questions, a public interface, a requirement-to-test map, complete pytest files
and manual checks, in that fixed order. Concise explanatory rationale is stored
separately and serialized using the local Qwen native thinking template.
Assistant proposals are not represented as historical human clarifications.

## Validation

- 142 reference cases pass across nine suites.
- 57 targeted broken variants are detected, with at least one
  explicitly targeted killed variant for each of 53 automated
  core requirements. A mapped test must actually be collected, and a fault must
  fail an assertion in a test mapped to its targeted requirement.
- Each suite passes three distinct shuffled collection orders (seeds 17,43,91).
  This is a stdlib shuffle plugin, not a claim of fresh hermetic environments.
- All complete native sequences fit 8,192 tokens. Maximum: 6,934;
  total across nine separate examples: 31,939. Includes system,
  request/constraints, rationale, full target, template and EOS. Counts are
  cross-checked against re-encoding serialized text; sections are not naively summed.
- Application imports are inventoried from test ASTs and declared in each target.
  Presence in an inventory does not prove semantic interface sufficiency; review
  signatures, schemas, defaults and method behavior in interface.md too.

Exact records: records.jsonl and each app's record.json, request.md, reasoning.md,
interface.md, target.md and tests/. Validation-only reference code is under each
app's reference/; it is excluded from model input/output and token counts.

## Important scope limits

Six apps needed new reference workflow facades to exercise missing app contracts.
Those are separately authored reference implementations, not proof the original
UI/CLI apps now implement or invoke them. Original application files were not
changed. Backend contract tests, delivery/manual integration checks and live checks
are distinguished explicitly. Approve this declared target scope or mark revise;
do not silently reinterpret these as nine certified complete original apps.

The paper classifier facade fixes instrumentation header placement for valid
module docstrings/future imports without changing the paper checkout. Old results
and frozen benchmark instances remain untouched. No real training, weights,
backend inference, live GitHub requests or mail access occurred.

## Review form

Q1 relevance/scope; Q2 interface sufficiency; Q3 coverage; Q4a correctness;
Q4b justification; Q5 fault discrimination; Q6 contextual smells; Q7 overall
rule-based decision; Q8 concise rationale; reviewer confidence. Fixed defect
categories and structured interface/coverage/assertion notes accompany a required
Blocking issues field (enter none when empty). Anchors, approval/revise/reject/
uncertain rules and two illustrative calibration examples are in
human-review-v02/GUIDELINES.md. No human answers are prefilled or submitted.
Actual model inputs/targets are in record.json. Review-only source/evidence
fields are excluded from messages.

Separate AI audit: second-ai-review/round-1.json preserves two genuine revise
findings; round-2.json records both fixed and approved by that AI reviewer.
These are not independent human ratings. Human paired-review agreement is
unavailable (zero pairs); use tdd_review_rules.agreement when actual paired
ratings exist. Rule consistency can be checked with
scripts/evaluation/tdd_review_rules.py without creating approvals.

## Split and next step

Proposed seven training repos: ghost-box, llm-bender-lab, ReflexModels,
codelang-detect, repo-context, cryptocurrency-analyser, miniature-llms.
Held out entirely: GitHub-insignia and slm_test_generation. In particular, the
paper-repo record never enters training when measuring paper-benchmark transfer.
No benchmark instances were used to create the fresh fixture tests. A broader
near-duplicate/provenance check remains a pre-training gate.

All nine are still training_eligible=false pending owner annotation. Next:
review/resolve blockers, freeze a tiny approved pilot and split, then run the
untouched Qwen thinking-on baseline before any SFT or scaling. Baseline tests
must be graded against their own proposed interface (using an aligned adapter or
implementation); a different consistent API name alone is not a model failure.
Keep that policy identical before and after training. Subsequently verify loss
masking, short SFT and matched held-out/transfer evaluation. No new whole-app
baseline or SFT has run yet.

## Reproduce trusted checks

Use the prepared local Torch/tokenizer interpreter documented in the parent
experiment. Commands from the lab repo:

```sh
python scripts/evaluation/run_tdd_core_suites.py --revision app-core-v03
python scripts/evaluation/check_tdd_revision_faults.py
python scripts/evaluation/check_tdd_revision_stability.py
python scripts/evaluation/build_tdd_app_revision.py
```

For publishing, use lab `.venv/bin/python scripts/evaluation/publish_tdd_app_revision.py`.
It checks snapshots, fault/stability provenance and immutable packet content before
logging missing IDs. Earlier Argilla datasets/reviews remain preserved. Do not
alter published packets in place; create another revision if targets change.
Subset reruns retain separate execution receipts; the builder combines their
latest matching snapshots and rejects stale file hashes. Fault/stability logs
remain external under llm-bender-artifacts/thinking-tdd/.

This host runner is for trusted authored suites only. Model-generated code needs
sandboxed execution; never send it directly to the trusted host runner.
