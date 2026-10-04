"""CPU-only, immutable E/F drafts and separately frozen control candidates.

Run with the existing tokenizer-only CPU venv. No GPU, base inference, W&B,
credentials, or training. Draft reports/configs deliberately cannot train.
"""
import copy
import csv
import hashlib
import io
import json
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
C = ROOT / 'exp-013-targeted-coverage-sft'
F = ROOT / 'exp-016-diverse-coverage-sft'
DRAFT = 'data-draft-v3'
PREFLIGHT = 'training-preflight-draft-v3'
CONTROL_DRAFT = 'controls-draft-v3'
REPORT = 'pair-preparation-report-v3.json'
sys.path.insert(0, str(ROOT / 'exp-009-minimal-edit'))
from prepare_training import encode_final, stats
sys.path.insert(0, str(HERE))
from specs import AUDIT_GROUPS, REPAIRS, NEW_TRAIN
from control_specs import CONTROLS

HASHES = {
    'train-reviewed.jsonl': 'd61bdfab544dc0d3ba5531e74005940d47b6b6af38fba864dbd5ceefcf948d7a',
    'validation-reviewed.jsonl': '43e10beed85aa6fbbda768a124c7a2e6feb3743ddc79c2e38098c7982cfad429',
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def jsonl(rows):
    return ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode('utf-8')

def load(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]

def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == raw:
            return
        raise ValueError('Immutable output exists with different bytes: ' + str(path))
    path.write_bytes(raw)

def original():
    for name, expected in HASHES.items():
        assert sha((C/'data-reviewed-v1'/name).read_bytes()) == expected, name
    return load(C/'data-reviewed-v1/train-reviewed.jsonl'), load(C/'data-reviewed-v1/validation-reviewed.jsonl')

def records(specs, control=False):
    result = []
    for i, (category, skill, scenario, turns, answer, rubric) in enumerate(specs, 1):
        messages = [dict(role=role, content=text) for role, text in turns]
        result.append(dict(id=('ef-control-' if control else 'ef-new-') + f'{i:03}',
            category=category, skill=skill, subtype=scenario, scenario_group_id='ef-'+scenario,
            split='control' if control else 'train', evaluation_only=control,
            messages=messages, prompt_tr='\n\n'.join(m['role']+': '+m['content'] for m in messages),
            desired_answer=answer, evaluation_criteria=rubric,
            source_path=HERE.relative_to(ROOT).as_posix()+'/'+('control_specs.py' if control else 'specs.py'),
            source_id=scenario, origin='new-project-agent-authored', authored_date='2026-10-04',
            answer_status='draft-awaiting-human-review', review_decision='pending',
            dataset_version='ef-draft-v3', loss_policy='evaluation-only; never gradients' if control else
            'final assistant only; all earlier turns masked'))
    return result

def drafts():
    train, validation = original()
    audited = [id_ for ids in AUDIT_GROUPS.values() for id_ in ids]
    assert len(audited) == len(set(audited)) == 24
    assert set(REPAIRS) <= set(audited) <= {r['id'] for r in train}
    e, audit = copy.deepcopy(train), []
    for row in e:
        if row['id'] not in audited:
            continue
        old = row['desired_answer']
        answer, reason = REPAIRS.get(row['id'], (old, 'Hedef doğru ve yeterli; zorunlu değişiklik yok.'))
        changed = answer != old
        skill = next(k for k, ids in AUDIT_GROUPS.items() if row['id'] in ids)
        audit.append(dict(id=row['id'], category=row['category'], skill=skill, messages=row['messages'],
            prompt_tr='\n\n'.join(m['role']+': '+m['content'] for m in row['messages']),
            original_answer=old, desired_answer=answer, reason=reason,
            intervention='repair' if changed else 'retain', review_decision='pending' if changed else 'unchanged-approved-parent',
            source_path='exp-013-targeted-coverage-sft/data-reviewed-v1/train-reviewed.jsonl',
            source_sha256=HASHES['train-reviewed.jsonl'], answer_status='draft-awaiting-human-review' if changed else row['answer_status']))
        if changed:
            row.update(desired_answer=answer, parent_desired_answer=old,
                answer_status='draft-awaiting-human-review', review_decision='pending',
                dataset_version='ef-draft-v3', repair_reason=reason,
                repair_source='exp-015-target-quality-sft/specs.py')
    new, controls = records(NEW_TRAIN), records(CONTROLS, True)
    assert len(new) == 24 and len(controls) == 12
    assert Counter(r['skill'] for r in new) == {k:4 for k in AUDIT_GROUPS}
    assert Counter(r['skill'] for r in controls) == {k:2 for k in AUDIT_GROUPS}
    assert [r['messages'] for r in e] == [r['messages'] for r in train]
    assert [r['id'] for r in e] == [r['id'] for r in train]
    assert [r['category'] for r in e] == [r['category'] for r in train]
    assert all(a == b for a,b in zip(e,train) if a['id'] not in REPAIRS)
    return train, e, e+new, validation, new, controls, audit

def norm(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())

def views(row):
    return list(dict.fromkeys([norm(m['content']) for m in row['messages']]
        + [norm('\n'.join(m['content'] for m in row['messages']))]))

def score(a, b, threshold):
    maximum = 0.
    for x in a:
        for y in b:
            matcher = SequenceMatcher(None,x,y,autojunk=False)
            if matcher.quick_ratio() >= threshold:
                maximum = max(maximum, matcher.ratio())
    return maximum

def leakage(train, validation, new, controls):
    # Preserve old inventories, including overlapping historical versions; counts
    # are entries scanned, NOT distinct independent questions.
    inventory = json.loads((ROOT/'exp-009-minimal-edit/data/audit-report.json').read_text(encoding='utf-8'))
    refs, files = [], {}
    for path, info in inventory['benchmark_inputs'].items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == info['sha256_bytes'], path
        files[path] = dict(sha256=sha(raw), kind='historical-benchmark')
        for i, row in enumerate(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))):
            text = row.get('prompt_tr') or row.get('prompt') or ''
            if text:
                refs.append((path, row.get('id',str(i)), [norm(text)], .78))
    old_meta = json.loads((C/'data-reviewed-v1/leakage-report.json').read_text(encoding='utf-8'))
    for path, expected in old_meta['source_inventory'].items():
        if path in files:
            continue
        source = ROOT/path
        if source.suffix not in ('.jsonl', '.csv'):
            continue
        raw = source.read_bytes()
        assert sha(raw) == expected['sha256_bytes'], path
        files[path] = dict(sha256=sha(raw), kind='historical-train')
        source_rows = load(source) if source.suffix=='.jsonl' else list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        for row in source_rows:
            messages = row.get('messages') or row.get('prompt_messages') or []
            if isinstance(messages,str):
                messages = json.loads(messages)
            refs.append((path,row['id'],[norm(m['content']) for m in messages if m['role']=='user'],.78))
    bpath = ROOT/'exp-012-coverage-ablation/data-reviewed-v1/train-reviewed.jsonl'
    files[str(bpath.relative_to(ROOT)).replace('\\','/')] = dict(sha256=sha(bpath.read_bytes()),kind='earlier-B')
    refs += [('earlier-B',r['id'],views(r),.78) for r in load(bpath) if r['id'].startswith('bc-')]
    historical_n = len(refs)
    refs += [('current-train',r['id'],views(r),.78) for r in train]
    refs += [('current-validation',r['id'],views(r),.60) for r in validation]
    flags, exact, nearest = [], [], []
    # New rows against all inventories; controls also against the entire E/F
    # train. Existing train is checked against controls and frozen validation.
    for row in new+controls:
        references = refs + [('new-train',r['id'],views(r),.60) for r in new] if row['evaluation_only'] else refs
        near_validation = []
        for source, other_id, texts, threshold in references:
            s = score(views(row), texts, threshold)
            if s == 1:
                exact.append(dict(id=row['id'],other_id=other_id,source=source))
            elif s >= threshold:
                flags.append(dict(id=row['id'],other_id=other_id,source=source,similarity=round(s,4),threshold=threshold))
            if source == 'current-validation':
                near_validation.append(dict(id=row['id'],other_id=other_id,similarity=round(s,4)))
        nearest.extend(sorted(near_validation,key=lambda x:x['similarity'],reverse=True)[:2])
    for i, row in enumerate(new+controls):
        for other in (new+controls)[i+1:]:
            threshold = .60 if row['evaluation_only'] != other['evaluation_only'] else .78
            s = score(views(row),views(other),threshold)
            if s >= threshold:
                dest = exact if s==1 else flags
                dest.append(dict(id=row['id'],other_id=other['id'],source='new-internal',similarity=round(s,4),threshold=threshold))
    for row in train:
        for other in validation:
            s = score(views(row),views(other),.60)
            if s >= .60:
                (exact if s==1 else flags).append(dict(id=row['id'],other_id=other['id'],source='existing-train-validation',similarity=round(s,4)))
    assert not ({r['scenario_group_id'] for r in train+new} & {r['scenario_group_id'] for r in validation+controls})
    return dict(status='passed-no-detected-overlap' if not exact and not flags else 'requires-overlap-review',
        exact_matches=exact, near_flags=flags, historical_entries_scanned=historical_n,
        current_train=80, current_validation=20, new_train=24, controls=12,
        source_inventory=files, nearest_validation_above_quick_bound=nearest,
        thresholds=dict(evaluation=.60, other=.78),
        semantic_review='Capability taxonomy only, not item-level prompts/solutions. New scenarios: warehouse, letter, drawer, doctoral education, museum bag, sewing, rental, export, shared queue, bakery, choir, minutes, exhibit review, library poll, ventilation, ceramics, absent text, lesson audience, games, ironing, disagreement, club boundary, puzzle, art participation. Controls independently authored in separate scene groups; no cafe sign, morning departure, desk/light division, exam venting, home belonging, presentation timing or mayor announcement derivatives.',
        limitation='Lexical checks plus agent provenance/scene review are not a proof of semantic independence. Shared generic behavior/task families are intentional. Threshold flags require review, not automatic deletion. Historical versions overlap.')

def config(arm):
    result = json.loads((C/'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
    folder = HERE if arm=='E' else F
    result.update(experiment_id=folder.name, parent=C.name if arm=='E' else HERE.name, status='blocked-human-review')
    result['dataset'].update(train='../'+folder.name+'/data-reviewed-v1/train-reviewed.jsonl',
        train_rows=80 if arm=='E' else 104, validation_rows=20, review_required=True,
        review_status='pending-target-repairs-and-new-records')
    result['dataset']['hashes']['train-reviewed.jsonl'] = 'UNAPPROVED-DRAFT-NOT-A-TRAINING-HASH'
    result['training'].update(max_steps=40, epochs=4, expected_optimizer_steps=40,
        save_strategy='steps', eval_strategy='steps', save_steps=10, eval_steps=10)
    result['tracking']['run_name'] = f'exp0{15 if arm=="E" else 16}-sft-'+('target-quality-80rows' if arm=='E' else 'diverse-104rows')+'-40steps'
    result['notes'] = [
        'Fresh pinned base for each arm; never initialize F from E adapter.',
        'E retains exact C80 prompts/IDs/order/categories; only necessary reviewed target repairs.',
        'F contains exact approved E80 plus24 independent reviewed new examples (4/skill).',
        'Explicit max_steps40 overrides epochs4 in full mode; F about3.08epochs, E4epochs.',
        'Same40-step cosine horizon and2 warmup; steps/save/eval10, final step40 preselected.',
        'Equal optimizer steps are not equal supervised-token exposure or equal update size.',
        '20 original development references unchanged incl disputed me089; sensitivity excludes089.',
        '12 separate controls never enter train/validation loss/replay; approve/freeze before outputs.',
        'Base,C,E,F generated under identical HF/Unsloth settings; historical vLLM base not canonical.',
        'Same-generation non-thinking protocol; cannot infer thinking-mode retention.',
        'No inherited GPU-gate waiver for new pair; environment/masks/W&B and required gates still needed.',
        'Paths resolved relative to shared exp009 runner; draft config cannot train.',
    ]
    return result

def tokenize(rows, output, conf, approved=False):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(conf['model']['name'],revision=conf['model']['revision'],local_files_only=True)
    template = json.loads((C/'training-preflight-v1/tokenizer-template.json').read_text(encoding='utf-8'))
    assert sha(tokenizer.chat_template.encode()) == template['template_sha256']
    prepared, inspected = [], []
    for row in rows:
        item,p,t = encode_final(tokenizer,row)
        assert len(item['input_ids']) <= conf['training']['max_seq_length'], row['id']
        assert all(x==-100 for x in item['labels'][:p]) and t>1
        assert [x for x in item['labels'] if x!=-100][-1] == tokenizer.convert_tokens_to_ids('<|im_end|>')
        prepared.append(dict(id=row['id'],split=row['split'],category=row['category'],prompt_tokens=p,target_tokens=t,**item))
        if row['id'] in REPAIRS or row['id'].startswith('ef-'):
            inspected.append(dict(id=row['id'],full_text=tokenizer.decode(item['input_ids'],skip_special_tokens=False),
                supervised_text=tokenizer.decode([x for x in item['labels'] if x!=-100],skip_special_tokens=False)))
    files = {}
    splits = sorted({r['split'] for r in rows})
    for s in splits:
        name = s+'-tokenized.jsonl'
        raw = jsonl([r for r in prepared if r['split']==s]); save(output/name,raw); files[name]=sha(raw)
    if 'validation' in splits:
        assert [r for r in prepared if r['split']=='validation'] == load(C/'training-preflight-v1/validation-tokenized.jsonl')
    if conf['experiment_id']==HERE.name and 'train' in splits:
        prior={r['id']:r for r in load(C/'training-preflight-v1/train-tokenized.jsonl')}
        assert all(r==prior[r['id']] for r in prepared if r['split']=='train' and r['id'] not in REPAIRS)
    for name, raw in [('mask-inspection.json',encoded(inspected)),('tokenizer-template.json',encoded(template)),('training-config.json',encoded(conf))]:
        save(output/name,raw); files[name]=sha(raw)
    report = dict(status='local-preflight-passed' if approved else 'draft-not-approved',splits={s:sum(r['split']==s for r in rows) for s in splits},
        split_stats={s:{'sequence':stats([len(r['input_ids']) for r in prepared if r['split']==s]),
            'target':stats([r['target_tokens'] for r in prepared if r['split']==s])} for s in splits},
        max_seq_length=1024,truncated_rows=0,zero_target_rows=0,
        all_context_tokens_masked=True,native_final_end_of_turn_supervised=True,files=files,
        validation_tokenization_matches_parent='validation' in splits,training_started=False,
        remaining=['human target/new/control review','hash-bound approved freeze','GPU environment/actual masking/W&B','required GPU gates'])
    save(output/'report.json',encoded(report))
    return report

def prepare():
    train,e,f,validation,new,controls,audit = drafts()
    leak = leakage(train,validation,new,controls)
    # Keep analysis even if a flag blocks preparation; no approved configs exist.
    save(HERE/DRAFT/'leakage-report.json',encoded(leak))
    if leak['exact_matches'] or leak['near_flags']:
        raise ValueError('Overlap review required: see '+DRAFT+'/leakage-report.json')
    repairs=[r for r in audit if r['intervention']=='repair']
    for name,rows in [('target-audit-24.jsonl',audit),('target-repairs.jsonl',repairs),('new-train-24.jsonl',new)]:
        save(HERE/DRAFT/name,jsonl(rows))
    for folder,rows in [(HERE,e),(F,f)]:
        save(folder/DRAFT/'train-reviewed.jsonl',jsonl(rows))
        save(folder/DRAFT/'validation-reviewed.jsonl',(C/'data-reviewed-v1/validation-reviewed.jsonl').read_bytes())
    save(HERE/CONTROL_DRAFT/'questions-12.jsonl',jsonl(controls))
    review = [dict(r,review_kind='repair') for r in repairs]+[dict(r,review_kind='new-train') for r in new]
    save(HERE/DRAFT/'review-candidates.jsonl',jsonl(review))
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=['id','review_kind','skill','prompt_tr','original_answer','desired_answer','reason','evaluation_criteria'],extrasaction='ignore',lineterminator='\n')
    writer.writeheader(); writer.writerows(review)
    save(HERE/DRAFT/'review-candidates.csv',stream.getvalue().encode('utf-8-sig'))
    reports={}
    for arm,folder,rows in [('E',HERE,e),('F',F,f)]:
        conf=config(arm); save(folder/'config.yaml',encoded(conf))
        reports[arm]=tokenize(rows+validation,folder/PREFLIGHT,conf)
    tokenize(controls,HERE/'control-preflight-draft-v3',config('E'))
    assert load(F/PREFLIGHT/'train-tokenized.jsonl')[:80] == load(HERE/PREFLIGHT/'train-tokenized.jsonl')
    report=dict(status='draft-CPU-passed-human-review-required',training_started=False,
        audit_rows=24,actual_repairs=len(repairs),retained_audited_rows=24-len(repairs),new_train_rows=24,
        controls=12,train_rows=dict(E=80,F=104),validation_rows=20,optimizer_steps_each=40,
        source_hashes=HASHES,parent_prompts_ids_categories_order_preserved=True,
        F_first80_identical_to_E=True,validation_unchanged=True,
        target_tokens_per_dataset={a:r['split_stats']['train']['target']['total'] for a,r in reports.items()},
        expected_example_presentations=dict(E=320,F=320),
        target_token_exposure_note='Actual shuffled40-step token exposure must be measured at runtime; F fewer passes per record. Dataset totals are not runtime totals.',
        authoring=dict(provider='OpenAI',interface='Codex project agent',exact_model='not exposed',sampling='not exposed',external_generation_api=False,date='2026-10-04',
            brief='Approved six skill families; repair necessary existing targets only;24 independent new train;12 separate controls; no evaluation question seeds or third-party text.',
            permission='User authorized project-local drafts; no third-party dataset/API used; no publication/license assertion.'),
        limitation='No claims of guaranteed zero semantic leakage, forgetting prevention or model superiority.',
        files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for folder in (HERE,F)
            for pattern in (DRAFT+'/*',CONTROL_DRAFT+'/*','config.yaml','specs.py','control_specs.py','prepare_pair.py') for p in folder.glob(pattern) if p.is_file()})
    save(HERE/REPORT,encoded(report))
    original()
    print(json.dumps({k:report[k] for k in ('status','actual_repairs','retained_audited_rows','new_train_rows','controls','train_rows','target_tokens_per_dataset','training_started')},ensure_ascii=False,indent=2))

if __name__=='__main__':
    prepare()
