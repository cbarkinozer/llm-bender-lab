"""Verify recovered files and materialize the original deterministic weighted mix."""
from pathlib import Path
import json,hashlib,collections
from train_combined_routing import weighted_mix,load_jsonl
root=Path('/workspace/reflex-wsp');data=root/'data/reflex-1'
manifest=json.loads((data/'recovery-manifest.json').read_text())
for row in manifest['files']:
    p=data/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],str(p)
phone=data/'phone-routing-human-reviewed-v2-1080-fixedval-20261013';general=data/'general-routing-v1-balanced'
mix,stats=weighted_mix(load_jsonl(phone/'train.jsonl'),load_jsonl(general/'train.jsonl'),1.,1.,3407)
assert len(mix)==1562
out=root/'data/materialized';out.mkdir(exist_ok=True)
p=out/'train-s3407.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in mix))
report={'all_recovered_hashes_verified':True,'rows':len(mix),'mix':stats,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sources':dict(collections.Counter(r.get('source','phone') for r in mix))}
(out/'manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)