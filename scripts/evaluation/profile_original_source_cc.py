"""Read-only complexity audit of original pinned source, never training content."""
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
from hashlib import sha256
import argparse
from active_tdd_data import EXP,rows,active_paths,read_json
from profile_tdd_dataset import complexity,stats


def main(output='original-source-complexity-v02'):
    from active_tdd_data import inside
    out=inside(output)
    if out.exists():raise ValueError('Preserve existing source audit')
    parent=EXP.parent/'exp-001-local-thinking-10/app-core-v07'
    original=read_json(parent/'source-snapshots.json')
    root=Path(r'C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\sources')
    external={s['repository']:s for s in read_json(EXP/'external-app-audit.json')['sources']}
    families={r['source_group'] for r in rows(active_paths()['tests'])}
    files=[];functions=[];errors=[]
    for family in sorted(families):
        if family in external:
            metadata=external[family];source=Path(metadata['local_source']);revision=metadata['revision']
            items=[(f['path'],f['sha256']) for f in metadata['files']]
        else:
            metadata=original[family];source=root/family;revision=metadata['revision']
            items=list(metadata['python_source_files'].items())
        for relative,expected in items:
            p=source/relative
            if not p.exists():errors.append(dict(family=family,path=relative,error='missing local source'));continue
            if sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('Pinned source changed: '+str(p))
            path=Path(relative);is_test=any(part.casefold() in ('test','tests','testing') for part in path.parts[:-1]) or path.name.startswith('test_') or path.name.endswith('_test.py') or path.name=='conftest.py'
            category='tests' if is_test else 'non_test'
            try:data=complexity(p.read_text(encoding='utf-8-sig'))
            except (SyntaxError,UnicodeError) as error:
                errors.append(dict(family=family,path=relative,error=str(error)));continue
            files.append(dict(family=family,revision=revision,path=relative,category=category,sha256=expected,sloc=data['sloc'],function_count=len(data['functions'])))
            for f in data['functions']:
                functions.append(dict(family=family,path=relative,category=category,name=f['name'],line=f['line'],cc=f['cc'],cc_without_asserts=f['cc_without_asserts']))
    def summarize(selected):
        return dict(functions=len(selected),cc=stats([f['cc'] for f in selected]),cc_without_asserts=stats([f['cc_without_asserts'] for f in selected]))
    repo={}
    for family in sorted(families):
        repo[family]={category:summarize([f for f in functions if f['family']==family and f['category']==category]) for category in ('non_test','tests')}
        repo[family]['file_counts']=dict(Counter(f['category'] for f in files if f['family']==family))
    report=dict(scope='11 active source families only. Original pinned upstream snapshots; excludes authored reference overlays and generated dataset tests. Non-test includes application code plus scripts/examples/benchmarks, not exclusively production core.',
        method='Radon CC per function, method and nested closure; no class aggregate blocks. Population std. Pooled values weight functions equally, not repositories. Files with no functions do not contribute function CC.',
        radon_version=importlib.metadata.version('radon'),repo=repo,
        pooled={category:summarize([f for f in functions if f['category']==category]) for category in ('non_test','tests')},
        all_original_python=summarize(functions),source_file_counts=dict(Counter(f['category'] for f in files)),
        errors=errors,top_non_test_functions=sorted([f for f in functions if f['category']=='non_test'],key=lambda f:f['cc'],reverse=True)[:20],
        source_body_exported=False,training_inputs_changed=False)
    out.mkdir()
    for name,value in [('summary.json',report),('file-metadata.json',files),('function-metrics.json',functions)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    lines=['# Original source cyclomatic complexity','','Original pinned source repositories backing the active dataset. No implementation bodies were exported or used for training. Non-test includes scripts, examples and benchmarks. CC is measured per function/method/closure; class aggregates are excluded. Standard deviation is population std.','', '| Repository | Non-test files | Functions | CC mean | CC std | Median | Max |','|---|---:|---:|---:|---:|---:|---:|']
    for family,value in repo.items():
        s=value['non_test']['cc'];lines.append(f"| {family} | {value['file_counts'].get('non_test',0)} | {s['n']} | {s.get('mean',0):.2f} | {s.get('std_population',0):.2f} | {s.get('median',0):g} | {s.get('max',0)} |")
    s=report['pooled']['non_test']['cc'];a=report['pooled']['non_test']['cc_without_asserts'];t=report['pooled']['tests']['cc']
    lines+=['',f"Pooled non-test source: {s['n']} functions, mean **{s['mean']:.2f}**, std **{s['std_population']:.2f}**, median {s['median']:g}, max {s['max']}.",f"With assertions excluded: mean {a['mean']:.2f}, std {a['std_population']:.2f}.",f"Original repository tests, separately: {t['n']} functions, mean {t['mean']:.2f}, std {t['std_population']:.2f}.",'',f"Skipped/missing/unparseable files: {len(errors)}. See summary.json for details.",'','Large functions and skew make mean/std alone incomplete. This describes code structure, not correctness, maintainability by itself, or the complexity of each requirement. Module-level code outside functions is not part of function CC. The two historical reserved evaluation repositories are outside these 11 active source families.','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    print('\n'.join(lines))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='original-source-complexity-v02')
    main(parser.parse_args().output)
