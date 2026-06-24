---
description: Design and scaffold a Looper agent loop.
argument-hint: [target-dir]
allowed-tools: Read, Write, Bash, PowerShell
---

# /looper

Run the Looper skill as an explicit slash command.

Arguments from the user: `$ARGUMENTS`

## Resolve Looper

Find the Looper skill root before doing any loop-design work:

1. Check `LOOPER_ROOT` env var first; then check install paths:
   - opencode: `~/.config/opencode/skills/looper`
   - Claude Code: `$HOME/.claude/skills/looper`
   - Windows: `%USERPROFILE%\.claude\skills\looper`
2. If no directory contains `SKILL.md`, stop and tell user to install Looper.
3. Read `SKILL.md` from that directory and follow its workflow exactly.
   Export `LOOPER_ROOT=<found-dir>` before running helper scripts.

## Target Directory

- If `$ARGUMENTS` is empty, use `./looper-output`.
- Otherwise, treat `$ARGUMENTS` as the target directory argument.

Then continue with the Looper skill workflow.
