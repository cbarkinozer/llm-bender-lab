# LFM3 Turkish CPT: 500-response diagnosis v01

Date: 2026-11-14. Checkpoint: cumulative 100M adapter, published repository
`cbarkinozer/LFM3-1.7B-Turkish-CPT`, revision
`6f213ec25a944dab2fbdeb6d337deb0e0442e638`.

**Main finding:** Turkish text modeling and grammatical discrimination improved
in the existing controlled diagnostics, while this assistant-generation cohort
shows severe task abandonment, unsupported additions, repetition and incomplete
termination. SFT should preserve language competence while teaching reliable
task completion, grounding and requested response shape. This is not evidence
that every response merely needs shortening.

## Evidence and review boundary

Input is the preserved full500 `scored-samples.jsonl`, joined by `id`, alongside
the original answers, manifest and scores. No generation was rerun or changed.
`automatic-summary.json` records all four input hashes and source Git commit.
The reproducible deterministic pass is:

```powershell
python scripts/evaluation/analyze_lfm3_final500.py
```

Existing analysis outputs are protected from overwrite. To recompute, pass
`--output` with a fresh directory. `--join-agent-reviews` additionally validates
the three annotation files in that output directory and creates the review
index; copy the fixed annotations there first when reproducing the joined view.

All 500 have complete-string mechanical diagnostics. Agent qualitative triage
uses source/reference, opening and tail excerpts, with per-record inspection
scope. Long outputs have **not** all received exhaustive claim-by-claim semantic
review. `semantic-*.jsonl` and companion reports document those judgments.
Every annotation is machine assisted and `human_reviewed: false`; none is owner
approval or a new ground-truth semantic accuracy score. Human adjudication is
still needed for ambiguous cases and any quantitative semantic-success claim.

Generation: temperature 0.1, top_k 50, top_p 1.0, repetition penalty 1.1,
4096 output tokens, 8192 context, batch 4, seed 3407. The recorded rendered
assistant prefix has an empty think region; this is not a reasoning-enabled
evaluation. Results do not establish thinking ability or its potential benefit.

The 500-item run is **100M only**. The separate matched 100-item screen supports
before/after observations, but is a subset of this cohort, not an independent
replication. Older full500 baseline output uses a different protocol. No pooled
"overall accuracy," causal CPT data-size effect, or pristine final-test claim
is appropriate. These inspected items are now historical development evidence.

## Complete-cohort observable results

Each task has 100 rows, so counts below are also percentages within the task.
"Repeated 8-gram" means a normalized contiguous eight-word sequence appears at
least five times anywhere in the full output. This is a repeatable triage rule,
not an exhaustive semantic repetition judgment or the engine's loop criterion.

| Task | EOS | Output limit | Loop guard | Repeated 8-gram | Median output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Turkish correction | 31 | 63 | 6 | 75 | 4096 |
| TQUAD grounded QA | 21 | 73 | 6 | 81 | 4096 |
| XQuAD Turkish QA | 16 | 81 | 3 | 91 | 4096 |
| English→Turkish translation | 53 | 46 | 1 | 58 | 807.5 |
| Turkish summarization | 15 | 77 | 8 | 79 | 4096 |
| Total | 136 | 340 | 24 | 384 | — |

Only 27.2% end with EOS; 68% hit the output limit; 4.8% trigger the recorded
loop guard. EOS is a stopping observation, not a correctness judgment. Some
EOS responses are unrelated or contain unsupported claims. The repeat signal
appears in 76.8% of outputs; repetition can occur without a loop-guard stop.

No stored U+FFFD occurs in the 500 prompts or predictions. Initial garbled
console display was an encoding/rendering issue and is not model corruption.

Original metrics are preserved: correction exact match 0/100; TQUAD mean F1
0.0070476; XQuAD mean F1 0.00064994; translation corpus chrF 3.00961 (0–100);
summary mean ROUGE-L 0.0127601 (0–1). They score full outputs and are strongly
affected by irrelevant continuation. They neither certify nor disprove every
opening answer's correctness.

The old QA "answerability accuracy 1.0" is not a strength: all 200 gold items
are answerable and the scorer mainly checks a narrow refusal marker. It does
not demonstrate calibrated uncertainty, answer correctness or abstention skill.

All 136 EOS records retain a terminal special-token marker in `raw_output`
that is absent from `prediction`. The historical scorers use raw output; these
scores remain unchanged. Any future cleaned scoring needs a separate revision,
not replacement of the historical files. The model failures described here
also occur in prediction text and are not explained by that marker.

## What useful behavior remains?

- **Correction openings:** 12/100 predictions start literally with the target;
  10 first nonempty lines equal it. A sentence can be right before a same-line
  continuation, so those are different observations. Of 100 sources, 47 already
  equal the target. Prefix matching alone is therefore not evidence of learning
  a necessary correction. Zero full outputs equal the target.
- **Grounded QA fragments:** normalized whole-word reference spans appear
  somewhere in 16/100 TQUAD and 5/100 XQuAD outputs, and within the first 300
  characters in 13 and 3 respectively. These are triage candidates, not success
  rates: copying, wrong relationships and accidental mentions can contain gold.
- **Translation:** it has the highest EOS rate and shortest median output among
  the five tasks. Some outputs convey part of the source meaning. Relative
  stopping success does not establish strong translation quality.

The stronger quantitative language evidence is **outside these 500 generations**:
the saved matched diagnostics in `../continuation-screen-results-v01.json` show
TurBLiMP1600 macro discrimination rising from 71.75% to 86.8125%, held-out Wiki
NLL from 3.26195 to 2.33659 and Web NLL from 3.88936 to 2.61781. These are
grammatical preference/text-likelihood measures, not assistant correctness.
Within that diagnostic, irregular forms, passives, quantifiers and scrambling
reach 100/100, while ellipsis is 33/100, island effects 70/100, determiners and
relative clauses 77/100. Treat these as linguistic probe priorities, not proof
of universal mastery or direct instructions to train on those benchmark items.
The matched 100-item screen records baseline EOS 100/100 versus 100M 26/100.

## Failure mechanisms and training implications

| Finding | Evidence and confidence | Priority | Desired training behavior |
| --- | --- | --- | --- |
| Runaway/repetitive continuation | Full-cohort stop metadata and repeat signals; high confidence in measured frequency | P0 | Finish a complete requested answer; native assistant terminator; no article/navigation continuation |
| Task substitution | Agent excerpt judgments plus directly inspected examples; prevalence requires adjudication | P0 | Translate, correct, summarize or answer as instructed; preserve the task across varied wording |
| Unsupported elaboration | Clear source/output contradictions in inspected cases; no exhaustive hallucination rate | P0 | Ground claims in given context; do not invent quotes, dates, entities or events |
| Entity/number/relation corruption | Explicit source/output differences below | P0 | Preserve who-did-what, direction of influence, quantities, tense and negation |
| Unnecessary rewriting and missed correction | GECTurk source/target/opening comparison; agent review pending owner | P1 | Minimal necessary edits and unchanged controls, with natural variants adjudicated |
| Response-shape mismatch | Complete outputs exceed correction/answer request; not just parser mismatch | P1 | Answer-only when asked; detailed explanation when asked; valid requested structures |
| Potential grammar subskill gaps | Separate likelihood-based linguistic probes, not these outputs | P2 | Independently authored ellipsis/relative-clause/determiner coverage; verify natural Turkish |

The continuation style is consistent with a prose-completion tendency after
raw-text CPT. This is a hypothesis, not an isolated causal finding: recipe,
data mix, cumulative exposure and checkpoint changed together. SFT is the next
test of whether task behavior can be restored while retaining language gains.

## Inspectable examples

These are evaluation evidence only. Do not reuse, paraphrase or transform them
into training records.

| ID | Observation | Implication |
| --- | --- | --- |
| gecturk-01174 | Expected unchanged sentence appears first, followed by click-through prose and repeated relationship headings | Opening correctness and completion control are separable |
| tquad-00718 | Correct solar-year measurement first; adds claims about a second-century Islamic-world setting absent from the passage | An answer can start correctly and still fail grounding |
| tquad-00538 | Mentions expected philosophers but substitutes another person and changes the relationship | Gold-name presence is not semantic QA success |
| xquad_tr-01137 | Passage gives an 18th-century origin; output adds a Turkish founding story with 2001/2012 and a 19th-century origin | Topical vocabulary can coexist with contradictory facts |
| xquad_tr-00181 | Question concerns Luther's works; output discusses Ibn Sina instead | Wholesale task/topic abandonment |
| wmt_en_tr-00449 | "second-year" becomes "first-year"; agency and organization detail also change | High reference overlap can hide meaning errors |
| wmt_en_tr-00220 | Broad source topic retained, but adds reporting language and changes the relationship | Partial translation ability; do not automatically accept the target |
| mlsum_tr-03264 | Adds security-camera footage and a driver quotation not in the source | Fluent news-like continuation is not faithful summarization |
| mlsum_tr-09652 | Football passage becomes an unrelated repeated New Year heading | High-ranked overlap items can still be unusable |

## What these responses do not measure

General knowledge accuracy, conversational helpfulness, multi-turn memory,
JSON/schema compliance under direct tests, coding, mathematical or explicit
reasoning, unanswerable QA, robust English retention, creative writing and
practical planning are unestablished. Long generation is not reasoning.
Low task scores alone do not establish that the model lacks all underlying
knowledge: instruction adherence and stopping confound its expression.

## Dataset decision

Adopt the owner's reusable-corpus-first direction in
[`docs/turkish-sft-corpus-design-v01.md`](../../../../docs/turkish-sft-corpus-design-v01.md).
The historical 40-row pilot remains unapproved, training-only candidate data;
its summary-heavy allocation is not the general corpus composition.

Next audit the four proposed sources against a broad coverage contract, with
pinned revisions, provenance, correctness, diversity and contamination checks.
Select their demonstrated strengths, then fill independent gaps synthetically.
Calibrate owner review on 60 candidates, build a first ~300-accepted snapshot,
then add reviewed batches of 200–300 toward ~1k, expanding only for remaining
coverage gaps. These are budgets, not quality guarantees. Freeze reviewed
general v01 before LoRA; later measured model-specific curation stays separate.

Keep verified reasoning as a planned configuration. It may benefit a 1.7B
model; measure final-answer accuracy, step validity, token cost, latency and
simple-query behavior separately. DPO follows stable SFT on fresh preference
prompts. Preserve time for the eventual Reflex-1 specialization.

## Files

- `automatic-diagnostics.jsonl`: reproducible per-row string and generation properties.
- `automatic-summary.json`: counts, definitions, hashes and limitations.
- `semantic-gecturk.jsonl` / `.md`: correction opening judgments and evidence.
- `semantic-qa.jsonl` / `.md`: QA excerpt triage and evidence.
- `semantic-mlsum-wmt.jsonl` / `.md`: summarization/translation triage and evidence.
- `review-queue.csv`: joined 500-ID index with blank owner decisions; not training data.

No original scoring file, generation, checkpoint, published dataset or model was
modified. No training or paid generation job was launched for this analysis.
