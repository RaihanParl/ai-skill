# Parallel agent plan — DEL — Raihan — 2026-07-29

## Scope
- Jira: https://smpobtransjakarta.atlassian.net/jira/software/projects/DEL/boards/1
- Person: Raihan
- Issues considered: DEL-5120, DEL-5128, DEL-5133, DEL-5141, DEL-5150
- Repos inspected: `~/proj/smpob-api/tije-smpob-api`, `~/proj/weltevreden`
- Confidence: medium
- Notes: Sample only. Assignee filter matched open DEL tickets; GitNexus not used. DEL-5150 has no clear local path yet.

## Parallel agent lanes (run now)

### Lane A — worktree `wt-del-5120`
- Tickets: DEL-5120 — Add rostering lite list filter by depot
- Repo: `~/proj/smpob-api/tije-smpob-api`
- Focus paths: `internal/rostering/`, `handlers/rostering_lite.go`
- Why safe alone / with others: Touches rostering list API only; no shared migration with Lane B
- Safe with: Lane B
- Agent prompt: Implement DEL-5120 depot filter on rostering lite list in tije-smpob-api; keep changes inside rostering list handler/repo; add scoped tests.

### Lane B — worktree `wt-del-5128`
- Tickets: DEL-5128 — Fix Weltevreden timetable card empty state
- Repo: `~/proj/weltevreden`
- Focus paths: `src/components/TimetableCard/`
- Why safe alone / with others: Different repo and UI-only; no API contract change
- Safe with: Lane A
- Agent prompt: Fix DEL-5128 empty state on TimetableCard in weltevreden; no API changes; keep UI scoped to that component.

## Sequential chains
- DEL-5133 → DEL-5141
  - Reason: DEL-5133 adds `rostering_lite.depot_id` migration + model; DEL-5141 BE filter depends on that column and API field

## Do not parallel (even if no Jira link)
- DEL-5120 + DEL-5141
  - Conflict: both edit `handlers/rostering_lite.go` and list query builder
  - Prefer: finish Lane A (DEL-5120), then DEL-5141 after DEL-5133 lands

## Deferred / unclear
- DEL-5150 — "Align PIS worker heartbeat" — no matching dir under `~/proj` with high confidence; confirm repo before laneing

## Suggested run order
1. Start lanes: A + B (parallel agents / worktrees)
2. After A merges: run DEL-5133 (migration) alone
3. After DEL-5133 lands: run DEL-5141
4. Clarify repo for DEL-5150, then schedule
