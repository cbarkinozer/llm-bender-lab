"""Freeze primary review, unblind only its five cases, run static paper diagnostics."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

from active_tdd_data import EXP, rows
from prepare_tdd_demo import digest, save
from publish_tdd_taxonomy_argilla import analyze, require_complete
from publish_tdd_threeway_argilla import payload

MODELS = ['base', 'arm_A', 'arm_B']
FOCAL_NAMES = {
    'path-parameters': ['extract_path_param_names', 'substitute_path_params'],
    'query-pair-merge': ['extract_query_pairs', 'merge_url_query_into_params'],
    'request-filenames': ['is_valid_filename', 'get_unique_request_filename'],
    'session-undo-redo': ['set', 'undo', 'redo', 'revert'],
    'session-history-limit': ['set', 'undo'],
}


def load_paper_tools(repo):
    """Load trusted detector definitions, excluding plotting and corpus runners."""
    source = repo/'step4_evaluation/analyze_test_smells.py'
    text = source.read_text(encoding='utf-8-sig')
    selected = []
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == 'run_analysis': break
        if isinstance(node, ast.Import) and any(a.name.split('.')[0] in {'matplotlib', 'seaborn', 'pandas', 'numpy'} for a in node.names): continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == 'matplotlib.use': continue
        selected.append(node)
    extracted = 'from __future__ import annotations\n' + ast.unparse(ast.Module(body=selected, type_ignores=[]))
    module = types.ModuleType('paper_demo_smell_tools')
    module.__file__ = str(source)
    sys.modules[module.__name__] = module
    # This is the user's trusted analyzer, never generated test code.
    exec(compile(extracted, str(source), 'exec'), module.__dict__)
    provenance = dict(repository=str(repo), commit=subprocess.check_output(
        ['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
        source_sha256=digest(source), normalized_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        executed_extraction_sha256=hashlib.sha256(extracted.encode()).hexdigest(),
        scope='Measurement tools only; AST definitions before corpus runner; plotting imports removed. No paper samples imported.')
    return module, provenance


def review_rows(snapshot, receipt, mappings, items):
    require_complete(snapshot)  # Only primary review is required for the demo.
    index = {r['record_id']: r['key'] for r in receipt['datasets']['primary']['index']}
    expected = {i['case_id'] for i in items}
    by_case = {i['case_id']: i for i in items}
    if set(index.values()) != expected or len(snapshot['items']) != len(expected):
        raise ValueError('Primary case inventory differs')
    results = []
    for row in snapshot['items']:
        rid = str(row.get('external_id') or row['id'])
        case = index[rid]
        if row['fields'] != payload(by_case[case], True):
            raise ValueError('Submitted review content does not match the blind packet')
        submitted = [r for r in row.get('responses', []) if r['status'] == 'submitted']
        if len(submitted) != 1: raise ValueError('Expected exactly one submitted primary reviewer')
        values = submitted[0]['values']
        ranking = values['ranking']['value']
        if {v['value'] for v in ranking} != {'X', 'Y', 'Z'} or len(ranking) != 3:
            raise ValueError('Incomplete ranking')
        mapping = mappings[case]
        ranks = {mapping[v['value']]: v['rank'] for v in ranking}
        if set(ranks) != set(MODELS) or any(not isinstance(v, int) or v < 1 for v in ranks.values()):
            raise ValueError('Invalid identity mapping/rank')
        assessments = {mapping[label]: values['assessment_' + label.lower()]['value'] for label in ('X', 'Y', 'Z')}
        if not set(assessments.values()) <= {'retain', 'repair', 'reject', 'uncertain'}:
            raise ValueError('Unknown assessment')
        results.append(dict(case_id=case, ranks=ranks, assessments=assessments,
            submitted_evidence=values['evidence']['value']))
    if {r['case_id'] for r in results} != expected: raise ValueError('Duplicate/missing primary case')
    return results


def aggregate_human(reviews):
    summary = {}
    for model in MODELS:
        summary[model] = dict(assessments=dict(Counter(r['assessments'][model] for r in reviews)),
            sole_best=sum(r['ranks'][model] == min(r['ranks'].values()) and list(r['ranks'].values()).count(min(r['ranks'].values())) == 1 for r in reviews),
            tied_best=sum(r['ranks'][model] == min(r['ranks'].values()) and list(r['ranks'].values()).count(min(r['ranks'].values())) > 1 for r in reviews))
    pairs = {}
    for a, b in [('base', 'arm_A'), ('base', 'arm_B'), ('arm_A', 'arm_B')]:
        pairs[a + '_vs_' + b] = dict(first_preferred=sum(r['ranks'][a] < r['ranks'][b] for r in reviews),
            tied=sum(r['ranks'][a] == r['ranks'][b] for r in reviews),
            second_preferred=sum(r['ranks'][a] > r['ranks'][b] for r in reviews))
    return dict(models=summary, pairwise=pairs)


def static_analysis(item, label, paper):
    code = item['candidates'][label]
    result = analyze(code)
    if result['status'] == 'unparseable': return result
    focal = next(v for k, v in FOCAL_NAMES.items() if '-'+k+'-' in item['case_id'])
    findings = {name: dict(flagged=False, evidence=[]) for name in paper.SMELL_NAMES}
    for name in focal:
        flags, details, parseable = paper.analyze_test_code(code, name)
        if not parseable: raise ValueError('Parser disagreement')
        for smell, flag in flags.items():
            if flag:
                findings[smell]['flagged'] = True
                if details[smell] not in findings[smell]['evidence']:
                    findings[smell]['evidence'].append(details[smell])
    result['smells'] = findings
    result['focal_names_from_supplied_interface'] = focal
    result['static_test_scan_eligible'] = result['test_functions'] > 0
    return result


def aggregate_static(records, names):
    result = {}
    for model in MODELS:
        selected = [r['analysis'] for r in records if r['model'] == model]
        eligible = [r for r in selected if r.get('static_test_scan_eligible')]
        counts = Counter(s['oracle_class'] for r in selected for s in r['sites'])
        result[model] = dict(outputs=len(selected), unparseable=sum(r['status'] == 'unparseable' for r in selected),
            parseable_without_test_functions=sum(r['status'] != 'unparseable' and not r['test_functions'] for r in selected),
            files_with_recognized_test_functions=len(eligible),
            static_test_functions=sum(r['test_functions'] for r in selected),
            flagged_files_by_smell={name: sum(r['smells'][name]['flagged'] for r in eligible) for name in names},
            files_with_any_flag=sum(any(s['flagged'] for s in r['smells'].values()) for r in eligible),
            oracle_site_classes={k: counts[k] for k in ['TRIVIAL', 'WEAK', 'STRONG', 'UNKNOWN']},
            static_oracle_sites=sum(counts.values()), runtime_reached_oracles='not_measured')
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--paper-repo', type=Path, default=Path('C:/Users/barkin/Documents/GitHub/slm_test_generation'))
    p.add_argument('--packet-dir', type=Path, default=Path('C:/Users/barkin/Documents/llm-bender-artifacts/tdd-gpu-20261107/blind-three-way-v02'))
    p.add_argument('--output', type=Path, default=EXP/'gpu-results-20261107/post-review-v01')
    args = p.parse_args()
    if args.output.exists(): raise ValueError('Preserve previous reports; choose a new output directory')
    receipt = json.loads((args.snapshot/'receipt.json').read_text())
    snapshot = json.loads((args.snapshot/'primary.json').read_text())
    source = args.packet_dir/'for-reviewer/primary-tests.jsonl'
    if digest(source) != receipt['source_sha256']: raise ValueError('Blind packet differs from reviewed packet')
    items = rows(source)
    require_complete(snapshot)
    # Freeze exported input before opening primary identities. No 169-site/manual-smell gate.
    backup = Path('C:/Users/barkin/Documents/llm-bender-artifacts/tdd-gpu-20261107/argilla-exports')/args.output.name
    if backup.exists(): raise ValueError('Preserve previous review freeze')
    backup.mkdir(parents=True)
    save(backup/'primary-frozen.json', snapshot)
    save(backup/'receipt.json', receipt)
    mapping_path = args.packet_dir/'PRIVATE-identities.json'
    mappings = {r['case_id']: r['mapping'] for r in json.loads(mapping_path.read_text())['mapping']}
    reviews = review_rows(snapshot, receipt, mappings, items)
    paper, provenance = load_paper_tools(args.paper_repo)
    # Verify oracle tool parity with requested checkout; do not silently substitute versions.
    original_oracle = args.paper_repo/'step4_evaluation/oracle_analysis.py'
    vendored_oracle = Path(__file__).parent/'paper_quality_tools/oracle_analysis.py'
    if original_oracle.read_text(encoding='utf-8-sig') != vendored_oracle.read_text(encoding='utf-8-sig'):
        raise ValueError('Requested oracle classifier differs; version it explicitly before analysis')
    provenance['oracle_source_sha256'] = digest(original_oracle)
    analyzed = [dict(case_id=i['case_id'], model=mappings[i['case_id']][label],
        analysis=static_analysis(i, label, paper)) for i in items for label in ('X', 'Y', 'Z')]
    measured = json.loads((EXP/'gpu-results-20261107/results-summary.json').read_text())
    summary = dict(scope='Five primary development tasks from one family; one user-submitted blind review',
        protocol_change='User waived exhaustive manual oracle/smell annotation for demo. Primary labels frozen before analysis; automatic labels are unvalidated diagnostics.',
        human=aggregate_human(reviews), automatic=aggregate_static(analyzed, paper.SMELL_NAMES),
        execution_and_generation=measured['results'],
        interpretation='Base preferred on four cases; adapters improve brevity/format but no useful-test or executable-correctness improvement demonstrated. No demonstrated benefit of rationale supervision.',
        supporting_review='Not included; no supporting identities disclosed in this report.', holdout_opened=False,
        primary_manual_review_complete=True, exhaustive_oracle_review='waived', manual_smell_review='waived for this demo',
        automatic_labels_human_validated=False,
        provenance=dict(paper_tools=provenance, snapshot_sha256=digest(args.snapshot/'primary.json'),
            receipt_sha256=digest(args.snapshot/'receipt.json'), packet_sha256=digest(source), mapping_sha256=digest(mapping_path)))
    args.output.mkdir(parents=True)
    save(args.output/'summary.json', summary)
    save(args.output/'submitted-primary-review.json', reviews)
    save(args.output/'automatic-per-candidate.json', analyzed)
    print(json.dumps(dict(human=summary['human'], automatic=summary['automatic']), indent=2))


if __name__ == '__main__': main()
