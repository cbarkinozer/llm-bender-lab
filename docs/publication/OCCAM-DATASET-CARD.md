---
license: apache-2.0
language:
- tr
task_categories:
- text-generation
size_categories:
- n<1K
tags:
- synthetic
- human-reviewed
- sft
- turkish
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.jsonl
  - split: validation
    path: data/validation.jsonl
---

# Occam — Turkish Response SFT

A small, human-reviewed Turkish response-style dataset curated by the author,
[cbarkinozer](https://huggingface.co/cbarkinozer), for the
[Occam adapter](https://huggingface.co/cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora).

The repository owner selected Apache-2.0; see `LICENSE`. This private upload
does not attest completion of historical provenance/provider-terms review.

## Purpose and composition

Human-reviewed, synthetic/AI-assisted Turkish conversations used for Occam
LoRA response-style SFT on Qwen3.5-4B. **104 training rows and 20 development rows.**
The initial80/20 selection was followed by24 additional training scenarios;
the released 104/20 split is **not** an 80/20 percentage split. Twelve independent
project control items and all external CETVEL inputs/references are excluded.
These are training targets, not labels certifying factual correctness in every case.

Desired behaviors: immediate answers and requested formatting; accurate extraction;
faithful shortening preserving uncertainty/negation/conditions; useful explanations;
clarification only when needed; no unsupported causes, motives or guarantees;
Turkish character/word/suffix/tense precision; no fabricated model feelings,
preferences or memories; neutral acknowledgment without reflexive advice/disclaimers.
Appropriate longer answers are allowed: brevity is not the sole objective.

## Creation and provenance

Questions were selected/curated from historical project inventories and new
project-agent-authored scenarios. Original Qwen3.5-4B generations informed minimal
edits, then a human reviewed/rewrote targets, sometimes assisted by a personal AI
assistant. Later core target repairs and24 reviewed independent additions formed the released dataset.
This is not naturally occurring human conversation and not wholly human-authored.
The exact personal-assistant provider/model and terms must be supplied by the owner;
some historical synthetic provenance is incomplete. Do not substitute a guessed
teacher model or claim every sample derives from the same generator.
`source-origins.json` preserves available origin/category counts; immutable original
experiment files carry fuller internal provenance and review receipts.

## Schema and supervision

JSONL with `id`, `category`, `subtype`, `scenario_group_id`, `origin`, `source_id`,
`evaluation_only`, and conversational `messages` (role/content). A final assistant
message contains the exact reviewed target. Earlier assistant turns are context,
NOT training targets under the recorded final-assistant-only loss policy.
Review criteria, original generations, user/review identifiers, annotations and
internal file paths are not included in the public training messages.

```python
from datasets import load_dataset
dataset = load_dataset("cbarkinozer/Occam-Turkish-Response-SFT")
print(dataset["train"][0]["messages"])
```

Apply the pinned model's native non-thinking chat template. Do not train raw
`user:` strings or include the annotation rubric as instructions. Hashes of the
source and clean release files are in `release-manifest.json`; serialization differs
from internal provenance-rich rows, but conversation/target content is preserved.

## Split and leakage limitations

Train/validation exact/near/scenario checks found no identified item-level leak;
retained task-family similarities and generic short answers are documented in
`SEMANTIC-LEAKAGE-REVIEW.md` in the code repository. Audits do not prove zero semantic
overlap. The20 validation prompts were repeatedly used during model/data selection:
they are a **development set**, not a clean final evaluation. One reference,
me-089, was disputed and preserved; use recorded sensitivity analysis rather
than silently treating all references as authoritative.
Do not add CETVEL questions, references or paraphrases to these training rows.
External evaluation-source licensing is separate from this dataset's license.

## Limitations, privacy and rights

Small, curated, uneven task distribution; many everyday synthetic situations.
No evidence that similar token frequencies prevent catastrophic forgetting.
Human review can miss unnatural Turkish, incorrect reasoning and unsupported claims.
Historical generation cannot be reproduced exactly from all surviving metadata.
Review every released row for privacy/third-party content before public upload;
this draft does not assert a completed legal or exhaustive privacy audit.
Dataset license: Apache-2.0, selected by the repository owner.
Historical provenance and provider-terms review remain incomplete; a license
selection alone does not establish all underlying publication rights.

