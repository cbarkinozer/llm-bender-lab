# CETVEL500: fixed Base versus final F, 2026-10-04

Completed500 NEW source-group-disjoint questions per arm;1000 outputs recovered.
F's output-compliance/reference-overlap gains persist beyond the100 pilot.
Translation is essentially unchanged. General semantic/Turkish superiority is
not established: blind human30 review is prepared and pending. No new SFT/W&B.

## Task-native results

Each task has100 questions. QA F1/ROUGE are displayed on0-100 scale; BLEU/chrF
already use that scale. Do not average different metrics into a single accuracy.

| Task / metric | Base | F |
| --- | ---: | ---: |
| GECTurk exact correction | 0/100 | 30/100 |
| TQUAD exact answer | 0/100 | 36/100 |
| TQUAD token F1 | 20.06 | 64.58 |
| XQuAD-TR exact answer | 0/100 | 29/100 |
| XQuAD-TR token F1 | 13.68 | 55.84 |
| EN-to-TR corpus BLEU | 16.84 | 16.81 |
| EN-to-TR corpus chrF | 52.16 | 52.43 |
| MLSum-TR ROUGE-1 | 25.54 | 27.82 |
| MLSum-TR ROUGE-2 | 12.79 | 14.79 |
| MLSum-TR ROUGE-L | 18.45 | 20.93 |

Exploratory paired bootstrap95% intervals for F-minus-Base,5000 resamples:

| Difference | Estimate | Interval |
| --- | ---: | ---: |
| GEC exact match (percentage points) | +30.00 | +22 to +39 |
| TQUAD F1 points | +44.51 | +37.56 to +51.24 |
| XQuAD F1 points | +42.16 | +35.44 to +49.00 |
| Mean sentence chrF points (NOT corpus chrF) | +0.38 | -0.90 to +1.68 |
| Summary ROUGE-L points | +2.49 | +1.18 to +3.80 |

Intervals characterize this source-group cohort, not all CETVEL or human
correctness. No formal multiple-comparison-adjusted superiority claim. Extra
prose depresses exact match and QA F1. The pilot's completed20 human review found
all8 reviewed QA items pass for both models despite large automatic gaps; do
not silently reinterpret this run's QA metric gain as new knowledge/reasoning.
GEC alternatives/over-correction and summary faithfulness need human inspection.
GEC30/100 exact is an improvement signal, not proof grammar is solved.
Translation interval spans zero; no convincing translation gain/regression.

## Generation and all failures

- Base nativeEOS496/500; F499/500.
- Base repetition guards: gecturk-00400 (1792tokens), gecturk-02614 (272),
  gecturk-13950 (336), gecturk-15107 (224).
- F repetition guard: tquad-00747 (176tokens). Retained and scored, no retry.
- No length-limit or wall-time-guard terminations. One final long F answer took
  additional time but eventually reached native EOS; it was not discarded.
- Median output tokens Base98/F26; mean158.802/63.954. Brevity alone is not accuracy.
- Benchmark + scoring + paired analysis1215.82seconds (~20m16s), excludes setup,
 9GB model download, transfer, recovery and local review UI. Model download~96s.
- RTX4090/24564MiB,driver590.48.01,Python3.12.3,Torch2.13.0+cu130,
  vLLM0.30.0,Transformers5.18.0,peft0.21.2. Full versions in saved pip freeze.

Same pinned Base/F identity and generation recipe as pilot: BF16, greedy,
rep1.05,8192 context/4096 output, active cap8,eager,no prefix cache,thinking off,
modelEOS248044 selected explicitly instead of tokenizerEOS248046. All prompts
fit; no truncation. Exact arm prompt/input-ID/config/template/package parity passed.
Driver differs from the earlier pilot; compare the paired models WITHIN this
fresh run. Do not assume bitwise equivalence across pods or pool cohort scores.

## Blind human30 and decision

Completed30/30; actual submitted grades/preferences exported read-only to
human-review-v1/summary.json. Single reviewer, six/task, identities shuffled
per item. F19 preferences/base6/tie2/neither3; F23pass/4partial/3fail versus
base21/3/6. QA12/12 both pass and all12 prefer F; GEC F4/6pass vs base0/6;
translation5/6 each, preferences2/2/tie2. Summaries base4/6pass versus F2/6,
preferences base4/F1/neither1. Latest30 optional notes were blank; external AI
commentary supplied by the user is not a recorded second evaluator or saved notes.

Decision2026-10-04: close this phase and share F as an experimental concise/direct
Turkish style adapter. Meaningful preference/compliance signal, no universal
capability preservation or summarization-faithfulness claim. No new fine-tune.
Future benchmark-driven training requires independent scenarios and a fresh test.
The original pre-review procedure below is preserved as protocol history.

Six preselected random questions per task, chosen before any new outputs.
Balanced per-item shuffled P/Q identities, private map outside Git. Required
P/Q/tie/neither preference and both pass/partial/fail; optional notes. Reference
and actual raw answers read back and verified on30/30 records; UI HTTP200 checked.

http://127.0.0.1:6900/dataset/1ddfe4d9-5d36-46bc-a1c8-0ebc4959c941/annotation-mode?page=1&status=pending

Judge meaning, source-faithfulness, grammatical correctness and natural Turkish
before cosmetics. Inspect guards and metric misses separately as diagnostics,
not replacements for the random30. No external judge called or human labels by
agent. F remains the fixed candidate, not modified for de/da. After human review,
summarize recurring error categories and decide whether a balanced training
supplement is justified. Never teach these benchmark sentences/targets/paraphrases.
If feedback guides training, classify500 as development and use a fresh final test.

## Reproducibility, recovery and setup lessons

45 archived files verified locally,1000 outputs and final F hashes verified.
Archive4246830bytes (~4.25MB), SHA256:
`abcd9cc94a7562e8c7f6a70685aa11ba54e39d0f81b4666a2f610035dc7ecf5a`.
Local: C:/Users/cbark/Documents/llm-bender-artifacts/cetvel-500-base-F/recovery-v1/
verified-recovery. Results-v1 retains per-arm answers/manifests/template/scored
samples, score comparison, paired analysis, engine settings, setup/run logs,
versions, invocation, backup file index/metadata and recovery proof. Actual
remote source snapshot is in the verified archive; narrow prepared source
archive and transfer hashes also retained externally. F weights already locally
recovered; Base immutable revision downloadable. GPU is safe to close.

Existing key authenticated on direct/proxy with explicit BatchMode/IdentitiesOnly.
No key content in Markdown, no .env upload or W&B needed. An early adapter
extraction while SCP was still active failed with EOF. After transfer exit0,
archive SHA matched; re-extracted and weight/config hashes passed BEFORE benchmark.
No benchmark retries, changed decoder settings or hidden output filtering.
Reusable authentication/transfer lessons recorded in environment-setup-gotchas.
Standalone launcher prevents SSH-held log pipes and is preserved in recovery.
