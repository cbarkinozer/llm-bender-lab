# exp-007-boundary-benchmark

## Status and purpose

Draft development benchmark awaiting human review. It has 50 original Turkish
user prompts: 10 in each exp-006 failure family. This is **not** a fresh final
test or an external benchmark. Its design is informed by exp-006 review, so it
may guide the next dataset but cannot support an independent release claim.

The dedicated 50-record benchmark-authoring review queue is now available:
<http://127.0.0.1:6900/dataset/8511f2a9-b73b-4244-ac5b-7ca993fd2855/annotation-mode>.
Use `import_argilla_review.py` to obtain the current instance's link; existing
reviews are preserved. Review prompts and scoring anchors rather than assistant
targets. The benchmark remains draft until these decisions are exported and validated.

## Design

- `development-v1.csv` contains prompts, a decision-boundary contrast, and a
  compact scoring anchor. It contains no model outputs or SFT targets.
- Hidden ambiguity mixes necessary clarification with already-answerable and
  conditional cases. The other families similarly mix the easy rule with its
  exception, so a model cannot pass by always asking, always being terse, or
  always denying subjective experience.
- Prompts use varied everyday Turkish rather than the old `Kaynak`/`Soru`
  templates. The five groups remain separate for slice-level diagnosis.
- The file is frozen only after human review and validation; its current status
  is `draft`. Keep future training prompts, contexts, and target answers
  independently authored. Do not paraphrase or translate these 50 items into
  training data.

Draft CSV SHA-256: `93eb7eba95f65962b38c3c205fc942651447b13356e5b8f39e8e83bef36012f8`.
The draft has 50 unique IDs/prompts, 10 items per family, and zero exact
normalized prompt matches against the exp-006 958-row training artifact,
the historical exp-003 2,442-row artifact, exp-006 and exp-005 holdouts,
and the historical exp-002 test. This check
does **not** establish semantic independence; human review must inspect shared
story structures and underlying tasks.

## Intended next stage

After this benchmark is reviewed, prepare a separate **20-example training
candidate tranche per family** (100 total), emphasizing natural Turkish and
both sides of each decision boundary. Human-review the candidate responses and
check conceptual/template overlap, not just lexical overlap. The next model
experiment, if authorized, needs a separate untouched final test for any
quality claim.

## Scoring

For each item, first judge task completion, correctness, and Turkish coherence.
Then inspect the listed pass condition and whether the response uses an
unnecessary clarification, unsupported causal story, stock emotional disclaimer,
semantic contradiction, or excessive filler. A short but incorrect answer
fails. Compare base and adapter under the same frozen decoding protocol with
randomized identities; report family counts and per-item failures, not only a
single aggregate win rate.
