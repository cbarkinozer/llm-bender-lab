# External source audit — 2026-10-05

Candidate source: nebius/SWE-rebench-leaderboard, pinned revision
`34d5a58864acf91613740a09ec5d205228dcfa39`.

The pinned `2026_03` parquet contains 110 tasks from 79 repositories, with
46 PR creation dates in March, 43 in April and 21 in May 2026. Split names
are not adequate temporal filters. SHA256 and task metadata are preserved in
`swe-rebench-march2026-metadata.json`; source-bearing parquet stays outside Git.
No task has been selected or run against the model.

Missing checks: original issue date, relevant code history, exact task-commit
license, gold test reliability, solution leakage in issue text, near-duplicates,
ARM64 dependency compatibility and pinned grading image digests. Supplied
x86_64 images use mutable tags. Current default-branch licenses for three
candidate repositories were inspected; this is not task-commit clearance.

This source measures repair. Converting it to test generation creates a labeled
adaptation, not an official SWE-rebench test-generation score. SWT/Multi-SWT
provide directly relevant external task protocols but their original source
freshness needs independent review. Model training cutoff remains unverified.

Before choosing tasks, settle whether the first pilot targets issue-reproduction
or general tests for correct modules. Keep pilot/development examples separate
from final holdout and do not derive training targets from evaluation tasks.
