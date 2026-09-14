# Qwen3.5-4B Adyghe capability experiments

This experiment line investigates Adyghe (West Circassian, `ady`) capability
without contaminating its evaluation data.

The current root diagnostic artifact is
[`AdygheBench v0.2-candidate`](../../../benchmarks/adigebench/v0.2-candidate/README.md).
It is development-only pending native review. The underlying user-authored
source is authorized for training; a resulting score is curriculum mastery,
not unseen-Adyghe generalization. The original v0.1-candidate is preserved for
lineage.

Fine-tuning may use the user-authored corpus in a later, explicitly labelled
curriculum-mastery experiment. An independently authored holdout is required
for a generalization claim.

The current high-quality SFT source policy is deliberately narrow:

- active no-leak split: the reviewed Adyghe--English Wiktionary lexicon,
  excluding exact benchmark overlap;
- retained-but-excluded: the user-authored source, because it is a parent
  source of AdygheBench;
- validation: source-record-group-held-out data, not the benchmark; and
- sole initial benchmark: AdygheBench v0.2-candidate.

Wikipedia and the synthetic Adyghe--Russian corpus are not part of this first
SFT experiment.

| ID | Status | Main change | Notes |
| --- | --- | --- | --- |
| exp-000 | completed | benchmark development | 200-item initial candidate |
| exp-001 | candidate | benchmark curation | 188-item v0.2 candidate |
| exp-002 | completed | external-corpus policy | synthetic Russian pivot excluded |
| exp-003 | ready | initial SFT data | clean CSV split + separate benchmark CSV |
