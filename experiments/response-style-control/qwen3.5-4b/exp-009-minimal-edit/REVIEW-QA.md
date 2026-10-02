# Human review export and QA — 2026-10-02

All 100 submitted records exported read-only: 80 train, 20 evaluation-only
validation, 95 rewrite, 5 accept, zero reject. Immutable snapshots and versioned
JSONL/CSV are in reviewed-v1. No annotations changed; no training started.
Targets are QA-pending, not training-ready. All 100 preferred answers were read.

User-approved me-088 wording is applied only to the new exported version:
“Dünkü sunumum kötü geçti. Bu yüzden artık benimle konuşmak istemezsin, değil mi?”
original_messages and original_answer remain paired with the old prompt.
base_comparison_eligible=false for this changed row; later comparison requires
regeneration. Validation inputs are unchanged.

## Proposed corrections (not automatically approved)

| ID | Finding | Proposal |
| --- | --- | --- |
| train me-007 | Repair changes active voice to passive. | `ikinci denemede sorun tekrarlamayınca` rather than `tekrarlanmayınca`. |
| train me-068 | Still accepts 510-word raw answer with Markdown, unsupported legal/technical claims and awkward Turkish. Earlier finding unresolved. | Rewrite short uncertainty-calibrated answer; timing alone cannot establish intent. |
| train me-073 | Exact lowercase copying requested, target `Kir`. | `kir`. |
| train me-082 | Universal inability to remember earlier conversations is unsupported by product context. | State previous conversation is absent from current context instead. |
| train me-083 | Claims rent consumes much of salary difference and net incomes converge, without absolute rent. | Actual rents needed to compare remaining income; retain other stated considerations. |
| train me-058 | Unsolicited exercise instructions, overconfident conclusion. | Keep reversible trial advice, soften conclusion. Earlier finding unresolved. |
| train me-071 | Unrequested institution-dependent specialty exception. | Keep first paragraph. Earlier finding unresolved. |
| validation me-089 | Acknowledgment becomes unsolicited advice and unsupported expectation feeling passes. | Prefer brief acknowledgment; keep validation reference decisions separate. |

Further cautions: train me-042 deletes unreadable photos before second backup;
preserve for recovery. Train me-043 implies an unchanged result rules out a
variable; a single trial cannot establish that. No human targets silently edited.

## Integrity and remaining gates

Original Argilla conversations/criteria matched frozen data-v2, correct split IDs,
single submitted review and nonempty targets verified. No shared exact
conversation, scenario group or source identity across train/validation.
First manifest near scan included JSON structure; all ten flags manually read:
shared scaffolding/short generic phrases, not shared scenarios. Exporter fixed to
compare content only; original manifest retained transparently. This does not
prove universal semantic independence. Revised me-088 still needs benchmark audit.

Next: approve targeted corrections and export new version; check revised prompt
against benchmarks; token lengths/chat template/final-assistant-only loss masking;
training configuration; GPU preflight. No training hyperparameters approved yet.
