---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing

Requires the codex CLI and a git repository.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI auth configured: either `OPENAI_API_KEY` or Codex OAuth credentials
  from the Codex CLI login flow
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

For Hermes itself, `model.provider: openai-codex` uses Hermes-managed Codex
OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. For the
standalone Codex CLI, a valid CLI OAuth session may live under
`~/.codex/auth.json`; do not treat a missing `OPENAI_API_KEY` alone as proof
that Codex auth is missing.

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |
| `--sandbox danger-full-access` | No Codex sandbox; useful when the host service context breaks bubblewrap |

## Hermes Gateway Caveat

When invoking the Codex CLI from a Hermes gateway/service context (for example,
Telegram-driven agent sessions), Codex `workspace-write` sandboxing may fail even
when the same command works in the user's interactive shell. A typical symptom is
bubblewrap/user-namespace errors such as `setting up uid map: Permission denied`
or `loopback: Failed RTM_NEWADDR: Operation not permitted`.

In that context, prefer:

```
codex exec --sandbox danger-full-access "<task>"
```

Use process boundaries as the safety layer instead: explicit `workdir`, clean git
status before launch, narrow task prompts, `git diff` review, targeted tests, and
human/agent confirmation before committing broad changes.

## Noninteractive Review Workers

For a supervised service/cron worker, `codex exec --sandbox read-only --model <model> <prompt>` is the bounded review form: it exits with a result, permits no implementation writes, and can be captured by a parent process. PTY remains preferred for human-terminal sessions; do not force PTY into a detached service subprocess when stdout/stderr capture and exit-status handling are required.

When the prompt invokes a repository review contract, pass the exact PR target and contract path. Normal review remains publication-free; an explicitly authorized Argus cron prompt may hand a validated result to `/post-review`. Classify output as `completed`, `blocked`, or `failed` from exit status, explicit contract text, and publication receipt. A zero Codex exit does not mean review completed if contract or publication reports a blocker.

### PR capability smoke tests

Test Codex PR operations separately before debugging a larger review worker:

1. Read: `gh pr view` plus `gh pr diff --name-only`.
2. Write: one explicitly labeled top-level `gh pr comment` smoke comment.
3. Combined: read live title/head, then post one deterministic summary comment.

For every GitHub CLI invocation, set the authenticated wrapper in that same shell command, for example:

```bash
GH_BIN=/path/to/gh-keychain-wrapper gh pr view 123 --repo OWNER/REPO --json title,author,headRefOid
GH_BIN=/path/to/gh-keychain-wrapper gh pr comment 123 --repo OWNER/REPO --body 'Codex integration smoke test...'
```

Verify mutations by reading the returned comment URL or querying issue comments. Distinguish four outcomes: Codex process exit, provider transport health, GitHub CLI operation result, and repository review-contract verdict. A websocket/provider warning can coexist with successful CLI operations; do not label review blocked as Codex failure. A cleanup SIGTERM is launcher/process termination, not Codex review failure. Capture each attempt in a fresh log; never append unrelated Codex sessions because mixed output can combine stale approve/blocked text with current results.

For long-running supervised batches, do not make a short-lived scheduler parent wait on Codex children. If scheduler execution caps can terminate the parent before reviews finish, persist batch membership and launch a detached waiter; waiter must wait for all child states, verify receipts, then send one aggregated Telegram summary. Do not send per-worker notifications.

Do not confuse direct PR capability with Argus review readiness. A Codex child can successfully run `gh pr view`, inspect files, or comment from the exact harness workspace while Argus `/review` fails before GitHub lookup on a mandatory managed-installation receipt gate. Record workspace/cwd separately from receipt validity, exact-head preflight, trust policy, and provider status. If validation tooling overwrites `.agents/local/harness.install-receipt.json` with repository-validation evidence, stop and repair the receipt collision through the supported installation workflow; do not blame cwd or bypass the gate.

See `references/pr-smoke-tests.md` for reproducible PR read/comment/combined smoke-test evidence.

If the worker depends on GitHub CLI auth, validate auth inside the worker environment. A keychain-backed `gh auth token` can be passed ephemerally as `GH_TOKEN`; never print, persist, or include the token in prompts/logs. Re-check `gh auth status` after injection because stale parent-shell auth can differ from child-process auth.

## Session & Cost Management

List sessions:

```
terminal(command="codex stats")
terminal(command="codex doctor")
```

When usage feels absurdly high, do not guess. Check local Codex state first:
- `~/.codex/state_5.sqlite` for thread metadata and `tokens_used`
- `~/.codex/thread_history_1.sqlite` for turn counts and rollout history
- `~/.codex/logs_2.sqlite` for logged events

Rank the top threads by tokens, then inspect turn counts. Most burn comes from one of these:
- giant recursive prompts
- subagent fanout
- repeated review/fix loops
- huge one-shot briefs with too much context
- tool spam inside a single thread

See `references/usage-audit.md` for the exact SQL snippets and triage order.

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
