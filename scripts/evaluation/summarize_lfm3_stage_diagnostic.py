"""Local scoring after verified artifact download; correctness and fluency stay separate."""
import csv
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
DATA=BASE/'stage-diagnostic-v01'
RUN=BASE/'stage-diagnostic-v01-local'
MODELS=['base','cpt','cpt-bilingual69']
def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cookbook',action='store_true',help='Score downloaded exp014/015 and matched base outputs separately from historical runs')
    args=parser.parse_args()
    models=['base','exp-014-completion-mask','exp-015-cookbook-recipe'] if args.cookbook else MODELS
    freeze=json.loads((DATA/'freeze.json').read_text());refs_path=DATA/'references-local-only.jsonl'
    assert sha(refs_path)==freeze['references_local_only_sha256']
    refs={r['id']:r for r in rows(refs_path)};report=dict(status='diagnostic-not-general-accuracy',models={},
        caveats=['Seen training probes MUST NOT be pooled with unseen diagnostic tasks.',
                 'Existing eval is consumed; no fresh final-test claim.',
                 'Numeric screen is only for eight integer symbolic controls; all prose correctness needs adjudication.',
                 'A stage difference locates observed regression, not its optimizer/data mechanism.'])
    review=[]
    for model in models:
        report['models'][model]={}
        for cohort,packet in [('main-off','prompts.jsonl'),('thinking-on','thinking-prompts.jsonl')]:
            if args.cookbook:
                root=BASE/'cookbook-runtime-local/base' if model=='base' else BASE/model/'results-local'
                folder=root/('inference-on' if cohort=='thinking-on' else 'inference-off')
            else:
                folder=RUN/'inference'/cohort/model
            manifest=json.loads((folder/'manifest.json').read_text())
            actual=rows(folder/'answers.jsonl');prompts=rows(DATA/packet)
            assert manifest['status']=='completed' and manifest['count']==len(actual)==len(prompts)
            assert manifest['questions_sha256']==sha(DATA/packet)
            assert {r['id'] for r in actual}=={r['id'] for r in prompts}
            assert manifest['decoding']['enable_thinking']==(cohort=='thinking-on')
            symbolic=[]
            for r in actual:
                text=r['raw_output'];closed='</think>' in text
                final=re.sub(r'<\|[^>]+\|>','',text.split('</think>')[-1]).strip()
                if cohort=='thinking-on' and not closed:final=''
                if 'symbolic' in r['id']:
                    match=re.search(r'(?<![\d.])(-?\d+)\s*[.!]?\s*$',final)
                    parsed=match.group(1) if match else None
                    symbolic.append(dict(id=r['id'],expected=refs[r['id']]['final_answer'],parsed=parsed,
                        numeric_match=parsed==refs[r['id']]['final_answer'],final_answer_present=bool(final)))
                reference=refs[r['id']]
                review.append(dict(model=model,mode=cohort,id=r['id'],cohort=r['cohort'],direction=r.get('direction','symbolic'),
                    prompt='\n\n'.join(m['content'] for m in r['messages']),
                    reference=reference.get('reference_answer',reference.get('final_answer','')),
                    raw_output=text,finish_reason=r['finish_reason'],correctness='',language='',constraints='',notes=''))
            strata={}
            for key in sorted({(r['cohort'],r.get('direction','symbolic')) for r in actual}):
                selected=[r for r in actual if (r['cohort'],r.get('direction','symbolic'))==key]
                strata['/'.join(key)]=dict(count=len(selected),finish_reasons=dict(Counter(r['finish_reason'] for r in selected)),
                    median_tokens=statistics.median(r['generated_tokens'] for r in selected),
                    length_hits=sum(r['hit_max_new_tokens'] for r in selected))
            report['models'][model][cohort]=dict(source_sha256=sha(folder/'answers.jsonl'),strata=strata,
                symbolic_matches=sum(r['numeric_match'] for r in symbolic),symbolic_count=len(symbolic),symbolic_details=symbolic)
    out=(BASE/'cookbook-runtime-local' if args.cookbook else RUN)/'analysis';out.mkdir(parents=True,exist_ok=True)
    (out/'diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target=out/'correctness-review.csv'
    if not target.exists():
        with target.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(review[0]));writer.writeheader();writer.writerows(review)
    print(json.dumps({m:{mode:dict(symbolic_matches=r['symbolic_matches'],symbolic_count=r['symbolic_count']) for mode,r in v.items()} for m,v in report['models'].items()},indent=2))

if __name__=='__main__':main()
