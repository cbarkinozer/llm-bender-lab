"""Apply documented agent sample-review exclusions without silently replacing drafts."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
from prepare_lfm3_cpt import sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args();root=a.model_dir
    source=root/'exp-000-baseline/data-local/cpt-mixed-10m-v04'
    target=source.with_name('cpt-mixed-10m-v05')
    review=json.loads((root/'cpt-pair-sample-review-v01.json').read_text())
    assert review['sample_sha256']==sha((source/'review-sample.jsonl').read_bytes())
    manifest=json.loads((source/'manifest.json').read_text())
    excluded=set(review['excluded_ids'])
    rows=[json.loads(s) for s in (source/'wiki_train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert excluded <= {r['id'] for r in rows}
    rows=[r for r in rows if r['id'] not in excluded]
    target.mkdir(exist_ok=False)
    for name in manifest['splits']:
        blob=(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode()
              if name=='wiki_train' else (source/f'{name}.jsonl').read_bytes())
        (target/f'{name}.jsonl').write_bytes(blob)
        if name=='wiki_train':manifest['splits'][name]=dict(count=len(rows),sha256=sha(blob),ids=[r['id'] for r in rows])
    from transformers import AutoTokenizer
    model=manifest['model'];tok=AutoTokenizer.from_pretrained(model['repo'],revision=model['revision'])
    lengths=[len(s) for s in tok([r['text'] for r in rows if r['source']=='wikimedia/wikipedia'],add_special_tokens=False)['input_ids']]
    web=[r for r in rows if r['source']=='HuggingFaceFW/fineweb-2'];web_lengths=[r['lfm_raw_tokens'] for r in web]
    def stats(values):
        ordered=sorted(values)
        return dict(count=len(values),tokens=sum(values),mean=statistics.mean(values),std_population=statistics.pstdev(values),
            min=min(values),max=max(values),percentiles={str(q):ordered[round((len(ordered)-1)*q/100)] for q in (50,90,95,99)})
    manifest.update(status='frozen_after_agent_sample_review',
        parent_candidate_manifest_sha256=sha((source/'manifest.json').read_bytes()),
        sample_review_sha256=sha((root/'cpt-pair-sample-review-v01.json').read_bytes()),
        manual_excluded_ids=sorted(excluded),
        raw_tokens_no_eos=dict(wikipedia=stats(lengths),fineweb=stats(web_lengths),combined=stats(lengths+web_lengths)))
    for field,key in [('web_host_tokens','host'),('web_dump_tokens','dump')]:
        counts=Counter()
        for r in web:counts[str(r[key])]+=r['lfm_raw_tokens']
        manifest[field]=dict(counts.most_common())
    manifest['limitations'].append('Four sampled pages manually excluded; nominal 10M budget has a small recorded undershoot; unreviewed pages may retain similar defects')
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (target/'review-sample.jsonl').write_bytes((source/'review-sample.jsonl').read_bytes())
    print(json.dumps(manifest['raw_tokens_no_eos']))


if __name__=='__main__':main()
