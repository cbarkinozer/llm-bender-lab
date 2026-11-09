"""Build fresh anonymous LR comparison and static diagnostics; execute no tests."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import re
from active_tdd_data import rows,read_json
from prepare_tdd_demo import save,lines,digest
from review_tdd_demo_outputs import verify_generation_pair,extract_test,semantic_review_code
from summarize_tdd_demo_review import load_paper_tools,static_analysis


def report(root,requests,destination,paper_repo):
    if destination.exists():raise ValueError('Preserve previous reports')
    sources={'base':root/'base/outputs.jsonl','Exp3':root/'Exp3-candidate/outputs.jsonl',
             'Exp4':root/'Exp4-candidate/outputs.jsonl'}
    if (root/'historical-A-candidate/outputs.jsonl').exists():
        sources['historical_A']=root/'historical-A-candidate/outputs.jsonl'
    for name,path in sources.items():
        if name!='base':verify_generation_pair(sources['base'],path)
    request_rows=rows(requests);expected={r['record_id'] for r in request_rows}
    data={name:{r['record_id']:r for r in rows(path)} for name,path in sources.items()}
    if any(set(r)!=expected for r in data.values()):raise ValueError('Missing response IDs')
    destination.mkdir();reviewer=destination/'for-reviewer';reviewer.mkdir()
    paper,provenance=load_paper_tools(paper_repo)
    rng=random.Random(250731);primary=[];support=[];mapping=[];diagnostics=[]
    labels=list('WXYZ') if len(sources)==4 else list('XYZ')
    for request in request_rows:
        rid=request['record_id'];order=list(sources);rng.shuffle(order)
        candidates={};identities={}
        for label,name in zip(labels,order):
            row=data[name][rid];identities[label]=name
            if request['capability']=='task-to-tests':
                code=semantic_review_code(row)
                candidates[label]=code or '[No complete parseable test file available]'
                analysis=static_analysis(dict(case_id=rid,candidates={label:candidates[label]}),label,paper)
                parsed=extract_test(row)
                wanted=re.search(r'^Target file:\s*(\S+)',request['messages'][1]['content'],re.M).group(1)
                diagnostics.append(dict(model=name,record_id=rid,strict_status=parsed['status'],
                    target_path_matches=parsed.get('path')==wanted,analysis=analysis))
            else:
                candidates[label]=row['text'].split('</think>',1)[-1].strip() if row['finish_reason']!='length' else '[Incomplete output]'
        item=dict(case_id=rid,requirement=request['messages'][1]['content'],candidates=candidates,
                  judgment=dict(rank_or_tie_groups=[],assessment_by_candidate={},evidence_by_candidate={},reviewer_notes=''))
        (primary if request['capability']=='task-to-tests' else support).append(item)
        mapping.append(dict(case_id=rid,mapping=identities))
    lines(reviewer/'primary-tests.jsonl',primary);lines(reviewer/'supporting-probes.jsonl',support)
    text=[]
    for item in primary:
        text.append('CASE '+item['case_id']+'\n\n'+item['requirement'])
        for label,code in item['candidates'].items():text.append('CANDIDATE '+label+'\n\n'+code)
    (reviewer/'primary-tests.txt').write_text('\n\n----\n\n'.join(text)+'\n',encoding='utf-8',newline='\n')
    (reviewer/'INSTRUCTIONS.txt').write_text(
        'Judge each candidate against the complete supplied contract. Thinking is hidden. Rank with ties allowed; all unusable is a valid conclusion. '
        'For each candidate use retain/repair/reject/uncertain and explain concrete code evidence, requirement coverage, oracle correctness and meaningful controls. '
        'Do not infer quality from length, smell counts or apparent assertion specificity. Do not inspect private mappings or diagnostics. '
        'This is adaptively clarified development after inspecting earlier outputs, not fresh holdout evidence. Record reviewer identity, AI assistance, and prior exposure. '
        'Supporting probes are optional and separate. No per-assertion human annotation is required for this demo.\n',encoding='utf-8')
    save(destination/'PRIVATE-identities.json',dict(seed=250731,mapping=mapping))
    save(destination/'PRIVATE-static-diagnostics.json',dict(detector=provenance,records=diagnostics,
        limitation='Static unvalidated screening only. Specific assertions can be incorrect. Necessary state transitions/constants are not automatically defects. No generated code executed.'))
    summary={}
    for name,records in data.items():
        values=list(records.values());primary_rows=[r for r in values if r['capability']=='task-to-tests']
        statuses=Counter(extract_test(r)['status'] for r in primary_rows)
        stop_ids=read_json(sources[name].parent/'generation-settings.json')['verified_stop_token_ids']
        term=[]
        for row in values:
            ids=row['token_ids'];periods=[]
            for width in range(1,min(128,len(ids)//4)+1):
                block=ids[-width:]
                if ids[-4*width:]==block*4:periods.append(width)
            term.append(dict(record_id=row['record_id'],finish_reason=row['finish_reason'],stop_reason=row.get('stop_reason'),
                tokens=len(ids),thinking_closed=row['text'].count('</think>')==1,
                native_stop_verified=row['finish_reason']=='stop' and bool(ids) and (ids[-1] in stop_ids or row.get('stop_reason') in stop_ids),
                repeated_suffix_periods=periods,heuristic_only=True))
        execution=read_json(root/(name+'-execution')/'summary.json')
        partial=[]
        for case in execution['records']:
            reference=root/(name+'-execution')/case['record_id']/'reference.json'
            if reference.exists():
                raw=read_json(reference);reports=raw.get('reports',[])
                partial.append(dict(record_id=case['record_id'],collected=len(raw.get('order',[])),
                    call_passes=sum(r['when']=='call' and r['outcome']=='passed' for r in reports),
                    call_failures=sum(r['when']=='call' and r['outcome']=='failed' for r in reports),
                    returncode=raw.get('returncode'),suite_pass=case['reference_pass']))
            else:partial.append(dict(record_id=case['record_id'],not_executed=case['status']))
        summary[name]=dict(responses=len(values),total_output_tokens=sum(len(r['token_ids']) for r in values),
            primary_output_tokens=sum(len(r['token_ids']) for r in primary_rows),primary_format_status=dict(statuses),
            reference_passes=execution['reference_passes'],useful_tasks=execution['useful_tasks'],
            kills=execution['kills'],faults=execution['faults'],termination=term,partial_reference_diagnostics=partial,
            partial_diagnostic_caveat='Exploratory only; partial passes do not rescue a failing suite or earn mutant credit.')
    save(destination/'summary.json',dict(models=summary,requests_sha256=digest(requests),
        output_hashes={k:digest(v) for k,v in sources.items()},review_submitted=False,
        scope='Five adaptively clarified development tasks from one family; one seed. Counts descriptive, not population estimates. No holdout inference.'))
    print(json.dumps({k:{n:v[n] for n in ['reference_passes','kills','faults','total_output_tokens']} for k,v in summary.items()}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['run-root','requests','output','paper-repo']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();report(a.run_root,a.requests,a.output,a.paper_repo)
