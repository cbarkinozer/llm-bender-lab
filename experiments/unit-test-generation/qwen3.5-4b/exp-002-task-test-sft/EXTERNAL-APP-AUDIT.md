# External application source audit

Snapshot: 2026-10-31T18:46:03.294917+00:00

Four immutable source snapshots were downloaded outside Git and statically inspected. No source code was executed. This adds **20 source-backed task proposals and zero SFT rows**. The existing pilot remains 38 draft examples.

| Repository | Revision | Source files* | Test/support files* | Proposed role | Task proposals |
|---|---|---:|---:|---|---:|
| [dbcli/litecli](https://github.com/dbcli/litecli/tree/aa53bb0c1530cd1dfb30534babb0bf47df33c60a) | `aa53bb0c1530` | 24 | 14 | train-proposed | 6 |
| [tldr-pages/tldr-python-client](https://github.com/tldr-pages/tldr-python-client/tree/c33ca6d38e1397a8ad9208ee83189b08b5446e0d) | `c33ca6d38e13` | 2 | 2 | train-proposed | 6 |
| [darrenburns/posting](https://github.com/darrenburns/posting/tree/32c45669032342cf9b95d5758af47a0d93de0ad7) | `32c456690323` | 82 | 30 | development-proposed | 5 |
| [jarun/ddgr](https://github.com/jarun/ddgr/tree/b0c9e74e226a22a96c863d03cb82e5b5569851c3) | `b0c9e74e226a` | 2 | 0 | holdout-proposed | 3 |

*Counts include setup/demo/docs/support Python files and ddgr's extensionless main script; they are not eligible task counts. Test counts include fixtures/helpers, not collected pytest cases.

LiteCLI and tldr are proposed training additions for SQL parsing/execution and cache/network routing. Posting is proposed development data for stateful backend contracts without its full terminal UI. ddgr is proposed additional final evaluation data; the two original reserved evaluation families remain excluded from training. Roles are proposed before authoring or model evaluation and are not frozen.

## Candidate tasks

### dbcli/litecli

- `litecli-sql-table-identifiers`: Extract schema, table and aliases across joins and nested queries. Source: `litecli/packages/parseutils.py` (extract_tables).
- `litecli-sql-destructive-detection`: Recognize destructive statements across comments and multiple statements; reject safe SELECT controls. Source: `litecli/packages/parseutils.py` (is_destructive, queries_start_with).
- `litecli-completion-last-word`: Respect punctuation modes, empty input and trailing whitespace. Source: `litecli/packages/parseutils.py` (last_word).
- `litecli-path-completion`: Complete temporary-directory paths and tilde prefixes with explicit platform semantics. Source: `litecli/packages/filepaths.py` (parse_path, complete_path, suggest_path).
- `litecli-sqlite-query-execution`: Run parameterized queries and preserve Unicode using a temporary SQLite database. Source: `litecli/sqlexecute.py` (SQLExecute).
- `litecli-special-command-dispatch`: Parse command arguments and distinguish known from unknown commands. Source: `litecli/packages/special/main.py` (parse_special_command, execute).

### tldr-pages/tldr-python-client

- `tldr-python-client-language-selection`: Resolve locale variants and explicit language priority with English fallback. Source: `tldr.py` (get_language_code, get_language_list).
- `tldr-python-client-cache-path-selection`: Resolve XDG, home, language and platform cache paths without touching real user files. Source: `tldr.py` (get_cache_dir, get_cache_file_path).
- `tldr-python-client-cache-freshness`: Check fresh, boundary-age, stale and missing cache files against a controlled clock. Source: `tldr.py` (have_recent_cache).
- `tldr-python-client-page-url`: Build language-specific and default-English URLs with escaped command names. Source: `tldr.py` (get_page_url).
- `tldr-python-client-cache-network-routing`: Exercise fresh-cache hits, successful mocked downloads, stale-cache fallback and cache-only misses. Source: `tldr.py` (get_page_for_platform).
- `tldr-python-client-platform-priority`: Place the active platform first without duplicate platforms; do not assert unordered tail order. Source: `tldr.py` (get_platform, get_platform_list).

### darrenburns/posting

- `posting-path-parameters`: Preserve placeholder order, escaped colons and query/fragment text. Source: `src/posting/urls.py` (extract_path_param_names, substitute_path_params).
- `posting-query-pair-merge`: Preserve duplicate occurrences, blanks, table overrides and disabled rows. Source: `src/posting/urls.py` (extract_query_pairs, merge_url_query_into_params).
- `posting-request-filenames`: Validate filenames and resolve collisions in a temporary directory. Source: `src/posting/files.py` (is_valid_filename, get_unique_request_filename).
- `posting-session-undo-redo`: Check set/revert/undo/redo transitions and redo invalidation after a new edit. Source: `src/posting/session_variables.py` (SessionVariables).
- `posting-session-history-limit`: Check the documented 50-edit retention boundary and script-written value restoration. Source: `src/posting/session_variables.py` (SessionVariables).

### jarun/ddgr

- `ddgr-unicode-safe-urls`: Check IDNA domains, credentials and percent encoding against an explicit approved contract. Source: `ddgr` (make_safe_url).
- `ddgr-search-pagination`: Check next/previous/first-page state transitions without network calls. Source: `ddgr` (DdgUrl).
- `ddgr-result-serialization`: Check structured result output and URL lookup without launching a browser. Source: `ddgr` (Result).

## Admission work

1. Compare task semantics and upstream lineage against the existing 38 rows and 62-item backlog; merge overlapping proposals rather than padding counts.
2. Check applicable license terms before deriving training material; preserve attribution. Metadata reports BSD-3-Clause, MIT, Apache-2.0 and GPL-3.0 respectively; ddgr is evaluation-only in this proposal.
3. Write requirement-first contracts with explicit interfaces, scope, positive controls and failure expectations. Source behavior is evidence, not an automatically correct specification.
4. Build standalone pytest targets and references; validate reference passes, targeted fault detection and order stability. Use temporary files, a controlled clock and mocked network/browser/subprocess boundaries.
5. Review task contracts and native-token labels, freeze source-family roles, then run the unchanged baseline before SFT.

Dependency inspection: LiteCLI declares sqlparse, click, prompt-toolkit and CLI formatting/config packages. tldr imports termcolor and shtab as well as the standard library. Posting backend slices should avoid importing the full Textual app where possible. ddgr requires loading an extensionless Python script; browser launch and real search requests must be replaced in tests. No dependencies were installed for this audit.

Full per-file SHA256 values, license-file hashes, repository metadata and symbol checks are in `external-app-audit.json`. The snapshots are under `C:/Users/barkin/Documents/llm-bender-artifacts/external-app-audit/`.
