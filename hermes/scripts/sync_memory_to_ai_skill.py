#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = Path.home() / '.hermes' / 'memories'
TARGET_DIR = REPO_ROOT / 'memory' / 'hermes'
FILES = ['USER.md', 'MEMORY.md']
MANIFEST = TARGET_DIR / 'manifest.json'


def run(cmd: list[str], cwd: Path | None = None, capture: bool = True) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=capture,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}'
        raise RuntimeError(message)
    return result.stdout.strip() if capture else ''


def ensure_repo() -> None:
    if not (REPO_ROOT / '.git').exists():
        raise RuntimeError(f'Not a git repo: {REPO_ROOT}')


def sync_files() -> list[str]:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in FILES:
        src = SOURCE_DIR / name
        dst = TARGET_DIR / name
        if not src.exists():
            raise RuntimeError(f'Missing source memory file: {src}')
        shutil.copy2(src, dst)
        copied.append(name)

    manifest = {
        'synced_at_utc': datetime.now(timezone.utc).isoformat(),
        'repo_root': str(REPO_ROOT),
        'source_dir': str(SOURCE_DIR),
        'files': [
            {
                'source': str(SOURCE_DIR / name),
                'target': str(TARGET_DIR / name),
            }
            for name in FILES
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    copied.append('manifest.json')
    return copied


def commit_and_push() -> str:
    branch = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=REPO_ROOT)
    run([
        'git', 'add',
        'README.md',
        'memory/README.md',
        'memory/hermes/USER.md',
        'memory/hermes/MEMORY.md',
        'memory/hermes/manifest.json',
        'hermes/scripts/sync_memory_to_ai_skill.py',
    ], cwd=REPO_ROOT)
    diff_exit = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO_ROOT, check=False)
    if diff_exit.returncode == 0:
        return ''
    run(['git', 'commit', '-m', 'chore: sync Hermes memory snapshot'], cwd=REPO_ROOT)
    run(['git', 'push', 'origin', branch], cwd=REPO_ROOT)
    return run(['git', 'rev-parse', '--short', 'HEAD'], cwd=REPO_ROOT)


def main() -> int:
    try:
        ensure_repo()
        sync_files()
        commit_hash = commit_and_push()
        if not commit_hash:
            return 0
        changed = run(['git', 'show', '--stat', '--oneline', '--format=%h %s', '-1'], cwd=REPO_ROOT)
        print(changed)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
