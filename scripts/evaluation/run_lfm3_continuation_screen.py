"""Matched official-general-preset screening, without training or W&B inference."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time


def main():
    root = Path('experiments/turkish-capability/lfm3-1.7b')
    control = root/'preparation-local/continuation-screen-v01'
    control.mkdir(parents=True, exist_ok=False)
    os.environ.update(HF_HOME='/workspace/.cache/huggingface', PYTHONUNBUFFERED='1')
    py = '/workspace/.venvs/lfm3/bin/python'
    vpy = '/workspace/.venvs/lfm3-vllm/bin/python'
    names = ['exp-000-baseline', 'exp-002-mixed-cpt', 'exp-003-cpt-cont-50m', 'exp-004-cpt-cont-100m']
    protocol = dict(name='continuation-screen-official-general-v01', models=names,
        temperature=0.1, top_k=50, top_p=1.0, repetition_penalty=1.1,
        max_new_tokens=4096, context=8192, batch_size=4, seed=3407,
        selected_ids=json.loads((root/'cpt-eval-fast100-v02.json').read_text())['selected_ids'],
        scope='Exploratory development screening; fixed seed does not guarantee bitwise reproducibility. Historical greedy outputs are not matched comparators.')
    (control/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')

    def run(cmd, label):
        started = time.time()
        with (control/(label+'.log')).open('w') as out:
            result = subprocess.run([str(x) for x in cmd], stdout=out, stderr=subprocess.STDOUT)
        with (control/'commands.jsonl').open('a') as out:
            out.write(json.dumps(dict(command=[str(x) for x in cmd], seconds=time.time()-started,
                exit_code=result.returncode, label=label))+'\n')
        if result.returncode:
            raise RuntimeError('Failed: '+label)
        print('COMPLETED '+label, flush=True)

    results = {}
    canonical = None
    for name in names:
        exp = root/name
        training = exp/'results-local/cpt-v01'
        if name != names[0] and not (training/'merged-model').exists():
            run([py, 'scripts/evaluation/merge_lfm3_cpt.py', '--experiment-dir', exp,
                '--training-dir', training], name+'-merge')
        output = exp/'results-local/continuation-screen-v01/cetvel'
        cmd = [vpy, 'scripts/evaluation/evaluate_lfm3_vllm_batched.py', '--experiment-dir', exp,
            '--output-dir', output, '--limit', '100', '--batch-size', '4',
            '--temperature', '.1', '--top-k', '50', '--repetition-penalty', '1.1',
            '--protocol-name', protocol['name']]
        if name != names[0]:
            cmd += ['--merged-model', training/'merged-model']
        run(cmd, name+'-generation')
        run([py, 'scripts/evaluation/score_lfm3_cetvel.py', '--results-dir', output], name+'-score')
        manifest = json.loads((output/'manifest.json').read_text())
        assert manifest['status'] == 'completed' and manifest['count'] == 100
        assert manifest['selected_ids'] == protocol['selected_ids']
        if canonical is None:
            canonical = manifest
        else:
            for key in ['questions_sha256', 'selected_ids', 'decoding', 'packages', 'chat_template_sha256', 'eos_token_ids', 'seed']:
                assert canonical[key] == manifest[key], key
        likelihood = exp/'results-local/continuation-screen-v01'
        if name in names[2:]:
            for task in ['text', 'turblimp']:
                run([py, f'scripts/evaluation/evaluate_lfm3_{task}.py', '--experiment-dir', exp,
                    '--output-dir', likelihood/task, '--adapter', training/'adapter'], name+'-'+task)
        else:
            likelihood = exp/'results-local'/('base-v01' if name == names[0] else 'cpt-eval-v01')
        results[name] = dict(scores=json.loads((output/'scores.json').read_text()),
            text=json.loads((likelihood/'text/text-scores.json').read_text()),
            grammar=json.loads((likelihood/'turblimp/scores.json').read_text()),
            manifest=manifest, answers_sha256=hashlib.sha256((output/'answers.jsonl').read_bytes()).hexdigest())
    (root/'continuation-screen-results-v01.json').write_text(json.dumps(dict(protocol=protocol, results=results), indent=2)+'\n')
    archive = Path('/workspace/lfm3-continuation-screen-v01-20261112.tar.gz')
    files = list(control.rglob('*')) + [root/'continuation-screen-results-v01.json']
    files += list(Path('scripts/evaluation').glob('*lfm3*.py'))
    for name in names:
        files += list((root/name/'results-local/continuation-screen-v01').rglob('*'))
        merge = root/name/'results-local/cpt-v01/merge-manifest.json'
        if merge.exists():
            files.append(merge)
    files = sorted(set(p for p in files if p.is_file() and '__pycache__' not in p.parts))
    evidence = {p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with tarfile.open(archive, 'w:gz') as out:
        for p in files:
            out.add(p, arcname=p.as_posix(), recursive=False)
    with tarfile.open(archive, 'r:gz') as source:
        for name, digest in evidence.items():
            assert hashlib.sha256(source.extractfile(name).read()).hexdigest() == digest
    archive.with_suffix('.gz.json').write_text(json.dumps(dict(status='all_members_hash_verified',
        file_count=len(evidence), archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        files=evidence), indent=2)+'\n')
    print('CONTINUATION_SCREEN_COMPLETED', flush=True)


if __name__ == '__main__':
    main()
