#!/usr/bin/env bash
set -euo pipefail

SOURCE_HOME="${SOURCE_HOME:-$HOME}"
OUTPUT_PATH="${1:-${OUTPUT_PATH:-$PWD/hermes-stack-$(date -u +%Y%m%dT%H%M%SZ).tar.gz}}"
INCLUDE_SECRETS="${INCLUDE_SECRETS:-0}"
INCLUDE_SESSIONS="${INCLUDE_SESSIONS:-0}"
INCLUDE_OPENCODE_CACHE="${INCLUDE_OPENCODE_CACHE:-1}"
DRY_RUN="${DRY_RUN:-0}"

python3 - "$SOURCE_HOME" "$OUTPUT_PATH" "$INCLUDE_SECRETS" "$INCLUDE_SESSIONS" "$INCLUDE_OPENCODE_CACHE" "$DRY_RUN" <<'PY'
from __future__ import annotations

import json
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

source_home = Path(sys.argv[1]).expanduser().resolve()
output_path = Path(sys.argv[2]).expanduser().resolve()
include_secrets = sys.argv[3] == "1"
include_sessions = sys.argv[4] == "1"
include_opencode_cache = sys.argv[5] == "1"
dry_run = sys.argv[6] == "1"

base_paths = [
    (source_home / ".hermes" / "config.yaml", Path("hermes/config.yaml")),
    (source_home / ".hermes" / "memories", Path("hermes/memories")),
    (source_home / ".hermes" / "profiles", Path("hermes/profiles")),
    (source_home / ".hermes" / "skills", Path("hermes/skills")),
    (source_home / ".hermes" / "plugins", Path("hermes/plugins")),
    (source_home / ".hermes" / "scripts", Path("hermes/scripts")),
    (source_home / ".config" / "opencode" / "opencode.jsonc", Path("opencode/opencode.jsonc")),
    (source_home / ".config" / "opencode" / "AGENTS.md", Path("opencode/AGENTS.md")),
    (source_home / ".config" / "opencode" / "agents", Path("opencode/agents")),
    (source_home / ".config" / "opencode" / "commands", Path("opencode/commands")),
    (source_home / ".config" / "opencode" / "skills", Path("opencode/skills")),
    (source_home / ".cursor" / "rules", Path("cursor/rules")),
]
if include_opencode_cache:
    base_paths.insert(7, (source_home / ".config" / "opencode" / "opencode.json", Path("opencode/opencode.json")))
if include_sessions:
    base_paths.extend([
        (source_home / ".hermes" / "sessions", Path("hermes/sessions")),
        (source_home / ".hermes" / "state.db", Path("hermes/state.db")),
    ])
if include_secrets:
    base_paths.extend([
        (source_home / ".hermes" / ".env", Path("hermes/.env")),
        (source_home / ".hermes" / "auth.json", Path("hermes/auth.json")),
    ])

if dry_run:
    print(f"would create: {output_path}")
    for src, rel in base_paths:
        if src.exists():
            print(f"[dry-run] {src} -> {rel}")
    raise SystemExit(0)

with tempfile.TemporaryDirectory(prefix="ai-skill-hermes-export-") as tmp:
    staging = Path(tmp) / "bundle"
    staging.mkdir(parents=True, exist_ok=True)

    copied = []
    for src, rel in base_paths:
        if not src.exists():
            continue
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        copied.append({"source": str(src), "target": str(dst.relative_to(staging))})

    manifest = {
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_home": str(source_home),
        "include_secrets": include_secrets,
        "include_sessions": include_sessions,
        "include_opencode_cache": include_opencode_cache,
        "files": copied,
    }
    (staging / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as tf:
        tf.add(staging, arcname=".")

print(output_path)
PY
