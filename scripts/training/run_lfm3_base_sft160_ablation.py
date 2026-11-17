"""Matched initialization ablation; preserve original pilot160 artifacts."""
import json
from pathlib import Path
import subprocess
import time
from run_lfm3_base_sft160 import BASE, DATA, ROOT, RUNTIME, dump, read, sha, environment

EXP = 'exp-009-base-sft160-lr1e4'
OLD = BASE / 'pilot160-runtime-local'
PY = '/workspace/.venvs/lfm3-sft/bin/python'
VLLM = '/workspace/.venvs/lfm3-vllm/bin/python'
TRAIN = ROOT / 'scripts/training/run_lfm3_base_sft160.py'
DEV = BASE / 'sft160-dev-v01/questions.jsonl'
ORIGINAL = BASE / 'exp-000-baseline'


def step(name, command, expected):
    command = list(map(str, command))
    receipt = RUNTIME / 'stages' / (name + '.json')
    if receipt.exists():
        r = read(receipt)
        assert r['command'] == command and sha(expected) == r['sha256'], name
        return
    log = RUNTIME / 'logs' / (name + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    print('START ' + name, flush=True)
    start = time.time()
    with log.open('xb') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    assert result.returncode == 0, f'{name} failed; preserve partials and inspect {log}'
    assert expected.exists(), name
    dump(receipt, dict(command=command, sha256=sha(expected), seconds=time.time()-start))
    print('COMPLETED ' + name, flush=True)


def inference(label, model, cohort, thinking=False):
    suffix = '-thinking' if thinking else ''
    out = RUNTIME / 'inference' / label / (cohort + suffix)
    cmd = [VLLM, ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
           '--experiment-dir', ORIGINAL, '--output-dir', out, '--merged-model', model,
           '--limit', '100', '--batch-size', '4', '--temperature', '0.1', '--top-k', '50',
           '--repetition-penalty', '1.1', '--protocol-name', 'sft160-dev-matched-v01'+suffix]
    if cohort in ['dev20', 'smoke2', 'reasoning4']:
        packet = DEV if cohort == 'dev20' else OLD/(cohort+'.jsonl')
        cmd += ['--packet-path', packet, '--packet-sha256', sha(packet), '--all-rows']
    if thinking:
        cmd += ['--enable-thinking']
    step(label+'-'+cohort+suffix, cmd, out/'manifest.json')
    manifest = read(out/'manifest.json')
    assert manifest['status'] == 'completed' and manifest['count'] == manifest['expected_count']
    if cohort == 'cetvel100':
        step(label+'-cetvel100-score', [VLLM, ROOT/'scripts/evaluation/score_lfm3_cetvel.py',
             '--results-dir', out], out/'scores.json')


def main():
    environment()
    cfg = read(BASE/EXP/'config.yaml')
    old_cfg = read(BASE/'exp-007-sft160-lr1e4/config.yaml')
    assert cfg['training'] == old_cfg['training'], 'Initialization must be the only recipe change'
    assert cfg['model']['revision'] == old_cfg['model']['parent_revision']
    assert sha(DATA/'train.jsonl') == cfg['dataset']['train_sha256']
    assert all(sha(DATA/name) == digest for name, digest in read(DATA/'manifest.json')['files'].items())
    assert sha(DEV) == read(BASE/'sft160-dev-v01/manifest.json')['questions_sha256']
    frozen = read(OLD/'run-source-manifest.json')
    # Evaluation implementation and frozen packets must match the previous run.
    for relative, digest in frozen['files'].items():
        if relative.startswith('scripts/evaluation/'):
            assert sha(ROOT/relative) == digest, relative
    sources = [Path(__file__), TRAIN, ROOT/'scripts/training/merge_lfm3_base_sft160_checkpoint.py',
               BASE/EXP/'config.yaml', DATA/'manifest.json', DEV]
    manifest = dict(files={str(p.relative_to(ROOT)):sha(p) for p in sources},
                    original_source_manifest_sha256=sha(OLD/'run-source-manifest.json'))
    source_path = RUNTIME/'run-source-manifest.json'
    if source_path.exists():
        assert read(source_path) == manifest, 'Ablation source changed'
    else:
        dump(source_path, manifest)
    for label in ['base', 'exp-007-sft160-lr1e4-step60']:
        for cohort in ['dev20', 'cetvel100', 'turblimp']:
            expected = OLD/'inference'/label/cohort/('scores.json' if cohort=='turblimp' else 'manifest.json')
            assert expected.exists()
            receipt = OLD/'stages'/(label+'-'+cohort+'.json')
            assert sha(expected) == read(receipt)['expected_sha256']
    step('prepare', [PY, TRAIN, '--mode', 'prepare'], RUNTIME/'init-model.json')
    assert sha(RUNTIME/'train-tokenized.jsonl') == sha(OLD/'train-tokenized.jsonl')
    for mode in ['smoke', 'tiny-overfit']:
        expected = BASE/EXP/'results-local'/mode/'training-manifest.json'
        step(mode, [PY, TRAIN, '--mode', mode], expected)
        assert read(expected)['status'] == 'passed'
    inference('smoke', BASE/EXP/'results-local/smoke/merged-model', 'smoke2')
    answers = [json.loads(s) for s in (RUNTIME/'inference/smoke/smoke2/answers.jsonl').read_text(encoding='utf8').splitlines()]
    assert len(answers) == 2 and all(r['prediction'].strip() and r['finish_reason'] != 'timeout' for r in answers)
    assert read(RUNTIME/'label-audit.json')['status'] == 'passed'
    dump(RUNTIME/'gpu-gate.json', dict(baseline_completed=True, labels_audited=True,
        smoke_passed=True, tiny_overfit_passed=True, semantic_review_passed=True,
        semantic_manifest_sha256=sha(DATA/'manifest.json'), tokenized_sha256=sha(RUNTIME/'train-tokenized.jsonl'),
        model_revision=cfg['model']['revision'], training_source_sha256=sha(TRAIN),
        config_sha256={EXP:sha(BASE/EXP/'config.yaml')}, dev_packet_sha256=sha(DEV)))
    step('sft', [PY, TRAIN, '--mode', 'sft'], BASE/EXP/'results-local/sft/training-manifest.json')
    dest = BASE/EXP/'results-local/merged-step60'
    step('merge60', [PY, ROOT/'scripts/training/merge_lfm3_base_sft160_checkpoint.py',
         '--experiment', EXP, '--step', '60'], dest/'merge-receipt.json')
    for label, model in [('cpt-only', OLD/'cpt-merged'), (EXP+'-step60', dest)]:
        inference(label, model, 'dev20')
        inference(label, model, 'cetvel100')
        out = RUNTIME/'inference'/label/'turblimp'
        step(label+'-turblimp', [PY, ROOT/'scripts/evaluation/evaluate_lfm3_turblimp.py',
             '--experiment-dir', ORIGINAL, '--output-dir', out, '--merged-model', model], out/'scores.json')
        inference(label, model, 'reasoning4')
        inference(label, model, 'reasoning4', True)
    dump(RUNTIME/'completion.json', dict(status='completed-pending-owner-review',
         preselected_checkpoint=EXP+'-step60', comparison='base, CPT, base-SFT, CPT-SFT',
         original_runtime=str(OLD), diagnostic_only=True))


if __name__ == '__main__':
    main()
