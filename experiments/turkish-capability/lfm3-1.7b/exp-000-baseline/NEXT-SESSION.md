# Resume after baseline, 2026-11-11

LATEST 2026-11-12: owner now requests two independent CPT runs (existing 2.202M
Wikipedia, and 10M total with the identical Wiki plus ~7.798M official FineWeb2
train tokens), followed later by a separate CPT -> Occam SFT branch. Current
source of truth: ../CPT-PAIR-TODO-20261112.md. Older deferral/70:30/Wiki-only
candidate proposals below are historical. No GPU training has run yet.

User explicitly deferred CPT today. No CPT, training smoke or overfit has run. Today's original future pilot remains2.2M Wikipedia tokens;10M/50M are future work only, not today's scope. Candidate10M Wiki is prepared but inactive; proposed FineWeb mixture is not prepared/activated.

Baseline complete: CETVEL500,496EOS/4length, no dropped outputs; generation2883.77s/171991tokens. TurBLiMP1600 macro71.75%. Text eval200 complete. Full results/logs/environment/code/data archived remote /workspace/lfm3-baseline-completed-20261111.tar.gz, adjacent receipt, SHA4049d61855c57ab19f9e275c53c474f244401fdc26310887f41ce20106550b48. Local archive and all123 member hashes verified;500 unique outputs,200 text eval docs,1600 pairs and all stage exit codes checked. Owner informed GPU can close. See baseline-local-recovery-v01.json.

User clarified W&B is for CPT training only, not inference. Baseline upload had already completed before clarification, run divq6zo8 in c-barkinozer/lfm3-turkish-post-training; no cloud record deleted. Future automatic evaluation upload removed from run_lfm3_stage.py; training tracking remains enabled.

Pod endpoint ssh2.vast.ai port11790; key C:/Users/barkin/.ssh/lfm3_vast_20261111. Do not assume pod survives later sessions. Full detailed setup/runtime notes in GPU-SESSION-20261111.md and Downloads/LFM3-CPT-CLAUDE-HANDOFF-20261111.txt; older training-scope-pending wording is superseded by today's explicit deferral. Before future CPT, inspect real baseline outputs, run actual GPU training smoke/label audit/tiny-overfit and bind gates to active model/data manifest. No full-training gate exists yet. Owner authorized a local commit on2026-11-11; see git log for its identity.


Next morning checklist: TODO-20261112.md and Downloads/LFM3-YARIN-TODO-20261112.txt. Owner is closing the old pod; do not assume endpoint remains active. Local archive reverified123/123 on final closure check. Base weights/venvs/caches are re-downloadable and not included; no CPT adapter exists because training never started.

Owner latest: remind them next session to retrieve Qwen raw backup from their Windows desktop/tower. Discuss2.2M pilot then5M/10M/20M/50M/up to100M scaling; not automatic execution. See updated TODO for nested subsets, constant data mix and checkpoint-vs-independent-run caveat.

2026-11-12 update: owner pulled ee4fba2 containing original Qwen recovery archive and raw base/F answers. Archive and member hashes verified locally; all500 Qwen base IDs/prompts/document hashes matched LFM. The missing-backup reminder above is resolved. Downloads/LFM3-QWEN-BASELINE-20261111.html/.txt now contain the same five seeded examples with actual Qwen base answers. No new inference or GPU needed.

2026-11-12 CPU pair preparation completed: exp-001-wiki-cpt 2,201,862 raw tokens; exp-002-mixed-cpt 9,995,322 raw tokens including identical Wiki plus 7,793,460 FineWeb TRAIN tokens. Sample review, independent token/hash/nesting audit and launch-gate checks recorded at model root. Use ../CPT-PAIR-TODO-20261112.md; request fresh SSH endpoint for real GPU diagnostics. No full-run GPU gates exist.
