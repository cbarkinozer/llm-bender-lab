"""Select a score-independent cleaned TurBLiMP subset, with exclusion receipts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from prepare_lfm3_cpt import download, records, norm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', type=Path, required=True)
    parser.add_argument('--cache-root', type=Path, required=True)
    args = parser.parse_args()
    source = json.loads((args.experiment_dir / 'source-inspection-v01.json').read_text(encoding='utf-8'))
    source = next(d for d in source['datasets'] if d['repo'] == 'juletxara/turblimp')
    chosen, files, exclusions = [], [], []
    seen = set()
    for item in source['files']:
        path, evidence = download(source['repo'], source['revision'], item['path'], args.cache_root)
        if evidence['sha256'] != item['sha256']:
            raise ValueError('Pinned source checksum mismatch')
        files.append(evidence)
        eligible = []
        for row in records(path):
            key = (norm(row['sentence_good']), norm(row['sentence_bad']))
            identifier = Path(item['path']).name.split('-00000')[0] + ':' + str(row['item_id'])
            reason = 'empty' if not all(key) else 'identical' if key[0] == key[1] else 'duplicate_pair' if key in seen else None
            if reason:
                exclusions.append(dict(id=identifier, reason=reason))
                continue
            seen.add(key)
            eligible.append(dict(row, id=identifier, evaluation_only=True))
        eligible.sort(key=lambda r: hashlib.sha256(('turblimp-v1-3407:' + r['id']).encode()).hexdigest())
        if len(eligible) < 100:
            raise ValueError('Insufficient unique pairs')
        chosen.extend(eligible[:100])
    output = args.experiment_dir / 'data-local/turblimp-1600.jsonl'
    blob = ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in chosen).encode()
    if output.exists() and output.read_bytes() != blob:
        raise ValueError('Refusing changed frozen packet')
    output.write_bytes(blob)
    report = dict(count=len(chosen), sha256=hashlib.sha256(blob).hexdigest(),
        per_phenomenon=dict(Counter(r['linguistic_phenomenon'] for r in chosen)), source_files=files,
        exclusion_counts=dict(Counter(r['reason'] for r in exclusions)), exclusions=exclusions,
        policy='NFC whitespace normalized, case preserved; drop empty/identical/global duplicate ordered pairs; SHA256 ID rank selects 100 per file; not linguistic validation',
        metric='strict total sentence log-probability preference; ties counted separately and not as wins',
        limitations='Cleaned subset, not the official full benchmark; report this distinction')
    (args.experiment_dir / 'turblimp-manifest-v01.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(count=len(chosen),exclusions=report['exclusion_counts'])))


if __name__ == '__main__':
    main()
