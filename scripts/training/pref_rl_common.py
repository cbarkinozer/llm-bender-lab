"""Shared helpers for the preference-rl experiments (DPO, GRPO) on LFM3-1.7B: pins, model loading, statistics, manifests.

Method and hyperparameters follow the public Liquid cookbook notebooks lfm3_dpo_with_trl and lfm3_grpo_with_trl, re-implemented here.
"""
import hashlib
import importlib.metadata
import json
import math
import platform
from pathlib import Path

MODEL = 'LiquidAI/LFM3-1.7B'
MODEL_REVISION = '0dc4268b561499c648c7ba7c9466bf3d8d01517a'
TEMPLATE_SHA256 = 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
PACKAGES = ('torch', 'transformers', 'trl', 'peft', 'datasets', 'accelerate')
# Library versions the Liquid notebooks were tested with (trl 1.16.0, transformers 5.20.2, peft 0.21.2, ...).
PINNED = {'trl': '1.16.0', 'transformers': '5.20.2', 'peft': '0.21.2', 'datasets': '5.1.0', 'accelerate': '1.15.0'}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def package_versions():
    return {p: importlib.metadata.version(p) for p in PACKAGES}


def check_pins():
    """Fail loudly when a library differs from the tested versions (a different TRL can change training behaviour)."""
    have = package_versions()
    wrong = {p: (have[p], want) for p, want in PINNED.items() if have[p].split('+')[0] != want}
    assert not wrong, f'library versions differ from the pinned ones (have, want): {wrong}'


def pick_device(requested):
    import torch
    device = 'cuda' if requested == 'auto' and torch.cuda.is_available() else ('cpu' if requested == 'auto' else requested)
    dtype = torch.bfloat16 if device == 'cuda' and torch.cuda.is_bf16_supported(including_emulation=False) else torch.float32
    return device, dtype


def load_tokenizer():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL, revision=MODEL_REVISION, trust_remote_code=True, padding_side='left')
    assert hashlib.sha256(tok.chat_template.encode()).hexdigest() == TEMPLATE_SHA256, 'chat template changed'
    return tok


def load_model(device, dtype, tiny=False):
    """The pinned model; with tiny=True a randomly initialised miniature of it (6 layers, hidden 128) for CPU pipeline tests only."""
    from transformers import AutoConfig, AutoModelForCausalLM
    if tiny:
        cfg = AutoConfig.from_pretrained(MODEL, revision=MODEL_REVISION, trust_remote_code=True)
        cfg.hidden_size, cfg.intermediate_size, cfg.num_hidden_layers = 128, 256, 6
        cfg.num_attention_heads, cfg.num_key_value_heads, cfg.head_dim = 4, 2, 32
        cfg.layer_types = list(cfg.layer_types[:6])
        return AutoModelForCausalLM.from_config(cfg, trust_remote_code=True, dtype=dtype).to(device)
    model = AutoModelForCausalLM.from_pretrained(MODEL, revision=MODEL_REVISION, code_revision=MODEL_REVISION,
                                                 trust_remote_code=True, dtype=dtype)
    return model.to(device)


def wilson(k, n, z=1.96):
    """95% Wilson interval of a proportion, as (low, high)."""
    assert n > 0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def rate(flags):
    """{'k', 'n', 'rate', 'ci95'} of a list of booleans."""
    k, n = sum(bool(f) for f in flags), len(flags)
    if n == 0:
        return dict(k=0, n=0, rate=None, ci95=[None, None])
    lo, hi = wilson(k, n)
    return dict(k=k, n=n, rate=k / n, ci95=[round(lo, 4), round(hi, 4)])


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')


def write_jsonl(path, rows):
    with Path(path).open('w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def git_state():
    """Commit and dirty flag of the code. A pod has no .git, so the launcher writes GIT_STATE.json next to the scripts."""
    import subprocess
    root = Path(__file__).resolve().parents[2]
    f = root / 'GIT_STATE.json'
    if f.exists():
        return json.loads(f.read_text(encoding='utf-8'))
    try:
        run = lambda *a: subprocess.check_output(['git', '-C', str(root), *a], text=True).strip()
        return dict(commit=run('rev-parse', 'HEAD'), dirty=bool(run('status', '--porcelain', '--', 'scripts')))
    except Exception:
        return dict(commit=None, dirty=None)


def environment(device):
    """Where and with what the run happened (docs/reproducibility.md: commit, hardware, CUDA stack, precision, determinism)."""
    import os
    import subprocess
    import torch
    env = dict(packages=package_versions(), python=platform.python_version(), platform=platform.platform(), device=device,
               cpu=platform.processor(), git=git_state(),
               torch_float32_matmul_precision=torch.get_float32_matmul_precision(),
               cudnn=dict(deterministic=torch.backends.cudnn.deterministic, benchmark=torch.backends.cudnn.benchmark),
               deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
               env_vars={k: os.environ.get(k) for k in ('CUBLAS_WORKSPACE_CONFIG', 'HF_HOME', 'HF_HUB_DISABLE_XET', 'TOKENIZERS_PARALLELISM', 'CUDA_VISIBLE_DEVICES')})
    if device == 'cuda':
        props = torch.cuda.get_device_properties(0)
        env.update(gpu=props.name, gpu_count=torch.cuda.device_count(), vram_gb=round(props.total_memory / 1e9, 1), torch_cuda=torch.version.cuda,
                   bf16_supported=torch.cuda.is_bf16_supported(including_emulation=False))
        try:
            env['driver'] = subprocess.check_output(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], text=True).strip()
        except Exception:
            env['driver'] = None
    return env


def adapter_to_fp32(model):
    """PEFT loads adapters in fp32 (autocast_adapter_dtype), while the trainer can leave them in bf16. Put the trained adapter in fp32
    before it is evaluated and saved, so the evaluated model, the saved adapter and the reloaded model are the same numbers."""
    import torch
    n = 0
    for name, p in model.named_parameters():
        if 'lora_' in name and p.dtype != torch.float32:
            p.data = p.data.float()
            n += 1
    return n


def answer_logprobs(model, tok, pairs, device, n=4):
    """Per-token log-probabilities of the chosen answers of the first n training pairs (answer tokens only), one flat list."""
    import torch
    out = []
    model.eval()
    for pair in pairs[:n]:
        kw = pair.get('chat_template_kwargs') or {}
        head = tok.apply_chat_template(pair['prompt'], add_generation_prompt=True, tokenize=False, **kw)
        full = tok.apply_chat_template(pair['prompt'] + pair['chosen'], tokenize=False, **kw)
        n_head = len(tok(head, add_special_tokens=False).input_ids)
        ids = tok(full, add_special_tokens=False, return_tensors='pt').input_ids.to(device)
        with torch.inference_mode():
            logp = model(input_ids=ids, use_cache=False).logits[0, :-1].float().log_softmax(-1)
        out.append(logp.gather(-1, ids[0, 1:, None])[n_head - 1:, 0].cpu())
    return torch.cat(out)


def generated_logprobs(model, items, device):
    """Per-token log-probabilities of generated answers. items: list of (prompt_ids, answer_ids) 1-D id tensors (for GRPO, which has no chosen answer)."""
    import torch
    out = []
    model.eval()
    for prompt_ids, answer_ids in items:
        ids = torch.cat([prompt_ids.cpu(), answer_ids.cpu()])[None].to(device)
        with torch.inference_mode():
            logp = model(input_ids=ids, use_cache=False).logits[0, :-1].float().log_softmax(-1)
        out.append(logp.gather(-1, ids[0, 1:, None])[len(prompt_ids) - 1:, 0].cpu())
    return torch.cat(out)


def reload_parity(on, off, after, max_noise=0.2):
    """The model rebuilt from the saved adapter must behave like the trained model. Bit equality is not possible (bf16 logits near 20 move in
    steps of 0.125 and a freshly built model can take other kernels), and a generic probe cannot tell noise from a lost adapter. So: on the
    trained answers, the difference trained-vs-reloaded (noise) must be below max_noise of the difference adapter-on-vs-off (effect)."""
    effect = (on - off).abs().mean().item()
    noise = (on - after).abs().mean().item()
    out = dict(tokens=int(on.numel()), effect=effect, noise=noise, noise_over_effect=noise / max(effect, 1e-9), max_noise=max_noise)
    print('RELOAD PARITY', out, flush=True)
    assert effect > 0 and noise <= max_noise * effect, f'Reload parity failed (adapter lost, or the probe is blind): {out}'
    return out


def learning_check(log_history, kind):
    """Did the training signal reach the model? kind='dpo': last logged rewards/accuracies >= 0.9; kind='grpo': the mean reward of
    the last third of the logged steps exceeds the first third by at least 0.05. Advisory for the tiny-overfit stages, recorded in the manifest."""
    key = 'rewards/accuracies' if kind == 'dpo' else 'reward'
    values = [x[key] for x in log_history if key in x]
    if len(values) < 3:
        return dict(kind=kind, key=key, values=values, passed=None, note='too few logged steps')
    if kind == 'dpo':
        return dict(kind=kind, key=key, values=values, passed=values[-1] >= 0.9)
    third = max(1, len(values) // 3)
    first, last = sum(values[:third]) / third, sum(values[-third:]) / third
    return dict(kind=kind, key=key, values=values, first_third=first, last_third=last, passed=last - first >= 0.05)
