# Bilingual pilot v01 (prepared; nothing trained, published, committed or pushed)

**Active data: `revisions/v01-corrections-02/` (see `ACTIVE-REVISION.json`).**
Owner-authorized repairs to 30 groups are applied in both languages and Argilla.
Original `data/`, translations and first correction revision remain preserved.
Use the active revision for training, not the original 640-row draft. Exp-010/011
configs now reference the corrected hashes and recomputed token plan; both CPU
label audits pass. See `reports/REPAIRS-APPLIED-20261118.md` for details.

160 reviewed Turkish task groups x 4 directions (tr-tr, en-tr, tr-en, en-en) = 640 rows, plus a fresh frozen eval (35 tasks x 4 = 140 prompts + 8 symbolic controls).

| Path | Content |
|---|---|
| `data/train.jsonl` | 640 rows (messages, `worked_solution` reasoning, ids, provenance) |
| `data/source-originals.jsonl` | untouched reviewed originals + hashes |
| `data/train-arm-a-tr-only.jsonl` | the 160 tr-tr rows |
| `translations/part-001..008.txt` | the agent translations (source of truth for EN text) |
| `eval-v01/` | frozen eval; prompts and references in separate files |
| `validation/`, `reports/`, `inspection/` | validation, leakage, token stats, issue report, owner sample |
| `plan/`, `EXPERIMENT-PLAN.md`, `../exp-010-*`, `../exp-011-*` | token-matched plans/configs (not run) |
| `UNRESOLVED-DECISIONS.md`, `build-manifest.json`, `release-manifest.json` | decisions, hashes |

Reproduce: `python scripts/datasets/{prepare_lfm3_bilingual_pilot_eval,build_lfm3_bilingual_pilot,validate_lfm3_bilingual_pilot,plan_lfm3_bilingual_pilot,report_lfm3_bilingual_pilot,finalize_lfm3_bilingual_pilot}.py` (frozen files must match byte for byte).
Limits: translations are agent-authored, not owner-reviewed, and RESTRICTED pending the provider-terms question (`TERMS-RESTRICTION.md`). Read `DATA-CHANGES.md` for exactly what differs from the reviewed originals and `UNRESOLVED-DECISIONS.md` for the open list.
