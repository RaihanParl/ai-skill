---
name: hermes-cron-ops
description: Manage Hermes cron jobs, schedule changes, response wrapping, and verification.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [hermes, cron, scheduler, gateway, config, troubleshooting]
---

# Hermes Cron Ops

Use this skill when the user asks about Hermes cron jobs, schedule changes, missing deliveries, wrapper text, or scheduler behavior.

## Core workflow

1. Inspect the live state first.
   - Prefer `hermes cron list` and `hermes gateway status` over assumptions.
   - If needed, check gateway logs for the actual delivery path.

2. Change schedules with the CLI.
   - Prefer `hermes cron edit <job> --schedule '...'` for existing jobs.
   - Confirm the saved schedule with `hermes cron list` after the edit.

3. Handle wrapper text separately from job output.
   - If the user wants raw output, set `cron.wrap_response: false` with `hermes config set cron.wrap_response false`.
   - Restart the gateway after config changes so the running service picks up the new value.

4. Verify end to end.
   - Re-list the job.
   - Restart the gateway if config changed.
   - Check logs or the next tick to confirm the new behavior actually fired.

## Argus review watcher batching

For repository-wide PR review watchers, enumerate all open PRs, exclude PRs authored by the configured user, and skip draft PRs until they become ready. Deduplicate by exact head SHA. Treat same-head `blocked` as terminal for that head, but rerun when head or readiness changes. Do not claim review completion when validation is blocked.

Workers may publish individual GitHub review events, but Telegram delivery should be one batch summary after all workers in a batch finish. Aggregate PR number, review state, canonical review URL, and blocked/no-publication reason; suppress per-worker Telegram sends. Persist batch membership and wait while any worker remains alive. Hermes no-agent jobs can be terminated by a short scheduler execution cap (observed 120s), so do not make the cron parent wait for multi-minute reviews: launch a detached waiter that owns batch completion and sends the summary immediately after the last worker exits. Send summary once, then clear batch receipt. A local cron delivery does not itself guarantee Telegram delivery; use explicit `hermes send --to telegram:<chat_id>` when Telegram output is required. Direct worker invocations such as `--run-review` bypass batch aggregation and must not be used when the user expects a Telegram summary; test the full watcher entrypoint instead.

For long-running workers, do not make the scheduler process own the wait: scheduler execution caps can kill it before completion. Persist batch membership, spawn a detached waiter, and have only that waiter send the one summary after every worker exits. In timeout handlers, normalize `TimeoutExpired.stdout` and `.stderr` independently because Python may return one as `bytes` despite `text=True`; decode bytes before concatenation and persist a clean `failed` state.

For review automation, state files are bookkeeping only. A `completed` state is not proof of publication. Verify live GitHub review `id`, `state`, `commit_id`, actor, and canonical URL against the current PR head. Treat `COMMENTED` bodies containing `REVIEW BLOCKED` as blocked/incomplete, not as substantive code review. For clean approval, distinguish historical PR-level `CHANGES_REQUESTED` metadata from current exact-head findings: only active findings in the fresh report or unresolved current threads block `APPROVE`, but any approval is valid only when its review `commit_id` exactly matches the live head. Re-fetch head and reviews immediately before claiming approval; a new push makes prior approval stale and requires a fresh review/publication cycle. When changing a no-agent watcher script, compile-check it and run its dry-run mode before the next live tick; verify the cron registration still points to the intended script and that the dry run queues changed heads while skipping verified same-head reviews.

For manual recovery after watcher failures, pause the watcher first and verify the paused job by listing cron state. Treat `cronjob run` responses as scheduling acknowledgements only: `executed: false`, `execution_skipped`, or “already being fired” is not proof that the script ran. For no-agent scripts, inspect the script entrypoint before invoking flags; never call `--help` unless the script explicitly implements help handling, because an unrecognized flag may fall through to the real watcher path and launch work. Run one exact target/head review outside the batch, with the mandatory authenticated GitHub wrapper exported in the same shell. Record worker PID, log path, and process liveness; stale `started` state with dead PID or empty log is failed/retryable, not completion. Do not trust worker state, truncated process output, or aggregator text as publication evidence. After completion, query `pulls/<number>/reviews` directly and require: expected actor, expected event state, `commit_id == live head`, numeric review ID, and `html_url` containing the same PR number. Batch summaries may misattribute URLs when worker logs contain historical links; never use summary URL alone. A successful manual recovery must report the API-derived canonical review URL.

## Pitfalls

- Do not assume the cron API, cronjob tool, and CLI all accept the same schedule syntax.
- Do not edit the jobs file by hand unless there is no supported command path.
- For no-agent jobs, empty stdout means silent delivery, not a failure.
- If the user wants to remove only the `Cronjob Response: ...` framing, change the wrapper setting, not the job script.
- For bootstrap-driven pings, keep the ping script tiny and separate from the bootstrap script. Copy it into `~/.hermes/scripts/`, make it executable, and gate job creation behind an env flag plus a configurable schedule.
- Do not send one Telegram message per parallel worker when user requests a review summary; collect canonical URLs from worker receipts/logs after batch completion.

## References

- `references/sub-minute-cron.md` — sub-minute scheduling note, wrapper removal, and verification recipe.
- `references/bootstrap-telegram-ping.md` — bootstrap pattern for a lightweight Telegram heartbeat cron.
- `references/argus-review-watcher-failure-modes.md` — receipt verification, detached waiters, Codex stdin/timeout safeguards, and contract-alias alignment.

## Review-watcher verification and iteration

For repository review watchers, distinguish queue selection from review eligibility. If user requests all PRs, remove review-request filters and enumerate every open PR; retain exact-head deduplication. Treat `blocked` as incomplete when no substantive GitHub review exists: it must be retryable, not terminal. A state file saying `completed` is also non-terminal unless live GitHub evidence proves a review ID, canonical URL, expected actor, expected event state, and exact current head SHA. Only `already_reviewed` backed by that live receipt is terminal. Retry automatically when head, readiness, helper contract, or evidence validity changes; suppress duplicates only after receipt verification. Publication must occur only after exact-head, receipt, ledger, helper-provenance, identity, and live-state gates pass; independently verify returned GitHub review ID, state, commit SHA, and URL.

When Codex runs from cron, close stdin with `stdin=subprocess.DEVNULL`; otherwise noninteractive `codex exec` can wait on inherited cron stdin. Normalize `subprocess.TimeoutExpired.stdout` and `.stderr` independently because Python may return one as `bytes` despite `text=True`. A zero Codex exit code without a canonical GitHub review URL is failure, not completion. If authoritative documents use equivalent headings (for example `MVP contract` for acceptance material or `Validation and handoff` for validation), update the ledger parser and review prompt together; parser-only changes can leave the model stopping at Tier 1.

A `local` delivery job can run successfully while producing no visible chat message. Diagnose with `hermes cron list`, current time, last/next run, job state, and per-target state files before assuming scheduler failure. Gateway service health is separate from local scheduler execution; report both independently.

## Review-comment coverage

For review watchers, distinguish comment types before claiming coverage:

- Review bodies: `APPROVED`, `CHANGES_REQUESTED`, and `COMMENTED` review events.
- Inline review comments: unresolved, non-outdated review threads, including body, author, path, line, URL, and commit identity.
- General PR conversation comments: issue-comment endpoint data (`/issues/<number>/comments`), which is separate and must be explicitly fetched if required by the review contract.

Read the governing review contract and helper implementation. Do not infer that “comments checked” means all PR conversation comments. Respect helper pagination limits; truncated review metadata must block approval or force manual verification.

## Detached-worker verification

A no-agent cron run can launch detached worker processes and return successfully before workers finish. After manual `run`, or before pausing a watcher:

1. Inspect cron state and scheduler status.
2. Search live process table for the watcher, worker command, and child agent processes.
3. Inspect per-run state/log files and verify worker PIDs are gone before claiming no background work remains.
4. Remember: pausing future ticks does not terminate workers already launched by a prior tick. Terminate only after identifying ownership and scope.

## Verification checklist

- `hermes cron list` shows the intended schedule.
- For review watchers, dry-run confirms expected PR population and no unintended review-request filter.
- Same-head `completed`, `already_reviewed`, and `blocked` states do not relaunch.
- New PR head triggers fresh review and publication.
- Review coverage is stated precisely: review bodies, inline threads, and general PR comments are separate sources.
- After manual trigger, live process/state/log inspection confirms whether detached workers remain.
- `hermes gateway restart` succeeds after config changes.
- The next delivered run matches the requested format.
- If the job is meant to be silent, confirm the script prints nothing on empty state.
