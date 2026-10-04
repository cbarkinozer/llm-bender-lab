"""Descriptive termination/style/length checks; no automatic semantic scoring."""
import argparse
import json
from pathlib import Path
import re
from import_comparison import load,MODELS

def percentile(values,q):
    values=sorted(values); index=(len(values)-1)*q
    left=int(index); right=min(left+1,len(values)-1)
    return values[left]+(values[right]-values[left])*(index-left)

def describe(data):
    lengths=[r['output_tokens'] for r in data]
    return dict(count=len(data),native_eos=sum(r['native_eos'] for r in data),
        incomplete_ids=[r['id'] for r in data if not r['native_eos']],
        token_lengths=dict(p10=percentile(lengths,.1),median=percentile(lengths,.5),p90=percentile(lengths,.9),
            maximum=max(lengths),total=sum(lengths)),
        markdown_flag_ids=[r['id'] for r in data if re.search(r'\*\*|(?m:^\s*#{1,6}\s)|```',r['answer'])],
        emoji_flag_ids=[r['id'] for r in data if re.search('[\U0001F300-\U0001FAFF\u2600-\u27BF]',r['answer'])])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--results-root',type=Path,required=True)
    p.add_argument('--historical-c',type=Path); a=p.parse_args()
    arms=load(a.results_root)
    report=dict(status='outputs-verified-human-semantic-review-pending',prompt_parity=True,
        caveat='Regex flags are not semantic/style grades. Length changes are not accuracy gains. Warmup/compilation affects timing.',models={})
    for model in MODELS:
        data=arms[model][1]
        report['models'][model]=dict(all32=describe(data),development20=describe([r for r in data if r['split']=='validation']),
            controls12=describe([r for r in data if r['split']=='control']))
    if a.historical_c:
        old={r['id']:r for r in [json.loads(s) for s in a.historical_c.read_text(encoding='utf-8').splitlines()]}
        new=[r for r in arms['C'][1] if r['split']=='validation']
        assert len(old)==len(new)==20 and set(old)=={r['id'] for r in new}
        assert all(r['messages']==old[r['id']]['messages'] and r['prompt_token_ids']==old[r['id']]['prompt_token_ids'] for r in new)
        report['historical_C_reproducibility']=dict(prompt_token_parity=True,
            exact_answer_matches=sum(r['answer']==old[r['id']]['adapter_answer'] for r in new),
            exact_output_token_matches=sum(r['output_token_ids']==old[r['id']]['output_token_ids'] for r in new),
            changed_ids=[r['id'] for r in new if r['answer']!=old[r['id']]['adapter_answer']],
            historical_source=str(a.historical_c))
    path=a.results_root/'output-diagnostics.json'
    assert not path.exists(),'Refusing overwrite'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],models={m:report['models'][m]['all32']['native_eos'] for m in MODELS})))

if __name__=='__main__':
    main()
