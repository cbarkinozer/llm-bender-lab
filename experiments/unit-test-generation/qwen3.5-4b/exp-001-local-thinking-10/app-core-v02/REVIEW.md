# Assistant review of the nine app briefs

Owner review waived for this demo; no human ratings have been submitted. The original drafts are preserved in app-briefs-v01. This revision replaces wide tables with vertically stacked requirement blocks.

## GitHub-insignia

- Keep existing agreed public-owned/nonfork scope and twelve-calendar-month UTC window.
- Keep private/token-visible contribution scope separate from public repository statistics.
- No grade; no live data required in core tests.
- Browser appearance and real authenticated GitHub compatibility are manual/live checks.

## ghost-box

- Keep one active account and RAM-only email data. Search can only make claims about explicitly downloaded mail.
- Literal filtering is case-insensitive with Turkish-aware folding; ranked search is a separate operation.
- Choose local-time UI date ranges with timezone/DST conversion; document boundaries before adding date assertions.
- Core store/search/evidence tests do not yet cover provider fetching, date filter integration, cancellation races, history cleanup or model lifecycle.
- GUI responsiveness and model-generated summary factuality need separate review.

## slm_test_generation

- Use fresh synthetic utility fixtures, never frozen paper benchmark tasks/predictions.
- A strong but incorrect oracle must remain a failed test; reachability and strength are independent.
- Infrastructure errors and missing observations must stay disclosed; choose denominators explicitly before adding aggregation tests.
- Current core suite verifies oracle taxonomy/reachability, not isolated execution, aggregation, mutation denominators or manifests.
- The app request is a pipeline MVP; the full paper reproduction is outside it.

## llm-bender-lab

- Do not include old authored evaluation rows in training; test preprocessing with fresh fixtures.
- Keep a replaceable backend in the requested app; do not call actual GPU training from core tests.
- Preserve baseline/candidate generation settings and distinguish percentage points from relative percent.
- The current application is experiment-specific scripts, not the generic orchestrator implied by the first brief.
- Current tests cover preprocessing/loss labels/padding/review but not generic run creation, backend success/failure or effective configuration comparison. Do not label this whole-app-ready.

## ReflexModels

- Use declared candidate order to resolve exact ties. Probability sums use the existing 1e-6 tolerance.
- Keep immutable runtime-defined choices and original Unicode identifiers.
- Treat empty-metric behavior as an explicit error unless a future interface specifies missing values; do not invent perfect scores.
- Core tests cover types/scoring/routing/metrics; calibration fitting, empty metrics and all serialization validation branches need further checks.
- Semantic decision quality and CPU latency are separate from injected-score arithmetic.

## codelang-detect

- Choose Python and JavaScript as explicit starter examples; extending language coverage is a later agreed requirement.
- Equal weighted scores choose the first declared language; rules are developer configuration, not a new runtime configuration service.
- File-open CLI usage failures exit 2; processing failures exit 1. Both are nonzero and use stderr. The first draft wrongly assumed all errors exit 1.
- No retained benchmark corpus included in these fresh cases.
- Throughput and broad language accuracy need separate evaluation; strong tests are not a perfect detection guarantee.

## repo-context

- MVP supports simple branch names in tree URLs; slash-containing branches need an explicit future syntax, not guessing.
- Line limit >0 truncates; zero means unlimited. Secret files and symlink policy need explicit checks before calling the output safe.
- The CLI/UI should share one operation, but that property is not established by core-helper tests alone.
- Generated checkout tests cover the core path but not CLI/Streamlit parity, sparse checkout, symlinks or credential sanitization on clone failure.
- Current code can include credentials in error text; do not certify credential-safe behavior until a dedicated check/fix exists.

## cryptocurrency-analyser

- Use a clearly named price-comparison MVP; remove influencer scraping, LLM recommendations, posting and trading from this demo request.
- Return = current/first-row price - 1; preserve interior NaNs, remove only all-missing columns.
- Zero/missing baseline and invalid inputs remain unresolved behavior gaps, not license to assert fabricated finite returns.
- CSV/offline app workflow and validation/error presentation are not yet represented by the comparator module.
- Current tests verify numeric/plot/orchestration core; provider error propagation and missing baselines need additional acceptance work.

## miniature-llms

- First-version scope must be explicit: compact PyTorch components plus a tiny composed model, not all 25 architectures/JAX/Triton.
- Numerical tensor comparison uses tolerance, not exact floating-point equality.
- Do not accept output shape or a decreasing loss as proof of correct causal behavior.
- Existing causal attention and RoPE use incompatible axis conventions in their composition; this needs a dedicated regression and implementation fix before model-level certification.
- Current suite covers RMSNorm/RoPE only. Embedding/composed causality/checkpoint/training/generation are not yet covered.
