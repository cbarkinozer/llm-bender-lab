# Semantic QA: all-row triage, selected deeper review

**Evaluation only. Machine-assisted Codex agent annotations; no human review or human approval.**

All 100 TQUAD and 100 XQUAD-TR rows have individual annotations. This is an honest all-200 triage artifact, not a completed full-text semantic adjudication of all 200 responses. Do not report a semantic accuracy score from these annotations.

## Provenance and instructions

Source: `experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl`
Source SHA-256: `0abe42c892374d79a907554189345c8ba41848ea1c93c008e64e9c6dec0ab595`

Read repository `AGENTS.md`, `docs/evaluation-guide.md`, and experiment README/config. In particular, distinguish semantic correctness, parser/reference diagnostics, source grounding, repetition and stopping. The experiment configuration labels CETVEL a previously inspected comparison cohort, not a pristine final holdout. No generations, rescoring of original metrics, training examples, or original artifact edits were performed.

## Inspection scope and limitations

Every selected row was parsed with UTF-8 and presented to the agent with its question, reference answers and response opening (at least 330 characters where available). Literal-match windows and some tails were also inspected. Initial oversized tool outputs were truncated and were not counted as full reviews; bounded later batches covered all 200 row openings.

Full-text review means the entire literal prediction was displayed and read. Compressed review means source context and a response view of unique sentences/templates were read, with repeated sentences and numeric variants collapsed; it is not a full literal-text review. Other rows are explicitly excerpt triage. Full machine scanning is not equivalent to full semantic inspection.

| Scope | Rows |
|---|---:|
| excerpt_triage | 169 |
| compressed_response_semantic_review | 19 |
| full_text_semantic_review | 12 |

Full literal-text review IDs: xquad_tr-01018, tquad-00468, tquad-00718, xquad_tr-00612, xquad_tr-01137, tquad-00179, tquad-00538, tquad-00877, tquad-00747, xquad_tr-00443, xquad_tr-01113, tquad-00232.

Compressed review IDs: tquad-00180, tquad-00594, tquad-00512, tquad-00155, tquad-00544, tquad-00460, xquad_tr-01037, tquad-00531, xquad_tr-00510, tquad-00294, xquad_tr-00209, xquad_tr-00964, tquad-00300, tquad-00292, xquad_tr-00528, tquad-00708, xquad_tr-00718, tquad-00350, tquad-00325.

For excerpt-only rows, `answer_anywhere=not_established_from_excerpts` deliberately does not assert that no valid paraphrase occurs later. Early means first 300 Unicode characters, although the initial displayed opening was 330 characters. Supported answer presence is a local claim about the requested slot, not approval of the whole response. Grounding contradictions and unsupported continuation remain separately visible. Some source contexts themselves have questionable wording or incomplete references; no external fact checking was performed. Agent identity/model revision and sampling settings were not exposed as a reproducible independent judge configuration. This was not blinded, and original metrics/model identity were visible.

## Reference-location diagnostics, not correctness

Normalization used for this QA annotation file: Python `str.lower()`; replace non-word/non-whitespace characters with spaces using `re.sub(r'[^\w\s]', ' ', text.lower())`; collapse whitespace with `split()` and space joining; require the whole normalized answer sequence bounded by spaces. No explicit Turkish I/? handling or NFC normalization is applied. Match each available reference against the full prediction, first 300 raw Unicode characters, and first raw line separately, then normalize each segment. This differs slightly from the parent diagnostics, which handle Turkish I/? and NFC. The counts agree on this cohort; matching totals do not establish equivalent normalization. The main report uses the parent diagnostics. This is not EM, semantic scoring, or answer extraction.

| Task | Anywhere | First 300 characters | First line |
|---|---:|---:|---:|
| tquad | 16 | 13 | 11 |
| xquad_tr | 5 | 3 | 3 |

Literal unbounded substring matches give different counts and false positives (e.g. On inside another word or 17 within a year). Even normalized boundary matches can be incidental: enumerated item 70, a wrong birth/death relation, or 12 inside a numeric enumeration. None of these match counts were used to assign semantic correctness.

## Semantic findings

- Correct early answer slots can coexist with severe continuation failures: tquad-00718 gives the solar-year measurement before unsupported history; tquad-00155 gives the right fee with a wrong year; tquad-00544 names the rector then changes the university; tquad-00325 gives Istanbul then contradicts the birth year.
- Source copying needs its own label: xquad_tr-01037 copies the whole Rhine passage, whose first sentence answers the question; tquad-00512 repeats the correct source sentence. These have responsive grounded content but do not demonstrate concise answer selection or stopping.
- Gold names are insufficient: tquad-00538 changes Ibn Bacce to Ibn Batira and reverses influence direction. tquad-00531 attaches the expected personal name to the wrong person. tquad-00747 mentions Mp 5 as a machinery category, not a submachine gun.
- Gold numbers are insufficient: tquad-00795 uses 925 for birth rather than death; tquad-00469 explicitly answers three maps despite mentioning two coasts; tquad-00267 chooses eight while 70 occurs as an item number.
- Valid paraphrases can lack the reference string: xquad_tr-00510 gives Eisenhower Highway, explicitly supported by context; tquad-00468 gives Piri Reis and 1513; xquad_tr-00964 preserves 9–18 using an ASCII hyphen. xquad_tr-00612 gives approximately 70,000 but drops the over qualifier.
- xquad_tr-01137 contradicts the eighteenth-century source with a nineteenth-century origin and omits the Church of England. xquad_tr-00181 produces an unrelated Ibn Sina essay. Many other openings drift into municipal projects, Turkish news, generic website prose, or question echoes.
- tquad-00232 contains the source-supported top-five statement late, while its opening invents fourth place. A late supported claim does not validate its unsupported precision, attribution or statistics.

## Repetition and stopping

| Task | Length limit | EOS | External exact-loop guard |
|---|---:|---:|---:|
| tquad | 73 | 21 | 6 |
| xquad_tr | 81 | 16 | 3 |

Across 200 rows: 154 length-limit terminations, 37 EOS, and 9 exact-loop guard stops. EOS records runtime termination; it does not establish that the model stopped promptly after answering. Length-limit and external loop guard stops are not natural completion. The annotation repetition diagnostic scans all overlapping whitespace-token 12-grams and flags a maximum count of at least three; it is machine assistance, misses shorter/near repetition, and does not establish a semantic loop on its own.

## Corruption and rendering

Explicit UTF-8 decoding/output was used (`sys.stdout.reconfigure(encoding="utf-8")`). Literal U+FFFD count across all 200 semantic prompts and predictions is zero, independently confirming the parent observation. Garbled default-console Turkish rendering is not artifact corruption.

Actual source mojibake does exist independently of U+FFFD: xquad_tr-00209 context contains `San Diegoâ€“Tijuana`; xquad_tr-00241 contains broken smart-quote sequences `â€˜` / `â€™`; xquad_tr-00266 contains `1â„2` in an imperial fraction (also in its reference). These source defects are distinct from generated semantic entity/relation/type corruption. None were repaired in the original artifacts.

All 37 raw_output/prediction differences coincide with EOS rows: the raw output retains a terminal special-token marker. These differences should not be labeled text corruption merely because prediction strips that marker.

## Use restrictions

The JSONL contains evaluation annotations and short audit excerpts only. It is not a training dataset and must not be converted to training examples. `reviewer="codex-agent"`, `human_reviewed=false`, and `human_approved=false` apply to every row. Full semantic adjudication remains outstanding for excerpt-triage rows and literal full-text inspection remains outstanding for compressed rows. No population accuracy, causal CPT effect, baseline improvement, or human-approved result is claimed.

Artifact status: finalized for the all-200 triage scope stated above; not a completed all-200 full semantic review. `qualitative_labels` is the structured annotation field. The optional queue-builder `labels` list is absent and may be treated as empty.
