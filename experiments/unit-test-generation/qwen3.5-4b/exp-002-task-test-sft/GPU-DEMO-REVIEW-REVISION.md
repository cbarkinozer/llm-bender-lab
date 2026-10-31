# Evaluation revision after external critique

Budget/next-session update: demo-preflight-v03 now uses8192 output tokens and9216
total inference context. See NEXT-SESSION.md for measured prompt lengths, study
evidence and the proposed two-arm rationale-loss ablation (Arm B still pending).
The v02 protocol below is preserved; its4096/8192 budget values are superseded.

Current protocol: **demo-preflight-v02**. Earlier v01 files and the original
GPU-DEMO-HANDOFF.md are historical; v02 supersedes their evaluation settings.
No training example, target, split, training hyperparameter or label array changed.
The v02 builder is `scripts/evaluation/revise_tdd_demo_protocol.py`.

## Scope and claims

This measures requirement-to-pytest generation under explicit interfaces and
acceptance specifications. Source families are excluded from our fine-tuning
data, not proven unseen during Qwen pretraining. Public upstream exposure is
unknown; neither training-source exclusion nor lack of output overlap disproves
pretraining contamination. There is no evidence establishing that particular
repositories were included in pretraining.

There are50 training tasks from9 correlated families. Development's5 test tasks
all come from Posting; holdout's3 come from ddgr. Do not treat rows as independent
repositories or claim that effective sample size is exactly9. Report small-sample
counts and per-task evidence, not precise population improvement estimates.
The existing three cross-split taught-principle overlaps remain disclosed.
No domain/complexity balancing or split reshuffle was performed.

## Evaluation changes

- Joint evidence: correct-reference pass and curated fault detection, plus
  semantic requirement/assertion review. Neither alone establishes test quality.
- All9 development requests use the same4096 new-token budget for base/adapter,
  thinking enabled. Max context8192. Prompt+budget overflow fails; no truncation.
- All-task completion/parseability/usability counts remain in the denominator.
  Completed-pair semantic quality is explicitly conditional; never silently
  discard incompletes. Future fixed2048-token latency comparisons are a separate
  experiment, not a substitute for this protocol.
- Greedy generation is not a bitwise determinism guarantee. Freeze installed
  vLLM/Torch/Transformers/tokenizers identities before baseline; require the same
  lock for candidate. Same order, max_num_seqs1, chunked prefill disabled, LoRA
  enabled in both base/candidate engines. Record effective flags and raw tokens.
- Native stops are derived and verified against the tokenizer, including
  single-token encoding, expected pinned IDs and tokenizer EOS identity.
- Save matched LoRA module names and trainable/total parameter counts. The seven
  requested projection suffixes are not asserted to cover every hybrid layer.
- Inspect baseline outputs and protected execution before full training; stop or
  proceed with a documented headroom/floor assessment. A script completing is
  not a quality approval.
- Blinded test review hides rationale and role, randomizes A/B sides, permits
  ties/both-unusable, and keeps the key separate. Record reviewer identity,
  authorship relationship and AI assistance. One reviewer does not establish
  inter-rater reliability. Do not send the PRIVATE key to the reviewer.
- Upstream screen: exact test-function AST hashes ignoring test name and
  eight-token shingle overlap (flag generated containment>=0.5). Current scope
  Posting development only. Flags require inspection; common boilerplate can
  overlap. No flag does not prove novelty. Holdout remains unopened.
- One initial seed3407; optional second3408 if promising/ambiguous. It requires a
  separately frozen recipe/gates. No automatic seed sweep; extra seeds do not
  fix narrow evaluation-family coverage. Answer-only supervision is future work.

## Protected execution

`grade_tdd_demo_protected.py` loads pinned Posting modules from the committed
portable ZIP and checks hashes. It reuses the existing five task definitions and
faults. Each condition runs in a fresh Docker container: no network, read-only
root/source mount, nonroot user, dropped capabilities, no-new-privileges, bounded
CPU/memory/PIDs/tmpfs and30-second timeout, with named-container cleanup.
It resolves the supplied image to its immutable image ID before execution.

Correct reference must pass collected tests with no skips before mutant credit.
Mutants must preserve collected node IDs and fail through call-phase assertions;
collection/import/setup errors and timeouts are not kills. All logs and individual
condition reports are retained. Output analysis is capped; excessive output earns
no credit. Curated faults are incomplete and correlated. This is bounded execution,
not proof against malicious tests manipulating pytest/reporting; semantic
anti-cheating review remains necessary. No generated code is executed on the host.

Use Dockerfile.development with a resolved Python3.13 base-image digest. Installation
occurs at build time; evaluation containers have no network. Commands on a Docker
host (bash):

```bash
exp=experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft
docker pull python:3.13-slim
python_base=$(docker image inspect python:3.13-slim --format '{{index .RepoDigests 0}}')
docker build --build-arg PYTHON_BASE="$python_base" -f "$exp/Dockerfile.development" -t tdd-posting:v02 .
out=/workspace/tdd-demo-v02
python scripts/evaluation/grade_tdd_demo_protected.py \
  --outputs "$exp/demo-preflight-v02/executor-reference-controls.jsonl" \
  --output "$out/executor-controls" --image tdd-posting:v02
```

Control output files are authored scoring references, not model-facing requests.
Full training requires this control report to show all5 references passing and
all declared faults detected. Inspect image Python version, logs and isolation
before treating it as ready. No such Docker run has been completed locally:
Docker's Linux daemon is unavailable on this machine.

## GPU sequence

Keep training and vLLM environments separate; reuse the historical training setup
described in GPU-DEMO-HANDOFF.md. Runtime versions cannot be frozen honestly until
the actual compatible pod environment exists. Capture the lock before measured
generation, then keep that installation unchanged. Do not silently switch engines
if Qwen hybrid-model LoRA support fails. Preserve all failed diagnostics.

```bash
runner=scripts/evaluation/run_tdd_demo_gpu.py
review=scripts/evaluation/review_tdd_demo_outputs.py
grade=scripts/evaluation/grade_tdd_demo_protected.py
# vLLM environment
python "$review" lock-runtime --output "$out/inference-lock.json"
python "$runner" --mode baseline --runtime-lock "$out/inference-lock.json" --output "$out/base"
python "$grade" --outputs "$out/base/outputs.jsonl" --output "$out/base-execution" --image tdd-posting:v02
python "$review" overlap --outputs "$out/base/outputs.jsonl" --upstream /path/to/pinned/posting --output "$out/base-upstream.json"
```

Copy baseline-review-template.json from the v02 preflight outside that immutable
directory. Inspect actual base outputs, completion, overlap and execution; fill
the actual output SHA256, reviewer, headroom notes, reason, outputs_inspected and
proceed_with_diagnostic. Set execution_summary to the actual absolute path of
base-execution/summary.json. This is an evidence record, not a substitute for
inspection or an automatic user permission request.

```bash
# Training environment
python "$runner" --mode smoke --output "$out/smoke"
python "$runner" --mode tiny --output "$out/tiny"
# vLLM environment
python "$runner" --mode candidate --adapter "$out/smoke/adapter" --runtime-lock "$out/inference-lock.json" --output "$out/reload"
# Training environment: full run only after inspected gates
python "$runner" --mode full --output "$out/sft" --baseline "$out/base" \
  --smoke "$out/smoke" --tiny "$out/tiny" --reload "$out/reload" \
  --baseline-review "$out/baseline-review.json" --execution-preflight "$out/executor-controls"
# vLLM environment
python "$runner" --mode candidate --adapter "$out/sft/adapter" --runtime-lock "$out/inference-lock.json" --output "$out/candidate"
python "$grade" --outputs "$out/candidate/outputs.jsonl" --output "$out/candidate-execution" --image tdd-posting:v02
python "$review" overlap --outputs "$out/candidate/outputs.jsonl" --upstream /path/to/pinned/posting --output "$out/candidate-upstream.json"
python "$review" pair --baseline "$out/base/outputs.jsonl" --candidate "$out/candidate/outputs.jsonl" --output "$out/blinded-review"
```

The upstream path can be the extracted portable ZIP's Posting source directory,
identified by audit/sources.json. The screen verifies inventoried test hashes.

## Local verification and remaining work

Regression checks cover stop-ID mismatch, masked padding/EOS, rejection of
truncated/thinking-only/unsafe-path outputs, blind packet/accounting, exact array
preservation, no holdout requests, AST normalization and invalid fault credit.
Authored development controls screened against30 pinned upstream test files:
no overlap flags. That is a tool/data check, not model contamination evidence.

Still pending: actual Docker executor controls, compatible pinned inference
environment, GPU baseline/headroom, module inventory, smoke/tiny/reload, training,
candidate scoring/review and final holdout. No new quality scores are claimed.

Training volume is unchanged; the earlier10–20min training allowance remains
approximate. Larger decoding and protected execution add time. Reserve45–90min
for a cold first session, potentially longer if engine compatibility needs work;
no15–20min end-to-end promise. Do not rent until the owner accepts the window.
