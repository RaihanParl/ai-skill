#!/usr/bin/env python3
"""Herdr event subscriber.

Subscribes to pane.agent_status_changed for the given panes over the
$HERDR_SOCKET_PATH unix socket and prints matching events as newline-delimited
JSON, then exits after N seconds of silence. This is the lossless record used
by both the recorder and pinger loops in the herdr-orchestration skill.

Usage:
    event_subscriber.py [silence_seconds]

Environment:
    HERDR_SOCKET_PATH  unix socket path (required)
    HERDR_PANES        space-separated pane IDs to watch
                        (default: w1:p1H w1:p1K)
    HERDR_WANT         space-separated statuses to match
                        (default: done blocked)
"""
import json
import os
import socket
import sys

SOCK = os.environ.get("HERDR_SOCKET_PATH")
if not SOCK:
    sys.stderr.write("HERDR_SOCKET_PATH is not set\n")
    sys.exit(2)

PANES = set(os.environ.get("HERDR_PANES", "w1:p1H w1:p1K").split())
WANT = tuple(os.environ.get("HERDR_WANT", "done blocked").split())
SILENCE = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0

req = {
    "id": "sub_ping",
    "method": "events.subscribe",
    "params": {
        "subscriptions": [
            {"type": "pane.agent_status_changed", "pane_id": p} for p in PANES
        ]
    },
}

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(15)
s.connect(SOCK)
s.sendall((json.dumps(req) + "\n").encode())

buf = b""
ack = False
s.settimeout(SILENCE)
try:
    while True:
        chunk = s.recv(65536)
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
                ack = True
                continue
            d = msg.get("data", {}) if isinstance(msg, dict) else {}
            if d.get("pane_id") in PANES and d.get("agent_status") in WANT:
                print(json.dumps(msg), flush=True)
except socket.timeout:
    pass
