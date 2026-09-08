# Agent Mirror Dashboard

Use this when the real problem is not control, but visibility: the user launches or steers agents from Telegram and cannot see live progress, reasoning traces, tool output, or side-channel state.

## When to use

Use alongside the Telegram bridge when the user says things like:
- "I can't see what it's doing from Telegram"
- "I can't see the thought process"
- "I need a live mirror of Cursor, Hermes, and OpenCode"
- "Telegram is too blind / too narrow"

This is an observability layer, not a control layer.

## Proven pattern

Build a small read-only local webserver that aggregates each agent's persisted state:

- Hermes:
  - `~/.hermes/state.db`
  - tables: `sessions`, `messages`
  - useful fields: `title`, `cwd`, `started_at`, `ended_at`, `message_count`, `tool_call_count`, `content`, `reasoning`, `reasoning_content`, `tool_name`

- OpenCode:
  - `~/.local/share/opencode/opencode.db`
  - tables: `session`, `message`, `part`
  - human-visible detail usually lives in `part.data`
  - useful part types: `text`, `reasoning`, `tool`, `step-start`, `step-finish`, `patch`

- Cursor:
  - `~/.cursor/projects/*/agent-transcripts/*/*.jsonl`
  - `~/.cursor/projects/*/terminals/*.txt`
  - `~/.cursor/ide_state.json`

Also include:
- `ps` process view for `hermes`, `opencode`, and `Cursor`
- `tmux ls` output for live session attachment clues

## UX goal

The page should let the user answer, at a glance:
1. Which agent/process is active?
2. Which session is newest?
3. What was the latest user prompt?
4. What did the assistant last say?
5. Is there reasoning/tool activity even if Telegram only shows the final reply?
6. Which tmux session or Cursor terminal likely corresponds to the work?

## Minimum endpoints

- `/` — HTML dashboard
- `/healthz` — simple health check
- `/api/state` — aggregate JSON
- `/api/hermes`
- `/api/opencode`
- `/api/cursor`

## Implementation notes

- Read-only is the right first version.
- Poll every 2-3 seconds; this is enough for human monitoring.
- Bind to `0.0.0.0` only if the user wants LAN access.
- Make it explicit when the dashboard has no auth.
- Prefer stdlib HTTP if speed matters more than framework choice.
- Render raw JSON/text for reasoning and tool blocks rather than overdesigning the UI.

## Verification

Do not claim success until all of these are true:
- `/healthz` returns `ok`
- `/api/state` returns non-empty real data
- browser rendering shows live sessions, not just a loading stub
- at least one Hermes session, one OpenCode session, and one Cursor artifact are visible when available locally

## Pitfalls

- Browser validation can fail because the page JS is invalid even when `/api/state` works. Validate both API and browser rendering.
- Cursor visibility is partial and depends on what Cursor persisted to transcript JSONL and terminal snapshots.
- OpenCode transcript recovery must read `part.data`, not only `message.data`.
- Hermes tool output is often JSON-encoded inside `messages.content`; parse it when possible but still preserve the raw string.
- If the user wants public exposure, add auth before exposing beyond the LAN.

## Relationship to the Telegram bridge

The Telegram bridge solves control and notification.
This dashboard solves observability.
For users who complain that Telegram is too opaque, deploy both together.