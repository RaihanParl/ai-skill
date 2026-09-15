#!/usr/bin/env bash
# Herdr pinger loop for event-driven orchestration supervision.
#
# Records pane.agent_status_changed events (done/blocked) from the worker
# panes into a pending file, then wakes the orchestrator pane once it has
# settled to idle/done. The wake-up arrives as a normal turn in the
# orchestrator session. Runs forever; launch with setsid nohup ... & so it
# survives the orchestrator turn.
#
# Required environment:
#   HERDR_ENV          set to 1
#   HERDR_SOCKET_PATH  unix socket path
#
# Configurable environment (with defaults):
#   ME            orchestrator pane id to wake        (w1:p13)
#   WORKERS       space-separated worker names        (worker-a worker-b)
#   SILENCE       subscriber silence seconds          (60)
#   LOG           pinger log path                     (/tmp/umbrella-pinger.log)
#   PENDING       pending events file                 (/tmp/umbrella-pending)
#   SUBSCRIBER    event_subscriber.py path            (beside this script)
set -u

export HERDR_ENV=1
ME="${ME:-w1:p13}"
WORKERS="${WORKERS:-worker-a worker-b}"
SILENCE="${SILENCE:-60}"
LOG="${LOG:-/tmp/umbrella-pinger.log}"
PENDING="${PENDING:-/tmp/umbrella-pending}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBSCRIBER="${SUBSCRIBER:-$SCRIPT_DIR/event_subscriber.py}"

touch "$PENDING"

me_settled() {
  local st
  st=$(herdr agent get "$ME" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
  [ "$st" = "idle" ] || [ "$st" = "done" ]
}

add_pending() {
  grep -qF "$1" "$PENDING" 2>/dev/null || echo "$1 $(date -u +%H:%M:%S)" >> "$PENDING"
}

# Bootstrap: sweep current statuses so already-settled workers are not missed,
# because subscriptions do not replay.
for n in $WORKERS; do
  st=$(herdr agent get "$n" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
  if [ "$st" = "done" ] || [ "$st" = "blocked" ]; then
    add_pending "$n $st"
  fi
done

while true; do
  python3 "$SUBSCRIBER" "$SILENCE" 2>/dev/null | while read -r line; do
    pane=$(echo "$line" | jq -r .data.pane_id 2>/dev/null)
    pst=$(echo "$line" | jq -r .data.agent_status 2>/dev/null)
    [ -n "$pane" ] && [ -n "$pst" ] && add_pending "$pane $pst"
  done
  # Catch up on any status changes since the last sweep, then deliver.
  for n in $WORKERS; do
    st=$(herdr agent get "$n" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
    if [ "$st" = "done" ] || [ "$st" = "blocked" ]; then
      add_pending "$n $st"
    fi
  done
  if [ -s "$PENDING" ] && me_settled; then
    BODY=$(head -c 900 "$PENDING")
    if herdr agent prompt "$ME" "SOMETHING-HAPPENED-CHECK: $BODY --- drain the event queue and handle per standing orders." >/dev/null 2>&1; then
      echo "$(date -u +%H:%M:%S) pinged orchestrator: $BODY" >> "$LOG"
      : > "$PENDING"
    fi
  fi
done
