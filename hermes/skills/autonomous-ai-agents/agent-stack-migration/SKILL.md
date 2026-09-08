---
name: agent-stack-migration
description: "Back up and migrate multi-agent coding environments while preserving workspace-linked sessions, project source, and restoreability."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [backup, migration, agents, hermes, opencode, codex, cursor, source-code]
    related_skills: [hermes-agent, opencode, codex, assistant-config-publishing]
---

# Agent Stack Migration

## Trigger

Use when a user is replacing or losing a machine and wants to preserve coding agents, agent history, skills, memory, configuration, and source code.

## Response format

Lead with a short TL;DR. User prefers concise answers for long migration work. Put detailed inventory, risks, and restore steps after the TL;DR only when needed.

## Core model

Treat migration as separate layers:

1. Agent state — databases, sessions, memories, skills, profiles, plugins, commands, rules, cron, config.
2. Project source — primary working trees, `.git` metadata, local branches, tracked changes, untracked source.
3. Secrets — `.env`, OAuth tokens, auth files, API keys, MCP credentials.
4. Rebuild metadata — tool versions, paths, remotes, branches, exclusions, restore commands.

Do not make one unfiltered home-directory archive. It copies caches, dependency trees, generated artifacts, and secrets into places where they do not belong.

## Workflow

1. Inventory installed agents and state paths without printing secret contents.
   - Hermes: `~/.hermes/`
   - OpenCode: `~/.config/opencode/`, `~/.local/share/opencode/`
   - Codex: `~/.codex/`
   - Cursor: `~/.cursor/`
   - Claude Code: `~/.claude/`, `~/.claude.json`
   - Pi: `~/.pi/`
   - Other discovered agent state: `~/.gemini/`, `~/.gitnexus/`, `~/.looper/`, `~/.mcp-auth/`, `~/.agent-kanban/`, `~/.agents/`
2. Inventory project roots using Git metadata. Count primary repositories separately from worktrees. Do not assume remote clones contain current work; inspect dirty and untracked state.
3. Verify workspace binding before backup. Session databases commonly store absolute `cwd`, project directory, worktree, workspace, or rollout paths.
   - Hermes sessions store `cwd`.
   - OpenCode stores project/workspace/session directory and path fields.
   - Codex stores thread `cwd` and rollout paths.
   - Cursor project identity can also depend on filesystem paths.
4. Prefer restoring the same macOS short username and absolute project paths. This gives best session continuity.
5. If paths must change, preserve path suffixes and perform controlled path migration only after making a byte-for-byte backup. Do not blindly search-and-replace database files.
6. Stop Hermes, OpenCode, Codex, and other active writers before copying SQLite databases. Use SQLite-aware backups or copy after shutdown. Export readable session/config data where the tool supports it.
7. Build separate outputs:
   - readable assistant-config repository
   - encrypted full agent-state archive
   - source snapshot or per-project Git backups
   - encrypted secrets archive
   - manifest and restore guide
8. Verify archive listings, checksums, archive extraction, SQLite integrity, and restore-path assumptions before declaring success.

## GitHub split

Private GitHub is suitable for text/config artifacts:

- skills
- rules
- commands
- agent definitions
- scripts
- cron definitions
- manifests
- restore scripts
- personal source repositories after secret scanning

Do not put these in normal Git history:

- `.env`
- auth/OAuth files
- API tokens
- agent databases and private session history
- company/work source without explicit permission
- generated artifacts or dependency trees

Existing work/company remotes must not be republished to personal GitHub automatically. Preserve uncommitted work in encrypted backup unless authorization exists.

## Source backup policy

Include for primary projects:

- source files
- `.git` metadata
- local branches and refs
- tracked modifications
- untracked source files
- project-local agent rules needed for behavior

Exclude by default:

- worktrees, unless user explicitly wants them
- `node_modules`, `.venv`, `venv`
- `dist`, `build`, `target`
- caches, logs, model downloads
- databases and runtime volumes
- generated media and screenshots

For mixed folders such as a parent containing many repositories, enumerate nested repositories before archiving. Never upload the parent folder blindly.

## Recommended artifact layout

```text
backup/
  agent-state.enc
  project-source.tar.zst
  agent-export/
  secrets.enc
  MANIFEST.json
  RESTORE.md
```

Use encrypted restic or age-based archives for private state. Keep a second copy on a separate destination.

## Restore order

1. Create same user short name when possible.
2. Recreate directory layout.
3. Restore project roots.
4. Restore agent state and secrets with correct permissions.
5. Restore readable config and skills.
6. Start agents only after paths exist.
7. Test one known workspace per agent and resume one known session.
8. Test a second workspace to confirm separation.
9. Only then consider path rewrites for sessions that point to removed workspaces.

## Pitfalls

- Cloning remotes alone loses dirty and untracked work.
- Same Git remote does not imply same agent workspace identity.
- Different username or project root can create duplicate OpenCode/Cursor projects and hide normal session history.
- Copying live SQLite databases can produce inconsistent snapshots.
- Private GitHub does not make leaked secrets safe; deleted secrets remain in Git history.
- A giant monorepo backup of all projects mixes personal, company, generated, and sensitive material.
- Long inventory reports reduce user comprehension. Give TL;DR first, then compact findings.

## References

- `references/path-bound-agent-state.md` — observed workspace-key fields and migration implications.
