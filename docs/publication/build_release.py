"""Build a local, hash-checked HF draft. No network/auth/upload or source mutation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIMENT = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-016-diverse-coverage-sft'
HASHES = {
    'adapter_model.safetensors': '7ec9b04a5ecac7a031352fb5d0db281ef018c11951a4b4862c418e2b7a002ca1',
    'adapter_config.json': '6f7f0480fdcf1cc32aed14a1c66981c1a454840ece4f05932b0ef338846a4335',
}


def sha(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256')
    return digest.hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def clean(row, evaluation):
    messages = row['messages']
    if not messages or messages[-1]['role'] != 'user':
        raise ValueError(f"Expected unsupervised conversation ending in user: {row['id']}")
    if not isinstance(row['desired_answer'], str) or not row['desired_answer'].strip():
        raise ValueError(f"Empty target: {row['id']}")
    fields = ('id', 'category', 'subtype', 'scenario_group_id', 'origin', 'source_id')
    result = {name: str(row.get(name) or '') for name in fields}
    result['evaluation_only'] = evaluation
    result['messages'] = [{key: message[key] for key in ('role', 'content')} for message in messages]
    result['messages'].append({'role': 'assistant', 'content': row['desired_answer']})
    return result


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model-id', default='NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1')
    parser.add_argument('--dataset-id', default='NAMESPACE/turkish-direct-response-sft-v1')
    parser.add_argument('--model-license', choices=['apache-2.0'])
    parser.add_argument('--dataset-license', choices=['cc-by-4.0', 'apache-2.0', 'cc0-1.0'])
    parser.add_argument('--rights-reviewed', action='store_true')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Release weights must be built outside the Git workspace')
    if output.exists():
        raise FileExistsError('Choose a NEW output directory; never overwrite a release')
    for repo_id in (args.model_id, args.dataset_id):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo_id):
            raise ValueError('Expected a namespace/repository Hub ID')
    if (args.model_license or args.dataset_license) and not args.rights_reviewed:
        raise ValueError('Declaring a license requires an explicit owner rights-review attestation')
    if args.rights_reviewed and (not args.model_license or not args.dataset_license
            or any(repo.startswith('NAMESPACE/') for repo in (args.model_id, args.dataset_id))):
        raise ValueError('Rights-reviewed packages require real IDs and both license selections')
    for name, expected in HASHES.items():
        if sha(args.adapter_dir / name) != expected:
            raise ValueError(f'Wrong selected F artifact: {name}')
    config = json.loads((EXPERIMENT / 'config-reviewed-v1.yaml').read_text(encoding='utf-8'))
    sources, cleaned = {}, {}
    for split, count in [('train', 104), ('validation', 20)]:
        source = EXPERIMENT / f'data-reviewed-v1/{split}-reviewed.jsonl'
        if sha(source) != config['dataset']['hashes'][source.name]:
            raise ValueError(f'Frozen source hash mismatch: {split}')
        original = rows(source)
        if len(original) != count or len({row['id'] for row in original}) != count:
            raise ValueError(f'Unexpected count or duplicate IDs: {split}')
        sources[split] = original
        cleaned[split] = [clean(row, split != 'train') for row in original]
    inputs = lambda split: {json.dumps(row['messages'], ensure_ascii=False, sort_keys=True)
                            for row in sources[split]}
    if inputs('train') & inputs('validation'):
        raise ValueError('Exact train/validation conversation overlap')
    (output / 'model').mkdir(parents=True)
    (output / 'dataset/data').mkdir(parents=True)
    for name in HASHES:
        shutil.copyfile(args.adapter_dir / name, output / 'model' / name)
        if sha(output / 'model' / name) != HASHES[name]:
            raise ValueError('Copy verification failed')
    for kind, template, license_id in [('model', 'MODEL-CARD.md', args.model_license),
                                      ('dataset', 'DATASET-CARD.md', args.dataset_license)]:
        content = (HERE / template).read_text(encoding='utf-8')
        content = content.replace('NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1', args.model_id)
        content = content.replace('NAMESPACE/turkish-direct-response-sft-v1', args.dataset_id)
        if license_id:
            content = content.replace('---\n', f'---\nlicense: {license_id}\n', 1)
        if kind == 'model':
            content = content.replace('library_name: peft', f'library_name: peft\ndatasets:\n- {args.dataset_id}')
        (output / kind / 'README.md').write_text(content, encoding='utf-8')
    for split, data in cleaned.items():
        (output / f'dataset/data/{split}.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in data), encoding='utf-8')
    save(output / 'model/training-config.json', config)
    save(output / 'dataset/source-origins.json', {
        'status': 'owner must complete historical/provider rights and generation provenance',
        'counts': {split: {field: dict(Counter(str(row.get(field) or 'unspecified') for row in data))
                          for field in ('origin', 'category')} for split, data in sources.items()},
        'known_generator': 'unsloth/Qwen3.5-4B for saved original base answers; not all prompt/target authors',
        'personal_assistant_provider_model_terms': 'not fully established in surviving metadata',
    })
    for kind in ('model', 'dataset'):
        files = {path.relative_to(output / kind).as_posix(): sha(path)
                 for path in sorted((output / kind).rglob('*')) if path.is_file()}
        save(output / kind / 'release-manifest.json', {
            'status': 'rights-attested-needs-final-card-license-text-and-load-review' if args.rights_reviewed else 'draft-not-publication-cleared',
            'experiment': 'exp-016-diverse-coverage-sft', 'selected_step': 40,
            'model_id': args.model_id, 'dataset_id': args.dataset_id,
            'base_revision': config['model']['revision'],
            'source_data_sha256': config['dataset']['hashes'],
            'counts': {'train': 104, 'validation_development': 20},
            'builder_git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'builder_git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)),
            'builder_sha256': sha(Path(__file__)), 'files_sha256': files,
            'privacy_metadata_removed': True,
            'rights_review_attested_by_invoker': args.rights_reviewed,
            'license_texts_and_published_revisions': 'owner must add/record before publication',
        })
    print(json.dumps({'output': str(output), 'counts': {key: len(data) for key, data in cleaned.items()},
                      'uploaded': False, 'rights_review_attested': args.rights_reviewed}))


if __name__ == '__main__':
    main()
