"""Reload saved smoke adapter against pinned base and export a vLLM checkpoint."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--adapter',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    if args.output_dir.exists():
        raise ValueError('Refusing overwrite')
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    model,processor=FastLanguageModel.from_pretrained(model_name='unsloth/Qwen3.5-4B',revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636',max_seq_length=1024,load_in_4bit=False,load_in_16bit=True,full_finetuning=False)
    adapted=PeftModel.from_pretrained(model,str(args.adapter),is_trainable=False)
    assert any('lora_' in name for name,_ in adapted.named_parameters())
    merged=adapted.merge_and_unload()
    merged.save_pretrained(args.output_dir,safe_serialization=True,max_shard_size='4GB')
    processor.save_pretrained(args.output_dir)
    (args.output_dir/'reload-manifest.json').write_text(json.dumps(dict(status='adapter-reloaded-and-merged',source_adapter=str(args.adapter),base_revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636',generation_test='pending-vllm'),indent=2)+'\n')
    print('Reloaded adapter and exported vLLM smoke checkpoint')

if __name__=='__main__':
    main()
