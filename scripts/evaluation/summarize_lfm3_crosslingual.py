"""Validate matched conditions; report stopping/length and narrow numeric diagnostics."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
RUN = BASE / 'crosslingual-runtime-local'


def main():
    packet = RUN / 'combined-questions.jsonl'
    digest = hashlib.sha256(packet.read_bytes()).hexdigest()
    prompts = {r['id']: r for r in map(json.loads, packet.read_text(encoding='utf-8').splitlines())}
    assert len(prompts) == 15
    result = dict(packet_sha256=digest, independent_matched_cases=3, models={},
        interpretation='No human correctness/naturalness inferred. Numeric candidates require inspection; strict symbolic numeric matches are narrow automatic scores. Correlated language variants are not independent tasks.')
    signature = None
    for model in ['base', 'cpt', 'base-sft', 'cpt-sft']:
        folder = RUN / 'inference' / model
        m = json.loads((folder / 'manifest.json').read_text())
        rows = list(map(json.loads, (folder / 'answers.jsonl').read_text(encoding='utf-8').splitlines()))
        assert m['status'] == 'completed' and m['count'] == m['expected_count'] == len(rows) == 15
        assert len({r['id'] for r in rows}) == 15 and {r['id'] for r in rows} == set(prompts)
        assert m['questions_sha256'] == digest
        current = {k: m[k] for k in ['selected_ids', 'seed', 'chat_template_sha256', 'decoding', 'packages']}
        current['engine_settings'] = {k: v for k, v in m['engine_args'].items() if k not in ['model', 'revision', 'code_revision']}
        if signature is None:
            signature = current
        assert current == signature, 'Comparison protocol mismatch'
        conditions = {}
        for src, dst in [('en', 'en'), ('tr', 'en'), ('en', 'tr'), ('tr', 'tr'), ('symbolic', 'numeric')]:
            group = [r for r in rows if r['input_language'] == src and r['output_language'] == dst]
            assert len(group) == 3
            conditions[src + '-' + dst] = dict(n=3, stopping=dict(Counter(r['finish_reason'] for r in group)),
                median_generated_tokens=statistics.median(r['generated_tokens'] for r in group))
        numeric = []
        for r in rows:
            if r['task'] not in ['arithmetic', 'symbolic_arithmetic']:
                continue
            expected = 48 if r['task'] == 'arithmetic' else int(r['target'])
            text = r['prediction'].strip()
            numbers = re.findall(r'(?<!\w)-?\d+(?:[.,]\d+)?(?!\w)', text)
            numeric.append(dict(id=r['id'], expected=expected,
                strict_numeric_only_correct=text == str(expected),
                last_numeric_candidate=numbers[-1] if numbers else None,
                candidate_policy='Last numeral is a heuristic, not correctness: inspect reasoning, contradictions, units and any trailing unrelated output.'))
        result['models'][model] = dict(conditions=conditions, numeric_checks=numeric,
            strict_symbolic_matches=sum(n['strict_numeric_only_correct'] for n in numeric if 'symbolic' in n['id']),
            answers_sha256=hashlib.sha256((folder / 'answers.jsonl').read_bytes()).hexdigest())
    result['matched_protocol'] = signature
    (BASE / 'CROSSLINGUAL-INFERENCE-METRICS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'validated_models': 4, 'answers': 60, 'matched_protocol': True}))


if __name__ == '__main__':
    main()
