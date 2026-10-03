"""CPU-only preparation of approved A/B design; B drafts cannot pass GPU gates."""
import argparse
import copy
import csv
import hashlib
import io
import json
import re
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from candidate_specs import SPECS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT / 'exp-009-minimal-edit'
A = ROOT / 'exp-011-duration-ablation'
sys.path.insert(0, str(PARENT))
from prepare_training import encode_final, stats

SOURCE_HASHES = {
    'train-reviewed.jsonl': 'bb66be2853f866b6b463f80d62cc7d388b4a3a203e22fa6d9909a6123ffd4ec9',
    'validation-reviewed.jsonl': '43e10beed85aa6fbbda768a124c7a2e6feb3743ddc79c2e38098c7982cfad429',
}
REMOVED = [f'me-{n:03}' for n in (
    1, 2, 3, 4, 5, 6, 11, 12, 13, 15, 16, 18,
    21, 22, 23, 24, 25, 26, 31, 33, 34, 35, 37, 38)]
HIGH_SIGNAL = ['me-049','me-050','me-059','me-069','me-070','me-079','me-089','me-090']

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def jsonl(rows):
    return ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode('utf-8')

def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != raw:
        # Directory listing/key order can differ after clone; preserve original
        # bytes when JSON is semantically identical, never rewrite frozen hashes.
        if path.suffix in ('.json','.yaml'):
            try:
                if json.loads(path.read_bytes()) == json.loads(raw):
                    return
            except (ValueError, UnicodeDecodeError):
                pass
        raise ValueError('Refusing to replace versioned artifact: ' + str(path))
    path.write_bytes(raw)

def load_rows(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]

def original():
    for name, expected in SOURCE_HASHES.items():
        assert sha((PARENT/'reviewed-v2'/name).read_bytes()) == expected, name
    return (load_rows(PARENT/'reviewed-v2/train-reviewed.jsonl'),
            load_rows(PARENT/'reviewed-v2/validation-reviewed.jsonl'))

def candidates():
    assert len(SPECS) == len(REMOVED) == 24
    rows = []
    for i, (category, scenario, turns, target, criteria) in enumerate(SPECS, 1):
        messages = [dict(role=role, content=text) for role, text in turns]
        assert [m['role'] for m in messages] in [['user'], ['user','assistant','user']]
        assert all(m['content'].strip() for m in messages) and target.strip()
        assert not re.search(r'\*\*|^\s*#{1,6}\s|[\U0001f300-\U0001faff]', target, re.M)
        rows.append(dict(id=f'bc-{i:03}', split='train', evaluation_only=False,
            category=category, subtype=scenario, scenario_group_id='coverage-'+scenario,
            messages=messages, prompt_tr='\n\n'.join(m['role']+': '+m['content'] for m in messages),
            desired_answer=target, evaluation_criteria=criteria,
            input_messages_sha256=sha(json.dumps(messages, ensure_ascii=False, separators=(',',':')).encode()),
            source_path='exp-012-coverage-ablation/candidate_specs.py', source_id=f'bc-{i:03}',
            origin='new-project-agent-authored', authored_date='2026-10-03',
            replaces_id=REMOVED[i-1], review_decision='pending',
            answer_status='draft-awaiting-human-review', dataset_version='coverage-draft-v1',
            loss_policy='final assistant only; all earlier turns masked'))
    return rows

def norm(text):
    text = re.sub(r'Verilen cümlenin yazım hatalarını düzeltin\.\s*Hatalı Cümle:\s*', '', text)
    text = re.sub(r'\s*Düzeltilmiş hali:\s*$', '', text)
    return ' '.join(unicodedata.normalize('NFC', text).split())

def views(row):
    # Inspect turns as well as full context; do not erase i/ı, accents or quantities.
    return list(dict.fromkeys([norm(m['content']) for m in row['messages']]
        + [norm('\n'.join(m['content'] for m in row['messages']))]))

def similarity(a, b):
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    return matcher.ratio()

def audit(new, train, validation):
    benchmarks = []
    inventories = {}
    old_audit = json.loads((PARENT/'data/audit-report.json').read_text(encoding='utf-8'))
    for path, info in old_audit['benchmark_inputs'].items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == info['sha256_bytes'], path
        records = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        selected = [r for r in records if r.get('prompt_tr')]
        inventories[path] = dict(rows=len(selected), sha256_bytes=sha(raw))
        for r in selected:
            benchmarks.append((path, r['id'], [norm(r['prompt_tr'])]))
    historic = []
    selection = json.loads((PARENT/'data-v2/selection-manifest.json').read_text(encoding='utf-8'))
    for path, info in selection['inputs'].items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == info['sha256_bytes'], path
        records = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        inventories[path] = dict(rows=len(records), sha256_bytes=sha(raw))
        for r in records:
            messages = json.loads(r['messages'])
            historic.append((path, r['id'], [norm(m['content']) for m in messages if m['role']=='user']))
    references = [('current-validation',r['id'],views(r)) for r in validation]
    references += [('current-train',r['id'],views(r)) for r in train]
    references += benchmarks + historic
    exact, near, nearest_validation = [], [], []
    for row in new:
        scores = []
        for source, id_, texts in references:
            score = 0.0
            for a in views(row):
                for b in texts:
                    if a == b:
                        exact.append(dict(id=row['id'], source=source, other_id=id_))
                    threshold = .60 if source == 'current-validation' else .78
                    matcher = SequenceMatcher(None, a, b, autojunk=False)
                    # quick_ratio is an upper bound: skip impossible near matches.
                    if source == 'current-validation' or matcher.quick_ratio() >= threshold:
                        score = max(score, matcher.ratio())
            if source == 'current-validation':
                scores.append(dict(candidate=row['id'], validation=id_, similarity=round(score,4)))
            if score >= (.60 if source == 'current-validation' else .78):
                near.append(dict(id=row['id'], source=source, other_id=id_, similarity=round(score,4)))
        nearest_validation.extend(sorted(scores, key=lambda x:x['similarity'], reverse=True)[:3])
    internal_exact = []
    internal_near = []
    for i, row in enumerate(new):
        for other in new[i+1:]:
            score = max(similarity(a,b) for a in views(row) for b in views(other))
            if score == 1:
                internal_exact.append([row['id'],other['id']])
            elif score >= .78:
                internal_near.append(dict(a=row['id'],b=other['id'],similarity=round(score,4)))
    assert not exact and not internal_exact, (exact, internal_exact)
    assert not near and not internal_near, (near, internal_near)
    assert not ({r['scenario_group_id'] for r in new} & {r['scenario_group_id'] for r in train+validation})
    return dict(status='no-detected-overlap', candidate_rows=24,
        current_training_rows=80, current_validation_rows=20,
        historical_benchmark_rows=len(benchmarks), historical_training_rows=len(historic),
        near_threshold_validation=.60, near_threshold_other=.78, exact_matches=exact,
        near_flags=near, internal_exact=internal_exact, internal_near=internal_near,
        closest_validation_pairs=nearest_validation, source_inventory=inventories,
        semantic_review='Agent-authored distinct settings: registration, labels, clubs, transcripts, lending, forms, inventory, survey groups, records, file formats and explicit logical conditions. No cafe sign, morning departure, desk/layout, exam-sharing or home-feeling derivatives. Human review still pending.',
        limitation='Lexical/provenance checks and agent inspection do not prove universal semantic independence. Shared target behaviors are intentional; no independent-final-test claim.')

def make_config(experiment_id, approved, train_hash=None):
    config = json.loads((ROOT/'exp-010-lr-ablation/config.yaml').read_text(encoding='utf-8'))
    config['experiment_id'] = experiment_id
    config['parent'] = 'exp-010-lr-ablation' if approved else 'exp-011-duration-ablation'
    config['status'] = 'prepared-needs-gpu-gates' if approved else 'blocked-human-review'
    config['training'].update(epochs=4, expected_optimizer_steps=40)
    config['dataset']['train'] = ('reviewed-v2/train-reviewed.jsonl' if approved else
        '../exp-012-coverage-ablation/data-reviewed-v1/train-reviewed.jsonl')
    config['dataset']['hashes']['train-reviewed.jsonl'] = train_hash or SOURCE_HASHES['train-reviewed.jsonl']
    config['dataset']['review_required'] = not approved
    config['dataset']['review_status'] = 'original-human-reviewed' if approved else 'pending-24-candidates'
    config['inference'].update(output_token_budgets=[4096], bounded=True,
        stop_policy='native EOS; exact token loops/180-second timeout are failures, not EOS')
    config['tracking'] = dict(run_name=('exp011-sft-duration-80rows-4ep' if approved else
                                      'exp012-sft-coverage-80rows-4ep'))
    config['notes'] = [
        'Fresh pinned base for each arm; no earlier adapter initialization.',
        'A changes 2 to 4 epochs versus exp010; cosine schedule extends with duration.',
        'B versus A changes 24 scenarios/targets, not LR/rank/batch/epochs; retain 56 original rows.',
        '80 examples, effective batch 8, four epochs, 40 optimizer steps; target-token exposure can differ.',
        'Shared train_reviewed.py resolves dataset paths against exp009, not this config folder.',
        'Final-assistant-only labels, masked empty-think prefix, native EOS supervised.',
        'Frozen 20 development-validation items, eight high-signal cases, never gradients.',
        'Use actual exp010 v2 bounded HF/Unsloth evaluation settings; no vLLM for adapter inference.',
        'Final scheduled epoch-four adapter preselected; no best-checkpoint selection on validation.',
        'New GPU gates needed; prior LR-only waiver does not automatically apply to these runs.',
    ]
    return config

def tokenize(rows, output, approved, config, require_original_parity=False):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config['model']['name'], revision=config['model']['revision'])
    template = json.loads((PARENT/'training-preflight-v1/tokenizer-template.json').read_text(encoding='utf-8'))
    assert sha(tokenizer.chat_template.encode()) == template['template_sha256'], 'Cached template differs'
    prepared = []
    for row in rows:
        item, prompt_count, target_count = encode_final(tokenizer, row)
        assert len(item['input_ids']) <= config['training']['max_seq_length'], row['id']
        assert all(x == -100 for x in item['labels'][:prompt_count])
        assert [x for x in item['labels'] if x!=-100][-1] == tokenizer.convert_tokens_to_ids('<|im_end|>')
        prepared.append(dict(id=row['id'], split=row['split'],category=row['category'],
            prompt_tokens=prompt_count,target_tokens=target_count,**item))
    if require_original_parity:
        for split in ('train','validation'):
            saved = load_rows(PARENT/f'training-preflight-v1/{split}-tokenized.jsonl')
            assert [r for r in prepared if r['split']==split] == saved, split
    files = {}
    for split in ('train','validation'):
        name = f'{split}-tokenized.jsonl'
        raw = jsonl([r for r in prepared if r['split']==split])
        save(output/name,raw); files[name]=sha(raw)
    inspected = [r for r in prepared if r['id'] in ['me-042','me-053','me-059','bc-001','bc-008','bc-018']]
    inspection = [dict(id=r['id'],full_text=tokenizer.decode(r['input_ids'],skip_special_tokens=False),
        supervised_text=tokenizer.decode([x for x in r['labels'] if x!=-100],skip_special_tokens=False),
        input_ids=r['input_ids'],labels=r['labels']) for r in inspected]
    for name, raw in [('mask-inspection.json',encoded(inspection)),('tokenizer-template.json',encoded(template))]:
        save(output/name, raw); files[name]=sha(raw)
    report = dict(status='local-preflight-passed' if approved else 'draft-not-approved',
        rows=100,splits={'train':80,'validation':20},packing=False,max_seq_length=1024,
        split_stats={s:{'sequence':stats([len(r['input_ids']) for r in prepared if r['split']==s]),
                       'target':stats([r['target_tokens'] for r in prepared if r['split']==s])}
                     for s in ('train','validation')},
        all_context_tokens_masked=True,native_final_end_of_turn_supervised=True,
        truncated_rows=0,zero_target_rows=0,files=files,
        validation_tokenization_matches_parent=([r for r in prepared if r['split']=='validation']==
            load_rows(PARENT/'training-preflight-v1/validation-tokenized.jsonl')),
        original_data_hashes=SOURCE_HASHES,remaining=['human approval for B' if not approved else
            'GPU actual-batch mask check','GPU smoke/reload','GPU tiny-overfit','W&B connection'],
        training_started=False)
    assert report['validation_tokenization_matches_parent']
    save(output/'report.json',encoded(report))
    save(output/'training-config.json',encoded(config))
    return report

def prepare():
    train, validation = original()
    new = candidates()
    mapping = {r['replaces_id']:r for r in new}
    draft = [mapping.get(r['id'],r) for r in train]
    assert len(draft) == 80 and len({r['id'] for r in draft}) == 80
    retained = [r for r in draft if r['id'].startswith('me-')]
    assert len(retained) == 56 and all(r in train for r in retained)
    for category in ['turkish_lexical_precision','non_anthropomorphic_interaction',
                     'selective_clarification','grounded_completion','useful_explanation','consistency_integrity']:
        assert sum(r['category']==category for r in retained) == 8
    leak = audit(new,train,validation)
    save(HERE/'data-draft-v1/candidates-24.jsonl',jsonl(new))
    save(HERE/'data-draft-v1/train-reviewed.jsonl',jsonl(draft))
    save(HERE/'data-draft-v1/validation-reviewed.jsonl',(PARENT/'reviewed-v2/validation-reviewed.jsonl').read_bytes())
    save(HERE/'data-draft-v1/leakage-report.json',encoded(leak))
    stream = io.StringIO(newline='')
    fields = ['id','category','scenario_group_id','replaces_id','prompt_tr','desired_answer','evaluation_criteria']
    writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
    writer.writeheader(); writer.writerows(new)
    save(HERE/'data-draft-v1/candidates-24.csv',stream.getvalue().encode('utf-8-sig'))
    manifest=dict(status='awaiting-human-review',training_started=False,retained_rows=56,new_rows=24,
        removed_ids=REMOVED, retained_ids=[r['id'] for r in retained],
        original_hashes=SOURCE_HASHES,draft_train_sha256=sha(jsonl(draft)),
        category_counts_A=dict(Counter(r['category'] for r in train)),
        category_counts_B=dict(Counter(r['category'] for r in draft)),
        authoring=dict(provider='OpenAI',interface='Codex project agent',exact_model='not exposed',
            date='2026-10-03',sampling='not exposed',external_generation_api=False,
            source_sha256=sha((HERE/'candidate_specs.py').read_bytes()),
            permission='User requested project-local draft examples; no third-party corpus copied; no public licensing claim'),
        substitution_policy='six rows each from grammar, extraction, numeric/entity and summary; keep two boundary controls per reduced family and all eight original rows in the other six families',
        order_policy='replace removed rows in their existing positions; no resorting of original retained rows',
        files={p.name:sha(p.read_bytes()) for p in (HERE/'data-draft-v1').iterdir() if p.name!='manifest.json'})
    save(HERE/'data-draft-v1/manifest.json',encoded(manifest))
    config_a=make_config(A.name,True)
    config_b=make_config(HERE.name,False, 'UNAPPROVED-DRAFT-NOT-A-TRAINING-HASH')
    save(A/'config.yaml',encoded(config_a)); save(HERE/'config.yaml',encoded(config_b))
    report_a=tokenize(train+validation,A/'training-preflight-v1',True,config_a,True)
    report_b=tokenize(draft+validation,HERE/'training-preflight-draft-v1',False,config_b)
    token_a=report_a['split_stats']['train']['target']['total']
    token_b=report_b['split_stats']['train']['target']['total']
    comparison=dict(status='A-needs-GPU-gates-B-needs-human-review',optimizer_steps_each=40,
        training_changes_A_vs_exp010=['epochs: 2 -> 4','expected optimizer steps: 20 -> 40'],
        training_changes_B_vs_A=[],dataset_changes_B_vs_A=dict(retain=56,replace=24),
        target_tokens_per_epoch=dict(A=token_a,B_draft=token_b),
        draft_target_token_change_percent=round(100*(token_b-token_a)/token_a,2),
        caveats=['A duration comparison includes extended cosine schedule.',
                 'B changes scenario/task composition, targets and supervised-token exposure; not isolated data quality.',
                 'Equal rows/steps do not mean equal token exposure or equal update magnitude.',
                 'Existing 20 are development, not independent final test.'],
        validation_original_sha256=SOURCE_HASHES['validation-reviewed.jsonl'],
        high_signal_ids=HIGH_SIGNAL,original_train_unchanged=True,training_started=False)
    save(HERE/'pair-preparation-report.json',encoded(comparison))
    original()
    print(json.dumps(comparison,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    prepare()
