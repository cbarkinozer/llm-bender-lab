#!/usr/bin/env bash
# Pod-side supervisor for the unattended understanding queue (diagnostic runs, then Belebele and the writing probe, then arm A).
# Every 60 s: restarts a crashed stage (at most 2 restarts each, finished runs are skipped, partial run dirs are removed),
# and when the queue ends it packs results (no model weights) into $ROOT/pkg with SHA256SUMS and writes SUPERVISOR_DONE.
# Progress for a human or a scheduled check: $ROOT/supervisor-status.txt
set -uo pipefail
ROOT=/workspace/lfm3-evalv2
REPO=$ROOT/repo
DIAG=$ROOT/diag-runs
STATUS=$ROOT/supervisor-status.txt
PRIMARY="base:off selfdistill-b-cpt:off base:on selfdistill-b-cpt:on"
diag_restarts=0
extras_restarts=0
cd "$REPO"

log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$STATUS"; }
running() { pgrep -f "$1" > /dev/null; }
clean_partial() {
  for d in "$DIAG"/*; do
    if [ -d "$d" ] && [ "$(basename "$d")" != logs ] && [ ! -f "$d/summary.json" ] && ! running run_lfm3_understanding_diagnostic.py; then
      log "removing partial run dir $d"; rm -rf "$d"
    fi
  done
}
package() {
  mkdir -p "$ROOT/pkg"
  (cd "$ROOT" && tar czf pkg/understanding-summaries.tar.gz --exclude='diag-runs/*/answers.jsonl' \
      diag-runs belebele-runs writing-runs extras-logs supervisor-status.txt 2> /dev/null
   tar czf pkg/understanding-diag-answers.tar.gz diag-runs/*/answers.jsonl 2> /dev/null
   cd pkg && sha256sum understanding-*.tar.gz > SHA256SUMS)
  log "packed: $(ls -la "$ROOT/pkg" | tail -n +2 | awk '{print $5, $9}' | tr '\n' ';')"
}

log "supervisor started"
while true; do
  sleep 60
  if grep -q EXTRAS_DONE "$ROOT/extras-full.log" 2> /dev/null; then
    log "queue finished (EXTRAS_DONE)"; package; log "SUPERVISOR_DONE ok"; date -u +%FT%TZ > "$ROOT/SUPERVISOR_DONE"; exit 0
  fi
  b_on=$DIAG/selfdistill-b-cpt-think-on/summary.json
  if [ ! -f "$b_on" ] && ! running run_lfm3_understanding_diagnostic_session.sh; then
    if [ "$diag_restarts" -ge 2 ]; then
      log "diagnostic driver died and restart budget is spent; stopping with partial results"; package
      date -u +%FT%TZ > "$ROOT/SUPERVISOR_DONE"; exit 1
    fi
    diag_restarts=$((diag_restarts + 1)); clean_partial
    log "diagnostic driver not running and primary runs unfinished: restart $diag_restarts"
    (RUN_LIST="$PRIMARY" setsid nohup bash scripts/evaluation/run_lfm3_understanding_diagnostic_session.sh full \
       >> "$ROOT/diag-full.log" 2>&1 < /dev/null &)
  elif [ -f "$b_on" ] && ! running run_lfm3_understanding_extras_session.sh; then
    if [ "$extras_restarts" -ge 2 ]; then
      log "extras driver died and restart budget is spent; stopping with partial results"; package
      date -u +%FT%TZ > "$ROOT/SUPERVISOR_DONE"; exit 1
    fi
    extras_restarts=$((extras_restarts + 1)); clean_partial
    log "extras driver not running before EXTRAS_DONE: restart $extras_restarts"
    (setsid nohup bash scripts/evaluation/run_lfm3_understanding_extras_session.sh >> "$ROOT/extras-full.log" 2>&1 < /dev/null &)
  fi
  if [ $((SECONDS % 600)) -lt 60 ]; then
    log "alive: diag runs=$(ls "$DIAG" | grep -c think) scored=$(ls "$DIAG"/*/summary.json 2> /dev/null | wc -l) belebele=$(ls "$ROOT"/belebele-runs/*/summary.json 2> /dev/null | wc -l) writing=$(ls "$ROOT"/writing-runs/*/run-manifest.json 2> /dev/null | wc -l)"
  fi
done
