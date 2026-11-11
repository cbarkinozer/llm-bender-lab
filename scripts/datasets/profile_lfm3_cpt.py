"""Verify active CPT file hashes/disjoint IDs and measure pinned raw token counts."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment-dir',type=Path,required=True)
    args=parser.parse_args()
    from transformers import AutoTokenizer
    base=args.experiment_dir
    model=json.loads((base/'config-planned.json').read_text())['model']
    manifest=json.loads((base/'cpt-data-manifest-v02.json').read_text())
    tokenizer=AutoTokenizer.from_pretrained(model['repo'],revision=model['revision'])
    output={}
    ids,texts,paragraphs=set(),set(),set()
    for name,split in manifest['splits'].items():
        file=base/'data-local/cpt-v02'/(name+'.jsonl')
        if hashlib.sha256(file.read_bytes()).hexdigest()!=split['sha256']:
            raise ValueError('Active split checksum mismatch')
        rows=[json.loads(line) for line in file.read_text(encoding='utf-8').splitlines()]
        if len(rows)!=split['count'] or [r['id'] for r in rows]!=split['ids']:
            raise ValueError('Split count or ID mismatch')
        lengths=[]
        from prepare_lfm3_cpt import norm
        for row in rows:
            paragraph_hashes={hashlib.sha256(norm(p).encode()).hexdigest() for p in row['text'].split('\n') if len(norm(p))>=200}
            if row['id'] in ids or row['normalized_text_sha256'] in texts or paragraph_hashes & paragraphs:
                raise ValueError('Duplicate ID, document or long paragraph across selected documents')
            ids.add(row['id']); texts.add(row['normalized_text_sha256']); paragraphs.update(paragraph_hashes)
            lengths.append(len(tokenizer(row['text'],add_special_tokens=False)['input_ids']))
        output[name]=dict(count=len(rows),tokens=sum(lengths),mean=statistics.mean(lengths),
            population_std=statistics.pstdev(lengths),min=min(lengths),max=max(lengths))
    report=dict(status='active_hashes_ids_exact_document_and_long_paragraph_checks_passed',
        model_revision=model['revision'],raw_tokens_no_eos=output,
        note='Packed training adds document EOS; actual supervised tokens are measured by trainer, not inferred from row count')
    (base/'cpt-token-profile-v02.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
