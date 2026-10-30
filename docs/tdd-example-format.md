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
