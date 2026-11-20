"""Render measured routing results while preserving the published comparison."""
import json
from pathlib import Path

def main():
    r=Path('/workspace/reflex-wsp')
    def load(path):
        p=r/path
        return json.loads(p.read_text()) if p.exists() else None
    native={arm:load(f'eval/routing/{arm}/summary.json') for arm in ['parent','wsp','released','candidate']}
    phone={arm:load(f'eval/phone-generative/{arm}/summary.json') for arm in ['parent','wsp']}
    rows=[('MOBILE_ROUTING9','MOBILE_ROUTING9','180 / 180',54.44,91.11,47.22),
          ('typed-decisions','typed_decisions','400 / 2000',34.10,60.70,36.30),
          ('BANKING77','BANKING77','462 / 462',8.44,74.89,36.36),
          ('CLINC150','CLINC150','450 / 450',4.44,81.11,55.33)]
    text=['# Reflex WSP routing comparison','',
          '## Published reference (unchanged)','',
          '| Benchmark | Cases / decisions | Base Qwen3.5-0.8B | Reflex-1 | Laya English |',
          '|---|---:|---:|---:|---:|']
    for name,key,count,b,f,l in rows:text.append(f'| {name} | {count} | {b:.2f} | {f:.2f} | {l:.2f} |')
    text+=['','## Current measurements','',
        '| Benchmark | Cases / decisions | Qwen parent | WSP base | Released Reflex-1 | WSP Reflex-1.5 candidate |',
        '|---|---:|---:|---:|---:|---:|']
    for name,key,count,*_ in rows:
        values=[]
        for arm in ['parent','wsp','released','candidate']:
            data=phone[arm] if key=='MOBILE_ROUTING9' and arm in phone else ((native[arm] or {}).get(key) or {}).get('metrics')
            values.append(f"{100*data['accuracy']:.2f}" if data else 'pending')
        text.append(f'| {name} | {count} | '+' | '.join(values)+' |')
    text+=['',
        'All current runs use the exact frozen published cohorts. Phone parent/WSP use a matched BF16 GPU schema-based non-thinking JSON router, so their scores must be compared with each other; they are a distinct profile from the historical A32 raw-HTTP base router. Released/candidate phone runs use native 4-bit decision-head inference. General parent/WSP runs use identically seeded fresh decision heads, matching the published general reference profile; these are not generative zero-shot classification scores. Adapter runs restore trained heads. Historical Laya and A32 latency are not remeasured here.',
        '',
        'Training/checkpoint choice uses recovered training/validation/calibration splits only. Test cohorts never select checkpoints or calibration. A candidate designation is not a release or an improvement claim. Raw per-decision logits/predictions, source hashes, precision and runner manifests accompany each run.']
    (r/'routing-comparison.md').write_text('\n'.join(text)+'\n')
    print('\n'.join(text))

if __name__=='__main__':main()
