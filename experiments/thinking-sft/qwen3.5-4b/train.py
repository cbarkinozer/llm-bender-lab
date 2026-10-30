"""CUDA BF16 LoRA entrypoint; smoke/tiny/full are separate fresh initializations.

Use pipeline.py prepare first. This script never reads test prompts or keys.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess

from pipeline import MODEL, REVISION, ROOT, DATA, read_rows, sha, write_json


class LabelCollator:
    """Pad by position: an EOS token also used as pad remains supervised."""
    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, features):
        import torch
        width = max(len(f['input_ids']) for f in features)
        return {key: torch.tensor([f[key] + [padding] * (width-len(f[key])) for f in features])
                for key, padding in [('input_ids', self.pad_id), ('attention_mask', 0), ('labels', -100)]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mode', choices=['smoke', 'tiny', 'full'], required=True)
    p.add_argument('--baseline', type=Path, help='Completed native HF baseline manifest; required for full')
    p.add_argument('--smoke-evidence', type=Path)
    p.add_argument('--tiny-evidence', type=Path)
    args = p.parse_args()
    if int(os.environ.get('WORLD_SIZE', '1')) != 1:
        raise ValueError('This frozen recipe is single-GPU only')
    if args.output.exists():
        raise ValueError('Output exists; diagnostics and full runs must be fresh')
    config = json.loads((ROOT / 'experiment-config.json').read_text())
    if args.mode == 'full' and not config.get('data_selection_ready', False):
        raise ValueError('Failure-guided data revision is pending; generic draft is not approved for full training')
    report = json.loads((args.prepared / 'representation-report.json').read_text())
    if (report['model'], report['revision'], report['rows'], report['truncated']) != (MODEL, REVISION, 80, 0):
        raise ValueError('Unexpected preparation/model identity')
    if report['max_length'] != config['max_length']:
        raise ValueError('Preparation/config length differs')
    if report['pipeline_sha256'] != sha(ROOT / 'pipeline.py'):
        raise ValueError('Preparation code changed; regenerate prepared data')
    for path, expected in [(args.prepared / 'train-tokenized.jsonl', report['tokenized_sha256']),
                           (DATA / 'manifest.json', report['manifest_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Preparation provenance mismatch: {path.name}')
    if args.mode == 'full':
        if not all((args.baseline, args.smoke_evidence, args.tiny_evidence)):
            raise ValueError('Full training needs baseline, smoke and tiny evidence')
        baseline = json.loads(args.baseline.read_text())
        if not (baseline['complete'] and baseline['backend'] == 'hf' and baseline['condition'] == 'base'
                and baseline['revision'] == REVISION and baseline['split'] == 'test'
                and baseline['items'] == 20 and baseline['config_sha256'] == sha(ROOT / 'experiment-config.json')
                and baseline['prompts_sha256'] == sha(DATA / 'test-prompts.jsonl')):
            raise ValueError('Baseline is incomplete or uses different settings/data')
        if (baseline['outputs_sha256'] != sha(args.baseline.parent / 'outputs.jsonl')
                or baseline['evaluate_script_sha256'] != sha(ROOT / 'evaluate.py')
                or baseline['template_sha256'] != report['template_sha256']):
            raise ValueError('Baseline outputs, evaluation code or template changed')
        for path, mode in [(args.smoke_evidence, 'smoke'), (args.tiny_evidence, 'tiny')]:
            evidence = json.loads(path.read_text())
            if not (evidence['mode'] == mode and evidence['mechanical_pass']
                    and evidence['representation_sha256'] == sha(args.prepared / 'representation-report.json')
                    and evidence['config_sha256'] == sha(ROOT / 'experiment-config.json')
                    and evidence['train_script_sha256'] == sha(Path(__file__))):
                raise ValueError(f'Invalid {mode} evidence')
        if not json.loads(args.tiny_evidence.read_text()).get('learning_pass'):
            raise ValueError('Tiny diagnostic did not demonstrate reduced training loss')
    import torch
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, Trainer, TrainingArguments, set_seed
    from peft import LoraConfig, TaskType, get_peft_model, PeftModel
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise SystemExit('This recipe requires a CUDA GPU with BF16 support; no training started.')
    set_seed(config['seed'])
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
    if tokenizer.chat_template != (args.prepared / 'tokenizer/chat_template.jinja').read_text():
        raise ValueError('Prepared tokenizer template differs')
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        MODEL, revision=REVISION, dtype=torch.bfloat16, trust_remote_code=False,
        attn_implementation='sdpa', device_map={'': 0})
    model.config.use_cache = False
    names = [name for name, module in model.named_modules() if isinstance(module, torch.nn.Linear)
             and 'language_model' in name and name.rsplit('.', 1)[-1] in config['target_module_suffixes']]
    if not names or any('visual' in name for name in names):
        raise ValueError('Could not identify text-only adapter targets')
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM,
        r=config['lora']['rank'], lora_alpha=config['lora']['alpha'],
        lora_dropout=config['lora']['dropout'], bias='none', target_modules=names))
    if any('lora_' not in name for name, parameter in model.named_parameters() if parameter.requires_grad):
        raise ValueError('Unexpected trainable non-LoRA parameter')
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    rows = read_rows(args.prepared / 'train-tokenized.jsonl')
    if args.mode != 'full':
        # Interleaved category indices, chosen without test feedback.
        indices = [0, 20, 40, 60] if args.mode == 'smoke' else [0, 1, 20, 21, 40, 41, 60, 61]
        rows = [rows[i] for i in indices]
    steps = {'smoke': 2, 'tiny': 30, 'full': config['max_steps']}[args.mode]
    args.output.mkdir(parents=True)
    try:
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                                              stderr=subprocess.DEVNULL).strip()
        git_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    except subprocess.CalledProcessError:
        git_commit, git_dirty = None, None
    bundled_source = ROOT / 'source-provenance.json'
    manifest = dict(mode=args.mode, mechanical_pass=False, model=MODEL, revision=REVISION,
        config=config, config_sha256=sha(ROOT / 'experiment-config.json'),
        representation_sha256=sha(args.prepared / 'representation-report.json'),
        train_script_sha256=sha(Path(__file__)), target_modules=names,
        trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        total_parameters=sum(p.numel() for p in model.parameters()), rows=len(rows), max_steps=steps,
        versions={k: importlib.metadata.version(k) for k in ['torch', 'transformers', 'peft', 'accelerate']},
        platform=platform.platform(), gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda,
        git_commit=git_commit, git_dirty=git_dirty,
        bundled_source=json.loads(bundled_source.read_text()) if bundled_source.exists() else None)
    write_json(args.output / 'run-manifest.json', manifest)
    collator = LabelCollator(tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id)
    trainer = Trainer(model=model, train_dataset=rows, eval_dataset=rows if args.mode != 'full' else None,
        data_collator=collator, args=TrainingArguments(output_dir=str(args.output / 'checkpoints'),
        per_device_train_batch_size=config['micro_batch'], per_device_eval_batch_size=1,
        prediction_loss_only=True, gradient_accumulation_steps=config['gradient_accumulation'],
        max_steps=steps, learning_rate=config['learning_rate'], warmup_steps=config['warmup_steps'],
        lr_scheduler_type=config['scheduler'], weight_decay=config['weight_decay'],
        max_grad_norm=config['max_grad_norm'], bf16=True, optim=config['optimizer'],
        gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False},
        logging_steps=1, save_strategy='no', report_to='none', run_name=f'occam2-{args.mode}-thinking-sft-r16', seed=config['seed'],
        data_seed=config['seed'], remove_unused_columns=False))
    before = trainer.evaluate()['eval_loss'] if args.mode != 'full' else None
    result = trainer.train()
    after = trainer.evaluate()['eval_loss'] if args.mode != 'full' else None
    import math
    if not math.isfinite(result.training_loss):
        raise ValueError('Nonfinite loss')
    trainer.save_model(str(args.output / 'adapter'))
    tokenizer.save_pretrained(args.output / 'adapter')
    # Reload the saved adapter against the correct base structure and generate
    # on a training prompt only. No hidden test is touched by training checks.
    base = model.unload()
    reloaded = PeftModel.from_pretrained(base, args.output / 'adapter', is_trainable=False)
    reloaded.eval()
    prompt = read_rows(DATA / 'train.jsonl')[0]['messages'][:-1]
    inputs = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True,
        enable_thinking=True, return_tensors='pt', return_dict=True).to('cuda')
    with torch.inference_mode():
        outputs = reloaded.generate(**inputs, max_new_tokens=256, do_sample=False, use_cache=True)
    completion = tokenizer.decode(outputs[0, inputs['input_ids'].shape[-1]:], skip_special_tokens=False)
    if not completion.strip():
        raise ValueError('Reload generation empty')
    manifest.update(mechanical_pass=True, learning_pass=(after <= .8 * before) if before is not None else None,
        diagnostic_loss_before=before, diagnostic_loss_after=after, metrics=result.metrics,
        peak_allocated_vram=torch.cuda.max_memory_allocated(), reload_training_prompt_output=completion,
        caveat='Tiny learning gate requires >=20% diagnostic loss reduction plus manual inspection of saved reload output; it is not an accuracy result.',
        adapter_files_sha256={f.name: sha(f) for f in (args.output / 'adapter').iterdir() if f.is_file()})
    write_json(args.output / 'run-manifest.json', manifest)


if __name__ == '__main__':
    main()
