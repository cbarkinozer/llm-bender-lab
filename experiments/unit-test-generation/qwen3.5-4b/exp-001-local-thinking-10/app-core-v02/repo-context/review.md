# repo-context — assistant review

## Whole-app request

Build me a Python tool that turns a GitHub repository into a readable Markdown context snapshot I can give an LLM. Let me supply a repository URL, optionally a branch and subfolder, choose file extensions and a per-file line limit, and get repository metadata, dependency summaries, a directory tree and selected text-file contents in deterministic order. Respect .gitignore and common generated/dependency directories, don't include secret environment files by default, skip non-text files, and clearly identify truncated files instead of making the snapshot look complete. Support private repositories with a token kept out of the output, show a useful error when cloning or reading fails, and clean up temporary checkouts even after failure. Give me a CLI and a simple local Streamlit page for generating and downloading the same snapshot; no hosted service is necessary. Keep the core independent of the UI so it can be checked with a small local fixture repository instead of real network requests.

## Decisions and corrections

- MVP supports simple branch names in tree URLs; slash-containing branches need an explicit future syntax, not guessing.
- Line limit >0 truncates; zero means unlimited. Secret files and symlink policy need explicit checks before calling the output safe.
- The CLI/UI should share one operation, but that property is not established by core-helper tests alone.

## Important limits / missing acceptance checks

- Generated checkout tests cover the core path but not CLI/Streamlit parity, sparse checkout, symlinks or credential sanitization on clone failure.
- Current code can include credentials in error text; do not certify credential-safe behavior until a dedicated check/fix exists.

## Requirement-to-test review

### R1 — Interpret repository URL and requested branch/subfolder.

**Core check:** Approved URL examples select the correct base repo, branch and analysis root; branch names containing slashes need an explicit agreed representation.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — Respect extension and ignore policies.

**Core check:** Fixture includes main.py, ignored private.py, .env, binary file and node_modules; only eligible text appears in both tree and contents.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — Produce truthful metadata and dependencies in deterministic order.

**Core check:** Known local fixture commit/branch and requirements appear exactly; repeated runs with fixed clock/content differ in no substantive fields.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Apply and disclose line limits.

**Core check:** Three-line file with limit one contains first line but not the second/third, and names the truncation; unlimited policy is explicit.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Preserve errors/cleanup and exclude credentials.

**Core check:** Injected clone failure yields useful error and no leftover checkout; fake token never appears in returned snapshot or exposed diagnostics.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — CLI and UI use the same generation operation.

**Core check:** Identical options produce identical generated Markdown; download payload matches the returned snapshot rather than a partial UI rendering.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_core.py::test_tree_filters_extensions_and_ignored_directories`
- `tests/test_core.py::test_explicit_ignore_removes_matching_file`
- `tests/test_core.py::test_requirements_are_included_in_dependency_context`
- `tests/test_core.py::test_pyproject_dependencies_are_listed`
- `tests/test_core.py::test_branch_and_subdirectory_are_separated`
- `tests/test_core.py::test_utf8_file_is_recognized`
- `tests/test_core.py::test_invalid_utf8_is_rejected`
- `tests/test_core.py::test_context_workflow_reads_selected_files_and_reports_truncation`
- `tests/test_core.py::test_clone_failure_returns_error_and_cleans_temporary_directory`

## Manual checks

- Streamlit form/download usability and one controlled live clone.
