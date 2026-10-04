"""Post-recovery config/checkpoint/adapter identity and exact input parity gates."""
import argparse
import json
from pathlib import Path
from archive_pair import sha
from import_comparison import load

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def verify(root):
    assert read(root/'status.json')['status']=='completed'
    arms=load(root)
    result={}
    for arm,count in [('E',80),('F',104)]:
        run=root/arm; sft=run/'sft-v1'
        config=read(sft/'source-config.json'); args=read(sft/'effective-training-arguments.json')
        assert config['dataset']['train_rows']==count and config['dataset']['validation_rows']==20
        assert config['model']['adapter'] is None
        assert args['max_steps']==40 and args['learning_rate']==1e-4 and args['gradient_accumulation_steps']==8
        assert args['per_device_train_batch_size']==1 and args['bf16'] and not args['fp16']
        assert args['seed']==args['data_seed']==3407 and args['save_steps']==args['eval_steps']==10
        state=read(sft/'checkpoints/checkpoint-40/trainer_state.json')
        assert state['global_step']==40
        assert abs(state['epoch']-(4 if arm=='E' else 40/13))<1e-6
        assert read(sft/'result.json')['status']=='completed'
        for step in (30,40):
            for file in ('adapter_model.safetensors','optimizer.pt','scheduler.pt','rng_state.pth','trainer_state.json','training_args.bin'):
                assert (sft/f'checkpoints/checkpoint-{step}'/file).is_file()
        manifest,data=arms[arm]
        assert manifest['adapter_hashes']=={file.name:sha(file) for file in (sft/'adapter').iterdir() if file.is_file()}
        assert all(0<len(r['output_token_ids'])<=4096 and r['output_tokens']==len(r['output_token_ids']) for r in data)
        assert all(r['native_eos']==(r['output_token_ids'][-1] in manifest['eos_token_ids']) for r in data)
        exposure=[json.loads(line) for line in (sft/'training-exposure.jsonl').read_text().splitlines()]
        assert len(exposure)==320 and {r['optimizer_step_before'] for r in exposure}==set(range(40))
        assert read(run/'wandb-summary.json')['state']=='finished'
        assert read(sft/'mask-check.json')['all_rows_verified']
        result[arm]=dict(train_rows=count,global_step=40,epoch=state['epoch'],final_adapter_identity_verified=True,
            native_eos=manifest['native_eos_count'],microbatches=len(exposure),
            actual_supervised_tokens=sum(r['supervised_tokens'] for r in exposure),
            actual_input_tokens=sum(r['input_tokens'] for r in exposure),wandb_state='finished')
    return dict(status='recovered-training-and-inference-verified-human-semantic-review-pending',arms=result,
        evaluation_count=32,models=['base','C','E','F'],prompt_parity=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--results-root',type=Path,required=True); a=p.parse_args()
    result=verify(a.results_root)
    path=a.results_root/'post-recovery-verification.json'
    assert not path.exists(),'Refusing overwrite'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':
    main()
