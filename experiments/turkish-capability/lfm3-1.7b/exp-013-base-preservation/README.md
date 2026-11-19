# exp-013-base-preservation

Training and inference completed2026-11-19. Owner blind review pending. Primary checkpoint69 was fixed before inference; later113 retained as backup.

Hypothesis: a verified arithmetic/reasoning and English retention supplement reduces regressions while maintaining useful Turkish.

Parent/control: exp-012-base-bilingual. Main change: 25% row slots retention supplement with one original row reweighted per update to match supervised-token budgets.
Recipe: LR1e-4, rank32/alpha64, micro2/accum4, 113 steps, cosine, warmup6, BF16.
Both new adapters start independently from original base; no continuation of an SFT adapter.
The historical trainer path name `cpt-merged` is a symlink to original base for these runs; receipt proves identity.

Evaluation: fresh frozen packet on original base and both historical SFT candidates before training, then both new checkpoint69 adapters. Raw outputs and deterministic arithmetic/reference checks, followed by blinded owner preference. Existing consumed evaluation16 is used ONLY for a separate thinking-mode diagnostic.
One seed and small synthetic pilot: no broad no-forgetting or release-quality claim.
Source/provider owner decisions remain as recorded. No publication authorized.
Results: both pipeline gates and adapter reloads passed, but symbolic arithmetic stayed at1/8 in both thinking modes. No demonstrated overall improvement. See [measured session results](../PRESERVATION-SESSION-RESULTS.md) and the16-record Argilla review.

This README is the post-run status. Its frozen pre-run version remains in the session input archive; reproduce from the source snapshots and execution addenda, not a mutable post-run README.
