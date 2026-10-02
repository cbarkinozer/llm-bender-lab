"""Reload saved smoke adapter against pinned base; verify a finite masked loss."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--adapter',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--export-merged',action='store_true',help='Optional, only when explicitly requested')
    args=p.parse_args()
    if args.output_dir.exists():
        raise ValueError('Refusing overwrite')
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    model,processor=FastLanguageModel.from_pretrained(model_name='unsloth/Qwen3.5-4B',revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636',max_seq_length=1024,load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    adapted=PeftModel.from_pretrained(model,str(args.adapter),is_trainable=False)
    assert any('lora_' in name for name,_ in adapted.named_parameters())
    from transformers import AutoTokenizer
    from prepare_training import HERE, encode_final
    tokenizer=AutoTokenizer.from_pretrained('unsloth/Qwen3.5-4B',revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636')
    row=json.loads((HERE/'reviewed-v2/train-reviewed.jsonl').read_text(encoding='utf-8').splitlines()[0])
    encoded,_,_=encode_final(tokenizer,row)
    adapted.eval()
    device=next(adapted.parameters()).device
    with torch.no_grad():
        result=adapted(**{k:torch.tensor([v],device=device) for k,v in encoded.items()})
    loss=float(result.loss)
    import math
    assert math.isfinite(loss)
    args.output_dir.mkdir()
    if args.export_merged:
        merged=adapted.merge_and_unload()
        merged.save_pretrained(args.output_dir/'merged',safe_serialization=True,max_shard_size='4GB')
        processor.save_pretrained(args.output_dir/'merged')
    (args.output_dir/'reload-manifest.json').write_text(json.dumps(dict(status='adapter-reloaded',source_adapter=str(args.adapter),base_revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636',finite_forward_loss=loss,merged_export=args.export_merged,generation_test='not-required-at-this-stage'),indent=2)+'\n')
    print('Reloaded adapter; finite masked forward loss:',loss)

if __name__=='__main__':
    main()
