#!/usr/bin/env bash
set -euo pipefail
export HF_HOME=/workspace/.cache/huggingface
export NLTK_DATA=/root/nltk_data
cd /workspace/reflex-wsp
exec 9>card-suite.lock
flock -n 9
PY=/workspace/.venvs/reflex-eval/bin/python
test -f eval/smoke/wsp/output.json
printf 'parent_smoke\n' > suite-stage.txt
"$PY" tools/run_card_eval.py parent --smoke > logs/smoke-parent.log 2>&1
printf 'wsp_benchmarks\n' > suite-stage.txt
"$PY" tools/run_card_eval.py wsp > logs/card-wsp.log 2>&1
printf 'parent_benchmarks\n' > suite-stage.txt
"$PY" tools/run_card_eval.py parent > logs/card-parent.log 2>&1
printf 'benchmarks_complete\n' > suite-stage.txt