# Prompt selection v2 frozen

Active version for future generation, frozen 2026-10-02 after coverage repair,
source/new-authoring binding checks, turn-aware overlap checks and documented
manual scenario review. V1 remains intact; no historical frozen artifact changed.

Scope: `data-v2/` prompt wording, semantic input messages, source metadata,
scenario groups, behavior mapping and 80/20 split. Canonical prompt hashes are in
`data-v2/selection-manifest.json`. No assistant target approval is implied.

Future changes require a new version, audit and generation-config dataset hash.
`--refresh-v2` may no longer overwrite differing v2 artifacts.
