#!/usr/bin/env bash
set -euo pipefail
python3 "$HOME/.hermes/scripts/opencode_telegram_bridge.py" launch "$@"
