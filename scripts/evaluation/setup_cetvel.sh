#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
external_root="${LLM_BENDER_EXTERNAL_ROOT:-${repo_root}/.cache/external}"
cetvel_dir="${external_root}/cetvel"
venv_dir="${CETVEL_VENV:-/workspace/.venvs/cetvel}"
cetvel_revision="6119c517e06cce23aaeac103ce3504c9380655e3"
nonthinking_patch="${repo_root}/patches/cetvel-harness-qwen35-nonthinking.patch"
chat_template_cache_patch="${repo_root}/patches/cetvel-harness-chat-template-cache.patch"
dataset_ids_patch="${repo_root}/patches/cetvel-canonical-dataset-ids.patch"
harness_dataset_ids_patch="${repo_root}/patches/cetvel-harness-canonical-dataset-ids.patch"

mkdir -p "${external_root}"

if [[ ! -d "${cetvel_dir}/.git" ]]; then
  git clone https://github.com/KUIS-AI/cetvel.git "${cetvel_dir}"
fi

git -C "${cetvel_dir}" fetch origin "${cetvel_revision}"
git -C "${cetvel_dir}" checkout --detach "${cetvel_revision}"
git -C "${cetvel_dir}" submodule update --init

if git -C "${cetvel_dir}/lm-evaluation-harness" apply --reverse --check "${nonthinking_patch}" 2>/dev/null; then
  echo "Non-thinking chat-template patch is already applied."
else
  git -C "${cetvel_dir}/lm-evaluation-harness" apply --check "${nonthinking_patch}"
  git -C "${cetvel_dir}/lm-evaluation-harness" apply "${nonthinking_patch}"
fi

if git -C "${cetvel_dir}/lm-evaluation-harness" apply --reverse --check "${chat_template_cache_patch}" 2>/dev/null; then
  echo "Chat-template cache compatibility patch is already applied."
else
  git -C "${cetvel_dir}/lm-evaluation-harness" apply --check "${chat_template_cache_patch}"
  git -C "${cetvel_dir}/lm-evaluation-harness" apply "${chat_template_cache_patch}"
fi

if git -C "${cetvel_dir}" apply --reverse --check "${dataset_ids_patch}" 2>/dev/null; then
  echo "Canonical dataset-ID patch is already applied."
else
  git -C "${cetvel_dir}" apply --check "${dataset_ids_patch}"
  git -C "${cetvel_dir}" apply "${dataset_ids_patch}"
fi

# lm-evaluation-harness ships its own built-in xnli/xnli_tr task (group
# "xnli") that collides by name with CETVEL's custom nli_tr/xnli_tr (group
# "nli_tr"). The built-in one is what actually resolves and still has the
# bare, pre-huggingface_hub-hardening "xnli" dataset_path.
if git -C "${cetvel_dir}/lm-evaluation-harness" apply --reverse --check "${harness_dataset_ids_patch}" 2>/dev/null; then
  echo "Harness canonical dataset-ID patch is already applied."
else
  git -C "${cetvel_dir}/lm-evaluation-harness" apply --check "${harness_dataset_ids_patch}"
  git -C "${cetvel_dir}/lm-evaluation-harness" apply "${harness_dataset_ids_patch}"
fi

python3 -m venv "${venv_dir}"
source "${venv_dir}/bin/activate"
python -m pip install --upgrade pip

# Transformers 5.17 requires PyTorch >=2.5. Pin a CUDA 12.4 wheel that is
# compatible with the selected RunPod base image and RTX 4090.
python -m pip install \
  --index-url https://download.pytorch.org/whl/cu124 \
  torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0
# A venv created with --system-site-packages can make pip mistake the image's
# older cuDNN wheel for the pinned Torch dependency. Install the matching wheel
# into the active environment explicitly so Torch does not depend on image paths.
python -m pip install --ignore-installed --no-deps nvidia-cudnn-cu12==9.1.0.70
python -m pip install -r "${repo_root}/requirements-evaluation.txt"
python -m pip install -e "${cetvel_dir}/lm-evaluation-harness"
