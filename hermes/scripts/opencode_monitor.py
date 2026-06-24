#!/usr/bin/env python3
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
DB_PATH = Path(os.environ.get('OPENCODE_MONITOR_DB', HOME / '.local/share/opencode/opencode.db'))
LOG_PATH = Path(os.environ.get('OPENCODE_MONITOR_LOG', HOME / '.local/share/opencode/log/opencode.log'))
STATE_PATH = Path(os.environ.get('OPENCODE_MONITOR_STATE', HOME / '.hermes/scripts/state/opencode-monitor.json'))
MAX_LINES = int(os.environ.get('OPENCODE_MONITOR_MAX_LINES', '6'))
QUIET_SECONDS = int(os.environ.get('OPENCODE_MONITOR_QUIET_SECONDS', '45'))

EXIT_RE = re.compile(r'^timestamp=(?P<ts>\S+) .*message="exiting loop" session\.id=(?P<sid>\S+)')


def iso_to_ms(ts: str) -> int:
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return int(datetime.fromisoformat(ts).astimezone(timezone.utc).timestamp() * 1000)


def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {
        'initialized': False,
        'last_permission_key': [0, ''],
        'last_exit_key': [0, ''],
        'last_session_update_key': [0, ''],
    }


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def fetch_titles(conn, session_ids):
    if not session_ids:
        return {}
    placeholders = ','.join('?' for _ in session_ids)
    rows = conn.execute(
        f"select id, title, directory from session where id in ({placeholders})",
        list(session_ids),
    ).fetchall()
    return {row[0]: {'title': row[1], 'directory': row[2]} for row in rows}


def fetch_permission_events(conn):
    return conn.execute(
        """
        select p.id, p.session_id, p.time_created,
               coalesce(json_extract(p.data, '$.state.metadata.output'), '') as output,
               coalesce(json_extract(p.data, '$.state.input.command'), '') as command,
               coalesce(json_extract(p.data, '$.tool'), '') as tool_name
        from part p
        where p.data like '%Waiting for authorization%'
        order by p.time_created asc, p.id asc
        """
    ).fetchall()


def fetch_exit_events():
    events = []
    if not LOG_PATH.exists():
        return events
    for line in LOG_PATH.read_text(errors='ignore').splitlines():
        m = EXIT_RE.search(line)
        if not m:
            continue
        ts_ms = iso_to_ms(m.group('ts'))
        sid = m.group('sid')
        events.append((ts_ms, sid))
    events.sort()
    return events


def fetch_session_updates(conn, quiet_before_ms):
    return conn.execute(
        """
        select id, title, directory, time_updated
        from session
        where time_updated <= ?
        order by time_updated asc, id asc
        """,
        (quiet_before_ms,),
    ).fetchall()


def latest_session_key(conn):
    row = conn.execute(
        "select time_updated, id from session order by time_updated desc, id desc limit 1"
    ).fetchone()
    return [row[0], row[1]] if row else [0, '']


def fmt_when(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone()
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def summarize_command(cmd: str) -> str:
    cmd = ' '.join(cmd.split())
    if len(cmd) > 120:
        cmd = cmd[:117] + '...'
    return cmd


def main():
    state = load_state()
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(str(DB_PATH))
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    quiet_before_ms = now_ms - QUIET_SECONDS * 1000

    permission_events = fetch_permission_events(conn)
    exit_events = fetch_exit_events()
    session_updates = fetch_session_updates(conn, quiet_before_ms)

    latest_permission_key = list(max(((row[2], row[0]) for row in permission_events), default=(0, '')))
    latest_exit_key = list(max(((row[0], row[1]) for row in exit_events), default=(0, '')))
    latest_session_update_key = latest_session_key(conn)

    if not state.get('initialized'):
        state['initialized'] = True
        state['last_permission_key'] = latest_permission_key
        state['last_exit_key'] = latest_exit_key
        state['last_session_update_key'] = latest_session_update_key
        save_state(state)
        return

    if 'last_session_update_key' not in state:
        state['last_session_update_key'] = latest_session_update_key
        save_state(state)
        return

    last_permission_key = tuple(state.get('last_permission_key', [0, '']))
    last_exit_key = tuple(state.get('last_exit_key', [0, '']))
    last_session_update_key = tuple(state.get('last_session_update_key', [0, '']))

    new_permissions = [row for row in permission_events if (row[2], row[0]) > last_permission_key]
    new_exits = [row for row in exit_events if (row[0], row[1]) > last_exit_key]
    new_session_updates = [row for row in session_updates if (row[3], row[0]) > last_session_update_key]

    exit_session_ids = {sid for _, sid in new_exits}
    filtered_session_updates = [row for row in new_session_updates if row[0] not in exit_session_ids]

    session_ids = {row[1] for row in new_permissions} | exit_session_ids | {row[0] for row in filtered_session_updates}
    titles = fetch_titles(conn, session_ids)

    lines = []
    for part_id, session_id, time_created, output, command, tool_name in new_permissions:
        meta = titles.get(session_id, {})
        title = meta.get('title') or '(untitled session)'
        directory = meta.get('directory') or ''
        command_summary = summarize_command(command) if command else 'authorization flow pending'
        lines.append(
            f"OpenCode needs authorization\n"
            f"- session: {title}\n"
            f"- id: {session_id}\n"
            f"- tool: {tool_name or 'unknown'}\n"
            f"- command: {command_summary}\n"
            f"- dir: {directory}\n"
            f"- seen: {fmt_when(time_created)}"
        )

    for ts_ms, session_id in new_exits:
        meta = titles.get(session_id, {})
        title = meta.get('title') or '(untitled session)'
        directory = meta.get('directory') or ''
        lines.append(
            f"OpenCode finished a task loop\n"
            f"- session: {title}\n"
            f"- id: {session_id}\n"
            f"- dir: {directory}\n"
            f"- finished: {fmt_when(ts_ms)}"
        )

    for session_id, title, directory, time_updated in filtered_session_updates:
        lines.append(
            f"OpenCode session went idle after work\n"
            f"- session: {title or '(untitled session)'}\n"
            f"- id: {session_id}\n"
            f"- dir: {directory or ''}\n"
            f"- last update: {fmt_when(time_updated)}"
        )

    state['last_permission_key'] = latest_permission_key
    state['last_exit_key'] = latest_exit_key
    state['last_session_update_key'] = latest_session_update_key
    save_state(state)

    if not lines:
        return

    print('\n\n'.join(lines[:MAX_LINES]))


if __name__ == '__main__':
    main()
