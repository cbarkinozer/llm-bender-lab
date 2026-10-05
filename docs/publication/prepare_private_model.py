"""Prepare only the private model upload; no auth, network or rights attestation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output.exists() or output == root or root in output.parents:
        raise ValueError('Choose a new output directory outside Git')
    manifest = json.loads((args.source / 'release-manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files_sha256'].items():
        if sha(args.source / name) != expected:
            raise ValueError(f'Source release hash mismatch: {name}')
    output.mkdir(parents=True)
    for name in ('adapter_model.safetensors', 'adapter_config.json', 'training-config.json'):
        shutil.copyfile(args.source / name, output / name)
    card = (root / 'docs/publication/MODEL-CARD.md').read_text(encoding='utf-8')
    card = card.replace('---\n', '---\nlicense: apache-2.0\n', 1)
    card = card.replace('# Turkish Direct Response LoRA — F / exp016',
                        '# Qwen3.5-4B Turkish Concise LoRA — F / exp016')
    card = card.replace('**Release draft.** Replace repository links, choose a license after rights review,\nand validate the loading example before publishing. No public Hub revision exists yet.',
                        '**Private release draft.** The owner selected Apache-2.0. Training-data\nprovenance/provider-terms review and fresh-environment loading verification remain\npending. This upload does not attest publication rights or authorize a public release.')
    card = card.replace('NAMESPACE/qwen3.5-4b-turkish-direct-lora-v1',
                        'cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora')
    card = card.replace('- Code, effective recipe and evidence: TODO add immutable GitHub commit link.',
                        '- Local code/evidence commit: `7d47f9a1a1cfa8d4421aeb19e799c4a20f942938`\n  in `cbarkinozer/llm-bender-lab`; GitHub publication has not been verified.')
    card = card.replace('- Dataset: TODO add Dataset Hub link and immutable dataset revision.',
                        '- Dataset: not uploaded yet; 104 training / 20 development examples.\n  Dataset license and public-release provenance review remain separate steps.')
    card = card.replace('- License: TODO owner decision; pinned upstream card declares Apache-2.0.',
                        '- Adapter license: Apache-2.0, selected by the owner; see `LICENSE`.\n  Upstream pinned base card also declares Apache-2.0. This is not a training-data rights attestation.')
    (output / 'README.md').write_text(card, encoding='utf-8')
    shutil.copyfile(root / 'LICENSE', output / 'LICENSE')
    manifest.update({
        'status': 'private-upload-draft-not-publication-cleared',
        'model_id': 'cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora',
        'dataset_id': None,
        'model_license': 'apache-2.0',
        'rights_review_attested_by_invoker': False,
        'prepared_for_upload_on': '2026-10-05',
        'private_visibility_required': True,
        'preparation_script_sha256': sha(Path(__file__)),
        'files_sha256': {p.name: sha(p) for p in sorted(output.iterdir())},
        'license_texts_and_published_revisions': 'Model license included; dataset license/provenance and public revisions pending',
    })
    (output / 'release-manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'files': sorted(p.name for p in output.iterdir()),
                      'uploaded': False, 'rights_review_attested': False}))


if __name__ == '__main__':
    main()
