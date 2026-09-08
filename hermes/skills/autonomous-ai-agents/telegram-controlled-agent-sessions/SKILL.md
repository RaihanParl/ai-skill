---
name: telegram-controlled-agent-sessions
description: Use when a user wants Telegram notifications or reply-to-control for long-running CLI agent sessions such as OpenCode, especially when Hermes already owns the Telegram bot integration.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [telegram, opencode, tmux, cron, hermes, agent-control]
    related_skills: [hermes-agent, opencode, agent-session-inspection]
---

# Telegram-Controlled Agent Sessions

## Overview

This skill turns a local CLI agent session into a Telegram-controllable workflow. The durable pattern is:

1. Hermes remains the only Telegram bot poller.
2. The target agent session runs inside tmux so Hermes can inject keystrokes or text later.
3. A lightweight bridge job watches Hermes's own Telegram session database for inbound commands and watches tmux output for prompts that need attention.
4. Notifications and control are tied to a bridge id so the user can reply from Telegram without touching the local terminal.
5. For Hermes CLI completion alerts, send only the last assistant message's point, then label the session as either `needs confirmation` or `complete`.

This pattern is especially useful for OpenCode because it does not expose a clean external approval API for arbitrary existing sessions.

Important lesson from this session:
- `opencode -s <session_id>` resumes or opens the OpenCode session, but it does not by itself make that session Telegram-controllable.
- To control an existing OpenCode session from Telegram, first attach or register the live tmux session with the bridge, then send Telegram commands through the bridge id.

## When to Use

Use when:
- The user wants Telegram pings when an agent run is done, idle, or blocked on approval.
- The user wants to approve, deny, stop, or answer a question in a live agent session from Telegram.
- Hermes already has Telegram configured and should remain the single owner of the bot token.
- The underlying agent is terminal-driven and can be controlled by stdin or keystrokes.
- The user wants a short completion ping for a Hermes CLI session that distinguishes "needs confirmation" from "complete" using only the final assistant message's point.

Do not use when:
- The session was launched outside Hermes and cannot be reattached safely.
- The target tool already exposes a first-class remote approval API.
- The user only needs passive notifications; then a simpler monitor is enough.

## Core Design Rules

1. Single Telegram owner.
   - Do not start a second Telegram long-poller on the same bot token when Hermes gateway already exists.
   - Read inbound Telegram messages from Hermes's own state DB instead of polling Telegram again.
   - Completion criterion: exactly one Telegram runtime owns the bot token, and bridge commands still arrive.

2. tmux is the control surface.
   - Launch or register the agent session in tmux.
   - Capture pane output for prompt detection.
   - Send `y`, `n`, `Enter`, `C-c`, or arbitrary text back into the live pane.
   - Completion criterion: a test command injected by the bridge is visible in the tmux pane output.

3. Bridge ids are mandatory.
   - Every controlled session gets a stable bridge id.
   - If only one bridge is active, simple commands like `approve` or `send: ...` may target it implicitly.
   - If several are active, require explicit `/oc <action> <bridge_id> ...` commands.
   - Completion criterion: the operator can list active bridges and map each one to a tmux session and workdir.

4. Separate notification from session launch.
   - Use one script for bridge control and, optionally, another monitor for completion or idle alerts.
   - Completion criterion: each job has one purpose and can be run by itself.

## Implementation Pattern

### A. Launch model-controlled sessions through the bridge

Preferred flow:
1. Start a tmux session that runs the agent CLI in the intended workdir.
2. Attach pane logging with `tmux pipe-pane -o` to a state/log directory.
3. Persist metadata: bridge id, tmux session name, workdir, chat id, last notification hash, last seen running state.
4. Send a Telegram boot message that explains the available commands.

For OpenCode specifically:
- Prefer a wrapper launcher that calls a Python bridge script with a `launch` subcommand.
- Keep the raw `opencode` command inside tmux rather than as a detached shell background process.

### B. Detect when attention is needed

Useful prompt signals include words such as:
- permission
- approve
- approval
- authorize
- authorization
- allow
- deny
- question
- continue?
- waiting for authorization

Heuristic rules:
- Hash the recent pane excerpt and do not resend the same excerpt repeatedly.
- Mark the session `waiting_input` only when the excerpt is both non-empty and actionable.
- Mark the session `exited` only after tmux has actually disappeared.

### C. Map Telegram replies into actions

Recommended commands:
- `approve`
- `deny`
- `stop`
- `send: <text>`
- `key: enter|y|n|escape|up|down|tab|ctrl-c`
- `/oc list`
- `/oc approve <bridge_id>`
- `/oc deny <bridge_id>`
- `/oc send <bridge_id> <text>`
- `/oc key <bridge_id> <key>`
- `/oc stop <bridge_id>`

Action mapping:
- `approve` -> send `y` then `Enter`
- `deny` -> send `n` then `Enter`
- `stop` -> send `C-c`
- `send:` -> send literal text plus `Enter`
- `key:` -> send the requested tmux key name

Completion criterion: a simulated inbound Telegram command changes the live tmux pane exactly as expected.

### D. Run the bridge via cron

Use a no-agent cron job that calls a tiny shell wrapper, not a `script` value with embedded arguments. This avoids scheduler path parsing mistakes.

Pattern:
1. Python bridge implements `tick`.
2. Shell wrapper runs `python3 "$HOME/.hermes/scripts/...py" tick`.
3. Cron job uses `no_agent=true`, `deliver=local`, and a 1-minute schedule.
4. Manually `run` the cron job once after creation or updates.

Completion criterion: the cron job's latest run status is `ok` and the same `tick` command also succeeds directly in the shell.

## When visibility is the real problem

Sometimes the user does not mainly need more Telegram control. They need to see what the agent is doing because Telegram only shows a narrow final reply and hides most of the work. When the complaint is "I can't see what it's doing" or "I can't see the thought process", add a local read-only web mirror.

Recommended dashboard inputs:
- Hermes `~/.hermes/state.db` (`sessions`, `messages`)
- OpenCode `~/.local/share/opencode/opencode.db` (`session`, `message`, `part`)
- Cursor transcript JSONL under `~/.cursor/projects/*/agent-transcripts/*/*.jsonl`
- Cursor terminal snapshots under `~/.cursor/projects/*/terminals/*.txt`
- `ps` output for `hermes`, `opencode`, and `Cursor`
- `tmux ls` output

Recommended endpoints:
- `/`
- `/healthz`
- `/api/state`
- `/api/hermes`
- `/api/opencode`
- `/api/cursor`

This turns Telegram into the control plane and the browser into the observability plane.

See `references/agent-mirror-dashboard.md` for the concrete storage locations, schema hints, UI goals, and verification checklist.

## Verification Recipes

### Minimal local bridge verification

1. Create a temporary sqlite DB with Hermes-like `sessions` and `messages` tables.
2. Start a dummy tmux session that echoes anything it receives on stdin.
3. Register that tmux session with the bridge using an isolated state dir.
4. Insert a synthetic Telegram message such as `/oc send <bridge_id> hello-from-telegram-bridge` into the temp DB.
5. Run bridge `tick` against that temp DB and state dir.
6. Capture the tmux pane and confirm the echoed text arrived.

This proves the control path end to end without waiting for a real Telegram reply.

### Live Telegram verification

1. Send a test Telegram message from the bridge itself.
2. Confirm Telegram delivery succeeded and returned a message id.
3. Launch one real bridged agent session.
4. Reply from Telegram with `approve`, `deny`, or `send: ...`.
5. Confirm the tmux pane and agent behavior reflect the reply.

## Common Pitfalls

1. Starting a second Telegram poller.
   - Symptom: missed updates or bot token conflicts.
   - Fix: let Hermes own Telegram and read Hermes DB for inbound commands.

2. Using a bridge for sessions that Hermes did not launch or register.
   - Symptom: no reliable target for approval injection.
   - Fix: launch through the bridge or explicitly register the tmux session first.

3. Treating all approval prompts as plain `y/n` prompts.
   - Symptom: the bridge sends `y` but the tool expected another key or free-form text.
   - Fix: fall back to `key:` or `send:` commands for prompt-specific control.

4. Embedding arguments directly in the cron `script` field.
   - Symptom: scheduler reports `Script not found`.
   - Fix: use a shell wrapper script and point cron at that wrapper.

5. Spamming repeated Telegram alerts for the same prompt.
   - Symptom: every minute sends the same message again.
   - Fix: hash the current actionable excerpt and suppress duplicates until the excerpt changes.

## References

- `references/opencode-telegram-bridge.md` — concrete file paths, cron jobs, control commands, and the verified tmux/sqlite smoke-test pattern from this session.
- `references/hermes-session-completion-monitor.md` — session-completion alerting pattern that summarizes the last assistant message as either confirmation-seeking or complete.

## Verification Checklist

- [ ] Hermes remains the only Telegram poller.
- [ ] Controlled sessions run inside tmux.
- [ ] Each active session has a bridge id and persisted state.
- [ ] The bridge can read inbound Telegram messages from Hermes DB.
- [ ] A synthetic DB message can drive text into a dummy tmux session.
- [ ] A real Telegram test send succeeds.
- [ ] Cron `tick` runs successfully through a wrapper script.
