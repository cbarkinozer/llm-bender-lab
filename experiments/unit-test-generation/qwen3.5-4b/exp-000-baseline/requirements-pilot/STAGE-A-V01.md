# Frozen Stage A development pilot v01

## Scope and current state

The [protocol](stage-a-protocol-v01.json) freezes requirements-to-tests generation
settings. It does not freeze a complete 20-task benchmark or the later implementation
comparison: 20 candidates are retained, one is quarantined, one completed a v01
generation, and 18 still require preflight. No candidate was replaced because of
model performance. Shortlisted repository groups remain excluded from future
independent transfer evaluation and training data.

Use [task inputs](stage-a-task-inputs-v01.json) for immutable ready packet hashes
and [run index](stage-a-run-index-v01.json) for outcomes. Readiness concerns inputs,
not whether generated tests pass. Do not edit a generated task's ready packet.

## Confirmed TOML reference defect

[Adjudication](tomlkit-reference-adjudication.json) contains two pairs of valid
TOML inputs with identical parsed data and no arrays of tables. Dotted notation
raises KeyAlreadyPresent during recursive inline conversion; explicit table notation
preserves values and returns the original document. The minimized pair reproduces
this representation-dependent failure. It contradicts the written conversion
contract, so reference-pass quality scoring is quarantined. Original benchmark
contents and previous model results are unchanged. No upstream message was sent.
The generated suite still has separate clear model mistakes; a reference defect
does not validate the whole suite.

## Pinned generation and execution

- Untouched Qwen3.5-4B Q4_K_M; Pi 1.0.3; server/Pi context 16,384 tokens.
- Thinking medium; 4,096 output tokens including reasoning; 240-second timeout;
  temperature 0.6, top_p 0.95, top_k 20, seed 42; one attempt, no repairs or tools.
- Source and effective prompt/context hashes checked before inference.
- Request JSON is stored outside Git. Transport checks verified SSE forwarding
  and exclusion of authorization headers. The first real v01 request confirms
  the sampling values, full output allowance and `enable_thinking=true`.
- Generated tests execute unchanged with source/tests/root filesystem read-only,
  no network, 1 CPU, 2 GB memory, 60-second timeout and a task-specific image ID.
- Retain invalid outputs, infrastructure failures and quarantined task statuses.
  Reference failures require semantic adjudication rather than automatic model
  error labels. No composite quality metric, reward or training recipe is frozen.

## Mashumaro: first v01 run

The reference passed 72 supplied feature tests and 30,008 selected regression
tests. An initial 512 MB regression execution ended with signal -9 despite a
complete passing XML report. It was recorded as unsuccessful infrastructure and
rerun unchanged at 2 GB with a clean exit; no checks were dropped. The public
fixture example also passed on the unmodified original source.

Pi generated 19 test functions, stopped normally and produced syntactically valid
Python. Actual request settings matched v01. The suite was independently executed
against reference and original code with unchanged hashes. Detailed outcomes are
in `mashumaro-stage-a-outcome.json`, separate from the initial annotation UI.
The original suite is not accepted for implementation; owner quality/semantic
ratings and failure adjudication are pending. No tests were repaired and no
test-first implementation was run.

## Independent human review

[Open initial review](http://127.0.0.1:7900/dataset/18519c25-5b8f-4a1b-94e8-12ce0a87a340/annotation-mode).
The separate dataset `requirements-stage-a-v01-initial-v02` shows the requirement,
approved public API context and unchanged tests. It omits model identity,
execution outcomes, automated suggestions and hidden tests. Apply the existing
robustness/assertion-strength/readability/conciseness rubric, oracle classes and
contextual smells. Record important behaviors protected or missing and evidence.

Imports append by stable anonymous ID and preserve existing records/responses;
a repeated import preserved the record. Retain initial judgments separately
from later evidence-assisted adjudication. Raw prompts, tests and traces remain
outside Git; compact provenance and results are recorded here.

## Next work

Collect the owner's initial review, then show execution evidence for separate
adjudication. Preflight the remaining shortlisted tasks under unchanged v01
generation settings. Do not tune prompts until a suite passes or silently replace
failures. Implementation requires a correct, useful, frozen original suite.

Review schema note: the first form version made smell/oracle questions required.
The server did not persist attempts to relax those published flags, so it was
preserved and superseded by v02 with optional selections verified after creation.
No records or responses were deleted.

### Review update — 2026-10-17

Review guidelines v0.3 clarify Pass@1 (one original sample, no repairs) and separate execution from runtime non-trivial gates. Frozen generation settings are unchanged. See `mashumaro-review-spec-v03.json` and `../../review-guidelines-v0.3.md`. The new review is assisted calibration with prior feedback exposure; older records remain preserved.
