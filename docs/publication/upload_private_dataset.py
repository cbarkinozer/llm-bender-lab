"""Prepare/upload only the clean Occam dataset to its existing private HF repo.

Reads HF_API_KEY from .env without displaying or persisting the credential.
No changes to messages, targets, visibility, training or existing local releases.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from dotenv import dotenv_values
from huggingface_hub import DatasetCard, HfApi, hf_hub_download


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    source = Path('C:/Users/cbark/Documents/llm-bender-artifacts/publication/F-v1-7d47f9a/dataset')
    folder = Path('C:/Users/cbark/Documents/llm-bender-artifacts/publication/Occam-dataset-private-20261005/dataset')
    repo = 'cbarkinozer/Occam-Turkish-Response-SFT'
    token = dotenv_values(root / '.env').get('HF_API_KEY')
    if not token:
        raise ValueError('Missing HF_API_KEY')
    api = HfApi(token=token)
    if api.whoami()['name'] != 'cbarkinozer':
        raise ValueError('Unexpected account')
    info = api.repo_info(repo, repo_type='dataset')
    if not info.private or info.card_data.get('license') != 'apache-2.0':
        raise ValueError('Expected existing private repository with owner-selected Apache-2.0')
    if folder.exists():
        raise FileExistsError('Prepared upload already exists; inspect receipt before retrying')
    manifest = json.loads((source / 'release-manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files_sha256'].items():
        if sha(source / name) != expected:
            raise ValueError(f'Source hash mismatch: {name}')
    inputs = {}
    for split, count in [('train', 104), ('validation', 20)]:
        rows = [json.loads(l) for l in (source / f'data/{split}.jsonl').read_text(encoding='utf-8').splitlines()]
        if len(rows) != count or len({r['id'] for r in rows}) != count:
            raise ValueError(f'Count/ID mismatch: {split}')
        original_path = root / ('experiments/response-style-control/qwen3.5-4b/'
                                f'exp-016-diverse-coverage-sft/data-reviewed-v1/{split}-reviewed.jsonl')
        if sha(original_path) != manifest['source_data_sha256'][original_path.name]:
            raise ValueError('Frozen original source hash mismatch')
        originals = [json.loads(l) for l in original_path.read_text(encoding='utf-8').splitlines()]
        for row, original in zip(rows, originals):
            expected = [{k: m[k] for k in ('role', 'content')} for m in original['messages']]
            expected.append({'role': 'assistant', 'content': original['desired_answer']})
            if row['id'] != original['id'] or row['messages'] != expected:
                raise ValueError('Released conversation/target changed')
            if set(row) != {'id', 'category', 'subtype', 'scenario_group_id', 'origin',
                            'source_id', 'evaluation_only', 'messages'}:
                raise ValueError('Unexpected row metadata')
            if row['evaluation_only'] != (split == 'validation'):
                raise ValueError('Wrong evaluation flag')
        inputs[split] = {json.dumps(r['messages'][:-1], sort_keys=True, ensure_ascii=False) for r in rows}
    if inputs['train'] & inputs['validation']:
        raise ValueError('Exact train/development input overlap')
    card = (root / 'docs/publication/DATASET-CARD.md').read_text(encoding='utf-8')
    card = card.replace('---\n', '---\nlicense: apache-2.0\n', 1)
    card = card.replace('# Turkish Direct Response SFT v1', '# Occam — Turkish Response SFT')
    card = card.replace('**Draft: publication rights, provider provenance and license must be completed\nbefore public redistribution.** TODO add owner, license and linked model/revisions.',
                        'A small, human-reviewed Turkish response-style dataset curated by the author,\n'
                        '[cbarkinozer](https://huggingface.co/cbarkinozer), for the\n'
                        '[Occam adapter](https://huggingface.co/cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora).\n\n'
                        'The repository owner selected Apache-2.0; see `LICENSE`. This private upload\n'
                        'does not attest completion of historical provenance/provider-terms review.')
    card = card.replace('NAMESPACE/turkish-direct-response-sft-v1', repo)
    card = card.replace('used for exp016/F\nLoRA response-style SFT on Qwen3.5-4B.104 training rows and20 development rows.',
                        'used for Occam\nLoRA response-style SFT on Qwen3.5-4B. **104 training rows and 20 development rows.**')
    card = card.replace('additional training scenarios;\nthe released104/20 split is **not** an80/20 percentage split.',
                        'additional training scenarios;\nthe released 104/20 split is **not** an 80/20 percentage split.')
    card = card.replace('additions formed F.', 'additions formed the released dataset.')
    card = card.replace('License and allowable downstream use remain pending rights/provider-term review.',
                        'Dataset license: Apache-2.0, selected by the repository owner.\n'
                        'Historical provenance and provider-terms review remain incomplete; a license\n'
                        'selection alone does not establish all underlying publication rights.')
    DatasetCard(card).validate()
    (folder / 'data').mkdir(parents=True)
    for name in ('data/train.jsonl', 'data/validation.jsonl', 'source-origins.json'):
        shutil.copyfile(source / name, folder / name)
    (folder / 'README.md').write_text(card, encoding='utf-8')
    shutil.copyfile(root / 'LICENSE', folder / 'LICENSE')
    manifest.update({
        'status': 'private-upload-draft-not-publication-cleared', 'dataset_id': repo,
        'model_id': 'cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora',
        'dataset_license': 'apache-2.0', 'private_visibility_required': True,
        'rights_review_attested_by_invoker': False, 'prepared_for_upload_on': '2026-10-05',
        'preparation_script_sha256': sha(Path(__file__)),
        'files_sha256': {p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()},
        'license_texts_and_published_revisions': 'Dataset license included; provenance/public release review pending',
    })
    (folder / 'release-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    expected = {p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
    # Stop if an exact credential value accidentally appears in any prepared file.
    for p in folder.rglob('*'):
        if p.is_file() and token.encode() in p.read_bytes():
            raise ValueError('Credential detected in prepared upload')
    print('Validated 104 training and 20 development rows against frozen originals; private destination confirmed.', flush=True)
    commit = api.upload_folder(repo_id=repo, repo_type='dataset', folder_path=folder,
                               parent_commit=info.sha,
                               commit_message='Upload reviewed Occam Turkish SFT dataset: 104 train, 20 development')
    receipt = {'repo_id': repo, 'revision': commit.oid, 'private': True,
               'counts': {'train': 104, 'validation_development': 20},
               'verification_complete': False, 'uploaded_files_sha256': expected}
    receipt_path = folder.parent / 'upload-receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    for name, digest in expected.items():
        cached = Path(hf_hub_download(repo, name, repo_type='dataset', revision=commit.oid, token=token))
        if sha(cached) != digest:
            raise ValueError(f'Remote hash mismatch: {name}')
    if not api.repo_info(repo, repo_type='dataset').private:
        raise ValueError('Visibility changed during upload')
    receipt['verification_complete'] = True
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        status = getattr(getattr(error, 'response', None), 'status_code', None)
        print(f'Dataset preparation/upload/verification failed: {type(error).__name__}; HTTP status={status}.', file=sys.stderr)
        sys.exit(1)
