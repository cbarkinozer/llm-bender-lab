"""Snapshot completed cookbook reviews and decode independently shuffled identities."""
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
RUN = BASE / 'cookbook-runtime-local'
OUT = RUN / 'argilla'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    key = read(OUT/'PRIVATE-model-key.json')
    mapping = {r['record_id']: r for r in key['records']}
    for source, digest in key['sources'].items():
        model, mode = source.split('/')
        root = RUN/'base' if model == 'base' else BASE/model/'results-local'
        assert hashlib.sha256((root/('inference-'+mode)/'answers.jsonl').read_bytes()).hexdigest() == digest
    load_dotenv(ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env')
    receipt = read(OUT/'receipt.json')
    response = requests.get(os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900').rstrip('/')+
        f"/api/v1/datasets/{receipt['id']}/records", params={'limit':100,'include':'responses'},
        headers={'X-Argilla-Api-Key':os.getenv('ARGILLA_API_KEY','argilla.apikey')}, timeout=30)
    response.raise_for_status()
    raw = response.json()
    snapshot = OUT/('responses-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    save(snapshot, raw)
    assert len(raw['items']) == 34
    decoded = []
    for row in raw['items']:
        identity = mapping[row['external_id']]
        submitted = [r for r in row['responses'] if r['status']=='submitted']
        assert len(submitted)==1, (row['external_id'], 'Need one submitted review')
        values = submitted[0]['values']
        ranking = values['ranking']['value']
        normalized = ranking.upper().strip().replace('→','>')
        assert re.fullmatch(r'[ABC\s>=,;]+',normalized), ranking
        groups = re.split(r'[>;,\s]+',re.sub(r'\s*=\s*','=',normalized))
        ranks = {}
        for rank, group in enumerate(groups):
            for letter in group.split('='):
                assert letter in 'ABC' and len(letter)==1 and letter not in ranks, ranking
                ranks[letter] = rank
        assert set(ranks)==set('ABC'), ranking
        notes = values['notes']['value']
        assert notes.strip()
        decoded.append(dict(**identity, ranking=ranking, notes=notes,
            model_ranks={model:ranks[letter] for letter,model in identity['models'].items()}))
    models = list(decoded[0]['model_ranks'])
    def summarize(rows):
        pairs = {}
        for a,b in itertools.combinations(sorted(models),2):
            signs = [1 if r['model_ranks'][a]<r['model_ranks'][b] else -1 if r['model_ranks'][a]>r['model_ranks'][b] else 0 for r in rows]
            pairs[a+' vs '+b] = dict(wins=signs.count(1),ties=signs.count(0),losses=signs.count(-1))
        return dict(n=len(rows),pairs=pairs,top_including_ties={m:sum(r['model_ranks'][m]==min(r['model_ranks'].values()) for r in rows) for m in sorted(models)})
    result = dict(dataset=receipt['name'],snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        review_provenance='User-reported AI-assisted blind judgments; not independent human correctness adjudication.',
        metric='Relative preference, NOT accuracy. Repeated task directions and thinking modes are correlated; consumed development data.',
        overall=summarize(decoded), subsets={label:summarize([r for r in decoded if predicate(r)]) for label,predicate in [
            ('thinking_off',lambda r:r['mode']=='off'),('thinking_on',lambda r:r['mode']=='on'),
            ('off_tr_tr',lambda r:r['mode']=='off' and r['direction']=='tr-tr'),
            ('off_en_tr',lambda r:r['mode']=='off' and r['direction']=='en-tr')]},reviews=decoded)
    save(OUT/'decoded-review.json',result)
    save(BASE/'COOKBOOK-BLIND-REVIEW.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='reviews'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
