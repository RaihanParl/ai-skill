# Argus review watcher failure modes

Use this note when a watcher claims completion but users see no useful review or Telegram message.

## Required evidence

1. Read per-PR state, but treat it as bookkeeping only.
2. Query live PR head and review list through the mandatory GitHub wrapper.
3. Match reviewer actor, event state, review ID, canonical URL, and `commit_id` to current head.
4. Require a canonical review URL before marking worker `completed`.
5. Treat `REVIEW BLOCKED`, no URL, invalid ledger, or timeout as incomplete/retryable.

## Cron process design

Hermes no-agent cron can be killed around 120 seconds. Do not make cron parent wait for Codex reviews. Persist batch membership, launch workers detached, then launch a detached waiter. Waiter polls worker state/processes and sends exactly one Telegram summary after all entries settle. Delete batch receipt only after send command succeeds.

## Codex subprocess safeguards

Use `stdin=subprocess.DEVNULL` for noninteractive `codex exec`. Set a bounded long timeout. In `TimeoutExpired`, decode `stdout` and `stderr` independently because Python can return mixed `bytes`/`str` values even with `text=True`.

## Review contract compatibility

Keep review prompt and ledger checker aligned. If authoritative source uses semantic heading variants, teach both layers. Do not weaken exact-head, trust, receipt, identity, or publication gates. A model report that says `approve` while active findings remain is invalid; require regeneration or classify failure.
