"""Independent frozen-pair hash, nesting, provenance and tokenizer verification."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from prepare_lfm3_cpt import norm


def digest(blob): return hashlib.sha256(blob).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--model-dir',type=Path,required=True)
    a=p.parse_args();root=a.model_dir
    from transformers import AutoTokenizer
    baseline=root/'exp-000-baseline'
    cfg=json.loads((baseline/'config-planned.json').read_text())
    tokenizer=AutoTokenizer.from_pretrained(cfg['model']['repo'],revision=cfg['model']['revision'])
    trains={};reports={}
    for name in ('exp-001-wiki-cpt','exp-002-mixed-cpt'):
        exp=root/name;c=json.loads((exp/'config-planned.json').read_text())
        assert (exp/'config-planned.json').read_bytes()==(exp/'config.yaml').read_bytes()
        manifest=json.loads((exp/c['active_cpt_manifest']).read_text())
        groups={};ids=set();texts=set();paragraphs=set()
        for split,receipt in manifest['splits'].items():
            blob=(exp/c['active_cpt_data']/f'{split}.jsonl').read_bytes()
            assert digest(blob)==receipt['sha256']
            rows=[json.loads(s) for s in blob.decode().splitlines()]
            assert len(rows)==receipt['count'] and [r['id'] for r in rows]==receipt['ids']
            for r in rows:
                assert digest(norm(r['text']).encode())==r['normalized_text_sha256']
                assert r['id'] not in ids and r['normalized_text_sha256'] not in texts
                paras={digest(norm(s).encode()) for s in r['text'].split('\n') if len(norm(s))>=200}
                assert not paras & paragraphs
                paragraphs.update(paras)
                ids.add(r['id']);texts.add(r['normalized_text_sha256'])
            groups[split]=rows
            if split!='wiki_train':
                assert blob==(baseline/'data-local/cpt-v02'/f'{split}.jsonl').read_bytes()
        for filename in ('questions-500.jsonl','turblimp-1600.jsonl'):
            assert (exp/'data-local'/filename).read_bytes()==(baseline/'data-local'/filename).read_bytes()
        train=groups['wiki_train'];trains[name]=train
        lengths=[]
        for start in range(0,len(train),128):
            lengths.extend(len(s) for s in tokenizer([r['text'] for r in train[start:start+128]],add_special_tokens=False)['input_ids'])
        reports[name]=dict(documents=len(train),recomputed_raw_tokens=sum(lengths),
            manifest_sha256=digest((exp/c['active_cpt_manifest']).read_bytes()),
            source_documents=dict(Counter(r['source'] for r in train)),
            no_gpu_gate_exists=not (exp/'data-local/gpu-gate.json').exists())
        print(name+': '+str(sum(lengths))+' tokens',flush=True)
    wiki={r['id']:r for r in trains['exp-001-wiki-cpt']}
    mixed=trains['exp-002-mixed-cpt']
    assert {r['id']:r for r in mixed if r['source']=='wikimedia/wikipedia'}==wiki
    web=[r for r in mixed if r['source']=='HuggingFaceFW/fineweb-2']
    assert all(r['source_split']=='train' and r['source_revision']=='af9c13333eb981300149d5ca60a8e9d659b276b9' for r in web)
    assert reports['exp-002-mixed-cpt']['recomputed_raw_tokens']==sum(r['lfm_raw_tokens'] for r in web)+reports['exp-001-wiki-cpt']['recomputed_raw_tokens']
    report=dict(status='passed',checks=['all split hashes/counts/IDs','unique IDs/text hashes across active splits',
        'recomputed normalized hashes and no shared long paragraphs','byte-identical evaluation copies','identical nested Wiki rows','web train-only pinned provenance',
        'independent pinned-tokenizer recount','config YAML/JSON byte equality'],
        experiments=reports,limitations=['Near-duplicate exclusion is performed by builder; this audit does not independently rerun semantic matching',
            'No claim that historical base pretraining excludes these evaluation texts'])
    (root/'cpt-pair-integrity-v01.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
