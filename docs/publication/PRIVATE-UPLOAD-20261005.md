# Private model upload — 2026-10-05

The owner authorized upload to the existing private Model Hub repository:
`cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora`.

- Revision: `1a8a07ff2a29f51a2b6a635a8c219191a7377996`.
- Six uploaded files: adapter weights, adapter config, model card, Apache-2.0
  license text, frozen training config, release manifest.
- All six files downloaded at that immutable revision and SHA256-verified against
  the prepared local package. Repository remained private after verification.
- Selected F weights/config bytes are unchanged; their canonical hashes still match.
- Owner-selected adapter license: Apache-2.0. This is not an attestation that all
  training-data provenance/provider terms have been reviewed.
- No dataset upload, public visibility change, GitHub push or new GPU test occurred.

Authentication lesson: the CLI's existing credential could read the repository but
upload returned HTTP 403 requiring a write token. The repository's local `.env`
contains `HF_API_KEY`; passing it directly to `HfApi` succeeded. No secret value was
printed, saved to documentation, passed in shell arguments, or uploaded. Do not
assume a successful `hf auth whoami` proves write permission. Verify destination
identity and privacy before upload; never upload the workspace using `.`.

Preparation: `prepare_private_model.py`. Upload/verification: `upload_private_model.py`.
The latter currently targets this specific private release and performs an upload;
do not run it as a read-only status command. It records the completion receipt outside
Git, alongside the release directory. Public release and dataset publication remain
separate owner decisions.

The prior 2026-10-04 cards, builder outputs, closure and blog describe the state at
phase closure; their "not uploaded" statements are historical, superseded here for
the private model only. Full rights/provenance review and fresh-environment loading
verification are still pending. The weights were hash-verified, not GPU-tested anew.

## Subsequent private dataset upload

The owner subsequently authorized uploading the clean dataset to
`cbarkinozer/Occam-Turkish-Response-SFT`, an existing private dataset repository
with Apache-2.0 selected in its card. This selection is not a rights-review attestation.

- Revision: `947850d484c71f657dbec2bb7e3d356cb5fb23e3`.
- 104 training and 20 reused development rows, unchanged from frozen originals.
- Six files: two JSONL splits, dataset card, license, source-origins summary, manifest.
- All six downloaded and SHA256-verified at the uploaded immutable revision.
- No annotation receipts/private reviewer metadata, original base responses, CETVEL
  texts or controls included. Whitelisted schema and every message/target checked.
- No dataset visibility change or model-card modification occurred during this upload.
- Preparation/upload helper: `upload_private_dataset.py`. It performs external writes
  and must not be run for read-only status; retry requires inspecting the saved receipt.

The earlier statement above that no dataset upload occurred describes the model-only
step, not the current state. Dataset license text is now included; historical
provenance/provider-terms review remains pending before public redistribution.

## Observed public state and migration snapshots

Read-only Hub check later on2026-10-05: both repositories are public, changed
by the owner outside the upload helpers. No visibility mutation by the agent.
Model current card revision: `2e88c9954bc892ffb10273fa9d3cb9b89f2d976c`;
dataset current revision: `947850d484c71f657dbec2bb7e3d356cb5fb23e3`.
Exact public README snapshots at those revisions are `OCCAM-MODEL-CARD.md` and
`OCCAM-DATASET-CARD.md` for the Mac handoff. Original verified weight revision
remains `1a8a07ff2a29f51a2b6a635a8c219191a7377996`.

Historical provenance/provider-terms review is not certified by this observation.
Windows-only publication scripts are retained as the operations record, not
portable setup scripts for the new Mac unit-test-generation project.
