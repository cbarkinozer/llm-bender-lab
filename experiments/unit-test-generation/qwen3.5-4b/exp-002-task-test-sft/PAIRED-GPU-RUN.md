# Current GPU entry point: shared baseline, rationale-loss A/B

The local pair implementation supersedes NEXT-SESSION.md's historical pending-B
checklist. Active preparation: paired-preflight-v01/A and /B. Previous v01–v03
single-arm artifacts remain unchanged. No baseline/model/GPU run has occurred.

Both arms use50 identical conversations, input IDs, attention masks, order/seed,
three epochs, BF16 LoRA rank/alpha16, LR1e-4, batch1/accumulation8, cosine/warmup2,
AdamW8bit and max3072 training sequence. Each starts from the fresh pinned base.

| Per epoch | A | B |
|---|---:|---:|
| Input tokens | 91,858 | 91,858 |
| Supervised tokens | 17,266 | 15,847 |
| Rationale tokens masked | 0 | 1,419 |

All1,419 removed labels belong exclusively to rationale-text tokens. Zero tokens
cross rationale/markup boundaries in these50 examples. Prompt masks, answer,
delimiters and EOS are preserved. B still sees teacher-forced rationale input;
this measures direct rationale supervision holding input exposure equal, not
rationale-free training. Different supervised-token exposure remains part of
the contrast. This is one seed per arm, not a robust causal/generalization claim.

Shared inference: greedy0, repetition_penalty1.15 (historical study starting
point),8192 output,9216 total context, pinned native thinking-enabled template.
The scalar study settings are reused; reserved-family examples/source are not.
If the baseline pilot requires a change, create a new common protocol and rerun
baseline before either arm. Report repetitive degeneration separately from long
progressive reasoning and from other incompletion. No hidden per-arm tuning.

## Loss and evidence isolation

The runner computes summed shifted-token CE in128-token chunks divided by the
actual nonignored token count across the accumulation group. Labels are stored
unshifted; the explicit loss shifts them once. This single-GPU path requires
returned logits and logs every supplied denominator. The actual pod's Unsloth/
Trainer implementation still must pass smoke; do not bypass failures or infer
GPU memory use from the small CPU tests. Logits can increase peak memory versus
the old fused-loss recipe. OOM requires diagnosing/refreezing a common recipe,
not silently changing one arm.

Local tests verify that accumulated loss/gradients equal a global token mean;
the synthetic CPU Trainer test checks the actual supplied denominators and
one-step SGD parameter update, guarding against double accumulation scaling.
This does not prove the different pinned GPU stack preserves that behavior.

Baseline reuse is keyed to model+inference+exact request hash. A/B share that
identity. Smoke/tiny/reload and adapter provenance remain bound to the complete
arm recipe hash. An A smoke/reload cannot unlock B training. Shared baseline
review must link the actual protected execution report and output SHA256.

## Start with a pod, then pass runtime checks

One visible RTX4090 24GB; persistent /workspace with enough disk for separate
training/inference environments and model caches (allow80GB). Preserve artifacts
before termination. Setup/package references and Docker instructions remain in
GPU-DEMO-REVIEW-REVISION.md; use the arm paths below instead of v02/v03 defaults.
Docker must be available on this or a separate CPU host for protected scoring.
The current local Docker daemon is unavailable. No generated code runs on host.

Use separate compatible Unsloth and vLLM environments. Confirm LoRA support,
native stops, model revision, driver and logits-memory behavior before full runs.
Freeze the resolved inference installation in inference-lock.json; reuse it.
No hardware/runtime compatibility success is claimed before these checks.

```bash
exp=experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft
out=/workspace/tdd-pair-v01
runner=scripts/evaluation/run_tdd_demo_gpu.py
review=scripts/evaluation/review_tdd_demo_outputs.py
grade=scripts/evaluation/grade_tdd_demo_protected.py
mkdir -p "$out"
# Docker controls (build tdd-posting:v02 as documented in the revision handoff)
python "$grade" --outputs "$exp/paired-preflight-v01/A/executor-reference-controls.jsonl" --output "$out/executor-controls" --image tdd-posting:v02
# vLLM environment: one common baseline
python "$review" lock-runtime --output "$out/inference-lock.json"
python "$runner" --preflight "$exp/paired-preflight-v01/A" --mode baseline --runtime-lock "$out/inference-lock.json" --output "$out/base"
python "$grade" --outputs "$out/base/outputs.jsonl" --output "$out/base-execution" --image tdd-posting:v02
```

Inspect baseline outputs, completion/degeneration, overlap screen and execution
before proceeding. Fill paired-baseline-review-template.json outside the frozen
preflight, save as $out/baseline-review.json, linking real outputs and execution.
An agent may perform the inspection within the authorized task; this is not an
extra mandatory user approval. If there is no informative headroom, stop/replan.

```bash
# Training environment
for arm in A B; do
  python "$runner" --preflight "$exp/paired-preflight-v01/$arm" --mode smoke --output "$out/$arm-smoke"
  python "$runner" --preflight "$exp/paired-preflight-v01/$arm" --mode tiny --output "$out/$arm-tiny"
done
# vLLM environment
for arm in A B; do
  python "$runner" --preflight "$exp/paired-preflight-v01/$arm" --mode candidate --adapter "$out/$arm-smoke/adapter" --runtime-lock "$out/inference-lock.json" --output "$out/$arm-reload"
done
# Training environment: separate fresh base loads, arm-specific gates
for arm in A B; do
  python "$runner" --preflight "$exp/paired-preflight-v01/$arm" --mode full --output "$out/$arm-sft" --baseline "$out/base" --smoke "$out/$arm-smoke" --tiny "$out/$arm-tiny" --reload "$out/$arm-reload" --baseline-review "$out/baseline-review.json" --execution-preflight "$out/executor-controls"
done
# vLLM environment and Docker scoring
for arm in A B; do
  python "$runner" --preflight "$exp/paired-preflight-v01/$arm" --mode candidate --adapter "$out/$arm-sft/adapter" --runtime-lock "$out/inference-lock.json" --output "$out/$arm-candidate"
  python "$grade" --outputs "$out/$arm-candidate/outputs.jsonl" --output "$out/$arm-execution" --image tdd-posting:v02
  python "$review" pair --baseline "$out/base/outputs.jsonl" --candidate "$out/$arm-candidate/outputs.jsonl" --right-label "arm_$arm" --output "$out/base-vs-$arm"
done
python "$review" pair --baseline "$out/A-candidate/outputs.jsonl" --candidate "$out/B-candidate/outputs.jsonl" --left-label arm_A --right-label arm_B --output "$out/A-vs-B"
```

Also run the upstream-overlap screen on base/A/B using the extracted pinned
Posting source. Hide rationales and private pairing keys from graders; allow ties.
Report all-task usable-test counts, reference passes, individual fault outcomes
and qualitative evidence. Do not pool unlike supporting probes or imply N=5 is
a reliable population estimate. Holdout stays unopened until final design freeze.

## Time allowance

Two training arms roughly20–40min from the earlier unmeasured extrapolation.
Setup, downloads, baseline/reload/candidate thinking output and Docker checks add
time. Reserve roughly1–2hours for a fresh first session; compatibility work or
long generations can exceed that. Revise ETA from actual baseline/smoke timing.
No15–20min end-to-end promise and no GPU rented by this preparation.
