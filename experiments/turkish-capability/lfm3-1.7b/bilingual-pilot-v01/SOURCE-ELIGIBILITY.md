# Source-data eligibility (read from existing records, 2026-11-18)

Records inspected: `source-audit-v01/source-card-review.md` + `download-manifest.json` (audit 2026-11-14, pinned revisions, README/LICENSE digests), `docs/turkish-sft-corpus-design-v01.md` (owner clarification on Occam), `sft-pilot160-v01/manifest.json` (per-row `source` blocks), plus a regex scan of our 160 rows. Missing paperwork below is **missing evidence, not a finding that use is prohibited**; the earlier audit itself found "no prohibited use established" for any source and no source definitely rejected.

| Source (rows in our 160) | Licence evidence | Missing evidence (specific) | Explicit restriction found |
|---|---|---|---|
| **Occam** `cbarkinozer/Occam-Turkish-Response-SFT`@947850d4 (40) | Apache-2.0 declared; LICENSE file present, digest matches manifest | Provider/model, dates and terms of the "personal AI assistant" used in human edits; model revision and output conditions for the Qwen3.5-4B base answers (`unsloth/Qwen3.5-4B`); row-level lineage of 58 "historical-verbatim" origins; release manifest says rights review "not attested" (private-upload draft). Owner clarification 2026-11-14: Occam is used only from the published repo, historical provenance is a limitation of that release | none |
| **Turkish-SFT** `AlicanKiraz0/Turkish-SFT-Dataset-v1.0`@5a5a852a (40) | MIT in README; no separate LICENSE | Crawl (100-120 GB) URLs/licences/permissions; per-row teacher; teacher output-use terms. Disclosed teachers include Grok 4, Claude Opus 4.1 / Sonnet 4.5, gpt-oss-120b, Kimi-K2 (via TogetherAPI): their terms may restrict training uses by whoever generated the data (the same Anthropic clause we checked); applicability to downstream users is unknown. Card has no leakage or audit evidence | none established; teacher-provider terms unresolved |
| **Atlas** `AlicanKiraz0/Turkce-Atlas-Instruct`@c387738c (40) | MIT "retained from metadata"; card says independent rights review not performed | Origin documents, generator/provider/model, dates, output-use terms; source manifest | none; card discloses PII-like regex hits (our 160: no emails/phones/ID numbers; only two IPv4 strings that are example data, 10.0.0.50 and 198.51.100.1) |
| **CoT** `AlicanKiraz0/Turkish-CoT-Instruct-Dataset`@3473e6c6 (40) | Apache-2.0 in README; no separate LICENSE | Question generator/seed material; MiniMax-M3 endpoint/date/terms; permission to reuse reasoning traces; 132 undocumented rejected rows | none established |

Scope notes: all 160 rows were individually reviewed/edited by the owner (`review.decision` / submitted text) and exp-007/009 already trained on them; the review is content quality, not a rights chain. Attribution: keep `original_source` blocks (repo, revision, line) in every row and credit the four repos in any dataset card; do not relicense wholesale.

## What would close each gap
Occam: ask the repo owner (you) for the assistant provider/model note; Turkish-SFT/Atlas/CoT: contact the publisher for generation history, or document a scoped exclusion of that source's 40 groups from both arms (coverage loss 25% per source). Alternatively record an owner decision accepting the documented gaps for private research (as done for the translation terms).

## Gate status
`source_eligibility_cleared` stays **false** until you record a decision. I have not set it. Suggested wording if you accept: "Owner accepts documented provenance gaps for private research use of the pinned public sources; no publication until upstream permissions are clarified."
