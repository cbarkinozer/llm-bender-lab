# Inference diagnosis — 2026-10-29

No new SFT has run. The original128-output matrix is complete. The later uniform
16k greedy rerun was interrupted after18 saved attempts because traces exposed
repeated paragraphs, not sustained progress on difficult questions. Preserve
both evidence series; no benchmark score is inferred from runtime counts.

## Latest finding: BF16 GGUF did not resolve the selected failure

The base BF16 GGUF reference completed me079 naturally after3535 tokens, using
the exact request from the Q4 presence0/repetition1.10 diagnostic. It still
misinterpreted the short extraction task, produced an irrelevant discussion of
tax/data-sharing administration and had unnatural Turkish. This single case
does not isolate every cause, but rules out “just increase weight precision” as
an established solution for this observed failure.

GGUF is a container and supports BF16; these latest weights were not Q4. The
llama.cpp/Metal runtime, conversion and the model/sampler remain possible
contributors. Next useful reference is the original pinned safetensors model
under native Transformers/Unsloth BF16, initially a few fixed diagnostic cases.
A4090 is a practical inference/training host, not an assumed accuracy fix. No
paid instance has been provisioned. Avoid more large local parameter sweeps.

## Observed failures

- me079 asks which rules changed in a sentence contrasting unchanged tax with
  changed data-sharing rules. The greedy trace repeatedly invents a need for
  external context; its need-context wording occurs61 times. Final answer absent.
- me090 explicitly requests listening rather than advice. The greedy trace
  repeatedly drafts a response, then restarts; “Okay, I'll write it” occurs78 times.
- me049 repeats explanations and response planning, then emits an excessively
  long answer with unsupported mechanisms. Some final text exists despite cap.

These traces do not establish a need for a larger reasoning budget. The earlier
decision to expand the allowance should have followed trace inspection first.
Greedy decoding is a plausible contributor; the precise cause is not isolated.

## Representation checks

All64 unique original rendered prompts have exactly identical token IDs between
the pinned Hugging Face tokenizer and the loaded llama.cpp GGUF tokenizer. All128
original responses also have matching evaluated prompt-token counts. Evidence:
external `prompt-tokenizer-parity.json`. This rules out that specific tokenization
mismatch; it does not prove every model conversion/backend operation is correct.

The two matched GGUFs share exact tensor names/shapes/quantization types,
vocabulary/token types and chat template. Source/weight hashes are recorded.

## Bounded diagnostics, not benchmark scores

Three selected problematic items, me049/me079/me090, are run on base and Occam.
Qwen's general-task thinking recipe is the reference: temperature1.0, top_p0.95,
top_k20, min_p0, presence1.5, repetition1.0. Output4096/context20480, seed3407.
Source: https://huggingface.co/Qwen/Qwen3.5-4B#quickstart.

1. `sampling-diagnostic-v1`: repetition1.0, presence1.5. Completed6 attempts;
   four naturally terminated, two reached4096 without final answers. Assistant
   inspection found substantial unsupported content/awkward Turkish in some
   completed answers. Do not call natural termination success or accuracy.
2. `sampling-diagnostic-repeat110-v1`: owner-requested modest repetition increase
   to1.10; all other settings fixed. In progress at this update. First completed
   answer terminated earlier but still had badly distorted Turkish and invented
   terminology. This is an observation, not a completed comparative conclusion.
3. `sampling-diagnostic-presence0-v1`: queued after condition2, same repetition1.10
   and sampling, presence reduced to0. Four attempts: me049/me079 on both models.
   This probes whether a strong presence penalty over the long window contributes
   to degraded phrasing. It is a hypothesis until outputs are inspected.

Runs are sequential; exact old diagnostic source bytes are preserved beside
their manifests before parameterization code changes. Returned sampler settings
are checked in newer conditions. No completed wrong answer is silently replaced.

The full benchmark is stopped pending diagnosis. If a usable recipe is chosen,
freeze it for all applicable conditions and rerun consistently; keep older
greedy and sampled conditions separate. Do not begin model training to compensate
for an unvalidated inference configuration.
