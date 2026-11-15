"""Measure raw content tokens for pinned audit sources; no chat/loss serialization."""
import hashlib
import json
from pathlib import Path
import statistics
from tokenizers import Tokenizer
from audit_turkish_sources import OUT, SOURCES, messages, filehash


def stats(v):
    v=sorted(v)
    return dict(n=len(v),total=sum(v),min=min(v),median=statistics.median(v),
                p90=v[int((len(v)-1)*.9)],p95=v[int((len(v)-1)*.95)],p99=v[int((len(v)-1)*.99)],max=max(v))


def main():
    path=OUT/'raw-local/tokenizer/tokenizer.json'
    expected='7e226e34bface23ccf6e495d157bf77186c1c30a7659880e1a8994db528c3701'
    if filehash(path)!=expected:raise ValueError('Tokenizer differs from independently verified pinned artifact')
    tok=Tokenizer.from_file(str(path));result={}
    for key,(_,_,files) in SOURCES.items():
        inputs=[];answers=[];systems=[];batch=[];system_cache={}
        def consume():
            if not batch:return
            encoded=tok.encode_batch([s for p,a,sy in batch for s in [p,a]],add_special_tokens=False)
            for i,(p,a,sy) in enumerate(batch):
                inputs.append(len(encoded[i*2].ids));answers.append(len(encoded[i*2+1].ids))
                if sy not in system_cache:system_cache[sy]=len(tok.encode(sy,add_special_tokens=False).ids)
                systems.append(system_cache[sy])
            batch.clear()
        for name in files:
            with (OUT/'raw-local'/key/name).open(encoding='utf-8-sig') as f:
                for line in f:
                    ms=messages(json.loads(line))
                    batch.append(tuple('\n'.join(m['content'] for m in ms if m['role']==role) for role in ['user','assistant','system']))
                    if len(batch)>=256:consume()
        consume()
        result[key]=dict(user_content_tokens=stats(inputs),assistant_content_tokens=stats(answers),system_content_tokens=stats(systems),
                        rows_above_4096_raw_content=sum(p+a+s>4096 for p,a,s in zip(inputs,answers,systems)),
                        rows_above_8192_raw_content=sum(p+a+s>8192 for p,a,s in zip(inputs,answers,systems)))
        print(key+': '+str(len(inputs))+' rows measured',flush=True)
    report=dict(tokenizer_repo='LiquidAI/LFM3-1.7B',revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a',
                tokenizer_url='https://huggingface.co/LiquidAI/LFM3-1.7B/resolve/0dc4268b561499c648c7ba7c9466bf3d8d01517a/tokenizer.json',
                tokenizer_sha256=filehash(path),analyzer_sha256=filehash(Path(__file__)),sources=result,
                scope='All rows, user/assistant/system contents separately concatenated by role, add_special_tokens=False. Not native chat serialization, truncation or supervised labels. Occam includes its 20 validation rows in descriptive totals only.')
    (OUT/'raw-token-inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
