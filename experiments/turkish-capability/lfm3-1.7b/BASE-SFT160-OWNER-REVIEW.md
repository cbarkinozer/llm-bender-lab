# Initialization ablation owner review

All 20 reviews were submitted and parsed successfully. Verbatim rankings and reasoning, decoded identities and snapshot/key hashes are preserved in `BASE-SFT160-OWNER-REVIEW.json`. The immutable raw snapshot remains in the ignored local runtime. Argilla annotations were not changed.

Selected working checkpoint remains **exp-007-sft160-lr1e4-step60**, CPT initialization, LR1e-4. Step60 belongs to the original 100-step cosine schedule. No additional training or publication was performed.

| First model versus second | Wins | Losses | Ties |
|---|---:|---:|---:|
| Untouched base versus CPT only | 18 | 2 | 0 |
| Untouched base versus CPT ? SFT, step60 | 4 | 16 | 0 |
| Untouched base versus Base ? SFT, step60 | 4 | 15 | 1 |
| CPT only versus CPT ? SFT, step60 | 0 | 20 | 0 |
| CPT only versus Base ? SFT, step60 | 0 | 20 | 0 |
| CPT ? SFT, step60 versus Base ? SFT, step60 | 12 | 3 | 5 |

| Model | Prompts in top preference group, ties included |
|---|---:|
| Untouched base | 3 |
| CPT only | 0 |
| CPT ? SFT, step60 | 15 |
| Base ? SFT, step60 | 6 |

The controlled initialization comparison favors CPT ? SFT by 12 wins, 3 losses and 5 ties. This does not support abandoning CPT as the sole remedy. Untouched base beats raw CPT 18?2, while both SFT paths beat raw CPT 20?0. The separately measured stopping results help explain this: raw CPT reaches EOS on 8/20 development prompts; base and both SFT paths reach EOS on 20/20. Preference still reflects the complete response, not stopping alone.

SFT improves relative preference over untouched base on both initializations: CPT ? SFT wins 16?4; base ? SFT wins 15?4 with one tie. Thus the blanket claim that SFT made the model worse is not supported on this set, although individual regressions exist. CPT improves grammar recognition (86.9375% versus base 71.750%); after SFT the corresponding values are 86.625% and 71.9375%. Grammar recognition is distinct from fluent, faithful generation.

Owner notes identify persistent spelling/diacritic errors (dev01), meaning lost during rewriting (dev02), unsupported ambiguity resolution (dev04), wrong arithmetic or time extraction (dev06/13/14), incorrect JSON values/schema (dev09), sorting and word-limit failures (dev10/11), and contextual language failures (dev19). All answers are described as wrong on several prompts. Dev03 has correct tied SFT answers; dev05 has a fully correct preferred grounded summary. Base remains better on some reasoning/uncertainty tasks. A top rank is not a correctness label.

Recommended next work: retain the selected adapter as a research checkpoint; audit CPT target construction and EOT handling to investigate the stopping regression, without asserting an unverified cause. Broaden and audit the training data around the observed capability categories. Keep intentional blank thinking targets unchanged. Source or author independent examples rather than copying these prompts, owner reference answers or close derivatives into training. Freeze a fresh independent evaluation before another promotion decision. Do not simply repeat the same 160 rows for longer on the strength of these results.

Limitations: these 20 prompts have been reviewed repeatedly and are development data. The single-owner relative rankings do not estimate production accuracy, statistical significance or broad Turkish quality. Pairwise comparisons within a prompt are correlated. Primary inference used thinking disabled; these rankings do not establish the value of thinking-on inference.
