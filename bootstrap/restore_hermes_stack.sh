#!/usr/bin/env bash
set -euo pipefail

BUNDLE_PATH="${1:-${BUNDLE_PATH:-}}"
TARGET_HOME="${TARGET_HOME:-$HOME}"
DRY_RUN="${DRY_RUN:-0}"
FORCE="${FORCE:-0}"

if [ -z "$BUNDLE_PATH" ]; then
  printf 'usage: %s <bundle.tar.gz>\n' "$0" >&2
  exit 1
fi

python3 - "$BUNDLE_PATH" "$TARGET_HOME" "$DRY_RUN" "$FORCE" <<'PY'
from __future__ import annotations

import json
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

bundle_path = Path(sys.argv[1]).expanduser().resolve()
target_home = Path(sys.argv[2]).expanduser().resolve()
dry_run = sys.argv[3] == "1"
force = sys.argv[4] == "1"

if not bundle_path.exists():
    raise SystemExit(f"bundle not found: {bundle_path}")

restore_plan = []
with tarfile.open(bundle_path, "r:gz") as tf:
    with tempfile.TemporaryDirectory(prefix="ai-skill-hermes-restore-") as tmp:
        extract_dir = Path(tmp) / "bundle"
        extract_dir.mkdir(parents=True, exist_ok=True)
        tf.extractall(extract_dir)
        manifest_path = extract_dir / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            manifest = {"files": []}
        restore_plan.extend(manifest.get("files", []))

        def copy_item(src: Path, dst: Path) -> None:
            if not src.exists():
                return
            if dst.exists():
                if not force:
                    raise SystemExit(f"target exists: {dst} (set FORCE=1 to overwrite)")
                if dst.is_dir() and not dst.is_symlink():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        mapping = {
            Path("hermes/config.yaml"): target_home / ".hermes" / "config.yaml",
            Path("hermes/memories"): target_home / ".hermes" / "memories",
            Path("hermes/profiles"): target_home / ".hermes" / "profiles",
            Path("hermes/skills"): target_home / ".hermes" / "skills",
            Path("hermes/plugins"): target_home / ".hermes" / "plugins",
            Path("hermes/scripts"): target_home / ".hermes" / "scripts",
            Path("hermes/sessions"): target_home / ".hermes" / "sessions",
            Path("hermes/state.db"): target_home / ".hermes" / "state.db",
            Path("hermes/.env"): target_home / ".hermes" / ".env",
            Path("hermes/auth.json"): target_home / ".hermes" / "auth.json",
            Path("opencode/opencode.jsonc"): target_home / ".config" / "opencode" / "opencode.jsonc",
            Path("opencode/opencode.json"): target_home / ".config" / "opencode" / "opencode.json",
            Path("opencode/AGENTS.md"): target_home / ".config" / "opencode" / "AGENTS.md",
            Path("opencode/agents"): target_home / ".config" / "opencode" / "agents",
            Path("opencode/commands"): target_home / ".config" / "opencode" / "commands",
            Path("opencode/skills"): target_home / ".config" / "opencode" / "skills",
            Path("cursor/rules"): target_home / ".cursor" / "rules",
        }

        for rel_src, dst in mapping.items():
            src = extract_dir / rel_src
            if not src.exists():
                continue
            if dry_run:
                print(f"[dry-run] {src} -> {dst}")
                continue
            copy_item(src, dst)

print("restored")
PY
