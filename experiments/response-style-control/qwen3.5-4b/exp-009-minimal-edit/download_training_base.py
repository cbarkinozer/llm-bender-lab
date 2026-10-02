"""Download only the pinned public base checkpoint to persistent HF cache."""
from huggingface_hub import snapshot_download
path=snapshot_download('unsloth/Qwen3.5-4B',revision='3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636',
    allow_patterns=['*.json','*.jinja','*.safetensors','*.model','*.txt'],max_workers=4)
print('Pinned base ready:',path)
