#!/usr/bin/env bash
# Herdr pinger loop (the waker).
#
# Records pane.agent_status_changed events (done/blocked) from the worker panes
# into a pending queue, on TRANSITIONS ONLY: the last observed status per pane
# is tracked in a last-seen file, and a wake-up is queued only when a pane
# *changes into* done/blocked. A pane resting in done (e.g. a parked worker)
# is therefore never pinged twice for the same state. When the orchestrator
# pane is idle/done, the pinger prompts that pane with a
# SOMETHING-HAPPENED-CHECK summary. The wake-up arrives as a normal turn in
# the orchestrator session. The pinger NEVER does the work itself; it only
# wakes the orchestrator.
#
# Launch: setsid nohup scripts/pinger_loop.sh &   (survives the orchestrator turn)
#
# Required environment:
#   HERDR_ENV          set to 1
#
# Configurable environment (with defaults):
#   ME            orchestrator pane id to wake        (w1:p13)
#   WORKERS       space-separated worker NAMES        (worker-a worker-b)
#   PANE_MAP      name=pane pairs, space-separated    ()
#                 e.g. "issue-194=w1:p1H issue-195=w1:p1K"
#   SILENCE       subscriber silence seconds          (60)
#   LOG           pinger log path                     (/tmp/umbrella-pinger.log)
#   PENDING       pending queue file                  (/tmp/umbrella-pending)
#   LASTSEEN      last-observed-status file           (/tmp/umbrella-lastseen)
set -u

export HERDR_ENV=1
ME="${ME:-w1:p13}"
WORKERS="${WORKERS:-worker-a worker-b}"
PANE_MAP="${PANE_MAP:-}"
SILENCE="${SILENCE:-60}"
LOG="${LOG:-/tmp/umbrella-pinger.log}"
PENDING="${PENDING:-/tmp/umbrella-pending}"
LASTSEEN="${LASTSEEN:-/tmp/umbrella-lastseen}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

touch "$PENDING" "$LASTSEEN"

me_settled() {
  local st
  st=$(herdr agent get "$ME" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
  [ "$st" = "idle" ] || [ "$st" = "done" ]
}

# Resolve a pane id (from an event) back to its worker NAME via PANE_MAP.
pane_to_name() {
  local pane="$1" kv name p
  for kv in $PANE_MAP; do
    name="${kv%%=*}"; p="${kv##*=}"
    [ "$p" = "$pane" ] && { echo "$name"; return; }
  done
  echo "$pane"
}

# Map a worker NAME to its pane id via PANE_MAP.
pane_for_name() {
  local name="$1" kv
  for kv in $PANE_MAP; do
    [ "${kv%%=*}" = "$name" ] && { echo "${kv##*=}"; return; }
  done
  echo ""
}

last_seen() { grep -F "$1 " "$LASTSEEN" 2>/dev/null | tail -1 | awk '{print $2}'; }

note_seen() {
  grep -v -F "$1 " "$LASTSEEN" 2>/dev/null > "$LASTSEEN.tmp" || true
  echo "$1 $2" >> "$LASTSEEN.tmp"
  mv "$LASTSEEN.tmp" "$LASTSEEN"
}

# Queue "name status" only when the pane changed INTO done/blocked since the
# last observation. Always records the observation, so done->working->done
# fires again while resting in done stays silent.
consider() {
  [ -n "${1:-}" ] && [ -n "${2:-}" ] || return 0
  local prev
  prev=$(last_seen "$1")
  note_seen "$1" "$2"
  if [ "$2" = "done" ] || [ "$2" = "blocked" ]; then
    if [ "$prev" != "$2" ]; then
      grep -qF "$1 $2" "$PENDING" 2>/dev/null || echo "$1 $2 $(date -u +%H:%M:%SZ)" >> "$PENDING"
    fi
  fi
}

# Bootstrap sweep: subscriptions do not replay, so seed already-settled
# workers. First sight of done/blocked queues once; repeats stay silent.
for n in $WORKERS; do
  p=$(pane_for_name "$n")
  [ -z "$p" ] && continue
  st=$(herdr agent get "$p" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
  consider "$n" "$st"
done

while true; do
  HERDR_PANES="$(echo "$PANE_MAP" | tr ' ' '\n' | cut -d= -f2 | grep -v '^' | tr '\n' ' ')" \
    python3 "$SCRIPT_DIR/event_subscriber.py" "$SILENCE" 2>/dev/null | while read -r line; do
    pane=$(echo "$line" | jq -r .data.pane_id 2>/dev/null)
    pst=$(echo "$line" | jq -r .data.agent_status 2>/dev/null)
    if [ -n "$pane" ] && [ -n "$pst" ]; then
      consider "$(pane_to_name "$pane")" "$pst"
    fi
  done
  # Catch-up sweep so any transition during the silence window is not missed.
  for n in $WORKERS; do
    p=$(pane_for_name "$n")
    [ -z "$p" ] && continue
    st=$(herdr agent get "$p" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
    consider "$n" "$st"
  done
  if [ -s "$PENDING" ] && me_settled; then
    BODY=$(head -c 900 "$PENDING")
    if herdr agent prompt "$ME" "SOMETHING-HAPPENED-CHECK: $BODY --- drain the event queue and handle per standing orders." >/dev/null 2>&1; then
      echo "$(date -u +%H:%M:%S) pinged: $BODY" >> "$LOG"
      : > "$PENDING"
    fi
  fi
done
