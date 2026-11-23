# Turkish correspondence: 80-row review candidate

`mail-080.json` and `mail-080.jsonl` contain the same 80 objects. `mail-001` through `mail-005` are the unchanged accepted pilot; `additional-075.jsonl` contains only `mail-006` through `mail-080`. The original pilot files and README have not been rewritten. All new files use UTF-8 with LF line endings.

The owner accepted the pilot in the conversation and requested completion of the 80-row set. The new rows were written by an AI assistant, not by a human. They have been reread by the assistant, but the new rows have not received independent human review. Generation was direct in this conversation, without an external translation or generation API. Exact backend revision, sampling configuration and seed are not available. Approval to prepare a review candidate is not represented as a provider license grant or as approval to train or publish a final release.

Purpose: natural Turkish emails, letters and short formal or informal messages for a small language model. Schema: exactly `id`, `type`, `prompt`, `answer`. Ten categories contain eight examples each. The expansion follows the owner's requested scenario exclusions, diverse openings and register, no emojis or unnecessary English in answers, no tables or placeholders, ordinary answer lengths of 40–160 words, and exact stated limits. Quoted source texts in the seven new rewrite examples use typographic double quotation marks. The accepted pilot is preserved verbatim, including its original quotation style and closing wording.

Composition checks in `composition-check-080.json`: 38 of the 75 new prompts have 8–20 whitespace-delimited words and do not start with a self-introduction; these short prompts omit names and cities. Eleven answers exceed 100 words under both word-count methods, and 68 are below 60 under both. All ordinary answers satisfy 40–160 words under both methods. Stated sentence, word and bullet limits pass. IDs, prompts, answers and the first four words of answer openings are unique. Full opening sentences and scenarios were also reread for distinctness. Each prompt contains at most three sentences.

Repository validation:

```text
python scripts/datasets/validate_lfm3_sft_core_extra_rows.py datasets/turkish-mail-pilot-v01/mail-080.jsonl --report datasets/turkish-mail-pilot-v01/validation-080.json
```

The validator needs Zeyrek, wordfreq and the local protected evaluation sources. During this review, missing analyzer dependencies were installed only into the ignored `.cache/mail-review-deps` directory and loaded with `PYTHONPATH`; the existing validator was not modified. Its raw report is retained. `validation-review-080.json` records the corresponding content hashes and the manual resolution of its one known tokenizer warning: `19.00'daki` in accepted pilot row `mail-005` produces the fragment `daki`, not an invented Turkish word. The validator reports no other row issues, duplicate prompts or protected-set lexical overlaps.

The protected-set audit covers the sets available to the existing repository validator, including the 40 writing prompts. It is a lexical screen, not proof of complete semantic or cross-language separation. No evaluation text was used as a generation seed. No training pack, experiment configuration, Atlas target or stored reasoning was changed. These files are review candidates; no commit, push or training run was performed.
