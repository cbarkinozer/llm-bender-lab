## Owner policy: intent-driven training, no implementation source

Train the workflow from user intent through clarification, planning, file-level tasks and requirement-based tests. Repository implementation source must not appear in model inputs or targets, even if a rich audit record retains source/reference columns. Serialize only the explicit conversation-field allowlist; never serialize the whole record or concatenate audit columns. Public interface contracts may be supplied as task context or labeled as proposed design choices. Generated pytest code and necessary synthetic fixture snippets remain intended targets. The current projection preview and its regression checks are documented in experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft/CONTENT-REVIEW.md.

> New active format, 2026-10-31: [task-to-tests pilot](../experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft/README.md). A persistent application plan and explicit interfaces are input context; each target is one complete pytest file with concise separate authored rationale. Planning targets remain separate and excluded from the first SFT. The whole-app format below is retained as history.

> Current bundle: [app-core-v07](../experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v07/README.md). Static AI feedback is stored separately from model messages and human annotations. The owner selected AI review for this utility demo. v07 clarifies interfaces, adds discriminating controls and uses fresh portable execution/fault/order evidence; older revision descriptions below are historical.

# Requirements-to-tests example format

The task is a natural application request followed by a proposed interface and
acceptance tests, written before implementation. This is shared across all nine
current candidates.

## Model-visible input

The system message contains common Python/pytest instructions, the response
structure and actual execution constraints such as offline fixtures. The user
message contains the natural application request. Include additional
clarifications only when they are available; do not invent historical user
answers or append dataset-construction commentary.

## Model-visible output

Keep concise, authored explanatory rationale in `reasoning_content`, separate
from the final response. Use these final-response sections in order:

1. Decisions and unresolved questions: state proposed assumptions and leave
   nonessential choices open.
2. Proposed interface agreement: define callable names, parameters, relevant
   schemas, errors and behavior before the tests use them.
3. Requirement-to-test map: connect requirements to actual test IDs or manual checks.
4. Complete test files: include fixtures and configuration, without app implementation.
5. Manual checks: list subjective, live-service and delivery checks explicitly.

API names may be chosen in the proposed interface; they need not be guessed
from the user paragraph. The tests must agree with that proposal.

## Outside the model messages

Store source repository/revision, authorship, split, provenance, review labels,
validation logs, faulty-variant results, length measurements and construction
notes as metadata. Argilla may display these as review evidence. Never serialize
the entire Argilla packet or JSON record as the model prompt or training target;
use only the intended messages and native chat template.

The word scanner checks model-visible content only. Terms such as “reference”
or “review” are inspection triggers, not universal bans: a requirement to retain
email source references is legitimate. Preserve functional requirements while
removing discussion about constructing or judging the dataset.

## Current revision

`app-core-v04` changes the shared format and module-description prose. Its test
executable ASTs and application reference implementations match v03. The
record-specific Docker/executor draft is archived separately and is not included
in the active examples. Existing annotations remain in their earlier datasets;
no approval is copied or fabricated for changed records.

## Presentation and pre-checks

The active review is app-core-v05. HTML escaping is a presentation transform only;
never feed escaped display fields back into training. The renderer must round-trip
angle brackets, comparisons, ampersands and HTML-looking literals to the original
code without creating tags. Existing annotations survive in-place display repair.

Process-word checks include revision/reference/paper/review, repo/lab names and
local source paths. A flagged keyword requires an assessment; application fields
such as model_revision and declared public API identifiers are legitimate.
Numbered test_rN_ names must agree with at least the corresponding R-id in the map.
Preservation claims need targeted state-loss/stale-state probes. Compare deep
copies and durable bytes across failed operations, and test legitimate replacement
on success so that an implementation which always keeps stale state also fails.
