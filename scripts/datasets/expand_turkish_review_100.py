"""Freeze an 80/20 source-balanced review allocation; optionally append in Argilla.

Preserves the original 60 packet and all existing annotations. No training export.
"""
import argparse
from collections import Counter
import json
import os
import random
from pathlib import Path

from audit_turkish_sources import ROOT, OUT, SOURCES, messages, norm, digest, filehash
from audit_turkish_source_overlap import grams


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]


def prompt(row):
    return '\n'.join(m['content'] for m in row['original_messages'] if m['role']=='user')


def prepare():
    manifest_path = OUT/'review-100-manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for split in ['train', 'test']:
            if filehash(OUT/manifest['packets'][split]['path']) != manifest['packets'][split]['sha256']:
                raise ValueError('Frozen packet changed')
        return manifest
    original = read(OUT/'review-local/calibration-60.jsonl')
    assert len(original) == 60
    selected = [dict(row, assigned_split='train', reserved_use='training-candidate-review-only') for row in original]
    seen = {r['source_prompt_sha256'] for r in selected}
    protected = set()
    cohort = ROOT/'experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl'
    for row in read(cohort):
        doc = row['document']
        texts = [row['semantic_prompt']] + [doc[k] for k in ['question','context','text','source'] if isinstance(doc.get(k), str)] + list(doc.get('translation', {}).values())
        for text in texts:
            protected.update(grams(text))
    for row in read(OUT/'raw-local/occam/data/validation.jsonl'):
        for msg in messages(row):
            if msg['role'] == 'user': protected.update(grams(msg['content']))
    # Avoid known duplicate prompt families, structural defects and previously
    # inspected samples for the new held-out records.
    for key, (repo, revision, files) in SOURCES.items():
        index = read(OUT/'review-local'/f'{key}-row-index.jsonl')
        counts = Counter(r['prompt_sha256'] for r in index)
        prior_sample_ids = {r['id'] for r in read(OUT/'review-local'/f'{key}-samples.jsonl')}
        candidates = [r for r in index if r['source_split']=='train' and not r['flags'] and counts[r['prompt_sha256']]==1 and r['prompt_sha256'] not in seen and r['answer_characters']>=20]
        # Reasoning tags are expected, not a structural defect.
        if key == 'cot':
            candidates = [r for r in index if r['source_split']=='train' and set(r['flags']) <= {'reasoning_tag'} and counts[r['prompt_sha256']]==1 and r['prompt_sha256'] not in seen and r['answer_characters']>=20]
        random.Random(3408).shuffle(candidates)
        # Five fresh holdout rows first, then five additional training candidates.
        choices = []
        for split in ['test', 'train']:
            pool = [r for r in candidates if r['prompt_sha256'] not in seen and (split!='test' or r['id'] not in prior_sample_ids)]
            ordered = sorted(pool, key=lambda r: r['answer_characters'])
            # Use middle positions in each length stratum rather than extremes.
            targets = [ordered[min(len(ordered)-1, int((i+.5)*len(ordered)/5))] for i in range(5)]
            for target in targets:
                choices.append((split, target)); seen.add(target['prompt_sha256'])
        wanted = {(r['filename'],r['line']):(split,r) for split,r in choices}
        for filename in files:
            if 'validation' in filename: continue
            for number, raw in enumerate((OUT/'raw-local'/key/filename).open(encoding='utf-8-sig'),1):
                if (filename,number) not in wanted: continue
                split, meta = wanted[(filename,number)]
                source = json.loads(raw); ms = messages(source)
                p = '\n'.join(m['content'] for m in ms if m['role']=='user')
                if grams(p) & protected: raise ValueError('Protected phrase overlap; inspect before choosing replacement')
                if ms[-1]['role']!='assistant': raise ValueError('Missing assistant target')
                selected.append(dict(id=meta['id'],source_repo=repo,source_revision=revision,
                    source_filename=filename,source_line_1based=number,source_row_id=source.get('id'),
                    original_messages=ms,source_category=source.get('category',source.get('alan')),
                    original_record_sha256=digest(json.dumps(source,ensure_ascii=False,sort_keys=True)),
                    source_prompt_sha256=meta['prompt_sha256'],source_answer_sha256=meta['answer_sha256'],
                    source_split='train',assigned_split=split,
                    reserved_use='held-out-test-only' if split=='test' else 'training-candidate-review-only',
                    review_status='pending',human_reviewed=False,training_eligible=False,
                    owner_decision=None,corrected_answer=None,owner_notes=None,
                    provenance_status='source-audit-provisional; not a training/release clearance'))
    assert len(selected)==100 and len({r['id'] for r in selected})==100 and len({r['source_prompt_sha256'] for r in selected})==100
    train=[r for r in selected if r['assigned_split']=='train'];test=[r for r in selected if r['assigned_split']=='test']
    # Phrase-family review candidates, excluding ubiquitous system instructions.
    similarities=[]
    for a in train:
        ga=grams(prompt(a),5)
        for b in test:
            gb=grams(prompt(b),5)
            overlap=len(ga & gb)/max(1,min(len(ga),len(gb)))
            if overlap>=.35: similarities.append(dict(train=a['id'],test=b['id'],containment=overlap))
    if similarities: raise ValueError(f'Cross-split phrase families require review: {similarities}')
    packets={}
    for split, rows in [('train',train),('test',test)]:
        assert Counter(r['source_repo'] for r in rows)==Counter({repo:20 if split=='train' else 5 for repo,_,_ in SOURCES.values()})
        path=OUT/'review-local'/f'review-100-{split}.jsonl'
        if path.exists(): raise FileExistsError(path)
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
        packets[split]=dict(path=str(path.relative_to(OUT)).replace('\\','/'),sha256=filehash(path),n=len(rows),ids=[r['id'] for r in rows])
    manifest=dict(seed=3408,packets=packets,original_60_sha256=filehash(OUT/'review-local/calibration-60.jsonl'),
        builder_sha256=filehash(Path(__file__)),source_counts_per_split={'train':{k:20 for k in SOURCES},'test':{k:5 for k in SOURCES}},
        protected_cohort_sha256=filehash(cohort),cross_split_exact_prompts=0,cross_split_5gram_containment_ge_035=similarities,
        selection='Original 60 preserved in train; add five train and five previously unsampled test rows per source across answer-length quintiles.',
        limitations=['Allocation is not an accepted training dataset. Review and replacement still required.',
          'No semantic/cross-lingual family clearance or unknown benchmark clearance; manually verify before training.',
          'Public source data may have been seen in pretraining; no claim of pristine model-unseen testing.',
          'Twenty test items form a small pilot, not a broad capability benchmark. Never use for gradient updates or checkpoint/tuning decisions.',
          'Keep Occam original validation separate; source_split and assigned_split have different meanings.'])
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


def publish(manifest):
    import argilla as rg
    env=ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            k,sep,v=line.partition('=')
            if sep and k.strip() in ['ARGILLA_API_KEY','ARGILLA_WORKSPACE']: os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
    client=rg.Argilla(api_url='http://127.0.0.1:6900',api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    workspace=os.getenv('ARGILLA_WORKSPACE','sft-review')
    existing=client.datasets(name='turkish-sft-source-calibration-v01',workspace=workspace)
    if existing is None: raise ValueError('Original review dataset missing')
    receipt={}
    for split in ['train','test']:
        rows=read(OUT/manifest['packets'][split]['path'])
        if split=='train': dataset=existing
        else:
            name='turkish-sft-holdout-test-v01'
            dataset=client.datasets(name=name,workspace=workspace)
            if dataset is None:
                settings=rg.Settings(fields=existing.settings.fields,questions=existing.settings.questions,
                    metadata=existing.settings.metadata,
                    guidelines='HELD-OUT TEST ONLY: never train on these records or their edits/variants. Review reference correctness before freezing. Do not use test results for model/checkpoint selection. '+existing.settings.guidelines)
                dataset=rg.Dataset(name=name,workspace=workspace,settings=settings,client=client).create()
        before=list(dataset.records)
        snapshot={str(r.id):r.to_dict() for r in before}
        expected={r['id'] for r in rows}
        if not set(snapshot)<=expected: raise ValueError('Unexpected existing records; refusing mutation')
        additions=[]
        for row in rows:
            if row['id'] in snapshot: continue
            ms=row['original_messages'];answer=ms[-1]['content'];reason=''
            if answer.startswith('<think>') and answer.count('<think>')==answer.count('</think>')==1:
                reason,answer=answer[7:].split('</think>',1);reason=reason.strip();answer=answer.strip()
            additions.append(rg.Record(id=row['id'],fields=dict(source=('HELD-OUT TEST ONLY\n' if split=='test' else 'TRAINING CANDIDATE\n')+row['source_repo']+' @ '+row['source_revision']+'\n'+row['source_filename']+':'+str(row['source_line_1based']),
                system='\n'.join(m['content'] for m in ms if m['role']=='system'),
                conversation='\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in ms[:-1] if m['role']!='system'),worked_solution=reason,answer=answer),metadata={'source_key':row['id'].split(':')[0]}))
        if additions: dataset.records.log(additions,batch_size=20)
        after={str(r.id):r.to_dict() for r in dataset.records}
        if set(after)!=expected: raise ValueError('Readback IDs mismatch')
        if any(after[k]!=v for k,v in snapshot.items()): raise ValueError('Existing records changed during append')
        receipt[split]=dict(dataset_id=str(dataset.id),n=len(after),added=len(additions),existing_records_and_responses_unchanged=True,
            url='http://127.0.0.1:6900/dataset/'+str(dataset.id)+'/annotation-mode')
    (OUT/'argilla-review-100-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    manifest=prepare()
    if args.publish: publish(manifest)
    else: print('Frozen 80 training candidates and 20 held-out test candidates; 20/5 per source.')
