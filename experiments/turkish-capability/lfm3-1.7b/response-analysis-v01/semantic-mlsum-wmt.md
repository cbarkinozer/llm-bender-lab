# MLSUM and WMT: bounded semantic triage

Evaluation only. Reviewer: **codex-agent**. **No human review or approval**: human_reviewed=false and human_approved=false on every row. No training examples or corrected target answers were created.

## Inspection scope and method

All 100 WMT and all 100 MLSUM responses received individual semantic triage and row-specific evidence. This is **not an exhaustive full-text semantic audit or a semantic correctness score**. Most long responses were inspected at the opening 500 Unicode code points and final 150. Unread middles can contain additional supported content or errors. Larger excerpts were sometimes displayed initially; recorded ranges conservatively count only the stated spans. All WMT English sources and all references were read. MLSUM source openings up to 700 code points were read; complete source articles were read for selected follow-ups.

Responses of at most 500 characters were displayed in full. Additional full response/source checks covered WMT-00172, -00700, -00427, -00769, -00348 and MLSUM-03264, -02314. Full response review does not establish independently verified factual truth. The JSONL records exact conservative inspected ranges, full lengths and unread-middle status per row.

Python assisted extraction, exact-text display, hashing, counts and metadata validation. The agent authored semantic categories and evidence from displayed texts; these are **not reference-overlap, regex or automatic correctness judgments**. Auxiliary dimension labels are coarse agent observations consolidated from these notes. No independent second judge, human approval, external fact checking or inter-rater agreement was obtained. Review was not blinded to model identity.

Task instructions were established from the protocol and source structure; not every serialized chat prompt or raw_output was semantically inspected. Strict UTF-8 decoding and machine integrity checks covered all complete stored prompts/predictions.

## Findings

WMT commonly replaces translation with Turkish essays, advice, invented news, vocabulary lessons or lists. Other rows retain a source-related opening and then add unsupported continuation. Short answers also contain clear semantic errors, so the problem is not solely excessive length or formatting.

- **wmt_en_tr-00449:** second-year becomes first-year; OUCA membership and self-introduction change. Full short response inspected.
- **wmt_en_tr-00220:** Islamist influence and Hamas's powerful/rich friends are substantially conveyed, but parallel growth nuance weakens and reporting "söylüyor" is added. Partial translation, not wholesale substitution.
- **wmt_en_tr-00525, -00956, -00911:** broad meaning survives with awkward Turkish. -00956 echoes English before translating. These are candidate adequate translations under this triage, not certified perfect outputs.
- **wmt_en_tr-00769:** first sentence conveys MTV advancement, followed by unsupported history/programming elaboration. Full response inspected.
- **wmt_en_tr-00240:** "bigger than" becomes "same level." Full short response inspected.
- **wmt_en_tr-00555 and -00999:** English source repeated without Turkish translation.
- **wmt_en_tr-01000:** pregnancy/stabbing/car assault becomes a rape/death account with reversed roles; retaining names does not make it adequate.
- **wmt_en_tr-00700:** translated headline followed by invented Israel/Berlin history and repetition, despite recorded eos.

MLSUM is dominated by article replacement rather than grounded concise summarisation. Recurrent motifs include women's portals, dating monologues, sexual-anatomy prose, Istanbul municipal construction and invented human-rights-court boilerplate. These motifs do not prove a specific training source, memorisation or causal CPT degradation.

- **mlsum_tr-09652:** full short response is an unrelated New Year loop instead of Trabzonspor/Krasnodar coach comments.
- **mlsum_tr-03264:** full source/response reviewed. Collision, three deaths and hospital destinations are partly supported. Cameras, passenger actions and a driver quote are invented; the collision description introduces a car. Supported fragments coexist with material hallucination and summarisation failure.
- **mlsum_tr-02314:** full source/response reviewed. Source requires further research on pregnancy Pilates safety/effectiveness; response confidently asserts abdominal benefits and repeats them. Topic overlap hides epistemic drift.
- **mlsum_tr-08327:** excerpt retains location/initials/abuse allegation but adds contradictory age/date and grandmother-as-victim material. No full-text correctness claim.
- **mlsum_tr-03809:** funeral source becomes invented detention/investigation about the same named person. Entity overlap is misleading.

## Labels and stopping

Supported content, substitution, drift, repetition, formatting and stopping are separate fields. Dominant overall categories are descriptive failure types, not mutually exclusive capabilities or official scores. Substitution means inspected material supplies another task/article; it does not certify no relevant sentence exists in an unread middle. Topical substitution retains a topic/entity but invents the account. Partial/incorrect plus drift separates source-related content from unsupported continuation. Acceptable translation means broad gist with awkwardness under this rubric.

Formatting labels describe plain text, English-only echoes or expanded prose/lists/web wrappers; they are not formal parser verdicts. Wrapper presence alone does not establish semantic failure. Repetition includes repeated phrases and numerical/heading progression with changing numbers. Absence labels mean not established within inspected text.

Recorded eos does not establish clean stopping or correctness: eos rows can contain long invented or repetitive passages. exact_loop is an **external guard**, not voluntary termination. The inspected batched evaluator aborts unfinished requests when token windows repeat. length is generation-limit stopping; hit_max_new_tokens is retained separately. Counts reproduce existing metadata. No generation/scoring was rerun or changed. Manifest settings include temperature 0.1, repetition penalty 1.1, max_new_tokens 4096 and engine max_num_seqs 4. No paired baseline or causal training-regression claim is made.

## Input and benchmark integrity

Strict UTF-8 machine checks found **zero literal U+FFFD in every semantic_prompt and prediction across all 500 rows**, agreeing with parent verification. Garbled default-console output was a rendering issue, not evidence of replacement characters in source bytes. No input corruption was identified by that check. This does not establish perfect upstream encoding, extraction, source completeness or reference quality; raw-output decoding and token-level fidelity were not independently audited.

Editorial source/reference mismatches warrant benchmark review: MLSUM-02314's reference discusses personalised programmes and risks beyond its supplied short article; MLSUM-03028's reference describes a lottery caller/preparations while its article concerns a stolen ticket allegation/legal complaint. These are not evidence of byte corruption. Judgments prioritize supplied-source support rather than reference phrasing.

## Descriptive counts

Counts describe this fixed inspected cohort, not population estimates, official benchmark scores or a human-approved pass rate.


### wmt_en_tr

- rows: 100.
- labels: {"substitution": 52, "partial_plus_drift": 18, "incorrect_translation": 9, "partial_translation": 5, "incorrect_plus_drift": 11, "acceptable_translation": 3, "untranslated": 2}.
- scope: {"full_response_semantic_triage": 23, "excerpt_semantic_triage": 77}.
- stopping: {"eos": 53, "length": 46, "exact_loop": 1}.
- repetition_observed: 71.
- total_characters: 678011.
- inspected_characters: 58847.

### mlsum_tr

- rows: 100.
- labels: {"substitution": 89, "partial_plus_drift": 2, "topical_substitution": 8, "incorrect_plus_drift": 1}.
- scope: {"full_response_semantic_triage": 7, "excerpt_semantic_triage": 93}.
- stopping: {"exact_loop": 8, "length": 77, "eos": 15}.
- repetition_observed: 98.
- total_characters: 1081422.
- inspected_characters: 64894.

## Provenance

Source: experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl

SHA-256: 0abe42c892374d79a907554189345c8ba41848ea1c93c008e64e9c6dec0ab595

Protocol: continuation-official-general-500-v01; recovered 100M continuation merged checkpoint, not the unmodified starting model. Previously inspected comparison/development cohort, not pristine final holdout.

Read: root AGENTS.md; docs/evaluation-guide.md; exp-004 README/config; recovered cetvel README/manifest; guard implementation in scripts/evaluation/evaluate_lfm3_vllm_batched.py. Older README/config says inference pending/disabled; completed recovered manifest governs this analysis.

Historical files were read only; all files in the source directory were hash-checked unchanged across artifact creation. Existing sibling analyses were untouched. Added only semantic-mlsum-wmt.jsonl and semantic-mlsum-wmt.md. Keep evaluation-only annotations out of training pipelines.
