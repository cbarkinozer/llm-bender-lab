"""Local anonymous three-way review; private identities never enter reviewer files."""
import argparse
from pathlib import Path
import random
from active_tdd_data import EXP,rows
from prepare_tdd_demo import save,lines,digest
from review_tdd_demo_outputs import verify_generation_pair,extract_test,semantic_review_code


def build(base,arm_a,arm_b,out,requests):
    if out.exists():raise ValueError('Preserve existing blind review')
    verify_generation_pair(base,arm_a);verify_generation_pair(base,arm_b)
    records={name:{r['record_id']:r for r in rows(path)} for name,path in [('base',base),('arm_A',arm_a),('arm_B',arm_b)]}
    expected={r['record_id'] for r in rows(requests)}
    if any(set(data)!=expected for data in records.values()):raise ValueError('Request set mismatch')
    rng=random.Random(90217);packet=[];support=[];private=[];accounting=[]
    reviewer=out/'for-reviewer';reviewer.mkdir(parents=True)
    for request in rows(requests):
        identity=['base','arm_A','arm_B'];rng.shuffle(identity)
        candidates={};mapping={}
        for label,name in zip(('X','Y','Z'),identity):
            row=records[name][request['record_id']];mapping[label]=name
            if request['capability']=='task-to-tests':
                code=semantic_review_code(row);candidates[label]=code or '[No complete parseable test file available]'
                accounting.append(dict(record_id=row['record_id'],source=name,strict_status=extract_test(row)['status'],semantic_code_available=bool(code),tokens=len(row['token_ids'])))
            else:
                candidates[label]=row['text'].split('</think>',1)[-1].strip() if row['finish_reason']!='length' else '[Incomplete output]'
        item=dict(case_id=request['record_id'],requirement=request['messages'][1]['content'],candidates=candidates,
                  judgment=dict(rank_or_tie_groups=[],evidence_by_candidate={},critical_defects={},reviewer_notes=''))
        (packet if request['capability']=='task-to-tests' else support).append(item)
        private.append(dict(case_id=request['record_id'],mapping=mapping))
    lines(reviewer/'primary-tests.jsonl',packet);lines(reviewer/'supporting-probes.jsonl',support)
    (reviewer/'INSTRUCTIONS.txt').write_text('Compare X/Y/Z against the supplied requirement. Rationale is hidden. Rank with ties allowed, e.g. [["X"],["Y","Z"]]. Both/all unusable is valid; explain with code evidence. Judge correctness, requirement coverage, assertion strength, controls and mocks. A complete code block is shown even if its filename header failed strict usability; format/completion is accounted separately. Do not infer quality from length alone. Supporting probes are a separate capability analysis. Record reviewer identity, AI assistance and independence from dataset authors. Never consult private mapping or source labels during grading.\n',encoding='utf-8')
    save(out/'PRIVATE-identities.json',dict(seed=90217,mapping=private))
    save(out/'PRIVATE-accounting.json',accounting)
    save(out/'provenance.json',dict(base_sha256=digest(base),arm_A_sha256=digest(arm_a),arm_B_sha256=digest(arm_b),
         requests_sha256=digest(requests),primary_cases=len(packet),supporting_cases=len(support),graded=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('base','arm-a','arm-b','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--requests',type=Path,default=EXP/'paired-preflight-v02/A/development-requests.jsonl')
    a=p.parse_args();build(a.base,a.arm_a,a.arm_b,a.output,a.requests)
