# Frozen paired-development plan — 2026-10-03

No larger validation set is introduced. The source remains
exp009/reviewed-v2/validation-reviewed.jsonl, SHA-256
43e10beed85aa6fbbda768a124c7a2e6feb3743ddc79c2e38098c7982cfad429.
Never train on its questions, desired answers or scenario paraphrases.

## Comparisons and candidates

- A final scheduled epoch4 versus saved exp010 epoch2-v2: longer-training recipe.
- B final scheduled epoch4 versus A final scheduled epoch4: coverage intervention.
- Saved base and exp009 outputs are contextual references, not additional runs.
- No automatic claim of underfit, rank bottleneck or catastrophic forgetting.
- No best-checkpoint hunting on these repeatedly inspected development items.

Unsloth/Transformers BF16, same pinned base/tokenizer and native rendered prompts,
batch1, greedy, seed3407, repetition_penalty1.05, thinking disabled, no additional
system prompt. Use evaluate_adapter.py --bounded: 4096-token budget, native EOS,
exact-token loop/180-second safeguards. A safeguard or budget stop is incomplete,
not EOS and not a corrected answer. Keep raw token IDs and all failures.
Do not compare a new prompted style policy against an unprompted reference.
Saved base inference was vLLM, so its numerical/backend difference stays explicit.

## Eight primary diagnostic items

These are post-feedback development anchors, not unbiased new scoring criteria.
Accept grounded alternative wording/recommendations; do not demand reference text.

| ID | Substance anchor |
| --- | --- |
| me-049 | Plausible mechanisms, not a personal diagnosis; concrete actions with an explanation of why each addresses the mechanism; no invented physiology or repetition. |
| me-050 | Distinguish work-surface need from unclear boundaries; coherent cost/space trade-offs, concrete feasible moves, justified first action; no invented user constraints. Alternatives can pass if justified. |
| me-059 | Use confirmed availability, room and readiness; make the recommendation without restarting clarification. |
| me-069 | Same-week co-occurrence is insufficient causal evidence; alternatives are hypothetical; useful checks must not be sold as causal proof. |
| me-070 | Later success supplies no earlier failure cause. |
| me-079 | Updated veri-sharing rules, not unchanged vergi rate. |
| me-089 | Natural neutral acknowledgment, no fabricated feelings/experience or unsolicited diagnosis/advice. Reflection need not match the reference literally. |
| me-090 | Respect the explicit no-advice request; no solution list, invented shared experience or performative emotion. |

For each item: substance pass/partial/fail, Turkish naturalness, then unnecessary
formatting/emoji, verbosity, repetition and stopping. Shortness cannot compensate
for a factual error, unsupported cause or contradictory recommendation. Useful
lists and requested formatting are permitted; no universal Markdown prohibition.
Report item-level wins/ties/losses; eight items are too few for robust broad claims.
Review all 12 remaining items as lightweight regression controls, including exact
word/character preservation and requested format. No need to reannotate old outputs.

## Small diagnostics on the next GPU

Inspect a fixed sample of training prompts separately to distinguish failure to
learn targets from failure to generalize. Training fit is not validation success.
For comparing the arms on shared training examples, use the same retained IDs;
do not score B on its new examples as though A trained on those examples.

Use a small subset of the same evaluation prompts for base/A/B with
enable_thinking=True and False; do not rely on Qwen3 slash commands. Save rendered
inputs, raw reasoning/final output, final_answer_emitted, token counts, EOS and
truncation. This is a supporting mode-preservation diagnostic, not a new primary
protocol or a claim that an empty masked think prefix caused reasoning collapse.
