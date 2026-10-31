"""Offline output extraction, blinded paired review and upstream reuse screening."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import random
import re
from active_tdd_data import EXP, read_json, rows
from prepare_tdd_demo import save, lines, digest


def extract_test(output):
    if output['finish_reason']=='length':return dict(status='truncated',code=None)
    text=output['text']
    if text.count('</think>')!=1:return dict(status='missing_or_ambiguous_thinking_boundary',code=None)
    answer=text.split('</think>',1)[1].strip()
    blocks=re.findall(r'```(?:python|py)\s*\n(.*?)```',answer,re.S)
    paths=re.findall(r'^File:\s*(\S+)\s*$',answer,re.M)
    if len(blocks)!=1 or len(paths)!=1:return dict(status='invalid_file_format',code=None)
    path=Path(paths[0])
    if path.is_absolute() or '..' in path.parts or '\\' in paths[0] or ':' in paths[0] or path.suffix!='.py':
        return dict(status='invalid_target_path',code=None)
    try: tree=ast.parse(blocks[0])
    except SyntaxError:return dict(status='syntax_error',code=None)
    tests=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')]
    if not tests:return dict(status='no_test_functions',code=None)
    return dict(status='complete_parseable',code=blocks[0],path=paths[0],test_functions=len(tests))


def functions(code):
    try:tree=ast.parse(code)
    except SyntaxError:return []
    result=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_'):
            name=node.name;node.name='TEST'
            result.append(dict(name=name,ast_sha256=sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()))
            node.name=name
    return result


def shingles(code):
    words=re.findall(r'[A-Za-z_][A-Za-z_0-9]*|\d+|[^\s\w]',code)
    return {sha256(' '.join(words[i:i+8]).encode()).hexdigest() for i in range(max(0,len(words)-7))}


def pair_review(base, candidate, output, requests, seed=7341,left_label='baseline',right_label='candidate'):
    if output.exists():raise ValueError('Preserve prior review')
    left={r['record_id']:r for r in rows(base)};right={r['record_id']:r for r in rows(candidate)}
    expected={r['record_id'] for r in rows(requests)}
    if set(left)!=set(right) or set(left)!=expected:raise ValueError('Missing or different request IDs')
    output.mkdir(parents=True)
    rng=random.Random(seed);packet=[];key=[];status=[]
    for request in rows(requests):
        if request['capability']!='task-to-tests':continue
        rid=request['record_id'];pair=[(left_label,left[rid]),(right_label,right[rid])];rng.shuffle(pair)
        presented={};mapping={}
        for side,(role,row) in zip(('A','B'),pair):
            extracted=extract_test(row)
            presented[side]=extracted['code'] if extracted['code'] is not None else '[No complete parseable test file available]'
            mapping[side]=role
            status.append(dict(record_id=rid,role=role,finish_reason=row['finish_reason'],status=extracted['status']))
        packet.append(dict(pair_id=rid,requirement=request['messages'][1]['content'],tests=presented,
                           grade=dict(preference='A / B / tie / both_unusable',requirement_coverage='',assertion_quality='',
                                      controls_and_mocks='',critical_defects='',evidence='')))
        key.append(dict(pair_id=rid,mapping=mapping))
    lines(output/'review-packet.jsonl',packet)
    save(output/'PRIVATE-pairing-key.json',dict(seed=seed,pairs=key,warning='Keep separate from reviewer packet'))
    save(output/'completion-accounting.json',status)
    save(output/'manifest.json',dict(baseline_sha256=digest(base),candidate_sha256=digest(candidate),
         requests_sha256=digest(requests),pairs=len(packet),rationales_hidden=True,
         instructions='Judge tests against requirements; allow ties. Report all-task usability and completion separately. Completed-pair quality is conditional, not a replacement denominator. Review authorship/independence must be recorded.'))


def overlap(outputs, upstream, destination):
    if destination.exists():raise ValueError('Preserve overlap report')
    audit=next(s for s in read_json(EXP/'external-app-audit.json')['sources'] if s['repository']=='darrenburns/posting')
    source=Path(upstream or audit['local_source']);inventory=[]
    for item in audit['files']:
        if not item['test']:continue
        path=source/item['path']
        if digest(path)!=item['sha256']:raise ValueError('Upstream test pin changed')
        code=path.read_text(encoding='utf-8-sig')
        inventory.append(dict(path=item['path'],sha256=item['sha256'],functions=functions(code),shingles=shingles(code)))
    reports=[]
    for row in rows(outputs):
        # Scope strictly to current development test tasks; do not inspect holdout.
        if not row['record_id'].startswith('posting-'):continue
        parsed=extract_test(row)
        if parsed['code'] is None:
            reports.append(dict(record_id=row['record_id'],status=parsed['status'],matches=[]));continue
        generated=functions(parsed['code']);hashes={f['ast_sha256'] for f in generated};grams=shingles(parsed['code']);matches=[]
        for item in inventory:
            exact=[f['name'] for f in item['functions'] if f['ast_sha256'] in hashes]
            similarity=len(grams&item['shingles'])/len(grams|item['shingles']) if grams|item['shingles'] else 0
            containment=len(grams&item['shingles'])/len(grams) if grams else 0
            if exact or containment>=.5:
                matches.append(dict(path=item['path'],exact_test_function_matches=exact,token_shingle_jaccard=similarity,generated_shingle_containment=containment))
        reports.append(dict(record_id=row['record_id'],status='screened',matches=matches))
    save(destination,dict(repository=audit['repository'],revision=audit['revision'],upstream_test_files=len(inventory),
         outputs_sha256=digest(outputs),reports=reports,
         limitation='Overlap flags require inspection: shared imports/contracts can overlap. No match does not establish absent pretraining exposure. No attribution to memorization from this screen alone. No source text sent to model.'))


def verify_generation_pair(base, candidate):
    left=read_json(base.parent/'result.json');right=read_json(candidate.parent/'result.json')
    if left['stage'] not in ('baseline','candidate') or right['stage']!='candidate':raise ValueError('Expected base/adapter versus adapter')
    identity_key='inference_identity' if 'inference_identity' in left and 'inference_identity' in right else 'recipe_sha256'
    for key in (identity_key,'runtime_lock_sha256'):
        if left[key]!=right[key]:raise ValueError('Generation protocol/runtime mismatch')
    if left['outputs_sha256']!=digest(base) or right['outputs_sha256']!=digest(candidate):raise ValueError('Generation outputs changed')


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    pair=sub.add_parser('pair');pair.add_argument('--baseline',type=Path,required=True);pair.add_argument('--candidate',type=Path,required=True)
    pair.add_argument('--requests',type=Path,default=EXP/'demo-preflight-v03/development-requests.jsonl');pair.add_argument('--output',type=Path,required=True)
    pair.add_argument('--left-label',default='baseline');pair.add_argument('--right-label',default='candidate')
    screen=sub.add_parser('overlap');screen.add_argument('--outputs',type=Path,required=True);screen.add_argument('--upstream',type=Path);screen.add_argument('--output',type=Path,required=True)
    lock=sub.add_parser('lock-runtime');lock.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='pair':
        verify_generation_pair(a.baseline,a.candidate)
        if a.left_label==a.right_label:raise ValueError('Distinct arm labels are required')
        pair_review(a.baseline,a.candidate,a.output,a.requests,left_label=a.left_label,right_label=a.right_label)
    elif a.command=='overlap':overlap(a.outputs,a.upstream,a.output)
    else:
        from run_tdd_demo_gpu import runtime_signature
        if a.output.exists():raise ValueError('Keep frozen runtime lock')
        save(a.output,dict(packages=runtime_signature(),scope='Capture before baseline; use unchanged for candidate. Package identities alone do not guarantee bitwise reproducibility.'))


if __name__=='__main__':main()
