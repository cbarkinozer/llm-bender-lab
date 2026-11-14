"""Static pilot checks and lexical leakage triage, not semantic certification."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
TRACK = ROOT/'experiments/turkish-capability/lfm3-1.7b'
OUT = TRACK/'sft-expansion-v01'


def norm(text):
    return ' '.join(unicodedata.normalize('NFC',text).casefold().split())


def main():
    from tokenizers import Tokenizer
    path = OUT/'pilot-train-draft.jsonl'
    rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 40 and len({r['id'] for r in rows}) == 40
    assert Counter(r['capability'] for r in rows) == dict(faithful_summary=20,
        grounded_qa=8,translation=6,instruction_control=4,minimal_correction=2)
    assert len({r['scenario_group'] for r in rows}) == 40
    assert all(r['split']=='train' and r['target'] for r in rows)
    assert '\ufffd' not in path.read_text(encoding='utf-8')
    for r in rows:
        assert r['messages'][-1]['role']=='user'
        assert r['rubric']['required_facts']
        assert all(t not in r['target'] for t in ['<think>','<|im_start|>','<|im_end|>'])
        payload=json.dumps(dict(messages=r['messages'],target=r['target']),ensure_ascii=False,sort_keys=True)
        assert hashlib.sha256(payload.encode('utf-8')).hexdigest()==r['content_sha256']
    structured=json.loads(rows[34]['target'])
    assert set(structured)=={'ad','gun','ucret_tl'} and structured['ucret_tl']==75
    assert len(rows[35]['target'].splitlines())==3
    assert len(rows[37]['messages'])==3
    assert rows[39]['target']==rows[39]['source_context']
    tokenizer_path=TRACK/'exp-004-cpt-cont-100m/results-local/cpt-v01/adapter/tokenizer.json'
    tokenizer=Tokenizer.from_file(str(tokenizer_path))
    def stats(values):
        return dict(count=len(values),mean=statistics.mean(values),std_population=statistics.pstdev(values),
            min=min(values),max=max(values),total=sum(values))
    def prompt(r):
        return '\n'.join(m['content'] for m in r['messages'])
    prompts=[norm(prompt(r)) for r in rows]
    assert len(set(prompts))==40
    occam=ROOT/'experiments/response-style-control/qwen3.5-4b/exp-016-diverse-coverage-sft/data-reviewed-v1'
    pools={name:occam/file for name,file in [('occam_train','train-reviewed.jsonl'),('occam_validation','validation-reviewed.jsonl')]}
    pools['cetvel500']=TRACK/'exp-000-baseline/data-local/questions-500.jsonl'
    comparisons={}
    for name,p in pools.items():
        references=[json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
        protected=[norm(prompt(r)) for r in references]
        exact=[rows[i]['id'] for i,s in enumerate(prompts) if s in set(protected)]
        assert not exact,(name,exact)
        # Lexical nearest neighbours are review leads only; low overlap is not semantic clearance.
        nearest=[]
        protected_words=[set(t.split()) for t in protected]
        for r,s in zip(rows,prompts):
            words=set(s.split())
            scores=[len(words & t)/len(words | t) for t in protected_words]
            j=max(range(len(scores)),key=scores.__getitem__)
            nearest.append(dict(pilot_id=r['id'],reference_id=references[j].get('id',j),ratio=scores[j]))
        comparisons[name]=dict(reference_rows=len(references),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            exact_prompt_matches=exact,lexical_metric='normalized whitespace-word set Jaccard',
            lexical_nearest=sorted(nearest,key=lambda x:x['ratio'],reverse=True))
    report=dict(status='STATIC_CHECKS_PASS; independent semantic/human review pending; not training-ready',
        dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rows=len(rows),
        capabilities=dict(Counter(r['capability'] for r in rows)),domains=dict(Counter(r['domain'] for r in rows)),
        tokenizer_sha256=hashlib.sha256(tokenizer_path.read_bytes()).hexdigest(),
        token_scope='Raw content only, add_special_tokens=False; not native chat serialization or actual loss labels.',
        raw_input_tokens=stats([len(tokenizer.encode(prompt(r),add_special_tokens=False).ids) for r in rows]),
        raw_target_tokens=stats([len(tokenizer.encode(r['target'],add_special_tokens=False).ids) for r in rows]),
        by_capability={cap:dict(raw_input_tokens=stats([len(tokenizer.encode(prompt(r),add_special_tokens=False).ids) for r in rows if r['capability']==cap]),
            raw_target_tokens=stats([len(tokenizer.encode(r['target'],add_special_tokens=False).ids) for r in rows if r['capability']==cap])) for cap in sorted({r['capability'] for r in rows})},
        protected_comparisons=comparisons,limitations=[
            'Lexical screening does not rule out semantic near-duplicates or pretraining contamination.',
            'Same author drafted contexts, targets and rubrics; this is not independent adjudication.',
            'No dev/final holdout examples generated; training-only pilot families must never cross splits.',
            'No native label masking, EOS or truncation audit yet.'])
    (OUT/'pilot-static-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','rows','capabilities','raw_input_tokens','raw_target_tokens']},indent=2))


if __name__=='__main__':
    main()
