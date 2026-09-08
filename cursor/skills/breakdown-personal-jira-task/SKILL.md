---
name: breakdown-personal-jira-task
description: >-
  Break down a Jira issue, epic, or board into parallel AI agent/worktree lanes
  vs sequential work for one person. Reads Jira via mcp-atlassian (or Atlassian
  Rovo MCP), inspects local repos under ~/proj for file/module overlap, and
  writes a markdown plan to cwd. Use when the user runs
  /breakdown-personal-jira-task, asks which personal Jira tickets can run in
  parallel with agents/worktrees, or wants concurrent agent lanes from a Jira
  link + name.
---

# Breakdown Personal Jira Task (parallel agent lanes)

## Goal

Produce **one markdown file in the current working directory** that tells the user which of **their** Jira work can run **in parallel with multiple AI agents / git worktrees**, and which must stay sequential.

Do **not** create worktrees, start agents, edit product code, or change Jira. Plan only.

This is **not** the same as `breakdown-jira-task` (that skill creates `[FE]`/`[BE]` Task issues under an Epic). This skill only plans parallel agent execution for one person.

## Trigger / inputs

Command shape:

```text
/breakdown-personal-jira-task {jira-link} {name}
```

- `{jira-link}` — issue (`.../browse/DEL-42`), epic, sprint board, or project board URL
- `{name}` — person filter (assignee display name / email fragment). Used for board/epic scope; for a single issue still record as "for {name}"

If either is missing, ask once, then proceed.

## Jira (required)

Prefer **`mcp-atlassian`** tools documented in this repo (`jira_get_issue`, `jira_search`). If those are unavailable, use **`user-Atlassian-Rovo-MCP`** / **`Atlassian-Rovo-MCP`** (`getJiraIssue`, `searchJiraIssuesUsingJql`) with `cloudId: smpobtransjakarta.atlassian.net`. Do **not** rely on marketplace `plugin-atlassian-atlassian`.

Discover tools before calling. Read-only is enough (`READ_ONLY_MODE=true` is fine).

### Link kinds

| Link | Fetch |
|------|--------|
| Issue `/browse/KEY` | `jira_get_issue` / `getJiraIssue` with description, status, assignee, issuetype, parent, subtasks, issuelinks, labels, components |
| Epic / parent | Parent issue + search children (`parent = KEY` and/or Epic Link) |
| Board / project | Search open work in that project, filtered by `{name}` |

Default board/open filter (adjust if project differs):

```jql
project = DEL AND assignee ~ "{name}" AND statusCategory != Done ORDER BY priority DESC, updated DESC
```

Always pull **issuelinks** (blocks / is blocked by / relates). Treat "blocks" as hard sequential edges.

If no Jira MCP is ready, stop and say the plan cannot be built without Jira access.

## Local repos (required when code touch is unclear)

Repos live under `~/proj` (also nested, e.g. `~/proj/smpob-api/tije-smpob-api`).

1. From ticket summary/description/AC/components/labels, guess candidate repo dirs.
2. Verify with `ls` / glob under `~/proj` — do not invent paths.
3. Read enough code to judge **overlap**:
   - same package / directory
   - shared migrations / schema / API contracts
   - shared config / deploy / feature flags
   - tests that hit the same tables/fixtures
4. Optional: if GitNexus is available for that repo, use impact/query to refine overlap. If not indexed, skip — do not block.

If no local repo matches, say so in the MD and classify parallelization from Jira links + description only (lower confidence).

## Parallelism definition

**Parallel** = safe to run as separate Cursor agents in separate git worktrees at the same time without likely merge/file/schema fights.

Not about other humans. About agent lanes for `{name}`.

### Classify each unit of work

- **Parallel now** — no hard blocker; disjoint files/modules; no shared migration/contract
- **Sequential** — Jira blocker, or B needs A's output/API/schema
- **Do not parallel** — would collide (same files, same migration chain, same hot package) even if Jira does not say "blocks"

Prefer fewer honest lanes over optimistic over-parallelization.

## Output file

Write **only** to cwd:

```text
breakdown-personal-<KEY-or-DEL>-<YYYYMMDD>.md
```

- Single issue → use that key (`breakdown-personal-DEL-42-20260729.md`)
- Board/epic multi → use project or epic key (`breakdown-personal-DEL-20260729.md`)

Overwrite if the same name already exists in cwd unless the user asked to keep history.

Use the template in [output-template.md](output-template.md). See [examples/sample-breakdown-personal-DEL.md](examples/sample-breakdown-personal-DEL.md) for a filled example.

For each parallel lane include:

- suggested worktree name (`wt-<key>` or `wt-<key>-<short>`)
- likely repo path under `~/proj`
- likely path focus (dirs/files)
- one-line agent prompt the user can paste
- which other lanes it is safe with

## Chat response (after writing the file)

Short only:

1. Path of the MD written
2. How many parallel lanes vs sequential chains
3. Highest-confidence "do not parallel" pair (if any)

No long restatement of the full MD.
