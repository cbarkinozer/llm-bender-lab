"""Matched four-arm diagnostics, with explicit stopping and regression checks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/turkish-capability/lfm3-1.7b'
OLD = BASE/'pilot160-runtime-local/inference'
NEW = BASE/'base-sft160-runtime-local/inference'
ARMS = {'base':OLD/'base', 'cpt':NEW/'cpt-only',
        'base_sft':NEW/'exp-009-base-sft160-lr1e4-step60',
        'cpt_sft':OLD/'exp-007-sft160-lr1e4-step60'}


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    models = {}
    hashes = {}
    protocols = {}
    for arm, folder in ARMS.items():
        result = {}
        for cohort in ['dev20', 'cetvel100']:
            path = folder/cohort/'answers.jsonl'
            rows = [json.loads(s) for s in path.read_text(encoding='utf8').splitlines()]
            manifest = read(folder/cohort/'manifest.json')
            expected = 20 if cohort == 'dev20' else 100
            assert len(rows) == len({r['id'] for r in rows}) == manifest['count'] == expected
            assert manifest['status'] == 'completed'
            signature = {k:manifest[k] for k in ['questions_sha256', 'selected_ids', 'decoding', 'seed', 'chat_template_sha256']}
            if cohort in protocols:
                assert signature == protocols[cohort], f'Protocol differs: {arm}/{cohort}'
            protocols[cohort] = signature
            result[cohort] = dict(count=len(rows), termination=dict(Counter(r['finish_reason'] for r in rows)),
                total_generated_tokens=sum(r['generated_tokens'] for r in rows),
                median_generated_tokens=median(r['generated_tokens'] for r in rows),
                max_generated_tokens=max(r['generated_tokens'] for r in rows), wall_seconds=manifest['wall_seconds'])
            hashes[str(path.relative_to(ROOT))] = sha(path)
        grammar = read(folder/'turblimp/scores.json')
        assert grammar['packet_sha256'] == '59b083e817ddafafe15b42bb3a31fc99d2abff3876f41370c44f47d390b918d0'
        assert grammar['official_full_benchmark'] is False
        result['grammar'] = grammar
        result['cetvel_scores'] = read(folder/'cetvel100/scores.json')
        for cohort in ['reasoning4', 'reasoning4-thinking']:
            path = folder/cohort/'answers.jsonl'
            rows = [json.loads(s) for s in path.read_text(encoding='utf8').splitlines()]
            assert len(rows) == 4
            result[cohort] = dict(termination=dict(Counter(r['finish_reason'] for r in rows)),
                total_generated_tokens=sum(r['generated_tokens'] for r in rows),
                correctness='Not inferred from termination; requires separate grading')
        models[arm] = result
    base = models['base']
    for arm, result in models.items():
        result['regression_flags_vs_base'] = dict(
            dev_stopping=result['dev20']['count']-result['dev20']['termination'].get('eos',0) > 1,
            grammar_macro=result['grammar']['macro_accuracy'] < base['grammar']['macro_accuracy']-.02,
            grammar_phenomena=[k for k,v in result['grammar']['per_phenomenon'].items()
                               if v['accuracy'] < base['grammar']['per_phenomenon'][k]['accuracy']-.05-1e-10])
    payload = dict(status='matched-inference-completed', models=models, source_sha256=hashes,
                   protocols=protocols, preselected_checkpoint='exp-009-base-sft160-lr1e4-step60',
                   interpretation='Development diagnostic only. Recognition, stopping and overlap metrics do not establish naturalness or absolute correctness. No overall quality winner inferred.')
    (BASE/'BASE-SFT160-INFERENCE-METRICS.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    lines = ['# Initialization ablation: measured diagnostics', '',
             'Same frozen prompts and primary decoding settings verified across all four arms. SFT step60 uses the same100-step cosine horizon. Development data were already examined; this is not a fresh final test.', '',
             '| Arm | Dev EOS | Dev median tokens | CETVEL EOS | Grammar subset |',
             '|---|---:|---:|---:|---:|']
    for arm,r in models.items():
        lines.append(f"| {arm} | {r['dev20']['termination'].get('eos',0)}/20 | {r['dev20']['median_generated_tokens']:g} | {r['cetvel100']['termination'].get('eos',0)}/100 | {100*r['grammar']['macro_accuracy']:.3f}% |")
    lines += ['', 'Grammar is strict sentence-likelihood recognition on the pinned1600-pair subset, not a writing-quality score. CETVEL task metrics remain separate in the JSON report. Reasoning probes remain separate from primary thinking-disabled comparison. Review the raw answers before choosing an initialization; these automatic metrics do not grade answer correctness or Turkish naturalness.', '']
    (BASE/'BASE-SFT160-INFERENCE-RESULTS.md').write_text('\n'.join(lines),encoding='utf8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
