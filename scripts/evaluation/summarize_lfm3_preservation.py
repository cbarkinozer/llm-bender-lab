"""Local, auditable numeric screening and stopping diagnostics; no prose grading."""
import csv
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'preservation-session-v01-local'
MODELS=['base','turkish60','bilingual69','exp-012-base-bilingual','exp-013-base-preservation']
NUMERIC={'synchronization','border_area','without_replacement','median','inclusion_exclusion','ceiling_capacity','midnight_rollover'}

def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def final(r,thinking=False):
    text=r['raw_output']
    if thinking and '</think>' not in text:return '',False
    text=text.split('</think>')[-1]
    return re.sub(r'<\|[^>]+\|>','',text).strip(),True
def value(s):
    s=s.strip().replace(' ','').replace(',','.')
    if re.fullmatch(r'\d{1,2}:\d{2}',s):
        a,b=s.split(':');return ('time',int(a)*60+int(b))
    try:return ('number',Fraction(s))
    except (ValueError,ZeroDivisionError):return None
def terminal(text):
    numbers=re.findall(r'(?<!\w)(?:\d{1,2}:\d{2}|[-+]?\d+\s*/\s*\d+|[-+]?\d+(?:[.,]\d+)?)',text)
    return numbers[-1] if numbers else None
def stats(values):
    return dict(count=len(values),finish_reasons=dict(Counter(r['finish_reason'] for r in values)),
        tokens_median=statistics.median(r['generated_tokens'] for r in values),
        tokens_max=max(r['generated_tokens'] for r in values),
        length_limit_hits=sum(r['hit_max_new_tokens'] for r in values),
        generated_think_closures=sum('</think>' in r['raw_output'] for r in values))

def main():
    report=dict(status='numeric-screening-needs-semantic-review',caveats=[
        'Last numeric expression is a reproducible screening heuristic, not semantic accuracy.',
        'Every arithmetic output needs review for units, contradictory work and intended final answer.',
        'Thinking-on scores require a closing native think tag and a nonempty final answer.',
        'Fresh evaluation has32 prompts with paired task families, not32 independent families.',
        'Thinking comparison reuses consumed test items and is diagnostic only.'],fresh={},thinking={},new_symbolic={})
    review=[]
    refs={r['id']:r for r in rows(BASE/'capability-preservation-v01/eval-references.jsonl')}
    for model in MODELS:
        p=RUN/'inference/fresh'/model/'answers.jsonl'
        if not p.exists():continue
        values=rows(p);assert len(values)==32 and {r['id'] for r in values}==set(refs)
        details=[]
        for r in values:
            text,present=final(r);reference=refs[r['id']]
            item=dict(model=model,id=r['id'],category=r['category'],language=r['output_language'],
                expected=reference['final_answer'],final_answer=text,finish_reason=r['finish_reason'],
                terminal_numeric='',numeric_value_match='',semantic_correct='',reviewer_notes='')
            if r['category'] in NUMERIC:
                parsed=terminal(text);item.update(terminal_numeric=parsed,numeric_value_match=value(parsed)==value(reference['final_answer']) if parsed else False)
                details.append(item.copy())
            review.append(item)
        report['fresh'][model]=dict(source_sha256=sha(p),generation=stats(values),numeric_screen=[
            dict(language=lang,matches=sum(d['numeric_value_match'] for d in details if d['language']==lang),
                 count=sum(d['language']==lang for d in details)) for lang in ['tr','en']],details=details)
    packet=BASE/'bilingual-pilot-v01/eval-v01'
    oldrefs={r['id']:r for name in ['eval-references.jsonl','symbolic-controls-references.jsonl'] for r in rows(packet/name)}
    for model in MODELS[:3]:
        on=RUN/'inference/thinking-diagnostic'/model/'answers.jsonl'
        off=BASE/'final-eval-v01-local/inference'/model/'answers.jsonl'
        if not on.exists():continue
        onrows=rows(on);assert len(onrows)==16
        offrows={r['id']:r for r in rows(off)}
        pairs=[]
        for r in onrows:
            original=offrows[r['id']]
            assert original['messages']==r['messages']
            assert original['rendered_prompt']!=r['rendered_prompt']
            assert original['rendered_prompt'].endswith('<think></think>') and r['rendered_prompt'].endswith('<think>')
            item=dict(id=r['id'],expected=oldrefs[r['id']]['final_answer'],prompt_unchanged_except_mode=True)
            for mode,answer in [('off',original),('on',r)]:
                text,present=final(answer,mode=='on');parsed=terminal(text)
                # ar08 needs both final requested quantities, handled manually.
                expected=value(item['expected'])
                item[mode]=dict(final=text,final_present=present,terminal_numeric=parsed,
                    numeric_value_match=(value(parsed)==expected) if parsed and expected is not None and present else False,
                    semantic_review_required=True,finish_reason=answer['finish_reason'],tokens=answer['generated_tokens'])
            pairs.append(item)
        report['thinking'][model]=dict(on_sha256=sha(on),off_sha256=sha(off),generation=stats(onrows),pairs=pairs)
    for model in MODELS[3:]:
        report['new_symbolic'][model]={}
        for mode in ['off','on']:
            p=RUN/'inference'/('new-symbolic-'+mode)/model/'answers.jsonl'
            if not p.exists():continue
            values=rows(p);assert len(values)==8
            details=[]
            for r in values:
                text,present=final(r,mode=='on');parsed=terminal(text)
                details.append(dict(id=r['id'],expected=oldrefs[r['id']]['final_answer'],final=text,
                    numeric_value_match=bool(present and parsed and value(parsed)==value(oldrefs[r['id']]['final_answer'])),
                    tokens=r['generated_tokens']))
            report['new_symbolic'][model][mode]=dict(source_sha256=sha(p),generation=stats(values),
                matches=sum(d['numeric_value_match'] for d in details),count=8,details=details)
    out=RUN/'analysis';out.mkdir(parents=True,exist_ok=True)
    (out/'automatic-diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    dest=out/'fresh-review.csv'
    if review:
        previous={}
        if dest.exists():
            with dest.open(encoding='utf-8-sig',newline='') as f:
                previous={(r['model'],r['id']):r for r in csv.DictReader(f)}
        for r in review:
            old=previous.get((r['model'],r['id']),{})
            for key in ['semantic_correct','reviewer_notes']:
                if old.get(key):r[key]=old[key]
        with dest.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(review[0]));writer.writeheader();writer.writerows(review)
    print(json.dumps({m:dict(generation=r['generation'],numeric_screen=r['numeric_screen']) for m,r in report['fresh'].items()},indent=2))

if __name__=='__main__':main()
