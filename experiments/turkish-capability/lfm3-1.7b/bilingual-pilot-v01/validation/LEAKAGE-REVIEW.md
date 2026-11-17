# Leakage review (2026-11-18)

**Superseded in detail by `LEAKAGE-FLAG-AUDIT.md` / `leakage-flag-audit.json`, which audits all 83 flags one by one (70 generic tokens/numbers, 6 shared numbers only, 4 topical (g111 vs TQuAD Müteferrika items), 3 template family; no shared underlying task, no quarantine). TurBLiMP1600 is UNCHECKED, not passed.**

Tool: `scripts/datasets/check_bilingual_pilot_leakage.py` (exact normalized overlap, 5-gram containment >= 0.15, non-trivial number/entity signatures; instruction text stripped; all four language variants of every group screened). Raw output: `leakage-report-train-vs-all-packets.json`; earlier eval-vs-train precheck: `../eval-v01/leakage-precheck-vs-train160-and-packets.json`.

Packets checked (887 protected items): old20 test, pilot80 test, reviewed-pilot test, dev20, crosslingual-holdout-v01 (12 + 3 symbolic), reasoning4 probe, CETVEL500 audit text (includes CETVEL100), and the new frozen eval (140 prompts, references, 8 symbolic). **Not checkable locally:** TurBLiMP1600 sentence pairs and any CETVEL items outside the 500-item audit file.

Result: **0 exact overlaps; 0 flags against the new eval or crosslingual-holdout-v01.** 83 group-level flags, all reviewed manually:

| Packet | Flags | Disposition |
|---|---|---|
| CETVEL500 audit | 65 | Chance coincidences of 2-digit numbers plus common Turkish words, except **topical** overlap: g111 (Ottoman printing press, 1727/1729, Müteferrika) and g105 (National Struggle dates) share historical facts with TQuAD/MLSUM items. No textual overlap (containment < 0.15). Inherited from frozen pilot160, not introduced here. Note if CETVEL TQuAD moves. |
| old20 / pilot80 / reviewed-pilot tests | 12 | Chance matches (g023, g151: generic words and small numbers). g115/g103 share the *Atlas template family* ("exactly 2 risks and 2 actions") with old20 `atlas:...:281286`; content differs. Inherited. |
| dev20 / reasoning4 | 6 | g075/g102 vs dev-13 (36 items, defective share) and g116 vs dev-14 (84 L ratio split): shared numbers only; different problems. |

Cross-lingual / canonical: eval tasks were authored from scratch before any translation (manifest `frozen_at_utc` 2026-11-17T20:44:26Z precedes every translation file); there are no shared source IDs, and no eval group shares a numeric+entity signature with a training group in either language. These screens give candidates for review, not proof of independence.
