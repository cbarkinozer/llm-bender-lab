---
base_model: LiquidAI/LFM3-1.7B
base_model_relation: adapter
library_name: peft
pipeline_tag: text-generation
language:
- tr
license: other
license_name: lfm1.0
license_link: LICENSE
tags:
- lfm3
- liquid
- lora
- peft
- continued-pretraining
- turkish
- research
- transformers
- custom_code
datasets:
- wikimedia/wikipedia
- HuggingFaceFW/fineweb-2
---

# LFM3-1.7B-Turkish-CPT

Turkish continued-pretraining (CPT) **LoRA research adapters** for
[LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B).
This release documents a small, single-GPU study of Turkish adaptation at
approximately **2.2M, 10M, 50M and 100M raw training tokens**.

**Main finding:** Turkish text prediction and grammatical discrimination improved
with additional CPT along this training trajectory, while instruction following,
task scores and generation termination substantially deteriorated. These are
intermediate checkpoints for further research and instruction tuning, **not a
claim of an improved general-purpose Turkish assistant**.

**The default adapter is the 100M checkpoint.** It ended normally on only 136/500
questions in the full generation evaluation; 340 reached the 4096-token limit and
24 triggered an exact-repetition guard. Use the checkpoint that fits your
research question rather than assuming that more CPT makes a better assistant.

## What is released

| Location | Nominal exposure | Exact raw tokens | Initialization |
|---|---:|---:|---|
| `checkpoints/wiki-2m2/` | 2.2M | 2,201,862 | Original starting model; independent Wikipedia-only branch |
| `checkpoints/cpt-10m/` | 10M | 9,995,322 | Original starting model; Wikipedia + FineWeb2 |
| `checkpoints/cpt-50m/` | 50M | 49,995,738 | Continue the saved 10M adapter |
| Repository root | 100M | 99,995,385 | Continue the saved 50M adapter |

All adapters load **directly onto the same original pinned starting model**.
The 50M/100M files contain the cumulative updated adapter parameters; do not
stack the earlier adapters when loading them. Full merged base weights are not
included. The 2.2M branch is separate from the 10M→50M→100M trajectory.

Starting checkpoint: **`LiquidAI/LFM3-1.7B`**, revision
`0dc4268b561499c648c7ba7c9466bf3d8d01517a`.
This is the post-trained checkpoint, **not `LiquidAI/LFM3-1.7B-Base`**.
No Turkish SFT, DPO, GRPO or rationale/thinking supervision has been applied in
this release. Training used raw text and all-token causal language-model loss.

## Language-modeling and grammar results

Lower negative log-likelihood (NLL) is better. Higher TurBLiMP accuracy is better.

| Checkpoint | Wikipedia NLL ↓ | Web NLL ↓ | TurBLiMP macro accuracy ↑ |
| --- | --- | --- | --- |
| Starting model | 3.2619 | 3.8894 | 71.75% |
| Wiki 2.2M | 2.4905 | 3.3101 | 73.19% |
| 10M | 2.3859 | 2.9850 | 80.31% |
| 50M | 2.3584 | 2.7299 | 85.12% |
| 100M | 2.3366 | 2.6178 | 86.81% |

At 100M, TurBLiMP macro accuracy increases by **15.06 percentage points** relative
to the starting model. Wikipedia NLL decreases by approximately **28.4%**, and
web NLL by approximately **32.7%**. These are benchmark-specific descriptive
changes, not equivalent percentages of improvement in Turkish ability.

**Text evaluation:** 100 held-out Wikipedia documents and 100 FineWeb2 documents,
scored separately. Scores are natural-log NLL per scored token using the pinned
tokenizer; document boundaries are respected. Windows have length 2048 with
2047 target tokens; no BOS/EOS is inserted, and the first token of each document
is unscored. Exact scored-token counts and data hashes are in `evaluation/`.
The web evaluation is a convenience sample from a pinned FineWeb2 TEST shard;
it is not a population estimate of Turkish web quality.

**Grammar evaluation:** a cleaned 1600-pair subset of
[TurBLiMP](https://huggingface.co/datasets/juletxara/turblimp), 100 pairs for each
of 16 phenomena. The grammatical sentence must receive strictly greater summed
log probability than its ungrammatical counterpart; BOS is included and EOS is
not. Ties count as incorrect. The reported number is the mean of the 16
phenomenon accuracies. This measures grammatical discrimination, **not free-form
grammar-correction accuracy**. Likelihood evaluation uses the unmerged LoRA
model; generation below uses a BF16 merge, which can change rounding.

## Instruction-following and task regressions

### Matched 100-question screening

The following four models were evaluated on exactly the same 100 questions:
20 each for GECTurk correction, TQUAD QA, Turkish XQuAD QA, English→Turkish
translation, and MLSUM-TR summarization. The 2.2M branch was evaluated under a
different earlier generation protocol and is intentionally omitted from this
matched generation table.

| Checkpoint | TQUAD F1 ↑ | XQuAD F1 ↑ | Translation chrF ↑ | Summary ROUGE-L ↑ | EOS /100 | Length /100 | Loop guard /100 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Starting model | 0.1306 | 0.0891 | 32.27 | 0.1431 | 100 | 0 | 0 |
| 10M | 0.0157 | 0.0138 | 15.28 | 0.0226 | 53 | 44 | 3 |
| 50M | 0.0016 | 0.0019 | 6.29 | 0.0077 | 36 | 60 | 4 |
| 100M | 0.0053 | 0.0034 | 2.69 | 0.0131 | 26 | 65 | 9 |

F1 and ROUGE-L are fractions in [0,1]; chrF uses its usual 0–100 scale. These
reference-overlap metrics are not interchangeable or a pooled accuracy measure.
GECTurk exact match was 0 for all four models; the scorer flagged 19–20 outputs
per model as verbose/format-failure candidates. Exact match can miss valid
alternative corrections, and overlap metrics alone do not establish factuality
or faithfulness. Normal EOS termination does not establish correctness.

**Identical generation configuration:** temperature 0.1, top_k 50, top_p 1.0,
repetition_penalty 1.1, 4096 maximum new tokens, 8192-token context, seed 3407,
continuous batch size 4, BF16, native tokenizer/chat template, thinking disabled.
The frozen guard aborts exact repeated 8/16/32-token blocks occurring four times
consecutively after at least 128 generated tokens. A 180-second per-request
timeout is also retained; all failures remain in scoring.

The backend is experimental vLLM
`0.34.0rc1.dev251+g7cc0a8a2b`, eager execution, prefix caching disabled. Fixed
seeds do not guarantee bitwise reproducibility; batching can affect outputs.
The same settings and engine packages were used for all four screening models.
Earlier greedy/rp 1.15 or rp 1.05 results must not be mixed into this comparison.

### Full 500-question evaluation of 100M

The 100M adapter was also evaluated on the entire existing 500-question cohort,
100 questions per task, with the same generation settings. **No new matched
500-question starting-model run is claimed here.**

| Measure | 100M, 500 questions |
| --- | --- |
| TQUAD F1 | 0.007048 |
| XQuAD F1 | 0.000650 |
| Translation chrF | 3.0096 |
| Summary ROUGE-L | 0.012760 |
| GECTurk exact match | 0.0 |
| Normal EOS | 136 /500 |
| Output limit | 340 /500 |
| Exact-loop guard | 24 /500 |

The full generation run took **41.94 minutes**, excluding loading, scoring and
backup. All 500 outputs were retained, including truncations and guarded loops.
The 100-question screening is a subset of these 500 questions; the 500-question
rerun changes order/batch composition, so overlapping outputs are not guaranteed
to be token-identical. This is not an independent replication.

## Data and training recipe

Training data:

- Turkish Wikipedia snapshot `20231101.tr` from
  [wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia),
  revision `b04c8d1ceb2f5cd4588862100d08de323dccfbaa`.
  The training subset contains 3000 documents and 2,201,862 raw tokens.
- Turkish `tur_Latn` TRAIN data from
  [HuggingFaceFW/fineweb-2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2),
  revision `af9c13333eb981300149d5ca60a8e9d659b276b9`, using four pinned shards
  `data/tur_Latn/train/000_00000.parquet` through `000_00003.parquet`.
  The 10M run adds 6466 documents / 7,793,460 raw web tokens. Later phases add
  39,184 documents / 40,000,416 tokens and 49,614 documents / 49,999,647 tokens.

The cumulative mixture is measured with the pinned LFM3 tokenizer, before
trainer-added EOS tokens:

| Checkpoint | Wikipedia tokens | FineWeb2 tokens | Wikipedia share |
|---|---:|---:|---:|
| Wiki 2.2M | 2,201,862 | 0 | 100% |
| 10M | 2,201,862 | 7,793,460 | 22.03% |
| 50M | 2,201,862 | 47,793,876 | 4.40% |
| 100M | 2,201,862 | 97,793,523 | 2.20% |

**Dataset distribution:** use the original dataset links above; no duplicate
dataset or raw corpus is published here. This model card, pinned source
revisions, selection code and provenance describe our mixture. Proportions
alone do not reproduce the exact selected documents: filtering, exclusions,
sampling order and tokenizer budget accounting also matter. Inclusion of a
source in this recipe does not relicense its text.

Selection includes language-score/prose/length/repetition heuristics, web-host
caps, exact-document and long-paragraph exclusions, and five-word overlap
checks against protected evaluation text. The continuation uses approximate
cross-training duplicate candidate retrieval followed by exact five-word
containment checks; it does **not** guarantee exhaustive semantic deduplication.
The 90M continuation excludes parent-corpus replay and uses additional
review-informed spam/download/commercial-template exclusions. Review was an
agent-assisted sample review, not independent human certification.

The training sample is a bounded shuffled frame of four web shards, not a
representative or equally balanced sample of Turkish domains. Wikipedia and web
pages can contain errors, offensive text, personal information and residual
boilerplate; factual correctness and privacy removal are not certified.
Source corpora and benchmark texts are not redistributed in this model repo.
Their upstream terms and attribution requirements remain applicable.

| Setting | Value |
|---|---|
| Method | LoRA continued pretraining, raw-text all-token causal loss |
| Precision | BF16, no quantization |
| LoRA | Rank 64, alpha 64, dropout 0; no bias training |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `in_proj`, `out_proj`, `w1`, `w2`, `w3` |
| Embeddings / output head | Frozen |
| Sequence length / packing | 2048 / wrapped packing |
| Microbatch / accumulation | 2 / 4; effective batch 8 packed sequences |
| Epochs | One per phase |
| Optimizer | Fused AdamW, betas 0.9/0.999, epsilon 1e-8, weight decay 0 |
| Schedule | Cosine, 5% warmup; max gradient norm 1 |
| Peak LR | 2e-4 for 2.2M/10M; 1e-4 for each later continuation phase |
| Seed | 3407 |
| Hardware | Single NVIDIA RTX 4090, 24GB VRAM |
| Checkpoint selection | Last completed epoch, not best benchmark score |

| Phase | Added raw tokens | Runtime (minutes) | Trainer token exposure |
| --- | --- | --- | --- |
| wiki-2m2 | 2,201,862 | 5.82 | 2,204,862 |
| cpt-10m | 9,995,322 | 26.39 | 10,004,788 |
| cpt-50m | 40,000,416 | 105.82 | 40,039,600 |
| cpt-100m | 49,999,647 | 132.34 | 50,049,261 |

Times are Trainer-reported full-phase runtime; they exclude corpus preparation,
model loading, separate smoke/overfit diagnostics, evaluation and transfers.
Trainer token counts include EOS/packing accounting and differ from the raw
corpus counts above. The 50M and 100M runs use **fresh optimizers and restarted
phase-local schedules**. New exposure after 10M is web-only, so cumulative
Wikipedia proportion decreases. Consequently **token quantity, source mixture,
learning rate, filtering and schedule are confounded**: this is a descriptive
trajectory, not a controlled token-scaling experiment. The independent 2.2M
Wikipedia branch is also not a token-only comparator for 10M.

## Loading an adapter

Use a Transformers release with LFM3 support. The recorded training environment
used Transformers 5.20.2, PEFT 0.21.2, TRL 1.16.0 and PyTorch 2.14.1. These are
recorded versions, not a claim that older releases cannot work. Experimental
vLLM was used only for generation evaluation. See `reproducibility/` for exact
environment records, metric summaries, source hashes and recipe files.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_id = "LiquidAI/LFM3-1.7B"
base_revision = "0dc4268b561499c648c7ba7c9466bf3d8d01517a"
adapter_id = "cbarkinozer/LFM3-1.7B-Turkish-CPT"

tokenizer = AutoTokenizer.from_pretrained(base_id, revision=base_revision)
base = AutoModelForCausalLM.from_pretrained(
    base_id,
    revision=base_revision,
    code_revision=base_revision,
    trust_remote_code=True,  # Review the upstream custom code before enabling.
    dtype=torch.bfloat16,
    device_map="auto",
)
model = PeftModel.from_pretrained(base, adapter_id).eval()  # Default: 100M
# To load 10M instead, load onto a fresh base with:
# model = PeftModel.from_pretrained(
#     base, adapter_id, subfolder="checkpoints/cpt-10m"
# ).eval()

# Raw continuation demonstrates the CPT objective; assistant behavior is degraded.
inputs = tokenizer("Türkçe,", return_tensors="pt").to(model.device)
with torch.inference_mode():
    output = model.generate(
        **inputs, max_new_tokens=128, do_sample=True,
        temperature=0.1, top_k=50, top_p=1.0,
        repetition_penalty=1.1,
        eos_token_id=124900, pad_token_id=tokenizer.pad_token_id,
    )
print(tokenizer.decode(output[0, inputs.input_ids.shape[1]:], skip_special_tokens=True))
```

This example is for raw continuation, **not the benchmark prompt protocol**.
For chat, use the pinned tokenizer's native `apply_chat_template` with
`enable_thinking=False`; do not invent a separate Turkish chat template.
The adapters are safe-tensor files. Adapter integrity, tensor shapes and finite
values were checked locally before publication; a fresh local end-to-end GPU
reload was not performed during publishing. The recovered checkpoint was loaded
and evaluated on the training pod before shutdown. Do not load multiple
cumulative checkpoints as stacked adapters.

## Limitations and intended use

- **Research / subsequent SFT:** evaluate Turkish language adaptation, grammar,
  retention and instruction-tuning recovery. Not recommended as a finished
  conversational assistant, factual authority, or high-stakes decision system.
- **Single seed and trajectory:** no training-seed variance estimate, confidence
  intervals, significance claim or universal optimal-token-budget claim.
- **Small screening cohort:** 20 questions/task is noisy. The 500 cohort has been
  repeatedly inspected and is development/comparison evidence, not a pristine
  final holdout. A fresh final test is needed for new generalization claims.
- **Possible pretraining contamination:** excluding our CPT/eval overlaps does
  not establish that the starting model never saw public benchmark/corpus text.
- **Narrow scope:** no matched English-retention/safety/bias audit; higher
  grammar accuracy or lower NLL does not establish safe, truthful or helpful
  assistant behavior. Instruction degradation is observed; its precise mechanism
  (e.g. forgetting versus behavior shift) has not been isolated.
- **No equal-domain-balance claim:** host caps are not topic labels or
  registrable-domain caps. Filtering and approximate deduplication have limits.
- **Future work:** compare starting-model+SFT against CPT+the same SFT, with
  matched evaluation, to test whether the language-modeling gains are useful
  after instruction-following recovery. That result is not available yet.

## Provenance, attribution and license

Released by **Barkin Ozer / cbarkinozer** as an independent experiment; no
affiliation with or endorsement by Liquid AI is implied. Liquid AI developed
the original model. Wikipedia contributors and FineWeb2 maintainers/web-content
authors provided the source material; benchmark creators retain their respective
rights. See dataset links and pinned manifests for provenance.

The upstream **LFM Open License v1.0** is included verbatim as `LICENSE`. It is a
custom license with a commercial-use revenue threshold; do not treat this
release as Apache 2.0/MIT or as unrestricted commercial permission. See the full
license for applicable terms. `NOTICE` describes this release's modifications.
No source model license or attribution has been removed. Original tokenizer
files are copied unchanged; trained adapter weights and release documentation
are the modifications. Published adapter configs additionally pin the original
model revision; that metadata change does not alter adapter tensors.

Checksums are provided in `SHA256SUMS` (all payload files except the checksum
file itself). Machine-readable results, token exposure, package versions and
checkpoint lineage are under `evaluation/` and `reproducibility/`. The build
script and study code are maintained in
[llm-bender-lab](https://github.com/cbarkinozer/llm-bender-lab).
The release contains no access tokens, private keys, optimizer pickles,
raw web/Wikipedia corpora, raw benchmark prompts or generated-answer transcripts.

### Training run records

- [wiki-2m2](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/aze747zg)
- [cpt-10m](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/jnupc6oq)
- [cpt-50m](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/4ubsysj7)
- [cpt-100m](https://wandb.ai/c-barkinozer/lfm3-turkish-post-training/runs/311vl5n7)

Run dashboards may require access; the included JSON summaries do not.
