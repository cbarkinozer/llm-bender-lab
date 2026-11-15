"""Pin/download four Turkish sources and build non-semantic, reproducible inventories.

Raw third-party text and review samples stay in ignored local directories.
String flags are triage signals, never admission or correctness judgments.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import sys
import unicodedata
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'experiments/turkish-capability/lfm3-1.7b/source-audit-v01'
SOURCES = {
 'occam': ('cbarkinozer/Occam-Turkish-Response-SFT', '947850d484c71f657dbec2bb7e3d356cb5fb23e3', ['data/train.jsonl','data/validation.jsonl']),
 'sft': ('AlicanKiraz0/Turkish-SFT-Dataset-v1.0','5a5a852ab9067866d72ed92381205518feaae5fb',['TR-part1-261025_v1-fixed.jsonl']),
 'atlas': ('AlicanKiraz0/Turkce-Atlas-Instruct','c387738c5deacbb35667ab4057930adc34e647e8',['train.chat.jsonl']),
 'cot': ('AlicanKiraz0/Turkish-CoT-Instruct-Dataset','3473e6c6350564d5a7000faf3ff140e9c4b9d1f2',['train.jsonl']),
}

def norm(s):
    return ' '.join(unicodedata.normalize('NFC',s).casefold().split())

def digest(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def filehash(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def stats(values):
    values=sorted(values)
    return dict(n=len(values), min=values[0], median=statistics.median(values),
                mean=statistics.mean(values),p90=values[int((len(values)-1)*.9)],max=values[-1])

def messages(row):
    if 'messages' in row:return row['messages']
    return [dict(role=k if k!='user' else 'user',content=row[k]) for k in ['system','user','assistant'] if row.get(k)]

def fetch(key):
    repo,revision,files=SOURCES[key]
    folder=OUT/'raw-local'/key
    folder.mkdir(parents=True,exist_ok=True)
    response=requests.get('https://huggingface.co/api/datasets/'+repo+'/revision/'+revision,params={'blobs':'true'},timeout=60)
    response.raise_for_status(); metadata=response.json()
    if metadata['sha']!=revision:raise ValueError('Revision mismatch')
    (folder/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    siblings={f['rfilename']:f for f in metadata['siblings']}
    wanted=files+[n for n in ['README.md','LICENSE','source-origins.json','release-manifest.json'] if n in siblings]
    receipts=[]
    for name in wanted:
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True)
        entry=siblings[name]
        expected=entry.get('lfs',{}).get('sha256')
        if not path.exists():
            temp=path.with_suffix(path.suffix+'.partial')
            with requests.get('https://huggingface.co/datasets/'+repo+'/resolve/'+revision+'/'+name,stream=True,timeout=(30,120)) as r:
                r.raise_for_status()
                with temp.open('wb') as f:
                    for block in r.iter_content(1024*1024):f.write(block)
            temp.replace(path)
        sha=filehash(path)
        if path.stat().st_size!=entry['size'] or (expected and sha!=expected):raise ValueError(f'Integrity failure: {key}/{name}')
        if not expected:
            content=path.read_bytes()
            git_blob=hashlib.sha1(b'blob '+str(len(content)).encode('ascii')+b'\0'+content).hexdigest()
            if git_blob!=entry['blobId']:raise ValueError(f'Pinned Git blob mismatch: {key}/{name}')
        receipts.append(dict(path=name,bytes=path.stat().st_size,sha256=sha,hub_lfs_sha256=expected))
    print('Downloaded and verified '+key,flush=True)
    return key,dict(repo=repo,revision=revision,declared_license=metadata.get('cardData',{}).get('license'),files=receipts)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool: receipts=dict(pool.map(fetch,SOURCES))
    (OUT/'download-manifest.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
    protected=defaultdict(set)
    benchmark=ROOT/'experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl'
    for line in benchmark.read_text(encoding='utf-8').splitlines():
        r=json.loads(line)
        protected[digest(norm(r['semantic_prompt']))].add('benchmark-prompt')
        doc=r['document']
        for field in ['question','context','text','source']:
            if isinstance(doc.get(field),str):protected[digest(norm(doc[field]))].add('benchmark-'+field)
        if 'translation' in doc:
            for text in doc['translation'].values():protected[digest(norm(text))].add('benchmark-translation')
    summary={};all_prompts=defaultdict(list); row_metadata={}; sample_views={}
    for key,(_,_,files) in SOURCES.items():
        counters=Counter(); roles=Counter(); systems=Counter(); metadata_fields=defaultdict(Counter)
        inputs=[];outputs=[];records=[];prompt_counts=Counter();pair_counts=Counter(); flags=Counter()
        for filename in files:
            with (OUT/'raw-local'/key/filename).open(encoding='utf-8-sig') as f:
                for number,line in enumerate(f,1):
                    row=json.loads(line);ms=messages(row)
                    users=[m['content'] for m in ms if m['role']=='user']
                    answers=[m['content'] for m in ms if m['role']=='assistant']
                    prompt='\n'.join(users);answer='\n'.join(answers)
                    row_id=key+':'+filename+':'+str(number)
                    ph=digest(norm(prompt)); ah=digest(norm(answer))
                    inputs.append(len(prompt));outputs.append(len(answer));prompt_counts[ph]+=1;pair_counts[(ph,ah)]+=1
                    counters['rows']+=1;roles[','.join(m['role'] for m in ms)]+=1
                    systems.update(m['content'] for m in ms if m['role']=='system')
                    for field in ['alan','alan_ad','akil_yurutme','zorluk','format','category','origin']:
                        if field in row:metadata_fields[field][str(row[field])]+=1
                    row_flags=[]
                    tests=dict(empty_prompt=not prompt.strip(),empty_answer=not answer.strip(),
                      replacement_character='\ufffd' in prompt+answer,
                      reasoning_tag='<think>' in answer,
                      reasoning_tag_unbalanced=answer.count('<think>')!=answer.count('</think>'),
                      multiple_user_turns=len(users)>1,
                      repeated_answer_line=any(n>=3 for s,n in Counter(answer.splitlines()).items() if len(s.strip())>=20))
                    for name,value in tests.items():
                        if value:flags[name]+=1;row_flags.append(name)
                    matches=set()
                    for candidate in [prompt,*users]:matches.update(protected.get(digest(norm(candidate)),set()))
                    if matches:flags['protected_exact_text_match']+=1;row_flags.append('protected_exact_text_match')
                    record=dict(id=row_id,source_row_id=row.get('id'),filename=filename,line=number,
                                input_characters=len(prompt),answer_characters=len(answer),
                                prompt_sha256=ph,answer_sha256=ah,flags=row_flags,
                                protected_match_types=sorted(matches),source_split='validation' if 'validation' in filename else 'train')
                    records.append(record);all_prompts[ph].append((key,row_id))
        order=sorted(range(len(records)),key=lambda i:(records[i]['answer_characters'],records[i]['id']))
        rng=random.Random(3407); chosen=set(rng.sample(range(len(records)),min(16,len(records))))
        for q in [0,.25,.5,.75,1]:
            position=int((len(order)-1)*q)
            chosen.update(order[max(0,position-2):min(len(order),position+3)])
        # Include representatives of declared categories/domains, not just length.
        wanted=set(chosen);original={};values_seen=defaultdict(set)
        cursor=0
        for filename in files:
            with (OUT/'raw-local'/key/filename).open(encoding='utf-8-sig') as f:
                for line in f:
                    row=json.loads(line)
                    for field in ['alan','category']:
                        if field in row and row[field] not in values_seen[field]:wanted.add(cursor);values_seen[field].add(row[field])
                    if cursor in wanted:original[cursor]=row
                    cursor+=1
        review=OUT/'review-local';review.mkdir(exist_ok=True)
        samples=[dict(**records[i],original=original[i]) for i in sorted(wanted)]
        (review/(key+'-samples.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in samples),encoding='utf-8')
        (review/(key+'-row-index.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
        summary[key]=dict(rows=counters['rows'],input_characters=stats(inputs),answer_characters=stats(outputs),
            role_sequences=dict(roles),unique_system_prompts=len(systems),top_system_prompt_sha256=[dict(sha256=digest(s),count=n) for s,n in systems.most_common(5)],
            metadata={k:dict(v) for k,v in metadata_fields.items()},flags=dict(flags),
            duplicate_prompt_excess=sum(n-1 for n in prompt_counts.values()),duplicate_pair_excess=sum(n-1 for n in pair_counts.values()),
            sampled_rows=len(samples),sampling='seed3407 random16 + adjacent answer-length quantiles + first declared category/domain representatives; purposive, not an error-rate estimate')
        print('Inventoried '+key+': '+str(counters['rows'])+' rows; '+str(len(samples))+' review samples',flush=True)
    cross=[dict(prompt_sha256=h,rows=rows) for h,rows in all_prompts.items() if len({k for k,_ in rows})>1]
    (OUT/'cross-source-exact-prompts.json').write_text(json.dumps(cross,indent=2)+'\n',encoding='utf-8')
    report=dict(sources=summary,cross_source_exact_prompt_groups=len(cross),
        protected_cohort_sha256=filehash(benchmark),
        analyzer_sha256=filehash(Path(__file__)),normalization='NFC + casefold + whitespace collapse; hashes of user content only, system excluded',
        limitations=['Static flags and metadata do not establish semantic quality or absence of leakage.',
          'Protected checks cover exact entire user messages/prompt vs 500 known prompts/questions/source documents; no fuzzy or cross-lingual clearance.',
          'Lengths are Unicode characters, not model tokens or training exposure.',
          'Source validation rows are not training candidates; all samples remain unapproved.'])
    (OUT/'static-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
