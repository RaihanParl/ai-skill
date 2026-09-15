#!/usr/bin/env bash
# Herdr event recorder (record-only event tap).
#
# Subscribes to worker pane state changes and pane.closed, appends every event
# to a JSONL queue, and NEVER acts. Auto-reconnects on subscriber exit so a
# transient socket drop or a vanished pane does not stop the record.
#
# Launch: setsid nohup scripts/events_daemon.sh &   (survives the orchestrator turn)
#
# Configurable environment (with defaults):
#   HERDR_PANES   space-separated worker pane IDs (w1:p1H w1:p1K)
#   SILENCE       subscriber silence seconds        (300)
#   QUEUE         event JSONL path                  (/tmp/umbrella-events.jsonl)
#   LOG           recorder log path                 (/tmp/umbrella-events-daemon.log)
export HERDR_ENV=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HERDR_CLOSED=1
QUEUE="${QUEUE:-/tmp/umbrella-events.jsonl}"
LOG="${LOG:-/tmp/umbrella-events-daemon.log}"

while true; do
  python3 "$SCRIPT_DIR/event_subscriber.py" "${SILENCE:-300}" >> "$LOG" 2>&1
  echo "$(date -u +%H:%M:%S) subscriber exited, reconnecting in 5s" >> "$LOG"
  sleep 5
done
