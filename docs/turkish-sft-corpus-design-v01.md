# Reusable Turkish SFT corpus: design v01

Owner decision, 2026-11-14: build and review a broadly useful Turkish dataset
first, release a separate LFM3-specific selection/recipe later, then DPO. MoE
and text diffusion reuse the semantic corpus with their own validated training
objectives. Keep these projects bounded so Reflex-1 remains the long-term focus.

This is a design, not an accepted dataset or a claim of an optimal mixture.
Dataset quality can be established before training; model utility still needs
held-out experiments. No finite audit establishes a universally perfect corpus.

## Dataset products

1. **General Turkish core**: independent of model, tokenizer, and chat template.
   Reviewed instruction/answer conversations, with provenance and rights retained.
2. **Reasoning configuration**: verified problems, worked solutions and final
   answers stored separately; direct-answer counterparts share a family ID and
   split. Reasoning is planned, including for 1.7B. Do not mechanically impose
   another model's think tags or make every simple interaction reason at length.
3. **LFM3 selection manifest**: references accepted core IDs plus independently
   authored repair examples and a documented task/token mixture. Publish the
   selection and model recipe separately; do not contaminate the general core
   with raw model failures or a universal brevity rule.
4. **Preference companion later**: reviewed shared-prompt/chosen/rejected records
   collected from the frozen SFT model. Keep separate from SFT targets.

Retain raw candidates and decisions. Never silently delete rejected records or
overwrite accepted releases. Each snapshot lists accepted IDs, edits, reasons,
source revisions, split assignments, hashes and review export identity.

## Coverage contract

The recovered 500-item cohort measures five tasks only. It cannot establish
strength or weakness in the remaining categories below. Every category needs
independent development and final evaluation families.

| Capability | Desired behavior and review checks | Current evidence |
| --- | --- | --- |
| Grounded QA / reading | Answer the asked question, cite supplied evidence when requested; include answerable and genuinely unanswerable contexts | Two answerable QA tasks; severe completion failures |
| Summarization | Preserve main points, entities, numbers, negation, uncertainty; match requested compression | MLSUM diagnostic |
| Translation | Preserve meaning in both directions; vary register and requested explanation | EN→TR measured; TR→EN untested |
| Turkish editing | Minimal necessary correction; preserve already-correct text and meaning | GECTurk diagnostic |
| Instruction and structured output | JSON/schema, tables, bullets, extraction, ordered constraints; correct content and valid structure | Only indirectly observed; add direct probes |
| General knowledge and explanation | Supported, accurate answers at requested depth; distinguish stable facts from time-dependent ones | Not established by these 500 |
| Reasoning / mathematics | Verifiable arithmetic, logic, constraints, multistep grounded inference; validate steps and final result | Not tested by these 500 |
| Coding and practical technical help | Small executable tasks and explanations; tests/checks where feasible | Not tested |
| Multi-turn interaction | Context tracking, corrections, follow-up references, useful clarification | Not tested |
| Planning and practical writing | Useful constraints, feasible steps, audience and register matching | Not tested |
| Creative writing and transformation | Coherent original Turkish, requested style, preserved constraints | Not tested |
| Uncertainty and responsible assistance | Admit missing evidence appropriately; helpful benign answers; proportionate handling of sensitive requests | Not tested; do not teach blanket refusal |

Cross-cutting axes: colloquial/formal Turkish, morphology and diacritics, varied
topics, short/medium/long context, direct/detailed answer, difficulty, source,
single/multi-turn, numeracy, negation and ambiguity. Do not call topical variety
alone general coverage. Tools/actions can be a separately scoped extension;
the Reflex benchmark and specialist decision labels stay independent.

## Source selection, not concatenation

Audit Occam, Turkish-SFT-Dataset-v1.0, Turkce-Atlas-Instruct, and
Turkish-CoT-Instruct-Dataset in the next phase. Pin revisions; measure their
actual schemas, coverage and source-family duplication; inspect stratified
samples and trace upstream provenance/rights. Their roles remain hypotheses
until the audit identifies strengths. Dataset card licenses alone do not clear
upstream sources. Preserve original licenses and credits; do not relicense a
mixed corpus wholesale without establishing compatibility.

Owner clarification, 2026-11-14: Occam data comes exclusively from the published
`cbarkinozer/Occam-Turkish-Response-SFT` repository. Use its pinned public files
and metadata; do not supplement it with historical local inventories, repaired
drafts or alternate versions. Record unavailable historical provenance as a
limitation of that release, not as another source to ingest.

Choose independently correct, diverse examples for empty coverage cells. Use
original synthetic examples to fill demonstrated gaps after source review.
Never use the recovered benchmark prompts, documents, answers, translations or
paraphrases as candidate authoring material. Transfer only abstract failure
categories to generation instructions.

## Controlled growth

1. **Calibrate** on 60 diverse candidate records, including the existing 40
   training-only drafts if eligible after review. Agree on accept/edit/reject
   using the same rubric. Those 40 are drafts, not approved seed data.
2. **First reviewed snapshot**: aim for about 300 accepted records, covering all
   core capabilities at more than one difficulty/length/register. Include a
   verified reasoning tranche; numbers are planning budgets, not pass criteria.
3. **Coverage build**: expand in batches of 200–300 candidates toward roughly
   1,000 accepted records. Inspect rejection reasons after every batch; revise
   acquisition before generating more of a defective family. Every released
   v01 row requires owner review, including corrections and reasoning.
4. **Freeze v01** when the coverage checklist, provenance, correctness, diversity,
   contamination checks and human review are complete. If important gaps remain,
   expand selectively toward 2,000–3,000 or revise scope explicitly. Do not
   create a huge pool and rely on mass deletion later.
5. **Measure utility** with a small, controlled LFM3 LoRA experiment after the
   dataset freeze. It may motivate v02 or an LFM3-specific manifest; preserve
   general coverage rather than removing useful material because one model
   struggles with it. Compare nested accepted subsets only if learning curves
   justify the extra compute. A static review cannot identify a best row count.

Track per-category counts, unique families, domains, length/difficulty diversity,
review acceptance/edit rates, source concentration and rationale/final-answer
lengths. Measure input and assistant token shares separately using LFM3 and each
later model; raw row fractions hide exposure from long answers. Freeze concrete
mixture targets after source inventory, not before knowing available quality.

## Review and acceptance

Use the existing Argilla workflow in a subsequent implementation phase. Show
prompt, context, proposed final answer and optional worked solution; allow an
editable corrected answer, accept/edit/reject, rubric dimensions and notes.
Keep automated checks and provenance visible to the reviewer without copying
them into model messages. Owner approval is pending until actually submitted.

Review correctness, grounding, instruction compliance, Turkish naturalness,
appropriate detail, completeness, ambiguity, diversity and source eligibility.
A fluent hallucination fails. A short answer missing the main point fails.
Reasoning must have valid steps and a valid final answer; check executable or
numeric claims with tools. Uncertain rows remain quarantined. After edits,
rerun applicable checks and preserve original + edited targets with provenance.

Store stable IDs, model-independent messages, final answer, optional worked
solution, capability/subskills, source revision/row, license, source family,
scenario group, transformations, authoring metadata, checks, review status and
split. Review notes, gold rubrics and evaluator scores remain outside inputs.

## Evaluation boundary and training gate

Assign source/problem/template families to train/dev/test before writing
variants; all direct/reasoned variants and translations stay together. Old
Occam dev and the inspected CETVEL500 remain development/comparison evidence.
Reserve fresh final families from this assistant's iterative authoring and
recipe tuning; user or independent evaluator can hold them. Broad evaluation
needs more than the old plan's 100 final examples for reliable per-capability
claims; size it after taxonomy and uncertainty requirements are fixed. Keep
English/general regression probes separate and report their scope.

Do not train until accepted snapshot and review export exist, source rights and
contamination dispositions are recorded, native serialization/assistant labels
and termination are inspected, and smoke/tiny-overfit gates pass. Compare CPT
unchanged with CPT+SFT; original+identical-SFT is valuable for measuring whether
CPT adds value. Reasoning uses its own held-out accuracy/token/latency analysis.
DPO follows a stable SFT checkpoint and fresh, reviewed preference prompts.

The next action after response analysis is the pinned four-source audit and
coverage comparison, followed by Argilla calibration.
