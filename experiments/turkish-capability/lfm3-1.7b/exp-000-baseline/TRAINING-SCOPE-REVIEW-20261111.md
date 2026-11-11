# Training scope review during baseline

User raised embedding training and 10M-50M CPT exposure before training began. Baseline remains unchanged and running; no CPT has started.

Verified local Downloads/lfm3_cpt_with_trl.ipynb: executable LoRA config targets nine projections and does not include embeddings or modules_to_save. Input embedding training is an optional Next steps suggestion. Existing runner follows executable recipe, not that extension.

Pinned model config: vocab128000, hidden2048, tie_word_embeddings=true. Shared embedding/output weight has262144000 parameters. Full embedding updates need explicit tied-weight preservation, memory/optimizer/save/reload checks. Existing LoRA-only recipe freezes it.

2.2M unique training tokens constitutes a small adaptation pilot, not a broad test of CPT effectiveness. Engineering smoke and adaptation pilot are distinct. No universal minimum10M/50M threshold is claimed. More epochs repeat exposure but do not create new unique data.

Recommendation presented:10M unique Wikipedia tokens with existing LoRA-only recipe; embeddings as separate follow-up. Alternatives offered:10M plus tied embedding training, or retain2.2M pilot. Training is on hold until scope is settled; continue baseline and independent preparation. No GPU training or expanded budget is reported as completed.

Any expansion must preserve existing wiki_dev/wiki_eval/web_eval and CETVEL/TurBLiMP packets, apply overlap checks to all additions, retain old data unchanged, version a new manifest/token profile, and bind actual training gates to that manifest. Existing100-document dev/eval cohorts are small and public; dataset size alone does not resolve evaluation limitations.

Reference example, not a universal threshold: https://arxiv.org/abs/2605.09015 reports11.5M Sardinian tokens plus2.4M replay on a24GB GPU.
