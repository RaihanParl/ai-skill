---
name: agent-session-inspection
description: "Inspect local coding-agent session history and recover recent prompts/replies from on-disk state, especially when the CLI only exposes session listings."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [Autonomous-Agents, OpenCode, Session-Forensics, SQLite, Observability]
    related_skills: [opencode, codex, claude-code]
---

# Agent Session Inspection

Recover what happened in a local autonomous coding-agent session when the user asks things like:

- "What was the last message in that OpenCode session?"
- "Did the agent ask for anything?"
- "Which session is the Mandiri one?"
- "Can you inspect a saved session even if it is not currently running?"

Use this skill when the agent CLI can list sessions but does not provide a transcript viewer, or when Hermes does not own the live background process.

## Triggers

- User asks about a past or current session from OpenCode, Codex-like tools, or another local coding agent
- You need the last user message, last assistant reply, or whether the agent was blocked / waiting for input
- `process(action='list')` shows nothing useful because the session was not started by Hermes
- The tool's CLI exposes `session list` but no `session show` / transcript command

## Core idea

Treat the local session database as the source of truth for saved conversations. For OpenCode specifically, the CLI can list sessions, but the detailed transcript is stored in SQLite under the local app data directory.

## OpenCode procedure

### 1) Confirm what the CLI can and cannot do

Start with:

```bash
opencode --version
opencode session list
opencode session --help
```

If `session --help` only supports `list` / `delete`, do not guess at hidden transcript commands. Move to the DB.

### 2) Locate the OpenCode data directory

Common macOS/Linux locations:

- `~/.local/share/opencode/opencode.db`
- `~/.config/opencode/`
- `~/.local/share/opencode/log/opencode.log`

The DB is usually `~/.local/share/opencode/opencode.db`.

### 3) Identify the target session

Query sessions by title or directory:

```bash
sqlite3 ~/.local/share/opencode/opencode.db \
  "select id, title, datetime(time_updated/1000,'unixepoch','localtime') as updated, directory from session order by time_updated desc;"
```

For a named session:

```bash
sqlite3 ~/.local/share/opencode/opencode.db \
  "select id, title, datetime(time_updated/1000,'unixepoch','localtime') as updated, directory from session where lower(title) like '%mandiri%' or lower(directory) like '%mandiri%' order by time_updated desc;"
```

### 4) Inspect message storage layout before reading content

OpenCode stores high-level messages in `message` and message bodies/segments in `part`.

Useful probes:

```bash
sqlite3 ~/.local/share/opencode/opencode.db '.tables'
sqlite3 ~/.local/share/opencode/opencode.db \
  "select count(*) from message where session_id='<SESSION_ID>';"
sqlite3 ~/.local/share/opencode/opencode.db \
  "select count(*) from part where session_id='<SESSION_ID>';"
```

Do not assume `session_message` is populated. In observed sessions it may be empty while `message` + `part` hold the transcript.

### 5) Read the most recent messages

Use a small Python/SQLite probe so you can parse JSON safely:

```python
import sqlite3, json
sid = "<SESSION_ID>"
conn = sqlite3.connect("~/.local/share/opencode/opencode.db")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "select id,time_created,data from message where session_id=? order by time_created desc limit 6",
    (sid,)
).fetchall()
for row in rows:
    print(row["id"], row["time_created"])
    print(json.loads(row["data"]))
```

Then expand each message into its `part` rows:

```python
import sqlite3, json
sid = "<SESSION_ID>"
conn = sqlite3.connect("~/.local/share/opencode/opencode.db")
conn.row_factory = sqlite3.Row
msg_ids = [r["id"] for r in conn.execute(
    "select id from message where session_id=? order by time_created desc limit 6",
    (sid,)
)]
for mid in msg_ids:
    print("MESSAGE", mid)
    parts = conn.execute(
        "select id,time_created,data from part where message_id=? order by time_created,id",
        (mid,)
    ).fetchall()
    for p in parts:
        obj = json.loads(p["data"])
        print(obj)
```

### 6) Extract what the user actually wants

Focus on the fields that answer human questions quickly:

- last user text: `part.data.type == "text"` on a `message.role == "user"`
- last assistant reply: `part.data.type == "text"` on `message.role == "assistant"`
- whether the agent asked for input: assistant text ending in a question, explicit options, or a partial step with no final text
- whether work is incomplete: assistant message with only `step-start` / `reasoning` and no final `text`

### 7) Report clearly

Return:

- session title / ID
- latest user message
- latest assistant text reply, if any
- whether the assistant was asking for a decision or permission
- whether the session appears unfinished

## Interpretation rules

- If the latest assistant message has only `step-start` / `reasoning` parts and no `text`, say the session appears to have started work but has no visible final reply yet.
- If `process(action='list')` is empty, that only means Hermes is not tracking a live background process. It does **not** mean the session does not exist.
- Do not claim the agent is currently running unless you verify current session activity, not merely a live process. OpenCode server listeners and old tmux client panes can outlive work or represent multiple UI attachments.
- To count currently working sessions, cross-check all three: (1) session.time_updated within a short window, (2) current `message=stream` or `message=loop` log entries for that same session, and (3) no later `message="exiting loop"` for it. Count unique session IDs meeting this evidence. Do not count a listener, tmux pane, or saved session by itself.
- Prefer quoting the exact last user/assistant text rather than paraphrasing when the user asks "what did they ask?"

## Pitfalls

- `opencode session --help` may not offer transcript viewing. Do not invent subcommands.
- `session_message` may be empty even for active-looking sessions.
- `message.data` contains metadata; the human-readable body is usually in `part.data` JSON rows.
- Session names may not include the keyword the user uses. Search both `title` and `directory`.
- A newer stub user message can exist with a following assistant step that has not produced final text yet. Read both together before concluding.

## Verification

You are done when you can answer all of these from evidence:

1. Which session matched?
2. What was the last user message?
3. What was the last assistant text reply?
4. Did the assistant ask for anything?
5. Does the session appear to be waiting, blocked, or unfinished?

## References

- `references/opencode-db-layout.md` — concise notes on the OpenCode DB tables and the specific transcript-recovery pattern observed in session work.
