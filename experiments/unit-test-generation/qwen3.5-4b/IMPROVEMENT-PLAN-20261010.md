# Pipeline improvement priorities — 2026-10-10

Owner accepted these recommendations and requested that they be saved locally.
Continue through the TODO without waiting for routine implementation decisions.

1. Validate tasks before generation. Reject incomplete extraction, unresolved
   revisions and missing dependencies. Specify inputs, outputs, exceptions and
   side effects; ambiguous contracts remain exploratory rather than scored.
2. Preserve original code and interfaces. Do not silently inject imports, add
   `self` or wrap functions in `Solution`. Save any necessary transformation,
   the original source and its rationale.
3. Strengthen provenance and freshness checks. Identify tasks by repository,
   full commit, full path and source hash. Inspect function history rather than
   repository activity. Keep contamination risk unknown without evidence and
   resolve source licenses before redistribution.
4. Keep execution and quality separate. Report collection/pass status, target
   exercise, assertion relevance/correctness, meaningful change detection and
   contextual smells independently. Do not turn these into a reward yet.
5. Strengthen protected execution. Isolate each task with time, memory,
   filesystem and network limits. Preserve original generated tests and separate
   syntax, collection, assertion and infrastructure failures.
6. Make Argilla review independent. Initially show contract, source and tests;
   hide model identity and automated quality suggestions. Record the initial
   judgment before revealing execution/oracle/smell evidence for a second review.
7. Preserve independent evaluation. Group splits by repository/code family and
   deduplicate across splits. Historical paper tasks are development fixtures.
   Maintain a separate trusted benchmark track instead of measuring gains only
   on our own collection.

Immediate order: independently validate smoke-task contracts, implement the
protected Pi execution harness, run a development pilot, then import original
suites and evidence into Argilla. Human annotations will inform whether SFT is
needed for demonstrated format/tool deficits or whether GRPO experimentation is
justified. Neither training approach is selected in advance.

See [TODO](TODO.md) for execution stages and
[paper pipeline audit](PAPER-PIPELINE-REUSE.md) for completed work and limitations.
