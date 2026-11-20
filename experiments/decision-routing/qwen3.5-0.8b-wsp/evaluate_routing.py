"""Frozen routing evaluation with the recovered decision runtime, including raw logits."""
import os
os.environ.update(UNSLOTH_DISABLE_STATISTICS='1', WANDB_MODE='disabled', TOKENIZERS_PARALLELISM='false')
import argparse, collections, hashlib, json, math, time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('arm', choices=['parent','wsp','released','candidate'])
    p.add_argument('--model');p.add_argument('--output');a=p.parse_args()
    root=Path('/workspace/reflex-wsp');models=json.loads((root/'models.json').read_text())
    ckpt=a.model or models[{'parent':'original_training_base','wsp':'wsp_training','released':'released_reflex','candidate':'wsp_training'}[a.arm]]
    if a.arm=='released': ckpt=str(Path(ckpt)/'adapter')
    out=Path(a.output) if a.output else root/'eval/routing'/a.arm
    out.mkdir(parents=True,exist_ok=False)
    from unsloth import FastDecisionModel
    import torch
    from datasets import Dataset
    from transformers import set_seed
    from decision_training_utils import check_build_report
    from unsloth.models.decision import _decision_logits, _metrics, _served_temperatures
    set_seed(3407);started=time.time()
    model,tok=FastDecisionModel.from_pretrained(model_name=ckpt,max_seq_length=4096,dtype=None,load_in_4bit=True)
    FastDecisionModel.for_inference(model)
    audit={}
    for name,param in model.named_parameters():
        if any(f'layers.{i}.mlp.down_proj.weight' in name for i in [15,19]):
            from bitsandbytes.functional import dequantize_4bit
            value=dequantize_4bit(param.data,param.quant_state).cpu().contiguous()
            audit[name]={'packed_sha256':hashlib.sha256(param.data.cpu().numpy().tobytes()).hexdigest(),
                         'dequantized_sha256':hashlib.sha256(value.view(torch.uint8).numpy().tobytes()).hexdigest()}
    manifest={'model':ckpt,'arm':a.arm,'seed':3407,'load_in_4bit':True,'max_seq_length':4096,'batch_size':8,
              'profile':'native decision head; fresh deterministic head for untrained parent/WSP, restored head for adapters',
              'historical_comparability':'Phone historical base used a generative A32 router; fresh-head phone scores are diagnostic only. Historical general fresh-head seed was unspecified.',
              'quantized_weight_audit':audit,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    summary={}
    for name,file,count,decisions in [('MOBILE_ROUTING9','phone180.jsonl',180,180),('typed_decisions','typed_decisions.jsonl',400,2000),('BANKING77','banking77.jsonl',462,462),('CLINC150','clinc150.jsonl',450,450)]:
        path=root/'data/routing-benchmarks'/file;rows=[json.loads(x) for x in path.read_text().splitlines()]
        assert len(rows)==count
        items,report=FastDecisionModel.build_dataset(Dataset.from_list(rows),tok,model)
        check_build_report(items,report,name);assert len(items)==count
        logits,flat=_decision_logits(model,tok,items,8)
        assert len(flat)==decisions
        scales=_served_temperatures(model.decision_config,logits,flat)
        metrics=_metrics(logits,flat,scales)
        assert all(math.isfinite(float(v)) for v in metrics.values())
        records=[]
        for z,item,scale in zip(logits,flat,scales):
            records.append({'id':rows[item['row']].get('id',str(item['row'])),'row':item['row'],
                            'gold_index':item['label'],'prediction_index':int(z.argmax()),'logits':z.tolist(),
                            'probabilities':(z/scale).softmax(-1).tolist(),'qtype':item['qtype']})
        if name!='typed_decisions':
            labels=sorted({r['gold_index'] for r in records});f1=[]
            for label in labels:
                tp=sum(r['gold_index']==label and r['prediction_index']==label for r in records)
                fp=sum(r['gold_index']!=label and r['prediction_index']==label for r in records)
                fn=sum(r['gold_index']==label and r['prediction_index']!=label for r in records)
                f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
            metrics['macro_f1']=sum(f1)/len(f1)
        (out/(name+'.predictions.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in records))
        summary[name]={'rows':count,'decisions':decisions,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'build_report':report,'metrics':metrics,'elapsed_seconds':time.time()-started}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(name,metrics,flush=True)

if __name__=='__main__': main()
