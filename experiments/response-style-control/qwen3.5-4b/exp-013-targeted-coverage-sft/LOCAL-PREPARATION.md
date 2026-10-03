# Local preparation verification — 2026-10-03

No training, inference, GPU rental or W&B run performed in this phase.

Active source/draft: candidate_specs.py, data-draft-v2 and
training-preflight-draft-v2. v1 source/data/preflight/queue preserved as
superseded authoring evidence; DO NOT review/export the old queue.
Authoring revision: clarify doctoral-program wording, without changing target.

Actual checks:

- Ten unittest tests passed with CPU environment
  C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe.
- Original exp009 reviewed-v2 train/validation byte hashes verified unchanged.
- Both draft artifact manifests and preserved v1 source digest verified.
- No detected exact/near overlap against original80/20,348 benchmark inventory,
  3500 historical training inventory and previous24 B candidates.
-100 tokenized rows, zero truncation; every68 retained train representation
  and every20 validation representation equal A; masks and native EOS checked.
- All12 new rendered prompt/label examples saved in candidate-mask-inspection-v2.json.
- Draft targets5578 tokens/epoch, +3.60% vs A. Shared C/D dataset;
  actual approved-token totals will be recomputed after human edits.
- Active UI page returned HTTP200. API re-read12 exact candidate targets;
  zero review responses at verification time.
- Live exporter refused unreviewed tc-001 as expected. No approved dataset
  or C/D config-reviewed-v1 exists; deliberately blocked source configs remain.

Active candidate file SHA256:
`0b4612716f566d9f3bd03c7e65f61678d28f629f50a9bb48d5e1305c4e0bdc0a`.

Argilla active dataset c0dc183f-e552-4a7d-9267-08211b88df94;
name exp-013-014-targeted-candidates-12-v2; workspace sft-review.

Preparation bug and fix: older shared helpers prepend sys.path directories,
causing export_review/import_review to resolve an older namesake. Restore the
current experiment first after loading shared helpers. Added test of both
module file paths; no fabricated Argilla review or GPU gate was produced.

Pending: user review12, explicit reference-version decision for disputed me-089
if changed, reviewed freeze/preflight, committed run sources, GPU access/checks,
independent C/D SFT and inference, verified logs/config/checkpoint recovery and
human comparison. Earlier A/B smoke/overfit waiver does not apply automatically.
