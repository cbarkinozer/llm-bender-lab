# Final reviewed E/F split audit — 2026-10-04

## Outcome

No identified item-level training/evaluation leakage in the reviewed artifacts.
This is an evidence-bounded finding, NOT a guarantee of universal semantic
independence or freedom from pretraining contamination. Both experiments are
data-frozen/CPU-checked, still pending GPU checks; neither has trained.

| Final artifact | Rows | Target tokens per full dataset |
| --- | ---: | ---: |
| E / exp015 train | 80 | 5121 |
| F / exp016 train | 104 | 6216 |
| Existing development | 20 | 1151 |
| New evaluation-only controls | 12 | See control-preflight-v1/report.json |

All45 Argilla submissions retained: train31 rewrite/2 accept; controls12 rewrite.
Nine E targets actually differ from C,71 unchanged; F first80 exactly equal E.
No original80 input message, ID, category or ordering changed. Original20
development artifact still SHA256
`43e10beed85aa6fbbda768a124c7a2e6feb3743ddc79c2e38098c7982cfad429`.
User-provided final answers were not silently edited or normalized beyond the
exporter's documented outer-whitespace trim for rewrite submissions.

## Automated evidence

[final-split-audit-v1.json](final-split-audit-v1.json) compares E80×32=2560 and
F104×32=3328 pairs (5888 comparisons, overlapping E/F core). Zero:

- exact normalized user-turn/context matches;
- character-similarity flags at0.60;
- five-word-shingle containment flags at0.50;
- exact reference-answer matches of eight or more words;
- full evaluation questions/references of eight or more words embedded in train;
- cross-split IDs, scenario groups or composite source-path/source-ID matches.

NFC/whitespace normalization does not erase Turkish characters, quantities or
case. Best F nearest prompt pair: control011 ↔ new024, ratio0.4894; that metric
is an inspection aid, not a semantic confidence level. All three nearest
candidate IDs per evaluation item are preserved for repeatable inspection.

The exporter also reran the historical/current inventory audit:348 historical
benchmark entries +3500 historical training entries +24 earlier B records,
plus current80/20, new24, controls12 and internal comparisons. Historical versions
overlap; those counts do not represent distinct independent questions. No flags.
Prompt questions were unchanged by answer review; final answer checks were
additionally rerun rather than relying solely on draft audit results.

## Agent semantic inspection, distinct from user annotations

Inspected all32 evaluation prompts/reference answers, their nearest training
pair listings and the six targeted behavior families. Explicit boundary cases:

| Evaluation | Related training | Interpretation |
| --- | --- | --- |
| control001 adet/âdet | me074 kar/kâr, me080 is evaluation-only | Same character-sensitive skill; different terms, meanings and sources, not a renamed source sentence |
| control002 odasında | me005 rapora, me006 binadan; new002 ben de | Different case/conjunction contexts; no copied corrected sentence |
| control004 language-course goal | me054 job-offer priority | Same preference-conditioned decision skill; different evidence and criteria; do not treat task-family familiarity as novelty |
| control005 watering progress | new009 request ownership/new010 ingredient search | Progress tracking versus ownership/search bottlenecks; different diagnosed mechanisms and concrete interventions |
| control006 microphone/room comparison | me046 Wi-Fi diagnosis, tc005 projector cable | Shared controlled-diagnosis skill, different observations and remedies; no copied noise scenario or heldout-specific solution |
| control007 pending dues vote | new013 pending exhibit review | Intentional preservation of future uncertainty; no identical institutional event, source text, entities or factual answer |
| control008 found valise/not delivered | older B vehicle reservation/not delivery | Distinct state transition, evidence and requested summarization; neither source question copied nor changed only by entity substitution |
| control010 constellation atlas | new019 board-game duration, earlier B file-format choice | Already answered follow-up, different content-purpose inference; old draft CSV/SVG-style control was replaced before authoritative review |
| control011 explicit mixed feelings | new024 approach/withdrawal behavior | Reflect only what user states; one contains explicitly named feelings, the other observable behavior; do not invent a common emotional explanation |
| control012 tiring journey/no advice or questions | new021 sibling disagreement/no advice or questions | Same generic listening contract, different episode; identical short target is a conventional acknowledgment, not a heldout fact/solution |

Original20 topics stay separate: no new train scenario copies cafe-sign causality,
morning departure, work/rest space division, presentation rescheduling, new-home
belonging or failed-exam venting. Training those general behaviors intentionally
shares task families, but not those item-specific prompts/solutions. No evaluation
row is fed as a generation seed, gradient example or replay item.

## The shared short answer

User selected `Tamam, dinliyorum.` for new021 and control012. Retain both approved
answers; shortening/listening often has only a few natural responses. Exact
equality here is NOT proof of leakage. However, these items mostly measure a
shared conversational contract rather than new reasoning. Report that limitation
instead of treating control012 as a difficult independent generalization win.
Do not change a correct answer merely to avoid a superficial string overlap.

## Limits and gates

The same project agent authored train/control drafts from an approved behavior
taxonomy. They are not independent-author evaluations. Existing20 repeatedly
informed experiment choices and are development, not final test. Twelve controls
are small and intentionally task-family-related. No embedding model, pretraining
corpus audit, external adjudicator or statistical independence proof was used.
The frozen me089 reference remains disputed; preserve historical annotations and
report sensitivity without089.

Controls are physically separate from train and original validation-loss files.
Approved config row counts are80/104 train and20 validation. Controls must never
be added to optimizer/replay/validation loss or chosen-checkpoint scoring. Final
step40 is preselected. Verify runtime loaded IDs/masks and preserve rendered inputs
when GPU execution is authorized; CPU files alone do not prove a future runner
will obey them.

Machine checks and signoff are versioned separately: raw audit status conservatively
says automated checks passed/semantic signoff needed; this document provides the
agent signoff without overwriting machine evidence or user annotations.
