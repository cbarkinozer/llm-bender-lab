"""Freeze matched parent and retention-data ablations before GPU execution."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
RUN=BASE/'preservation-session-v01-local'
DATA=BASE/'capability-preservation-v01'
sys.path.insert(0,str(ROOT/'scripts/training'))
from run_lfm3_bilingual_pilot import render

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]

def main():
    from tokenizers import Tokenizer
    assert not (RUN/'freeze.json').exists(),'Never overwrite a frozen session'
    cfg=read(BASE/'exp-011-bilingual-sft640/config.yaml')
    original=rows(ROOT/cfg['dataset']['train_file'])
    assert len(original)==640 and sha(ROOT/cfg['dataset']['train_file'])==cfg['dataset']['train_sha256']
    supplement=rows(DATA/'train.jsonl')
    combined=original+supplement
    (DATA/'combined-train.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in combined),encoding='utf-8')
    tok=Tokenizer.from_file(str(BASE/'bilingual-runtime-local/native/exp-011-bilingual-sft640/tokenizer/tokenizer.json'))
    lengths=[];supervised=[]
    for r in combined:
        prefix,full=render(r['messages'],r['worked_solution'])
        ids=tok.encode(full,add_special_tokens=False).ids;pids=tok.encode(prefix,add_special_tokens=False).ids
        assert ids[:len(pids)]==pids and len(ids)<=4096
        lengths.append(len(ids));supervised.append(len(ids)-len(pids))
    oldorder=read(ROOT/cfg['dataset']['data_order_file'])['order_b']
    assert len(oldorder)==904 and sum(supervised[i] for i in oldorder)==209811
    # Short retention targets contribute few tokens. Replace two short rows per
    # update (25% row slots), then adjust one original row's length to preserve
    # the per-update supervised-token budget. This is a composition/reweighting
    # pilot, not 20% retention tokens or an unchanged-original-exposure claim.
    rng=random.Random(3407);order=[];counts={'supplement':0,'original':0}
    original_pool=list(range(640));supp_pool=list(range(640,len(combined)))
    rng.shuffle(original_pool);rng.shuffle(supp_pool)
    oldorder=read(ROOT/cfg['dataset']['data_order_file'])['order_b']
    target=sum(supervised[i] for i in oldorder);supp_exposure=0;exposure=0;cursor=0
    for step in range(113):
        block=oldorder[step*8:(step+1)*8].copy()
        replacements=sorted(range(8),key=lambda j:supervised[block[j]])[:2]
        desired=sum(supervised[i] for i in block)
        for slot in replacements:
            choice=supp_pool[cursor%len(supp_pool)];cursor+=1
            block[slot]=choice;supp_exposure+=supervised[choice]
        adjust=max((j for j in range(8) if j not in replacements),key=lambda j:supervised[block[j]])
        ideal=supervised[block[adjust]]+desired-sum(supervised[i] for i in block)
        block[adjust]=min(original_pool,key=lambda i:abs(supervised[i]-ideal))
        order.extend(block);exposure+=sum(supervised[i] for i in block)
    counts={'supplement':cursor,'original':len(order)-cursor}
    assert abs(exposure/target-1)<.01,(exposure,target)
    early_a=sum(supervised[i] for i in oldorder[:69*8]);early_b=sum(supervised[i] for i in order[:69*8])
    assert abs(early_b/early_a-1)<.01,(early_a,early_b)
    dump(DATA/'matched-order.json',dict(order_b=order,seed=3407,supervised_total=exposure,
        reference_total=target,primary_step69_tokens=early_b,reference_step69_tokens=early_a,
        supplemental_tokens=supp_exposure,supplemental_fraction=supp_exposure/exposure,
        sampled_rows=counts,unique_original_rows=len(set(order)&set(original_pool)),unique_supplement_rows=len(set(order)&set(supp_pool))))
    dump(DATA/'token-audit.json',dict(rows=len(combined),max_length=max(lengths),truncated_rows=0,
        supervised_lengths=supervised,total_lengths=lengths))
    experiments=['exp-012-base-bilingual','exp-013-base-preservation']
    for index,exp in enumerate(experiments):
        c=copy.deepcopy(cfg);c['status']='frozen-before-training'
        c['model'].update(repo='LiquidAI/LFM3-1.7B',revision=c['model']['parent_revision'],
            load_policy='Original pinned BF16 base; independent fresh LoRA. NO CPT merge for new training.')
        if index:
            c['dataset'].update(train_file=(DATA/'combined-train.jsonl').relative_to(ROOT).as_posix(),
                train_sha256=sha(DATA/'combined-train.jsonl'),train_rows=len(combined),
                data_order_file=(DATA/'matched-order.json').relative_to(ROOT).as_posix())
            c['training']['supervised_token_budget']=exposure
        c['dataset'].update(eval_directory=DATA.relative_to(ROOT).as_posix(),eval_manifest_sha256=sha(DATA/'manifest.json'),
            gate='New session native audit + smoke + tiny-overfit + fresh baseline; historical owner data acceptance preserved')
        c['training'].update(runner='scripts/training/run_lfm3_preservation_gpu.py',
            checkpoint_selection='PRIMARY FIXED checkpoint69, preregistered before outputs; checkpoint113 exploratory backup, not selected on fresh holdout')
        c['tracking'].update(group='lfm3-preservation-session-v01',run_name=exp+'-sft-lr1e-4-r32-113step')
        c['experiment'].update(id=exp,parent='exp-011-bilingual-sft640' if index==0 else experiments[0],
            comparison_variable='initialization parent only' if index==0 else '25% row slots retention supplement with one original row reweighted per update to match supervised-token budgets',
            initialization='Independent fresh LoRA on original LiquidAI base',dataset_revision='capability-preservation-v01' if index else 'v01-corrections-02')
        dump(BASE/exp/'config.yaml',c)
        note=f'''# {exp}

Frozen before GPU training. Primary checkpoint69, later113 retained as backup.

Hypothesis: {'original-base initialization avoids CPT-associated capability loss under identical bilingual SFT.' if index==0 else 'a verified arithmetic/reasoning and English retention supplement reduces regressions while maintaining useful Turkish.'}

Parent/control: {c['experiment']['parent']}. Main change: {c['experiment']['comparison_variable']}.
Recipe: LR1e-4, rank32/alpha64, micro2/accum4, 113 steps, cosine, warmup6, BF16.
Both new adapters start independently from original base; no continuation of an SFT adapter.
The historical trainer path name `cpt-merged` is a symlink to original base for these runs; receipt proves identity.

Evaluation: fresh frozen packet on original base and both historical SFT candidates before training, then both new checkpoint69 adapters. Raw outputs and deterministic arithmetic/reference checks, followed by blinded owner preference. Existing consumed evaluation16 is used ONLY for a separate thinking-mode diagnostic.
One seed and small synthetic pilot: no broad no-forgetting or release-quality claim.
Source/provider owner decisions remain as recorded. No publication authorized.
Results and conclusion: pending execution.
'''
        (BASE/exp/'README.md').write_text(note,encoding='utf-8')
    oldpacket=BASE/'bilingual-pilot-v01/eval-v01'
    diagnostic=rows(oldpacket/'symbolic-controls-prompts.jsonl')+[r for r in rows(oldpacket/'eval-prompts.jsonl') if r['category']=='arithmetic' and r['direction']=='tr-tr']
    assert len(diagnostic)==16
    RUN.mkdir(parents=True,exist_ok=True)
    (RUN/'thinking-prompts.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in diagnostic),encoding='utf-8')
    files=list((ROOT/'scripts/training').glob('*.py'))+[ROOT/'scripts/evaluation/run_lfm3_preservation_session.py',ROOT/'scripts/evaluation/evaluate_lfm3_vllm_batched.py',
        BASE/'exp-000-baseline/config-planned.json',BASE/'bilingual-pilot-v01/plan/gates.json',RUN/'thinking-prompts.jsonl',
        DATA/'train.jsonl',DATA/'combined-train.jsonl',DATA/'matched-order.json',DATA/'manifest.json',DATA/'eval-prompts.jsonl',DATA/'token-audit.json',
        ROOT/cfg['dataset']['train_file'],ROOT/cfg['dataset']['data_order_file'],BASE/'NEXT-GPU-AUTHORIZATION.md']
    for exp in experiments:files += [BASE/exp/'config.yaml',BASE/exp/'README.md']
    for exp,step in [('exp-010-tr-only-sft160',60),('exp-011-bilingual-sft640',69)]:
        files += [BASE/exp/'results-local/sft'/f'checkpoint-{step}'/name for name in ['adapter_config.json','adapter_model.safetensors']]
    files=list(dict.fromkeys(files))
    dump(RUN/'freeze.json',dict(status='frozen-before-training-and-new-baseline',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        primary_checkpoint=69,seed=3407,experiments=experiments,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        working_tree_dirty=True,files={p.relative_to(ROOT).as_posix():sha(p) for p in files},
        prior_eval_used_only_for_diagnostic=True,reference_files_stay_local=True,
        retention=dict(total_tokens=exposure,control_tokens=target,step69_tokens=early_b,control_step69_tokens=early_a,supplemental_tokens=supp_exposure)))
    # Historical adapters were transferred in the existing checksummed archive.
    with tarfile.open(RUN/'session-input.tar.gz','w:gz') as t:
        for p in files+[RUN/'freeze.json']:
            if p.suffix!='.safetensors':t.add(p,arcname=p.relative_to(ROOT))
    print(json.dumps(dict(freeze_sha256=sha(RUN/'freeze.json'),bundle_sha256=sha(RUN/'session-input.tar.gz'),
        retention_total=exposure,reference_total=target,early_tokens=[early_a,early_b],supplement_share=supp_exposure/exposure),indent=2))

if __name__=='__main__':main()
