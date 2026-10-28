"""Upload only the validated GGUF release files to the existing Occam model repo.

Reads HF_API_KEY from the repository's ignored .env; never prints the credential.
Does not create repositories, change visibility, or modify adapter weights.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from dotenv import dotenv_values
from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download

REPO = 'cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora'
WEIGHT = 'Qwen3.5-4B-Turkish-Concise-Q4_K_M.gguf'
FILES = (WEIGHT, 'gguf-export-manifest.json', 'GGUF.md', 'README.md')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    folder = work / 'upload'
    receipt = work / 'gguf-upload-receipt.json'
    if receipt.exists():
        raise ValueError('Upload receipt already exists; inspect it before retrying.')
    if set(p.name for p in folder.iterdir()) != set(FILES):
        raise ValueError('Unexpected upload files')
    manifest = json.loads((folder / 'gguf-export-manifest.json').read_text())
    artifact = manifest['artifact']
    if artifact['filename'] != WEIGHT or sha(folder / WEIGHT) != artifact['sha256']:
        raise ValueError('GGUF hash mismatch')
    if not manifest['validation']['runtime_smoke_passed']:
        raise ValueError('Deployment validation not passed')
    expected = {name: sha(folder / name) for name in FILES}
    root = Path(__file__).resolve().parents[2]
    token = dotenv_values(root / '.env').get('HF_API_KEY')
    if not token:
        raise ValueError('HF_API_KEY missing')
    api = HfApi(token=token)
    if api.whoami()['name'] != 'cbarkinozer':
        raise ValueError('Unexpected Hub identity')
    info = api.model_info(REPO, files_metadata=True)
    destination = json.loads((work / 'destination.json').read_text())
    if info.sha != destination['parent_commit'] or info.private != destination['private']:
        raise ValueError('Destination changed since preparation; review before retrying')
    if any(file.rfilename == WEIGHT for file in info.siblings):
        raise ValueError('A GGUF with this filename already exists; do not overwrite silently')
    # Protect existing adapter identity; this commit only adds the GGUF/docs/manifest.
    existing = {file.rfilename: file for file in info.siblings}
    if existing['adapter_model.safetensors'].lfs.sha256 != manifest['source_adapter_sha256']['adapter_model.safetensors']:
        raise ValueError('Existing adapter identity changed')
    print('Uploading four whitelisted release files; existing visibility preserved.', flush=True)
    commit = api.create_commit(
        repo_id=REPO, repo_type='model', parent_commit=info.sha,
        commit_message='Add merged Occam Q4_K_M GGUF with export provenance and smoke validation',
        operations=[CommitOperationAdd(path_in_repo=name, path_or_fileobj=folder / name) for name in FILES],
    )
    record = dict(repo_id=REPO, revision=commit.oid, commit_url=commit.commit_url,
                  private=info.private, uploaded_files_sha256=expected, verification_complete=False)
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    remote = api.model_info(REPO, revision=commit.oid, files_metadata=True)
    weight = next(f for f in remote.siblings if f.rfilename == WEIGHT)
    if not weight.lfs or weight.lfs.sha256 != artifact['sha256'] or weight.size != artifact['size_bytes']:
        raise ValueError('Uploaded GGUF storage metadata mismatch')
    if remote.private != info.private:
        raise ValueError('Visibility changed')
    for name in FILES[1:]:
        path = Path(hf_hub_download(REPO, name, revision=commit.oid, token=token))
        if sha(path) != expected[name]:
            raise ValueError(f'Remote file mismatch: {name}')
    record.update(verification_complete=True,
                  gguf_verification='Hub LFS SHA256 and byte count; full GGUF not downloaded again',
                  small_files_verification='Downloaded and SHA256 checked at uploaded revision')
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        status = getattr(getattr(error, 'response', None), 'status_code', None)
        print(f'Upload/verification failed: {type(error).__name__}; HTTP status={status}.', file=sys.stderr)
        sys.exit(1)
