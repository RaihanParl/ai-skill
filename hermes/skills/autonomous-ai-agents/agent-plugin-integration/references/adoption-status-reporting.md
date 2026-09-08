# Adoption status reporting

Use this checklist when a user asks whether a requested tool is already in use.

## Separate the states

For each requested tool, answer all three:

1. Installed
   - Exists in local config, plugin registry, filesystem, or package manager output.

2. Callable now
   - Can be invoked directly in the current environment, usually via `command -v`, `--help`, `version`, or another harmless read-only command.

3. Always-on in this host
   - Actually injected or active for the current agent host, not merely installed for some other tool.

## Why this matters

Agent ecosystems mix several integration layers:
- standalone CLI binaries
- host plugins
- rule files / instruction packs
- repo-local vs global activation

A truthful answer must say which layer succeeded.

## Recommended reply shape

For each tool:
- name
- installed: yes/no
- callable now: yes/no
- always-on in this host: yes/no
- one-sentence explanation

Example:
- RTK: installed yes; callable now yes; always-on in Hermes no. It is a direct CLI I can invoke, but Hermes does not automatically route every shell command through it unless I choose to.
- Ponytail: installed for OpenCode yes; callable now indirectly via OpenCode host integration; always-on in Hermes no. The plugin affects OpenCode, not Hermes itself.
- Caveman: installer not completed, so do not claim use.

## Session-specific cue

If the user says something like "all I want to know is whether you already use it and always use it," stop optimizing for process detail and answer the status question first, then add one short explanation per item.
