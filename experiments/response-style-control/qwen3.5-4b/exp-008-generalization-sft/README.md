# exp-008-generalization-sft

## Status

Candidate authoring and human review only. No training dataset, config, GPU run,
or claim of model improvement exists for this experiment.

## Hypothesis

The previous SFT data taught surface patterns more readily than the decisions
behind them. A more varied, human-reviewed tranche containing both a rule and
its exceptions may improve generalization without teaching the model to always
ask a question, always answer in one sentence, or use a stock emotional phrase.

## Candidate pool

`data/candidates-v1.csv` has 100 proposed prompt/response pairs: 20 for each
of the five exp-006 failure families. The hidden-ambiguity group deliberately
contains 8 answerable, 8 clarification, and 4 conditional cases. Other groups
include both the desired behavior and closely related cases where it would be
wrong. Prompts vary in topic and register. Proposed responses are **drafts**, not
approved training targets.

Candidate CSV SHA-256:
`f27780c875b95b8ecb5561dd09e88c8ab9f64832195a054008e05a4d39aa1513`.
The authoring source is project-agent-written Turkish prompts and responses on
2026-09-27. Provider/model metadata for this authoring process must be recorded
before any public dataset release; the provisional license remains
`project-internal-draft`.

The 100 rows are not to be appended automatically to exp-006's 958 rows. Such
an append would leave the old synthetic core dominant and might recreate the
same problem. After review, choose a mixture or a distinct training recipe as
a separately documented experimental decision.

## Isolation and evaluation

- The exp-007 50-item set is a development diagnostic, not a final test. Its
  prompts and scenarios must not be used as training examples or paraphrase
  seeds. Also exclude all earlier benchmark items and their variants.
- Candidate IDs and boundary labels are retained so review can audit whether
  both sides of each decision were actually taught.
- Validate exact and near overlap, then manually inspect suspicious shared
  story structures. Lexical similarity alone cannot establish independence.
- If a model is eventually trained, freeze an untouched external or otherwise
  independently sourced test before claiming general Turkish improvement.

## Human review gate

Every proposed target needs an explicit accept, rewrite, or reject decision in
Argilla. Reject unsuitable prompts; rewrite any unnatural Turkish, invented
cause, missing qualification, repeated sentence, or misleading self-state
claim. Pay special attention to examples that are short because shortness is
not itself the target. Do not build a final SFT artifact until the review and
post-review QA are complete.

Argilla workspace: `sft-review`. All five groups currently have 20 pending
records. Review the draft response against the actual user message; selecting
`rewrite` requires entering a complete replacement reply.

| Family | Review URL |
| --- | --- |
| Hidden ambiguity | <http://127.0.0.1:6900/dataset/38f3e872-72cd-448b-91df-41f43682ac1d/annotation-mode?page=1&status=pending> |
| Unsupported completion | <http://127.0.0.1:6900/dataset/cfbee70f-8b4f-497c-8374-0756edfa9496/annotation-mode?page=1&status=pending> |
| Turkish precision | <http://127.0.0.1:6900/dataset/eccf1194-dd2d-471e-adf0-07fce809555f/annotation-mode?page=1&status=pending> |
| Calibrated emotional | <http://127.0.0.1:6900/dataset/e8d95272-c285-4c1a-8aea-76cf67edf8be/annotation-mode?page=1&status=pending> |
| Consistency and integrity | <http://127.0.0.1:6900/dataset/d0179d5e-6471-448c-a97f-6311be517793/annotation-mode?page=1&status=pending> |
