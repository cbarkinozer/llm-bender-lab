# AdygheBench v0.1-candidate

`AdygheBench` is a user-provided, small diagnostic suite for **Adyghe**
(West Circassian; ISO 639-3: `ady`).  The source title says “AdigeBench”; this
repository uses the language's common English name while retaining the source
name in the artifact metadata.

## Status and permitted claim

This is a **candidate development benchmark**, not a final proficiency test.
It may be used to diagnose a baseline and compare development checkpoints under
an identical protocol.  It must not be used to make a general claim such as
“the model speaks Adyghe at X%.”

Before a reportable result, a qualified native reviewer must validate every
item, especially IDs 121–145 (morphology/syntax) and all free-generation tasks.
The reviewer must also define accepted alternative answers and the scoring
rubric.

## Training and interpretation

The supplied benchmark is visibly derived from `adige data.txt`: it reuses its
lexicon, bilingual phrases, and the Crow, Wind-and-Sun, and UDHR passages.
The material is user-authored and authorized for this project's training use.
It may therefore be used for training, validation, or synthetic-data creation.

If the intended experiment teaches the model this supplied curriculum,
AdygheBench measures **curriculum mastery**. A separately authored/collected
and native-reviewed holdout is required only to claim generalization beyond
this material.

## Contents

The source has 200 rows:

| Family | IDs | Intended diagnostic |
| --- | --- | --- |
| Lexical and bilingual recall | 001–100 | closed vocabulary and EN↔Adyghe translation |
| Conversation | 101–120 | short Adyghe responses |
| Morphology and syntax | 121–145 | linguistic analysis; native review required |
| Reading and summaries | 146–180 | comprehension and generation over three source groups |
| Semantic/classification | 181–190 | closed semantic relations |
| English→Adyghe instruction | 191–195 | currently duplicates earlier lexical prompts |
| Contrast explanations | 196–200 | free Adyghe explanation |

The JSONL stores semantic fields only: `prompt`, `context`, `references`,
`task`, `source_group`, and an initial scoring policy. The builder attaches the
relevant full passage to every reading item, so it tests comprehension rather
than recall of an omitted source. It deliberately does not embed a Qwen chat
template.

## Known design limits

- There are nine exact duplicate-input groups. IDs 191–195 repeat earlier
  lexical prompts, while some conversation prompts intentionally allow
  different acceptable replies. There is one additional repeated question
  template (159/174) over different passages, so it is not a duplicated input.
  Duplicate inputs must not be counted as independent evidence, and
  multi-answer prompts require native scoring.
- Many lexical items test recall of a very small vocabulary, not productive
  language ability.
- Reading questions from the same story are correlated.  Report scores by
  `source_group`, not only a pooled item accuracy.
- Exact normalized match is reasonable for closed answers, but it is
  insufficient for conversations, summaries, contrast explanations, and many
  morphology answers.  Preserve outputs and manually score those items using a
  pre-written native rubric.
- Source provenance is user-authored and training-authorized. Confirm the
  desired licence only before public release or external redistribution.

## Import and validation

The versioned source hash is:

```text
adige-bench.txt SHA-256
c1059e339dbf53ed8df10745d62db7f7fafafa2899c1ea94015fa29177258366f5
```

From the repository root, build the committed JSONL and audit from the original
UTF-8 source:

```powershell
python scripts/evaluation/build_adigebench_v01.py `
  --source 'C:\Users\cbark\Downloads\adige-bench.txt' `
  --related-source 'C:\Users\cbark\Downloads\adige data.txt' `
  --output-jsonl benchmarks/adigebench/v0.1-candidate/adigebench-v0.1.jsonl `
  --audit-json benchmarks/adigebench/v0.1-candidate/audit.json
```

The builder fails if IDs or field counts differ or if either supplied source
hash differs from the pinned artifact. It records input/output hashes and
surfaces exact duplicate prompts. Run it again after changes to a candidate
source; a changed hash is a new benchmark revision.

## Evaluation protocol to freeze before the baseline

- Generate direct answers using the model's native chat template with
  `enable_thinking=False`; this suite measures direct usability first.
- Use `do_sample=False`, `temperature=0`, a fixed seed, pinned model/tokenizer
  revisions, and task-appropriate output caps.
- Preserve per-item prompt, raw output, normalized output, parsed answer,
  reference, scoring mode, and failure category.
- Do not batch until output-equivalence with sequential inference has been
  demonstrated for the exact engine/version.
- Report closed exact-match results separately from native-reviewed generation
  results.  Do not pool them into one “Adyghe score.”
