# Pilot80 semantic preparation

This versioned copy applies the three owner-authorized training corrections and
one shared Turkish system instruction to the reviewed 80/20 pilot. Original
reviewed messages, answers and worked solutions remain as provenance fields.
No held-out target was edited. Reasoning remains optional.

Rebuild with `python scripts/datasets/prepare_turkish_pilot80_sft.py`.
`manifest.json` hashes the semantic rows, corrections and builder. The separate
`semantic-review.json` describes prompt-neighbor review and its limitations.

Do not feed the complete JSON objects as training text: provenance includes
original and corrected answers. `scripts/training/run_lfm3_sft_pilot.py --mode
prepare` selects only `messages` and `worked_solution`, renders the pinned native
template, serializes reasoning once, and audits explicit assistant/EOT labels for
every training row. Its tokenized manifest and decoded-label audit are kept under
the ignored `pilot80-runtime-local` artifact directory. Test rows never enter
that tokenized training packet.
