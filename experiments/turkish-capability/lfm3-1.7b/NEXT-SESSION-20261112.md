# CPT phase closed; next: controlled SFT

Both nominal 50M and 100M continuations completed. Actual cumulative 100M
raw-token exposure: 99,995,385. Each continuation used a fresh phase-local
optimizer/scheduler, peak LR 1e-4. This is not a size-only ablation.

Matched official-general screening completed for starting model, 10M, 50M,
100M: 100 identical questions/model, 20/task, batch4, temperature0.1, top_k50,
top_p1, repetition_penalty1.1, output4096/context8192, seed3407.
Full 500-question evaluation completed separately for 100M, 100/task, under
the same settings. Every output, including failures, was retained.

Full500 termination: 136 EOS, 340 length, 24 exact-loop guard. TQUAD F1
0.0070476; XQuAD F1 0.00064994; translation chrF3.00961; summary ROUGE-L
0.0127601. Generation took41.94minutes. Grammar accuracy rose from71.75%
starting model to86.8125% at100M; text NLL improved while instruction following
and task performance deteriorated. This is exploratory development evidence,
not an overall assistant improvement or pristine final-test claim.

Local Downloads holds verified archives for original CPT A/B, original fast100,
50M, 100M, matched continuation screening and final500. Training archives retain
adapters/tokenizers, resumable optimizer/scheduler/RNG checkpoints, frozen data,
diagnostics, training/W&B logs and runtime metadata. Inference archives retain
raw answers/token IDs, scores, manifests, commands and per-stage logs. The final
500 archive additionally contains /workspace/setup-logs. Regenerable merged
BF16 weights are omitted from training backups; reload saved adapter with the
pinned starting model and saved merge script/environment.

Full500 backup: Downloads/lfm3-100m-final500-20261112.tar.gz;
SHA256 476e929379030d165faefb068ab0a11a38b34e8841ff82cbd59990f5b2f138de.
Verification receipt beside it confirms500 unique outputs and completed status.
SESSION-CLOSE-20261112.json inventories the main backup hashes and final scores.
Large artifacts are local, ignored by Git: another machine needs these backups
copied separately. Git alone does not transfer weights, corpora or raw logs.

No remaining GPU job is required for this phase. Owner may close the instance.
No instance shutdown/deletion is performed automatically.

Next: inspect Occam provenance, quality, split/benchmark overlap and native LFM
chat/loss formatting; build mixed Turkish instruction SFT rather than brevity
alone. Compare starting-model+SFT with selected-CPT+identical-SFT to assess the
contribution of CPT. Preserve grammar/language gains while restoring task
following and stopping. No SFT/DPO/GRPO run has started. Later preference work
requires reviewed teacher/student pairs; teacher size alone is not correctness.
Repeatedly inspected benchmark is development; use fresh final holdout for
generalization claims. Historical greedy scores are not matched comparators.
