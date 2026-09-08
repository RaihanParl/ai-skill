# Hermes Session Completion Monitor

Session-derived notes from the 2026-06-24 Hermes Telegram completion-alert workflow.

## Goal

Send a Telegram ping when a Hermes CLI session finishes, but keep the notification short and actionable:

- include the session title/id
- say whether the last assistant message looks like a request for confirmation or a clean completion
- include only the point of the last assistant message, not the full transcript

## Classification heuristic

Treat the session as `needs confirmation` when the last assistant message contains a question mark or a confirmation-seeking phrase such as:

- please confirm
- need your confirmation
- can you confirm
- should I
- would you like
- do you want
- shall I
- want me to
- let me know if
- is this okay
- can I proceed
- waiting for confirmation
- reply with

Otherwise classify it as `complete`.

## Output shape

Suggested Telegram body:

```text
Hermes session finished
- session: <title>
- id: <session id>
- status: needs confirmation | complete
- last: <one-line summary of the final assistant message>
- ended: <local timestamp>
- dir: <cwd>
- end reason: <reason>
```

## Implementation notes

- Read the canonical Hermes SQLite session store, not conversation history from memory.
- Use the most recent assistant message in the finished session as the source for the summary.
- Reduce the message to one line by taking the first non-empty line or sentence fragment.
- Persist the last processed `(ended_at, session_id)` key so the monitor is idempotent.
- Deliver to the user's Telegram home channel, matching the existing OpenCode alert pattern.

## Verification pattern

1. Create a tiny temp SQLite DB with `sessions` and `messages` tables.
2. Insert one finished session whose last assistant message is a question.
3. Run the monitor once and confirm it reports `needs confirmation` with a one-line summary.
4. Insert a second finished session whose last assistant message is declarative.
5. Run the monitor again and confirm it reports `complete`.
6. Run the monitor a third time without new sessions and confirm it stays silent.
