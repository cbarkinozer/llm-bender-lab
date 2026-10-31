"""Build a local portable audit release; never publish or enable training."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile

from active_tdd_data import EXP, ROOT, active_paths, read_json, rows
from export_intent_only_preview import project_record


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def build(destination):
    destination = Path(destination).resolve()
    if destination.exists() or destination.with_suffix('.zip').exists():
        raise ValueError('Use a new release path; existing releases are preserved')
    paths = active_paths()
    parent = EXP.parent/'exp-001-local-thinking-10/app-core-v07'
    original = read_json(parent/'source-snapshots.json')
    external = {s['repository']: s for s in read_json(EXP/'external-app-audit.json')['sources']}
    source_root = Path(r'C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\sources')
    mapping = read_json(EXP/'dataset-profile-v02/audit-only-reference-complexity.json')
    if mapping['missing_mappings']:
        raise ValueError('Resolve missing reference mappings first')
    tracks = {name: rows(paths[name]) for name in ('tests', 'planning', 'reliability')}
    families = sorted({r['source_group'] for rs in tracks.values() for r in rs})
    destination.mkdir(parents=True)
    copied = {}

    def copy(source, relative, expected=None):
        source = Path(source)
        actual = digest(source)
        if expected and actual != expected:
            raise ValueError('Source hash changed: '+str(source))
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if digest(target) != actual:
            raise ValueError('Copy verification failed')
        copied[str(source.resolve())] = relative
        return relative

    inventory = []
    for number, family in enumerate(families, 1):
        metadata = external.get(family, original.get(family))
        root = Path(metadata['local_source']) if family in external else source_root/family
        folder = f'audit/sources/{number:02d}'
        items = ({f['path']: f['sha256'] for f in metadata['files']}
                 if family in external else metadata['python_source_files'])
        exported = [copy(root/name, folder+'/'+name, expected) for name, expected in sorted(items.items())]
        notices = []
        for source in sorted(root.rglob('*')):
            if source.is_file() and source.name.lower().startswith(('license', 'copying', 'notice', 'copyright')):
                notices.append(copy(source, folder+'/'+source.relative_to(root).as_posix()))
        inventory.append(dict(source_group=family, revision=metadata['revision'], directory=folder,
                              license=metadata.get('license', 'See included upstream notices; no blanket dataset license assigned'),
                              files=exported, notice_files=notices,
                              scope='Inventoried pinned Python/source files plus upstream legal notices; not a complete executable repository archive'))

    reference_table = {}
    for number, entry in enumerate(mapping['files'], 1):
        source = Path(entry['path'])
        key = str(source.resolve())
        relative = copied.get(key)
        if relative is None:
            relative = copy(source, f'audit/authored-references/{number:02d}/{source.name}', entry['sha256'])
        elif digest(destination/relative) != entry['sha256']:
            raise ValueError('Mapped reference hash mismatch')
        reference_table[entry['path']] = dict(path=relative, sha256=entry['sha256'], role=entry['scope'])

    index = []
    for track, records in tracks.items():
        for split in ('train', 'development', 'holdout'):
            selected = [r for r in records if r['candidate_split'] == split]
            relative = f'model-data/{split}/{track}.jsonl'
            target = destination/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            projected = []
            for line, row in enumerate(selected, 1):
                # Same strict allowlist for every split; evaluation never enters train.
                model = project_record(dict(row, candidate_split='train'))
                projected.append(model)
                refs = [reference_table[p] for p in mapping['record_file_mapping'].get(row['record_id'], [])]
                family = next(s for s in inventory if s['source_group'] == row['source_group'])
                index.append(dict(record_id=row['record_id'], track=track, split=split,
                                  source_group=row['source_group'], model_file=relative, line=line,
                                  original_source_directory=family['directory'], revision=family['revision'],
                                  reference_files=refs,
                                  mapping_scope='Declared task modules; not an execution-complete dependency closure' if refs else 'Family-level provenance; no per-file solution asserted'))
            target.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in projected), encoding='utf-8')
            if split == 'train':
                if projected != rows(paths['preview']/(track+'-train-preview.jsonl')):
                    raise ValueError('Training export differs from audited active preview')
    save(destination/'audit/records.json', index)
    save(destination/'audit/sources.json', inventory)
    for relative in ('config-planned.json', 'dataset-profile-v02/semantic-review.json', 'native-label-audit-v01/report.json'):
        copy(EXP/relative, 'provenance/'+relative)
    for source in (ROOT/'LICENSE', ROOT/'LICENSE.md', ROOT/'LICENSE.txt'):
        if source.exists():
            copy(source, 'provenance/project-'+source.name)
    readme = '''# Intent-driven TDD dataset: portable review package

95 candidate examples: 58 task-to-tests, 15 planning, 22 clarification/integrity.
Splits: 78 train-family candidates, 9 development, 8 holdout.

`model-data/` contains ONLY allowlisted conversations. Train, development and
holdout are physically separated. Tracks remain separate: no training mixture
has been approved. This package does not enable training or freeze the splits.

`audit/records.json` joins each example to its conversation file/line, pinned
source family and mapped reference modules. `audit/sources.json` records revisions
and copied file inventories. Sources are stored once per family. Authored/adapted
references are labeled separately from original upstream modules. Original source
is not necessarily a passing implementation of the adapted task contract.

NEVER feed audit files, source snapshots or reference implementations into model
inputs/targets. Do not stringify the audit records for training. Generated pytest
targets and necessary synthetic fixtures in model conversations are intentional.

Scope: inventoried upstream source files and license notices, not full runnable
repositories. Reference mappings cover the declared modules for all 58 test rows;
they are not complete runtime fixtures. Plans/decisions have family-level links.
No absolute local path is required to resolve package links. Historical provenance
reports may mention the author's machine, but are not needed to resolve links.

This is a local review package, not a published or uniformly licensed dataset.
Upstream code retains its own notices and restrictions; no blanket license is
assigned here. Check included notices before redistribution. Dataset readiness,
runtime protocol and actual trainer label parity remain unresolved. The included
semantic review records three cross-split overlaps of taught principles.

Run `python verify_package.py` after extracting to verify hashes and record links.
'''
    owner_confirmed = ['ReflexModels', 'repo-context']
    missing_notices = [s['source_group'] for s in inventory if not s['notice_files'] and s['source_group'] not in owner_confirmed]
    readme += '\nOwner confirmation: on 2026-10-31 the dataset owner confirmed ownership of ReflexModels and repo-context and authorized their inclusion. These snapshots lack license notices; no third-party permission blocker is inferred for those owner-controlled projects.\n'
    if missing_notices:
        readme += '\nRedistribution blocker: no upstream license/notice file was found in the pinned snapshots for: '+', '.join(missing_notices)+'. Obtain permission or resolve their licensing before distributing their code publicly. This package is for local review pending that resolution.\n'
    (destination/'README.md').write_text(readme, encoding='utf-8')
    verifier = '''import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
for name,expected in manifest['sha256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
records=json.loads((root/'audit/records.json').read_text(encoding='utf-8'))
for r in records:
    row=json.loads((root/r['model_file']).read_text(encoding='utf-8').splitlines()[r['line']-1])
    assert set(row)=={'messages'}
    assert (root/r['original_source_directory']).is_dir()
    for f in r['reference_files']:
        assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
assert len(records)==95
assert sum(bool(r['reference_files']) for r in records if r['track']=='tests')==58
assert sum(r['split']=='train' for r in records)==78
print('PASS: file hashes, 95 record links, 58 test mappings, 78 training candidates')
'''
    (destination/'verify_package.py').write_text(verifier, encoding='utf-8')
    hashes = {p.relative_to(destination).as_posix(): digest(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    save(destination/'manifest.json', dict(schema_version=1, status='local review package; not published',
         counts=dict(Counter(r['split'] for r in index)), training_enabled=False,
         training_matches_active_preview=True, source_families=len(inventory),
         missing_upstream_license_notices=missing_notices, public_redistribution_cleared=False,
         owner_confirmed_source_families=owner_confirmed,
         builder_sha256=digest(Path(__file__)), sha256=hashes))
    archive = destination.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for p in sorted(destination.rglob('*')):
            if p.is_file():
                bundle.write(p, destination.name+'/'+p.relative_to(destination).as_posix())
    print(json.dumps(dict(directory=str(destination), archive=str(archive), archive_sha256=digest(archive), bytes=archive.stat().st_size, records=len(index))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    build(parser.parse_args().output)
