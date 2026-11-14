# Occam + Turkish task recovery: expansion v01

Status: inventory complete; 40 training-only pilot drafts and a full review TXT
are built. Independent content review and LFM native training packets are still
pending. No GPU or paid external teacher service is needed for this step.
Original Occam files and published datasets remain unchanged.

## Evidence and scope

Pinned Occam dataset: cbarkinozer/Occam-Turkish-Response-SFT,
revision947850d484c71f657dbec2bb7e3d356cb5fb23e3. The104 local training and20
validation inputs/targets exactly match the public release, including order.
Published format includes the final assistant message; internal reviewed format
stores it separately as desired_answer. Do not append the answer twice.

Only10/104 training rows are faithful summaries; their targets average140.7
characters (97–185). Raw input lengths across Occam average45.67 LFM tokens,
max105, excluding chat serialization. There is no explicit translation category.
These are short-context examples; they do not establish long-document coverage.

Historical blind30 Qwen review: summary pass F2/6 versus starting model4/6,
despite higher automatic ROUGE. This is small, single-reviewer evidence of a
possible regression, not proof that all summary targets are wrong. LFM100M CPT
also invents unsupported story details and fails to stop; full500 has136 EOS,
340 output limits and24 guarded loops. Treat faithfulness, task adherence,
coverage and stopping separately from brevity and reference overlap.

Static inventory found no exact train/dev prompt overlap, no shared declared
scenario groups, no exact prompt matches to CETVEL500, and no replacement
characters. This does not clear semantic near-duplicates or historical rights:
the original dataset card declares Apache2.0 but documents incomplete historical
synthetic/provider provenance. Retain that limitation and each row's origins;
do not relabel the old corpus as newly generated or universally re-reviewed.

## Provisional expansion budget

These are design targets, not already generated/accepted row counts. Revise
after pilot review and native token measurement. Quality and token exposure
matter more than reaching the row quota.

| New training component | Target rows | Why |
|---|---:|---|
| Faithful summarization |140| Strong expansion for both Occam and CPT weaknesses |
| Passage-grounded QA |100| Answer the actual question using supplied evidence |
| Direct English→Turkish translation |80| Repair task substitution and unwanted explanations |
| Instruction/format/completion controls |60| Respect requested outputs, finish, avoid continuation boilerplate |
| Minimal correction and unchanged controls |20| Preserve meaning and already-correct sentences |
| Total new train |400| Plus the104 original Occam train rows if retained after audit |

Candidate mixture:504 training rows. Do not repeatedly oversample Occam merely
to equalize row counts: inspect task shares in input and supervised tokens too.
Preserve useful explanation and selective clarification coverage from Occam;
do not train a blanket one-sentence policy.

Plan60 new dev and100 fresh final-holdout records, across the same capabilities.
Assign independent source/scenario/template families to splits before writing
questions or answers. Source variants and paraphrases cannot cross splits.
Reserve final evaluation families from authoring and iterative inspection; log
any accidental exposure and replace the affected final-test family. Existing
Occam20 and CETVEL500 remain legacy diagnostic/development cohorts.

## Summarization design

Cover one sentence, a short paragraph, and requested bullet formats. Include
short and moderate passages, varied source lengths and compression ratios,
ordinary and technical text, everyday notices, news-like accounts, explanatory
articles and simple numerical reports. Topic is a metadata axis, not evidence
that domain balance has been achieved. Use original authored contexts initially
or record exact permitted external-source provenance; no benchmark paraphrases.

Cross-cutting contrasts: past versus planned events; proposal versus completed
action; correlation versus causation; conditional outcomes; exceptions; speaker
attribution; negation; multiple people with similar names; dates, units and
percentages; essential caveats that cannot be removed to meet a length target.
Include benign cases without traps so cautious boilerplate is not rewarded.

Review dimensions: supported claims, main-point coverage, entity/number fidelity,
temporal/modality fidelity, requested format/length, natural Turkish, no added
commentary. A shorter answer that loses the core meaning fails. A fluent answer
with an invented event fails regardless of ROUGE. Length is secondary to
faithfulness and required coverage. Metadata may list required facts and
forbidden unsupported claims, but must never leak into model input.

## Other task controls

QA: direct answer extraction, numerical/entity precision, multi-fact answers,
short reasoning grounded in supplied facts; add explicitly unanswerable cases
without treating abstention as desirable on answerable cases. Existing CPT QA
cohort was answerable-only and did not measure abstention.

Translation: preserve meaning, negation, tense, names and quantities; vary domain
and sentence length. Direct translation should not become language lessons.
Include requested-explanation contrasts, so explanatory answers are not always
punished. Do not require single literal phrasing when alternatives are correct.

Instruction controls: requested prose/bullets/JSON, concise and requested-detailed
answers, short contextual follow-ups, answer-only transformation tasks. Content
must remain correct; format compliance cannot excuse wrong answers. Teach native
assistant EOS through real target serialization, not a prose instruction to
"emit EOS" or copied webpage endings.

Correction: wrong and already-correct Turkish, meaning-preserving minimal edits,
negation, case/person agreement and common spelling distinctions. Do not create
unnecessary rewrites or explanations when only the corrected sentence is asked.

## Pilot and acceptance gates

1. Draft40 training-only candidates:20 summaries,8 grounded QA,6 translation,
   4 instruction controls and2 corrections. Do not claim these are human-reviewed.
2. Per row retain id, capability, subskills, source_family, scenario_group,
   split, domain, source provenance, messages, target, target-authoring provenance,
   review status, required-facts rubric and hashes. No hidden chain-of-thought
   targets; this phase is final-answer SFT. Keep rubrics outside model messages.
3. Independently review coverage/faithfulness and instruction compliance. Check
   synthetic teacher answers instead of assuming teacher superiority. No external
   API request is currently configured or billed.
4. Expand only after resolving pilot defects. Audit exact and semantic overlaps
   against Occam splits, legacy benchmarks and new reserved source families.
5. Freeze immutable raw inputs/targets. Apply LFM's pinned native chat template,
   mask all prompt/earlier-turn tokens, supervise only the final assistant answer
   plus its correct terminator. Audit actual labels, empty/truncated targets,
   EOS and per-task input/supervised token counts before GPU training.
6. Compare original LFM+SFT and100M-CPT+identical SFT. Hold dataset, initial LoRA
   policy, optimization recipe and evaluation settings fixed; record parent
   differences. An experiment solely on CPT cannot isolate CPT's benefit.
7. Smoke, gradients/labels, overfit and runtime gates precede both full runs.
   W&B for training; recover all artifacts/logs before GPU termination. Freeze
   epochs/LR/update/exposure and an estimated runtime after tokenization.

## Files and next action

occam-inventory.json is generated by scripts/datasets/audit_occam_for_lfm3.py.
The40-row pilot is in pilot-train-draft.jsonl; PILOT-REVIEW.txt contains complete
prompts, targets and rubrics. Rebuild with scripts/datasets/build_turkish_sft_pilot.py
and statically check with scripts/datasets/audit_turkish_sft_pilot.py.
Next concrete work: independently review the40-row training pilot, then prepare
grouped new dev/final families and a native-tokenized mixture. Nothing in this
document certifies training readiness or publication of an expanded dataset.
