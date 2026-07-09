---
name: setup-goal
description: Interactively scaffold /goal into any project. Asks ticket system, project key, branch target, model prefs, then writes command/skills/agents/goal state.
---

# Setup Goal

Use for `/setup-goal` requests.

## Mission

Interactively scaffold the full `/goal` execution loop into whatever project the user is currently in.

## Scope

The agent (`setup-goal`) is responsible for the interactive Q&A session. This skill provides the templates, the question flow, and the file-writing rules; the agent orchestrates the conversation and writes the files.

## Question flow

Ask ONE question at a time. Wait for answer. Do not batch.

1. Check for existing `.opencode/command/goal.md`. If exists → ask overwrite or cancel.
2. Detect child repos for FE/BE. Run `ls -d */` and sniff for web/API markers. Show findings.
3. "Which ticket system?" → Jira / GitLab / None
4. (Jira) "Jira project key?" (e.g. TOTS)
5. (Jira) "Jira site URL?" (e.g. https://my-site.atlassian.net)
6. (GitLab) "GitLab project path?" (e.g. user/repo)
7. (GitLab) "Branch target?" (default: main)
8. "Branch target for MRs?" (default: dev for Jira, main for GitLab)
9. "Planning model?" (default: openai/gpt-5.4)
10. "Execution model?" (default: opencode deepseek v4 flash free)
11. "FE repo folder?" (detected or manual)
12. "BE repo folder?" (detected or manual)

## File writing

Write these files into the project root:

- `.opencode/command/goal.md`
- `.opencode/skills/goal-loop/SKILL.md`
- `.opencode/agent/goal-orchestrator.md`
- `.opencode/agent/goal-planner.md`
- `.opencode/agent/goal-builder.md`
- `.opencode/agent/goal-reviewer.md`
- `.opencode/agent/goal-visual-reviewer.md`
- `.goal/state.json`

Use exact templates from the agent instruction.

## Templates source

Reference templates:
- Jira flow: `/Users/mraihanparlaungan/proj/tara/.opencode/command/goal.md` and siblings
- GitLab flow: `/Users/mraihanparlaungan/personal/lukre/content-generator/.opencode/command/goal.md` and siblings
- None flow: simplified version without ticket ops

## Project detection

```bash
# list child dirs
ls -d */ 2>/dev/null

# FE markers
test -f "$dir/package.json" && grep -q '"next"' "$dir/package.json" 2>/dev/null
test -f "$dir/package.json" && grep -q '"react"' "$dir/package.json" 2>/dev/null

# BE markers
test -f "$dir/requirements.txt"
test -f "$dir/app.py" || test -f "$dir/main.py"
test -d "$dir/api"
```

## Error handling

- If user cancels mid-way, delete any partially written files.
- If writing fails, show exact path and error.