# Cursor ACP / OpenCode bridge notes

Use this when setting up or verifying OpenCode with a Cursor-backed bridge package.

## What to verify
- The bridge package is installed in the same OpenCode profile that will use it.
- The OpenCode config points at the bridge provider and model names that the bridge exposes.
- The local `cursor-agent` binary is authenticated and matches the flags the bridge emits.
- A real `opencode run` path succeeds, not just `opencode models` listing the provider.

## Fast verification path
1. Check host availability.
   - `opencode --version`
   - `cursor-agent --version`
   - `cursor-agent status`
2. Check the bridge config.
   - Look for the provider entry in `~/.config/opencode/opencode.jsonc` or `opencode.json`.
3. Check model discovery.
   - `opencode models | grep cursor-acp`
4. Check runtime behavior.
   - Run a harmless prompt through the bridged model.

## Compatibility pitfall
A README or bridge package may emit argv flags that do not exist in the installed `cursor-agent` version.
If a run fails with `unknown option`, compare:
- the emitted argv in the bridge source or logs
- `cursor-agent --help`

Fix the mismatch at the bridge/CLI compatibility layer first.

## Reporting
When asked if the setup is usable, split the answer into:
- installed
- callable now
- always-on in this host

That avoids saying "yes" when only the package exists but the runtime still fails.
