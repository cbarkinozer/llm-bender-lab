# llm-bender-lab — draft core acceptance map

The whole small lab workflow, not implementation of every SFT/RL/CPT method. Existing adapter tests only partially support this proposed contract; additional core tests will be needed.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Reject malformed conversations and held-out overlap before training. | Missing message roles/content or exact shared train/eval IDs/text fail validation; fake trainer has zero calls. | unit/integration |
| R2 | Resolve and preserve effective config and identities. | CLI override of configured learning rate appears in effective manifest while source config remains unchanged; seed/model/data/code IDs retained. | unit |
| R3 | Keep runs isolated and preserve previous artifacts. | Two run IDs write distinct directories; attempting to reuse an existing immutable run fails without changing its original bytes. | integration |
| R4 | Coordinate a smoke run and adapter artifact. | Fake backend receives approved inputs/settings; successful artifact and completion status agree; missing artifact cannot be labeled successful. | integration |
| R5 | Keep evidence when a run fails. | Injected trainer error yields failed status and retained logs; no selected-success checkpoint or completed metric is fabricated. | integration |
| R6 | Compare matched baseline/candidate and omit credentials. | Mismatched thinking/budgets raise a comparability warning/error under the agreed policy; 2/4 to 3/4 is a +25 percentage-point change; absent metrics stay unavailable; fixture secrets absent from manifest. | unit/integration |

## Public test boundary (proposal)

Experiment CLI plus public config/data/manifest records; trainer and evaluator are injected boundaries, not mocked domain calculations.

## Decisions still needing agreement

- Confirm the minimum backend and data schema for this standalone MVP.
- Decide whether comparison mismatch blocks the command or produces an explicitly non-comparable report.

## Manual / live checks

- Real adapter loading and one GPU/CPU backend smoke require separate hardware validation.
- Inspect the summary for clear scope, limits and artifact recovery instructions.

## Candidate existing evidence — not automatically selected

- `scripts/evaluation/test_paper_pipeline_adapter.py`
- `experiments/response-style-control/qwen3.5-4b/exp-009-minimal-edit/test_training_preparation.py`
- `experiments/response-style-control/qwen3.5-4b/exp-015-target-quality-sft/test_execution.py`

Source revision: `fa79eb8eed190a67c28cdda4ca18c0419d842ca8`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
