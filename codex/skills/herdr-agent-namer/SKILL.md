---
name: herdr-agent-namer
description: Rename the current Herdr agent from the repository's first name component and an explicit issue number when working issue-scoped tasks.
---

# Herdr Agent Namer

Use this skill when beginning work in a Herdr-managed repository, when the user asks to rename the current agent, or when an issue number becomes known.

The skill is user-level: do not create, edit, or stage files in the repository for this convention.

## Naming rule

1. Determine the repository root with `git rev-parse --show-toplevel` and take the first hyphen-separated component of its basename. For example, `agent-dev-command-harness` becomes `agent`.
2. If the task has an explicit issue number, use `<repo-first-word>-<issue-number>` (for example, `agent-72`). Do not guess an issue number.
3. Without an issue number, use `<repo-first-word>`.
4. Herdr names must be lowercase and contain only letters, digits, `-`, or `_`; use the hyphenated form above.

## Rename

Rename only the current agent pane, identified by `$HERDR_PANE_ID`:

```sh
herdr agent rename "$HERDR_PANE_ID" "$name"
```

Before mutating, confirm that `HERDR_PANE_ID` is set and that `herdr agent list` is available. If the requested name is already taken, inspect the listed pane and report the collision rather than renaming another agent or clearing a name automatically. Verify the result with `herdr agent get "$HERDR_PANE_ID"`.

If the user explicitly requests a different descriptive name (such as `herdr-researcher`), honor that request, subject to Herdr's lowercase slug rules; spaces should become hyphens.
