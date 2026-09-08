# OpenCode usage audit

Use when user asks why usage/cost is high, or when a session feels like it burned too fast.

## Fast checks

1. `opencode stats` for recent aggregate cost/tokens.
2. Inspect local SQLite for hotspots:
   - `~/.codex/state_5.sqlite` for thread metadata and token totals.
   - `~/.codex/thread_history_1.sqlite` for turn counts.
3. Rank by `tokens_used`, then by turn count.
4. Check whether burn came from:
   - massive prompt/context
   - recursive subagent fanout
   - long review/fix loops
   - repeated giant one-shot jobs
   - tool spam inside a single session

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

## Triage pattern

- If 1-3 sessions dominate tokens, inspect their prompts. Usually recursion or giant task briefs.
- If turn count is high, look for repeated clarification, retries, or subagent loops.
- If one-shot sessions still burn hard, the prompt/task scope is too large.
- If `opencode stats` looks small but Codex feels expensive, check `~/.codex` too. They are separate usage pools.

## Reporting

When summarizing, give:
- top session IDs
- token count per session
- turn count per session
- dominant pattern
- direct fix recommendation

Keep it blunt. Do not guess.
