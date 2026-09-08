# OpenCode Telegram Bridge Reference

Session-derived implementation details for the `telegram-controlled-agent-sessions` umbrella.

## Local files

- Bridge controller: `~/.hermes/scripts/opencode_telegram_bridge.py`
- Bridge cron wrapper: `~/.hermes/scripts/opencode_telegram_bridge_tick.sh`
- Launch wrapper: `~/.hermes/scripts/opencode_bridge_launch.sh`
- Passive monitor: `~/.hermes/scripts/opencode_monitor.py`
- State file: `~/.hermes/scripts/state/opencode-telegram-bridge.json`
- Session logs dir: `~/.hermes/scripts/state/opencode-bridge-logs/`

## Cron jobs seen in this session

- Passive monitor job: `6c471e37bb20`
- Reply-to-control bridge job: `738bb0b866ec`
- Bridge schedule: every 1 minute, `no_agent=true`, `deliver=local`

## Telegram command set

Implicit single-session commands:
- `approve`
- `deny`
- `stop`
- `send: <text>`
- `key: enter|y|n|escape|up|down|tab|ctrl-c`

Explicit multi-session commands:
- `/oc list`
- `/oc approve <bridge_id>`
- `/oc deny <bridge_id>`
- `/oc send <bridge_id> <text>`
- `/oc key <bridge_id> <key>`
- `/oc stop <bridge_id>`

## Verified smoke test pattern

A fully local verification succeeded with this shape:

1. Create a temp sqlite DB with:
   - `sessions(id text primary key, source text, user_id text)`
   - `messages(id integer primary key, session_id text, role text, content text)`
2. Start a dummy tmux session that echoes stdin.
3. Run bridge `register` against the tmux session with isolated `OPENCODE_BRIDGE_STATE_DIR` and `OPENCODE_BRIDGE_HERMES_DB`.
4. Insert a synthetic Telegram message like:
   - `/oc send <bridge_id> hello-from-telegram-bridge`
5. Run bridge `tick`.
6. Capture the tmux pane and confirm:
   - `RECEIVED:hello-from-telegram-bridge`

Observed successful pane output in this session:

```text
hello-from-telegram-bridge
RECEIVED:hello-from-telegram-bridge
```

## Important implementation choices

- Inbound Telegram commands were read from Hermes `state.db`, not from Telegram Bot API polling.
- The bridge used tmux as the control surface because OpenCode lacks a clean external approval API for arbitrary existing sessions.
- The cron job had to call a shell wrapper because putting `opencode_telegram_bridge.py tick` directly in the cron `script` field caused `Script not found`.

## Attach an existing OpenCode session

Use this when OpenCode is already running in tmux and the user wants Telegram control after the fact.

1. Find the tmux session that is actually running OpenCode.
2. Register it with the bridge:

```bash
~/.hermes/scripts/opencode_telegram_bridge.py register --tmux-session <tmux-session-name> --dir /path/to/repo --title "<session title>" --kind opencode
```

3. Confirm the bridge is active:

```bash
~/.hermes/scripts/opencode_telegram_bridge.py list
```

4. Use Telegram commands against the returned bridge id.

Important:
- `opencode -s <session_id>` alone only resumes OpenCode; it does not wire Telegram control.
- The bridge needs the live tmux session, because it injects keystrokes/text into tmux, not into a historical OpenCode session record.
