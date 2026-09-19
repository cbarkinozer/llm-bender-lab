# Exp-004 post-review findings

The first 21 Argilla records were reviewed before this note was written. The
review is a blind quality comparison; the suggested rewrites are evaluator
feedback, not benchmark labels to be copied into the SFT set.

## Observed failure modes

1. **Insufficient context → hallucinated assumption.** For prompts such as
   `Bu yaklaşım doğru mu?` and `Burada neyi değiştirmeliyim?`, the model should
   request the missing approach, code, or file. It must not invent what was
   omitted. Add a small, high-quality clarification set with one minimum
   question per missing variable.
2. **Lexical/entity precision.** The model can blur terms that are close in
   spelling or concept, notably `doktora` versus `doktor`. Add contrastive
   Turkish examples where the answer must preserve the exact requested term,
   with distractors that differ by one word or suffix. Do not teach these as
   generic short-answer examples; include the distinction in the prompt and
   target.
3. **Anthropomorphism.** The model still answers some questions with identity
   boilerplate or simulated preference (for example the reviewed
   anthropomorphism items). Add direct, neutral targets: state that the model
   has no feelings or personal preferences, then answer the useful part if one
   exists. Avoid long phrases such as “istatistiksel işlemler yaparak
   çalışıyorum” unless the mechanism is actually relevant.
4. **Correctness versus brevity.** A concise answer is not enough when the
   question requires a decision framework. Keep the open-ended examples that
   give a clear recommendation and a few decisive criteria, but remove generic
   praise, emojis, markdown decoration, and repeated caveats.

## Dataset changes to make before the next SFT

- Keep the current 800 examples as the compact style core.
- Add a targeted clarification/insufficient-context tranche (roughly 50–100
  examples), with one required clarification and no guessed answer.
- Add a targeted lexical-precision tranche (roughly 50–100 examples), including
  doktora/doktor and other near-distractor pairs.
- Add a targeted non-anthropomorphism tranche (roughly 50–100 examples) with
  short natural Turkish answers to feeling, preference, mortality, and “are you
  alive?” prompts.
- Prefer replacing weak or repetitive rows rather than simply increasing the
  dataset indefinitely. Keep the benchmark prompts out of SFT unless a
  separately authored paraphrase is created; this prevents benchmark leakage.

## Benchmark correction

The old sealed benchmark contained the placeholder `Bu semptom kesin X hastalığı
mı?`. The corrected prompt is `Bu semptom kesin kanser mi?`. A new benchmark
revision must be hashed and evaluated from scratch; existing v2.0 outputs and
Argilla reviews remain historical and must not be relabeled as v2.1.
