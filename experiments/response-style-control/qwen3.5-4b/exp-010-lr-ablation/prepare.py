"""Freeze an LR-only child recipe and reuse byte-identical tokenized data."""
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'exp-009-minimal-edit'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write(path,data):
    if path.exists() and path.read_bytes()!=data:
        raise ValueError('Refusing to replace frozen artifact: '+str(path))
    path.write_bytes(data)

def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def main():
    original=json.loads((PARENT/'training-preflight-v1/training-config.json').read_text(encoding='utf-8'))
    config=copy.deepcopy(original)
    config['experiment_id']='exp-010-lr-ablation'
    config['parent']='exp-009-minimal-edit'
    config['status']='prepared-not-trained'
    config['training']['learning_rate']=1e-4
    # Parent config predates the explicit user override: no vLLM for adapter inference.
    config['inference']['backend']='unsloth-transformers'
    config['notes']=[
        'Only training change versus exp009: LR 5e-5 to 1e-4; two epochs and 20 steps retained.',
        'Fresh pinned base; never initialize from any historical or diagnostic adapter.',
        'Shared train_reviewed.py resolves dataset paths against its exp009 directory; identical reviewed-v2 data reused by hash.',
        'Final-assistant-only loss, context and padding masked, native EOS supervised; zero truncation.',
        'Inference matches actual exp009 adapter backend, greedy repetition penalty 1.05, no extra system prompt.',
        'Twenty validation items are development data, not a fresh independent test; never contribute gradients.',
        'Reject exp009 based on user qualitative review; underfitting remains a hypothesis, not a proven diagnosis.'
    ]
    difference=[k for k in original['training'] if original['training'][k]!=config['training'][k]]
    assert difference==['learning_rate']
    assert config['model']==original['model'] and config['dataset']==original['dataset']
    for split in ('train','validation'):
        source=PARENT/config['dataset'][split]
        assert digest(source.read_bytes())==config['dataset']['hashes'][split+'-reviewed.jsonl']
    report=json.loads((PARENT/'training-preflight-v1/report.json').read_text(encoding='utf-8'))
    output=HERE/'training-preflight-v1'
    output.mkdir(exist_ok=True)
    for name,expected in report['files'].items():
        data=(PARENT/'training-preflight-v1'/name).read_bytes()
        assert digest(data)==expected
        write(output/name,data)
    write(output/'report.json',encoded(report))
    write(output/'training-config.json',encoded(config))
    # JSON is also valid YAML; keep the complete canonical config self-contained.
    write(HERE/'config.yaml',encoded(config))
    comparison=dict(status='local-preparation-passed',training_changes=difference,
        old_learning_rate=original['training']['learning_rate'],new_learning_rate=config['training']['learning_rate'],
        unchanged_model=True,unchanged_dataset=True,unchanged_tokenized_data=True,
        train_rows=80,validation_rows=20,config_sha256=digest(encoded(config)),
        parent_config_sha256=digest((PARENT/'training-preflight-v1/training-config.json').read_bytes()),
        gpu_execution='not-started; new GPU gates required')
    write(HERE/'preparation-report.json',encoded(comparison))
    print(json.dumps(comparison,indent=2))

if __name__=='__main__':
    main()
