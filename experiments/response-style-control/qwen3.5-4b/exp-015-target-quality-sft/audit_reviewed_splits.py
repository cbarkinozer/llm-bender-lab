"""Read-only final E/F train versus all32 eval prompts and reviewed references.

Write a new immutable audit artifact; never alter source data or annotations.
String metrics find inspection candidates, not semantic-independence proofs.
"""
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from prepare_pair import HERE,F,C,ROOT,HASHES,sha,load,save,encoded

def norm(text):
    return ' '.join(unicodedata.normalize('NFC',text).split())

def user_views(row):
    turns=[norm(m['content']) for m in row['messages'] if m['role']=='user']
    return list(dict.fromkeys(turns+[' '.join(turns)]))

def words(text):
    return re.findall(r'\w+',unicodedata.normalize('NFC',text),flags=re.UNICODE)

def shingles(text,n=5):
    tokens=words(text)
    return {tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)}

def pairs(train,eval_rows):
    exact=[]; near=[]; ngram=[]; common_answers=[]; long_answers=[]; embedded=[]; nearest=[]
    pair_count=0
    for ev in eval_rows:
        scores=[]
        for tr in train:
            pair_count+=1
            a=user_views(ev); b=user_views(tr)
            similarity=max(SequenceMatcher(None,x,y,autojunk=False).ratio() for x in a for y in b)
            match=dict(eval_id=ev['id'],train_id=tr['id'],similarity=round(similarity,4))
            scores.append(match)
            if set(a)&set(b): exact.append(match)
            elif similarity>=.60: near.append(match)
            e5=shingles(' '.join(a)); t5=shingles(' '.join(b))
            overlap=e5&t5
            containment=len(overlap)/min(len(e5),len(t5)) if e5 and t5 else 0.
            if containment>=.50:
                ngram.append(dict(match,shingle_containment=round(containment,4),shared_5grams=len(overlap)))
            target_e=norm(ev['desired_answer']); target_t=norm(tr['desired_answer'])
            if target_e==target_t:
                item=dict(eval_id=ev['id'],train_id=tr['id'],target=target_e,word_count=len(words(target_e)))
                (common_answers if len(words(target_e))<8 else long_answers).append(item)
            # Very short acknowledgments/names are not item-specific leakage.
            for kind,text in [('eval-question', ' '.join(a)),('eval-reference',target_e)]:
                if len(words(text))>=8 and (text in ' '.join(b) or text in target_t):
                    embedded.append(dict(eval_id=ev['id'],train_id=tr['id'],kind=kind))
        nearest.append(dict(eval_id=ev['id'],closest=sorted(scores,key=lambda x:x['similarity'],reverse=True)[:3]))
    return dict(pairs_checked=pair_count,exact_user_prompt_matches=exact,near_prompt_flags=near,
        high_ngram_containment_flags=ngram,long_exact_reference_matches=long_answers,
        evaluation_text_embedded_in_train=embedded,shared_short_generic_answers=common_answers,
        nearest_prompt_pairs=nearest)

def main():
    e=load(HERE/'data-reviewed-v1/train-reviewed.jsonl')
    f=load(F/'data-reviewed-v1/train-reviewed.jsonl')
    validation=load(HERE/'data-reviewed-v1/validation-reviewed.jsonl')
    controls=load(HERE/'controls-reviewed-v1/questions-12.jsonl')
    assert len(e)==80 and len(f)==104 and e==f[:80]
    assert len(validation)==20 and len(controls)==12
    assert len({r['id'] for r in validation+controls})==32
    assert all(r['split']=='train' and not r['evaluation_only'] for r in f)
    assert all(r['evaluation_only'] for r in validation+controls)
    assert len({r['id'] for r in f})==104
    old=load(C/'data-reviewed-v1/train-reviewed.jsonl')
    assert [(r['id'],r['messages']) for r in e]==[(r['id'],r['messages']) for r in old]
    assert sha((HERE/'data-reviewed-v1/validation-reviewed.jsonl').read_bytes())==HASHES['validation-reviewed.jsonl']
    assert sha((F/'data-reviewed-v1/validation-reviewed.jsonl').read_bytes())==HASHES['validation-reviewed.jsonl']
    groups={r['scenario_group_id'] for r in f}&{r['scenario_group_id'] for r in validation+controls}
    ids={r['id'] for r in f}&{r['id'] for r in validation+controls}
    assert not groups and not ids
    # Source path alone is not identity: historical records can come from one
    # CSV. Check composite path+source_id, ignoring missing source metadata.
    def source_id(row):
        return (row['source_path'],row['source_id']) if row.get('source_path') and row.get('source_id') else None
    sources={source_id(r) for r in f}-{None}
    overlaps=[r['id'] for r in validation+controls if source_id(r) in sources]
    assert not overlaps
    report=dict(status='requires-semantic-inspection',training_started=False,
        train_counts=dict(E=80,F=104),evaluation_counts=dict(development=20,new_controls=12,total=32),
        F_first80_identical_to_E=True,E_prompts_ids_order_unchanged=True,
        exact_cross_split_id_matches=sorted(ids),exact_cross_split_scenario_matches=sorted(groups),
        exact_cross_split_source_identity_matches=overlaps,
        results={arm:pairs(rows,validation+controls) for arm,rows in [('E',e),('F',f)]},
        hash_inventory={str(path.relative_to(ROOT)).replace('\\','/'):sha(path.read_bytes()) for path in
            [HERE/'data-reviewed-v1/train-reviewed.jsonl',F/'data-reviewed-v1/train-reviewed.jsonl',
             HERE/'data-reviewed-v1/validation-reviewed.jsonl',HERE/'controls-reviewed-v1/questions-12.jsonl',
             HERE/'data-reviewed-v1/argilla-train-snapshot.json',HERE/'data-reviewed-v1/argilla-controls-snapshot.json']},
        normalized_unicode='NFC + whitespace only; Turkish characters, case and quantities preserved',
        thresholds=dict(character_similarity=.60,five_word_shingle_containment=.50,long_reference_min_words=8),
        policy='Shared task families/short generic acknowledgments are intentional. Inspect nearest pairs for specific scenarios, substituted entities or benchmark-derived solutions. Character/ngram/source checks are not a semantic proof.',
        limitations=['20 old questions repeatedly inform experimental decisions: development, not fresh final test.',
                    '12 controls are small, agent-authored by same author as train: not evaluator/generator-independent.',
                    'No embedding model or base/adapter model inference used; human semantic inspection is separate.',
                    'No all-purpose guarantee about pretraining contamination or universal zero semantic leakage.'])
    flags=[v for r in report['results'].values() for k,v in r.items() if k in
        ('exact_user_prompt_matches','near_prompt_flags','high_ngram_containment_flags','long_exact_reference_matches','evaluation_text_embedded_in_train') and v]
    report['status']='automated-checks-passed-needs-semantic-signoff' if not flags else 'requires-overlap-review'
    save(HERE/'data-reviewed-v1/final-split-audit-v1.json',encoded(report))
    print(json.dumps(dict(status=report['status'],groups=sorted(groups),source_overlaps=overlaps,
        results={arm:{k:v for k,v in result.items() if k!='nearest_prompt_pairs'} for arm,result in report['results'].items()}),ensure_ascii=True,indent=2))

if __name__=='__main__': main()
