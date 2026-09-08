---
name: agent-plugin-integration
description: Install, verify, and accurately report third-party agent plugins, skills, rulesets, and companion CLIs across hosts like OpenCode, Hermes, Codex, Claude Code, and similar tools.
version: 1.0.0
author: Hermes Agent
license: MIT
created_by: agent
---

# Agent Plugin Integration

## When to use

Use this skill when the user asks to install or use third-party agent tooling such as:
- host plugins for OpenCode, Codex, Claude Code, Copilot CLI, Gemini, or similar
- agent rulesets / always-on instruction packs
- companion CLIs that can be invoked directly from the shell
- mixed stacks where one project includes both a standalone CLI and one or more host-specific plugins

Typical examples:
- "install and use X with OpenCode"
- "set this up in Hermes / Codex / Claude Code"
- "are you already using this, or just saying you are?"

## Core lesson

Do not blur together these three states:
1. installed on disk
2. callable directly as a CLI right now
3. always-on inside the current host agent

Users often care about the difference more than the install itself. Report them separately.

## Workflow

1. Identify the tool shape first.
   - Determine whether each requested item is:
     - a standalone CLI
     - a host plugin / extension
     - a ruleset / instruction pack
     - a mixed package that offers more than one of the above
   - Do not assume a GitHub repo implies a binary, or that an npm package implies a universal CLI.

2. Inspect official install instructions before acting.
   - Prefer the upstream README / install guide.
   - Note host-specific commands exactly.
   - If the package supports several hosts, pick the host the user actually has installed.

3. Verify local host availability.
   - Check which host CLIs are present before choosing an install path.
   - Example distinction:
     - OpenCode plugin install only matters if `opencode` exists.
     - A companion CLI can be verified with `command -v` and `--help`.

4. Install with the host-native mechanism.
   - Use the tool's documented install path for that host rather than inventing a manual copy process.
   - Examples: `opencode plugin ...`, `codex plugin ...`, marketplace install, extension install, or repo-provided installer.

5. Verify with real output.
   - For standalone CLIs: run a real command like `--help`, `version`, or a harmless read-only subcommand.
   - For host plugins: confirm the host config changed, the plugin is listed, or the installer reports success.
   - Do not claim success from a guessed side effect.

6. Report status in three buckets.
   - `installed`
   - `usable now`
   - `always-on in this host`
   This avoids misleading users when a plugin is installed for OpenCode but not active in Hermes itself.

7. If Hermes-local config, skills, or global agent docs were changed for the integration, follow the user's publishing workflow for assistant config repos.

## Reporting format

When the user asks whether you already use something, answer directly in this shape:
- `X: installed / not installed`
- `X: callable now / not callable now`
- `X: always-on in this host / not always-on in this host`
- one short sentence explaining the gap, if any

Avoid hiding the answer inside a long narrative.

## Pitfalls

- Do not say "I use it" when only the package exists upstream or was installed into a different host.
- Do not treat a plugin install as equivalent to Hermes adopting that behavior automatically.
- Do not conflate repo documentation with verified local state.
- Do not stop after installation; verify a real command or config change.
- If an installer is blocked by approvals, report the partial state explicitly instead of implying completion.
- If a bridge package shells out to another CLI, verify the exact flags against the locally installed binary. README examples can drift from the installed version.
- When a plugin fails with `unknown option`, inspect the emitted argv and the companion CLI `--help` output before changing anything else. Fix the version mismatch at the integration layer, not by assuming the bridge is broken.

## Host-specific note from this session

OpenCode plugin installs can be verified by both:
- installer success output, and
- a concrete config update under `~/.config/opencode/opencode.jsonc`

Cursor/OpenCode bridge installs may also need a compatibility check for the installed `cursor-agent` binary. The important test is whether a harmless `opencode run` can actually stream through the bridge, not just whether the package is present.

## References

- `references/adoption-status-reporting.md` — concise checklist for distinguishing installed vs callable vs always-on and how to report that back to the user.
- `references/cursor-acp-compat.md` — bridge-specific verification notes for Cursor ACP / OpenCode integration and flag compatibility checks.
