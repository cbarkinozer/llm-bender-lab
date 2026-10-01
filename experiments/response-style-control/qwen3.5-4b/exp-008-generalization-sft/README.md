# exp-008-generalization-sft

## Status

All 100 initial Argilla reviews were completed and exported: 82 rewrites,
18 accepts, zero rejects. The original reviews are preserved in
`data/generalization-reviewed-100.jsonl`; the standalone 100-row CSV is a
provisional artifact pending semantic QA. No exp-008 GPU run has started.

Structural, source-binding, canonical-LF hash, exact-overlap, and near-overlap
checks passed. The full response review flagged 11 replies containing unsupported
certainty or meaning changes; see `evaluation/reviewed-quality-report.json`.
Proposed corrections are in a separate Argilla queue:
<http://127.0.0.1:6900/dataset/27f8c155-41ca-4d6f-9856-2c8004a1777f/annotation-mode>.
Original human annotations were not overwritten. These corrections need review
before the training artifact can be frozen.

There are 958 exp-006 examples and 100 new exp-008 examples, totaling 1,058
across separate artifacts. This is not a merged training set. Exp-007 contributes
50 development benchmark questions, excluded from training.

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

Argilla workspace: `sft-review`. All five initial groups have 20 completed
records. Review the draft response against the actual user message; selecting
`rewrite` requires entering a complete replacement reply.

| Family | Review URL |
| --- | --- |
| Hidden ambiguity | <http://127.0.0.1:6900/dataset/b109486c-d31c-47b4-bba8-a7c9d92a4ad1/annotation-mode> |
| Unsupported completion | <http://127.0.0.1:6900/dataset/ffdfbc36-c11e-483e-afe5-62516077109f/annotation-mode> |
| Turkish precision | <http://127.0.0.1:6900/dataset/09b844e9-7032-4f22-8de7-ace9454fa07a/annotation-mode> |
| Calibrated emotional | <http://127.0.0.1:6900/dataset/53697ccd-98b4-4dee-a77a-99e806ece0d2/annotation-mode> |
| Consistency and integrity | <http://127.0.0.1:6900/dataset/48d7f05b-cc0d-4667-b74b-3cb1b7badc71/annotation-mode> |

Dataset IDs are local to each Argilla database; running the importers prints
the current instance's links. Git transfers files, not the Argilla database.

## Remaining work

1. Complete the 11-item QA correction review and export it separately; apply
   accepted corrections with provenance while preserving the initial exports.
2. Complete exp-007 benchmark authoring review and freeze its development protocol.
3. Revalidate effective targets, including conceptual overlap and the requested
   rule/exception coverage. Lexical overlap checks alone are insufficient.
4. Document the training mixture and recipe; do not automatically append the
   tranche to the older 958 rows. Freeze independent evaluation before a quality claim.
5. Capture comparable base generations, run representation, smoke, and tiny-overfit
   checks on the GPU, then full training and blind comparison.

Re-export initial annotations using `export_reviews.py`; validate with
`validate_candidates.py` and `validate_reviews.py`. The latter writes a quality
report and explicitly records semantic blockers even when structural checks pass.
