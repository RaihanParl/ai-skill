---
description: Interactively install and validate a complete /goal workflow in the current workspace.
agent: setup-goal
model: openai/gpt-5.6-sol
---

Use `setup-goal` skill.

Setup preferences: $ARGUMENTS

Operate from the current directory. Discover repositories before asking configuration questions. Ask one setup question at a time. Install only from the setup-goal skill templates, validate every generated component, and never request or store credentials. Generated `/goal` runs use one plan approval only, review integrated changes before full repository tests and QA, then continue autonomously within approved scope.
