#!/usr/bin/env bash
set -euo pipefail
/workspace/.venvs/exp010-train/bin/python -u /workspace/archive_pair.py
/workspace/.venvs/exp010-train/bin/python -u /workspace/transfer_backup.py --mode split --root /workspace
