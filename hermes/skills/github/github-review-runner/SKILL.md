---
name: github-review-runner
description: Build, troubleshoot, and verify automated read-only GitHub PR review runners across coding-agent providers. Use when a watcher polls assigned PRs, selects models, launches Codex/OpenCode review workers, deduplicates heads, and reports completion through Telegram or another notifier.
---

# GitHub Review Runner

Use deterministic orchestration around provider agents. Keep GitHub targeting, exact-head deduplication, process lifecycle, model selection, review invocation, and notifications outside provider-specific prose where possible.

## Workflow

1. Read repository instructions and review contract before changing runner behavior.
2. Verify live GitHub access directly with the exact CLI context the worker will use:
   - `gh auth status -h github.com`
   - `gh pr view <number> --repo OWNER/REPO --json number,state,headRefOid`
   Do not infer auth health from a different shell, parent process, or earlier command.
3. Validate installation/receipt integrity before PR lookup when repository policy requires managed helpers. If receipt hashes drift, identify whether current files match current source and whether receipt is stale before overwriting anything.
4. Select model from a real provider usage signal. Never derive quota percentage from token counts or cost totals. Use strict threshold semantics explicitly (`> 30`, not `>= 30`) and safe fallback on missing/invalid telemetry.
5. Launch provider in noninteractive mode while preserving review-command safety boundaries. Prefer Codex `codex exec --sandbox read-only --model <provider-model> <prompt>`. If sandbox isolation prevents required authenticated GitHub access, use `--sandbox danger-full-access` only when the prompt and contract explicitly forbid implementation edits and GitHub writes; record this mode in verification. Do not use generic OpenCode slash-command behavior as a substitute for the repository review contract.
6. Preserve exact review target and head SHA. Skip matching active processes and previously handled heads. Persist terminal child status, but treat only `completed` and `already_reviewed` as terminal skip states. `blocked`, `failed`, and interrupted/timeout states must remain retryable after the process is gone; otherwise one transient failure can permanently suppress review. New head SHA must always remain eligible.
7. Classify child result from observed output, not process exit code alone. `blocked` preflight is not `completed`; it produces no review bundle or GitHub findings. Keep the review retryable until a real completed result or matching GitHub review exists. Parse the provider's final response segment, not the entire transcript: contract prose, tool output, and prior attempts can contain words such as `blocked` or `configuration blocker` without describing the terminal result. Require a canonical GitHub review URL bound to exact head before marking `completed`; exit code zero without receipt is failed/retryable.
8. Launch noninteractive providers with stdin closed (`stdin=DEVNULL` or equivalent). Cron stdin can remain open and make Codex wait for additional input. Catch timeout output robustly because Python may return mixed `bytes`/`str` fields from `TimeoutExpired`; decode bytes before concatenation.
9. Capture each attempt in a fresh, uniquely named log opened with truncation/write mode. Never append attempts for the same PR/head; stale text can create false status classifications and contaminated evidence. Store selected log path in state.
10. Treat semantically equivalent authoritative contract headings as valid only when their requirements are structurally present and the checker supports them; do not force a blocked result merely because legacy heading names differ. Conversely, do not weaken missing/contradictory evidence gates.
11. For cron runtimes with a foreground deadline, launch a detached waiter that owns batch completion and notification. Keep one batch state file, deduplicate PR/head entries, wait for every child, then send exactly one aggregate notification. Do not use direct single-PR mode to test aggregate delivery.
12. Send notification only after child exit and receipt classification. Include PR number, verdict, canonical URL, draft/deferred entries, and terminal status. Verify notification command result and batch-state cleanup; do not claim user-visible delivery from a worker exit alone.
13. Verify output after execution: provider, model, exit/status, review artifact or explicit blocker, head identity, duplicate behavior, and notification attempt. Report blockers plainly; do not claim review completion when preflight stopped it.
14. For own-PR remediation, select only open, non-draft PRs authored by the configured user, and exclude all self-review aliases before selecting external feedback. Accept external review on an older head: stale review evidence is a remediation trigger, not a skip condition. Re-fetch current head, mergeability, and threads before any write.
15. Treat conflict reconciliation as a separate bounded delivery stage. Prefer normal main merge under non-force policy. If true rebase is explicitly authorized, bind it to the exact remote head lease and verify the resulting head before review/fix; never blind-force push.
16. Run the remediation loop as review → classify external findings → fix safe findings → validate → one bounded push → reviewer comment → fresh review. Do not invent code fixes for evidence-only or question findings; preserve those as blockers. Only a verified clean current-head review ends the loop.
17. If native Argus execution fails, verify the failure, create one concrete issue through `/issue`, then continue with another native path or isolated fallback worker. Record issue URL, exact error, head, and host evidence. Parallelize independent PR workers, but serialize each PR's own head-changing loop.
18. Separate worker completion from success. A zero exit code with no pushed/verified head, review receipt, or explicit blocker is incomplete and must not be reported as done.
20. During manual recovery, distinguish scheduler acknowledgement from actual execution. A paused no-agent job may return `executed: false` or `execution_skipped: already being fired`; verify child PID, fresh log bytes, and state transition before assuming launch. Inspect no-agent script CLI handling before passing flags: an unimplemented `--help` can fall through to the production watcher path and launch every eligible PR. Prefer one exact target/head invocation for recovery, then verify live GitHub receipt fields directly.

## Provider credential boundary

Provider sandboxes may have a different environment, HOME, keychain access, or token precedence than the host shell. A host-side `gh pr view` success does not prove a Codex child can authenticate. Test the exact child path. Do not blindly inject `GH_TOKEN`: an invalid/stale variable overrides valid keychain authentication. Prefer an authenticated `GH_BIN` wrapper that is reachable inside the worker environment and deliberately controls token-variable precedence, or pass a valid short-lived token through an approved secret channel without logging it.

When debugging apparent auth contradiction, compare these separately:

- host `gh` with `GH_TOKEN`, `GITHUB_TOKEN`, and enterprise token variables unset;
- worker `gh` using the same `GH_BIN` and environment;
- actual PR read, not only `auth status`.

Do not print tokens, `gh auth token` output, credential files, or masked values into logs.

## Installation receipt handling

A hash mismatch can mean stale receipt after checkout/version drift, not tampering. Compare current managed files with current source before repair. Use the installer’s supported `update`/receipt-write path. Do not uninstall a receipt-managed installation merely to bypass conflicts unless the removal scope is reviewed and restoration is guaranteed. Re-run doctor after any receipt change and record host/kernel for installation-sensitive evidence.

## Notification contract

Completion notifier must be idempotent with respect to one PR head and run only after terminal child classification. Recommended message states: `completed`, `blocked`, `failed`, or `cancelled`. A launcher exit of zero means provider process exited, not necessarily successful review. Keep notifications read-only; never publish GitHub findings as part of automatic review unless separately authorized.

## References

- See `references/codex-gh-auth.md` for provider-sandbox auth diagnosis and safe probe sequence.
- See `references/review-runner-checklist.md` for exact verification checklist.
- See `references/own-pr-remediation.md` for own-PR eligibility, conflict reconciliation, review/fix looping, fallback, parallelism, and completion proof.
