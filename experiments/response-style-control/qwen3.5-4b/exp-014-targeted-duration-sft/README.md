# exp-014-targeted-duration-sft (D)

## Status

SFT6epochs/60steps and20-question inference completed. Same12 reviews and
two authorized QA corrections as C;20/20 native EOS. Human comparison pending.
Active config-reviewed-v1.yaml and training-preflight-v1, using C's one frozen
data-reviewed-v1. Draft config.yaml remains blocked historical preparation.

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

Mean training loss0.9682095202,132.0165seconds. Lower loss does not establish
better output quality: preliminary D050 inspection finds619tokens of repeated,
contradictory advice. Both primary adapters reloaded successfully; W&B finished.
Retained checkpoint50/60 plus final adapter and logs/config/resume states verified
locally. User can terminate GPU; agent did not terminate it.
[Desired/A/C/D comparison](http://127.0.0.1:6900/dataset/e3b691cb-79fc-4bd8-a358-39f9a23770b5/annotation-mode?page=1&status=pending).
See exp013/GPU-RUN-NOTES.md for exact archive digest, authority and evidence.

The earlier preparation plan below is historical; execution is now complete.

No model-quality results. Shared data reviewed/frozen and CPU verified; now
obtain GPU, pass checks, independently train C/D, generate20 each, verify durable
backups and prepare desired/A/C/D Argilla comparison. Append all outcomes and
failures to the parent experiment journal.
