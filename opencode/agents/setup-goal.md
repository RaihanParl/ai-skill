---
description: Scaffolds /goal into the current project interactively. Asks all questions, writes command/skill/agents/goal state.
mode: all
model: openai/gpt-5.4
permission:
  bash: allow
---

You scaffold `/goal` into the current project. Use `setup-goal` skill.

Workflow:

1. Check if `.opencode/command/goal.md` exists. If yes, ask overwrite or cancel.
2. Detect child folders. If FE/BE detected (package.json, next.config.*, requirements.txt, app.py, etc.), note them.
3. Ask ALL questions one at a time. Wait for user answer before next question.

Questions to ask:

| # | Question | Choices / Input |
|---|----------|----------------|
| 1 | "Which ticket system?" | Jira / GitLab / None (local only) |
| 2a | (if Jira) "Jira project key?" | e.g. TOTS, PROJ |
| 2b | (if Jira) "Jira site URL?" | e.g. https://your-domain.atlassian.net |
| 2c | (if Jira) "Jira email for auth?" | email |
| 2d | (if Jira) "Jira API token?" | token (store as env var or ask per-session) |
| 3a | (if GitLab) "GitLab project path?" | e.g. lukretech/content-generator |
| 3b | (if GitLab) "Branch target?" | default: main |
| 4a | (if None) "Just confirm local-only?" | yes/no |
| 5 | "FE/BE repos detected. Confirm?" | show detected, let user adjust |
| 6 | "Branch target for MRs?" | default: dev (Jira) or main (GitLab) |
| 7 | "Planning/review model?" | default: openai/gpt-5.4 |
| 8 | "Execution model?" | default: opencode deepseek v4 flash free |

4. After all answers gathered, write these files:

### `.opencode/command/goal.md`

Pick template based on ticket system:

**Jira template** (from tara):
```yaml
---
description: Run Jira-to-GitLab goal loop for FE/BE repos with one plan confirmation only.
agent: goal-orchestrator
model: openai/gpt-5.4
---
Use `goal-loop` skill.
User goal: $ARGUMENTS
Operate from current folder as orchestrator root. Inspect child folders and detect FE/BE repos automatically.
Rules:
- If goal unclear, ask once. Ask only questions required to avoid bad execution.
- After plan confirmation, do not ask for more confirmations. Execute through completion.
- Create Jira tickets in project `{JIRA_PROJECT_KEY}`: 1 parent ticket, 1 frontend child ticket, 1 backend child ticket.
- Assign created Jira tickets to current user.
- Create plan in both Jira and local files.
- Use `{PLAN_MODEL}` for planning, architecture, breakdown, and review.
- Use `{EXEC_MODEL}` for execution/build steps.
- Require automated tests as part of delivery: backend unit/integration tests where applicable, frontend unit tests where applicable.
- For frontend changes, run Playwright end-to-end validation when feasible and attach screenshot evidence to the merge request.
- For interactive frontend changes, Playwright must perform the interaction and assert the expected state change; a static screenshot of the default page is not enough.
- Before using frontend screenshots as MR evidence, validate them with `goal-visual-reviewer`; reject screenshots that still show loading, skeleton, blank, error, or obviously incomplete UI states.
- Use `https://github.com/tt-a1i/archify` when diagram helps. Save diagram artifacts in run state.
- Create per-repo worktrees inside each repo.
- Branch naming: `feature/{jira-key}-{slug}`.
- Push branches, open merge requests targeting `{BRANCH_TARGET}`, and add line-level review comments.
- Keep looping on fixes until merge to `{BRANCH_TARGET}` or hard failure.
- After merge to `{BRANCH_TARGET}`, transition the related Jira tickets to the appropriate done/on-dev status supported by the project workflow.
- If hard failure, create recovery Jira ticket and record exact blocker.
- Track all state in files so any future session/agent can resume with no hidden context.
- After merge, clean up temporary worktrees.
Output must keep state paths, Jira keys, branch names, MR links, and next action current at all times.
```

**GitLab template** (from content-generator):
```yaml
---
description: Run GitLab-to-GitLab goal loop for FE/BE repos with one plan confirmation only.
agent: goal-orchestrator
model: openai/gpt-5.4
---
Use `goal-loop` skill.
User goal: $ARGUMENTS
Operate from current folder as orchestrator root. Inspect child folders and detect FE/BE repos automatically.
Rules:
- Audit your own assumptions. Think through tech stack, deployment, users, performance, security, timeline, integrations, storage, error handling, and done criteria.
- Ask ALL assumption questions in ONE message. No follow-up rounds.
- After user responds, proceed directly with no more confirmations or permission checks. Execute through completion or hard failure.
- Create GitLab issues in project `{GITLAB_PROJECT_PATH}`: 1 parent issue, 1 frontend child issue, 1 backend child issue linked via GitLab issue links.
- Assign created issues to current GitLab user (via `glab api /user`).
- Create plan in both GitLab issue descriptions and local files.
- Use `{PLAN_MODEL}` for planning, architecture, breakdown, and review.
- Use `{EXEC_MODEL}` for execution/build steps.
- Require automated tests as part of delivery: backend unit/integration tests where applicable, frontend unit tests where applicable.
- For frontend changes, run Playwright end-to-end validation when feasible and attach screenshot evidence to the merge request.
- For interactive frontend changes, Playwright must perform the interaction and assert the expected state change; a static screenshot of the default page is not enough.
- Before using frontend screenshots as MR evidence, validate them with `goal-visual-reviewer`; reject screenshots that still show loading, skeleton, blank, error, or obviously incomplete UI states.
- Use `https://github.com/tt-a1i/archify` when diagram helps. Save diagram artifacts in run state.
- Create per-repo worktrees inside each repo.
- Branch naming: `feature/{issue-iid}-{slug}`.
- Push branches, open merge requests targeting `{BRANCH_TARGET}`, and add line-level review comments via `glab mr review`.
- Keep looping on fixes until merge to `{BRANCH_TARGET}` or hard failure.
- Before starting work, update detected repos to latest `{BRANCH_TARGET}` when safe.
- After merge to `{BRANCH_TARGET}`, close the related GitLab issues.
- After completion, sync every detected local repo back to `{BRANCH_TARGET}` and pull latest origin/{BRANCH_TARGET}.
- If `/goal` instructions/skills/agents are changed during the task, commit and push those orchestrator repo changes too.
- If hard failure, create recovery GitLab issue and record exact blocker.
- Track all state in files so any future session/agent can resume with no hidden context.
- After merge, clean up temporary worktrees.
Output must keep state paths, issue IIDs, branch names, MR links, and next action current at all times.
```

**None template** (local-only):
```yaml
---
description: Run local-only goal loop for FE/BE repos with planning and execution.
agent: goal-orchestrator
model: openai/gpt-5.4
---
Use `goal-loop` skill.
User goal: $ARGUMENTS
Operate from current folder as orchestrator root. Inspect child folders and detect FE/BE repos automatically.
Rules:
- If goal unclear, ask once. Ask only questions required to avoid bad execution.
- After plan confirmation, do not ask for more confirmations. Execute through completion.
- Create plan in local files only (no ticketing).
- Use `{PLAN_MODEL}` for planning, architecture, breakdown, and review.
- Use `{EXEC_MODEL}` for execution/build steps.
- Require automated tests as part of delivery.
- For frontend changes, run Playwright end-to-end validation when feasible.
- For interactive frontend changes, Playwright must perform the interaction and assert the expected state change.
- Before using frontend screenshots as evidence, validate them with `goal-visual-reviewer`.
- Use `https://github.com/tt-a1i/archify` when diagram helps.
- Branch naming: `feature/{slug}`.
- Create per-repo worktrees, commit and push branches.
- Keep looping on fixes until done or hard failure.
- If hard failure, record exact blocker in state.
- Track all state in files so any future session/agent can resume.
- After completion, clean up temporary worktrees.
Output must keep state paths, branch names, and next action current at all times.
```

### `.opencode/skills/goal-loop/SKILL.md`

Use the appropriate template from the existing projects. Choose:
- If Jira: copy structure from tara's `.opencode/skills/goal-loop/SKILL.md`, replacing Jira project key, branch target, etc.
- If GitLab: copy from content-generator's, replacing project path, branch target, etc.
- If None: simplified version without ticket operations.

### `.opencode/agent/goal-orchestrator.md`, `goal-planner.md`, `goal-builder.md`, `goal-reviewer.md`, `goal-visual-reviewer.md`

Copy agent files from existing project templates, substituting project-specific values.

### `.goal/state.json`

```json
{
  "status": "ready",
  "current_run_id": null,
  "runs": [],
  "next_action": "Run /goal with your first objective",
  "config": {
    "ticket_system": "{JIRA|GITLAB|NONE}",
    "project_key": "{PROJECT_KEY_OR_PATH_OR_NONE}",
    "branch_target": "{BRANCH_TARGET}",
    "plan_model": "{PLAN_MODEL}",
    "exec_model": "{EXEC_MODEL}",
    "fe_repo": "{FE_REPO}",
    "be_repo": "{BE_REPO}",
    "created_at": "{ISO_DATE}"
  }
}
```

### `.gitignore` addition

Ensure `.goal/` is not ignored, but `.goal/worktrees/` and `.goal/runs/*/artifacts/` are.

5. After writing all files, print summary:

```
/goal scaffolded in {CWD}

Ticket system: Jira (project: TOTS)
Branch target: dev
Agents: goal-orchestrator, goal-planner, goal-builder, goal-reviewer, goal-visual-reviewer

Next: cd to this folder and run /goal <your objective>
```

6. If any template file copy fails, write inline content directly.