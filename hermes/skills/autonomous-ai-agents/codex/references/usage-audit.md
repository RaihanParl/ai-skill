# Codex usage audit

Use when user asks where Codex usage went, or when one day of work burns far more than expected.

## Fast checks

1. `codex stats` and `codex doctor` for aggregate state.
2. Inspect local SQLite under `~/.codex/`.
3. Rank by `tokens_used` first.
4. Then check turn counts and thread histories.

## Useful files

- `~/.codex/state_5.sqlite` — thread metadata, token totals, model, cwd, source
- `~/.codex/thread_history_1.sqlite` — turn counts and rollout history
- `~/.codex/logs_2.sqlite` — log events

## Helpful SQL

```sql
select id, title, source, model_provider, model, tokens_used, created_at, updated_at, cwd
from threads
order by tokens_used desc
limit 20;
```

```sql
select thread_id, count(*) as turns, min(started_at) as first_start, max(completed_at) as last_end
from thread_turns
group by thread_id
order by turns desc
limit 20;
```

```sql
select source, model_provider, model, count(*) as n, sum(tokens_used) as tokens, avg(tokens_used) as avg_tokens
from threads
where updated_at >= strftime('%s','now') - 86400
group by source, model_provider, model
order by tokens desc;
```

## Triage order

- Find top token hogs.
- Check whether prompts are massive or recursive.
- Check whether many subagents were spawned.
- Check whether one thread is looping on retries or tool spam.
- Separate Codex usage from OpenCode usage. They are different pools.

## Reporting

When reporting back, say:
- top thread IDs
- token totals
- turn totals
- dominant cause
- practical fix

Do not guess. Use local DB facts.
