"""Supplement source inventory with exact conflicts and protected phrase triage.

No automatic semantic contamination clearance. Raw text remains ignored locally.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from audit_turkish_sources import ROOT, OUT, SOURCES, messages, norm, digest, filehash


def words(text):
    return re.findall(r'\w+',norm(text))


def grams(text,n=12):
    tokens=words(text)
    return {tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)}


def main():
    protected=defaultdict(set)
    cohort=ROOT/'experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl'
    for line in cohort.read_text(encoding='utf-8').splitlines():
        r=json.loads(line);d=r['document'];texts=[r['semantic_prompt']]
        texts.extend(d[k] for k in ['question','context','text','source'] if isinstance(d.get(k),str))
        texts.extend(d.get('translation',{}).values())
        for text in texts:
            for g in grams(text):protected[g].add(r['id'])
    validation=OUT/'raw-local/occam/data/validation.jsonl'
    for line in validation.read_text(encoding='utf-8').splitlines():
        r=json.loads(line)
        for m in r['messages']:
            if m['role']=='user':
                for g in grams(m['content']):protected[g].add('occam-validation:'+r['id'])
    result={};review_rows=[]
    for key,(_,_,files) in SOURCES.items():
        grouped=defaultdict(list);flags=Counter();cue_counts=Counter();suspects=[];think_languages=Counter()
        for filename in files:
            with (OUT/'raw-local'/key/filename).open(encoding='utf-8-sig') as f:
                for number,line in enumerate(f,1):
                    r=json.loads(line);ms=messages(r)
                    p='\n'.join(m['content'] for m in ms if m['role']=='user')
                    a='\n'.join(m['content'] for m in ms if m['role']=='assistant')
                    row_id=key+':'+filename+':'+str(number)
                    grouped[digest(norm(p))].append((row_id,digest(norm(a))))
                    hits=Counter()
                    for g in grams(p):
                        for protected_id in protected.get(g,[]):hits[protected_id]+=1
                    # Known Occam dev rows are expected matches, never candidate contamination findings.
                    if hits and not (key=='occam' and 'validation' in filename):
                        suspects.append(dict(id=row_id,matches=dict(hits)))
                    pn=norm(p)
                    cues={'summary':r'özet', 'translation':r'çevir|tercüme',
                          'editing':r'düzelt|yazım|imla', 'grounded_context':r'kaynak metin|metne göre|metin:|aşağıdaki met',
                          'json':r'\bjson\b', 'code':r'\bpython\b|\bsql\b|javascript|kod yaz',
                          'requested_detail':r'detaylı|ayrıntılı|adım adım|gerekçe',
                          'clarification':r'netleştir|açıklayıcı soru|belirsiz'}
                    cue_counts.update(k for k,pattern in cues.items() if re.search(pattern,pn))
                    if '<think>' in a:
                        before,sep,after=a.partition('</think>')
                        if sep and not after.strip():flags['empty_final_after_think']+=1
                        if sep and before.count('<think>')==1:
                            reason=before.split('<think>',1)[1]
                            if len(reason)>200 and re.search(r'\b(the user|let me|we need|the question|first,|i need)\b',reason.lower()):
                                flags['english_reasoning_phrase_signal']+=1
                        if a.count('<think>')!=1 or a.count('</think>')!=1:
                            review_rows.append(dict(id=row_id,issue='non-single-balanced-think-pair'))
                    if '\ufffd' in p+a:review_rows.append(dict(id=row_id,issue='replacement-character'))
        duplicates=[dict(prompt_sha256=h,rows=rows,distinct_answers=len({a for _,a in rows})) for h,rows in grouped.items() if len(rows)>1]
        (OUT/'review-local'/(key+'-duplicate-prompts.json')).write_text(json.dumps(duplicates,indent=2)+'\n',encoding='utf-8')
        result[key]=dict(duplicate_prompt_groups=len(duplicates),
            groups_with_distinct_answers=sum(r['distinct_answers']>1 for r in duplicates),
            max_group_rows=max([len(r['rows']) for r in duplicates],default=1),
            task_wording_signals=dict(cue_counts),reasoning_format_flags=dict(flags),protected_phrase_candidates=suspects)
        print(key+': '+str(len(suspects))+' protected phrase candidates',flush=True)
    (OUT/'review-local/structural-quarantine-index.json').write_text(json.dumps(review_rows,indent=2)+'\n',encoding='utf-8')
    report=dict(sources=result,analyzer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protected_cohort_sha256=filehash(cohort),occam_validation_sha256=filehash(validation),
        phrase_method='Any normalized contiguous 12-word prompt overlap with known CETVEL500 prompts/documents or Occam validation user turns; triage, not proof.',
        limitations=['No semantic/cross-lingual benchmark clearance; no full public benchmark corpus scan.',
        'Task wording signals overlap and omit implicit tasks; not capability labels or quality estimates.',
        'Same prompt with different answers is not necessarily contradiction; compare the answers before disposition.',
        'English phrase signal is not a reliable language detector or a rejection verdict.'])
    (OUT/'overlap-and-format-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
