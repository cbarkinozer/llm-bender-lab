"""Versioned, two-stage oracle/smell review. Never execute generated code."""
import argparse
import ast
import json
from pathlib import Path
import uuid

from active_tdd_data import EXP, rows
from prepare_tdd_demo import digest, save
from publish_tdd_threeway_argilla import credential, api_get, payload, settings
from paper_quality_tools import oracle_analysis as oracle
from paper_quality_tools import analyze_test_smells as smells

LABELS = ['TRIVIAL', 'WEAK', 'STRONG', 'UNKNOWN']
RUBRIC = (
    'Rate only the highlighted oracle site, using the full candidate and requirement. '
    'TRIVIAL: constant/tautological/self-comparison, unable to distinguish focal behavior. '
    'WEAK: SUT-dependent existence, truthiness, nullity, type, non-emptiness or coarse shape. '
    'STRONG: specific expected value/content, state transition, exception/warning or relevant mock interaction. '
    'UNKNOWN: insufficient evidence of dependency or strength. A precise but wrong expectation can be STRONG: '
    'record correctness separately. assert True remains TRIVIAL after a focal call. '
    'Static presence does not prove execution. Parameterization does not increase strength. '
    'Missing implementation context can justify UNKNOWN; do not guess. '
    'No oracle/unparseable are administrative statuses, not UNKNOWN or weak assertions. '
    'Protocol: paper manual_validation/oracle_classes/PROTOCOL_V2.md, prospectively adopted for this review. '
    'Do not consult machine predictions or private identities before submitting independent labels.'
)
SMELL_HELP = {
    'assertion_roulette': 'Multiple assertions without diagnostic messages; assess whether failures remain understandable.',
    'eager_test': 'Repeated focal calls in one test; necessary state transitions can be justified.',
    'mystery_guest': 'External file/network/database resource coupling; controlled tmp fixtures may be appropriate.',
    'magic_number_test': 'Unexplained numeric assertion literals; requirement-derived expected values may be appropriate.',
    'obscure_test': 'Excessive length or local state obscures test purpose.',
    'general_fixture': 'Oversized/general setup; distinguish necessary fixture state from unused setup.',
    'conditional_test_logic': 'Branch/loop/try logic inside tests; assess whether it obscures or skips checks.',
    'fragile_test': 'Clock, sleep, randomness, hardcoded paths or other uncontrolled environment dependence.',
    'unknown_test': 'Unverified action: no effective oracle for the behavior.',
    'trivial_assertion': 'Paper smell: ALL checks in a test are coarse/null/type/bool or tautological. Broader than oracle-class TRIVIAL; WEAK oracles may trigger this smell.',
    'duplicated_setup': 'Repeated setup across tests that impairs maintenance.',
}


def analyze(code):
    """Return static evidence only; no eval/import/exec of candidate code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return dict(status='unparseable', sites=[], smells={}, test_functions=0)
    sut_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or '').split('.')[0] == 'posting':
            sut_names.update(a.asname or a.name for a in node.names)
        if isinstance(node, ast.Import):
            sut_names.update(a.asname or a.name for a in node.names if a.name.split('.')[0] == 'posting')
    sites = [s.to_dict() for s in oracle.classify_oracles(code, sut_names=sut_names)]
    # Keep every raw assert visible even if the classifier misses its context.
    locations = {(s['lineno'], s['col_offset']) for s in sites}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and (node.lineno, node.col_offset) not in locations:
            sites.append(dict(oracle_id='unclassified', oracle_kind='assert', oracle_class='UNKNOWN',
                lineno=node.lineno, col_offset=node.col_offset, sut_dependent=None,
                classification_reason='Raw assertion not covered by paper classifier traversal'))
    sites.sort(key=lambda s: (s['lineno'], s['col_offset'], s['oracle_kind']))
    for i, site in enumerate(sites, 1):
        site['oracle_id'] = f'oracle_{i:04d}'
        site['source'] = code.splitlines()[site['lineno'] - 1].strip()
    funcs = smells._get_test_functions(tree)
    evidence = {name: [] for name in smells.SMELL_NAMES}
    module_checks = {'general_fixture': lambda: smells.detect_general_fixture(tree),
                     'duplicated_setup': lambda: smells.detect_duplicated_setup(funcs)}
    for name, check in module_checks.items():
        found, detail = check()
        if found: evidence[name].append(dict(scope='module', reason=detail))
    for func in funcs:
        checks = {
            'assertion_roulette': lambda: smells.detect_assertion_roulette(func),
            'mystery_guest': lambda: smells.detect_mystery_guest(func, tree),
            'magic_number_test': lambda: smells.detect_magic_number_test(func),
            'obscure_test': lambda: smells.detect_obscure_test(func),
            'conditional_test_logic': lambda: smells.detect_conditional_test_logic(func),
            'fragile_test': lambda: smells.detect_fragile_test(func, tree),
            'unknown_test': lambda: smells.detect_unknown_test(func),
            'trivial_assertion': lambda: smells.detect_trivial_assertion(func),
        }
        for name, check in checks.items():
            found, detail = check()
            if found: evidence[name].append(dict(scope=func.name, lineno=func.lineno, reason=detail))
        for focal in sorted(sut_names):
            found, detail = smells.detect_eager_test(func, focal)
            if found: evidence['eager_test'].append(dict(scope=func.name, lineno=func.lineno, reason=detail))
    return dict(status='parseable' if sites else 'no_oracle', sites=sites, test_functions=len(funcs),
        smells={k: dict(flagged=bool(v), evidence=v) for k, v in evidence.items()},
        inferred_sut_names=sorted(sut_names), runtime_reached='not_measured')


def make_rows(items):
    oracles, smell_rows, automatic = [], [], []
    for item in items:
        # Reuse strict identity/think allowlist validation.
        payload(item, True)
        for label in ('X', 'Y', 'Z'):
            code = item['candidates'][label]
            analysis = analyze(code)
            base_id = item['case_id'] + ':' + label
            base = dict(requirement=item['requirement'], candidate='```python\n' + code + '\n```')
            for site in analysis['sites'] or [None]:
                key = base_id + ':' + (site['oracle_id'] if site else analysis['status'])
                target = (f"Line {site['lineno']}, column {site['col_offset']}: {site['source']}"
                          if site else 'Administrative status: ' + analysis['status'])
                oracles.append(dict(key=key, fields={**base, 'target': target}))
            smell_rows.append(dict(key=base_id, fields=base))
            automatic.append(dict(key=base_id, analysis=analysis))
    return oracles, smell_rows, automatic


def taxonomy_settings(rg, kind, assisted=False):
    fields = [rg.TextField(name='requirement', title='Requirement and interface'),
              rg.TextField(name='candidate', title='Anonymous candidate', use_markdown=True)]
    if kind == 'oracles':
        fields.append(rg.TextField(name='target', title='Oracle site to classify'))
        questions = [
            rg.LabelQuestion(name='oracle_class', title='Class of this oracle site',
                labels=LABELS + ['NO_ORACLE', 'UNPARSEABLE'], required=True),
            rg.LabelQuestion(name='sut_dependent', title='Does this oracle depend on focal behavior?',
                labels=['yes', 'no', 'unsure', 'not_applicable'], required=True),
            rg.LabelQuestion(name='requirement_correctness', title='Is this expectation justified by the requirement?',
                labels=['correct', 'incorrect', 'ambiguous', 'not_applicable'], required=True),
        ]
        guidelines = RUBRIC
    else:
        questions = [rg.LabelQuestion(name=name, title=name.replace('_', ' ').title(),
            description=SMELL_HELP[name], labels=['present', 'absent', 'uncertain', 'not_rateable'], required=True)
            for name in smells.SMELL_NAMES]
        guidelines = ('Independently rate every smell, including possible false negatives. ' +
            'Heuristic thresholds are not proof of bad quality. Use not_rateable for missing/unparseable code; '
            'no collected tests is not evidence of smell-free code. Do not reward mocks that bypass real logic. '
            'Eight classic categories plus three additional checks from the current paper implementation. '
            'Machine predictions are hidden until the independent review is frozen. ')
    if assisted:
        fields.append(rg.TextField(name='automatic_findings', title='Static machine prediction and evidence', use_markdown=True))
        guidelines += (' This is assisted adjudication, not an independent second rating. '
            'Record your final labels, including rejected automatic flags and missed findings. '
            'Previous independent labels remain frozen separately. UNKNOWN is not an intermediate strength. '
            'Static flags and assertion classes do not prove runtime execution or passing correctness.')
    questions += [rg.LabelQuestion(name='confidence', title='Confidence', labels=['high', 'medium', 'low'], required=True),
                  rg.TextQuestion(name='evidence', title='Evidence / ambiguity / reasons for corrections', required=True)]
    return rg.Settings(guidelines=guidelines, fields=fields, questions=questions)


def log_dataset(client, rg, args, key, kind, records, schema):
    name = 'tdd-' + kind + '-20261107-v02'
    dataset = client.datasets(name=name, workspace=args.workspace)
    if dataset is None:
        dataset = rg.Dataset(name=name, workspace=args.workspace, settings=schema, client=client).create()
    current = api_get(args.url, key, f'datasets/{dataset.id}/records?limit=1000&include=responses')
    existing = {str(r.get('external_id') or r['id']): r for r in current['items']}
    expected, pending = {}, []
    for row in records:
        rid = str(uuid.uuid5(uuid.NAMESPACE_URL, name + ':' + row['key']))
        expected[rid] = row['fields']
        if rid in existing:
            if existing[rid]['fields'] != row['fields']: raise ValueError('Existing content differs: ' + kind)
        else:
            pending.append(rg.Record(id=rid, fields=row['fields']))
    if pending: dataset.records.log(pending)
    actual = api_get(args.url, key, f'datasets/{dataset.id}/records?limit=1000&include=responses')
    if actual['total'] != len(expected) or len(actual['items']) != len(expected): raise ValueError('Record count mismatch')
    for row in actual['items']:
        if row['fields'] != expected[str(row.get('external_id') or row['id'])]: raise ValueError('Content changed')
        if row.get('suggestions'): raise ValueError('Unexpected prefilled labels')
    return dict(id=str(dataset.id), name=name, records=len(expected),
        url=args.url + f'/dataset/{dataset.id}/annotation-mode',
        index=[dict(record_id=str(uuid.uuid5(uuid.NAMESPACE_URL, name + ':' + r['key'])), key=r['key']) for r in records])


def require_complete(snapshot):
    if len(snapshot['items']) != snapshot['total'] or not snapshot['total']:
        raise ValueError('Incomplete or empty snapshot')
    if not all(any(r['status'] == 'submitted' for r in row.get('responses', [])) for row in snapshot['items']):
        raise ValueError('Finish all independent overall, oracle and smell reviews before revealing automatic findings')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['publish', 'adjudicate', 'export'])
    p.add_argument('--credential-env', type=Path, required=True)
    p.add_argument('--url', default='http://127.0.0.1:7900')
    p.add_argument('--workspace', default='tdd-blind-comparison')
    p.add_argument('--packet-dir', type=Path, default=Path('C:/Users/barkin/Documents/llm-bender-artifacts/tdd-gpu-20261107/blind-three-way-v02/for-reviewer'))
    p.add_argument('--output', type=Path, default=EXP/'gpu-results-20261107/argilla-review-v02')
    args = p.parse_args()
    key = credential(args.credential_env)
    args.output.mkdir(parents=True, exist_ok=True)
    import argilla as rg
    client = rg.Argilla(api_url=args.url, api_key=key)
    items = rows(args.packet_dir/'primary-tests.jsonl')
    oracle_rows, smell_rows, automatic = make_rows(items)
    receipt_path = args.output/'receipt.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else dict(datasets={})
    receipt.update(dict(api_url=args.url, workspace=args.workspace, source_sha256=digest(args.packet_dir/'primary-tests.jsonl'),
        protocol='oracle PROTOCOL_V2 + current paper 11-smell implementation; measurement tools only',
        model_identities_uploaded=False, runtime_scores_uploaded=False))
    if args.action == 'export':
        from datetime import datetime, timezone
        dest = args.output/('snapshot-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        dest.mkdir()
        for kind, entry in receipt['datasets'].items():
            save(dest/(kind+'.json'), api_get(args.url, key, f'datasets/{entry["id"]}/records?limit=1000&include=responses'))
        save(dest/'receipt.json', receipt)
        print(str(dest)); return
    assisted = args.action == 'adjudicate'
    if assisted:
        snapshots = {}
        for kind in ('primary', 'oracles', 'smells'):
            entry = receipt['datasets'][kind]
            snapshots[kind] = api_get(args.url, key, f'datasets/{entry["id"]}/records?limit=1000&include=responses')
            require_complete(snapshots[kind])
        frozen = args.output/'independent-frozen.json'
        if frozen.exists():
            if json.loads(frozen.read_text()) != snapshots: raise ValueError('Independent labels changed after freeze')
        else: save(frozen, snapshots)
    else:
        schema = settings(rg, True)
        schema.questions = [q for q in schema.questions if not q.name.startswith('assertion_strength_')]
        schema.guidelines += (' Assertion strength is rated per oracle site in the separate tdd-oracles dataset. '
            'Smells are rated independently in tdd-smells. No 1-5 assertion-strength score is used in v02.')
        receipt['datasets']['primary'] = log_dataset(client, rg, args, key, 'threeway-primary',
            [dict(key=i['case_id'], fields=payload(i, True)) for i in items], schema)
    by_key = {a['key']: a['analysis'] for a in automatic}
    for kind, records in [('oracles', oracle_rows), ('smells', smell_rows)]:
        if assisted:
            records = json.loads(json.dumps(records))
            for row in records:
                base_key = row['key'].rsplit(':', 1)[0] if kind == 'oracles' else row['key']
                analysis = by_key[base_key]
                if kind == 'oracles':
                    site_id = row['key'].rsplit(':', 1)[1]
                    shown = next((s for s in analysis['sites'] if s['oracle_id'] == site_id), dict(status=analysis['status']))
                else: shown = {k: analysis[k] for k in ('status', 'test_functions', 'smells')}
                row['fields']['automatic_findings'] = '```json\n' + json.dumps(shown, indent=2) + '\n```'
        dataset_kind = kind + ('-adjudication' if assisted else '')
        receipt['datasets'][dataset_kind] = log_dataset(client, rg, args, key, dataset_kind, records,
            taxonomy_settings(rg, kind, assisted))
    save(args.output/'automatic-analysis.json', automatic)
    save(receipt_path, receipt)
    print(json.dumps({k: {a: b for a, b in v.items() if a != 'index'} for k, v in receipt['datasets'].items()}, indent=2))


if __name__ == '__main__': main()
