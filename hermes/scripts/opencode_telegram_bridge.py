#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shlex
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request

HOME = Path.home()
ENV_PATH = Path(os.environ.get('OPENCODE_BRIDGE_ENV_PATH', HOME / '.hermes' / '.env')).expanduser()
HERMES_DB = Path(os.environ.get('OPENCODE_BRIDGE_HERMES_DB', HOME / '.hermes' / 'state.db')).expanduser()
STATE_DIR = Path(os.environ.get('OPENCODE_BRIDGE_STATE_DIR', HOME / '.hermes' / 'scripts' / 'state')).expanduser()
STATE_PATH = STATE_DIR / 'opencode-telegram-bridge.json'
LOG_DIR = STATE_DIR / 'opencode-bridge-logs'
BRIDGE_PREFIX = 'ocb_'
MAX_EXCERPT_LINES = 18
KEYWORDS = [
    'permission', 'approve', 'approval', 'authorize', 'authorization',
    'allow', 'deny', 'question', 'which one', 'continue?', 'continue ?',
    'waiting for authorization'
]
BRIDGE_RE = re.compile(r'\[bridge:([a-z0-9_-]+)\]', re.I)
SIMPLE_REPLY_RE = re.compile(r'^(approve|deny|stop)$', re.I)
SEND_REPLY_RE = re.compile(r'^(?:send:|answer:|reply:)\s*(.+)$', re.I | re.S)
KEY_REPLY_RE = re.compile(r'^key:\s*(.+)$', re.I)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def load_env():
    data = {}
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            data[k] = v
    return data


def load_config():
    env = load_env()
    token = env.get('TELEGRAM_BOT_TOKEN', '').strip()
    allowed = [x.strip() for x in env.get('TELEGRAM_ALLOWED_USERS', '').split(',') if x.strip()]
    if not token:
        raise SystemExit('Missing TELEGRAM_BOT_TOKEN in ~/.hermes/.env')
    if not allowed:
        raise SystemExit('Missing TELEGRAM_ALLOWED_USERS in ~/.hermes/.env')
    return {
        'token': token,
        'allowed_users': allowed,
        'default_chat_id': allowed[0],
    }


def current_telegram_max_message_id(allowed_users):
    if not HERMES_DB.exists():
        return 0
    conn = sqlite3.connect(str(HERMES_DB))
    placeholders = ','.join('?' for _ in allowed_users)
    row = conn.execute(
        f"""
        select coalesce(max(m.id), 0)
        from messages m
        join sessions s on s.id = m.session_id
        where s.source='telegram' and s.user_id in ({placeholders}) and m.role='user'
        """,
        allowed_users,
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def load_state(config):
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {
        'telegram_last_db_message_id': current_telegram_max_message_id(config['allowed_users']),
        'sessions': {},
    }


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def tg_api(config, method, payload=None):
    payload = payload or {}
    data = parse.urlencode(payload).encode()
    req = request.Request(
        f"https://api.telegram.org/bot{config['token']}/{method}",
        data=data,
        method='POST',
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def tg_send(config, chat_id, text, reply_to_message_id=None):
    payload = {'chat_id': str(chat_id), 'text': text, 'disable_web_page_preview': 'true'}
    if reply_to_message_id:
        payload['reply_to_message_id'] = str(reply_to_message_id)
    result = tg_api(config, 'sendMessage', payload)
    if not result.get('ok'):
        raise RuntimeError(f'Telegram send failed: {result}')
    return result['result']


def run(*args, check=True, capture=True):
    return subprocess.run(
        list(args),
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def tmux_has(session_name):
    proc = subprocess.run(['tmux', 'has-session', '-t', session_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0


def tmux_capture(session_name, start='-120'):
    proc = run('tmux', 'capture-pane', '-p', '-t', session_name, '-S', str(start))
    return proc.stdout


def tmux_send_text(session_name, text, submit=False):
    run('tmux', 'send-keys', '-t', session_name, '-l', text)
    if submit:
        run('tmux', 'send-keys', '-t', session_name, 'Enter')


def tmux_send_key(session_name, key):
    run('tmux', 'send-keys', '-t', session_name, key)


def make_bridge_id(state):
    base = datetime.now().strftime('%m%d%H%M%S')
    suffix = 1
    bridge_id = base
    while bridge_id in state['sessions']:
        suffix += 1
        bridge_id = f'{base}-{suffix}'
    return bridge_id


def extract_bridge_id(text):
    if not text:
        return None
    m = BRIDGE_RE.search(text)
    return m.group(1) if m else None


def key_alias(name):
    mapping = {
        'enter': 'Enter',
        'escape': 'Escape',
        'esc': 'Escape',
        'up': 'Up',
        'down': 'Down',
        'left': 'Left',
        'right': 'Right',
        'tab': 'Tab',
        'ctrl-c': 'C-c',
        'c-c': 'C-c',
        'space': 'Space',
        'y': 'y',
        'n': 'n',
    }
    return mapping.get(name.lower(), name)


def choose_bridge_id(state):
    waiting = [bid for bid, s in state['sessions'].items() if s.get('status') == 'waiting_input' and tmux_has(s['tmux_session'])]
    if len(waiting) == 1:
        return waiting[0]
    running = [bid for bid, s in state['sessions'].items() if s.get('status') in {'running', 'waiting_input'} and tmux_has(s['tmux_session'])]
    if len(running) == 1:
        return running[0]
    return None


def launch_opencode(state, config, directory, prompt=None, title=None, model=None, agent=None):
    bridge_id = make_bridge_id(state)
    session_name = f'{BRIDGE_PREFIX}{bridge_id}'
    log_path = LOG_DIR / f'{bridge_id}.log'
    directory = str(Path(directory).expanduser().resolve())
    cmd = f'cd {shlex.quote(directory)} && exec opencode'
    if model:
        cmd += f' --model {shlex.quote(model)}'
    if agent:
        cmd += f' --agent {shlex.quote(agent)}'
    run('tmux', 'new-session', '-d', '-s', session_name, cmd)
    run('tmux', 'pipe-pane', '-o', '-t', session_name, f'cat >> {shlex.quote(str(log_path))}')
    time.sleep(4)
    if prompt:
        tmux_send_text(session_name, prompt, submit=True)
    state['sessions'][bridge_id] = {
        'bridge_id': bridge_id,
        'tmux_session': session_name,
        'directory': directory,
        'title': title or f'OpenCode {bridge_id}',
        'kind': 'opencode',
        'status': 'running',
        'created_at': now_iso(),
        'last_notified_hash': '',
        'last_notified_at': '',
        'last_seen_running': True,
        'reply_target_chat_id': config['default_chat_id'],
        'last_bot_message_id': None,
        'log_path': str(log_path),
    }
    save_state(state)
    msg = (
        f'OpenCode bridge started\n'
        f'[bridge:{bridge_id}]\n'
        f'- tmux: {session_name}\n'
        f'- dir: {directory}\n\n'
        f'From Telegram, send either:\n'
        f'- approve\n'
        f'- deny\n'
        f'- stop\n'
        f'- send: <text>\n'
        f'- key: enter|y|n|escape|up|down|tab|ctrl-c\n\n'
        f'If more than one bridge is active, use /oc help for explicit commands.'
    )
    sent = tg_send(config, config['default_chat_id'], msg)
    state['sessions'][bridge_id]['last_bot_message_id'] = sent['message_id']
    save_state(state)
    return bridge_id


def register_tmux(state, config, session_name, directory='.', title=None, kind='generic'):
    if not tmux_has(session_name):
        raise SystemExit(f'tmux session not found: {session_name}')
    bridge_id = make_bridge_id(state)
    directory = str(Path(directory).expanduser().resolve())
    log_path = LOG_DIR / f'{bridge_id}.log'
    run('tmux', 'pipe-pane', '-o', '-t', session_name, f'cat >> {shlex.quote(str(log_path))}')
    state['sessions'][bridge_id] = {
        'bridge_id': bridge_id,
        'tmux_session': session_name,
        'directory': directory,
        'title': title or f'{kind} {bridge_id}',
        'kind': kind,
        'status': 'running',
        'created_at': now_iso(),
        'last_notified_hash': '',
        'last_notified_at': '',
        'last_seen_running': True,
        'reply_target_chat_id': config['default_chat_id'],
        'last_bot_message_id': None,
        'log_path': str(log_path),
    }
    save_state(state)
    sent = tg_send(
        config,
        config['default_chat_id'],
        f'Bridge attached\n[bridge:{bridge_id}]\n- tmux: {session_name}\n- dir: {directory}\n- kind: {kind}',
    )
    state['sessions'][bridge_id]['last_bot_message_id'] = sent['message_id']
    save_state(state)
    return bridge_id


def send_control(state, config, bridge_id, action, value='', chat_id=None):
    session = state['sessions'].get(bridge_id)
    if not session:
        raise SystemExit(f'Unknown bridge id: {bridge_id}')
    session_name = session['tmux_session']
    if not tmux_has(session_name):
        session['status'] = 'exited'
        save_state(state)
        raise SystemExit(f'tmux session is not running: {session_name}')

    action = action.lower()
    if action == 'approve':
        tmux_send_key(session_name, 'y')
        tmux_send_key(session_name, 'Enter')
        ack = f'Approved [bridge:{bridge_id}]'
    elif action == 'deny':
        tmux_send_key(session_name, 'n')
        tmux_send_key(session_name, 'Enter')
        ack = f'Denied [bridge:{bridge_id}]'
    elif action == 'send':
        tmux_send_text(session_name, value, submit=True)
        ack = f'Sent to [bridge:{bridge_id}]: {value[:120]}'
    elif action == 'text':
        tmux_send_text(session_name, value, submit=False)
        ack = f'Typed into [bridge:{bridge_id}]: {value[:120]}'
    elif action == 'key':
        tmux_send_key(session_name, key_alias(value))
        ack = f'Sent key to [bridge:{bridge_id}]: {value}'
    elif action == 'stop':
        tmux_send_key(session_name, 'C-c')
        ack = f'Sent Ctrl+C to [bridge:{bridge_id}]'
    else:
        raise SystemExit(f'Unsupported action: {action}')

    session['status'] = 'running'
    if chat_id:
        sent = tg_send(config, chat_id, ack)
        session['last_bot_message_id'] = sent['message_id']
    save_state(state)
    return ack


def list_bridges(state):
    rows = []
    for bridge_id, session in sorted(state['sessions'].items()):
        active = 'up' if tmux_has(session['tmux_session']) else 'down'
        rows.append(
            f"[bridge:{bridge_id}] {session['status']} ({active}) tmux={session['tmux_session']} dir={session['directory']} title={session['title']}"
        )
    return '\n'.join(rows) if rows else 'No bridged sessions.'


def tail_excerpt(text):
    clean = '\n'.join(line.rstrip() for line in text.splitlines() if line.strip())
    lines = clean.splitlines()[-MAX_EXCERPT_LINES:]
    return '\n'.join(lines).strip()


def looks_actionable(excerpt):
    lower = excerpt.lower()
    return any(word in lower for word in KEYWORDS)


def fetch_new_telegram_messages(state, allowed_users):
    if not HERMES_DB.exists():
        return []
    conn = sqlite3.connect(str(HERMES_DB))
    placeholders = ','.join('?' for _ in allowed_users)
    rows = conn.execute(
        f"""
        select m.id, s.user_id, m.content
        from messages m
        join sessions s on s.id = m.session_id
        where s.source='telegram'
          and s.user_id in ({placeholders})
          and m.role='user'
          and m.id > ?
        order by m.id asc
        """,
        [*allowed_users, int(state.get('telegram_last_db_message_id', 0))],
    ).fetchall()
    conn.close()
    return rows


def handle_text_command(state, config, chat_id, text):
    text = (text or '').strip()
    if not text:
        return False

    if text.startswith('/oc'):
        parts = text.split(maxsplit=3)
        cmd = parts[1] if len(parts) > 1 else 'help'
        if cmd == 'list':
            tg_send(config, chat_id, list_bridges(state))
            return True
        if cmd == 'help':
            tg_send(
                config,
                chat_id,
                '/oc list\n/oc approve <bridge>\n/oc deny <bridge>\n/oc send <bridge> <text>\n/oc key <bridge> <key>\n/oc stop <bridge>\n\nIf only one bridge is active, you can also just send: approve, deny, stop, send: ..., key: ...',
            )
            return True
        if cmd in {'approve', 'deny', 'stop'}:
            bridge_id = parts[2] if len(parts) > 2 else choose_bridge_id(state)
            if not bridge_id:
                tg_send(config, chat_id, 'Need a bridge id. Use /oc list.')
                return True
            send_control(state, config, bridge_id, cmd, chat_id=chat_id)
            return True
        if cmd in {'send', 'key'}:
            if len(parts) < 4:
                tg_send(config, chat_id, f'Usage: /oc {cmd} <bridge> <value>')
                return True
            bridge_id, value = parts[2], parts[3]
            send_control(state, config, bridge_id, cmd, value=value, chat_id=chat_id)
            return True
        tg_send(config, chat_id, f'Unknown /oc command: {cmd}')
        return True

    m = SIMPLE_REPLY_RE.match(text)
    if m:
        bridge_id = choose_bridge_id(state)
        if not bridge_id:
            return False
        send_control(state, config, bridge_id, m.group(1).lower(), chat_id=chat_id)
        return True

    m = SEND_REPLY_RE.match(text)
    if m:
        bridge_id = choose_bridge_id(state)
        if not bridge_id:
            return False
        send_control(state, config, bridge_id, 'send', value=m.group(1).strip(), chat_id=chat_id)
        return True

    m = KEY_REPLY_RE.match(text)
    if m:
        bridge_id = choose_bridge_id(state)
        if not bridge_id:
            return False
        send_control(state, config, bridge_id, 'key', value=m.group(1).strip(), chat_id=chat_id)
        return True

    return False


def process_inbound_commands(state, config):
    rows = fetch_new_telegram_messages(state, config['allowed_users'])
    for msg_id, user_id, content in rows:
        state['telegram_last_db_message_id'] = int(msg_id)
        handle_text_command(state, config, user_id, content)
    if rows:
        save_state(state)


def inspect_sessions(state, config):
    changed = False
    for bridge_id, session in list(state['sessions'].items()):
        session_name = session['tmux_session']
        running = tmux_has(session_name)
        if running:
            excerpt = tail_excerpt(tmux_capture(session_name))
            digest = hashlib.sha1(excerpt.encode()).hexdigest() if excerpt else ''
            if excerpt and looks_actionable(excerpt) and digest != session.get('last_notified_hash'):
                body = (
                    f'OpenCode may need input\n'
                    f'[bridge:{bridge_id}]\n'
                    f'- tmux: {session_name}\n'
                    f'- dir: {session["directory"]}\n\n'
                    f'{excerpt[-3500:]}\n\n'
                    f'Reply with approve, deny, stop, send: <text>, or key: <key>. If several bridges are active, use /oc list.'
                )
                sent = tg_send(config, session['reply_target_chat_id'], body)
                session['last_bot_message_id'] = sent['message_id']
                session['last_notified_hash'] = digest
                session['last_notified_at'] = now_iso()
                session['status'] = 'waiting_input'
                changed = True
            elif session.get('status') != 'waiting_input':
                session['status'] = 'running'
            session['last_seen_running'] = True
        else:
            if session.get('last_seen_running'):
                excerpt = ''
                try:
                    excerpt = tail_excerpt(Path(session['log_path']).read_text(errors='ignore'))
                except Exception:
                    pass
                body = (
                    f'Bridged session exited\n'
                    f'[bridge:{bridge_id}]\n'
                    f'- tmux: {session_name}\n'
                    f'- dir: {session["directory"]}\n\n'
                    f'{excerpt[-3500:] if excerpt else "(no captured output)"}'
                )
                sent = tg_send(config, session['reply_target_chat_id'], body)
                session['last_bot_message_id'] = sent['message_id']
                session['last_seen_running'] = False
                session['status'] = 'exited'
                changed = True
    if changed:
        save_state(state)


def cmd_tick(args):
    config = load_config()
    state = load_state(config)
    process_inbound_commands(state, config)
    inspect_sessions(state, config)


def cmd_launch(args):
    config = load_config()
    state = load_state(config)
    bridge_id = launch_opencode(state, config, args.dir, prompt=args.prompt, title=args.title, model=args.model, agent=args.agent)
    print(bridge_id)


def cmd_register(args):
    config = load_config()
    state = load_state(config)
    bridge_id = register_tmux(state, config, args.tmux_session, directory=args.dir, title=args.title, kind=args.kind)
    print(bridge_id)


def cmd_send(args):
    config = load_config()
    state = load_state(config)
    print(send_control(state, config, args.bridge, args.action, value=args.value or ''))


def cmd_list(args):
    config = load_config()
    state = load_state(config)
    print(list_bridges(state))


def cmd_notify(args):
    config = load_config()
    result = tg_send(config, config['default_chat_id'], args.message)
    print(result['message_id'])


def build_parser():
    p = argparse.ArgumentParser(description='Telegram bridge for tmux-managed OpenCode sessions')
    sub = p.add_subparsers(dest='cmd', required=True)

    tick = sub.add_parser('tick')
    tick.set_defaults(func=cmd_tick)

    launch = sub.add_parser('launch')
    launch.add_argument('--dir', required=True)
    launch.add_argument('--prompt')
    launch.add_argument('--title')
    launch.add_argument('--model')
    launch.add_argument('--agent')
    launch.set_defaults(func=cmd_launch)

    reg = sub.add_parser('register')
    reg.add_argument('--tmux-session', required=True)
    reg.add_argument('--dir', default='.')
    reg.add_argument('--title')
    reg.add_argument('--kind', default='generic')
    reg.set_defaults(func=cmd_register)

    send = sub.add_parser('send')
    send.add_argument('--bridge', required=True)
    send.add_argument('--action', required=True, choices=['approve', 'deny', 'send', 'text', 'key', 'stop'])
    send.add_argument('--value')
    send.set_defaults(func=cmd_send)

    ls = sub.add_parser('list')
    ls.set_defaults(func=cmd_list)

    note = sub.add_parser('notify-test')
    note.add_argument('message')
    note.set_defaults(func=cmd_notify)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
