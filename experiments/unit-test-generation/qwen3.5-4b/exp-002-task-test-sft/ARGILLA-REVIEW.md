# Demo protocol update: exhaustive annotation waived

The owner waived the 169-site oracle review and manual smell checklist for this
demo. All five primary comparisons are submitted and frozen outside Git before
unblinding. Run `scripts/evaluation/summarize_tdd_demo_review.py --snapshot <export-folder>`
with a new `--output` for a new report version; only complete PRIMARY reviews are
required. Its automatic pass uses the requested local study checkout and imports
measurement tooling only. See [POST-REVIEW-RESULTS.md](POST-REVIEW-RESULTS.md).

The original strict `adjudicate` command below remains available for optional full
validation; it is not a required demo gate. No manual labels or human validation
are fabricated for skipped oracle/smell records. Supporting reviews are separate
and remain pending. Current primary/UI records are preserved unchanged.

Historical v02 full-validation instructions follow.

# Local anonymous comparison UI - v02 taxonomy review

Argilla: http://127.0.0.1:7900 ; workspace `tdd-blind-comparison`.
Existing server, credentials, volumes and v01 reviews are preserved.

Review in this order, clicking Submit on each record:

1. [Overall usefulness: five comparisons](http://127.0.0.1:7900/dataset/1ed2b4a4-a785-45b2-ba44-3e571a499bad/annotation-mode).
   Rank X/Y/Z with ties allowed; retain/repair/reject/uncertain plus evidence.
2. [Individual oracles: 169 records](http://127.0.0.1:7900/dataset/da418388-67c8-4111-934f-38384b94e508/annotation-mode).
   168 sites plus one administrative unparseable output. Rate only the highlighted
   site, using the complete requirement and candidate for context.
3. [Smells: 15 candidate files](http://127.0.0.1:7900/dataset/2a154ccb-eedb-4798-a38e-2b4275b1a8a6/annotation-mode).
   Independently label each of 11 categories present/absent/uncertain/not_rateable.
4. [Supporting probes: four comparisons](http://127.0.0.1:7900/dataset/5d13e6ae-4cc5-4054-b65e-9cb502ab0a43/annotation-mode).
   Separate capability; retained from v01.

## Assertion rubric

The previous unanchored 1-5 file rating is removed from current overall comparisons.
Adopt the paper's PROTOCOL_V2 prospectively for these oracle-site annotations:

- TRIVIAL: constant, tautological, self-comparison; unable to distinguish focal behavior.
- WEAK: SUT-dependent existence, truthiness, nullity, type, non-emptiness or coarse shape.
- STRONG: specific value/content, state transition, exception/warning or relevant mock interaction.
- UNKNOWN: insufficient evidence to establish provenance or strength; not a middle strength.

SUT dependency, requirement correctness, confidence and evidence are recorded separately.
A precise wrong expectation can be STRONG and incorrect. Static presence does not prove
execution. NO_ORACLE and UNPARSEABLE are administrative statuses, not UNKNOWN/WEAK.
Parametrized assertions are rated once per static site. Aggregate class counts rather
than replacing the distribution with a file's strongest assertion.
Full protocol: `scripts/evaluation/paper_quality_tools/ORACLE-PROTOCOL-V2.md`.

## Smells and automatic adjudication

Eight classic categories: assertion roulette, eager test, mystery guest, magic number,
obscure test, general fixture, conditional test logic and fragile test.
The current paper implementation additionally checks unverified action (`unknown_test`),
trivial/suboptimal assertions and duplicated setup. All eleven are included.
The smell named trivial/suboptimal assertion is broader than oracle-class TRIVIAL:
it includes tests containing only coarse null/type/bool checks (some WEAK oracles).

Automatic predictions are computed statically and saved locally, but NEVER shown in
independent review fields or suggestions. After all overall, oracle and smell records
have submitted responses, the `adjudicate` command freezes the raw independent snapshots
and creates SEPARATE assisted datasets showing machine predictions and evidence.
It refuses premature reveal or changes to an existing freeze. Human final labels and
reasons live separately; original independent labels are not overwritten. Assisted
agreement must not be reported as independent inter-rater reliability. This workflow
currently assumes the single local reviewer; it is not a multi-rater completion gate.

Flags are heuristics, not established defects. Controlled filesystem fixtures, repeated
calls for state transitions and requirement-derived constants may be justified. Review
false negatives as well as positive flags. No test functions is not smell-free evidence.
SUT names are inferred only from Posting imports in these generated development tests;
unresolved calls can be missed. The frozen paper classifier has documented limitations,
including incomplete provenance and strong/weak disagreements. Do not equate its labels
with ground truth. No runtime-reached oracle claim is made by this static pass.

Only measurement code and the written protocol were reused from the pinned reserved
paper repository (commit 380b7d362f49d43fd55af5b2f7e015d4fa651e97). No paper applications,
tests, requirements, outputs or samples enter current splits or training. Tool source
hashes, extraction details and upstream Apache license accompany the vendored tools.
This is a post-run diagnostic protocol extension, not a pre-training registered metric.

## Recreate, export and reveal

Dedicated SDK environment: `C:/Users/barkin/Documents/llm-bender-artifacts/argilla-tdd-review/.venv`.
SDK/environment freeze is preserved under `gpu-results-20261107/argilla-review-v01`.
Credentials remain in the ignored ReflexModels `experiments/decision-followups/review-ui/.env`.
No credentials or private model-identity mappings are uploaded or committed.

```powershell
$reviewPython = 'C:/Users/barkin/Documents/llm-bender-artifacts/argilla-tdd-review/.venv/Scripts/python.exe'
$credentialFile = 'C:/Users/barkin/Documents/GitHub/ReflexModels/experiments/decision-followups/review-ui/.env'
& $reviewPython scripts/evaluation/publish_tdd_taxonomy_argilla.py publish --credential-env $credentialFile
& $reviewPython scripts/evaluation/publish_tdd_taxonomy_argilla.py export --credential-env $credentialFile
# Only after all independent overall/oracle/smell labels are submitted:
& $reviewPython scripts/evaluation/publish_tdd_taxonomy_argilla.py adjudicate --credential-env $credentialFile
# Supporting probes are exported separately using the historical v01 receipt:
& $reviewPython scripts/evaluation/publish_tdd_threeway_argilla.py export --credential-env $credentialFile --output C:/Users/barkin/Documents/llm-bender-artifacts/tdd-gpu-20261107/argilla-exports/supporting-session-02
```

v02 exports create unique timestamped directories, ignored by Git. Preserve those and
`independent-frozen.json` with the external artifact backups after rating sessions.
Current receipt: `gpu-results-20261107/argilla-review-v02/receipt.json`.
Initial v01 backup: external `argilla-exports/before-taxonomy-v02` (zero submitted).
Keep `blind-three-way-v02/PRIVATE-identities.json` outside the UI. Unblind only after
ratings are exported/frozen, then combine human evidence with execution results.
