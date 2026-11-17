# Exactly what changed relative to the reviewed originals

Source: `sft-pilot160-v01/train.jsonl` (sha256 e8bd148d...), 160 rows, never edited. Originals are also copied verbatim to `data/source-originals.jsonl` with per-field sha256.

| Field | tr-tr | en-tr | tr-en | en-en |
|---|---|---|---|---|
| system | original TR prompt, unchanged | EN rendering of it (drops the word "Turkish") | original | EN rendering |
| user | original + instruction | agent EN translation + instruction | original + instruction | agent EN translation + instruction |
| assistant | original, unchanged | original TR, unchanged | agent EN translation | agent EN translation |
| worked_solution (30 rows) | original | original | agent EN translation | agent EN translation |

- Instruction (separate paragraph appended to the user turn; recorded in `language_instruction` incl. `variant`): tr input -> "Yanıtını Türkçe ver." / "Yanıtını İngilizce ver."; en input -> "Answer in Turkish." / "Answer in English.". Sent in BOTH arms (Arm A uses the tr-tr rows, which carry "Yanıtını Türkçe ver.").
- 12 groups need Turkish text preserved in EN output, so their EN-output rows use: `preserve_explain` (g004, g007, g012, g015, g019, g130): "Explain in English; preserve the requested Turkish text." / "İngilizce açıkla; istenen Türkçe metni olduğu gibi koru."; `preserve_answer` (g041, g051, g052, g055, g123, g135): "Answer in English; preserve the requested Turkish text." / "Yanıtını İngilizce ver; istenen Türkçe metni olduğu gibi koru.". 3 groups (g010 JSON, g044 name, g058 catalog name) have language-neutral answers and keep the standard instruction (`output_language_effect=neutral_content`). No group was excluded: all 160 remain in both arms.
- Trailing whitespace of each translated field is copied from the original. Numbers are localized (8.000 -> 8,000; 0,10 -> 0.10; %20 -> 20%); units, names, entities and structured keys kept.
- Not copied: `reviewed_target` (contains `<thinking>` review notation); only its hash is stored.
- Nothing in the eval was changed (`eval-v01` hashes verified identical).
