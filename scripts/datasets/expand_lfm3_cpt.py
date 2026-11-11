"""Prepare a candidate larger corpus without activating it or changing evaluation."""
import argparse
from collections import Counter,defaultdict
import hashlib
import heapq
import json
from pathlib import Path
import statistics
from prepare_lfm3_cpt import norm,shingles,sha,records,download,WIKI_REV


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--experiment-dir',type=Path,required=True)
    p.add_argument('--cache-root',type=Path,required=True)
    p.add_argument('--target-tokens',type=int,default=10_000_000)
    a=p.parse_args();base=a.experiment_dir
    from transformers import AutoTokenizer
    cfg=json.loads((base/'config-planned.json').read_text())['model']
    tokenizer=AutoTokenizer.from_pretrained(cfg['repo'],revision=cfg['revision'])
    original=base/'data-local/cpt-v02'
    parent=json.loads((base/'cpt-data-manifest-v02.json').read_text())
    assert sha((base/'data-local/questions-500.jsonl').read_bytes())==parent['benchmark_sha256']
    assert sha((base/'data-local/turblimp-1600.jsonl').read_bytes())==parent['turblimp_sha256']
    groups={}
    for key,receipt in parent['splits'].items():
        blob=(original/(key+'.jsonl')).read_bytes()
        assert sha(blob)==receipt['sha256']
        groups[key]=[json.loads(s) for s in blob.decode().splitlines()]
    train=list(groups['wiki_train']);old_ids={r['id'] for rows in groups.values() for r in rows}
    token_lengths=[len(ids) for ids in tokenizer([r['text'] for r in train],add_special_tokens=False)['input_ids']]
    tokens=sum(token_lengths)
    if a.target_tokens<=tokens:raise ValueError('Expansion target must exceed the original training corpus')
    index=defaultdict(set);sizes=[];seen=set();paragraphs=set()
    def add(text,whole=False):
        words=shingles(text);idx=len(sizes);sizes.append(len(words))
        for word in words:index[word].add(idx)
        if whole:
            seen.add(sha(norm(text).encode()))
            paragraphs.update(sha(norm(s).encode()) for s in text.split('\n') if len(norm(s))>=200)
    for rows in groups.values():
        for row in rows:add(row['text'],True)
    for line in (base/'data-local/turblimp-1600.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line);add(row['sentence_good']);add(row['sentence_bad'])
    for line in (base/'data-local/questions-500.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line);add(row['semantic_prompt']);doc=row['document']
        for key in ('text','context','source','target','summary'):
            if isinstance(doc.get(key),str):add(doc[key])
        if isinstance(doc.get('translation'),dict):
            for text in doc['translation'].values():add(text)
    heap=[];counts=Counter();sources=[]
    for shard in range(2):
        path,source=download('wikimedia/wikipedia',WIKI_REV,f'20231101.tr/train-{shard:05}-of-00002.parquet',a.cache_root)
        sources.append(source)
        for doc in records(path):
            counts['scanned']+=1;identity='wiki-'+str(doc['id'])
            if identity in old_ids:continue
            cleaned=norm(doc['text'])
            if not 500<=len(cleaned)<=20000 or sum(c.isalpha() for c in cleaned)/len(cleaned)<.65:
                continue
            rank=int(sha(('lfm3-cpt-v1-3407:'+str(doc['id'])).encode()),16)
            entry=(-rank,identity,doc)
            if len(heap)<25000:heapq.heappush(heap,entry)
            elif entry[:2]>heap[0][:2]:heapq.heapreplace(heap,entry)
        print('Scanned shard '+str(shard),flush=True)
    for _,identity,doc in sorted(heap,key=lambda item:(-item[0],item[1])):
        text=doc['text'];digest=sha(norm(text).encode())
        paras={sha(norm(s).encode()) for s in text.split('\n') if len(norm(s))>=200}
        if digest in seen or paras&paragraphs:
            counts['document_or_paragraph_duplicate_excluded']+=1;continue
        words=shingles(text);hits=Counter(i for word in words for i in index.get(word,()))
        if any(count/min(len(words),sizes[i])>=.8 for i,count in hits.items()):
            counts['protected_or_selected_overlap_excluded']+=1;continue
        length=len(tokenizer(text,add_special_tokens=False)['input_ids'])
        train.append(dict(id=identity,title=doc['title'],url=doc['url'],text=text,
            source='wikimedia/wikipedia',source_revision=WIKI_REV,normalized_text_sha256=digest))
        add(text,True);token_lengths.append(length);tokens+=length
        if len(train)%1000==0:print(f'{len(train)} documents; {tokens} raw tokens',flush=True)
        if tokens>=a.target_tokens:break
    if tokens<a.target_tokens:raise ValueError('Candidate pool cannot meet token budget')
    groups['wiki_train']=train
    output=base/'data-local/cpt-10m-candidate-v01';output.mkdir(exist_ok=False)
    receipts={}
    for name,rows in groups.items():
        blob=(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows).encode()
            if name=='wiki_train' else (original/(name+'.jsonl')).read_bytes())
        (output/(name+'.jsonl')).write_bytes(blob)
        receipts[name]=dict(count=len(rows),sha256=sha(blob),ids=[r['id'] for r in rows])
    report=dict(status='candidate_only_not_activated',target_raw_tokens=a.target_tokens,
        model=cfg,raw_train_tokens=tokens,documents=len(train),token_mean=statistics.mean(token_lengths),
        token_std_population=statistics.pstdev(token_lengths),min_tokens=min(token_lengths),max_tokens=max(token_lengths),
        original_train_rows_preserved_as_prefix=parent['splits']['wiki_train']['count'],
        source_files=sources,parent_manifest_sha256=sha((base/'cpt-data-manifest-v02.json').read_bytes()),
        splits=receipts,counters=dict(counts),
        policy='Same length/letter filters; original train retained; added documents in stable SHA rank; exact document, >=200-character paragraph and five-word containment>=.8 exclusions against all fixed evaluation and selected training text',
        limitations=parent['limitations'])
    (base/'cpt-10m-candidate-manifest-v01.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('splits','source_files')}),flush=True)


if __name__=='__main__':main()
