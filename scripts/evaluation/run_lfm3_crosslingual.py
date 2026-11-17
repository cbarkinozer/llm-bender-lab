"""Inference-only four-arm diagnostic, recoverable from adapters without optimizer states."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
RUN = BASE / 'crosslingual-runtime-local'
PACKET = BASE / 'crosslingual-holdout-v01'
PARENT = 'LiquidAI/LFM3-1.7B'
REV = '0dc4268b561499c648c7ba7c9466bf3d8d01517a'
CPT_REV = '6f213ec25a944dab2fbdeb6d337deb0e0442e638'
ADAPTERS = {
    'cpt-sft': ('exp-007-sft160-lr1e4', '00836cefaa21f586bea82588d155b9aa3218a8699aa59df5154d12cbfe222626'),
    'base-sft': ('exp-009-base-sft160-lr1e4', '788d3d9b443bd2fdbcbb32bad07f97728be3b8d78865656e0937a499f969d90a'),
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from huggingface_hub import snapshot_download
    assert torch.cuda.is_bf16_supported()
    tokenizer = AutoTokenizer.from_pretrained(PARENT, revision=REV, trust_remote_code=True)
    assert hashlib.sha256(tokenizer.chat_template.encode()).hexdigest() == 'f45005c50cd2a97329722bf3a2dee9f16c04cdf825a589b280fb7e99e6827818'
    probe = tokenizer('A brief check. Kısa bir deneme.', return_tensors='pt').to('cuda')
    for label in ['cpt', 'base-sft', 'cpt-sft']:
        dest = RUN / 'models' / label
        receipt = dest / 'merge-receipt.json'
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            assert all(sha(dest / p) == h for p, h in saved['files'].items())
            continue
        assert not dest.exists(), f'Incomplete merge: {dest}; preserve and inspect'
        source = RUN / 'models/cpt' if label == 'cpt-sft' else PARENT
        kwargs = {} if label == 'cpt-sft' else dict(revision=REV, code_revision=REV)
        model = AutoModelForCausalLM.from_pretrained(source, trust_remote_code=True,
                    dtype=torch.bfloat16, **kwargs).to('cuda').eval()
        if label == 'cpt':
            adapter = Path(snapshot_download('cbarkinozer/LFM3-1.7B-Turkish-CPT', revision=CPT_REV,
                            allow_patterns=['adapter_config.json', 'adapter_model.safetensors']))
        else:
            exp, expected = ADAPTERS[label]
            adapter = BASE / exp / 'results-local/sft/checkpoint-60'
            assert sha(adapter / 'adapter_model.safetensors') == expected
        model = PeftModel.from_pretrained(model, adapter).eval()
        with torch.inference_mode():
            before = model(**probe, use_cache=False).logits[:, -1].float().cpu()
        model = model.merge_and_unload(safe_merge=True).eval()
        model.config.use_cache = True
        with torch.inference_mode():
            merged = model(**probe, use_cache=False).logits[:, -1].float().cpu()
        assert torch.isfinite(merged).all()
        model.save_pretrained(dest, safe_serialization=True)
        tokenizer.save_pretrained(dest)
        del model
        gc.collect(); torch.cuda.empty_cache()
        model = AutoModelForCausalLM.from_pretrained(dest, trust_remote_code=True,
                    dtype=torch.bfloat16).to('cuda').eval()
        with torch.inference_mode():
            after = model(**probe, use_cache=False).logits[:, -1].float().cpu()
        assert torch.equal(merged, after), 'Merged reload logits changed'
        dump(receipt, dict(status='passed', label=label, parent=str(source), parent_revision=REV,
            cpt_revision=CPT_REV if label != 'base-sft' else None,
            adapter_sha256=sha(adapter / 'adapter_model.safetensors'), reload_exact=True,
            merge_max_abs_difference=float((before - merged).abs().max()),
            files={p.name: sha(p) for p in dest.iterdir() if p.is_file()}))
        del model
        gc.collect(); torch.cuda.empty_cache()
        print('MERGED ' + label, flush=True)


def infer():
    frozen = json.loads((PACKET / 'manifest.json').read_text())
    rows = []
    for name in ['questions.jsonl', 'symbolic-controls.jsonl']:
        assert sha(PACKET / name) == frozen['files'][name]['sha256']
        rows += [json.loads(s) for s in (PACKET / name).read_text(encoding='utf-8').splitlines()]
    assert len(rows) == len({r['id'] for r in rows}) == 15
    combined = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode()
    packet = RUN / 'combined-questions.jsonl'
    packet.parent.mkdir(parents=True, exist_ok=True)
    if packet.exists():
        assert packet.read_bytes() == combined
    else:
        packet.write_bytes(combined)
    dump(RUN / 'source-manifest.json', dict(files={str(p.relative_to(ROOT)): sha(p) for p in
         [Path(__file__), ROOT / 'scripts/evaluation/evaluate_lfm3_vllm_batched.py', PACKET / 'manifest.json', packet]},
         base_revision=REV, cpt_revision=CPT_REV, adapters=ADAPTERS))
    smoke = RUN / 'smoke-question.jsonl'
    smoke.write_text(json.dumps(dict(id='crosslingual-infra-smoke', task='infra-smoke',
        messages=[dict(role='user', content='Write only the number 2.')])) + '\n')
    smoke_out = RUN / 'smoke-output'
    if not (smoke_out / 'manifest.json').exists():
        cmd = ['/workspace/.venvs/lfm3-vllm/bin/python', ROOT / 'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
               '--experiment-dir', BASE / 'exp-000-baseline', '--output-dir', smoke_out,
               '--packet-path', smoke, '--packet-sha256', sha(smoke), '--all-rows',
               '--batch-size', '4', '--temperature', '0.1', '--top-k', '50',
               '--repetition-penalty', '1.1', '--protocol-name', 'crosslingual-infrastructure-smoke']
        (RUN / 'logs').mkdir(exist_ok=True)
        with (RUN / 'logs/smoke.log').open('xb') as stream:
            subprocess.run(list(map(str, cmd)), cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    sm = json.loads((smoke_out / 'manifest.json').read_text())
    sa = json.loads((smoke_out / 'answers.jsonl').read_text(encoding='utf-8').strip())
    assert sm['status'] == 'completed' and sm['count'] == 1 and sa['prediction'].strip()
    for label in ['base', 'cpt', 'base-sft', 'cpt-sft']:
        out = RUN / 'inference' / label
        if (out / 'manifest.json').exists():
            old = json.loads((out / 'manifest.json').read_text())
            assert old['status'] == 'completed' and old['count'] == 15
            assert old['questions_sha256'] == sha(packet)
            continue
        cmd = ['/workspace/.venvs/lfm3-vllm/bin/python', ROOT / 'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
               '--experiment-dir', BASE / 'exp-000-baseline', '--output-dir', out,
               '--packet-path', packet, '--packet-sha256', sha(packet), '--all-rows',
               '--batch-size', '4', '--temperature', '0.1', '--top-k', '50',
               '--repetition-penalty', '1.1', '--protocol-name', 'crosslingual-holdout-v01-thinking-off']
        if label != 'base':
            assert (RUN / 'models' / label / 'merge-receipt.json').exists()
            cmd += ['--merged-model', RUN / 'models' / label]
        log = RUN / 'logs' / (label + '.log'); log.parent.mkdir(exist_ok=True)
        print('INFERENCE ' + label, flush=True)
        started = time.time()
        with log.open('xb') as stream:
            subprocess.run(list(map(str, cmd)), cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
        m = json.loads((out / 'manifest.json').read_text())
        answers = [json.loads(s) for s in (out / 'answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert m['status'] == 'completed' and m['count'] == len(answers) == 15
        assert {r['id'] for r in answers} == {r['id'] for r in rows}
        dump(RUN / 'stages' / (label + '.json'), dict(seconds=time.time()-started,
             answers_sha256=sha(out / 'answers.jsonl'), manifest_sha256=sha(out / 'manifest.json')))
    dump(RUN / 'completion.json', dict(status='completed-pending-owner-review', models=4,
         prompts_per_model=15, generations=60, thinking=False, training_performed=False))


if __name__ == '__main__':
    os.environ.setdefault('HF_HOME', '/workspace/.cache/huggingface')
    private = Path('/workspace/private-credentials.json')
    if private.exists():
        for k, v in json.loads(private.read_text()).items():
            os.environ[k] = v.strip()
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['prepare', 'infer'], required=True)
    args = parser.parse_args()
    prepare() if args.mode == 'prepare' else infer()
