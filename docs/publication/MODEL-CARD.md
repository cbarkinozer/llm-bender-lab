---
language:
- tr
library_name: peft
base_model: unsloth/Qwen3.5-4B
base_model_relation: adapter
pipeline_tag: text-generation
tags:
- lora
- sft
- turkish
- experimental
---

# Turkish Direct Response LoRA — F / exp016

**Release draft.** Replace repository links, choose a license after rights review,
and validate the loading example before publishing. No public Hub revision exists yet.

## Summary and intended use

A text-only LoRA adapter for Qwen3.5-4B, trained to produce concise, direct,
natural Turkish answers with less gratuitous Markdown, emoji and anthropomorphic
self-description. Answer length should remain appropriate to the task, not
universally minimal. It is an experimental candidate for conversational response
style, not a general Turkish-capability upgrade or a hallucination-free model.

Turkish summary: Daha kısa ve doğrudan Türkçe cevaplar için104 insan denetimli
örnekle eğitilmiş adaptör. Özetleme sadakati ve bazı dil bilgisi hataları sürüyor.

## Identity and lineage

- Starting checkpoint: `unsloth/Qwen3.5-4B`.
- Immutable base/tokenizer revision: `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`.
- Selected artifact: exp016/F, final optimizer step40, independently initialized
  from that base; **not** continued from E or previous adapters.
- Adapter SHA256: `7ec9b04a5ecac7a031352fb5d0db281ef018c11951a4b4862c418e2b7a002ca1`.
- Adapter config SHA256: `6f7f0480fdcf1cc32aed14a1c66981c1a454840ece4f05932b0ef338846a4335`.
- Approximately85MB adapter only. Base weights/tokenizer are not included.
- Code, effective recipe and evidence: TODO add immutable GitHub commit link.
- Dataset: TODO add Dataset Hub link and immutable dataset revision.
- License: TODO owner decision; pinned upstream card declares Apache-2.0.

The Unsloth and official Qwen checkpoint weight shards were verified byte-identical
at the recorded revisions, but configuration/tokenizer/template files differ.
Use the pinned starting repository, not a different template based on a name match.
The saved PEFT config has `revision: null`; explicitly pin base loading as below.
Original config bytes are preserved, not silently rewritten for publication.

## Training

Unsloth BF16 LoRA;104 reviewed training examples (80 repaired core +24 independent
additional scenarios);20 repeatedly used development examples. No CETVEL example
was deliberately added to training. Exact/near/group leakage audits found no
identified item-level overlap; this is not a guarantee of semantic or pretraining
independence. Historical synthetic/AI-assisted provenance has gaps; see dataset card.

| Setting | Value |
| --- | --- |
| Learning rate / scheduler | 1e-4 / cosine |
| Optimizer / clipping | adamw_8bit / max grad norm1.0 |
| Microbatch / accumulation / effective batch | 1 / 8 / 8 |
| Optimizer steps / warmup | 40 / 2 |
| Effective epochs | 3.0769; max_steps overrides nominal4 epochs |
| LoRA rank / alpha / dropout | 16 / 16 / 0 |
| Target projections | language attention q/k/v/o and MLP gate/up/down |
| Max sequence / packing | 1024 / off; no training truncation |
| Loss | final assistant response + native EOS only; earlier turns masked |
| Seed | 3407 |

Actual exposure:19131 supervised tokens,37334 input tokens,320 microbatches.
Recorded training time106.8984 seconds is **not** setup/end-to-end rental time.
See `training-config.json`; preserve original package/hardware evidence in linked code.

## Evaluation

Matched base/adapter generations, no additional system prompt, non-thinking mode,
BF16, greedy, repetition penalty1.05. The external500 cohort is source-group
sampled with100 examples each from GECTurk, TQUAD, XQuAD-TR, WMT EN→TR and MLSum-TR.
It excludes the historical700 source groups and pilot100, but does not cover all
CETVEL task families and is **not an official CETVEL leaderboard score**.

| Metric (0–100 unless counts) | Base | F |
| --- | ---: | ---: |
| GECTurk exact correction | 0/100 | 30/100 |
| TQUAD token F1 | 20.06 | 64.58 |
| XQuAD-TR token F1 | 13.68 | 55.84 |
| EN→TR corpus BLEU | 16.84 | 16.81 |
| EN→TR corpus chrF | 52.16 | 52.43 |
| MLSum-TR ROUGE-L | 18.45 | 20.93 |
| Median generated tokens | 98 | 26 |

Single-reviewer blind review:30 preselected examples, six/task, per-item shuffled
identities. Preferences F19/base6/tie2/neither3. Grades F23 pass/4 partial/3 fail;
base21/3/6. All12 reviewed QA answers passed for **both** models; all12 preferences
favored F. Much of the automatic QA gain is output compliance/shorter answers,
not evidence of new knowledge. GEC pass F4/6 versus base0/6. Translation pass5/6
each, preferences split2/2 with2 ties. Summary pass **F2/6 versus base4/6**,
preferences base4/F1/neither1: ROUGE improvement does not establish faithfulness.
The sample is small and one reviewer does not establish general superiority.

Earlier32-item project development comparison: F26 pass versus base17.
These items were repeatedly used for iterative decisions; not an unbiased final test.
The pilot100 and its20 human reviews are separate cohorts, not pooled with500.

Runtime for external evaluation: vLLM0.30.0, Torch2.13.0+cu130,
Transformers5.18.0, PEFT0.21.2, RTX4090; context8192/output4096.
Native model EOS248044 differs from tokenizer EOS248046 (`im_end`). The
recorded protocol explicitly stops on248044 (vLLM ignore_eos + explicit stop ID)
to match prior generation. Base496/500 and F499/500 terminated on that EOS;
remaining4/1 were repetition guards, retained/scored without retries. No length
or timeout terminations. Changing EOS, template, backend or thinking mode changes
the protocol; validate deployment settings rather than treating them as equivalent.

## Loading example

Illustrative native Transformers/PEFT example. The adapter was actually evaluated
through the repository's Unsloth/HF and vLLM runners, not this new snippet in a fresh
installation. Validate against those saved outputs before claiming deployment parity.
Use a compatible CUDA/PyTorch installation and Transformers5.18.0/PEFT0.21.2.

```python
import torch
from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
from peft import PeftModel

BASE = "unsloth/Qwen3.5-4B"
REVISION = "3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636"
ADAPTER = "NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1"
tokenizer = AutoTokenizer.from_pretrained(BASE, revision=REVISION)
base = Qwen3_5ForConditionalGeneration.from_pretrained(
    BASE, revision=REVISION, dtype=torch.bfloat16, device_map="auto")
model = PeftModel.from_pretrained(base, ADAPTER).eval()
messages = [{"role": "user", "content": "Yeni eve taşındım ama hâlâ misafir gibi hissediyorum."}]
ids = tokenizer.apply_chat_template(messages, tokenize=True,
    add_generation_prompt=True, enable_thinking=False, return_dict=False)
x = torch.tensor([ids], device=model.get_input_embeddings().weight.device)
with torch.inference_mode():
    y = model.generate(input_ids=x, attention_mask=torch.ones_like(x),
        do_sample=False, max_new_tokens=4096, repetition_penalty=1.05,
        eos_token_id=248044, forced_eos_token_id=None,
        pad_token_id=tokenizer.pad_token_id)
print(tokenizer.decode(y[0, len(ids):], skip_special_tokens=True))
```

This example omits the benchmark repetition/time guards; it is not a full
reproduction command. At release, pin the adapter Hub revision too.
For exact evaluation, use linked `exp-003-cetvel-500` scripts/config and source pins.

## Limitations and responsible use

No guarantee of zero hallucinations, flawless Turkish or removal of all Markdown.
Summary faithfulness can regress; translations and corrections can still be wrong.
de/da and correct-input over-correction remain concerns. Non-thinking text-only
evaluation does not establish preservation of reasoning-mode control, broad reasoning,
multimodal ability, English, safety, factual QA without context or tool use.
Do not use as an autonomous medical/legal/financial authority. Human verification
is needed where mistakes matter. This is a usable experimental style adapter,
not a certified production model or a universal capability improvement.
