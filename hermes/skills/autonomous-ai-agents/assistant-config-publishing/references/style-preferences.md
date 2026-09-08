# Style preferences sync

Session-derived rule for assistant config publishing.

## Durable preference

The user prefers Caveman / RTK / Ponytail style by default, and treats it as a hard reply rule when explicitly requested:

- direct
- compact
- practical
- blunt when useful
- low on explanatory fluff unless asked
- short enough to read fast
- no chatty padding unless asked for detail

When this preference is corrected mid-session, update the live instruction surface first, then mirror the same wording into any repo-backed assistant config so the next session starts with the fix already loaded.

## Where to encode it

When updating assistant config for this preference, mirror it in the live instruction surface that the agent actually loads first, then publish the same change into the repo-backed config:

- `opencode/AGENTS.md` or similar always-on agent instructions
- Hermes/Cursor rule files when they are the active source of truth
- the config repo committed to GitHub

## Review heuristic

If a reply feels like it is over-explaining a straightforward answer, treat that as a style regression and tighten the default voice in the relevant live instructions.
