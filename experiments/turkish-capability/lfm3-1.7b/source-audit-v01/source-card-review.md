# Pinned source provenance and dataset-card review v01

Audit date: 2026-11-14. Scope: documentary source eligibility for the reusable Turkish SFT core and later LFM3 selection. This is an engineering intake assessment, not legal advice or a determination of infringement. No source is cleared for training or republication by this review.

## Scope, method and decision rules

Read `AGENTS.md`, `docs/dataset-guide.md` (especially sections 10–19, 24–27, 45–49 and acceptance rules), experiment/reproducibility guidance, the LFM3 study README, `sft-expansion-v01/PLAN.md`, and `docs/turkish-sft-corpus-design-v01.md`. The latter supersedes the old narrow expansion allocation: reasoning remains a planned capability, with worked solutions separate from final answers.

Used Python `requests` for anonymous HTTPS GETs of each exact revision's Hub metadata (`/api/datasets/{repo}/revision/{sha}`), then every listed README, LICENSE, source-origins and release-manifest document. Four metadata requests and seven document requests completed successfully; documents were bounded to 300 KB each. No corpus files, viewer samples, teacher endpoints, training or paid services were requested. Documents were retained only in an OS temporary directory outside the repository. The tracked deliverable contains analysis, links and document digests, not full cards or corpora. Parent-owned raw downloads/static inventory were not inspected or modified.

The directory already contained parent-owned `raw-local` work when inspected; this review adds only this new report. Other dirty/untracked repository work was left alone. No training config was created: this is a source audit, not a training experiment.

These labels are this audit's engineering conventions, not labels mandated by the dataset guide. The earlier whole-source quarantine designation was a conservative interpretation and is superseded here. The user currently authorizes audit and candidate comparison, not training or release.

- **Eligible for a specified downstream use:** sufficient relevant evidence supports that use, subject to content/split checks. Eligibility must name the use; audit, training and redistribution are distinct decisions.
- **Provisional audit/selection; unresolved release eligibility:** continue read-only content comparison, sampling and candidate selection while recording provenance and permission gaps. Candidate selection is not acceptance into a released or training-ready snapshot.
- **Row/family quarantine or definite rejection:** record the specific reason and evidence, such as confirmed benchmark derivation, an applicable prohibited use, or a verified defective target. Unresolved provenance can justify a temporary hold for a downstream use, but is not proof of prohibited use or a definite content rejection.

MIT and Apache declarations are meaningful evidence of the publisher's offered licensing terms; Occam also supplies the Apache license text. They do not independently settle authority over every upstream contribution or applicable provider contract. No prohibited use was established for any of these four sources by this bounded review. Missing evidence remains missing evidence, not a finding of infringement or a conclusion that the licenses are meaningless. Current generic provider terms would not necessarily reconstruct historical conditions; follow-up should focus on evidence material to the intended use.

Rights eligibility and reproducibility are separate questions. Missing sampling seeds, temperatures, full prompt templates or an exact legacy model revision can limit reproduction and quality attribution without independently blocking rights eligibility. Provider/model identity, relevant generation period and applicable permission evidence matter where needed to determine output-use restrictions; a sufficiently supported permission chain need not reconstruct every legacy sampling parameter.

## Disposition

| Pinned source | License evidence | Audit/selection disposition | Unresolved downstream eligibility |
| --- | --- | --- | --- |
| Occam | Apache-2.0; separate license supplied | **Provisional audit/selection** | Historical assistant/provider provenance incomplete; manifest does not attest rights review |
| Turkish-SFT-Dataset-v1.0 | MIT in README | **Provisional audit/selection** | Multi-provider output-use conditions and unidentified crawl/RAG sources need clarification |
| Turkce-Atlas-Instruct | MIT metadata, expressly qualified | **Provisional audit/selection** | Source/generation history absent; card does not establish upstream rights |
| Turkish-CoT-Instruct-Dataset | Apache-2.0 in README | **Provisional audit/selection** | Question lineage and teacher output/reasoning conditions need clarification |

All four remain candidates for the authorized content comparison. None is established training/release eligible by this documentary review alone; none is definitely rejected as a whole source. Occam has the strongest surviving lineage and a concrete follow-up path. No row-level prohibited use, benchmark contamination or definite rejection was established here. Card-reported defects remain candidates for verification, not adjudicated row decisions. No accepted row counts follow from this card review.

## Immutable evidence register

All document links below use the requested commit, never `main`. Digests cover downloaded response bytes before decoding/newline normalization. File presence/absence was checked against the exact-revision metadata listing, not guessed from conventional URLs. No separate LICENSE or source-origins file is listed for SFT, Atlas or CoT; that absence does not invalidate the README declaration, but leaves less documentary evidence.

### occam: `cbarkinozer/Occam-Turkish-Response-SFT`

Revision: `947850d484c71f657dbec2bb7e3d356cb5fb23e3`. [Pinned tree](https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT/tree/947850d484c71f657dbec2bb7e3d356cb5fb23e3); [revision metadata](https://huggingface.co/api/datasets/cbarkinozer/Occam-Turkish-Response-SFT/revision/947850d484c71f657dbec2bb7e3d356cb5fb23e3).

| Retrieved document | Bytes | SHA-256 |
| --- | ---: | --- |
| [LICENSE](https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT/resolve/947850d484c71f657dbec2bb7e3d356cb5fb23e3/LICENSE) | 11357 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| [README.md](https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT/resolve/947850d484c71f657dbec2bb7e3d356cb5fb23e3/README.md) | 5083 | `fcf88ff787bdf978dbab24d9721ff585159c24db7a4b97a5a81d70324ba9371e` |
| [release-manifest.json](https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT/resolve/947850d484c71f657dbec2bb7e3d356cb5fb23e3/release-manifest.json) | 1716 | `57c8c2da14e2ee82fcdee6ac3a68fae57e02416fc54972d48ea6322903f254d3` |
| [source-origins.json](https://huggingface.co/datasets/cbarkinozer/Occam-Turkish-Response-SFT/resolve/947850d484c71f657dbec2bb7e3d356cb5fb23e3/source-origins.json) | 1681 | `44db64260f89957f5bd8962b483d3c9bc972814317a05b2712f5f9019540fd03` |

### sft: `AlicanKiraz0/Turkish-SFT-Dataset-v1.0`

Revision: `5a5a852ab9067866d72ed92381205518feaae5fb`. [Pinned tree](https://huggingface.co/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0/tree/5a5a852ab9067866d72ed92381205518feaae5fb); [revision metadata](https://huggingface.co/api/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0/revision/5a5a852ab9067866d72ed92381205518feaae5fb).

| Retrieved document | Bytes | SHA-256 |
| --- | ---: | --- |
| [README.md](https://huggingface.co/datasets/AlicanKiraz0/Turkish-SFT-Dataset-v1.0/resolve/5a5a852ab9067866d72ed92381205518feaae5fb/README.md) | 6428 | `edfce890643f0f086177c9d07d0fa0c3950e504dd8ceb896dcc5e9a46baffd35` |

### atlas: `AlicanKiraz0/Turkce-Atlas-Instruct`

Revision: `c387738c5deacbb35667ab4057930adc34e647e8`. [Pinned tree](https://huggingface.co/datasets/AlicanKiraz0/Turkce-Atlas-Instruct/tree/c387738c5deacbb35667ab4057930adc34e647e8); [revision metadata](https://huggingface.co/api/datasets/AlicanKiraz0/Turkce-Atlas-Instruct/revision/c387738c5deacbb35667ab4057930adc34e647e8).

| Retrieved document | Bytes | SHA-256 |
| --- | ---: | --- |
| [README.md](https://huggingface.co/datasets/AlicanKiraz0/Turkce-Atlas-Instruct/resolve/c387738c5deacbb35667ab4057930adc34e647e8/README.md) | 12967 | `dab6a0900657e137182fe057fed587378bf892b1188e57bdd53e53f32d14f369` |

### cot: `AlicanKiraz0/Turkish-CoT-Instruct-Dataset`

Revision: `3473e6c6350564d5a7000faf3ff140e9c4b9d1f2`. [Pinned tree](https://huggingface.co/datasets/AlicanKiraz0/Turkish-CoT-Instruct-Dataset/tree/3473e6c6350564d5a7000faf3ff140e9c4b9d1f2); [revision metadata](https://huggingface.co/api/datasets/AlicanKiraz0/Turkish-CoT-Instruct-Dataset/revision/3473e6c6350564d5a7000faf3ff140e9c4b9d1f2).

| Retrieved document | Bytes | SHA-256 |
| --- | ---: | --- |
| [README.md](https://huggingface.co/datasets/AlicanKiraz0/Turkish-CoT-Instruct-Dataset/resolve/3473e6c6350564d5a7000faf3ff140e9c4b9d1f2/README.md) | 5161 | `88338c5f58e818b3a647f6ca8d477416fc0bb597662a4e62fcc13f7575f12558` |

## Occam — provisional audit/selection;  strongest surviving lineage, unresolved historical rights

Evidence: pinned README sections Creation and provenance, Split and leakage limitations, Limitations/privacy/rights; source-origins and release-manifest in the register above.

**Actual claims.** A human-reviewed synthetic/AI-assisted response-style corpus, 104 train and 20 development rows, initially selected from historical inventories with later project-agent scenarios and target repairs. Original Qwen3.5-4B answers informed edits; human review/rewrites sometimes used a personal AI assistant. `source-origins.json` identifies `unsloth/Qwen3.5-4B` for saved original base answers, explicitly not all authors. It reports 58 historical-verbatim training origins and 17 validation origins, plus other historical/agent-authored groups. These are origin labels, not evidence that historical text came from an external copyrighted corpus.

**Rights and reproducibility evidence.** The Apache license text is present and its digest matches the manifest. The manifest and all three other fetched documents (README, LICENSE, source-origins) were inspected; README/LICENSE/source-origins byte digests match their manifest entries. The manifest records a builder commit, script hashes and train/dev file hashes, but this review did not download data or verify those data hashes. Its status is private-upload draft, rights review is not attested, and private visibility is required. Those are release-document statements, not a verified claim about today's Hub access setting. Anonymous retrieval worked; accessibility does not change the stated review status.

**Missing evidence.** The personal-assistant provider/model, generation dates, exact applicable terms/contract and allowed downstream training/publication are explicitly incomplete. Original base-answer model revision and its applicable model/output conditions are not established merely by naming Qwen. Historical prompt/context origins need row-level traceability to surviving original inventories and permission evidence where external material was involved. Human editing and an owner-selected license do not repair an unestablished upstream permission chain. Removing private review metadata is not an exhaustive privacy audit.

**Leakage.** The card reports no identified exact/near/scenario item leakage and excludes 12 project control items and external CETVEL inputs/references. It explicitly does not prove zero semantic overlap. Its 20 validation prompts were repeatedly used for selection and are development data; disputed reference `me-089` remains preserved. A code-repository semantic review is mentioned but no immutable locator is supplied in the card. This audit did not follow an inferred mutable repository path. Obtain its exact commit/path and evidence before relying on the claim. Never convert this dev set into a fresh final test.

**Quality and role.** Human-reviewed is not a correctness certificate: the card admits errors, uneven coverage and historical reproducibility limits. Useful concise and explanatory behaviors coexist; do not turn this into a universal brevity objective. Final-assistant-only supervision is explicit; earlier assistant messages are context. Small curated coverage cannot establish broad Turkish competence or resistance to forgetting.

**Follow-up for downstream eligibility and quality.** Obtain the owner's historical prompt/target lineage and applicable assistant/base-model permission records, resolve privacy/third-party content at row level, and record any subset exclusions in a new manifest. Preserve the original revision and dev status. Then independently review retained targets and repeat source-family/cross-language leakage checks. Record unresolved lineage at row/family level and hold the affected subset from downstream acceptance if material evidence remains insufficient; continue its audit without declaring it prohibited or defective.

## Turkish SFT — provisional audit/selection;  teachers disclosed, crawl lineage unresolved

Evidence: pinned README, especially production source/method, quality principles, limitations and license sections.

**Actual claims.** The repository named v1.0 contains a card headed v1.01; its citation points to a v1.01 dataset identifier. Use the requested repository/commit, not that alternate citation ID. The card claims about 5,500 rows, 3,000–4,500 tokens per row and 20M+ tokens across 12 capability families. Later it describes 3K–4.5K-token answers, so row versus answer length is ambiguous, and no tokenizer/measurement recipe establishes either. These are publisher claims, not inventory results.

It names approximate teacher shares: Grok 4 (25%), Claude Opus 4.1 (10%), Claude Sonnet 4.5 (20%), gpt-oss-120b reasoning-high (30%), and Kimi-K2-0905 non-reasoning through TogetherAPI (15%). It additionally says 30% was produced locally with gpt-oss-120b using RAG/distillation over roughly 100–120 GB of Turkish crawl material. The listed teacher shares already total 100%; the wording does not establish whether the local 30% overlaps the gpt-oss share. Do not add it to get 130% or assume a unique per-row assignment.

**Critical gaps.** No crawl URLs/domains, snapshot dates, source licenses, collection permissions, retained extracts, source IDs or retrieval-to-row mapping. Thus both prompts and answers may carry transformed third-party material without a documented permission chain. No teacher-per-row metadata, immutable teacher revisions, endpoint/account details, generation dates, prompts/settings beyond broad reasoning labels, or applicable provider output-use/competitive-training/publication terms. TogetherAPI is a serving route, not sufficient evidence of the underlying model and hosting conditions. Open-weight/local generation also does not clear crawl material. MIT is asserted in the card; no separate license/notice file is in the pinned listing. Third-party-rights caution in the card is not a rights clearance.

**Quality promises and limits.** Long outputs, high-reasoning generation and high-quality prompts are design choices, not factual verification. The card explicitly says there was no exhaustive manual audit, only spot checks and automatic format/validation checks; it does not supply sample size, rubric, error rates or validation receipts. Safety/refusal topic coverage does not prove calibrated refusal behavior. Tool awareness is not evidence of structurally valid tool-call records. The displayed schema has system/user/assistant strings, so multi-turn competency claims need actual content inspection. No targeted PII collection is weaker than no PII present.

**Leakage.** No documented benchmark exclusion list, canonical source matching, cross-lingual screening, grouped split method or contamination results. RAG over an unidentified crawl is a plausible route for benchmark problems, translations and solutions; this is a risk inference, not an observed overlap. A high-reasoning teacher can also reproduce benchmark material. Do not interpret silence as a no-leakage claim.

**Follow-up for downstream eligibility and quality.** Obtain crawl source manifest and permission chain plus row-level teacher/retrieval mappings and historical output-use evidence. Resolve title/citation and length/share ambiguities. Partition by canonical source/template families, check all benchmark derivatives, then verify correctness, refusal calibration, language and token exposure with the parent inventory. Keep unresolved source/teacher strata provisional for comparison; before downstream acceptance, resolve material permission gaps or document a scoped exclusion. Preserve the offered MIT terms and source credits.

## Türkçe Atlas — provisional audit/selection;  useful structural self-audit, absent generation history

Evidence: pinned README's structure, quality review and license sections. Its loading example pins `180fb437a6df27cc09505b72eec4bc536b6c113b`, which differs from this audit's requested revision; do not silently substitute it.

**Actual claims.** 336,146 train-only conversations with three messages, a shared 654-character system instruction, and no independent validation/test split. The card reports a full structural scan plus a systematic 60-row content sample, taking roughly every 5,600th row. Those reported observations are not this review's measurements and a systematic sample may miss periodic/template clusters.

**Missing provenance.** The card does not identify original datasets/documents, source licenses, generation provider/model/revision, authoring process, generation date or output-use terms. Synthetic-looking examples are not proof of synthetic generation or a particular teacher. No source manifest, teacher map, source-family IDs or builder revision is supplied. Its license section explicitly says MIT was retained from metadata, independent rights review was not performed, and underlying sources/relicensing are not established. No separate license or origins document is listed. This leaves downstream eligibility unresolved while audit and content comparison continue; it does not establish prohibited use.

**Quality findings already disclosed.** The card reports 1,001 excess repeated-user rows across 688 groups (maximum repetition 11), 136 excess repeated-answer rows, three answers consisting only of `S:`, and 25,120 rows sharing the same first instruction line (7.47%). Exact equality does not detect semantic/template duplication. That common instruction alone is not a reason to delete all those rows; inspect source families and content. A fixed system prompt may limit generalization to other system instructions. The example's friendly rewrite adds a call to action and changes water-consumption tracking to goal tracking despite requesting no meaning shift: a concrete card-example review concern, not a corpus-wide error-rate estimate.

The card reports PII-like regex matches: 405 email-like, 395 compact Turkish-mobile-like, 117 identity-number-like and 4,375 IPv4-like rows, with overlap/false positives and missed formats explicitly possible. These are not verified real identities and not a privacy clearance. The card itself calls for contextual review/masking. Character lengths must not be relabeled as LFM token lengths.

**Leakage.** No benchmark exclusion, cross-lingual canonical-source audit or independent evaluation guarantee is supplied. Low exact duplicate rates within train do not establish independence from evaluation or the other three candidate datasets. Creating a random holdout before recovering source/problem/template families risks leakage across variants.

**Follow-up for downstream eligibility and quality.** Recover source and generation lineage with license/output-use evidence and a row-to-family map. Resolve known truncated-answer candidates and contextual PII flags; check correctness and task fidelity in stratified samples. Cross-deduplicate candidate sources, group splits, and screen exact/near/translated benchmark material. Structural completeness alone cannot promote this source.

## Turkish CoT — provisional audit/selection;  explicit reasoning format, incomplete permission chain

Evidence: pinned README's two-stage generation description, schema, statistics and limitations.

**Actual claims.** 5,000 original deduplicated Turkish questions from a five-axis taxonomy; MiniMax-M3 generated reasoning and final answers. Release claims 4,868 rows, 14 domains, 13 reasoning types, four difficulties and eight formats, roughly 3,900 answer characters on average and roughly 99% Turkish thinking. The 132-row difference from generated questions is not explained by a documented rejection/filter log. Domain/difficulty counts describe intended taxonomy, not verified correctness or difficulty.

**Missing lineage and permissions.** The question generator/provider/model, prompt templates, source/seed material and exact dedup method are not documented. MiniMax-M3 is a teacher name, not an immutable model/endpoint/account/date record. No applicable generation-time contract, output-use permission, reasoning-trace publication/training conditions, source-level permissions or per-row provenance is provided. Do not infer that the teacher is DeepSeek: the card describes a DeepSeek-R1-style format, not that model as the generator. Apache-2.0 is asserted in the README without a separate license file at this revision; that does not resolve teacher/question-source conditions.

**Reasoning and quality limits.** Assistant messages combine `<think>` traces and detailed final answers; the presence of tags does not establish that traces are permitted for reuse, valid worked solutions, or compatible with LFM's native format. The card says 47 examples retain English thinking after excessive/runaway attempts to force Turkish. This qualifies the earlier all-Turkish description. Deduplicated questions can still share canonical problems and templates. No independent answer/step verification, pass rates, reviewer rubric, filter thresholds or reproducible language-ratio measurement are supplied. Long plausible reasoning can still be wrong.

**Leakage.** Original-question and dedup claims do not demonstrate independence from memorized problems, benchmark translations or generated derivatives. There is no named benchmark exclusion list, source-family matching or cross-language contamination evidence. Train is the only declared split; do not claim held-out generalization.

**Follow-up for downstream eligibility and quality.** Recover both question and answer generation records and applicable output/reasoning permissions. Obtain rejection history, dedup definitions and canonical family mappings. Independently verify steps and final answers. Store permitted worked solutions separately from final answers with shared family/split IDs, as the corpus design requires; choose native serialization later. Stripping think tags or retaining only final answers does not by itself resolve unresolved output rights.

## Handoff to parent audit and next evidence

This report deliberately makes no downloaded-row counts, token distributions, observed contamination rates or corpus-level correctness estimates. Card-reported values above must be checked by the parent's separate static inventory; disagreement should be recorded against the same revision rather than silently replacing claims.

For audit and candidate selection, record known lineage, offered licenses, gaps and content findings now. Before training or release acceptance, attach a per-source/per-stratum decision receipt with evidence material to that intended use: upstream identity/version where available, applicable license or permission evidence and attribution obligations, relevant provider/output-use conditions, transformations and row mappings, unresolved gaps, scoped exclusions and reviewer/date. Distinguish training, redistribution and commercial use. Historical endpoint/date details should be sought where needed to identify applicable terms, not imposed as an unconditional checklist when adequate permission evidence is otherwise available. Do not invent a provider for missing historical records. Newly recovered upstream links also need immutable snapshots/hashes; no upstream corpus or full card needs to enter tracked files.

Then combine documentary decisions with the parent's schema/quality inventory, owner content review and contamination checks. Check exact normalized overlap, near duplicates, canonical source/problem/template families and translated/paraphrased benchmark questions, answers, passages and solutions against the frozen evaluation manifest, including CETVEL. Check across all four candidate sources as well as within splits. All direct/reasoned/translated variants stay in one family/split. Occam's reused dev set and inspected CETVEL500 remain diagnostic/development material, not fresh final tests.

Prioritize Occam's recoverable internal records, SFT's identifiable teacher strata and crawl manifest, CoT's two-stage generation receipts, and Atlas's missing source history. This is a provenance follow-up priority, not a utility ranking. Continue the authorized content comparison across all four sources; mark selected candidates provisional until downstream eligibility is decided. If material permission evidence remains insufficient for an intended downstream use, document a scoped hold or exclusion rather than definite rejection by inference. Independent replacement material can be authored from abstract capability specifications under documented permitted methods; transformation does not resolve an established restriction. A new accepted snapshot must retain source credits, exclusions, review identity and split lineage. No paid requests, training, publication or outreach were performed by this audit.
