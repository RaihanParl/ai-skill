# OpenCode Telegram reply-to-control bridge

Use this when the user wants to control a live OpenCode session from Telegram through Hermes.

## Scope

This works for bridge-managed sessions only:
- OpenCode sessions launched through the bridge script, or
- tmux sessions explicitly registered with the bridge.

It is not a universal controller for arbitrary existing OpenCode processes.

## Why this design

Do not poll Telegram Bot API directly from the bridge when Hermes gateway already owns the same bot token. Two long-pollers on one bot conflict.

Instead, the bridge should:
1. Watch Hermes's own session DB (`~/.hermes/state.db`) for new Telegram user messages.
2. Parse control messages from the authorized Telegram user.
3. Forward them into a tmux-managed OpenCode session.
4. Send outbound alerts through the Telegram Bot API for bridge status and actionable prompts.

## Proven pattern

Scripts created under `~/.hermes/scripts/`:
- `opencode_telegram_bridge.py`
- `opencode_telegram_bridge_tick.sh`
- `opencode_bridge_launch.sh`

Typical cron watchdog:
- `no_agent=true`
- schedule `every 1m`
- script wrapper runs `python3 ~/.hermes/scripts/opencode_telegram_bridge.py tick`

## Session model

The bridge stores session state under:
- `~/.hermes/scripts/state/opencode-telegram-bridge.json`
- logs under `~/.hermes/scripts/state/opencode-bridge-logs/`

Each bridged session should track:
- bridge id
- tmux session name
- workdir
- title/kind
- last notified hash
- status: running / waiting_input / exited

## Recommended Telegram commands

If only one bridged session is active, these can map automatically:
- `approve`
- `deny`
- `stop`
- `send: <text>`
- `key: <key>`

For multiple active bridges, support explicit commands:
- `/oc list`
- `/oc approve <bridge_id>`
- `/oc deny <bridge_id>`
- `/oc send <bridge_id> <text>`
- `/oc key <bridge_id> <key>`
- `/oc stop <bridge_id>`

## Input forwarding

Use tmux as the transport boundary.
- Text replies: `tmux send-keys -l ...` then `Enter` if submitting.
- Approval shortcuts can be implemented as `y` + `Enter` and `n` + `Enter`.
- Keep a raw `key:` escape hatch for prompts that need different keys.

## Actionable-prompt detection

A practical heuristic is to capture the last pane lines and look for words like:
- `permission`
- `approve`
- `approval`
- `authorize`
- `authorization`
- `allow`
- `deny`
- `question`
- `waiting for authorization`

When the excerpt hash changes and looks actionable, send a Telegram prompt with the bridge id and reply instructions.

## Verification pattern

A reliable local smoke test is:
1. Start a dummy tmux session that echoes input.
2. Register it with the bridge.
3. Insert a fake Telegram user command into a temp copy of Hermes `state.db`.
4. Run `tick`.
5. Confirm the tmux pane shows the forwarded text.

Observed good result shape:
- sent `/oc send <bridge_id> hello-from-telegram-bridge`
- tmux pane showed `RECEIVED:hello-from-telegram-bridge`

## Pitfalls

- Do not rely on `reply_to_message` metadata unless you have verified Hermes stores it in the session DB for your platform flow.
- Prefer explicit bridge IDs when more than one bridged session is active.
- This pattern depends on tmux-managed sessions; unmanaged OpenCode TUI processes are not safely controllable from Telegram.
- Some terminal actions may trigger command-approval prompts from Hermes tooling during testing; avoid encoding the denial itself as a lesson. The durable lesson is the tmux/DB bridge pattern.
