# User-authored Adyghe source v0.1

This is the normalized, model-neutral form of the material supplied by the
data author. It is authorized for this project's training use.

It contains orthography/romanization, short bilingual phrases, vocabulary,
parallel passages, and story vocabulary. It is **not yet an SFT dataset**:
later SFT construction must turn these records into explicit prompt/answer
messages and record its own trainable-token and leakage audit.

## Current use policy

This is an active **training-candidate** source alongside the curated
Adyghe--English Wiktionary lexicon. `AdygheBench v0.2-candidate` remains the
fixed final curriculum-mastery diagnostic; do not use it for validation,
checkpoint selection, or early stopping. Validation will instead be a
source-record-group-held-out split of the SFT candidates.

## Applied fixes

- Source line 24: `Х х → kğ` was corrected to `Х х → h / kh`, matching the
  source's later `Х х → h / kh` mapping.
- Source line 79: `Мыр&nbsp;` was normalized to `Мыр`.

No other linguistic content was silently rewritten.

## Evaluation interpretation

AdygheBench v0.2 uses material derived from this source. Training on this
dataset is permitted, but a post-training score on AdygheBench must be called
**curriculum mastery**—it is not evidence of generalization to unseen Adyghe.
An independently authored holdout will be needed for that later claim.
