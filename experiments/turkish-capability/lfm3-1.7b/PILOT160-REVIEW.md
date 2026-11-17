# Pilot160 blind owner review

[Open Argilla](http://127.0.0.1:6900/dataset/c53bfd4c-b96d-46e4-8919-e8924191e3f9/annotation-mode)

Twenty development prompts, five primary thinking-disabled answers per prompt: untouched base and the four SFT checkpoints. Only two required textboxes: ordering and reasoning. Example `A > C > B = E > D`; plain `A C B E D` also works. Ties and all-bad judgments are allowed; explain them in your reasoning. No good/bad, edit/keep, correctness or fluency selections.

A-E identities change per prompt and each model occupies each letter exactly four times. Private mapping stays only in ignored `pilot160-runtime-local/argilla-blind-dev20-v01/PRIVATE-model-key.json`. No identities, source IDs, automatic metrics, suggested rankings or gold answers were uploaded. All100 displayed answers round-trip matched the frozen inference by prompt ID. Reruns preserve saved owner responses.

The queue uses the new development20, not training160 or the old diagnostic20. Thinking-on/off probes remain separate and are not mixed into primary review. Rankings indicate relative preference; no absolute correctness/pass score is inferred. After submission, `scripts/evaluation/export_lfm3_sft160_owner_review.py` snapshots the raw responses, validates typed rankings and decodes pairwise preferences without mutating Argilla. Invalid/incomplete rankings are preserved and flagged, never guessed.
