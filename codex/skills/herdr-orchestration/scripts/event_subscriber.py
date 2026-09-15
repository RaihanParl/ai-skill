#!/usr/bin/env python3
"""Herdr event subscriber (shared by the recorder and the pinger).

Connects to the Herdr unix socket, subscribes to pane.agent_status_changed for
each watched pane, and prints matching events as newline-delimited JSON, then
exits after SILENCE seconds with no new event. With HERDR_CLOSED set it also
subscribes to pane.closed so dead panes are recorded.

IMPORTANT: the server resets the whole connection if any one subscription is
rejected (e.g. a pane that no longer exists). So before connecting we resolve
the pane set against the live 'herdr pane list' output and drop any pane that is
not present. That keeps a vanished pane from killing the entire tap.

Usage:
    event_subscriber.py [silence_seconds]

Environment:
    HERDR_SOCKET_PATH  unix socket path (default: ~/.config/herdr/herdr.sock)
    HERDR_PANES        space-separated pane IDs, or "live" for every pane
                       currently reported by 'herdr pane list' (default: live)
    HERDR_WANT         space-separated statuses to match (default: done blocked)
    HERDR_CLOSED        any non-empty value also subscribes to pane.closed
"""
import json
import os
import socket
import subprocess
import sys

SOCK = os.environ.get("HERDR_SOCKET_PATH", os.path.expanduser("~/.config/herdr/herdr.sock"))
WANT = tuple(os.environ.get("HERDR_WANT", "done blocked").split())
CLOSED = bool(os.environ.get("HERDR_CLOSED"))
SILENCE = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0


def live_panes():
    try:
        out = subprocess.run(
            ["herdr", "pane", "list"],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(out.stdout)
        return [p["pane_id"] for p in data.get("result", {}).get("panes", [])]
    except Exception:
        return []


raw = os.environ.get("HERDR_PANES", "live")
if raw.strip().lower() == "live":
    PANES = live_panes()
else:
    PANES = raw.split()

if not PANES:
    sys.stderr.write("no panes to watch\n")
    sys.exit(0)

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(15)
s.connect(SOCK)


def send(sub_type, pane_id, idx):
    req = {
        "id": "sub_%d" % idx,
        "method": "events.subscribe",
        "params": {"subscriptions": [{"type": sub_type, "pane_id": pane_id}]},
    }
    s.sendall((json.dumps(req) + "\n").encode())


for i, p in enumerate(PANES):
    send("pane.agent_status_changed", p, i)
    if CLOSED:
        send("pane.closed", p, i + 1000)

buf = b""
ack = False
s.settimeout(SILENCE)
try:
    while True:
        try:
            chunk = s.recv(65536)
        except (ConnectionResetError, OSError):
            # Server dropped the connection (rejected subscription, socket gone).
            # Exit cleanly so the caller can reconnect.
            break
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if not ack:
                # First frames are the subscription acks; skip them.
                ack = True
                continue
            if isinstance(msg, dict) and "error" in msg:
                # A rejected subscription is reported as an error frame; skip.
                continue
            d = msg.get("data", {}) if isinstance(msg, dict) else {}
            etype = msg.get("event")
            pane = d.get("pane_id")
            if etype == "pane.closed":
                if pane in PANES:
                    print(json.dumps(msg), flush=True)
                continue
            if pane in PANES and d.get("agent_status") in WANT:
                print(json.dumps(msg), flush=True)
except socket.timeout:
    pass
