"""Compare the frozen before/after cohorts without pooling unrelated metrics."""
import argparse
from collections import Counter
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--experiment-dir',type=Path,required=True)
    a=p.parse_args()
    root=a.experiment_dir/'results-local'
    def read(path):
        return json.loads(path.read_text())
    b=root/'base-v01';c=root/'cpt-eval-v01'
    bm=read(b/'cetvel/manifest.json');cm=read(c/'cetvel/manifest.json')
    for key in ('model','questions_sha256','decoding','packages','chat_template_sha256','eos_token_ids','seed'):
        assert bm[key]==cm[key], 'Protocol mismatch: '+key
    for key in ('dtype','max_model_len','gpu_memory_utilization','enforce_eager','max_num_seqs',
                'seed','trust_remote_code','generation_config','enable_prefix_caching'):
        assert bm['engine_args'][key]==cm['engine_args'][key], 'Engine mismatch: '+key
    for m in (bm,cm):
        assert m['status']=='completed' and m['count']==500
    base=[json.loads(line) for line in (b/'cetvel/answers.jsonl').read_text(encoding='utf-8').splitlines()]
    trained=[json.loads(line) for line in (c/'cetvel/answers.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [r['id'] for r in base]==[r['id'] for r in trained]
    def delta(x,y):
        if isinstance(x,dict) and isinstance(y,dict):
            return {k:delta(x[k],y[k]) for k in x.keys()&y.keys()}
        if isinstance(x,(int,float)) and isinstance(y,(int,float)):
            return dict(base=x,cpt=y,delta=y-x)
        return dict(base=x,cpt=y)
    text={}
    bt=read(b/'text/text-scores.json')['results'];ct=read(c/'text/text-scores.json')['results']
    for split in bt:
        assert bt[split]['source_sha256']==ct[split]['source_sha256']
        assert bt[split]['scored_tokens']==ct[split]['scored_tokens']
        text[split]={key:delta(bt[split][key],ct[split][key]) for key in ('nll','perplexity','scored_tokens')}
    bg=read(b/'turblimp/scores.json');cg=read(c/'turblimp/scores.json')
    assert bg['packet_sha256']==cg['packet_sha256']
    grammar=dict(macro_accuracy=delta(bg['macro_accuracy'],cg['macro_accuracy']),
        per_phenomenon=delta(bg['per_phenomenon'],cg['per_phenomenon']))
    def health(rows):
        return dict(termination=dict(Counter(r['finish_reason'] for r in rows)),
            total_generated_tokens=sum(r['generated_tokens'] for r in rows),
            total_generation_seconds=sum(r['generation_seconds'] for r in rows))
    report=dict(status='matched_comparison_completed',model=bm['model'],
        text=text,turblimp=grammar,
        cetvel=delta(read(b/'cetvel/scores.json')['results'],read(c/'cetvel/scores.json')['results']),
        generation_health=dict(base=health(base),cpt=health(trained)),
        identical_predictions=sum(x['prediction']==y['prediction'] for x,y in zip(base,trained)),
        caveats=['One seed, exploratory recipe comparison; no algorithm-superiority claim',
            'Public comparison cohorts can have pretraining contamination',
            'CETVEL cohort was inspected historically; not pristine final test',
            'Native vLLM BF16 generation; CPT adapter merged with BF16 rounding',
            'NLL and grammar scored with unmerged adapter in the same Transformers environment',
            'No pooled cross-task score; cross-model perplexity is not compared'])
    (root/'comparison-v01.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
