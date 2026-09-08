---
name: breakdown-personal-jira-task
description: Break a personal Jira link into parallel AI agent/worktree lanes vs sequential work; write an MD plan to cwd.
---

Follow the `breakdown-personal-jira-task` skill exactly.

Inputs from the user after `/breakdown-personal-jira-task`:
1. Jira link (issue, epic, or board)
2. Name (assignee / person filter)

If either is missing, ask once for the missing piece, then continue.

Produce only the markdown plan in the current working directory. Do not create worktrees or start agents.

Do not confuse this with `/breakdown-jira-task` (that creates `[FE]`/`[BE]` Jira Task issues under an Epic).
