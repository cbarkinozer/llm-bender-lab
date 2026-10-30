# Occam 2 authored Turkish reasoning data v1

80 training examples and 20 held-out tests, four categories balanced 20/5:
updates/attribution, rules/exceptions, quantities/schedules, evidence/uncertainty.
All are assistant-authored synthetic scenarios, not copied benchmark items,
private correspondence, or teacher-model hidden reasoning. No external teacher
API was called. Authoring date: 2026-10-28.

- `authored-cases.tsv`: editable source, including solutions; not a trainer input.
- `train.jsonl`: only the80 supervised conversations.
- `test-prompts.jsonl`: only the20 test conversations with no assistant targets.
- `test-keys.jsonl`: references for post-run semantic scoring; never sent to model.
- `manifest.json`: exact hashes, counts, lexical split audit and provenance.

Rebuild with `python pipeline.py build` from the model directory. Generated
JSONL is deterministic. Changing authored data invalidates preparation and baseline
hashes; never revise it in response to held-out baseline mistakes.

## Review and limitations

The author made a semantic self-review of all100 worked answers. This is not
independent human annotation. The review corrected a spelling error and made the
time-window boundary explicit before any held-out inference. Numerical checks
recompute arithmetic/time outcomes; native-tokenizer checks cover all80 masks.
No train/test lexical pair crossed the0.65 similarity flag threshold. This does
not prove semantic independence: related task skills intentionally occur in both.

The data teaches compact, explicit reasoning over short sources. It is likely
easy for a capable 4B model; baseline ceiling is a real possibility. It is not a
broad Turkish, long-context, factual-knowledge or advanced-reasoning benchmark.
If development checks show the task needs redesign, version a new dataset before
held-out inference. A base near ceiling is an honest result, not grounds for
selectively replacing test questions.

## Scoring before viewing test outputs

Score final answers semantically against each key: correct=1, partial=0.5,
wrong/unsupported/empty=0. Accept equivalent phrasing and number formatting.
All requested subanswers must be correct for a full pass. The primary accuracy
is full passes/20; partial scores are reported separately. Do not require a model
to reproduce the authored worked solution or exact wording.

Record critical invented facts, reasoning-answer contradictions, unnecessary
clarification, Turkish reasoning adherence, final-answer verbosity and natural
termination separately. A token-limit failure is an operational failure even if
partial text contains a plausible answer; retain semantic and termination fields
separately. Infrastructure errors are not semantic errors and require explicit
unchanged rerun records. Inspect all paired outputs, preferably blinded to model.

The eight separate regression probes check basic formatting, translation,
source faithfulness, uncertainty and arithmetic. Their small count provides
qualitative regression evidence, not a broad forgetting guarantee.
