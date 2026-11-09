"""Audit real microbatch exposure, arm ordering and accumulation normalization."""
import argparse
from collections import Counter,defaultdict
from pathlib import Path
from active_tdd_data import EXP,rows,read_json
from prepare_tdd_demo import save,digest


def verify_training_arguments(actual,recipe):
    training=recipe['training']
    mapping={'learning_rate':'learning_rate','num_train_epochs':'epochs',
             'per_device_train_batch_size':'batch_size','gradient_accumulation_steps':'gradient_accumulation_steps',
             'seed':'seed','data_seed':'seed','warmup_steps':'warmup_steps','weight_decay':'weight_decay',
             'max_grad_norm':'max_grad_norm','optim':'optimizer','lr_scheduler_type':'scheduler'}
    for key,source in mapping.items():
        if actual[key]!=training[source]:raise ValueError('Actual training argument differs: '+key)
    if not actual['bf16'] or actual['fp16']:raise ValueError('Actual training precision differs')


def audit(root,output,preflight_root=None,arms=('A','B')):
    reports={};orders={}
    for arm in arms:
        preflight=(preflight_root or EXP/'paired-preflight-v02')/arm
        recipe=read_json(preflight/'recipe.json')
        records=rows(preflight/'train-encoded.jsonl')
        signatures={(len(r['input_ids']),sum(x!=-100 for x in r['labels'])):r['record_id'] for r in records}
        if len(signatures)!=50:raise ValueError('Exposure signatures are not unique; cannot infer order')
        run=root/(arm+'-full');exposure=rows(run/'exposure.jsonl');normalization=rows(run/'loss-normalization.jsonl')
        verify_training_arguments(read_json(run/'training-arguments.json'),recipe)
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
        reports[arm]['actual_training_arguments_verified']=True
        reports[arm]['actual_peak_learning_rate']=recipe['training']['learning_rate']
        orders[arm]=order
        if reports[arm]['input_tokens']!=3*sum(len(r['input_ids']) for r in records) or reports[arm]['supervised_tokens']!=3*recipe['supervised_tokens_per_epoch']:
            raise ValueError('Unexpected actual exposure totals')
    if any(orders[arm]!=orders[arms[0]] for arm in arms):raise ValueError('Arms used different actual example orders')
    save(output,dict(status='passed',arms=reports,actual_training_order_identical=True,
         order_recovery='Each arm has50 unique (input length, supervised count) signatures, mapped to record IDs; no ambiguous lookup',
         actual_record_order=orders[arms[0]],loss_normalization='Per optimizer-group nonignored shifted-token count verified on every microbatch',
         limitation='Exposure verification does not establish better test quality; objectives and learning rates are recorded in the corresponding recipes.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--preflight-root',type=Path);p.add_argument('--arms',nargs=2,default=['A','B'])
    a=p.parse_args();audit(a.run_root,a.output,a.preflight_root,tuple(a.arms))
