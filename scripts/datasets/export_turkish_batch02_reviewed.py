"""Export submitted batch02 text edits and freeze semantic pilot160; never trains."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import statistics

from dotenv import load_dotenv
import requests
from tokenizers import Tokenizer
from audit_turkish_sources import ROOT, OUT, filehash, norm, messages
from audit_turkish_source_overlap import grams
from prepare_turkish_pilot80_sft import SYSTEM

BASE = OUT.parent
LOCAL = OUT / 'review-local/batch02'
DEST = BASE / 'sft-pilot160-v01'
DATASET = '2622bd70-e5e5-48af-8905-91a4ea47032f'


def read(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines()]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def main():
    load_dotenv(ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    url = os.getenv('ARGILLA_API_URL', 'http://127.0.0.1:6900').rstrip('/')
    response = requests.get(url+f'/api/v1/datasets/{DATASET}/records',
        params={'limit':100,'include':'responses'},
        headers={'X-Argilla-Api-Key':os.getenv('ARGILLA_API_KEY','argilla.apikey')}, timeout=30)
    response.raise_for_status()
    snapshot = response.json()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    snap = LOCAL / f'completed-text-reviews-{stamp}.json'
    assert not snap.exists()
    write(snap, snapshot)
    assert snapshot['total'] == len(snapshot['items']) == 80
    packet = read(LOCAL/'candidates80.jsonl')
    assert filehash(LOCAL/'candidates80.jsonl') == json.loads((LOCAL/'manifest.json').read_text())['packet_sha256']
    records = {r['external_id']:r for r in snapshot['items']}
    assert set(records) == {r['id'] for r in packet}
    new = []
    for candidate in packet:
        record = records[candidate['id']]
        assert len(record['responses']) == 1, candidate['id']
        review = record['responses'][0]
        assert review['status'] == 'submitted', f"Unfinished: {candidate['id']}"
        vals = review['values']
        inp = vals.get('input',{}).get('value','')
        thinking = vals.get('thinking',{}).get('value','') or ''
        output = vals.get('output',{}).get('value','')
        assert isinstance(inp,str) and inp.strip() and isinstance(output,str) and output.strip()
        assert isinstance(thinking,str)
        assert not re.search(r'</?(?:think|thinking)>', thinking+output), candidate['id']
        source = {k:v for k,v in candidate.items() if k.startswith('source_') or k=='original_record_sha256'}
        new.append(dict(id=candidate['id'], split='train', source_key=candidate['id'].split(':')[0],
            source=source, original_messages=candidate['original_messages'],
            messages=[dict(role='system',content=SYSTEM),dict(role='user',content=inp),dict(role='assistant',content=output)],
            worked_solution=thinking if thinking.strip() else None,
            reviewed_target=(f'<thinking>{thinking}</thinking>' if thinking.strip() else '')+output,
            review=dict(dataset_id=DATASET,record_id=record['id'],response=review,
                approval_basis='standing-owner-approval' if candidate['id'].startswith('occam:') else 'submitted-owner-text-review',
                no_quality_rating_inferred=True),
            supervision=dict(assistant_turns='final-only',worked_solution_separate=bool(thinking.strip())),
            intended_use='training-candidate', preparation_policy='shared-system-v01; submitted text authoritative; blank thinking means none',
            release_status='owner-content-reviewed; native-template and semantic-leakage gates pending'))
    old = read(BASE/'sft-pilot80-v01/train.jsonl')
    test = read(BASE/'sft-pilot80-v01/test.jsonl')
    train = old+new
    assert len(train)==160 and len({r['id'] for r in train})==160 and len(test)==20
    prompts = [norm(r['messages'][-2]['content']) for r in train]
    assert len(set(prompts))==160, 'Duplicate reviewed training prompts'
    assert not set(prompts) & {norm(r['messages'][-2]['content']) for r in test}
    protected = set()
    for row in test:
        for m in row['messages']:
            if m['role']!='system': protected.update(grams(m['content']))
        protected.update(grams(row.get('worked_solution') or ''))
    for row in read(OUT/'raw-local/occam/data/validation.jsonl'):
        for m in messages(row):
            if m['role']!='system': protected.update(grams(m['content']))
    cohort = BASE/'exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl'
    for row in read(cohort):
        d=row['document']
        texts=[row['semantic_prompt']]+[d[k] for k in ['question','context','text','source'] if isinstance(d.get(k),str)]+list(d.get('translation',{}).values())
        for text in texts: protected.update(grams(text))
    hits=[]
    for row in new:
        texts=[m['content'] for m in row['messages'] if m['role']!='system']+[row.get('worked_solution') or '']
        if any(grams(t)&protected for t in texts): hits.append(row['id'])
    assert not hits, f'Protected phrase matches need review: {hits}'
    near=[]
    for row in new:
        g=grams(row['messages'][-2]['content'],5)
        for ref in test:
            h=grams(ref['messages'][-2]['content'],5)
            if g and h and len(g&h)/min(len(g),len(h))>=.35: near.append([row['id'],ref['id']])
    assert not near, f'Near holdout prompts need review: {near}'
    tok=Tokenizer.from_file(str(OUT/'raw-local/tokenizer/tokenizer.json'))
    count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    stats={}
    for name,rows in [('new80',new),('combined160',train)]:
        bysource={}
        for key in ['occam','sft','atlas','cot']:
            selected=[r for r in rows if r['source_key']==key]
            lengths=[count((r.get('worked_solution') or '')+r['messages'][-1]['content']) for r in selected]
            bysource[key]=dict(rows=len(selected),reasoning_rows=sum(bool(r.get('worked_solution')) for r in selected),target_tokens=sum(lengths),min=min(lengths),median=statistics.median(lengths),max=max(lengths))
        stats[name]=bysource
    DEST.mkdir(exist_ok=True)
    artifacts={'batch02-train.jsonl':new,'train.jsonl':train}
    for name, rows in artifacts.items():
        data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
        path=DEST/name
        if path.exists(): assert path.read_text(encoding='utf-8')==data, 'Refusing to overwrite an existing frozen export'
        else: path.write_text(data,encoding='utf-8',newline='\n')
    target=DEST/'test.jsonl'
    original=(BASE/'sft-pilot80-v01/test.jsonl').read_bytes()
    if target.exists(): assert target.read_bytes()==original
    else: target.write_bytes(original)
    manifest=dict(status='semantic-frozen-not-training-ready',dataset_id=DATASET,snapshot_sha256=filehash(snap),
        packet_sha256=filehash(LOCAL/'candidates80.jsonl'),builder_sha256=filehash(Path(__file__)),
        old_train_sha256=filehash(BASE/'sft-pilot80-v01/train.jsonl'),counts=dict(train=160,new_train=80,test=20),
        submitted_responses=80,source_counts=dict(Counter(r['source_key'] for r in train)),statistics=stats,
        checks=dict(unique_train_ids=True,unique_normalized_train_prompts=True,test_bytes_unchanged=True,
            new80_protected_12gram_matches=hits,new80_holdout_5gram_containment_matches=near),
        limitations=['Selection was source/length stratified, not weakness-quota targeted.','Lexical checks do not establish semantic or cross-lingual independence.','Native rendered length, labels, EOS, smoke/tiny-overfit and separate development set remain launch gates.','Old20 is diagnostic/selection-used, not pristine final test.'],
        files={name:filehash(DEST/name) for name in ['batch02-train.jsonl','train.jsonl','test.jsonl']})
    write(DEST/'manifest.json',manifest)
    print(json.dumps(manifest,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
