# Nine whole-app TDD briefs — draft revision 01

The owner scope is a natural whole-app request -> reasoning -> minimal public
interface and compact core acceptance tests. This replaces the earlier proposal
to make every training example a narrow feature. It does not concatenate all
historical regression suites or require predicting every private function.

[All nine single-paragraph requests](REQUESTS.md) are ready for review. Each repo
folder contains request.md and acceptance-map.md. briefs.jsonl preserves the same
requests, proposed system/user messages, 53 requirement mappings, manual checks,
open decisions, source revision and candidate test references. No application
source code or old test implementation is included in the proposed model inputs.

Review: http://127.0.0.1:7900/dataset/ee48112d-5b2a-4626-9fd1-ada50f8f0f6b/annotation-mode

## What review decides

- Is this the whole usable core app you mean? Crypto, miniature-llms and the lab
  intentionally state a first-version scope, rather than pretending to cover all
  historical features. Scope changes remain explicit and require owner judgment.
- Are important observable requirements missing or ambiguous?
- Are expected outcomes justified? The reviewer map is not hidden grading input.
  Any added detail must become a visible approved clarification before evaluation.
- Which requirements need UI, manual, live-provider or model-quality review?

A proposed map is not a selected test suite. Existing candidate tests only cover
parts of these contracts; they must be selected/adapted and supplemented before
claiming coverage. Strong assertions, contextual smells, mutation evidence and
execution correctness are separate checks. No approved teacher reasoning or tests
have been generated for this new whole-app revision yet. The source apps already
exist, so reconstructed test examples are implementation-informed, not evidence
that all nine apps historically followed TDD.

## Next steps after review

1. Record clarification answers and approve app scope/public boundaries.
2. Assign training versus evaluation roles before creating teacher material; keep
   paper benchmark data and its derivatives out of training. An app cannot be its
   own held-out evaluation after its request/tests become a training example.
3. Select/create compact complete pytest acceptance suites with needed fixtures;
   every important testable requirement must map to a real executed check. Retain
   manual/live checks separately. Use fault probes for major behaviors.
4. Validate against the existing app or an explicitly adapted reference. A proposed
   new behavior unsupported by the current app is a gap, not a reason to weaken
   the requirement. Preserve suite revisions and traceability.
5. Prepare concise teacher reasoning, then measure the actual fully serialized
   request/clarifications/interface/reasoning/tests. Choose context from those
   lengths; current prompt-lengths.json is input-content-only, not final SFT size.
6. Measure baseline on evaluation tasks, run short thinking-plus-answer SFT and
   repeat matched evaluations, including the disjoint paper transfer subset.

One fine-tune can contain all training examples. Zero-shot inference means no
worked examples in the evaluation prompt. Whole-app output size will be measured
rather than inferred from repository regression-test totals.

Publish idempotently (existing owner responses are never overwritten):
`.venv/bin/python scripts/evaluation/publish_tdd_app_briefs.py`
After publication, change content only under a new revision/dataset.
