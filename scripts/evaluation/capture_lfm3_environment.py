"""Sanitized runtime snapshot; never dump the complete process environment."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    import torch
    assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    data=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
        packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
        cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),gpu=torch.cuda.get_device_name(),
        nvidia_smi=subprocess.check_output(['nvidia-smi','-q'],text=True),
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        cudnn_deterministic=torch.backends.cudnn.deterministic,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        float32_matmul_precision=torch.get_float32_matmul_precision(),
        allow_tf32_matmul=torch.backends.cuda.matmul.allow_tf32,
        environment={k:os.environ.get(k) for k in ('HF_HOME','CUDA_VISIBLE_DEVICES','CUBLAS_WORKSPACE_CONFIG',
            'PYTHONHASHSEED','TOKENIZERS_PARALLELISM','VLLM_ATTENTION_BACKEND','UV_CACHE_DIR')})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2)+'\n')
    a.output.with_suffix('.freeze.txt').write_bytes(subprocess.check_output([sys.executable,'-m','pip','freeze']))
    print('CUDA/BF16 verified; sanitized environment saved',flush=True)


if __name__=='__main__':
    main()
