"""Audit real microbatch exposure, arm ordering and accumulation normalization."""
import argparse
from collections import Counter,defaultdict
from pathlib import Path
from active_tdd_data import EXP,rows,read_json
from prepare_tdd_demo import save,digest


def audit(root,output):
    reports={};orders={}
    for arm in ('A','B'):
        preflight=EXP/'paired-preflight-v02'/arm
        records=rows(preflight/'train-encoded.jsonl')
        signatures={(len(r['input_ids']),sum(x!=-100 for x in r['labels'])):r['record_id'] for r in records}
        if len(signatures)!=50:raise ValueError('Exposure signatures are not unique; cannot infer order')
        run=root/(arm+'-full');exposure=rows(run/'exposure.jsonl');normalization=rows(run/'loss-normalization.jsonl')
        if len(exposure)!=150 or len(normalization)!=150:raise ValueError('Expected150 training microbatches')
        order=[signatures[(r['input_tokens'],r['supervised_tokens'])] for r in exposure]
        if Counter(order)!=Counter({r['record_id']:3 for r in records}):raise ValueError('Not exactly3 passes over all50 rows')
        totals=defaultdict(int)
        for r in exposure:totals[r['step']]+=r['supervised_tokens']
        if sorted(totals)!=list(range(21)):raise ValueError('Unexpected optimizer-step exposure')
        for actual,loss in zip(exposure,normalization):
            if loss['accumulation_group_tokens']!=totals[actual['step']] or loss['microbatch_tokens']!=actual['supervised_tokens']:
                raise ValueError('Actual loss denominator does not match optimizer-group tokens')
        result=read_json(run/'result.json')
        if result['recipe_sha256']!=digest(preflight/'recipe.json') or result['metrics']['epoch']!=3:
            raise ValueError('Run recipe/epoch mismatch')
        reports[arm]=dict(microbatches=150,optimizer_steps=21,input_tokens=sum(r['input_tokens'] for r in exposure),
                         supervised_tokens=sum(r['supervised_tokens'] for r in exposure),every_row_seen_three_times=True,
                         actual_token_denominators_verified=True,metrics=result['metrics'],
                         gpu_peak_allocated_bytes=result.get('gpu_peak_allocated_bytes'))
        orders[arm]=order
    if orders['A']!=orders['B']:raise ValueError('Arms used different actual example orders')
    if reports['A']['input_tokens']!=275574 or reports['A']['supervised_tokens']!=51798 or reports['B']['supervised_tokens']!=47541:
        raise ValueError('Unexpected actual exposure totals')
    save(output,dict(status='passed',arms=reports,actual_training_order_identical=True,
         order_recovery='Each arm has50 unique (input length, supervised count) signatures, mapped to record IDs; no ambiguous lookup',
         actual_record_order=orders['A'],loss_normalization='Per optimizer-group nonignored shifted-token count verified on every microbatch',
         limitation='Different rationale supervision/exposure remains intentional; these checks do not establish better test quality.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.run_root,a.output)
