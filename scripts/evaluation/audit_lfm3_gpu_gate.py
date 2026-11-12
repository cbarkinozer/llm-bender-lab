"""Create a manifest-bound CPT gate from completed real GPU diagnostics."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--experiment-dir', type=Path, required=True)
    p.add_argument('--baseline-dir', type=Path, required=True)
    a = p.parse_args()
    evidence = {}

    def read(path):
        data = path.read_bytes()
        evidence[str(path)] = hashlib.sha256(data).hexdigest()
        return json.loads(data)

    cfg = read(a.experiment_dir / 'config-planned.json')
    baseline = a.baseline_dir / 'results-local/base-v01'
    base = read(baseline / 'cetvel/manifest.json')
    if base['status'] != 'completed' or base['count'] != 500 or base['model'] != cfg['model']:
        raise ValueError('Completed matching baseline missing')
    root = a.experiment_dir / 'results-local'
    reports = {}
    for stage, folder in [('train-smoke', 'cpt-smoke-v01'), ('overfit', 'cpt-overfit-v01')]:
        commands = root / 'control' / (stage + '-commands.jsonl')
        commands_bytes = commands.read_bytes()
        evidence[str(commands)] = hashlib.sha256(commands_bytes).hexdigest()
        records = [json.loads(line) for line in commands_bytes.decode().splitlines()]
        if len(records) != 1 or records[0]['exit_code'] != 0:
            raise ValueError('Diagnostic stage failed or incomplete: ' + stage)
        report = read(root / folder / 'training-manifest.json')
        labels = read(root / folder / 'label-audit.json')
        gradients = read(root / folder / 'gradient-audit.json')
        state = read(root / folder / 'trainer_state.json')
        if report['model'] != cfg['model'] or report['source_manifest_sha256'] != hashlib.sha256((a.experiment_dir / cfg['active_cpt_manifest']).read_bytes()).hexdigest():
            raise ValueError('Diagnostic model/data identity mismatch')
        if labels['status'] != 'passed' or labels['supervised_tokens'] <= 0:
            raise ValueError('Packed labels failed')
        if gradients['status'] != 'passed' or not all(gradients[k] for k in ['finite', 'nonzero', 'input_embeddings_frozen', 'output_embeddings_frozen']):
            raise ValueError('Actual gradient/frozen-embedding check failed')
        if state['global_step'] != (2 if stage == 'train-smoke' else 30):
            raise ValueError('Diagnostic did not finish expected steps')
        loss = report['training']['train_loss']
        if not math.isfinite(loss) or loss <= 0 or not 0 < report['peak_gpu_allocated_bytes'] < 24564 * 1024**2:
            raise ValueError('Invalid loss/memory diagnostic')
        if stage == 'overfit':
            before, after = report['initial_evaluation']['eval_loss'], report['development']['eval_loss']
            if not math.isfinite(before) or not math.isfinite(after) or after >= before * .98:
                raise ValueError('Tiny-overfit loss must decrease by at least 2%')
        reports[stage] = dict(training=report['training'], development=report['development'],
            initial_evaluation=report['initial_evaluation'], peak_gpu_allocated_bytes=report['peak_gpu_allocated_bytes'])
    output = a.experiment_dir / 'data-local/gpu-gate.json'
    if output.exists():
        raise ValueError('Preserve existing gate; do not overwrite')
    output.write_text(json.dumps(dict(baseline_completed=True, training_smoke_passed=True,
        labels_audited=True, tiny_overfit_passed=True, model_revision=cfg['model']['revision'],
        data_manifest_sha256=hashlib.sha256((a.experiment_dir / cfg['active_cpt_manifest']).read_bytes()).hexdigest(),
        evidence_sha256=evidence, diagnostics=reports,
        scope='Real pinned BF16 model, actual packed labels and gradients; not benchmark improvement evidence'), indent=2) + '\n')
    print(json.dumps(dict(status='GPU_GATE_PASSED', experiment=str(a.experiment_dir), diagnostics=reports), indent=2))


if __name__ == '__main__':
    main()
