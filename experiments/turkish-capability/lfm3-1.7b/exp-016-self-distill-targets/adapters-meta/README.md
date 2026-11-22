# exp-016 adapters (weights are not in Git)

Each LoRA adapter is 128,881,784 bytes, above GitHub's 100 MB file limit, and the repo rules exclude checkpoints.
The files stay on the owner's disk (ignored `results-local/`); back them up or publish them to the Hub with a base-first
name (for example `cbarkinozer/LFM3-1.7B-Turkish-SelfDistill-SFT`) after approval. Each folder here keeps the adapter
config and training manifest. Verify a copy with the sha256 below.

| Arm | Path under `experiments/turkish-capability/lfm3-1.7b/` | Bytes | sha256 of adapter_model.safetensors |
|---|---|---:|---|
| arm-a-base-55steps | `exp-016-self-distill-targets/results-local/sft/adapter` | 128,881,784 | `0401ffefc211e82f58e9115d35195b56d4b5108497ecc105abf1cfeefb54531f` |
| arm-b-cpt-parent-55steps | `exp-016-self-distill-targets/results-local/sft-arm-b-cpt-parent/adapter` | 128,881,784 | `1236192309eb27f8ae37a0f5cccd4c4193acbd8eb8d1bf143d1bf2e056e50761` |
| arm-c-base-165steps | `exp-016-self-distill-targets/results-local/sft-arm-c-base-x3/adapter` | 128,881,784 | `050d9274ca1ae95f491ab022dea66e201514a6eaf859979c1dd7dcd974d5710e` |

Arm B was trained on the CPT-merged parent (base + `cbarkinozer/LFM3-1.7B-Turkish-CPT@6f213ec`, merged weight sha256 `f4562118c3196462d73649198d856450714ae67081cd6af7df851f59dccf5e46`), so apply it to that merged model, not to the original base.
