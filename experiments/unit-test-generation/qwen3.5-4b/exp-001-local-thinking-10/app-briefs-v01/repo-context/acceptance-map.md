# repo-context — draft core acceptance map

Whole context-generation app MVP, excluding optional repository-quality scoring and deep-wiki generation. Several new core acceptance tests remain needed.

These are proposed checks, not an executed suite or proof of complete coverage.

| ID | Observable requirement | Concrete oracle / core check | Level |
|---|---|---|---|
| R1 | Interpret repository URL and requested branch/subfolder. | Approved URL examples select the correct base repo, branch and analysis root; branch names containing slashes need an explicit agreed representation. | unit/integration |
| R2 | Respect extension and ignore policies. | Fixture includes main.py, ignored private.py, .env, binary file and node_modules; only eligible text appears in both tree and contents. | integration |
| R3 | Produce truthful metadata and dependencies in deterministic order. | Known local fixture commit/branch and requirements appear exactly; repeated runs with fixed clock/content differ in no substantive fields. | integration |
| R4 | Apply and disclose line limits. | Three-line file with limit one contains first line but not the second/third, and names the truncation; unlimited policy is explicit. | unit/integration |
| R5 | Preserve errors/cleanup and exclude credentials. | Injected clone failure yields useful error and no leftover checkout; fake token never appears in returned snapshot or exposed diagnostics. | integration |
| R6 | CLI and UI use the same generation operation. | Identical options produce identical generated Markdown; download payload matches the returned snapshot rather than a partial UI rendering. | integration |

## Public test boundary (proposal)

Generate-snapshot operation and CLI/UI adapters; temporary checkout fixture, injected clone/clock and no internal helper-name requirements.

## Decisions still needing agreement

- Agree URL syntax for slash-containing branches, symlink handling, zero/negative line limits and which secret filenames are excluded.
- Define whether unreadable selected files fail the whole snapshot or appear as explicit omissions.

## Manual / live checks

- Streamlit form/download usability and one controlled live clone.

## Candidate existing evidence — not automatically selected

- `tests/test_core.py`
- `tests/conftest.py`

Source revision: `efc00f0c4c77fb404a65ba7447e974c754b27452`. These prompts are reconstructed drafts, not historical original user messages. Split role is unassigned; never use the same app/scenario for both SFT and claimed held-out improvement.
