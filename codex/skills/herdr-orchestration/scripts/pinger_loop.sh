#!/usr/bin/env bash
# Herdr pinger loop (the waker).
#
# Records pane.agent_status_changed events (done/blocked) from the worker panes
# into a pending queue, deduplicated against a delivered log so an already-settled
# pane is not pinged repeatedly. When the orchestrator pane is idle/done, it
# prompts that pane with a SOMETHING-HAPPENED-CHECK summary. The wake-up arrives
# as a normal turn in the orchestrator session. The pinger NEVER does the work
# itself; it only wakes the orchestrator.
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
#   DELIVERED     delivered memory file               (/tmp/umbrella-delivered)
#   DEDUP_SECS    suppress re-ping within this window  (1800)
set -u

export HERDR_ENV=1
ME="${ME:-w1:p13}"
WORKERS="${WORKERS:-worker-a worker-b}"
PANE_MAP="${PANE_MAP:-}"
SILENCE="${SILENCE:-60}"
LOG="${LOG:-/tmp/umbrella-pinger.log}"
PENDING="${PENDING:-/tmp/umbrella-pending}"
DELIVERED="${DELIVERED:-/tmp/umbrella-delivered}"
DEDUP_SECS="${DEDUP_SECS:-1800}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

touch "$PENDING" "$DELIVERED"

now() { date +%s; }

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

# Record "name status" into PENDING, but skip if delivered within DEDUP_SECS.
add_pending() {
  local fp="$1 $2" t old
  t=$(now)
  old=$(grep -F "$fp " "$DELIVERED" 2>/dev/null | tail -1 | awk '{print $NF}')
  if [ -n "$old" ] && [ $((t - old)) -lt "$DEDUP_SECS" ]; then
    return 0
  fi
  grep -qF "$fp" "$PENDING" 2>/dev/null || echo "$fp $t" >> "$PENDING"
}

# Bootstrap sweep: subscriptions do not replay, so seed already-settled workers.
# Map worker names to panes from PANE_MAP when provided.
pane_for_name() {
  local name="$1" kv p
  for kv in $PANE_MAP; do
    [ "${kv%%=*}" = "$name" ] && { echo "${kv##*=}"; return; }
  done
  echo ""
}
for n in $WORKERS; do
  p=$(pane_for_name "$n")
  [ -z "$p" ] && continue
  st=$(herdr agent get "$p" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
  if [ "$st" = "done" ] || [ "$st" = "blocked" ]; then
    add_pending "$n" "$st"
  fi
done

while true; do
  HERDR_PANES="$(echo "$PANE_MAP" | tr ' ' '\n' | cut -d= -f2 | grep -v '^' | tr '\n' ' ')" \
    python3 "$SCRIPT_DIR/event_subscriber.py" "$SILENCE" 2>/dev/null | while read -r line; do
    pane=$(echo "$line" | jq -r .data.pane_id 2>/dev/null)
    pst=$(echo "$line" | jq -r .data.agent_status 2>/dev/null)
    if [ -n "$pane" ] && [ -n "$pst" ]; then
      add_pending "$(pane_to_name "$pane")" "$pst"
    fi
  done
  # Catch-up sweep so any transition during the silence window is not missed.
  for n in $WORKERS; do
    p=$(pane_for_name "$n")
    [ -z "$p" ] && continue
    st=$(herdr agent get "$p" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
    if [ "$st" = "done" ] || [ "$st" = "blocked" ]; then
      add_pending "$n" "$st"
    fi
  done
  if [ -s "$PENDING" ] && me_settled; then
    BODY=$(head -c 900 "$PENDING")
    if herdr agent prompt "$ME" "SOMETHING-HAPPENED-CHECK: $BODY --- drain the event queue and handle per standing orders." >/dev/null 2>&1; then
      echo "$(date -u +%H:%M:%S) pinged: $BODY" >> "$LOG"
      awk '{print $1, $2, $NF}' "$PENDING" >> "$DELIVERED"
      : > "$PENDING"
    fi
  fi
done
