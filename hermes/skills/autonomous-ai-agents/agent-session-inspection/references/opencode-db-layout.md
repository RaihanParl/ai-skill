# OpenCode DB layout and transcript recovery

Observed durable pattern for local OpenCode session inspection on macOS:

## Key paths

- Session DB: `~/.local/share/opencode/opencode.db`
- Log file: `~/.local/share/opencode/log/opencode.log`
- Config: `~/.config/opencode/`

## Tables that mattered

- `session`: canonical list of sessions, titles, directories, timestamps
- `message`: top-level role/metadata rows per conversation turn
- `part`: message body fragments, including `text`, `reasoning`, `tool`, `step-start`, `step-finish`
- `session_message`: present in schema but was empty for the inspected session, so not reliable as first stop

## Reliable lookup flow

1. Find session by title or directory:
   - search `session.title`
   - also search `session.directory` because project names may carry the keyword instead of the title
2. Pull latest `message` rows ordered by `time_created desc`
3. For each target `message.id`, read `part` rows ordered by `time_created,id`
4. Extract exact human-visible content from `part.data.text` where `part.data.type == "text"`
5. Treat `reasoning` and `step-*` rows as execution state, not final user-visible output

## What this recovers well

- last user prompt
- last assistant visible reply
- whether the assistant asked for a decision
- whether the newest assistant turn started but never produced final text

## Example interpretation from session work

A session can show this sequence near the end:

- user: asks whether the agent is stuck
- assistant: explains status and asks which recovery path to try
- user: grants permission to continue
- assistant: newest row exists, but only `step-start` and empty `reasoning`

Interpretation: the assistant had started the next turn, but there was no completed visible reply yet.

## Why this belongs in a skill

The CLI exposed `opencode session list` but not a transcript viewer. The DB inspection path is the durable recovery method when a user asks about saved session contents or pending agent questions.
