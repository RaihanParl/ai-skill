---
name: breakdown
description: Use when the user says /breakdown, asks to break down requirements, or wants issue drafts for GitHub, GitLab, or Jira. Produces user-level, dependency-aware, goal-ready tasks and asks before publishing.
---

# Breakdown

Convert requirement, objective, roadmap, or planning documents into user-level issue drafts. Default to dry-run.

## User-Level Boundary

Every issue must represent one outcome a user, operator, or stakeholder can recognize as complete.

- Prefer vertical slices: keep UI, API, data, and tests for one outcome in one issue.
- Do not create layer-only issues such as "add endpoint", "build component", or "update schema" unless that layer delivers independent value.
- Write titles as capabilities or resolved problems, not implementation steps.
- Write acceptance criteria as observable behavior. Put routes, files, schemas, and implementation guidance under `Technical Notes`.
- Split an outcome only when each resulting issue remains independently usable or verifiable.
- Preserve technical objectives such as security audits, performance targets, migrations, or ADRs, but state their stakeholder outcome first.

Before emitting a draft, ask: "Could a user or stakeholder verify the value without reading the implementation?" If not, merge it into its parent outcome or rewrite it.

## Workflow

1. Read the referenced sources.
2. Extract outcomes, constraints, dependencies, risks, and stated estimates.
3. Group implementation details into user-level vertical slices.
4. Build a dependency graph, including explicit and necessary implicit dependencies.
5. Assign phases: Phase 1 has no blockers; later phases depend on earlier work. Tasks in one phase may run in parallel.
6. Rank by unblock value, user value, risk, effort, and confidence.
7. Produce directly executable issue drafts with phase and dependency metadata.
8. Ask whether to revise, publish, or run a selected draft.

Do not invent requirements. Prefer fewer complete outcomes over many technical subtasks.

## Draft Format

```markdown
## Breakdown

### Execution Plan
| Phase | Tasks | Parallel? |
|-------|-------|-----------|
| 1 | U1, U2 | Yes |
| 2 | U3 | After U1 |

### Recommended Order
1. [ID] User-level title - value, effort, phase, and rationale

### Issue Drafts
#### [ID] User-level title
**Goal**: <desired outcome>
**User Outcome**: <who benefits and what becomes possible or reliable>
**Context**: <source and concise problem summary>
**Done When**:
- <observable acceptance criterion>

**Technical Notes**:
- <source-supported constraints or implementation guidance>

**Execution**:
- Source: `<file:line-range>`
- Phase: <N>
- Parallel With: <IDs or None>
- Depends On: <IDs or None>
- Risks: <risks>
- Estimate: <source estimate or small/medium/large>
- Labels: <phase and priority labels>
```

## Publishing Safety

- Never publish without explicit approval.
- Use available GitHub, GitLab, or Jira tools after approval.
- If destination details or credentials are missing, ask one concise question.
- Return created links; never claim publication when it failed.

Always end dry-runs with:

```markdown
Next:
1. Revise these drafts?
2. Publish to GitHub/GitLab/Jira?
3. Run a selected draft?
```
