---
name: argus-own-pr-remediation
description: Safely automate remediation of the user's own reviewed GitHub pull requests with Argus review/fix loops, conflict reconciliation, parallel workers, exact-head gates, and durable cron execution.
version: 1.0.0
metadata:
  hermes:
    tags: [argus, github, pull-requests, review, fix, cron, parallel-workers]
---

# Argus own-PR remediation

Use when user wants Argus to inspect, rebase or merge main into, fix, validate, push, and re-review open pull requests authored by the user.

## Scope gate

1. Discover open PRs in the configured repository.
2. Keep only non-draft PRs authored by configured self identities. Treat known account aliases as one owner; do not identify ownership by display name.
3. Require review evidence from a reviewer outside self identities. A review on an older head still matters: newer commits make it stale, and current-head `/review` must reconcile it.
4. Skip closed, draft, foreign-owned, and review-free PRs.

## Exact-head and idempotency gate

- Capture PR number, branch, base, author, current head SHA, mergeability, external review ID, and reviewer login before launch.
- Use state key `(PR number, head SHA, external review ID)`.
- Skip same-key completed or blocked work; retry when head or external review changes.
- Persist worker PID and skip while PID is alive.
- Use a nonblocking scheduler lock so overlapping cron ticks cannot launch duplicate workers.
- Never treat process exit code alone as proof of successful remediation. Require exact current-head evidence, validation output, push commit, and comment receipt.

## Remediation workflow

1. Fetch live PR metadata and all external review bodies/threads through the required authenticated GitHub wrapper.
2. Use Argus-native `/review` and `/fix` first. `/review` remains read-only; remediation must not publish duplicate GitHub reviews.
3. Reconcile main before fixing conflicts. Prefer normal merge because it preserves non-force delivery. Only rebase with explicit authorization, exact remote lease, and no blind force push.
4. Run `/review` at the exact reconciled head. Partition independent findings into isolated worktrees/workers when safe; never let workers share mutable checkout state.
5. Run `/fix` for actionable findings tied to external feedback. Preserve questions, unsafe scope, missing evidence, and environment blockers as explicit blockers.
6. Validate each fix plus relevant repository checks. Keep changes bounded and unrelated user modifications untouched.
7. Push only after branch, parent, authorization, exact-head, and delivery checks pass. Prefer one bounded commit per loop.
8. Comment on PR with commit, addressed findings, validation, exact new head, and request for original reviewer re-review.
9. Repeat `/review -> /fix -> validate -> push -> comment` until no active findings remain. Never claim clean while blockers or required evidence remain.
10. Send one aggregate notification after all parallel workers settle. Include URLs, states, commits, heads, tests, blockers, and delivery result.

## Harness failure fallback

If native execution fails, hangs, crashes, or blocks:

1. Verify failure is real and capture concise evidence.
2. Create an issue in Argus repository through `/issue`.
3. Try another functional native path.
4. If none remains, spawn isolated fallback worker/subagent and continue original PR work.
5. Report the issue URL and distinguish remediation result from harness failure.

## Durable cron pattern

- Cron entry must be no-agent and invoke a small launcher script.
- Launcher must detach long-running workers with closed stdin, a new session, durable logs, and persisted state; Hermes cron execution caps must not own multi-minute waits.
- Worker completion owns final notification and state update.
- Cron should be local-delivery when the script sends Telegram explicitly; local scheduler success is not proof of Telegram delivery.
- Verify cron registration, gateway health, manual tick, worker launch, state transitions, and actual notification separately.

## Reporting discipline

Lead with current state, not plans. Distinguish:

- cron healthy vs PR remediation complete;
- worker launched vs worker completed;
- pushed fix vs reviewer re-review pending;
- no code findings vs no blockers;
- old Telegram message vs current delivery evidence.

Keep status terse and evidence-backed. Do not report “all good” when a PR remains blocked or when delivery evidence is missing.

## References

- `references/argus-own-pr-session-lessons.md` — concrete implementation lessons, failure modes, and verification recipe from a live remediation/cron setup.
