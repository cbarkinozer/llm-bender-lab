# exp-015-target-quality-sft (E)

## Status

Planned; all33 training and12 control reviews completed and exported read-only.
Approved data-reviewed-v1, controls-reviewed-v1, config-reviewed-v1.yaml and
training-preflight-v1 are frozen. CPU readiness passed; GPU gates pending.
No GPU run, model inference or W&B run started. config.yaml remains blocked
draft history; use the reviewed config, never the draft.

## Question and hypothesis

Do necessary repairs to C's target answers improve semantic quality without
changing the80 input questions? Compare E with C/exp013, not with D's6epochs.
Parent is exp013; initialize a new adapter from the pinned base, not C weights.

## Intervention

Audit24 existing records, four each for Turkish editing, conditional decisions,
mechanisms/trade-offs, faithful summaries, selective clarification and interaction.
Propose9 repairs; retain15 already-good audited targets and56 other rows exactly.
All80 input messages, IDs, categories and row positions stay unchanged.
Actual proposed changes: me006/041/043/046/048/052/055/057/088.
See `data-draft-v3/target-audit-24.jsonl` for reasons and before/after answers.
Summary targets were already faithful; do not manufacture defects. The original
grammar targets also mostly work; one punctuation repair is proposed.

Repairs clarify load versus priority, bounded causal inference, Wi-Fi diagnosis,
habit mechanisms, missing decision information, safe deletion conditions and
neutral conversational availability. They are not validated model improvements.
Original prompts cannot be changed through the answer-review workflow.

## Data and review

[Review33 training candidates](http://127.0.0.1:6900/dataset/ecf0fa64-79bd-4b9e-bd7a-2d80b2fdcb3e/annotation-mode?page=1&status=pending):
9 old-target repairs shared by E/F,24 new questions used only by F.
Accept or rewrite with the complete answer; reject with notes if a prompt needs
repair. No annotation is fabricated; the15 retained audit rows need no new review.

Review completed:31 rewrite/2 accept; controls12 rewrite. All user final answers
preserved. Nine E targets differ from C;71 others unchanged. See
[final leakage review](data-reviewed-v1/SEMANTIC-LEAKAGE-REVIEW.md).

There are also12 separate evaluation-only control references, two per skill.
[Review12 control references](http://127.0.0.1:6900/dataset/bd1ad5d2-2a74-4507-bf91-865ca3e3a15e/annotation-mode?page=1&status=pending).
See annotation-links-v2.json for their active queue. Approve/freeze before any
compared model outputs. They never enter train, replay or validation loss.
Original20 development records/reference answers remain byte-identical, including
disputed me089; report sensitivity without089, do not silently repair its gold.
80/20 is the original split; adding24 training rows and12 separate controls does
not create a new random80/20 split. Historical train and evaluation remain fixed.

No external teacher API or third-party text was used. Project-agent-authored
drafts, not base-answer summaries; exact author model/sampling not exposed.
Store resulting artifacts and hashes rather than claim deterministic regeneration.
No public licensing claim. Approval precedes any training.

## Training recipe

Pinned unsloth/Qwen3.5-4B, revision3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636.
BF16 LoRA, attention+MLP, rank/alpha16/16, LR1e-4, batch1×8, seed3407,
max sequence1024, AdamW8bit, cosine, warmup2, no packing/dropout/weight decay.
Explicit40 optimizer steps, step10 saves/evaluation, final step40 preselected.
Nominal epochs4 overridden by max_steps40. Fresh base for E and F independently.
Shared exp009 runner now honors explicit row counts/max_steps/step strategies;
old configs retain epoch/default behavior. Required GPU gates remain outstanding;
no prior pair's smoke/tiny/reload waiver is inherited.

Draft E has5133 supervised tokens per dataset versus C5653 (-9.2%). Necessary
explanations became more focused, not universally longer. This intervention
changes target content/style/length together, not an isolated length or causal
estimate. Equal40 steps do not imply equal tokens or update magnitude.

## Evaluation and recovery

See [EVALUATION.md](EVALUATION.md) for frozen proposal: same-backend base/C/E/F,
32 items, per-item blinded balanced ordering, separate semantic/Turkish/style
grades and unambiguous ties. No outputs yet; report small-sample uncertainty.
Verify runtime configs/step40/row counts, actual labels, checkpoint reload,
raw outputs/termination and all artifact hashes before declaring GPU disposable.
Do not terminate an instance automatically.

## Local commands

Existing CPU venv: `C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe`.
Run `prepare_pair.py`, then `test_preparation.py`. Argilla SDK lives in exp001's
annotation venv; run `import_review.py` to create/verify queues idempotently.
After33 training and12 control reviews, `export_review.py` reads annotations
without mutation, rejects pending/rejected/missing rewrites and rechecks hashes,
leakage, EOS/masks before freezing. Export now completed. Run
audit_reviewed_splits.py and verify_ready.py for final approved artifact checks.

## Preparation lessons

v1 local draft audit accidentally skipped historical CSV training inventories;
corrected in v2 and tested (3500 historical entries, not distinct rows).
Before evaluation, v2 control010 was recognized as too close to older B's
resolved-file-format scenario. Replaced in v3 by an atlas-purpose scenario.
Original snapshots and old control queue are retained, never authoritative.
Active training fields unchanged, active controls are v2 queue/v3 data.
No annotations were moved, overwritten or fabricated.

## Results and next step

No training/quality results. Review/freeze complete: E5121/F6216 target tokens
per dataset, max sequence514, no truncation; EOS/masks verified. Final audit5888
cross-split comparisons found no exact/near/long-reference/embedded-eval flags.
One short shared listening acknowledgment is documented, not removed. Semantic
signoff is evidence-bounded, not universal independence proof. GPU checks next.
