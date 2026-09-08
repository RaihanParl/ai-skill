# Breakdown personal output template

Copy this structure into the cwd markdown file. Replace placeholders. Keep headings stable.

```markdown
# Parallel agent plan — <KEY or DEL> — <name> — <YYYY-MM-DD>

## Scope
- Jira: <url>
- Person: <name>
- Issues considered: <keys>
- Repos inspected: <~/proj/...>
- Confidence: high | medium | low
- Notes: <assumptions / missing repos / MCP gaps>

## Parallel agent lanes (run now)

### Lane A — worktree `wt-<key>`
- Tickets: <KEY> — <summary>
- Repo: `~/proj/<repo>`
- Focus paths: `<dir/file>`
- Why safe alone / with others: <one line>
- Safe with: Lane B, …
- Agent prompt: <one pasteable sentence>

### Lane B — worktree `wt-<key>`
- …

## Sequential chains
- <KEY-A> → <KEY-B> → <KEY-C>
  - Reason: <Jira block | shared schema | API contract | …>

## Do not parallel (even if no Jira link)
- <KEY-X> + <KEY-Y>
  - Conflict: <same package / migration / files>
  - Prefer: run <KEY-X> first, then <KEY-Y>

## Deferred / unclear
- <KEY> — <why unclear; what to check>

## Suggested run order
1. Start lanes: A + B (parallel)
2. After A merges/lands: start C
3. …
```
