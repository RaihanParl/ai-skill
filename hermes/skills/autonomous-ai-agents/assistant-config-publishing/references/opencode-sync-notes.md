# OpenCode assistant-config sync notes

Use this when mirroring OpenCode-based assistant configuration into the publishing repo.

## What to mirror

- `opencode/opencode.jsonc`: the readable global config source.
- `opencode/opencode.json`: the effective runtime manifest when the tool writes a separate file.
- `opencode/AGENTS.md`: always-on rules injected into OpenCode sessions.

## When it matters

- After installing a rule-based agent or plugin that affects OpenCode session behavior.
- After changing the global plugin list.
- After any edit that should be reproducible from the dedicated config repo.

## Practical pattern

1. Install or update the agent/plugin locally.
2. Inspect the generated OpenCode files.
3. Mirror the changed files into the repo under `opencode/`.
4. Commit and push in the same change set.
5. Verify the repo is clean and the remote HEAD advanced.

## Example from the current session

- `ponytail` was added as a global OpenCode plugin.
- `caveman` was installed into OpenCode and added a caveman block to `opencode/AGENTS.md`.
- The repo mirrored both the config and the injected rules, then pushed the update.
