---
name: breakdown
description: Use when the user says /breakdown, breakdown tasks, parse OBJECTIVES.md, create issue drafts, or publish-ready tasks for GitHub/GitLab/Jira. Turns objective docs into ranked, dependency-aware, goal-ready plans and asks before any publishing step.
---

# Breakdown

Convert objective docs into clear goal-ready, issue-ready tasks. Default safe mode: dry-run only.

## Trigger

Use for:
- `/breakdown @OBJECTIVES.md`
- `/breakdown @file --target github|gitlab|jira`
- task breakdown from requirements, challenge docs, roadmap docs
- issue draft generation for GitHub/GitLab/Jira
- goal-ready task plans with required agents per task

## Model

Planner should use strongest available frontier model. Prefer `GPT-5.6 Sol` when available. If exact model ID is unknown, do not guess config; ask or use current strongest model.

## Inputs

Accept natural language or flags:

```text
/breakdown @OBJECTIVES.md --dry-run
/breakdown @OBJECTIVES.md --top 5
/breakdown @OBJECTIVES.md --target github --repo owner/repo
/breakdown @OBJECTIVES.md --target gitlab --project group/project
/breakdown @OBJECTIVES.md --target jira --project SW --type Task
```

## Safety

- Default to plan-only.
- After plan, ask if drafts are good enough or need edits.
- Then ask whether to publish to GitHub/GitLab/Jira.
- If current agent cannot publish because shell/API tools are unavailable, spawn or delegate to an agent that has the needed tools.
- If no capable publisher exists after delegation, output copy-paste commands and issue bodies instead of pretending.
- If destination metadata missing, ask one question.
- Preserve source meaning; do not invent requirements.
- Prefer fewer, high-value issues over noisy one-objective-per-line dumping.

## Dependency Analysis

Before ranking, build a dependency graph:

1. For each objective, scan for explicit and implicit dependencies.
   - Explicit: "depends on X", "requires X", "after X is done"
   - Implicit: shares a service/engine that must be correct first (e.g. availability engine used by bookings, reports, UI)
2. Identify blocked-by relationships between tasks.
3. Group tasks into execution phases:
   - **Phase 1**: no dependencies (can start immediately)
   - **Phase 2+**: depend on Phase 1 tasks completing
   - Within each phase, all tasks are independent and can run in parallel.
4. Assign parallel groups: phase number is the parallel group. All tasks in same phase run concurrently.
5. Compute total points unlockable per Phase 1 task to prioritize high-unblock tasks first.

## Workflow

1. Read provided doc/path.
2. Extract objectives, constraints, dependencies, risks.
3. Build dependency graph (see Dependency Analysis above).
4. Group into execution phases (parallel groups).
5. Rank within each phase by: unblock value > point value > effort.
6. Produce goal-ready issue drafts with phase/parallel metadata.
7. Include required agents for each task.
8. Ask: "Are these issue drafts good, or should I revise?"
9. Ask: "Publish to GitHub/GitLab/Jira now?"
10. Publish only if user approves.
11. If publishing, include execution phase and parallel group info in issue bodies and add phase:1/phase:2/priority:critical/priority:high/priority:medium labels.
12. If the current agent lacks publishing tools, delegate publishing to a shell/API-capable agent.
13. Return created links, or copy-paste commands if publishing still cannot run.

## Ranking

Score each task:
- value: user/product/test points
- unblock: total points of tasks this task enables (high unblock = high priority)
- risk: security/data-loss/regression risk
- effort: small/medium/large
- confidence: clear/ambiguous

Then apply:
1. Build dependency graph and assign phases.
2. Sort Phase 1 tasks by unblock value descending, then by point value descending.
3. Sort Phase 2+ tasks within their phase by point value descending.
4. The top Phase 1 task is the single most valuable thing to start first.

Prefer tasks with high value, high unblock, low ambiguity.

## Output: dry-run

```markdown
## Breakdown

### Execution Plan

| Phase | Tasks | Parallel? |
|-------|-------|-----------|
| 1 (do first) | X1, B3, X3, ... | Yes — all run concurrently |
| 2 (after X1) | B2, F2, D1, ... | Yes — all run concurrently |

**Why start with X1:** blocks B2+F2+D1 (27pts unblocked). Fix availability so downstream work is correct.

### Recommended order
1. [ID] Title — value, effort, phase, parallel group, why first

### Goal-ready issue drafts
#### [ID] Title
Goal: <title>
Context: <source + summary>
Done when:
- ...acceptance criteria...
Required agents:
- planner: scope/dependencies/risks
- builder: implementation
- reviewer: correctness/security/regression
Issue fields:
- Source: `file:line-range`
- Execution Phase: Phase [1/2/N]
- Parallel Group: can run with [comma-separated list of same-phase issues]
- Depends On: [phase 1 issue IDs, or "None"]
- Dependencies:
- Risks:
- Labels:
- Estimate:
```

## Output: follow-up prompt

After drafts, always end with:

```markdown
Next:
1. Revise these drafts?
2. Publish to GitHub/GitLab/Jira?
3. Run selected draft with `/goal`?
```

## Issue template

Each issue must include:
- title
- summary
- acceptance criteria
- execution phase
- parallel group (which other issues can run concurrently)
- dependencies (which issues block this one)
- risk notes
- source excerpt or line reference
- labels
- estimate/points when available

When publishing to GitHub/GitLab/Jira, include execution phase and parallel group in the issue body. Add GitHub labels: `phase:1`, `phase:2` (or N), `priority:critical|high|medium`.

## Platform mapping

GitHub:
- title, body, labels, assignee/milestone if provided
- preferred publisher: `gh issue create`
- before publishing, verify `gh` exists and is authenticated with `gh auth status`
- if `gh` is missing and shell install is allowed, install it with the platform package manager, then re-check auth
- if current agent has no shell access, spawn/delegate to a shell-capable agent to run `gh`

GitLab:
- title, description, labels, weight if provided
- preferred publisher: `glab issue create` when available, otherwise GitLab API/tool if configured
- if current agent has no shell/API access, spawn/delegate to a capable agent

Jira:
- project key, issue type, summary, description, labels/custom fields if provided
- preferred publisher: configured Jira/Atlassian tool
- if current agent has no Jira tool access, ask for configuration or output copy-paste bodies

## Publishing delegation

Do not let missing tools in the current agent block the workflow.

When user approves publishing:
- Use available native API tools first.
- For GitHub, use `gh` when shell is available.
- If current agent lacks shell/API tools, spawn a capable publishing agent with exact approved drafts and destination metadata.
- The publishing agent must only create approved issues; no edits to source code.
- If delegation is unavailable or still lacks credentials, return exact commands/bodies for manual execution.

## Publishing updates

When issues are already published but lack execution metadata, update them:

1. Fetch current body with `gh issue view <num> --json body --jq .body`
2. Append phase/parallel/depends metadata to body.
3. Write back with `gh issue edit <num> --body-file -` piping from `printf '%s\n\n%s' "$body" "$extra"`.
4. Add labels: `phase:1|2|N` and `priority:critical|high|medium`.

Example extra metadata block:
```
## Execution Phase: Phase 1
## Parallel Group: can run with X1, B3, X3, X2, X4, ADR, B1, F1, F3
## Depends On: None
```

Always make every dry-run draft directly pasteable into `/goal`. No flag or extra user mention required.
