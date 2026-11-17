# CONTINUE-BILINGUAL-PILOT

## Latest authoritative state — 2026-11-18 owner-authorized repairs

Use `ACTIVE-REVISION.json`: `revisions/v01-corrections-02/` is active. All 24
main anomaly groups and six secondary cleanup groups were repaired. No groups
removed; 160 TR-only / 640 bilingual rows; 30 / 120 reasoning rows. Source
originals, earlier revisions, translations and frozen evaluation remain unchanged.
Argilla's 30 affected groups were updated with saved owner text/status preservation
and an immutable pre-update API backup. Repairs are agent-authored under owner
authorization, not invented individual owner approvals.

Exp-010/011 config paths/hashes now point to the corrected revision. Token budgets:
A 100 steps, checkpoints 60/100, 208665 supervised tokens; B 113 steps,
checkpoints 69/113, 209811 tokens (+0.55%). Both CPU label audits pass with zero
findings. Old plans/reports below are historical and do NOT override these values.

Commands: `python scripts/datasets/apply_lfm3_bilingual_repairs02.py` (idempotent
after completion); `python scripts/datasets/plan_lfm3_bilingual_repairs02.py`;
`python scripts/training/run_lfm3_bilingual_pilot.py --experiment
exp-010-tr-only-sft160 --mode audit` and similarly exp-011-bilingual-sft640.

No training/pod/commit/push was performed. Tomorrow: retain existing terms/source
decisions, implement the currently preparation-only GPU training path, run real
native-template/GPU label audit and smoke/tiny-overfit before training. Do not mark
unperformed GPU gates complete. Existing source-verification uncertainties remain
separate from the repaired concrete anomalies.

Task: prepare 640-row four-direction bilingual SFT pilot data + frozen eval + plans (no training, no pod,
no publish, no push, no commit). Work dir: `experiments/turkish-capability/lfm3-1.7b/bilingual-pilot-v01/`.

## Order of operations (do not reorder)
1. [x] Author + validate + FREEZE new eval (35 tasks x 4 = 140 prompts + symbolic controls) BEFORE translating training data
2. [ ] Translate 160 groups in chunks -> `translations/part-NNN.txt` (never regenerate a finished part)
3. [ ] Build dataset (`scripts/datasets/build_lfm3_bilingual_pilot.py`), validate, token stats, leakage, reports
4. [ ] Experiment plans A (TR-only) and B (bilingual), stratified sample, unresolved decisions

## Status log (append below; newest last)
- 2026-11-17: read AGENTS.md, dataset/reproducibility guides, CROSSLINGUAL-DIAGNOSIS, exp-007 config, train.jsonl schema.
  Local tokenizer: `base-sft160-runtime-local/tokenizer/` (tokenizers lib only; no jinja2). Render verified via label-audit.json.
- DONE step 1: eval frozen (35 tasks, 140 prompts, 8 symbolic). `python scripts/datasets/prepare_lfm3_bilingual_pilot_eval.py` must say frozen
  (byte-identical). Leakage precheck: `eval-v01/leakage-precheck-vs-train160-and-packets.json` (0 exact; 40 flagged = template/boilerplate and coincidental small numbers).
  Shared helpers: `scripts/datasets/bilingual_pilot_common.py` (SYSTEM_EN, INSTRUCTION wording). Leakage tool: `scripts/datasets/check_bilingual_pilot_leakage.py`.
- Translation file format (`translations/part-NNN.txt`): `=== gNNN` / `@@SOURCE_ID <orig id>` / `@@USER` / `@@ASSISTANT` / `@@REASONING` (only if the original has worked_solution) / `@@FLAGS` (`severity | type | note` lines).
  gNNN = 1-based row order in `sft-pilot160-v01/train.jsonl`. EN text excludes the language instruction (added by builder). Trailing whitespace is copied from the original by the builder.
  Dump for reading originals: regenerate with the python snippet in builder (`--dump`) if scratchpad is gone.
- Translation policy: numbers localized (decimal comma->point, 1.200->1,200, %20->20%); TL kept; Turkish quoted material kept verbatim for Turkish-language tasks (spelling/morphology/ki); structured keys kept; JSON-only outputs identical across output languages (flag language_neutral_output).
- Translated parts: part-001..part-008 = ALL 160 groups DONE, parse-verified (ids/reasoning presence). Do NOT retranslate.
  Next: step 3 = write builder `scripts/datasets/build_lfm3_bilingual_pilot.py` (data/source-originals.jsonl, data/train.jsonl 640 rows, manifest), then validator + leakage + token stats + reports + plans + sample + decisions.
- 2026-11-18: builder done (`data/train.jsonl` 640 rows; `data/source-originals.jsonl`; `data/train-arm-a-tr-only.jsonl`; `build-manifest.json`), validator passes
  (`python scripts/datasets/validate_lfm3_bilingual_pilot.py`; reports in `validation/`; hand-reviewed exceptions in `validation/reviewed-exceptions.json`).
  Leakage vs all packets: `validation/leakage-report-train-vs-all-packets.json` (0 exact; flags are chance matches/topical, review pending write-up in leakage-review.json).
  Token plan: `plan/token-budget-and-order.json` (A 100 steps/230,440 sup. tokens; B 112 steps/229,643, ckpts 69/112).
  Remaining: leakage-review.json, translation issue reports, stratified sample, EXPERIMENT-PLAN + exp-010/011 folders, unresolved decisions, release-manifest, README.
- 2026-11-18: ALL DELIVERABLES WRITTEN (README, EXPERIMENT-PLAN, UNRESOLVED-DECISIONS, reports, sample, exp-010/011, release-manifest). Only owner decisions remain. No commit/push done.
- 2026-11-18 (round 2): terms checked (Consumer Terms s.3 item 2, eff. 2025-10-08; account Free/Pro/Max/Ultra) -> translations RESTRICTED (`TERMS-RESTRICTION.md`, row field use_restriction, `plan/gates.json` all false).
  Language-bound rows resolved by instruction variants (12 preserve groups, 3 neutral); no group excluded; dataset rebuilt (train.jsonl sha ad04a971...), eval hashes unchanged.
  Per-flag leakage audit done (`validation/LEAKAGE-FLAG-AUDIT.md`); medium flags sheet (`reports/MEDIUM-FLAGS-FOR-OWNER.md`); runner/audit (`scripts/training/run_lfm3_bilingual_pilot.py --mode audit`, outputs `plan/audit-*.json`); token plan unchanged (A 100 steps/230,440; B 112/229,643).
  Re-run order: prepare_..._eval, build, validate, plan, prepare_lfm3_bilingual_experiments, report, report_..._medium_flags, audit_..._leakage_flags (needs leakage screen first), finalize.
  Next: owner answers UNRESOLVED-DECISIONS; nothing committed/pushed/published.
- 2026-11-18 (round 3): owner accepted provider-terms risk for private research (gates.json `provider_terms_owner_risk_acceptance`); terms stay UNRESOLVED/not cleared. Other gates still false: source eligibility, owner decisions on flags/masking, GPU audit/smoke. No training started.
- 2026-11-18 (round 4): terms issue recorded as resolved by owner decision (risk accepted); empty-think masking decision closed: keep parity, no masking (blank thinking stays blank; reasoning only translated, never invented).
- 2026-11-18 (round 5): terms decision kept; reasoning treatment = exp-007 parity (masking audit confirms only context masked). New: reports/CORRECTION-REPORT.md (9 fix/6 retain, none applied), SOURCE-ELIGIBILITY.md, runner audit masking_policy. Gates still false: source eligibility, owner decisions (corrections/source), GPU label audit, smoke, tiny-overfit. If corrections approved: edit data/source-originals via a correction record, update translations/part-*.txt entries, rebuild, validate, re-plan, regenerate configs.
