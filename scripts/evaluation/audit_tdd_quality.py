"""Conservative static triage; flags request semantic review, never prove cheating."""
import ast
from hashlib import sha256
import json
from pathlib import Path
from active_tdd_data import active_paths

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'


def inspect_tests(source):
    tree = ast.parse(source)
    assertions, numeric, exceptions, mocks, flags = [], [], [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            assertions.append(node.lineno)
            expression = node.test
            if isinstance(expression, ast.Constant) and expression.value:
                flags.append(dict(kind='constant-true-assertion', line=node.lineno))
            if isinstance(expression, ast.Compare) and len(expression.comparators)==1 and ast.dump(expression.left)==ast.dump(expression.comparators[0]):
                flags.append(dict(kind='self-comparison', line=node.lineno))
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            leaf = name.rsplit('.',1)[-1]
            if leaf.startswith('assert_'):
                numeric.append(dict(line=node.lineno, call=name))
            if name.endswith('pytest.raises'):
                target = ast.unparse(node.args[0]) if node.args else None
                exceptions.append(dict(line=node.lineno, exception=target))
                if target in ('Exception','BaseException'):
                    flags.append(dict(kind='broad-expected-exception', line=node.lineno))
            if leaf in ('setattr','patch','patch.object') or name.startswith('patch.'):
                mocks.append(dict(line=node.lineno, expression=ast.unparse(node)))
            if leaf in ('skip','xfail') or '.mark.skip' in name or '.mark.xfail' in name:
                flags.append(dict(kind='disabled-or-expected-failing-test', line=node.lineno))
            if name in ('time.sleep','sleep'):
                flags.append(dict(kind='real-sleep', line=node.lineno))
        if isinstance(node, ast.Attribute) and ast.unparse(node).startswith(('pytest.mark.skip','pytest.mark.xfail')):
            flags.append(dict(kind='disabled-or-expected-failing-test', line=node.lineno))
    success_helpers = [item for item in numeric if not item['call'].endswith('.assert_not_called')]
    if not assertions and not success_helpers and exceptions:
        flags.append(dict(kind='only-expected-exceptions-no-observable-success-control', line=None))
    if not assertions and not numeric and not exceptions:
        flags.append(dict(kind='no-recognized-oracle-review-custom-helpers', line=None))
    return dict(assert_lines=assertions, assertion_helper_calls=numeric, expected_exceptions=exceptions,
                patches_to_review=mocks, flags=flags,
                limitations='Does not infer correct expected values, positive-control sufficiency, mocked-away business logic, commented-out historical tests or implementation hardcoding.')


def main():
    out = EXP / 'quality-audit-v02'
    out.mkdir(exist_ok=True)
    results=[]
    path=active_paths()['tests']
    for line in path.read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        results.append(dict(record_id=row['record_id'],task_id=row['task_id'],split=row['candidate_split'],
                            input_records=path.relative_to(EXP).as_posix(),records_sha256=sha256(path.read_bytes()).hexdigest(),
                            artifact_sha256=sha256(row['artifact']['content'].encode()).hexdigest(),
                            findings=inspect_tests(row['artifact']['content'])))
    (out/'static-test-triage.json').write_text(json.dumps(dict(status='triage only; no semantic approval',rows=results),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Inspected',len(results),'test files;',sum(bool(r['findings']['flags']) for r in results),'files flagged.')


if __name__=='__main__': main()
