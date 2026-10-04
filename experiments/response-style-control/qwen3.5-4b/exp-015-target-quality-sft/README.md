# exp-015-target-quality-sft (E)

## Status

Completed SFT/inference2026-10-04; urgent essential recovery hash-verified.
Human32 review completed: E24pass/3partial/5fail versus F26/3/3 and base17/11/4.
E is completed, not selected; F is the phase's experimental style candidate.
Current SFT phase closed; sharing preparations live in docs/publication.
All33 training and12 control reviews completed and exported read-only.
Approved data-reviewed-v1, controls-reviewed-v1, config-reviewed-v1.yaml and
training-preflight-v1 remain frozen. E genuine checks passed before later user
smoke/tiny waiver; F uses explicit waiver, actual masks and same-pod reload proof.
See GPU-HANDOFF.md and gpu-results-v1. config.yaml remains blocked
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

Active human review: [simplified32-item comparison](http://127.0.0.1:6900/dataset/ff9f4e4c-796b-4595-aa33-0229137b6258/annotation-mode?page=1&status=pending).
Best-output selection P/Q/R/S/tie/neither and one pass/partial/fail grade for each
output; optional notes, with tied positions specified when selecting tie.
Same blinded positions and original
answers/reference as the preserved detailed queue. See EVALUATION.md's user-approved
v3 amendment: one grade per output, not separate semantic/Turkish/style metrics.
Recreate/verify idempotently with `import_simple_comparison.py --results-root`
pointing to the external `exp-015-016-paired/review-outputs` artifact folder.

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

E40steps/4epochs/110.012seconds; F40steps/3.0769epochs/106.8984seconds.
Actual supervised tokens E20484/F19131; equal steps are not equal exposure.
Base/C/E/F128answers all nativeEOS, exact per-item render/token parity verified.
Historical C20 outputs/token IDs reproduce20/20 exactly. No semantic-quality
claim yet. Human comparison32 is ready:
[blind review](http://127.0.0.1:6900/dataset/3b2cf5b1-13d2-4ea1-859b-2faa16c029ad/annotation-mode?page=1&status=pending).
Final adapters and155 essential files locally hash-verified; GPU no longer needed.
Full1.45GB backup was NOT fully downloaded. User urgently requested essentials;
optimizer/RNG/intermediate/diagnostic weights omitted, no exact checkpoint resume.
See gpu-results-v1/essential-recovery-verification.json; weights stay outsideGit.

Review/freeze complete: E5121/F6216 target tokens
per dataset, max sequence514, no truncation; EOS/masks verified. Final audit5888
cross-split comparisons found no exact/near/long-reference/embedded-eval flags.
One short shared listening acknowledgment is documented, not removed. Semantic
signoff is evidence-bounded, not universal independence proof. Human outcome review next.
