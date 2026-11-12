# Owner-approved continuation: nominal 50M and 100M

Continue saved CPT-B (9,995,322 raw tokens) with fresh FineWeb2 TRAIN prose:
approximately40M new tokens to the50M milestone, then approximately50M more
to100M. No replay of existing parent Wiki/web rows. Exact cumulative raw-token
counts and trainer EOS/packed exposure are recorded; milestone names are nominal.

Two phase-local schedules: fresh AdamW, peak LR1e-4, warmup5%, cosine decay to
zero, one epoch each; rank64/alpha64/dropout0, the existing nine projection
targets, frozen embeddings/head, BF16, sequence2048, batch2/accum4, seed3407.
This lowers the peak relative to CPT-B's2e-4 and is a restarted continuation,
not one uninterrupted100M run. Source mixture also changes: new exposure is web
only, so cumulative Wiki share decreases. Do not claim a size-only ablation.

New data use the same pinned FineWeb2 revision and four TRAIN shards, excluding
all parent rows and protected evaluation text. Full five-word containment checks
cover protected text/original Wiki; cross-training candidate search uses twelve
bottom-hash anchors (at least two shared), then exact containment. This bounds
memory but is approximate and does not guarantee all semantic duplicates are
removed. Retain upstream metadata, tokenizer counts, IDs/hashes, host caps,
language/prose/repetition filters, and selection/rejection counters.

Initial sampling exposed download/crack pages, product catalogs, game-cheat
pages and commercial health/sexual-product pages. The final builder adds
review-informed exclusions. A Windows text-decoding problem in intermediate
forked filters was caught before any new model training; original UTF8 filters
were restored and Turkish-pattern checks pass. v01-v04 selection attempts are
inactive; v05 is the candidate reviewed for training. No claim of factual or
uniform editorial quality. All original10M datasets/checkpoints remain unchanged.

Each stage must pass real parent-adapter/model/data identity checks, smoke,
packed-label and finite/nonzero-gradient audits, frozen-embedding audit and
tiny-overfit loss reduction before its full run. Parent LoRA is loaded trainable;
no second adapter is stacked. The100M stage initializes from the completed50M
adapter with a fresh phase-local optimizer/scheduler.

Save resumable Trainer checkpoints every200 updates, retain the last two,
and retain final adapters, optimizer/scheduler/RNG, effective arguments, trainer
state, token exposure, diagnostics, frozen data, logs and W&B identities at both
milestones. SIGTERM/SIGINT requests a graceful save at the next optimizer-step
boundary. There is NO automatic training wall-time limit (owner override).
If interrupted, do not start the next phase. Resume with the saved Trainer
checkpoint and identical phase config; do not reconstruct optimizer state from
the adapter alone.

W&B training only. No inference or merge job is queued. Owner may defer all
generation to tomorrow. Later screening100/expanded200/finalist500 must use a
matched base and frozen decoding; official general preset remains a candidate,
not silently mixed with existing greedy/rp1.15 outputs.

Measured prior speed suggests about4h additional training total, plus data,
diagnostics, periodic saves and transfers. Owner was asked to return about22:00
Europe/Istanbul on2026-11-12. This is an ETA, not a timeout.

Remote: root@77.235.122.199:17103, /workspace/llm-bender-lab. Preparation logs:
/workspace/setup-logs/continuation-data-v05.log. Training log:
/workspace/setup-logs/continuation-training.log.

Local hidden recovery helper:
C:/Users/barkin/Downloads/lfm3-continuation-recovery-20261112.py.
It independently polls for completed milestone receipts, downloads archives,
verifies every member, restores missing local files and records status in
C:/Users/barkin/Downloads/LFM3-CPT-CONTINUATION-STATUS.json. This is an ordinary
background process, with no model polling or token usage. Check its .log and
.stderr.log on return. No instance shutdown or deletion is automatic.

New experiment IDs: exp-003-cpt-cont-50m, exp-004-cpt-cont-100m. Raw data,
checkpoints and logs are ignored. Source/configs/manifest metadata stay reviewable.
Current changes are not committed.
