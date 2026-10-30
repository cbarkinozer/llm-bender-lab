# Ten requirement-to-pytest questions, revision 02

These are evaluation/development questions, never SFT training targets.
The original questions, baseline generations and Argilla responses remain preserved.
The old failed suites are diagnostic evidence; they are not approved demonstrations.

Each record stores the full model input as system/user messages. The shared system
instruction specifies Python, pytest, standard-library-only dependencies, native
thinking and a final executable test module. Each user message specifies an agreed
public interface and numbered acceptance criteria, with no implementation.
Titles/IDs are reviewer metadata, not extra model input. Metadata and grading
references must never be appended to model prompts.

Revision 02 clarifies collection shapes, outputs, validation scope, copying, empty
inputs and CSV rules. It also changes the shared quality instructions. Old baseline
scores must not be presented as measurements of these revised prompts. Rerun the
baseline after question review; do not select questions only because they failed.
The v01 runner is tied to the old input file and must be adapted explicitly for v02.

Review is question approval only: no generated reasoning, generated tests or raw
execution logs. Approval is recorded by the owner in Argilla; no responses were
submitted on the owner's behalf. Separate training tasks will later contain correct,
verified reasoning and tests, with semantic correctness, assertion strength,
contextual smells and test complexity reviewed separately.

The ten domains are varied, but dependency levels are only L0/L1. This is a small
demo, not a balanced sample across all paper context/dependency levels. Paper
function-context tiers do not directly map onto requirement-only input. No teacher
solution or test complexity is claimed verified at this stage.

Review: http://127.0.0.1:7900/dataset/bc90f87b-6f3a-4125-979f-fb063ffcb3ee/annotation-mode

Recreate/append without modifying existing owner responses:
`.venv/bin/python scripts/evaluation/prepare_thinking_tdd_questions.py`
