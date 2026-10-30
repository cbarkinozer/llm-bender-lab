# miniature-llms — draft core acceptance map

Complete minimal educational repo; new composition/causality/checkpoint/training acceptance tests are required. Existing RMSNorm/RoPE checks alone are insufficient.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Components obey public tensor/dimension contracts. | Tiny embedding/model inputs produce exact declared shapes; incompatible head/model dimensions raise the agreed error. | unit |
| R2 | RMSNorm implements the numeric scaling contract. | For x=[3,4], epsilon=0 and scale=[2,3], output is [6,12]/sqrt(12.5); zero input with positive epsilon is finite zero. | unit |
| R3 | RoPE applies positions on the sequence axis. | Position zero is identity for every head; at position one a [1,0] pair rotates to [cos(1),sin(1)], independent of head index. | unit |
| R4 | Causal attention does not leak future tokens. | With fixed weights, changing tokens only after position k leaves outputs up through k numerically unchanged; at least one later output can change. | unit/integration |
| R5 | Gradient and checkpoint paths work end to end. | Fixed scalar-loss fixture produces expected gradient direction/values for a controlled component; checkpoint reload preserves all model logits on a fixed batch. | integration |
| R6 | Tiny training/generation workflow is usable and bounded. | Fixed seed/corpus, agreed small step budget and optimizer produce finite loss below the initial value under a specified stable fixture; generation stops at its token budget. | integration |

## Public test boundary (proposal)

Component constructors/forward tensor conventions and public tiny-model train/save/load/generate operations; not source-folder/private-helper predictions.

## Decisions still needing agreement

- Approve this first-version component set rather than all 25 source-repo components.
- Agree exact model/loss/optimizer/corpus and tolerances before using training-loss reduction as an oracle.

## Manual / live checks

- Educational clarity of explanations and actual CPU runtime of the demo.
- A tiny training check is a smoke, not proof that every architecture or learned output is correct.

## Candidate existing evidence — not automatically selected

- `tests/test_normalization_and_rope.py`

Source revision: `d369337b151cedd9c39fbc654dfed8236344a7cd`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
