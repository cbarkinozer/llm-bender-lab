# Next steps after the bilingual development review

Status: training and development inference complete; 20/20 owner reviews
exported. Four LoRAs, logs and predictions are verified locally. The previous
pod can remain closed. See BILINGUAL-DEV-REVIEW.md for evidence and limitations.

## 1. Freeze candidates before opening the final test

Use original LiquidAI/LFM3-1.7B, exp-010 checkpoint60, and exp-011 checkpoint69.
The latter two are selected from development results; keep checkpoint100/113
as archived alternatives, not additional final-test selection candidates.
Record adapter hashes, pinned CPT/base revisions, dataset hashes and protocol
in the final inference manifest. No new training is required for this stage.

## 2. Prepare the final evaluation locally, then use one GPU session

Implement a resumable final-evaluation entrypoint using the existing matched
vLLM implementation. Keep final references separate from generation inputs.
Verify local adapters and prepare installation/merge commands before renting
the pod. Audit generated prompt token IDs against the native template and
check thinking-disabled prefix handling; do not silently alter the historical
protocol. If a real protocol defect is found, document it and run a separate,
matched diagnostic for all three models rather than mixing protocols.

Run the frozen 35 task groups in four directions (140 prompts), plus eight
symbolic controls: 148 prompts per model, 444 outputs total. Do not reconstruct
these from older crosslingual outputs. Preserve references, item IDs, actual
termination reasons, token counts, raw text and generated token IDs.

Before closing the new pod, download only adapters if changed, inference
outputs, logs, environments, manifests and scores. Verify archive/member
hashes locally. No full model weights need to be downloaded.

## 3. Score capabilities separately and minimize annotation

Score arithmetic and symbolic controls against frozen references with
task-appropriate deterministic extraction, reporting extraction failures
separately. Compare the same task across all four directions. Track:

- Answer correctness, independently of formatting and requested language.
- Turkish naturalness, meaning preservation and spelling.
- Requested output language, including Turkish-to-English compliance.
- English retention and symbolic arithmetic regressions.
- Repetition, length-limit hits, exposed think tags and duplicated answers.

Create one blind Argilla record per task group: 35 records, grouping the four
directions and three anonymous model outputs clearly. Keep only ranking and
free-text reasoning as requested; optional targeted comments can identify a
direction. Rank overall task performance, while per-direction automatic and
qualitative analysis retains the diagnostic detail. Keep identities consistent
within a group, randomized across groups, and hidden until export. Put the
eight symbolic controls in the automatic report; manually inspect ambiguities
without adding routine annotation. Preserve the raw owner submissions.

## 4. Decide whether another training experiment is justified

Write the final comparison before proposing more data. This is a small pilot,
so use paired counts and task-level uncertainty; do not pool four related
directions as independent samples or claim broad capability from preference.
Once inspected, this final packet is consumed: future tuning requires a new
independent holdout for final claims.

| Observation | Next action |
|---|---|
| Bilingual improves Turkish correctness while preserving English and arithmetic | Keep the bilingual candidate; consider a modest targeted data expansion after reviewing failures. |
| Bilingual helps language compliance but not correctness | Treat that as instruction-following improvement; do not scale translations on the assumption that reasoning transferred. |
| Turkish-only remains as good or better, or bilingual loops/regressions dominate | Keep Turkish60 and stop scaling this bilingual recipe. |
| A template/termination defect explains failures | Fix it in a separate controlled diagnostic before changing data or optimization. |
| Both candidates fail Turkish tasks that base solves in English | Consider one causal parent ablation: identical chosen SFT recipe/data on original base versus CPT parent; freeze a new holdout before running it. |

The parent ablation is conditional, not an authorized run waiting for a GPU.
Current comparisons cannot isolate the effect of CPT because SFT candidates
share that parent. Do not assert that CPT caused a regression without that
control. Likewise, a near tie does not establish that more rows or repeated
epochs will solve the problem.

## 5. Bound the project before moving on

If evidence supports a further pilot, change one main variable, keep the
reviewed 160 groups reusable, and create only the missing skill examples;
do not default to annotating 2,000 more rows. Keep final-test tasks and their
translations out of training. If gains remain weak after a justified diagnostic,
archive the findings and prioritize Reflex-1 decision models.

Defer DPO until the chosen SFT model has acceptable factual/task correctness
and reliable stopping. DPO can target preferences but is not a presumed cure
for arithmetic or Turkish meaning failures. MoE and text-diffusion SFT remain
later learning projects, separate from the current diagnosis.
