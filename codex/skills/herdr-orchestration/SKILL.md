---
name: herdr-orchestration
description: Coordinate parallel work across visible Herdr sessions, one live agent per pane. Use when the user asks to run multiple workstreams in parallel via Herdr, to orchestrate issue workers in separate panes or tabs, or mentions fanning out herdr agents under one orchestrator.
---

# Herdr Orchestration

Run parallel workstreams as visible live agents, not hidden background workers. One pane holds one named agent, one agent owns one workstream. The orchestrator briefs, polls, and unblocks; it does not do the workstream work itself.

## Layout

- Check topology first: `herdr pane list`, `herdr tab list`. Max four panes per tab; create new tabs (`herdr tab create --label <name>`) when more capacity is needed.
- Split with `--no-focus` and an explicit `--cwd` so the user's focus never moves. Parse new pane IDs from the JSON responses.
- Close only panes the orchestration created.

## Sessions

- Start one real agent per worker pane: `herdr agent start <name> --kind <kind> --pane <id>`. Names match `[a-z][a-z0-9_-]{0,31}`.
- Never substitute invisible subagents for pane sessions. A workstream without a live named agent does not exist.
- Prove liveness before briefing real work: prompt each session for a short reply and confirm every pane answers.

## Fan-out, never serial waiting

- Brief all agents first with `herdr agent prompt <name> "..."` and no `--wait`. Sends return instantly, so every session starts working at once.
- Then run one polling loop: `herdr agent get` for status, `herdr agent read` for output. Total time follows the slowest session, not the sum.
- Resend only to panes that never picked the work up. If a session lands in `blocked`, read what it is asking and surface it to the user instead of answering on their behalf.

## Done per workstream

Each session finishes only when its deliverable exists plus its evidence: tests run, review loop clean, reviewer findings addressed. Report pane, branch, and artifact URLs per workstream.

## Review doctrine (astra decides, sessions review)

- The orchestrator astra consults decide next steps only. They never review code directly and the orchestrator never spawns reviewer subagents.
- Each worker session reviews its own branch by launching separate top-level reviewer sessions from its shell (read-only scope, pinned to the exact pushed SHA). Pane sessions do not have the orchestrator spawn tool, so never order them to call it by name.
- Review repeats until the worker's own reviewer returns clean. Only a clean verdict on the exact pushed HEAD unblocks PR creation.
- If a worker reports it cannot launch any independent review, treat that as a blocker to surface, not a step to skip or substitute.

## Verify claims, never trust transcripts

- A session saying review launched or awaiting verdict proves nothing. Confirm independent evidence before acting on it: reviewer prompt and verdict files, a live process, a pane transcript showing the run, or a matching SHA.
- A claimed review with no artifact behind it is vapor. Call it out, re-establish the review, and say so plainly.
- The main checkout must stay clean. Workers touch only their own worktrees; if a stray edit lands in the shared checkout, confirm the same content exists on the worker branch, then revert the checkout.

## PR end-state

- Once a worker's own reviews are clean, it drives itself to an open PR: base is the agreed base branch, title names the change and closes the issue, creation only, never merge.
- PR bodies follow the repo argus shape: Summary, Before/after table, Try-it verification steps, Automated checks, plus the Closes line. Verify the sections exist with gh pr view before reporting the URL.
- Report one PR URL per workstream on completion.

## Model fallback under throttling

- The default model holds everywhere until astra orders otherwise. Repeated 429 and backoff loops are the trigger for astra to decide a targeted switch.
- The replacement model is named explicitly in the order (no silent swaps), applies at the next resumable boundary with worktree and context preserved, and includes the switch-back condition.

## Worktree isolation

- Give each worker its own git worktree off the base branch (for example `git worktree add ../<repo>-wt-<id> origin/<base> -b <branch>`). Never let two sessions share one checkout; a branch switch in one pane stomps the others.
- Name the exact worktree path and branch in each brief. On teardown, `git worktree remove --force` each one and delete its branch.

## Stopping a worker without killing the pane

- Interrupt first: `herdr agent send-keys <name> esc`, then send a stand-down prompt with no `--wait`: drop work immediately, no more edits/commits/pushes, leave the worktree as-is, reply STOOD-DOWN, wait idle.
- Verify with `herdr agent get` until the status settles.

## Event-driven supervision

The two pieces below ship as runnable scripts in scripts/. Both are taken from a working live deployment (the person-orchestration umbrella). They are records-first: the recorder never acts, and only the pinger acts, and only by waking the orchestrator pane.
- scripts/event_subscriber.py - the reference event subscription (subscribes to pane.agent_status_changed for the given panes, prints matching events as newline JSON, exits after silence). Used by both the recorder and the pinger. Per-pane subscriptions tolerate vanished panes, so one stale pane never kills the whole tap.
- scripts/events_daemon.sh - the recorder. Subscribes to worker pane state changes AND pane.closed (so dead panes are logged), appends every event to a JSONL queue, and NEVER acts. Auto-reconnects on exit. Run with setsid nohup scripts/events_daemon.sh &.
- scripts/pinger_loop.sh - the waker. Records done/blocked into a pending queue (deduped against a delivered log so a settled pane is not pinged repeatedly), then prompts the orchestrator pane once it is idle/done. Configure via env vars ME, WORKERS, PANE_MAP, SILENCE, LOG, PENDING, DELIVERED; launch with setsid nohup scripts/pinger_loop.sh &.

Polling only works while the orchestrator turn is active. For coverage between turns, tap the socket event stream. Two pieces, both record-first. Only the pinger acts, and only by waking the orchestrator pane:

1. Recorder: subscribes to `pane.agent_status_changed` for every worker pane and appends each event to a JSONL queue. This is the lossless record; every orchestrator turn starts by draining it.
2. Pinger: same subscription, client-side filtered to `done`/`blocked`, banks matches in a pending file, and prompts the orchestrator's own pane (`herdr agent prompt <orchestrator-pane-id>`) with a short CHECK summary once the orchestrator is `idle`/`done`. The wake-up arrives as a normal turn in the orchestrator session.

Subscription request (newline-delimited JSON over $HERDR_SOCKET_PATH):

{"id":"sub_1","method":"events.subscribe","params":{"subscriptions":[{"type":"pane.agent_status_changed","pane_id":"w1:p1"}]}}

The first frame acknowledges the subscription ({"result":{"type":"subscription_started"}}); later lines are pushed events shaped like {"data":{"agent_status":"done","pane_id":"w1:p1"}, "event":"pane.agent_status_changed"}.

Reference subscriber (adjust pane IDs; keep scripts outside the repo). Prints matching events, exits after N seconds of silence:

    import socket, json, os, sys
    SOCK = os.environ.get("HERDR_SOCKET_PATH")
    PANES = {"w1:p1H", "w1:p1K"}
    WANT = ("done", "blocked")
    req = {"id": "sub_ping", "method": "events.subscribe", "params": {"subscriptions": [{"type": "pane.agent_status_changed", "pane_id": p} for p in PANES]}}
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(15); s.connect(SOCK)
    s.sendall((json.dumps(req) + "\n").encode())
    buf, ack = b"", False
    s.settimeout(float(sys.argv[1]) if len(sys.argv) > 1 else 300)
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk: break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line: continue
                try: msg = json.loads(line)
                except Exception: continue
                if not ack: ack = True; continue
                d = msg.get("data", {}) if isinstance(msg, dict) else {}
                if d.get("pane_id") in PANES and d.get("agent_status") in WANT:
                    print(json.dumps(msg), flush=True)
    except socket.timeout:
        pass

Reference pinger loop. The stream never blocks on delivery; matches accumulate in a pending file and one batched prompt goes out when the orchestrator is settled:

    export HERDR_ENV=1
    ME=w1:p13
    LOG=/tmp/umbrella-pinger.log
    PENDING=/tmp/umbrella-pending
    touch $PENDING
    me_settled(){
      st=$(herdr agent get $ME 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
      [ "$st" = "idle" ] || [ "$st" = "done" ]
    }
    add_pending(){
      grep -qF "$1" $PENDING 2>/dev/null || echo "$1 $(date -u +%H:%M:%S)" >> $PENDING
    }
    for n in worker-a worker-b; do
      st=$(herdr agent get "$n" 2>/dev/null | jq -r .result.agent.agent_status 2>/dev/null)
      if [ "$st" = "done" ] || [ "$st" = "blocked" ]; then add_pending "$n $st"; fi
    done
    while true; do
      python3 /tmp/umbrella-ping-sub.py 60 2>/dev/null | while read -r line; do
        pane=$(echo "$line" | jq -r .data.pane_id 2>/dev/null)
        pst=$(echo "$line" | jq -r .data.agent_status 2>/dev/null)
        [ -n "$pane" ] && [ -n "$pst" ] && add_pending "$pane $pst"
      done
      if [ -s $PENDING ] && me_settled; then
        BODY=$(head -c 900 $PENDING)
        if herdr agent prompt $ME "SOMETHING-HAPPENED-CHECK: $BODY --- drain the event queue and handle per standing orders." >/dev/null 2>&1; then
          echo "$(date -u +%H:%M:%S) pinged orchestrator: $BODY" >> $LOG
          > $PENDING
        fi
      fi
    done

Run each loop under `setsid nohup ... &` so it survives the turn.

## Watcher troubleshooting (earned the hard way)

- Server-side status filters on the subscription silently match nothing. Subscribe unfiltered per pane and filter `data.agent_status` client-side.
- Subscriptions do not replay. On (re)start, sweep current statuses first (bootstrap) or already-settled workers stay invisible until their next transition.
- Never block the event stream on delivery. Waiting for the orchestrator to settle inside the streaming path wedges everything behind the first event; accumulate-then-deliver instead.
- `pkill -f <name>` matches your own shell when the pattern text is in its command line (heredocs included). Exclude $$, and never put the kill and a heredoc mentioning the same filename in one shell invocation.
- A prompt that returns `idle` with no transcript change stalled. Read the pane before retrying to avoid double submission.
- Short-lived subscribers lose transitions that fire during reconnect because subscriptions do not replay. After every subscriber run, sweep current statuses into pending before delivering, so gaps self-heal on the next cycle.
