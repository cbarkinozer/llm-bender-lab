---
license: apache-2.0
base_model: Qwen/Qwen3.5-0.8B
library_name: transformers
tags:
- ml-intern
- weight-space-programming
---

# Qwen3.5-0.8B, edited by an LLM with no training (Weight-Space Programming)

[![Built with ML Intern](https://huggingface.co/datasets/huggingface/badges/resolve/main/built-with-ml-intern-sm.svg)](https://hf.co/chat?mode=ml-intern)

This is the edited model from Experiment 8 of **["Sparks of Weight-Space Programming"](https://rikiyat.github.io/blog/weight-space-programming/)**.
We asked a frontier LLM ("Astra") to make Qwen3.5-0.8B better at math by editing its weights directly,
with no gradient descent and no training. Working in a Python session over the weights, with a budget of
50 forward passes on practice problems from the GSM8K and MATH training sets, Astra traced the base
model's thinking loops to one direction written by the MLPs of layers 15 and 19, and subtracted it from
64 output columns of `down_proj` in each layer (131,072 weights, 0.016% of the model).

The base model loops until the token limit on almost every math problem. The edited one mostly doesn't.

**🎮 Try it live:** [akhaliq/weight-space-programming-demo](https://huggingface.co/spaces/akhaliq/weight-space-programming-demo) —
type a problem, watch the base model loop while the edited one solves it.

## Results

From the post (thinking on, up to 32,768 tokens, several samples per problem):

| Qwen3.5-0.8B | MATH-500 (%) | GSM8K (%) | IFEval (%) | Hit token limit (%) |
|---|---|---|---|---|
| Base | 7.9 | 13.8 | 21.0 | 93.0 |
| **Edited (this model)** | **48.1** | **67.1** | **62.3** | **33.1** |

**Independent re-run of this checkpoint:** full MATH-500, 500 problems × 4 samples = 2,000 generations
(43.4M generated tokens, 51 min on an H200), with the post's protocol: vLLM, thinking on, temperature 0.6,
top_p 0.95, top_k 20, presence_penalty 1.5, max 32,768 new tokens, seed 0, last `\boxed{}` graded with
math-verify 0.9.0. The edited model scored **51.0%**, with **31.6%** of answers hitting the token limit.
A 25-problem smoke test of the base model gave 5.0%, with 95% hitting the limit.
Raw scores, per-problem results and sample generations:
[`eval/`](https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming/tree/main/eval).

## Verifying the weights

Astra's edit is published as a bit-exact diff in
[`RikiyaT/lm_understand-logs`](https://github.com/RikiyaT/lm_understand-logs) (`exp8_math/runs/p50c/edit/`).
This checkpoint was rebuilt with `exp8_math/code/apply_edit.py`, which **sha256-verifies every rebuilt
tensor against the checkpoint evaluated in the post**. Only these two tensors differ from
`Qwen/Qwen3.5-0.8B` @ `2fc06364715b967f1860aea9cf38778875588b17`:

| Tensor | sha256 of the raw bfloat16 bytes |
|---|---|
| `model.language_model.layers.15.mlp.down_proj.weight` | `82e2d733ea64feaeb4af93a1e065641d3df98b494a8b7576ef2f52e90fe2ee53` |
| `model.language_model.layers.19.mlp.down_proj.weight` | `8ef3c61bc36af113ad58e89dbb0a4a14dcba5a45cb750c15ab515c82ddd12eb2` |

## Reproduction

This checkpoint and the re-run above were built by [akhaliq](https://huggingface.co/akhaliq) with
[ML Intern](https://hf.co/chat?mode=ml-intern) on Hugging Face Jobs, 2026-11-02: the edit was rebuilt and
hash-verified on CPU, and the benchmark run on an NVIDIA H200 with vLLM 0.33.0 / transformers 5.20.2 /
math-verify 0.9.0, following `exp8_math/code/evaluate.py` (thinking on, `think35` sampling,
last-`\boxed{}` grading). One substitution: the post evaluated a text-only export of the model, and this
checkpoint is the full multimodal release. The language-model tensors are identical (hash-verified), and
text prompts do not use the vision tower.

## Usage

```python
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

ckpt = "RikiyaT/Qwen3.5-0.8B-weight-space-programming"
tok = AutoTokenizer.from_pretrained(ckpt)
llm = LLM(model=ckpt, dtype="bfloat16", max_model_len=34816)

prompt = tok.apply_chat_template(
    [{"role": "user", "content": "What is $2^{10} + 24$?\nPlease reason step by step, and put your final answer within \\boxed{}."}],
    tokenize=False, add_generation_prompt=True, enable_thinking=True)
sp = SamplingParams(n=1, temperature=0.6, top_p=0.95, top_k=20, presence_penalty=1.5,
                    max_tokens=32768, seed=0)
print(llm.generate([prompt], sp)[0].outputs[0].text)
```

## Provenance

- Blog post: https://rikiyat.github.io/blog/weight-space-programming/
- Logs, diffs, and rebuild code: https://github.com/RikiyaT/lm_understand-logs (`exp8_math/`, CC BY 4.0 / MIT)
- Demo: [akhaliq/weight-space-programming-demo](https://huggingface.co/spaces/akhaliq/weight-space-programming-demo)
- Re-run (this repo's `eval/`): MATH-500 (HuggingFaceH4/MATH-500), math-verify 0.9.0
- Base model: [Qwen/Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B), Apache 2.0
