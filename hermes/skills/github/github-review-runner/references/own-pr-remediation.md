# Own-PR Remediation Reference

Use for a watcher that repairs the current user's already-reviewed pull requests.

## Eligibility

- PR must be open and non-draft.
- PR author must match configured identity.
- Maintain an explicit alias set for accounts representing the same user; exclude all aliases from external-review selection.
- Require actionable or unresolved external review evidence. A review on an older head still qualifies: it means the PR needs current-head reconciliation and re-review.
- Do not treat self-authored review text as external feedback.

## Per-PR state machine

```text
eligible
  -> preflight current PR/head/reviews/threads
  -> reconcile main if conflicting or behind
  -> review current exact head
  -> classify external findings
  -> fix safe findings
  -> validate
  -> one bounded push
  -> comment original reviewer
  -> fresh review
  -> repeat or terminal clean/blocker
```

Serialize this state machine per PR because each fix changes head. Run independent PR state machines in parallel.

## Reconciliation

Prefer normal merge of live `main` when policy requires non-force delivery. True rebase rewrites the remote branch and needs explicit authorization, exact remote-head lease, and post-push identity verification. Never blind-force push.

## Finding policy

- Fix only active findings tied to external review and classified `safe_fix`.
- Evidence gaps, questions, scope changes, unsafe repairs, and unavailable validation remain blockers.
- Do not invent implementation changes when review has zero code findings.
- After every push, run fresh `/review` at the new exact head. Only clean current-head evidence ends the loop.

## Native fallback

When native Argus execution fails, verify the failure first. Create one concrete issue with `/issue`, including exact error, target/head, timestamp, host/kernel, and attempted command. Then use another native path or isolated fallback worker. Preserve the issue URL and blocker in final state.

## Cron launcher pattern

For scheduled remediation, keep cron foreground work short. Acquire a nonblocking scheduler lock, enumerate eligible PRs, and launch one detached worker per PR with `stdin=DEVNULL`, unique log path, and persisted `{pr, head, external_review_id, pid, status}` state. Serialize each PR's head-changing loop, but launch independent PR workers concurrently. Next tick skips a live PID and skips a terminal `{head, external_review_id}` pair; a new head or new external review reopens work. Do not use process exit code as completion proof. Worker sends one bounded summary after classification; cron delivery may remain local when worker owns explicit Telegram delivery.

Before enabling cron, run a dry-run against a PR with both a stale external review and self-authored reviews. Verify the stale external review qualifies, every configured self alias is excluded, conflict state is reported, and no worker or GitHub mutation occurs. Then trigger one live tick and verify state, exact head, push/comment receipts, and no duplicate worker on the next tick.

## Completion proof

Require all relevant receipts before claiming success:

- exact current PR head;
- merge/rebase result and branch identity;
- commit parent and non-force push receipt;
- fresh review result and canonical URL or explicit blocker;
- reviewer comment URL;
- Telegram send result and aggregate batch cleanup.

A worker exit code of zero alone proves nothing.
