# Submitted blind review, 2026-11-19

All16 Argilla records are submitted, with valid ABCD rankings and nonempty notes.
Export verified every displayed answer against the hashed source outputs and
decoded the independently shuffled identity mapping for each record. Raw review
snapshot SHA256: bda221e90776db48db64967893f05c9060cc780dfbb89a8d5c7d69ea3941a1f0.
Exact notes, decoded judgments and statistics: [review JSON](PRESERVATION-OWNER-REVIEW.json).
Owner-supplied, AI-assisted/API review; judge model/prompt not supplied. This is
not independently adjudicated human accuracy. No judgments were rewritten.

| Candidate | Mean occupied rank (lower better) | Pairwise preference, ties half |
|---|---:|---:|
| exp013 original-base preservation69 | 2.156 | 61.46% |
| CPT bilingual69 | 2.469 | 51.04% |
| exp012 original-base bilingual69 | 2.469 | 51.04% |
| Original base | 2.906 | 36.46% |

These are preferences among frequently unsuccessful answers, not correctness
percentages. The owner explicitly reports most questions have no successful
candidate. The reference median18 is answered as the mean19.6; synchronization,
geometry and instruction following also fail across candidates. Correct numeric
answers can retain invalid explanations. Concision can win without correctness.

Exp013 vs exp012:5 wins/6 ties/5 losses. Exp013 vs CPT bilingual69:9/2/5.
Exp013 vs base:11/1/4. CPT bilingual69 vs exp012:7/3/6. All exploratory paired
bootstrap95% intervals for net wins include zero. Small single-seed comparison;
do not claim reliable population superiority.

Exp013's strongest relative preference is on the eight general-language tasks:
75% pairwise preference, six top placements including ties. Exp012 leads the
seven numeric questions by relative preference, yet its correct required Turkish
numeric values remain1/7. This illustrates why ranking must not become accuracy.
The four truncated answers noted for synchronization, geometry, switch logic and
title all map to original base, consistent with its four4096-token length hits.
No SFT candidate hit that limit on fresh32. This affects preference substantially.

Conclusion: exp013 is the preference-leading candidate in this packet, not a
successful Turkish general assistant or an established replacement. The review
does not support treating the remaining issue as a small arithmetic tradeoff.
Keep all candidates as research artifacts; no new GPU run or publication has
been authorized by this review submission.

Next: stop expanding translations for now. Use the saved failures to audit the
actual supervision and task coverage; native label/EOT and preservation of
existing reasoning already passed, so do not assume missing tags without evidence.
If continuing with a training experiment, pre-register one change to SFT update
strength or reasoning supervision, keep a matched control, and measure correctness
separately from style. This32-prompt packet is now development data; reserve new
held-out tasks for future final claims. Defer DPO until task correctness improves.
