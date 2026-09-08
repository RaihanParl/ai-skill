---
name: opencode
description: "Delegate coding to OpenCode CLI (features, PR review)."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

Use [OpenCode](https://opencode.ai) as an autonomous coding worker orchestrated by Hermes terminal/process tools. OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.

## When to Use

- User explicitly asks to use OpenCode
- You want an external coding agent to implement/refactor/review code
- You need long-running coding sessions with progress checks
- You want parallel task execution in isolated workdirs/worktrees

## Prerequisites

- OpenCode installed: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- Auth configured: `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)
- Verify: `opencode auth list` should show at least one provider
- Git repository for code tasks (recommended)
- `pty=true` for interactive TUI sessions

## Binary Resolution (Important)

Shell environments may resolve different OpenCode binaries. If behavior differs between your terminal and Hermes, check:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

If needed, pin an explicit binary path:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## One-Shot Tasks

Use `opencode run` for bounded, non-interactive tasks:

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files with `-f`:

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Show model thinking with `--thinking`:

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Force a specific model:

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Interactive Sessions (Background)

For iterative work requiring multiple exchanges, start the TUI in background:

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**Important:** Do NOT use `/exit` — it is not a valid OpenCode command and will open an agent selector dialog instead. Use Ctrl+C (`\x03`) or `process(action="kill")` to exit.

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

### Resuming Sessions

After exiting, OpenCode prints a session ID. Resume with:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue the last OpenCode session |
| `--session <id>` / `-s` | Continue a specific session |
| `--agent <name>` | Choose OpenCode agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--format json` | Machine-readable output/events |
| `--file <path>` / `-f` | Attach file(s) to the message |
| `--thinking` | Show model thinking blocks |
| `--variant <level>` | Reasoning effort (high, max, minimal) |
| `--title <name>` | Name the session |
| `--attach <url>` | Connect to a running opencode server |

## Procedure

1. Verify tool readiness:
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. For bounded tasks, use `opencode run '...'` (no pty needed).
3. For iterative tasks, start `opencode` with `background=true, pty=true`.
4. Monitor long tasks with `process(action="poll"|"log")`.
5. If OpenCode asks for input, respond via `process(action="submit", ...)`.
6. Exit with `process(action="write", data="\x03")` or `process(action="kill")`.
7. Summarize file changes, test results, and next steps back to user.

## User workflow preference

When the user asks for coding work, treat OpenCode as default execution path. Keep planning in GPT-5.4 when the user asked for it, then hand implementation to OpenCode using the requested execution model. Do not silently switch to direct terminal editing for code tasks unless OpenCode is only being used to supervise or verify a step.

Recommended pattern for coding asks:
1. Plan with GPT-5.4.
2. Run implementation in OpenCode, usually with `opencode run` for bounded changes.
3. Use the user-selected model in OpenCode when specified; if the user names a model pair, follow it exactly.
4. Verify with real build/test output before reporting done.

## Repo resolution before OpenCode work

Before starting OpenCode on a GitLab task, resolve exact target repo and local clone path first.

- Prefer the exact remote from user URL or MR host, not a similarly named sibling repo.
- If repo is missing locally, clone target repo first, then create worktree from that clone.
- Before handing work to OpenCode, confirm workdir remote matches target host/path.
- If a worktree already exists but points at wrong remote, stop and switch. Do not "close enough" it.
- For GitLab CI/MR work, scope edits to exact repository from user link, not a branch or folder in another repo that happens to have similar files.

See `references/repo-resolution-pitfalls.md` for one concrete drift case and check sequence.

## OpenCode session handling

- Use the local OpenCode DB when the user asks which session did work or what a session asked for.
- Match by title and directory, then inspect `message` and `part` rows for the exact user ask and latest assistant reply.
- If a run stalls, inspect logs / DB state before assuming failure. Do not trust the TUI alone.
- Prefer worktree-scoped runs for repo tasks so edits stay isolated from the main checkout.

## PR Review Automation: Quota, Argus, and Telegram

Detailed endpoint, receipt, and notification notes: `references/argus-review-automation.md`.

For scheduled Argus PR reviews:

1. Determine OpenAI Codex weekly usage from the authenticated OpenCode OAuth token, not from `opencode stats` token totals. Query `https://chatgpt.com/backend-api/wham/usage`; use `rate_limit.primary_window.used_percent` only when `limit_window_seconds` is a seven-day window (`604800`). Never print or persist the token or response PII.
2. Select the requested model with strict threshold semantics: usage `> 30` → `openai/gpt-5.6-sol`; usage `<= 30` → `openai/gpt-5.6-luna`. On endpoint/auth/shape failure, fail closed to Luna and log only the reason/status.
3. If Telegram completion alerts are required, verify delivery before launching a costly review. Use `hermes send --to telegram:<chat_id> --quiet "..."`; do not create a competing Telegram Bot API poller when Hermes gateway owns the bot.
4. For Argus `/review`, `opencode run` does not interpret a literal interactive slash command reliably. Pass an explicit review-contract prompt that tells OpenCode to read `.commands/review.md`, avoid generic review behavior, avoid implementation edits, and avoid publishing findings unless contract requires it.
5. Treat Argus preflight as a hard safety gate. A managed installation receipt hashes helper files; `hash_mismatch` means review must stop before GitHub lookup. Report the exact failed managed paths and repair with the repository-prescribed receipt-managed repair command; never bypass the check.
6. Completion notification must distinguish `completed`, `failed`, and `blocked`. A zero OpenCode exit code can still mean Argus reported a blocked preflight, so inspect output for `Review blocked` / `configuration blocker` before claiming success.
7. Persist terminal state per PR head SHA and skip same-head `started`, `completed`, `blocked`, or `failed` runs. New head SHA may trigger a new review.

## PR Review Workflow

OpenCode has a built-in PR command:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or review in a temporary clone for isolation:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Parallel Work Pattern

Use separate workdirs/worktrees to avoid collisions:

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## Session & Cost Management

List past sessions:

```
terminal(command="opencode session list")
```

Inspect actual session content / latest asks:

- `opencode session list` only shows metadata, not the conversation text.
- For "what did that session ask me?" style questions, inspect the local SQLite DB at `~/.local/share/opencode/opencode.db`.
- Read `references/session-inspection.md` for the exact workflow and query pattern.
- In practice, recent user-visible text often lives in the `part` table (`type="text"`), while `message` holds mostly envelope metadata.
- When reporting back, explicitly say whether OpenCode is waiting on the user, what it asked, the latest user reply, and whether there is a newer visible assistant response yet.

Check token usage and costs:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

For usage blowups, inspect thread/token hotspots before guessing. See `references/usage-audit.md` for the exact local DB queries and triage order.

## Telegram / Hermes monitoring for background OpenCode work

When the user wants Telegram pings for OpenCode sessions that finish or need manual authorization, use a Hermes cron watchdog rather than trying to keep a live PTY attached.

If the user already has a live OpenCode session and wants to control it from Telegram, do not rely on `opencode -s <session_id>` alone. Attach or register the running tmux session with the Telegram bridge first, then drive it through the bridge id.

Pattern:
1. Create a script under `~/.hermes/scripts/` that reads OpenCode state from:
   - `~/.local/share/opencode/opencode.db`
   - `~/.local/share/opencode/log/opencode.log`
2. Store a small cursor/state file so each cron tick reports only new events.
3. Schedule it with `cronjob(action='create', no_agent=true, script='<name>.py', schedule='every 1m', deliver='telegram:<user_id>')`.
4. Make the script stay silent when nothing changed. Non-empty stdout becomes the Telegram alert.

Useful signals discovered in practice:
- Authorization needed: search `part.data` for `Waiting for authorization` in `opencode.db`.
- Finished loop: `opencode.log` contains `message="exiting loop" session.id=...` for some sessions.
- One-shot runs may not always emit a fresh `exiting loop` line immediately; a practical fallback is to treat a `session.time_updated` change that has gone quiet for a short threshold as "idle after work" and notify on that.

Caveats:
- Permission/authorization detection is best-effort because OpenCode does not expose every interactive gate in one uniform place.
- Polling cron means alerts are near-real-time, not instant.

See `references/opencode-monitoring.md` for the concrete DB/log queries and watchdog shape.

## Telegram reply-to-control bridge for live OpenCode sessions

If the user wants to approve, deny, stop, or answer a live OpenCode session from Telegram, do not try to control arbitrary OpenCode processes directly. Use a bridge-managed tmux session.

Pattern:
1. Launch OpenCode inside tmux and register that tmux session with a bridge state file.
2. Have a cron tick script watch Hermes's own `~/.hermes/state.db` for new Telegram user messages from the allowed user.
3. Parse simple control messages like `approve`, `deny`, `stop`, `send: <text>`, and `key: <key>`.
4. Forward those controls into tmux with `tmux send-keys`.
5. Send outbound Telegram alerts when the tmux pane looks actionable or when the session exits.

Important workflow rule:
- Do not poll Telegram Bot API updates from the bridge if Hermes gateway already uses the same bot token. That creates competing long-pollers. Read inbound Telegram commands from Hermes session storage instead.

Operational rule:
- If only one bridged session is active, plain Telegram messages can target it automatically.
- If several bridged sessions are active, require explicit `/oc <action> <bridge_id> ...` commands.

See `references/opencode-telegram-bridge.md` for the concrete bridge workflow and smoke-test recipe.

## Session control and handoff from Telegram

For session monitoring, latest-ask detection, and post-OpenCode git handoffs, read `references/session-control-and-handoff.md`.

Key rules:

- A running PTY does not prove OpenCode is progressing. Check the DB/log latest assistant parts before reporting state.
- When the user asks what OpenCode said, explicitly report whether OpenCode is waiting on them and quote the ask.
- If the user asks Hermes to push code after an OpenCode loop, prefer direct Hermes git workflow over telling OpenCode to push, unless the user explicitly requests OpenCode delegation.
- If the user corrects the target after a background OpenCode process starts, kill that process before doing anything else.

## Pitfalls

- Interactive `opencode` (TUI) sessions require `pty=true`. The `opencode run` command does NOT need pty.
- `/exit` is NOT a valid command — it opens an agent selector. Use Ctrl+C to exit the TUI.
- PATH mismatch can select the wrong OpenCode binary/model config.
- If OpenCode appears stuck, inspect logs and persisted DB parts before killing:
  - `process(action="log", session_id="<id>")`
  - check `~/.local/share/opencode/opencode.db` for latest `message`/`part` rows
- Avoid sharing one working directory across parallel OpenCode sessions.
- Enter may need to be pressed twice to submit in the TUI (once to finalize text, once to send).

## Verification

Smoke test:

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Success criteria:
- Output includes `OPENCODE_SMOKE_OK`
- Command exits without provider/model errors
- For code tasks: expected files changed and tests pass

## Rules

1. Prefer `opencode run` for one-shot automation — it's simpler and doesn't need pty.
2. Use interactive background mode only when iteration is needed.
3. Always scope OpenCode sessions to a single repo/workdir.
4. For long tasks, provide progress updates from `process` logs.
5. Report concrete outcomes (files changed, tests, remaining risks).
6. Exit interactive sessions with Ctrl+C or kill, never `/exit`.
