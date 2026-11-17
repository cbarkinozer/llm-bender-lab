# Applied bilingual repairs — 2026-11-18

Owner instruction: “düzelt bunları.” Active revision:
`revisions/v01-corrections-02/`, built from immutable `v01-corrections-01`.
All 24 main groups in FULL-QUICK-REVIEW-20261118.md and six secondary cleanup
groups were addressed: 30 groups, 79 edited language-specific text fields. Full
before/after text is in the revision's corrections.json. The six secondary groups
are g012, g034, g071, g106, g113 and g126. No source group was removed.

- Corrected logical validity, existential consequences, conditional assumptions,
  implication direction, listening versus hearing, confounding versus reverse
  causation, and unsupported conclusions.
- Clarified purchased-fuel budget, central fold lines, and “very satisfied”.
- Restored packing/refund conditions, three bullets, open-question translation,
  and started-versus-completed data collection.
- Removed fabricated milestones, technical specifications, operational promises,
  undefined financial formula and unsupported behavioral guarantees.
- g154 deliberately narrows the prompt from bibliographic citations to correctly
  named poems and uses two identifiable examples without invented page numbers.
- g012 retains suffix/conjunction spelling guidance while removing categorical
  comma rules; g034 explicitly applies the exercise's stipulated classification.
- Qualified scientific/technical generalizations, corrected the film title and
  emergency number, removed a fixed net/gross percentage and platform guarantees.

The 30 affected Argilla records were updated in the existing queue. Submitted and
draft statuses, notes and owner edits were preserved; no automatic owner approval
was inferred. A pre-update API snapshot is stored under the ignored
crosslingual-runtime-local/bilingual-review-backups directory. Roundtrip checks
verify displayed text and saved responses; untouched records remain identical.

Validation: 160 groups / 640 rows, no cross-direction mismatch, no blank answers,
no embedded model/reasoning tags, no truncation (maximum 1602 tokens). Reasoning
presence remains 30 original groups: 120 bilingual rows and 520 direct answers.
148 frozen evaluation prompts were exact-overlap checked; eval JSONL hashes remain
unchanged. This does not replace the existing broader near-duplicate review.

Configs for the unrun exp-010/011 now reference the new data and token plan.
A: 100 steps, checkpoints 60/100, 208665 supervised tokens.
B: 113 steps, checkpoints 69/113, 209811 supervised tokens (+0.55%). B's earlier
checkpoint is matched to A's actual step60 exposure; both CPU native-format label
audits pass. Earlier configs are preserved under the revision's previous-plans/.
Model parent, LR, LoRA settings, masking and frozen eval remain unchanged.

Primary sources consulted for targeted factual corrections (no claim of complete
domain verification):

- TCP SYN data: https://datatracker.ietf.org/doc/html/rfc9293 §§3.5, 3.10.7.3.
- Blockchain consensus example: https://bitcoin.org/bitcoin.pdf.
- Film title: IKSV festival catalogue search-index text,
  https://catalogues.iksv.org/film_katalog_2012_low_res.pdf (full PDF web retrieval
  exceeded tool size; indexed title supports the corrected name).
- Unified emergency service: https://www.ogm.gov.tr/ekoloji/duyurular/tek-numaramiz-1121.
- Ki spelling: https://tdk.gov.tr/icerik/yazim-kurallari/baglac-olan-kinin-yazilisi/.
- Constitution article 56: official Constitutional Court decision,
  https://normkararlarbilgibankasi.anayasa.gov.tr/ND/2024/175?NormunTurler_id=14&page=1.
- Poem identification: https://www.yapikrediyayinlari.com.tr/kuvayi-milliye-abidin-dinonun-desenleriyle.aspx
  and https://turkce.eba.gov.tr/iceriklistesi/n%C3%A2zim-hikmet-534.

Unverified legal citations and other domain claims elsewhere are not certified by
this pass. Existing owner terms decisions and source/GPU gates were not changed.
No training, pod launch, publication, commit or push occurred.
