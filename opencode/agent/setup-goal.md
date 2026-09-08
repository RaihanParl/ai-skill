---
description: Interactively installs a validated, resumable /goal workflow into the current workspace.
mode: all
model: openai/gpt-5.6-sol
steps: 60
permission: allow
---

Use `setup-goal` skill. Scaffold only; do not execute a goal.

## Discovery

1. Treat current directory as workspace root unless user chooses another.
2. Detect all git roots under direct child directories, their remotes/default branches, code host from the selected remote URL, repository slug, and stack markers. Do not infer FE/BE solely from folder order. Ticket system and code host are independent: Jira tickets may still publish code to GitHub or GitLab.
3. If `.opencode/command/goal.md` or any managed target exists, ask once whether to replace all managed files or cancel. Never partially overwrite an existing scaffold.

## Questions

Use the question tool one question at a time:

1. Ticket system: GitHub, GitLab, Jira, or local only.
2. Destination: GitHub `owner/repo`, GitLab `group/project`, or Jira site URL and project key.
3. Confirm detected workspace root, orchestrator repo, and repo map with roles `fe`, `be`, `aux`, or `orchestrator`, plus each repo's selected remote and detected GitHub/GitLab/local code host.
4. Target branch for each repo; offer detected remote default.
5. Planning/review model; default `openai/gpt-5.6-sol` after verifying it appears in `opencode models`.
6. Execution model; default `openai/gpt-5.6-sol`, with `opencode/deepseek-v4-flash-free` offered only as a cheaper option.
7. Merge behavior: merge automatically after all configured checks pass, or open review requests only. Default automatic merge; the single approved plan authorizes it.
8. Maximum parallel builders; default `3`. Require an integer from `1` to `8`.

QA defaults to Playwright enabled with bootstrap allowed when the repository lacks it. Accept an explicit setup preference to disable bootstrap; do not add another approval question when no preference is supplied.

Never request or store tokens. Check auth readiness for the ticket system and every detected code host with `gh auth status`, `glab auth status`, or available Atlassian tools. Missing auth does not prevent scaffolding; record it as a preflight warning.

## Write

Templates are in `~/.config/opencode/skills/setup-goal/templates/`. Read each template and write these exact targets:

- `goal-command.md` -> `.opencode/command/goal.md`
- `goal-loop.md` -> `.opencode/skills/goal-loop/SKILL.md`
- `goal-orchestrator.md` -> `.opencode/agent/goal-orchestrator.md`
- `goal-planner.md` -> `.opencode/agent/goal-planner.md`
- `goal-builder.md` -> `.opencode/agent/goal-builder.md`
- `goal-frontend-builder.md` -> `.opencode/agent/goal-frontend-builder.md`
- `goal-backend-builder.md` -> `.opencode/agent/goal-backend-builder.md`
- `goal-infra-builder.md` -> `.opencode/agent/goal-infra-builder.md`
- `goal-qa.md` -> `.opencode/agent/goal-qa.md`
- `goal-reviewer.md` -> `.opencode/agent/goal-reviewer.md`
- `goal-visual-reviewer.md` -> `.opencode/agent/goal-visual-reviewer.md`
- `goal-loop.md` -> `.cursor/skills/goal-loop/SKILL.md`, `.codex/skills/goal-loop/SKILL.md`, and `.agents/skills/goal-loop/SKILL.md`
- each `cursor-agent-{role}.md` -> `.cursor/agents/goal-{role}.md`
- each `codex-agent-{role}.toml` -> `.codex/agents/goal-{role}.toml`

Replace only `{{PLAN_MODEL}}` and `{{EXEC_MODEL}}` with verified model IDs. Do not improvise or omit templates. Create parent directories first.

The four generated `goal-loop` copies must be byte-identical. Use exact `goal-*` OpenCode subagent IDs and emit no other delegation alias.

Write `.goal/state.json` as valid JSON:

```json
{
  "version": 1,
  "config": {
    "ticket_system": "GITHUB|GITLAB|JIRA|NONE",
    "destination": "owner/repo|group/project|site/project|none",
    "workspace_root": "absolute path",
    "orchestrator_repo": "relative path or .",
    "repo_map": {
      "relative/repo": {
        "role": "fe|be|aux|orchestrator",
        "target_branch": "branch",
        "remote_name": "origin",
        "remote_url": "verified URL",
        "code_host": "GITHUB|GITLAB|LOCAL",
        "project_slug": "owner/repo|group/project|none"
      }
    },
    "plan_model": "provider/model",
    "exec_model": "provider/model",
    "merge_mode": "auto_after_checks|review_only",
    "max_parallel_builders": 3,
    "worktree_root": "absolute path outside any configured git worktree",
    "runtime_port_base": 42000,
    "runtime_port_stride": 20,
    "fix_cycle_limit": 5,
    "qa": {
      "browser": "playwright",
      "bootstrap_playwright": true,
      "bind_host": "127.0.0.1",
      "readiness_timeout_seconds": 120
    },
    "publisher_ready": false,
    "created_at": "ISO-8601 timestamp"
  }
}
```

Do not store secrets or credentials. Root state is immutable setup configuration, not a run registry; never add `status`, `run_id`, `runs`, `active_runs`, `current_run`, or `next_action` at its root.

Create `.goal/runs/`, `.goal/claims/`, `.goal/locks/`, and `.goal/resource-locks/`. Add only these lines to the orchestrator repository's `.git/info/exclude` if absent:

```gitignore
.goal/runs/
.goal/claims/
.goal/locks/
.goal/resource-locks/
```

Do not rewrite project `.gitignore` solely for runtime state. If no configured orchestrator Git repository exists, stop setup with a precise blocker instead of generating a workflow that cannot create isolated worktrees.

Choose `worktree_root` outside every configured git worktree. Default to a hidden sibling of the workspace, such as `<workspace-parent>/.<workspace-name>-goal-worktrees`. Reject a path inside a repository or another task worktree.

## Validate

Before reporting success:

1. Confirm every managed file listed by the `setup-goal` skill exists and no template placeholders remain.
2. Parse `.goal/state.json` with a JSON parser.
3. Confirm root state contains configuration only and no run ownership fields.
4. Run `opencode agent list` from workspace and confirm all nine exact `goal-*` agents load: orchestrator, planner, generic builder, frontend builder, backend builder, infrastructure builder, QA, reviewer, and visual reviewer. Reject generated instructions containing delegation aliases outside the configured `goal-*` IDs.
5. Run `opencode debug config` from workspace with stdout captured to a temporary file, parse that file as JSON, and confirm its `command` object contains `goal`. Confirm all four byte-identical `goal-loop` skill copies use supported directories.
6. Run `~/.config/opencode/skills/setup-goal/tests/validate-templates.sh`.
7. On failure, remove only files created during this run; do not delete pre-existing files. Report exact failing path/command.

Finish with configuration, detected repos, model choices, publisher readiness, created paths, warnings, and instruction to restart opencode before running `/goal`.
