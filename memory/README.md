# Hermes memory snapshots

This directory mirrors durable Hermes memory from the local machine into Git.

Current sources:
- `~/.hermes/memories/USER.md`
- `~/.hermes/memories/MEMORY.md`

Mirrored files:
- `memory/hermes/USER.md`
- `memory/hermes/MEMORY.md`
- `memory/hermes/manifest.json`

Sync automation:
- `hermes/scripts/sync_memory_to_ai_skill.py`

Behavior:
- Copies the current Hermes memory files into this repo
- Updates `manifest.json` with source paths and sync time
- Creates a git commit only when the mirrored files changed
- Pushes to the current branch on `origin`
- Exits silently when there is nothing new to publish
