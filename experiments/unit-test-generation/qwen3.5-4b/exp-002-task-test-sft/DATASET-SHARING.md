# Portable dataset review package

Current local artifact: `C:/Users/barkin/Documents/llm-bender-artifacts/dataset-share/intent-tdd-v03.zip`.
SHA256: `3241b376da312827f77fc1c8d91aeb6e12df76e42a1834e6efb60f5f4af530e4`.
Size: 1,625,101 bytes. Earlier v01/v02 are superseded by v03's owner clarification.

Builder: `scripts/evaluation/build_dataset_share.py --output <new-directory>`.
Refuses to overwrite existing releases. Copies pinned inventoried source files
once per family and preserves discovered upstream license/notice files.
This is a scoped source snapshot, not a complete executable repository archive.

- 95 conversations, separated into tests/planning/reliability and train/development/holdout.
- 78 training-family conversations exactly match the active audited preview.
- Audit index joins records to package-relative files and pinned revisions.
- All 58 test examples have mapped original/authored reference modules; these
  are declared task modules, not complete runtime dependency closures.
- Original source and adapted/authored references remain distinct and audit-only.
- SHA256 inventory and standalone `verify_package.py` support offline verification.

Verification: all file hashes and 95 record links pass, including 58 test mappings.
The ZIP was extracted to a temporary location and its standalone verifier passed
there. Existing projection regression tests: 2 passed. No model run, training,
publication, split freeze or training mixture selection was performed.

Owner clarification (2026-10-31): the user confirmed ownership of ReflexModels
and repo-context and authorized their inclusion. Their missing snapshot license
notices are therefore not a third-party permission blocker. The v03 ZIP includes
this clarification; v02 predates it and should not be used as the current release.
Other upstream licenses remain separate; the package assigns no blanket license
to third-party code or the dataset. No public publication has been performed.

The manifest records provenance and readiness limitations. Semantic review still
has three cross-split taught-principle overlaps; runtime protocol and actual
trainer label parity remain pending. Sharing packaging changes none of those
experimental decisions. Never train from `audit/` or stringify its records.
