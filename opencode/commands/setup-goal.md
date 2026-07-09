---
description: Interactively scaffold /goal into the current project. Asks ticket system, project key, branch target, FE/BE detection, and all config needed.
agent: setup-goal
model: openai/gpt-5.4
---

# /setup-goal

Interactively scaffold a `/goal` loop into the current project.

Use `setup-goal` skill.

User intent:

$ARGUMENTS

Operate from current folder as project root.

Rules:
- Detect if `.opencode/command/goal.md` already exists. If yes, ask user if they want to overwrite or cancel.
- Ask ALL questions iteratively — one at a time — don't batch, give user space to think.
- Ask about: ticket system (Jira/GitLab/none), project key, branch target, FE/BE detection, Jira credentials if needed (URL, email, token), model preferences.
- Write `.opencode/command/goal.md`, `.opencode/skills/goal-loop/SKILL.md`, `.opencode/agent/goal-*` agents, and `.goal/state.json`.
- For Jira flow: use same structure as tara's /goal but with user-provided project key.
- For GitLab flow: use same structure as content-generator's /goal but with user-provided project path.
- For "none" flow: create a plan-and-execute loop without ticket system.
- After scaffold, print a summary of what was created and next steps.