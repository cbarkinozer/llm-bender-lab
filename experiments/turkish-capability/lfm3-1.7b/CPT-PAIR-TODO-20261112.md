# Turkish CPT pair: preparation and GPU execution

Owner-approved 2026-11-12. This supersedes the older Wikipedia-only deferral and
70/30 mixture proposals. No training has happened. Do not reuse the old SSH pod.

## Questions and fixed decisions

- A: Does the existing 2,201,862-token Wikipedia corpus improve Turkish modeling?
- B: Does that identical Wikipedia corpus plus 7,793,460 FineWeb2 tokens
  improve the broader adaptation recipe? Final total: 9,995,322 raw tokens
  (nominal 10M, 0.047% below target after four sample-review exclusions).
- A and B independently start from LiquidAI/LFM3-1.7B revision
  0dc4268b561499c648c7ba7c9466bf3d8d01517a. Neither starts from the other's adapter.
- Same rank64/alpha64/dropout0, LR2e-4, cosine, warmup5%, one epoch, BF16,
  batch2/accum4, context2048, wrapped packing, raw-text all-token loss, seed3407.
  Train the nine notebook projection targets; keep embeddings frozen.
- B changes both quantity and source distribution, with more optimizer updates.
  This compares practical recipes, not an isolated causal source or size effect.
- W&B training only. Names identify wiki-2m2 versus wiki-fineweb-10m, rank, LR,
  epoch and seed. Diagnostics have explicit smoke/tiny-overfit suffixes.

## Before renting a pod

- [x] Recover historical Qwen base/F raw answers and verify archive/member hashes.
- [x] Complete LFM baseline; recover all 123 archived files and inspect paired examples.
- [x] Fix the two questions and preserve identical Wikipedia rows in A and B.
- [x] Add train-only pinned FineWeb builder with metadata, bounded shuffled sampling,
  host-token caps, language/length/repetition filtering and protected-text checks.
- [x] Finish mixed corpus selection and freeze its IDs, hashes and token profile.
- [x] Inspect 30 seeded web previews and six complete samples; record exact review
  scope, issues and observed topic/style coverage. These are agent inspections,
  not independent human certification. Do not claim native topic labels or equality.
- [x] Freeze separate exp-001-wiki-cpt and exp-002-mixed-cpt complete configs/data.
- [x] Verify counts, hashes, exact/paragraph/near-duplicate protection and shared Wiki IDs.
- [x] Build private transfer archive and verify every member against its receipt.
- [x] Mark CPU preparation done only once those actual artifacts exist.

Builder: scripts/datasets/prepare_lfm3_cpt_pair.py. It uses official FineWeb2 revision
af9c13333eb981300149d5ca60a8e9d659b276b9, tur_Latn TRAIN only, four pinned shards,
bounded shuffle seed3407 and host <=1% web token budget. It retains every original
selected column and adds source split/revision, host and LFM token count. A host
cap does not merge sibling subdomains. This is a bounded convenience frame, not
a representative sample of all Turkish web or a certified topic-balanced corpus.

Preparation quality review: earlier private candidates exposed Wikipedia recrawls,
adult/gambling advertising, translated hotel templates, download walls and short
navigation-heavy pages. The final v04 builder adds recorded exclusions plus
>=120 words and >=4 substantial sentence spans. These heuristics bias selection
toward prose and cannot certify factual correctness. Sampled crawl coverage is
2013-2014; report that historical frame explicitly rather than claiming recency.
Final v05 applies four documented sample-review exclusions to v04. Older
candidates are retained privately for diagnosis, not used in either run.
Final web coverage: 6,466 documents from 4,074 hosts; largest host supplies
66,431 tokens (0.852% of web tokens). This measures host diversity, not topic balance.
See cpt-pair-sample-review-v01.json and cpt-pair-integrity-v01.json.

Streaming selection emitted Windows HTTP-prefetch shutdown errors after writing
complete artifacts; logs are retained. The later offline curation and independent
hash/tokenizer audit both exited successfully. No ignored streaming error is being
treated as evidence of correctness; frozen outputs passed separate checks.

Raw data, models, GPU gates and results stay ignored/private; code, pins, profiles
and manifests are versioned. Preserve upstream attribution/terms. No public raw
data release is implied by this preparation.

## After receiving a fresh RTX4090 SSH endpoint

1. Authenticate with the existing matching key; inspect actual GPU, free disk,
   driver, OS, Python and persistent storage. No local Docker. Capture environment.
2. Transfer verified source/data archive and verify remote SHA/member hashes before
   extraction. Transfer .env W&B credential privately as bytes into a chmod600 file
   outside artifacts; never print it or archive it.
3. Recreate the already measured Transformers training environment and isolated
   native vLLM environment from the baseline freeze. Stable vLLM0.33 lacked LFM3;
   use the recorded nightly commit 7cc0a8a2b1ef6888b44973933c8a208e91122229.
   Run pip check, CUDA/BF16, pinned model/tokenizer checks and synthetic inference.
   A fresh model download/setup may dominate initial time.
4. Reuse original baseline outputs. Do not rerun CETVEL500 unless the protocol or
   environment changes materially; any changed protocol needs matched baseline.
5. For EACH experiment run train-smoke (2 steps), audit actual packed batch/labels,
   finite nonzero LoRA gradients, frozen embeddings and peak memory; then run the
   2-document tiny-overfit diagnostic (30 steps), inspect initial/final loss.
   Record real diagnostic evidence and bind gate to that experiment manifest SHA
   and pinned model. Never fabricate gate flags or reuse the diagnostic adapter.
6. Use measured tokens/sec and memory to revise each ETA before the long run.
   No measured training ETA exists yet; earlier hour ranges were rough estimates.
   If OOM, stop and record any recipe change before continuing both matched arms.
7. Train A from a fresh original checkpoint, then save adapter/tokenizer, effective
   config, trainer state, optimizer/scheduler/RNG, exposure, logs and W&B identity.
   Validate adapter save/reload, merge BF16 for vLLM and inspect merge diagnostics.
8. Evaluate A on the exact CETVEL500, TurBLiMP1600 and Wiki100/Web100 packets;
   retain all answers, including length/loop/timeout cases, and all scores/logs.
   Archive/download/verify A before spending further GPU time if practical.
9. Train B independently from the original checkpoint, then perform the identical
   save/reload/merge/evaluation/recovery procedure. Do not use A weights.
10. Download BOTH adapters/tokenizers, optimizer state, manifests, exact source/data,
    raw predictions, scores, stderr/stdout, failed-attempt logs, environment freezes,
    training throughput/memory/timings and W&B run receipts. Include merged models
    or document verified reconstruction from saved adapters and pinned base.
11. Verify archive SHA and EVERY member locally. Separately check each run completed,
    adapter reload evidence, 500 unique answers, 1600 grammar pairs and 200 text
    eval docs; correct counts do not prove answer quality. Verify W&B sync.
12. Tell owner GPU is safe to close only after both recovery and completion checks.
    Do not close or delete anything automatically.

Entrypoints (repo root on Linux):

```bash
PY=/workspace/.venvs/lfm3/bin/python
E=experiments/turkish-capability/lfm3-1.7b/exp-001-wiki-cpt
$PY scripts/evaluation/run_lfm3_stage.py train-smoke --experiment-dir "$E"
$PY scripts/evaluation/run_lfm3_stage.py overfit --experiment-dir "$E"
# Review diagnostic files and create evidence-bound GPU gate before this command.
$PY scripts/evaluation/run_lfm3_stage.py train --experiment-dir "$E"
$PY scripts/evaluation/merge_lfm3_cpt.py --experiment-dir "$E" --training-dir "$E/results-local/cpt-v01"
$PY scripts/evaluation/run_lfm3_stage.py after --experiment-dir "$E"
$PY scripts/evaluation/compare_lfm3_cpt.py --experiment-dir "$E" --baseline-dir experiments/turkish-capability/lfm3-1.7b/exp-000-baseline
# Repeat with E=.../exp-002-mixed-cpt after its own diagnostic gates.
```

## Reading results and next SFT step

Primary CPT diagnostics: held-out Wikipedia and web NLL separately (same tokenizer).
Supporting: grammar accuracy, each CETVEL task score, answer length, termination,
and blinded semantic correctness/grounding on the same seeded examples. Do not
reward merely shorter but incomplete/incorrect answers. No pooled score or English
retention claim; this suite has no matched English retention baseline. Web eval is
now same-source held-out. Public pretraining contamination and single-seed noise
remain limitations. Report differences as exploratory, with paired uncertainty
where meaningful; do not promise improvement or call either model selected yet.

Owner's later deployment hypothesis: CPT -> Occam SFT for concise, correct Turkish
answers. This is a NEW sequential branch and supersedes independent-arm intent
only for that future branch, not for the original standalone method comparison.
Before SFT: inspect Occam provenance/splits and native LFM formatting, exclude all
our evaluation prompts/answers/near-duplicates, inspect rationale/answer loss policy
and suitability of targets. Compare original+same SFT vs selected CPT+same SFT to
isolate CPT contribution if budget allows. Concision can improve overlap metrics
without increasing factual competence; retain both correctness and length reports.
No Occam data has been ingested into these CPT runs.
