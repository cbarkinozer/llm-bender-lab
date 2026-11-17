# Cross-lingual owner review: 2026-11-17

All 15 records submitted, all rankings valid. Verbatim owner notes and decoded
rankings are preserved in CROSSLINGUAL-OWNER-REVIEW.json; immutable raw API
snapshot remains in the ignored local Argilla directory with its recorded SHA256.
No training has been run from this diagnostic.

## Preference result

Wins/losses/ties for the first named model:

| Comparison | Wins | Losses | Ties |
|---|---:|---:|---:|
| CPT+SFT vs original | 10 | 4 | 1 |
| CPT+SFT vs direct-original SFT | 7 | 4 | 4 |
| CPT+SFT vs CPT | 12 | 3 | 0 |
| Original vs CPT | 13 | 2 | 0 |

CPT+SFT is exp-007 checkpoint-60; direct-original SFT is exp-009 checkpoint-60.
Original means LiquidAI/LFM3-1.7B post-trained checkpoint, not its -Base variant.
Relative preference is not a correctness score. Many first-ranked answers are
still wrong. Only three independent matched tasks were evaluated across four
language conditions, plus three controls: do not infer population accuracy.

## Diagnosis from matched tasks and raw outputs

1. English capability exists on these examples, but is imperfect. The original
   solves the English purchase problem and gives correct battery reasoning,
   although it exceeds the sentence limit. All models introduce problems in the
   English delivery task: even fluent English can invent causal relationships.
2. Turkish input is a separate bottleneck. Original solves the purchase task with
   English input but misreads the Turkish initial balance as a notebook price.
   Turkish battery input is also misread. Thus this is not just Turkish spelling
   or a missing Turkish output style.
3. Output-language control is weak. Turkish-to-English battery answers are all
   Turkish; purchase answers are Turkish or essentially numeric. CPT+SFT's
   Turkish-to-English delivery is English but reverses recipient absence into
   presence. Answering in English does not by itself demonstrate understanding.
4. Turkish generation remains weak even with English input. Delivery outputs
   mistranslate yesterday and parcel, invent causality, and change semantic roles.
   Purchase arithmetic can remain correct while notebook/bag vocabulary fails.
   CPT+SFT's English-to-Turkish battery answer is a clean positive example.
5. SFT arithmetic regression is visible on these controls. Original arrives at
   104, 15 and 575, though it violates numeric-only formatting and emits a closing
   thinking marker on the first. Both SFT models answer 128 instead of 104.
   Direct-original SFT answers 12 instead of 15; CPT+SFT uses 81/6 = 13.5.
   Both get the third value 575; only CPT+SFT follows numeric-only there.
   These are three controls with Turkish instructions, not a language-free or
   broad arithmetic benchmark. We cannot attribute all loss to abstract math.
6. Stopping is repaired by SFT: original and both SFT runs reach EOS on 15/15;
   CPT reaches EOS on 8/15, exact-loop guard on 1 and token limit on 6.
   Shorter fluent wrong answers must not be counted as capability gains.
7. Thinking-format leakage warrants investigation before more training. Despite
   thinking disabled, raw original emits </think> on one control; direct-original
   SFT emits it in four outputs, several duplicating reasoning and answer.
   CPT+SFT emits none in this packet. Preserve raw text; do not retroactively
   strip markers to improve scores. This does not prove empty-thinking targets
   caused the errors: inspect serialization, masking and native template first.

## Next steps and decision gate

### Verified thinking-tag conversion

The owner's `<thinking>...</thinking>` review notation was not accidentally
trained as a replacement for the native `<think>...</think>` format. The original
review exporter accepts both spellings and extracts reasoning separately from
the final answer. The later three-textbox exporter likewise stores reasoning in
`worked_solution`; its `<thinking>`-wrapped `reviewed_target` is provenance only.
The training scripts pass reasoning through the assistant `thinking` field to
the native chat template.

Both saved 160-row label audits (base-sft160 and pilot160 runtime directories)
passed and contain no literal `<thinking>` tags. The frozen training set has 30
nonempty reasoning targets and 130 intentional direct-answer targets. Those
direct answers serialize as `<think></think>` under the native template; this
does not mean the 30 reasoning targets were emptied. A forgotten tag conversion
is therefore not supported as the cause of these failures. The broader audit of
training/inference prefixes, masks and mode behavior remains a separate gate.

### Agreed direction: target weaknesses with bilingual tasks

Build training data around the observed weaknesses, not generic dataset growth.
The working hypothesis is that aligned bilingual supervision can help transfer
existing English skills into Turkish; this experiment has not established that
transfer will occur or that the original English skills are uniformly strong.

- Include arithmetic with verified calculations and correct interpretation of
  quantities, balances, units and operations; retain English and symbolic
  regression coverage as well as Turkish word problems.
- Use matched English-input/English-output, Turkish-input/English-output,
  English-input/Turkish-output and Turkish-input/Turkish-output task variants.
  These are task-solving directions, not just literal translation exercises.
- Include explicit English-to-Turkish and Turkish-to-English translation where
  meaning, negation, time, entities and semantic roles must remain unchanged.
- Include grounded comprehension, faithful rewriting and natural Turkish answers
  without invented causes or unsupported details. Match requested output language.

Create fresh canonical task groups and keep every translation/paraphrase of a
group in the same split. Never turn the reviewed diagnostic questions, their
translations or close rewrites into training examples. Freeze a fresh holdout
before generation, then validate a small pilot before committing to larger data
or another training run. No final row count, parent or training launch is fixed
by this decision.

- Keep exp-007 checkpoint-60 as the current research candidate. No production
  claim and no evidence for universal English improvement.
- Audit training/inference chat serialization, intentional blank versus nonempty
  thinking targets, assistant loss masks, and duplicated reasoning/final text.
  Verify rendered/tokenized examples before choosing a new training recipe.
- Prepare a small paired bilingual pilot rather than manually authoring 2,000
  generic rows. Use fresh tasks with verified English/Turkish versions covering
  all four directions, output-language instructions, arithmetic with changed
  operands, negation, semantic roles, faithful rewriting and concise uncertainty.
  Keep reasoning optional and useful; do not add empty thinking artificially.
- Use an owner-reviewed small stratified sample to validate the generation and
  filtering process. Automatically check arithmetic, duplicates, required output
  language and structure; do not pretend these validate all Turkish semantics.
- Compare a bilingual arm against a Turkish-only arm with the same underlying
  task families, fixed parent, fresh adapters, recipe and supervised-token budget.
  Resolve parent and final row/token budget after the format audit; the existing
  handoff's 500-1,000 rows per arm is a candidate scale, not a frozen requirement.
- This diagnostic now informs decisions and is development data. Freeze fresh
  independent task families before pilot training; keep them out of generation
  examples, correction targets and training. Measure English retention, Turkish
  understanding/output, math and stopping independently. Scale only if Turkish
  meaning improves without repeating the observed math regression.

No pilot training, new synthetic data generation, publication or pod action was
performed as part of this review export.
