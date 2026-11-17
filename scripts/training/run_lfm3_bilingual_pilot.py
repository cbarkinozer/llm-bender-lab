"""CPU-side preparation/audit and (gated) runner for exp-010 / exp-011 (bilingual pilot arms). NOT EXECUTED FOR TRAINING.

  python scripts/training/run_lfm3_bilingual_pilot.py --experiment exp-010-tr-only-sft160 --mode audit
Modes: audit (CPU only: native-template render, labels, masks, thinking-format audit, deterministic order check)
       sft   (GPU; refuses to start unless plan/gates.json marks every gate true and the training source hash matches)
Differences from run_lfm3_sft160.py: dataset/order come from the experiment config; rows are consumed in the explicit
precomputed order (sequential sampler, 1 pass, max_steps from config) so supervised-token exposure is exact.
The empty-think prefix of direct-answer rows is supervised by default (exp-007 parity); --mask-empty-think is an opt-in recipe change.
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
PILOT = BASE / 'bilingual-pilot-v01'
TOKENIZER = BASE / 'base-sft160-runtime-local/tokenizer/tokenizer.json'
BOS, EOT_ID = '<|startoftext|>', 124900
GATES = PILOT / 'plan/gates.json'
REQUIRED_GATES = ['source_eligibility_cleared', 'owner_decisions_1_to_4_answered',
                  'native_label_audit_on_gpu_environment', 'smoke_and_tiny_overfit_passed']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def render(messages, reasoning):
    prefix = (f"{BOS}<|im_start|>system\n{messages[0]['content']}<|im_end|>\n<|im_start|>user\n{messages[1]['content']}<|im_end|>\n<|im_start|>assistant\n")
    return prefix, prefix + '<think>' + (reasoning or '') + '</think>' + messages[2]['content'] + '<|im_end|>\n'


def load(cfg_path):
    cfg = json.loads(Path(cfg_path).read_text(encoding='utf-8'))
    d = cfg['dataset']
    rows = [json.loads(l) for l in (ROOT / d['train_file']).read_text(encoding='utf-8').splitlines()]
    assert sha(ROOT / d['train_file']) == d['train_sha256'], 'training file changed'
    plan = json.loads((ROOT / d['data_order_file']).read_text(encoding='utf-8'))
    order = plan[d['data_order_key']]
    return cfg, rows, order


def audit(experiment, mask_empty_think):
    from tokenizers import Tokenizer
    cfg, rows, order = load(BASE / experiment / 'config.yaml')
    tok = Tokenizer.from_file(str(TOKENIZER))
    assert tok.token_to_id('<|im_end|>') == EOT_ID
    empty_think = tok.encode('<think></think>', add_special_tokens=False).ids
    findings, examples, tallies = [], [], collections.Counter()
    for i, r in enumerate(rows):
        prefix, full = render(r['messages'], r['worked_solution'])
        ids = tok.encode(full, add_special_tokens=False).ids
        pids = tok.encode(prefix, add_special_tokens=False).ids
        assert ids[:len(pids)] == pids, f"{r['id']}: token boundary changed"
        start = len(pids)
        labels = [-100] * start + ids[start:]
        reasoning = bool(r['worked_solution'])
        target_text = full[len(prefix):]
        # thinking-format audit
        if target_text.count('<think>') != 1 or target_text.count('</think>') != 1:
            findings.append(f"{r['id']}: think tags per target != 1/1")
        if not reasoning and not target_text.startswith('<think></think>'):
            findings.append(f"{r['id']}: direct row without empty think prefix")
        if '</think>' in r['messages'][2]['content'] or '<think>' in r['messages'][2]['content']:
            findings.append(f"{r['id']}: think tag inside final answer")
        if not reasoning:
            tallies['direct_rows'] += 1
            if ids[start:start + len(empty_think)] != empty_think:
                findings.append(f"{r['id']}: empty-think prefix tokenization differs from standalone")
            if mask_empty_think:
                for k in range(start, start + len(empty_think)):
                    labels[k] = -100
            tallies['empty_think_prefix_tokens_supervised' if not mask_empty_think else 'empty_think_prefix_tokens_masked'] += len(empty_think)
        else:
            tallies['reasoning_rows'] += 1
        # masks / EOT / padding-free checks
        if all(l == -100 for l in labels):
            findings.append(f"{r['id']}: zero supervised tokens")
        if labels[:start] != [-100] * start:
            findings.append(f"{r['id']}: context not fully masked")
        if EOT_ID not in labels[start:]:
            findings.append(f"{r['id']}: EOT not supervised")
        if ids.count(tok.token_to_id(BOS)) != 1:
            findings.append(f"{r['id']}: BOS count != 1")
        if len(ids) > 4096:
            findings.append(f"{r['id']}: exceeds max_length 4096")
        examples.append(dict(input_ids=ids, labels=labels))
    # deterministic order + exposure
    assert len(order) == cfg['training']['optimizer_steps'] * 8
    exposed = sum(sum(1 for l in examples[i]['labels'] if l != -100) for i in order)
    plan_total = cfg['training']['supervised_token_budget']
    if not mask_empty_think and exposed != plan_total:
        findings.append(f'planned supervised tokens {plan_total} != audited exposure {exposed}')
    inference_note = ('At thinking-disabled inference the template prompt already ends with "<think></think>", while direct-answer '
                      'training targets also START with "<think></think>" and supervise it; the model may therefore be trained to emit a second '
                      'empty think block / stray "</think>". Candidate cause of the </think> leakage seen in CROSSLINGUAL-DIAGNOSIS; '
                      'masking those tokens is an opt-in recipe change (--mask-empty-think), not enabled by default.')
    sample = examples[0]
    first_sup = next(i for i, l in enumerate(sample['labels']) if l != -100)
    masking_policy = dict(masked='BOS, system turn, user turn (incl. language instruction), and the assistant header up to and including "<|im_start|>assistant\n" (exp-007 parity)',
                          supervised='<think>...</think> (blank for direct answers; reasoning only where the row has it) + final answer + <|im_end|> + trailing newline',
                          extra_masking='none (empty-think prefix is NOT masked unless --mask-empty-think)',
                          sample_last_masked_token=repr(tok.decode([sample['input_ids'][first_sup - 1]], skip_special_tokens=False)),
                          sample_first_supervised_token=repr(tok.decode([sample['input_ids'][first_sup]], skip_special_tokens=False)))
    report = dict(experiment=experiment, masking_policy=masking_policy, status='passed' if not findings else 'FAILED', rows=len(rows), order_rows=len(order),
                  mask_empty_think=mask_empty_think, supervised_tokens_exposed=exposed, supervised_tokens_planned=plan_total,
                  tallies=dict(tallies), empty_think_token_ids=empty_think, findings=findings[:50], finding_count=len(findings),
                  thinking_format_note=inference_note, train_file_sha256=sha(ROOT / cfg['dataset']['train_file']),
                  tokenizer_sha256=sha(TOKENIZER), runner_sha256=sha(Path(__file__)),
                  tokenized_sha256=hashlib.sha256(json.dumps(examples, separators=(',', ':')).encode()).hexdigest())
    out = PILOT / 'plan' / f'audit-{experiment}{"-masked" if mask_empty_think else ""}.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('experiment', 'status', 'rows', 'supervised_tokens_exposed', 'supervised_tokens_planned', 'tallies', 'finding_count')}))
    return 0 if not findings else 1


def train(experiment, mask_empty_think):
    """GPU path (not run here). Mirrors run_lfm3_sft160.py; consumes rows in the explicit order, one pass, no shuffling."""
    gates = json.loads(GATES.read_text(encoding='utf-8')) if GATES.exists() else {}
    missing = [g for g in REQUIRED_GATES if not gates.get(g)]
    if not (gates.get('provider_terms_cleared_for_translated_rows') or gates.get('provider_terms_owner_risk_acceptance', {}).get('accepted')):
        missing.append('provider_terms (cleared or owner risk acceptance)')
    if missing:
        raise SystemExit(f'Refusing to train: gates not satisfied: {missing}')
    raise SystemExit('Training path intentionally not implemented in the preparation phase: port the Trainer section of '
                     'run_lfm3_sft160.py (SequentialSampler over the ordered examples, max_steps=config optimizer_steps) after the gates pass.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--experiment', required=True)
    p.add_argument('--mode', choices=['audit', 'sft'], required=True)
    p.add_argument('--mask-empty-think', action='store_true')
    a = p.parse_args()
    sys.exit(audit(a.experiment, a.mask_empty_think) if a.mode == 'audit' else train(a.experiment, a.mask_empty_think))


if __name__ == '__main__':
    main()
