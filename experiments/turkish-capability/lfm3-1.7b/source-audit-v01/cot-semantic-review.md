# Turkish CoT source semantic review

AI-authored audit; human_reviewed: false. No training dataset, replacement training examples, paid teacher calls, source edits or training runs were made.

Source: AlicanKiraz0/Turkish-CoT-Instruct-Dataset, revision `3473e6c6350564d5a7000faf3ff140e9c4b9d1f2`. Local SHA-256 `da9c2dd50d54ecb2d4868b264009081a9bf18c1d76e1662b161794cf46c94741` matches download-manifest.json. Source has 4868 records; identifiers below distinguish one-based file line from original source ID.

Reviewed 37 of the parent's 51 purposively selected records (0.76% of source rows), spanning 14/14 domains. Parent sampling combines seed3407 random16, length quantiles and domain representatives. This review chooses a bounded subset for full inspection, including one 20,235-character reasoning-heavy route record and short endpoint examples. This is a purposive audit, NOT a representative error-rate estimate. Uninspected rows are not certified, including other long-tail and English-trace candidates. All reviewed user prompts and assistant reasoning/finals were read completely; source system instruction was inspected. No excerpt-only record is counted as reviewed. No per-domain statistical assurance follows from sparse coverage.

Decisions in this inspected subset: {'conditional_select': 13, 'discard': 8, 'repair': 16}. These counts describe review dispositions, not estimated corpus prevalence. `conditional_select` is a semantic candidate only; every row remains training_eligible=false pending shared gates. `repair` means withhold original until correction and re-review; no repair text was generated. `discard` means exclude original target, not delete the source file.

## Decision

Do not ingest this corpus wholesale or treat balanced topic labels as quality assurance. Conditionally select individually verified, self-contained arithmetic/logical items. Withhold repair candidates. Discard forced-answer puzzles, fabricated quantitative claims, unsupported real-world explanations and reasoning that contradicts its own diagnosis. Correct final answers do not rescue erroneous rationales: rows 2002 and 2123 demonstrate this clearly.

The owner goal is a broad reusable core with appropriate detail, plus a planned separate reasoning configuration. The shared source system requires detailed visible reasoning and detailed finals; duplicating rationale in the final should not become a universal response style, and detail should remain appropriate to the task and user request. Keep reasoning in the plan: verify the target model's native reasoning mode, permitted trace use, formatting and loss policy before configuring that separate path. Do not assume literal source tags implement the native reasoning mode or strip them indiscriminately. The source card declares Apache-2.0 and MiniMax-M3 generation but does not itself establish provider training rights or independently validated answers. Verify provenance/provider terms, benchmark and translated overlap, deduplication, group splits, model-native template, token lengths/truncation and assistant masking before any training selection. This audit does not clear those gates.

## Verification and parsing scope

Python independently recomputed interest, annuity, equations, geometry/bearing, energy, proportions, exercise timing, combinatorics and fuel feasibility. Exhaustive enumeration of all 120 matching permutations disproves the puzzle's purported sufficiency. Numeric evidence is in `review-local/cot-calculation-checks.json`. Loan payment is 11,197.3403004 TL; original differs by one kurus, a minor rounding issue distinct from its erroneous interest subtotal. Matching clue counts are 48/96/120/24/96, never one. Poker probabilities concern hand frequency and cannot identify conditional winning probability.

A separate entire-file tag-count scan found 5 rows with two opening tags and one closing tag: [{'source_row_1based': 167, 'source_id': 170}, {'source_row_1based': 746, 'source_id': 762}, {'source_row_1based': 1840, 'source_id': 1897}, {'source_row_1based': 1884, 'source_id': 1941}, {'source_row_1based': 2242, 'source_id': 2311}]. This is structural screening only, not semantic review of those rows. All 37 fully inspected records have one opening/closing pair and a nonempty final. Balanced tags alone do not establish valid reasoning, language quality or a model-native reasoning channel. No tokenizer/rendered-label check was performed. Corpus-wide semantic, Turkish-language and English-trace incidence remain unmeasured here.

## Coverage

Domain counts: {'finans_ekonomi': 3, 'programlama_algoritma': 4, 'etik_deger': 1, 'genel_muhakeme': 2, 'saglik_beslenme': 2, 'sosyal_bilimler': 3, 'fen_bilimleri': 4, 'uzamsal_gorsel': 3, 'gunluk_yasam': 1, 'dil_anlam': 4, 'matematik': 2, 'mantik_bulmaca': 4, 'oyun_strateji': 1, 'nedensellik_yontem': 3}.

Difficulty-label counts: {'kolay': 9, 'orta': 16, 'zor': 11, 'uzman': 1}. These labels are source metadata, not validated difficulty judgments. Reviewed length range: 114–20235 assistant characters. Character lengths are not token lengths. Parent's full inventory is 4,868 CoT records; other source inventories are outside this report's scope.

## Item findings

| File row | Source ID | Domain | Decision | Evidence |
|---:|---:|---|---|---|
| 1 | 1 | finans_ekonomi | conditional_select | Simple interest recomputed: 10400 TL; reasoning and final agree. |
| 48 | 51 | programlama_algoritma | conditional_select | 0.012*64=0.768 seconds, option C; no unsupported complexity claim needed. |
| 73 | 76 | etik_deger | discard | Six-step structure is met, but numerous empirical effect sizes and research claims have no evidence: coefficient 0.62, CAC reductions, crisis resilience and growth rates. Illustrative CLV arithmetic does not validate these claims. |
| 98 | 101 | genel_muhakeme | conditional_select | 32/(4*8)=1 day under the stipulated constant-speed arithmetic model; real currents and feasibility are not evaluated. |
| 123 | 126 | saglik_beslenme | conditional_select | 1000/250 * 1/4=1 under the supplied proportional calcium premise. No independent dietary adequacy claim verified. |
| 148 | 151 | sosyal_bilimler | discard | Prompt incorrectly places establishment of Nizam-i Cedid under Mahmud II. Assistant repeats this rather than separating stipulated implication from historical truth. Civil modernization beginning solely from this chain is also overstated. |
| 173 | 176 | fen_bilimleri | discard | Free-fall arithmetic gives height 15.876 m and vertical energy 93350.88 J under zero initial vertical speed. Sound timbre cannot be determined from these data. Option B says all energy becomes heat and sound while explanation adds deformation; horizontal velocity is unknown. |
| 198 | 201 | uzamsal_gorsel | repair | R squared=-I and (3,7) maps to (-3,-7), but prompt mixes equivalence to one 90-degree rotation with proportionality to its square; proportionality factor is unspecified. |
| 223 | 226 | gunluk_yasam | discard | Full 20235-character assistant inspected in two contiguous spans. Initial full tank is invented; zero queue preference is softened. Reasoning repeatedly proposes adding 12.4 L to a full 50 L tank. Final mislabels Konya as cheapest despite cheaper Antalya and double-counts required fuel for two stops. |
| 247 | 251 | dil_anlam | discard | Adding one tax and reducing another can coexist; prompt does not establish same tax, taxpayer or rate. Answer invents mutual exclusion and selects B. Option A also describes division while naming composition. |
| 269 | 273 | matematik | repair | x=7.5 and y=13.75 satisfy both equations. Prompt and target both call substitution elimination; Turkish terminology is conflated. |
| 294 | 298 | mantik_bulmaca | discard | Exhaustive 120 permutations leave 48,96,120,24,96 assignments under clues I-V individually. None uniquely determines matching. Reasoning notices this then forces C by equating redundancy with sufficiency. |
| 466 | 479 | oyun_strateji | discard | Hand-frequency arithmetic is correct including straight flushes, but frequency of receiving a hand is not conditional probability of winning. Opponent/game information is missing. Difference is 4.5558 percentage points, not a winning-probability loss of 4.56 percent. |
| 596 | 612 | finans_ekonomi | repair | Assuming monthly rates: initial interest 5562 TL; balance 180000 TL; payment 11197.3403004 TL, rounded 11197.34 rather than 11197.35. Reasoning subtracts first-period interest from second-period interest even though they are disjoint. Final totals are approximately consistent. |
| 677 | 693 | uzamsal_gorsel | repair | Conclusion holds when folding ON each midline; arbitrary lines parallel to a midline do not bisect the rectangle. Reasoning also confuses horizontal and vertical orientation without a diagram. Final is one sentence as requested. |
| 983 | 1002 | nedensellik_yontem | repair | Correct intuition that variation/comparison is required, but not grouping children does not fix sleep duration. Table falsely implies all children then perform similarly; raw comparison alone does not establish causation. Continuous measurement alternative is acknowledged only later. |
| 1088 | 1107 | programlama_algoritma | repair | Python StringIO confirms blank line is newline, not empty string; strip-based counting works if whitespace-only lines are defined as blank. Claims that stripping is always necessary and whitespace must count as empty overgeneralize. |
| 1090 | 1109 | programlama_algoritma | repair | General quadratic concatenation explanation is supported by Python FAQ, but n=1000000 implies 500000500000 cumulative characters, not approximately 500000000. Purported timing output is unmeasured and environment-free. |
| 1238 | 1262 | sosyal_bilimler | repair | Missing sampling details merit skepticism. Expert agreement is not automatically an authority/popularity fallacy; wording moves from possible misuse to definite diagnosis. Short-answer request gets extended answer. |
| 1761 | 1809 | dil_anlam | repair | Universal instantiation plus modus ponens establishes Hasan can obtain a card. Target labels particular statements as A and presents singular inference as literal Barbara AAA-1, muddling categorical notation. |
| 1766 | 1814 | nedensellik_yontem | repair | Rainfall/weather is a plausible common-cause candidate, but vanishing adjusted correlation does not prove no direct effect or uniquely identify cause. Null simulated-discharge result also cannot prove the observational relationship noncausal. |
| 1827 | 1884 | mantik_bulmaca | repair | False dilemma is defensible, but dismissing ad hominem on grounds that calling dissenters enemies or ignorant contains no personal insult is false. Options can overlap. |
| 2002 | 2071 | saglik_beslenme | repair | 250 repetitions take 1050 s, intra-movement rest 1200 s, transitions 360 s; total 2610 s=43.5 min. Summary wrongly labels 2250 s as repetition time. |
| 2123 | 2192 | finans_ekonomi | repair | Final difference 15360 TL matches annual compounding assumption. Printed six-month equation includes both 16 percent and 6/12: that expression is 7680, not 15360. |
| 2144 | 2213 | nedensellik_yontem | repair | Correlation is insufficient for the proposed counterfactual, but insufficient evidence does not make causal claim false. Turkish calls valid causal-inference methods sahte (fake); intended quasi-experimental meaning is corrupted. |
| 2236 | 2305 | dil_anlam | discard | Treats sufficient information implying a sound result as its converse. Increased error probability is strengthened to high error probability and unreliable outcome. Opening proverb is suspicious and not independently authenticated. |
| 2290 | 2359 | uzamsal_gorsel | conditional_select | Clock orientation gives bearing (0-90) mod 360=270 degrees west; reasoning and final agree. |
| 2497 | 2569 | mantik_bulmaca | conditional_select | 4**5=1024 so one-based term index is 6; full sequence and final agree. |
| 2711 | 2795 | matematik | conditional_select | 0.42*0.07=0.0294 so total increases 2.94 percent if fuel volume stays fixed. Reasoning explicitly states that assumption; final omits it. Expert difficulty label overstates actual task. |
| 2829 | 2913 | programlama_algoritma | conditional_select | Prompt explicitly means second DISTINCT maximum. sorted(set(...),reverse=True) with length guard returns 6, None and 5 on the discussed distinct-value cases. |
| 3156 | 3258 | sosyal_bilimler | repair | Self-sealing interpretation explains A. Concludes unfalsifiable claims have no information value, which exceeds the demonstrated defect; duplicate C/D options reduce assessment quality. Historical attribution not independently audited. |
| 3304 | 3412 | mantik_bulmaca | conditional_select | All six assignment constraints and bijection hold; not claiming uniqueness. |
| 3336 | 3444 | dil_anlam | repair | Answer follows explicitly supplied rule, but then teaches it as standard Turkish grammar. Table conflates bagli with bagimli sirali; a connective alone does not determine girisik structure. |
| 3357 | 3466 | genel_muhakeme | conditional_select | D+Y=208 and D-Y/4=168 give Y=32,D=176; all 240 questions accounted for. |
| 3666 | 3787 | fen_bilimleri | conditional_select | 8*9*5=360 Wh; option C agrees with reasoning. |
| 3676 | 3797 | fen_bilimleri | conditional_select | 150/60=2.5 TL/kWh, option C, under stipulated uniform unit billing. Not an assertion about current electricity tariffs. |
| 3680 | 3801 | fen_bilimleri | conditional_select | 75*60=4500 Wh, option D; units and final agree. |

## Parent calibration handoff

All reviewed records are source train rows. Proposed keep/edit/reject labels are recorded separately from training eligibility and are AI judgments awaiting human calibration. For the parent's 15-item CoT contribution to a 60-item calibration, a diverse candidate shortlist is file rows 1, 48, 73, 148, 173, 198, 223, 247, 269, 294, 466, 677, 2002, 2144, 3336. This offers 13 domains and all three dispositions; it is a review shortlist only, not 15 approved training items. Retain original row IDs when the parent assembles its calibration artifact. No calibration completion or human approval is claimed.

The parent's 183 broad English-phrase signals are a screening heuristic, not a language classification or a measured count of English reasoning traces. They were not semantically adjudicated by this bounded review. Source reasoning, format and difficulty metadata remain unverified labels.

## Source checks and limitations

Repository AGENTS.md, dataset guide (including rationale provenance, leakage, semantic review, formatting and immutable artifacts), reproducibility guidance, experiment README and local source card informed this review. No experiment configuration was changed.

Chronology check: [Nizam-i Cedid entry, TDV](https://islamansiklopedisi.org.tr/nizam-i-cedid) places the reforms under Selim III; the prompt's Mahmud II attribution is defective. [Python official programming FAQ](https://docs.python.org/3/faq/programming.html#what-is-the-most-efficient-way-to-concatenate-many-strings-together) supports the general-case quadratic concatenation warning, not the sample's invented timings. Accessed 2026-11-14. Other domain-history, grammar and empirical claims were assessed for internal validity or flagged for specialist verification; they are not comprehensively fact-checked. This is dataset review, not medical or financial advice, and the hypothetical arithmetic checks do not validate real-world policies or recommendations.

Turkish is mostly readable in inspected items, with formula/notation inconsistency, English technical terminology, repetitive headings and serious semantic mistranslations. Especially harmful are the word sahte applied to causal methods, the elimination/substitution conflation, and invented definitions used to force multiple-choice answers. Full-corpus Turkish quality and translation provenance are unreviewed. Source text is not reproduced at length in these artifacts.
