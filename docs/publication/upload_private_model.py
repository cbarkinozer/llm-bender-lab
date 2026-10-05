"""Upload the prepared F model privately using HF_API_KEY from local .env.

Never prints/persists the credential or uploads .env. No visibility changes.
"""
import hashlib
import json
from pathlib import Path
import sys

from dotenv import dotenv_values
from huggingface_hub import HfApi, hf_hub_download


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    folder = Path('C:/Users/cbark/Documents/llm-bender-artifacts/publication/F-hf-private-20261005/model')
    receipt = folder.parent / 'upload-receipt.json'
    token = dotenv_values(root / '.env').get('HF_API_KEY')
    if not token:
        raise ValueError('HF_API_KEY missing or empty')
    manifest = json.loads((folder / 'release-manifest.json').read_text(encoding='utf-8'))
    expected = dict(manifest['files_sha256'])
    expected['release-manifest.json'] = sha(folder / 'release-manifest.json')
    if set(p.name for p in folder.iterdir()) != set(expected):
        raise ValueError('Unexpected upload files')
    for name, digest in expected.items():
        if sha(folder / name) != digest:
            raise ValueError(f'Local hash mismatch: {name}')
    repo = manifest['model_id']
    api = HfApi(token=token)
    identity = api.whoami()
    if identity['name'] != 'cbarkinozer':
        raise ValueError('Unexpected authenticated account')
    info = api.model_info(repo)
    if not info.private:
        raise ValueError('Destination must remain private')
    print('Credential accepted for cbarkinozer; private repository confirmed.', flush=True)
    commit = api.upload_folder(
        repo_id=repo, repo_type='model', folder_path=folder,
        parent_commit=info.sha,
        commit_message='Upload F exp016 Turkish concise LoRA and reproducibility metadata')
    print(f'Upload completed at revision {commit.oid}; downloading files for hash verification.', flush=True)
    # Preserve completion evidence even if subsequent network verification fails.
    record = {'repo_id': repo, 'revision': commit.oid, 'commit_url': commit.commit_url,
              'private': True, 'verification_complete': False,
              'uploaded_files_sha256': expected}
    receipt.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    for name, digest in expected.items():
        cached = Path(hf_hub_download(repo, name, revision=commit.oid, token=token))
        if sha(cached) != digest:
            raise ValueError(f'Remote download hash mismatch: {name}')
    if not api.model_info(repo, revision=commit.oid).private:
        raise ValueError('Repository visibility changed during upload')
    record['verification_complete'] = True
    receipt.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Avoid printing request headers, credential values or verbose tracebacks.
        status = getattr(getattr(error, 'response', None), 'status_code', None)
        print(f'Upload/verification failed: {type(error).__name__}; HTTP status={status}.', file=sys.stderr)
        sys.exit(1)
