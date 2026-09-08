#!/usr/bin/env python3
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
DB_PATH = Path(os.environ.get('HERMES_SESSION_MONITOR_DB', HOME / '.hermes' / 'state.db'))
STATE_PATH = Path(os.environ.get('HERMES_SESSION_MONITOR_STATE', HOME / '.hermes' / 'scripts' / 'state' / 'hermes-session-monitor.json'))
MAX_NOTIFICATIONS = int(os.environ.get('HERMES_SESSION_MONITOR_MAX_NOTIFICATIONS', '6'))
MAX_SUMMARY_CHARS = int(os.environ.get('HERMES_SESSION_MONITOR_MAX_SUMMARY_CHARS', '220'))

QUESTION_HINTS = (
    'please confirm',
    'need your confirmation',
    'confirm whether',
    'can you confirm',
    'should i',
    'would you like',
    'do you want',
    'shall i',
    'want me to',
    'let me know if',
    'is this okay',
    'can i proceed',
    'waiting for confirmation',
    'reply with',
)


def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {
        'initialized': False,
        'last_ended_key': [0, ''],
    }


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def latest_ended_key(conn):
    row = conn.execute(
        """
        select ended_at, id
        from sessions
        where ended_at is not null and source != 'telegram'
        order by ended_at desc, id desc
        limit 1
        """
    ).fetchone()
    return [row[0], row[1]] if row else [0, '']


def fetch_finished_sessions(conn, last_key):
    return conn.execute(
        """
        select id, source, title, cwd, ended_at, end_reason
        from sessions
        where ended_at is not null
          and source != 'telegram'
          and (ended_at > ? or (ended_at = ? and id > ?))
        order by ended_at asc, id asc
        """,
        (last_key[0], last_key[0], last_key[1]),
    ).fetchall()


def fetch_last_message(conn, session_id):
    rows = conn.execute(
        """
        select role,
               coalesce(content, ''),
               coalesce(reasoning_content, ''),
               coalesce(reasoning, '')
        from messages
        where session_id = ?
        order by id desc
        limit 60
        """,
        (session_id,),
    ).fetchall()

    for role, content, reasoning_content, reasoning in rows:
        text = content or reasoning_content or reasoning
        if role == 'assistant' and text.strip():
            return text.strip()

    for role, content, reasoning_content, reasoning in rows:
        text = content or reasoning_content or reasoning
        if text.strip():
            return text.strip()

    return ''


def compact_text(text):
    lines = [line.strip('•-* \t') for line in text.splitlines() if line.strip()]
    candidate = lines[0] if lines else ' '.join(text.split())
    candidate = re.split(r'(?<=[.!?])\s+', candidate, maxsplit=1)[0]
    candidate = ' '.join(candidate.split())
    if len(candidate) > MAX_SUMMARY_CHARS:
        candidate = candidate[: MAX_SUMMARY_CHARS - 1] + '…'
    return candidate or '(no message text)'


def needs_confirmation(text):
    lower = text.lower()
    if '?' in text:
        return True
    return any(hint in lower for hint in QUESTION_HINTS)


def fmt_when(ms):
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone()
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def build_notice(row, last_message):
    session_id, source, title, cwd, ended_at, end_reason = row
    summary = compact_text(last_message)
    status = 'needs confirmation' if needs_confirmation(last_message) else 'complete'
    lines = [
        'Hermes session finished',
        f'- session: {title or "(untitled session)"}',
        f'- id: {session_id}',
        f'- status: {status}',
        f'- last: {summary}',
        f'- ended: {fmt_when(ended_at)}',
    ]
    if cwd:
        lines.append(f'- dir: {cwd}')
    if end_reason:
        lines.append(f'- end reason: {end_reason}')
    return '\n'.join(lines)


def main():
    state = load_state()
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(str(DB_PATH))
    latest_key = latest_ended_key(conn)

    if not state.get('initialized'):
        state['initialized'] = True
        state['last_ended_key'] = latest_key
        save_state(state)
        return

    last_key = tuple(state.get('last_ended_key', [0, '']))
    rows = fetch_finished_sessions(conn, last_key)
    if not rows:
        state['last_ended_key'] = latest_key
        save_state(state)
        return

    notices = []
    new_last_key = list(last_key)
    for row in rows:
        session_id = row[0]
        last_message = fetch_last_message(conn, session_id)
        notices.append(build_notice(row, last_message))
        new_last_key = [row[4], row[0]]

    state['last_ended_key'] = new_last_key
    save_state(state)

    print('\n\n'.join(notices[:MAX_NOTIFICATIONS]))


if __name__ == '__main__':
    main()
