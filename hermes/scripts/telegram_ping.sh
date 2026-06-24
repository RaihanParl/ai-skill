#!/usr/bin/env bash
set -euo pipefail

host="$(hostname 2>/dev/null || echo unknown-host)"
when="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
printf 'Hermes ping: %s @ %s\n' "$host" "$when"
