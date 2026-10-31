# Continue on another machine

For the next GPU session, start with NEXT-SESSION.md. It records the baseline-first
two-arm plan, the8192-output/9216-context revision, and pending Arm B masking work.

Pull the repository. Active selections are in `config-planned.json`; do not pick
the largest version number independently from each directory.

The actual source-free training conversations are committed under
`intent-only-preview-v02/`: tests 50, planning 13, reliability 15. Keep tracks
separate: no mixture or training recipe has been approved. Development and
holdout records are in the active rich candidate bundles; the portable package
also supplies allowlisted conversations physically separated by split.

`portable-share/intent-tdd-v03.zip` is committed so source snapshots do not depend
on the original Windows machine. SHA256:
`3241b376da312827f77fc1c8d91aeb6e12df76e42a1834e6efb60f5f4af530e4`.
Extract outside the checkout and run `python intent-tdd-v03/verify_package.py`.
It contains 95 conversations and 11 inventoried pinned source snapshots with
notices, plus the mapped original/authored modules for 58 test tasks. It is a
scoped audit package, not complete runnable upstream repository archives.

Never feed `audit/` source/reference files into the model. Existing builders and
reference runners still contain original-machine paths; extracting this package
does not automatically relocate those runners. Adapt their source-root settings
or path resolution before rebuilding/reference execution on the desktop.
Python environments, model weights, and tokenizer caches are not committed.
Recreate dependencies and obtain the pinned tokenizer/model revision from config
when needed. Existing native label audit arrays/evidence are committed, but
actual trainer batch parity remains to be checked in the chosen runtime.

## Current quality limits

No exact conversation/test/test-function duplicates were found. Repository
families are disjoint across splits. Targeted semantic review recorded three
train-to-development/holdout taught-principle overlaps. It is not an exhaustive
semantic independence guarantee. Those scenarios can measure transfer of taught
principles, but cannot be called entirely unseen-rule evaluation.

Domain distribution is intentionally different across splits: nine families are
training, Posting is development, ddgr is holdout. Domains are not equal or
balanced across splits; the small development/holdout sets limit conclusions.
Cyclomatic complexity and token lengths were profiled, not matched or certified
balanced across splits. Combined training token exposure is dominated by planning
if every row is sampled equally. See `DATASET-PROFILE.md` and its linked v02 data.

Do not claim zero validation-to-test leakage or professional benchmark readiness.
Choose whether evaluation measures domain transfer or matched-distribution
performance, resolve the documented overlaps accordingly, then freeze splits and
runtime. Baseline inference and fine-tuning have not run. Data selection, recipe,
runtime/protocol freeze and actual trainer label parity remain open.

The owner confirmed ownership of ReflexModels and repo-context on 2026-10-31;
their missing snapshot license notices are not a third-party permission blocker.
Other upstream notices remain applicable; no blanket dataset license is assigned.
