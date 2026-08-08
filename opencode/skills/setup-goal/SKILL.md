---
name: setup-goal
description: Use only for /setup-goal requests to install or replace a complete, validated /goal workflow in the current workspace.
---

# Setup Goal

Install the managed `/goal` scaffold from this skill's `templates/` directory. The setup agent owns interactive discovery and substitution; templates own runtime behavior.

## Guarantees

- Ask one setup question at a time.
- Support GitHub, GitLab, Jira, and local-only operation.
- Detect each repo's GitHub/GitLab code host from its verified remote independently of ticket system.
- Detect repository roots, roles, remotes, and target branches before writing.
- Default planning, building, and review to `openai/gpt-5.6-sol` when available; offer cheaper execution only as an explicit choice.
- Never request, print, or store credentials.
- Publish only after auth preflight and approved plan.
- Never fabricate ticket, branch, PR/MR, merge, check, or test success.
- Preserve unrelated files and changes.
- Generate resumable state with bounded review/fix loops and truthful blocked states.
- Run multiple goals in one workspace without shared run ownership or mutable root state.
- Run only dependency-independent, non-overlapping tasks concurrently, each on a unique branch and worktree.
- Serialize per-repository integration and stop safely on conflicts or shared runtime resources.
- Open draft PRs/MRs, review and fix first, then run full repository checks and QA, and auto-merge only through verified protections and checks.

## Managed files

### opencode
- `.opencode/command/goal.md`
- `.opencode/skills/goal-loop/SKILL.md`
- `.opencode/agent/goal-orchestrator.md`
- `.opencode/agent/goal-planner.md`
- `.opencode/agent/goal-builder.md`
- `.opencode/agent/goal-frontend-builder.md`
- `.opencode/agent/goal-backend-builder.md`
- `.opencode/agent/goal-infra-builder.md`
- `.opencode/agent/goal-qa.md`
- `.opencode/agent/goal-reviewer.md`
- `.opencode/agent/goal-visual-reviewer.md`

### Cursor
- `.cursor/skills/goal-loop/SKILL.md`
- `.cursor/agents/goal-planner.md`
- `.cursor/agents/goal-builder.md`
- `.cursor/agents/goal-frontend-builder.md`
- `.cursor/agents/goal-backend-builder.md`
- `.cursor/agents/goal-infra-builder.md`
- `.cursor/agents/goal-qa.md`
- `.cursor/agents/goal-reviewer.md`
- `.cursor/agents/goal-visual-reviewer.md`

### Codex CLI
- `.codex/skills/goal-loop/SKILL.md`
- `.codex/agents/goal-planner.toml`
- `.codex/agents/goal-builder.toml`
- `.codex/agents/goal-frontend-builder.toml`
- `.codex/agents/goal-backend-builder.toml`
- `.codex/agents/goal-infra-builder.toml`
- `.codex/agents/goal-qa.toml`
- `.codex/agents/goal-reviewer.toml`
- `.codex/agents/goal-visual-reviewer.toml`

### Universal (all tools via `.agents/`)
- `.agents/skills/goal-loop/SKILL.md`

### Shared
- `.goal/state.json`

`.goal/state.json` contains immutable setup configuration only. It must not contain `status`, `run_id`, `runs`, `active_runs`, or `current_run`. Runtime discovers runs from `.goal/runs/*/state.json`; every run writes only its own directory.

Replace all managed files together or none. If any exist, require overwrite confirmation before writing.

When writing the goal-loop skill (SKILL.md), write the same content to ALL skill paths: `.opencode/skills/goal-loop/SKILL.md`, `.cursor/skills/goal-loop/SKILL.md`, `.codex/skills/goal-loop/SKILL.md`, and `.agents/skills/goal-loop/SKILL.md`.

When writing agent files, use the appropriate template for each tool:
- opencode agents: `goal-{role}.md` template → `.opencode/agent/goal-{role}.md`
- Cursor agents: `cursor-agent-{role}.md` template → `.cursor/agents/goal-{role}.md`
- Codex agents: `codex-agent-{role}.toml` template → `.codex/agents/goal-{role}.toml`

## Template rules

Read templates from `templates/`; never invent missing agent prompts. Replace only documented placeholders with validated values. Generated agents use purpose-specific permissions:

- orchestrator: state, delegation, git, publishing
- planner: read-only planning
- frontend builder: UI/client behavior, accessibility, responsive validation
- backend builder: API/data/security/migration validation
- infrastructure builder: CI/container/cloud config and dry-run validation
- generic builder: bounded aux or unknown-stack edits and checks
- QA: boots integrated product on isolated loopback ports and runs integration/Playwright acceptance tests
- reviewer: read-only correctness/security review
- visual reviewer: read-only UI interaction/evidence validation

### Placeholders

| Placeholder | Description | Origin |
|---|---|---|
| `{{PLAN_MODEL}}` | Model for planning, QA, reviewer agents | User input |
| `{{EXEC_MODEL}}` | Model for builder agents | User input |

### Template-to-path mapping

| Template | Written to | Tool |
|---|---|---|
| `goal-orchestrator.md` | `.opencode/agent/goal-orchestrator.md` | opencode |
| `goal-{role}.md` | `.opencode/agent/goal-{role}.md` | opencode |
| `cursor-agent-{role}.md` | `.cursor/agents/goal-{role}.md` | Cursor |
| `codex-agent-{role}.toml` | `.codex/agents/goal-{role}.toml` | Codex CLI |
| `goal-loop.md` | All 4 skill paths | universal |
| `goal-command.md` | `.opencode/command/goal.md` | opencode |

No generated file may contain unresolved `{{...}}` placeholders.

## Runtime State

During setup, create `.goal/runs/`, `.goal/claims/`, `.goal/locks/`, and `.goal/resource-locks/`. Add these paths to the orchestrator repository's `.git/info/exclude` so mutable run data is never committed or copied into task worktrees:

```text
.goal/runs/
.goal/claims/
.goal/locks/
.goal/resource-locks/
```

Do not add or rewrite project `.gitignore` solely for this workflow. Before installation, run `git ls-files .goal/runs .goal/claims .goal/locks .goal/resource-locks`. If any runtime file is already tracked, preserve it and require explicit approval before removing it from the index; otherwise block with the exact `git rm --cached` command. Never delete historical run files from disk.

Each invocation briefly acquires `.goal/claims/<sha256-goal-key>` while selecting or creating the run, preventing duplicate runs for the same goal. Each run then has its own `.goal/locks/<run-id>` lock and state directory. Root config is never a run registry and is never rewritten by `/goal`. Shared ports, databases, devices, emulators, and deployment environments use separate atomic locks under `.goal/resource-locks/`; unrelated goals do not block each other.

## Auth preflight

- GitHub: `gh --version`, `gh auth status`, and a non-destructive git write probe against the verified remote that the workflow will later push to. `gh auth status`, `ssh -T`, or `git ls-remote` alone are not enough.
- GitLab: `glab --version`, `glab auth status`, and a non-destructive git write probe against the verified remote that the workflow will later push to.
- Jira: configured Atlassian tools and accessible project metadata.
- Local only: no publisher required.

Missing auth becomes a warning in scaffold output. Missing write capability must be called out separately from read/auth success. Runtime publishing must become `blocked` with exact recovery steps and exact manual publish commands if auth or push capability remains unavailable.

## Validation

Setup is incomplete until:

1. all managed files exist for every configured tool (opencode, Cursor, Codex)
2. `.goal/state.json` parses
3. root state contains configuration only and no run ownership fields
4. runtime directories are ignored and no runtime file is tracked
5. no placeholders remain
6. installed goal-loop files are byte-identical and contain per-run locking, canonical goal matching, isolated orchestrator worktrees, and explicit approval rules; they must not instruct acquisition of a global `.goal/lock`
7. `opencode agent list` loads all nine generated agents for opencode
   - delegation uses exact `goal-*` IDs and generated files contain no other delegation alias
8. command and skill files are discoverable by each tool:
   - capture `opencode debug config` to a temporary file, parse that JSON, and confirm its `command` object contains `goal`
   - Cursor reads `.cursor/skills/goal-loop/SKILL.md`
   - Codex reads `.codex/skills/goal-loop/SKILL.md`
9. `.agents/skills/goal-loop/SKILL.md` exists (universal fallback)

If validation fails, remove only newly created files and report the exact failure. Restart opencode after successful installation because config-time files are not hot-reloaded.
