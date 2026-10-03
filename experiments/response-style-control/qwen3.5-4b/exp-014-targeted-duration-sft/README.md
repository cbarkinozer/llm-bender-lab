# exp-014-targeted-duration-sft (D)

## Status

Planned; same12 human reviews as C are pending. No training/inference started.
Draft config is blocked; data-reviewed-v1 and config-reviewed-v1 do not exist yet.

## Hypothesis and change

Six epochs/60steps may improve learning of C's reviewed targets relative to
four epochs/40steps, or may overfit/degrade explanation and natural Turkish.
Only duration and consequent cosine trajectory/total exposure change.
Same LR1e-4, rank16, effective batch8, pinned fresh base/template,80 examples,
loss/masking and decoding as C. Parent C is a recipe comparison, NOT an adapter
initialization. Do not train D from C's checkpoint.

One exact shared80-row artifact under exp013/data-reviewed-v1, unchanged20
development validation. No extra review/extra data for D. Approved C/D train
hashes and tokenized files must match byte-for-byte. Do not use draft artifacts.

Preparation/review/freeze tools live under
[C](../exp-013-targeted-coverage-sft/README.md); use its export_review.py once
to produce both reviewed configs and both preflights.
[Shared evaluation protocol](../exp-013-targeted-coverage-sft/EVALUATION.md).

Final scheduled epoch-six adapter preselected; no best-checkpoint selection
on development data. New GPU gates or explicit scoped waiver required;
the previous A/B waiver does not authorize this pair.

## Results / next step

No model-quality results. Review12, freeze shared data, commit provenance,
obtain GPU, pass checks, independently train C/D, generate20 each, verify durable
backups and prepare desired/A/C/D Argilla comparison. Append all outcomes and
failures to the parent experiment journal.
