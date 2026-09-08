---
name: assistant-config-publishing
description: Use when editing local AI assistant skills, rules, Agent.md-style instructions, or helper scripts that the user wants mirrored into a dedicated git repository and pushed immediately.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, rules, agent-md, git, publishing, sync]
    related_skills: [github-repo-management, hermes-agent, hermes-agent-skill-authoring]
---

# Assistant Config Publishing

## Overview

Some users want assistant configuration work treated like source code: when skills, rules, Agent.md-like files, or helper scripts change, sync them into a dedicated repository and push right away. This skill captures that workflow so assistant-config edits do not remain trapped in local dotfiles.

The durable lesson from this session is that the repository of record can be separate from the live config directories. The job is to identify what changed locally, mirror the relevant files into the repo in a stable layout, commit with a descriptive message, push, and verify the working tree is clean.

## When to Use

Use when:
- You edited `~/.hermes/skills`, `~/.cursor/rules`, `Agent.md`-style instructions, or assistant helper scripts.
- The user explicitly wants those updates pushed to a dedicated repo.
- The live files are outside the repo and need to be copied in before commit.

Do not use when:
- The edited files already live inside the target repo and only need a normal git commit.
- The user asked only for a local change with no publishing.

## Workflow

1. Confirm the target repo and local mirror layout.
   - Identify the canonical remote and the local clone path.
   - If the repo does not exist locally, clone it first.
   - Completion criterion: you know the exact local repo path and `origin` remote.

2. Identify the changed assistant artifacts.
   - Typical sources: `~/.hermes/scripts/`, `~/.hermes/skills/`, `~/.cursor/rules/`, `AGENTS.md`, `Agent.md`, OpenCode `opencode.json`/`opencode.jsonc`, or similar assistant-doc roots.
   - If the user corrected style, tone, verbosity, or response shape, treat that as publishable assistant config, not just memory.
   - Completion criterion: every file you plan to publish is listed explicitly before commit.

3. Mirror files into the repo in a stable directory structure.
   - Keep the repo layout human-readable, e.g. `hermes/scripts/...`, `cursor/rules/...`, `skills/...`, `opencode/...`.
   - For style corrections, update the live instruction surface first, then mirror the same change into the repo so the next session starts with the fix already loaded.
   - For OpenCode, keep both the human-edited config and the effective plugin file when they differ (`opencode.jsonc` and `opencode.json`) so the repo preserves intent and runtime shape.
   - Add or update a top-level `README.md` if the repo was empty or the structure changed materially.
   - Completion criterion: `git status --short` inside the repo shows exactly the intended additions or modifications.

4. Commit and push immediately.
   - Use a descriptive commit message that names the class of change.
   - Push to the intended branch, usually `main`, and set upstream if this is the first push.
   - Completion criterion: `git push` succeeds.

5. Verify the repo state.
   - Check `git status --short`, `git rev-parse HEAD`, and `git remote -v`.
   - Completion criterion: working tree is clean and the pushed commit hash is recorded.

## Style Preference Hardening

When the user explicitly says a style should be "hard rules", do not leave it only in memory.

- Update the live instruction files that the active agent loads first.
- Prefer `SOUL.md`, `AGENTS.md`, `Agent.md`, or the project rule file the session actually consumes.
- Mirror the same preference into the repo-backed assistant config if one exists.
- Keep the wording short and declarative so future sessions inherit the same voice without extra steering.
- If the user later complains that the assistant is still too chatty, tighten the live rules again rather than only adjusting memory.

## OpenCode + Agent Rules Sync

When an agent/plugin install changes OpenCode behavior, treat both the config and the injected rules as publishable assistant artifacts.

- Sync `opencode/opencode.jsonc` when the global plugin list or agent-specific config changes.
- Sync `opencode/opencode.json` when the runtime plugin manifest differs from the human-friendly source.
- Sync `opencode/AGENTS.md` when the active always-on rules change, especially when installing rule-based agents like caveman or ponytail.
- If the user expresses a stable style preference that should shape future replies, encode it in the live instruction surface that the agent actually loads first, then mirror the same change into the repo so the next session starts with the same voice.
- Treat style complaints as durable config work, not just memory. When the user says the voice drifted, harden the loaded rule file(s) that govern that surface, not only the memory store.
- If the repo is the publication target, commit and push the mirrored files in the same change set so the repo and live config do not drift.
- If the user says to "always push it" or similar, treat that as a standing publication rule for future assistant-config edits.
- For OpenCode work, keep the skill file and any paired command file in sync together. If `opencode/skills/<name>/SKILL.md` changes, check whether `opencode/commands/<name>.md` also needs the same behavior reflected.
- For user-level slash commands that are meant to improve across sessions, put the durable policy in always-on config (`AGENTS.md` / equivalent), keep command stub terse, and add a memory-writeback rule when the command surfaces stable learning. Mirror both live config and repo copy in same change set.
- If a repo skill depends on live config paths, record the real path used in session, then mirror that path in the repo before push so later sessions do not guess.
- Pointer: `references/opencode-sync-notes.md`.
- Pointer: `references/style-preferences.md`.
- Pointer: `references/opencode-looper-memory-loop.md`.

## Handling Related Repositories

If the user separately asks to also push an adjacent project repo, treat that as a second repo workflow:
- inspect `git status`
- review the diff
- run the repo-appropriate validation command
- commit and push
- verify clean status

Do not automatically push unrelated repos just because they mention the same tool or feature. Wait for an explicit user request.

## Publishing Hermes Memory Snapshots

When the user expects "what Hermes learned" to appear in the GitHub config repo, do not assume the built-in memory store is already tracked. Hermes durable memory may live locally in `~/.hermes/memories/USER.md` and `~/.hermes/memories/MEMORY.md` while the publishing repo stays clean.

Use this extension of the workflow:
1. Inspect whether the live memory store exists under `~/.hermes/memories/`.
2. Mirror `USER.md` and `MEMORY.md` into a stable repo path such as `memory/hermes/`.
3. Add a small `memory/README.md` that explains the source files and sync behavior.
4. Add a rerunnable sync script in the repo and, if needed, a thin wrapper under `~/.hermes/scripts/` so Hermes cron can execute it.
5. If the user wants ongoing publishing, create a cron job that reruns the sync script and stays silent when there is no change.
6. Verify the push by comparing local `HEAD` with `origin/<branch>` and confirming a clean working tree.

This prevents the common mismatch where the user expects GitHub-visible updates but Hermes only learned something in local memory.

Reference: `references/hermes-memory-sync.md`.

## Publishing bootstrap and migration workflows

When the user wants a fast way to recreate their assistant stack on a new device, do not stop at scattered docs or individual install commands. Add a rerunnable bootstrap artifact to the publishing repo itself.

Recommended pattern:
1. Create a top-level `bootstrap/` directory in the repo.
2. Add a primary shell entrypoint such as `bootstrap/bootstrap_ai_stack.sh`.
3. Make the script handle the durable parts of the setup class:
   - install Hermes
   - install OpenCode
   - install GitNexus when it is part of the user's default workflow
   - copy repo-managed assistant config files into their live locations
   - write expected values into `~/.hermes/.env`
   - recreate recurring Hermes cron jobs that belong to the setup
4. Prefer environment-variable inputs plus interactive prompts as a fallback. This keeps the script useful in both manual and non-interactive runs.
5. Add a `bootstrap/README.md` with real invocation examples, including a non-interactive example and a dry-run example.
6. Validate the script before pushing:
   - `bash -n bootstrap/bootstrap_ai_stack.sh`
   - `DRY_RUN=1 NONINTERACTIVE=1 ... bash bootstrap/bootstrap_ai_stack.sh`
7. Push the bootstrap workflow to the GitHub config repo immediately with the rest of the assistant artifacts.

This is the right pattern for "new laptop / new machine / move device" requests because it turns local assistant state into a portable, repo-backed provisioning workflow instead of a one-off checklist.

## Common Pitfalls

1. Forgetting that the live config lives outside the publishing repo.
   - Symptom: `git status` in the repo shows nothing even though you changed local assistant files.
   - Fix: copy or sync the changed files into the repo first.

2. Publishing without verifying the remote.
   - Symptom: changes land in the wrong repository.
   - Fix: check `git remote -v` before the first push.

3. Committing helper scripts without preserving executable bits.
   - Symptom: wrapper scripts lose execute permissions.
   - Fix: verify mode changes in the commit and use executable files where needed.

4. Skipping validation on a related code repo.
   - Symptom: a secondary repo is pushed with unverified runtime changes.
   - Fix: run the project's build or tests before commit.

## References

- `references/ai-skill-publishing.md` — concrete repo paths, commit examples, and the session pattern that synced local Hermes/Cursor files into a dedicated `ai-skill` repo.
- `references/bootstrap-provisioning.md` — durable pattern for turning the config repo into a rerunnable new-device bootstrap workflow.

## Verification Checklist

- [ ] Target repo path and `origin` remote confirmed.
- [ ] Every intended assistant config file to publish is enumerated.
- [ ] Files are mirrored into the repo in a stable layout.
- [ ] Commit created with a descriptive message.
- [ ] Push succeeded to the intended remote/branch.
- [ ] Final `git status --short` is clean.
