# OpenCode monitoring via Hermes cron

Use this when the user wants Telegram alerts for OpenCode background work.

## Goal

Send a message only when something meaningful changed:
- OpenCode needs manual authorization
- OpenCode finished a task loop
- OpenCode one-shot work appears done and has gone quiet

## Data sources

OpenCode stores useful state in:
- `~/.local/share/opencode/opencode.db`
- `~/.local/share/opencode/log/opencode.log`

Useful tables seen in practice:
- `session`
- `message`
- `part`
- `session_message`
- `permission`

Useful facts:
- Session title and working directory live in `session`.
- Authorization waits can appear in `part.data` as `Waiting for authorization`.
- Some completions appear in the log as `message="exiting loop" session.id=...`.
- Some quick one-shot runs are easier to detect by `session.time_updated` becoming quiet for a short threshold.

## Recommended watchdog pattern

1. Write a script under `~/.hermes/scripts/`.
2. The script reads the DB/log, compares against a small JSON state file, and prints alerts only for new events.
3. Schedule it with Hermes cron in script-only mode:

```python
cronjob(
  action='create',
  name='opencode-telegram-monitor',
  schedule='every 1m',
  script='opencode_monitor.py',
  no_agent=True,
  deliver='telegram:<user_id>'
)
```

Why `no_agent=True`:
- stdout is delivered verbatim
- empty stdout stays silent
- no LLM cost

## Detection queries

Authorization-needed rows:

```sql
select p.id, p.session_id, p.time_created,
       coalesce(json_extract(p.data, '$.state.input.command'), '') as command,
       coalesce(json_extract(p.data, '$.tool'), '') as tool_name
from part p
where p.data like '%Waiting for authorization%'
order by p.time_created asc, p.id asc;
```

Session titles/directories:

```sql
select id, title, directory, time_updated
from session
order by time_updated desc;
```

## Practical message shape

Keep alerts terse and actionable:

- `OpenCode needs authorization`
- session title
- session id
- tool/command if available
- working directory
- observed timestamp

And for completion:

- `OpenCode finished a task loop` or `OpenCode session went idle after work`
- session title
- session id
- working directory
- finished/last-update timestamp

## Pitfalls

- Do not emit on the first watchdog run. Bootstrap the cursor state and stay silent.
- Do not assume every finished session writes a fresh `exiting loop` line.
- Do not assume authorization events have a dedicated structured table; string-match in `part.data` was the durable signal found here.
- Cron `script` must be passed as a filename relative to `~/.hermes/scripts/`, not an absolute path.
- Telegram delivery needs a valid target such as `telegram:<user_id>`.
