# Candidate CPT sources, reviewed before training

Baseline running unchanged; no CPT has started. The10M Wikipedia candidate is prepared but not active. User proposed afkfatih/turkish-cpt-dataset and altaidevorg/fineweb-2-turkish-categorized.

Preferred broad-web source: official HuggingFaceFW/fineweb-2, tur_Latn, train only, pinned af9c13333eb981300149d5ca60a8e9d659b276b9. Current card reports95,129,129 Turkish documents and41,933,799,420 words, not50M tokens. Tokens require the pinned LFM3 tokenizer. Sampling should preserve document metadata, use fixed source revisions/IDs and document the sampling frame. Never train on test split.

Afkfatih revision7f97191df415d0f4f58494ab9504052b2771bbcd: author reports1,908,378 examples/~2.19B tokens/~80%Turkish/~20%English. Sources include TR/EN Wikipedia, habanoz/c4_tr_fineweb_plus, FineWeb2 TR and FineWeb EN. Displayed schema text only, so per-row provenance is less transparent. Cleaning card does not establish cross-source dedup or protection against our evaluation. Compilation CC-BY4.0 is not a replacement for original component terms; card explicitly says components retain original licenses. Reported tokens/ratios not independently recomputed. Includes Wiki and FineWeb content, so direct use without exclusion can overlap existing eval.

Altai revision6882f33dee05845c370d29179cc1fda92a85a2f4: categorized derivative,87,964,933 rows/~177GB. Card says ongoing effort and details forthcoming; no explicit license in card metadata. Spot inspection, not representative audit, showed apparent category errors (e.g. political shipping-news text labelled adult content); category labels are not quality scores. Parent FineWeb2 version/selection/split mapping is not fully explained by the card. Prefer original source for first reproducible run.

Recommendation discussed: broader Turkish adaptation could use10M unique tokens with70%filtered FineWeb2 train/30%Wikipedia by token count, an initial engineering choice rather than optimized mixture. This changes the planned Wikipedia-only recipe and requires a versioned dataset and gates. Do not silently activate it. The already prepared10M Wikipedia subset remains a simpler cookbook-style option.

If FineWeb2 enters training, web_eval is held-out same-source, not OOD. Preserve existing packets and before/after scorer. Include train/dev/eval ID, exact text, paragraph and near-overlap checks across sources. English replay is a separate design choice; current Turkish suites do not establish preservation of English reasoning.

Sources:
- https://huggingface.co/datasets/HuggingFaceFW/fineweb-2
- https://huggingface.co/datasets/afkfatih/turkish-cpt-dataset
- https://huggingface.co/datasets/altaidevorg/fineweb-2-turkish-categorized
