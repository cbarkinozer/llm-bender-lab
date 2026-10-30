"""Download exact public original Occam base/adapter; verify published shard hashes."""
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('HF_HOME','/workspace/.cache/huggingface')
from huggingface_hub import snapshot_download

ROOT=Path('/workspace/occam2-reference')
BASE='unsloth/Qwen3.5-4B'
REVISION='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636'
WEIGHTS={
    'model.safetensors-00001-of-00002.safetensors':'26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61',
    'model.safetensors-00002-of-00002.safetensors':'cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188'}
ADAPTER_REV='1a8a07ff2a29f51a2b6a635a8c219191a7377996'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    assert (ROOT/'environment.json').exists(),'Complete CUDA/import setup before downloading weights'
    base=Path(snapshot_download(BASE,revision=REVISION,local_dir=ROOT/'base',max_workers=4,
        allow_patterns=['*.json','*.jinja','*.txt','*.safetensors','LICENSE']))
    for name,digest in WEIGHTS.items():
        assert sha(base/name)==digest,f'Base identity mismatch:{name}'
        print('Verified',name,flush=True)
    adapter=Path(snapshot_download('cbarkinozer/Qwen3.5-4B-Turkish-Concise-Lora',revision=ADAPTER_REV,
        local_dir=ROOT/'adapter',allow_patterns=['adapter_config.json','adapter_model.safetensors']))
    expected='7ec9b04a5ecac7a031352fb5d0db281ef018c11951a4b4862c418e2b7a002ca1'
    assert sha(adapter/'adapter_model.safetensors')==expected,'Adapter identity mismatch'
    record=dict(base=BASE,base_revision=REVISION,source_weights_sha256=WEIGHTS,
        adapter_revision=ADAPTER_REV,adapter_sha256=expected,
        tokenizer_sha256=sha(base/'tokenizer.json'),template_sha256=sha(base/'chat_template.jinja'))
    (ROOT/'download-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Pinned original base and released adapter downloaded and verified',flush=True)


if __name__=='__main__':main()
