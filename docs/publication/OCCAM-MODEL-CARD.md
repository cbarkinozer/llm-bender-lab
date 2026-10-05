C:\Users\cbark\AppData\Roaming\Python\Python312\site-packages\huggingface_hub\file_download.py:138: UserWarning: `huggingface_hub` cache-system uses symlinks by default to efficiently store duplicated files but your machine does not support them in C:\Users\cbark\.cache\huggingface\hub\models--cbarkinozer--Qwen3.5-4B-Turkish-Concise-Lora. Caching files will still work but in a degraded version that might require more space on your disk. This warning can be disabled by setting the `HF_HUB_DISABLE_SYMLINKS_WARNING` environment variable. For more details, see https://huggingface.co/docs/huggingface_hub/how-to-cache#limitations.
To support symlinks on Windows, you either need to activate Developer Mode or to run Python as an administrator. In order to activate developer mode, see this article: https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development
  warnings.warn(message)
---
license: apache-2.0
language:
- tr
library_name: peft
base_model: Qwen/Qwen3.5-4B
base_model_relation: adapter
pipeline_tag: text-generation
tags:
- lora
- sft
- turkish
- experimental
datasets:
- cbarkinozer/Occam-Turkish-Response-SFT
---

# Occam — Qwen3.5-4B Turkish Concise LoRA

![Occam](https://cdn-uploads.huggingface.co/production/uploads/64c77dd4c96a10fa8582bcb1/4LUgApevMwrrRPO0Go8TP.png)

An experimental LoRA adapter for more concise, direct Turkish responses. Trained on **104 human-reviewed examples** and evaluated against the base model on a **500-example CETVEL-derived subset**, including **30 blind human comparisons**.

## Summary

Occam adapts `Qwen3.5-4B` toward natural Turkish responses with less unnecessary Markdown, emoji, and anthropomorphic self-description.

The goal is **appropriate concision**, not making every answer short. Explanations should preserve the information needed to answer the question.

The evaluation supports a response-style improvement, particularly for direct, context-grounded answers. It does **not** establish a general improvement in Turkish proficiency, reasoning, or factual knowledge. **Summarization faithfulness remains a significant limitation.**

**Türkçe özet:** Occam, daha kısa, doğrudan ve doğal Türkçe yanıtlar için 104 insan denetimli örnekle eğitilmiş deneysel bir LoRA adaptörüdür. Değerlendirmede yanıt biçimi ve doğrudanlık açısından kazanımlar görülmüştür; özetleme sadakati ve bazı dil bilgisi hataları hâlâ sınırlamalardır.

## Model information

| Item | Value |
| --- | --- |
| Base model family | `Qwen/Qwen3.5-4B` |
| Adapter type | PEFT LoRA |
| Training framework | Unsloth |
| Training precision | BF16 |
| Training examples | 104 |
| Development examples | 20 |
| Adapter size | Approximately 85 MB |
| License | Apache-2.0 |

The adapter was trained directly from the base model, not continued from another adapter. Base-model weights and tokenizer files are **not included**.

Training and evaluation used the Unsloth distribution of this model. Although the recorded Unsloth and official Qwen weight shards were byte-identical, their configuration, tokenizer, and chat-template files differed. Exact reproduction requires the Unsloth repository and revision recorded below; substituting the official repository's defaults has not been validated.

## Examples: direct answers with less unnecessary decoration

These three cherry-picked illustrations use actual saved base and adapter outputs from previously used project-development items. They are not training targets or independent evidence of generalization. Both models received the same prompts and generation settings. Only trailing whitespace is omitted; Markdown and emojis in the base responses are preserved.

### 1. Answer the question instead of inventing a troubleshooting context

Source item: `me-070`.

**Prompt**

> Üçüncü denemede işlem başarılı oldu. Önceki iki denemenin neden başarısız olduğunu biliyor muyuz?

**Base model**

<details>
<summary>Read the full base response: multiple headings, lists and speculative explanations</summary>

```text
Evet, bu çok önemli bir soru ve genellikle yapay zeka modellerinin (ve insanların) öğrenme süreçlerinde karşılaşılan en kritik noktalarından biridir.

Ancak, **şu anki konuşmamızın bağlamına veya geçmişteki spesifik denemelerinizin detaylarına erişimim yok.** Ben bir yapay zeka modeli olarak, sadece sizin bana bildirdiğiniz veya bu sohbet penceresinde paylaştığınız verilerle çalışıyorum. Eğer önceki iki deneme başarısız olduysa, o başarısızlıkların nedenini şu anki bu cümleyle birlikte analiz edemem; çünkü o olayların "loglarını" veya "hatalarını" hatırlamıyorum.

Bunun yerine, üçüncü denemenizin başarılı olmasının arkasındaki muhtemel mantığı ve önceki denemelerin başarısız olma sebeplerini **genel bir çerçevede** şöyle özetleyebilirim:

### 1. Nedenler Neler Olabilir?
Önceki denemelerin başarısız olması, genellikle şu senaryolardan biriyle ilgilidir:
*   **Yetersiz Veri veya Kontekst:** Modelin soruyu tam olarak anlaması için gereken tüm bilgileri veya bağlamı almamış olabilir.
*   **Hatalı Prompt Yapısı:** Soru veya talimatın net olmaması, modelin yanlış yönlendirilmesine neden olmuş olabilir.
*   **Karmaşık Çıktı Beklentisi:** Modelin üreteceği çıktı formatının (örneğin JSON, tablo, belirli bir dil) teknik kısıtlamaları nedeniyle sağlanamamış olabilir.

### 2. Üçüncü Deneme Başarılı Oldu Demektir Ne?
Üçüncü denemenizin başarılı olması, muhtemelen şu değişikliklerin yapıldığını gösterir:
*   **İterasyon ve Düzeltme:** İlk hatalar tespit edilip, prompt'un veya yaklaşımın revize edildiği.
*   **Doğru Bağlamın Sağlanması:** Modelin işlemini gerçekleştirebilmesi için eksik parçaların tamamlandığı.
*   **Testin Doğrulanması:** Sonuçların beklenen çıktıyla eşleştiği ve doğrulandığı.

### Nasıl İlerleyelim?
Bu süreci tam olarak anlamamız ve gelecekte benzer sorunlarla karşılaşmamamız için şunları yapmamızı öneririm:

1.  **Önceki Hataları Paylaşın:** Eğer önceki iki denemedeki hata mesajlarını, beklenen çıktıyı ilettiğiniz sonucu veya modelin verdiği yanıtı paylaşabilirseniz, nedenlerini analiz edebiliriz.
2.  **Başarılı Denemenin Farkını Belirtin:** Üçüncü denemede neleri değiştirdiniz? (Örneğin: Daha fazla örnek verdiniz mi? Prompt'u daha net yazdınız mı?)
3.  **Gelecek Adımlar:** Bu başarıyı nasıl ölçeklendireceksiniz veya sonraki adımda ne yapmayı planlıyorsunuz?

Eğer bu bir kodlama, veri analizi veya özel bir görevle ilgiliyse, o görevin detaylarını buraya yazarsanız, önceki denemelerin neden başarısız olabileceğine dair **spesifik ve teknik bir analiz** yapabilirim.
```

</details>

**Occam**

> Hayır, önceki iki denemenin neden başarısız olduğunu bilmiyoruz.

The base gives a long, Markdown-heavy response and assumes an AI/prompting context the user never supplied. Occam answers the actual question in one sentence without inventing an explanation. This illustrates the intended response-style change, not a guarantee that every short answer is better or that all unnecessary Markdown has been eliminated.

### 2. Respect a request to talk without unsolicited advice or celebration

Source item: `me-090`.

**Prompt**

> Sınavdan kaldım. Şu an tavsiye değil sadece anlatmak istiyorum.

**Base model**

```text
Tamam, anladım. Sınavdan çıkışın için tebrik ederim! 🎉

Şu an sadece deneyimlerini, hislerini veya süreci paylaşmak istiyorsan, buradayım. Ne hakkında konuşmak istersin?

*   Sınavın kendisi mi?
*   Sonuçlar mı?
*   Ya da sınav öncesi/sonrası yaşadığın bir anı mı?

İstediğin kadar detayla anlatmaya çalışabilirsin, dinliyorum.
```

**Occam**

> Tamam, anlatmak istediğin şeyi paylaşabilirsin.

Occam gives a simple conversational acknowledgment. The base adds an inappropriate congratulation, a celebratory emoji and a menu of follow-up topics.

### 3. Answer a source-grounded question without adding an explanation

Source item: `me-020`.

**Prompt**

```text
Kaynak: Yavaş turizm akımının temel felsefesi bir yeri aceleye getirmeden derinlemesine deneyimlemektir.

Soru: Yavaş turizm akımının temel felsefesi nedir?

Cevap:
```

**Base model**

```text
Yavaş turizm akımının temel felsefesi, bir yeri aceleye getirmeden **derinlemesine deneyimlemektir**. Bu yaklaşım, gezginlerin yerel kültürleri, mutfakları ve doğasını yavaşça keşfetmesini, günlük hayatın ritmine uyum sağlamasını ve anı oluşturma sürecine odaklanmasını teşvik eder.
```

**Occam**

> Bir yeri aceleye getirmeden derinlemesine deneyimlemek.

Both responses identify the requested idea. Occam gives the source-grounded answer without bold formatting or the base's additional explanation. This is a presentation difference, not evidence of newly acquired knowledge.

## Training data

The training set contains:

- 80 reviewed core examples.
- 24 additional examples covering independent scenarios.

The examples target directness, accurate extraction, faithful summarization, useful explanations, selective clarification, groundedness, Turkish precision, non-anthropomorphic interaction, and neutral acknowledgment.

A separate **20-example development set** was repeatedly used during iteration and model selection. It is not an independent final test set.

No CETVEL example was deliberately included in training. The recorded exact, near-duplicate, and source-group audits identified no item-level overlap in the comparisons checked. This does not guarantee semantic independence or absence of overlap with the base model’s pretraining data.

The dataset has not yet been uploaded. Historical synthetic and AI-assisted generation provenance has gaps; its licensing and publication review remain outstanding.

## Training configuration

| Setting | Value |
| --- | --- |
| Learning rate / scheduler | `1e-4` / cosine |
| Optimizer | `adamw_8bit` |
| Max gradient norm | `1.0` |
| Microbatch / gradient accumulation | 1 / 8 |
| Effective batch size | 8 |
| Optimizer steps / warmup steps | 40 / 2 |
| Effective epochs | Approximately 3.08 |
| LoRA rank / alpha / dropout | 16 / 16 / 0 |
| Target projections | Language attention `q/k/v/o`; MLP `gate/up/down` |
| Maximum sequence length | 1024 |
| Packing | Disabled |
| Training truncation | None |
| Loss | Final assistant response and native EOS only |
| Earlier conversation turns | Masked from loss |
| Seed | 3407 |

Training used 19,131 supervised tokens across 320 microbatches. The measured training run took approximately **107 seconds**, excluding environment setup, preprocessing, evaluation, and artifact transfer.

The recorded configuration is included in `training-config.json`. Its nominal four-epoch setting was overridden by the fixed 40-step budget.

## Evaluation

The base model and adapter were evaluated under matched generation conditions:

- No additional system prompt.
- Non-thinking mode.
- BF16.
- Greedy decoding.
- Repetition penalty of `1.05`.

The evaluation contains **100 examples from each of five tasks**: GECTurk, TQUAD, XQuAD-TR, WMT English-to-Turkish, and MLSum-TR.

This is a source-group-sampled, CETVEL-derived subset—not the complete benchmark or an official CETVEL leaderboard score. It excludes the historical 700-example source groups and the separate 100-example pilot cohort.

### Automatic results

Scores are on a 0–100 scale unless shown as counts or token lengths.

| Metric | Base | Adapter |
| --- | ---: | ---: |
| GECTurk exact correction | 0/100 | 30/100 |
| TQUAD token F1 | 20.06 | 64.58 |
| XQuAD-TR token F1 | 13.68 | 55.84 |
| English→Turkish corpus BLEU | 16.84 | 16.81 |
| English→Turkish corpus chrF | 52.16 | 52.43 |
| MLSum-TR ROUGE-L | 18.45 | 20.93 |
| Median generated tokens | 98 | 26 |

Responses became substantially shorter. Much of the QA metric improvement reflects more direct, extractive answers and better output compliance; it should not be interpreted as evidence that the adapter acquired new factual knowledge.

Translation metrics were similar. The higher summarization ROUGE-L score did **not** correspond to better faithfulness in the human-reviewed sample.

### Blind human review

The author evaluated **30 preselected examples**, six per task. Model identities were shuffled independently for each item. This was a single-author assessment, not an independent external review.

| Preference | Count |
| --- | ---: |
| Adapter | 19 |
| Base | 6 |
| Tie | 2 |
| Neither | 3 |

| Model | Pass | Partial | Fail |
| --- | ---: | ---: | ---: |
| Base | 21 | 3 | 6 |
| Adapter | 23 | 4 | 3 |

Task-level findings:

- **Context-grounded QA:** All 12 reviewed answers passed for both models. All 12 preferences favored the adapter, supporting a presentation and directness improvement rather than a demonstrated knowledge gain.
- **Grammatical correction:** The adapter passed 4/6 examples; the base passed 0/6.
- **Translation:** Both passed 5/6. Preferences were evenly split, with two ties.
- **Summarization:** The adapter passed 2/6, compared with 4/6 for the base. Preferences favored the base in four examples, the adapter in one, and neither in one.

**Summarization quality regressed in this small reviewed sample despite the ROUGE-L increase.**

These findings come from a small, single-reviewer sample and do not establish general superiority or preservation of every base-model capability.

An earlier, repeatedly used 32-item project-development comparison recorded 26 passes for the adapter and 17 for the base. That comparison is development evidence, not an unbiased final test.

## Inference settings

Load this repository as a PEFT LoRA adapter on top of the base model; it is not a standalone checkpoint. Base weights and tokenizer must be loaded separately.

The following settings reproduce the main generation choices used for the reported evaluation:

| Setting | Value |
| --- | --- |
| Precision | BF16 |
| Thinking | Disabled (`enable_thinking=False`) |
| Additional system prompt | None |
| Decoding | Greedy (`do_sample=False`; temperature 0 for vLLM) |
| Repetition penalty | `1.05` |
| Maximum generated tokens | 4096 |
| Context window used in external evaluation | 8192 |
| Chat template | Pinned training tokenizer's native template; generation prompt enabled |
| Stop token | Native model EOS `248044` |
| vLLM EOS handling | `ignore_eos=True`, `stop_token_ids=[248044]` |
| Adapter revision for the released weights | `1a8a07ff2a29f51a2b6a635a8c219191a7377996` |

Use an inference backend compatible with this model architecture and PEFT adapter. The model's native EOS differs from the tokenizer EOS; see the reproducibility details before changing termination behavior.

These parameters are not a complete reproduction procedure: the recorded benchmark also used repetition/time guards and a fixed rendered-prompt protocol. A fresh-install deployment with a different checkpoint distribution or backend has not been verified. Agent-generated integration code should be checked against these settings and the saved protocol.

## Limitations and responsible use

The adapter can still hallucinate, produce unnatural Turkish, use Markdown, mistranslate, or make grammatical errors. Observed concerns include:

- Summarization-faithfulness regressions.
- Inconsistent `de/da` usage.
- Unnecessary corrections to already-correct sentences.
- Translation and grammatical-correction errors.

Evaluation was text-only and non-thinking. Preservation of reasoning-mode control, multimodal capabilities, English performance, safety behavior, tool use, long-context performance, and factual QA without supplied context was not established.

Occam is an experimental response-style adapter, not a certified production model or an autonomous authority for medical, legal, financial, or other high-stakes decisions. Verify consequential outputs.

## License

The adapter is offered under **Apache-2.0**; see `LICENSE`. The pinned base-model card also declares Apache-2.0.

The adapter license does not independently establish publication rights for its training data. Training-data provenance and provider-terms review remain separate requirements.

<details>
<summary>Reproducibility details</summary>

### Artifact identity

- Internal experiment identifier: `exp016/F`.
- Selected checkpoint: optimizer step 40.
- Exact training/evaluation base and tokenizer: `unsloth/Qwen3.5-4B`, revision `3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`.
- Official Qwen checkpoint used for the recorded weight-shard identity check: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
- Adapter revision: `1a8a07ff2a29f51a2b6a635a8c219191a7377996`.
- Adapter SHA256: `7ec9b04a5ecac7a031352fb5d0db281ef018c11951a4b4862c418e2b7a002ca1`.
- Adapter-config SHA256: `6f7f0480fdcf1cc32aed14a1c66981c1a454840ece4f05932b0ef338846a4335`.
- Local code/evidence commit: `7d47f9a1a1cfa8d4421aeb19e799c4a20f942938` in `cbarkinozer/llm-bender-lab`. Publication of that GitHub commit has not been verified.

The saved adapter configuration names `unsloth/Qwen3.5-4B` and contains `revision: null`; pin the exact training base/tokenizer revision explicitly for reproduction. The public metadata names the official Qwen model family, not a newly tested deployment. Original adapter weights and configuration bytes were preserved.

See `release-manifest.json` for file hashes and `training-config.json` for the recorded recipe.

### External evaluation environment

| Component | Version / configuration |
| --- | --- |
| vLLM | `0.30.0` |
| PyTorch | `2.13.0+cu130` |
| Transformers | `5.18.0` |
| PEFT | `0.21.2` |
| GPU | NVIDIA RTX 4090 |
| Context / maximum output | 8192 / 4096 tokens |

### Termination protocol

The model’s native EOS ID, `248044`, differs from the tokenizer EOS ID, `248046` (`im_end`).

Evaluation used vLLM `ignore_eos` with explicit stop-token ID `248044` to match the project’s earlier generation protocol.

| Model | Native EOS | Repetition guard |
| --- | ---: | ---: |
| Base | 496/500 | 4/500 |
| Adapter | 499/500 | 1/500 |

All guard-terminated outputs were retained and scored without retries. No output reached the length or timeout limit.

Changing EOS settings, chat templates, thinking mode, or inference backend changes the protocol. Deployment equivalence should be tested rather than assumed.

The project’s `exp-003-cetvel-500` scripts, configuration, and recorded source revisions define the evaluation procedure. The separate pilot cohort and development comparisons were not pooled with the 500-example evaluation.

</details>
