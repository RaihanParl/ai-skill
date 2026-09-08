---
name: memanto-local-setup
description: Use when installing or repairing Memanto locally on macOS and wiring it into Cursor or OpenCode with an on-prem backend via OrbStack and Ollama.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memanto, cursor, opencode, orbstack, ollama, macos]
    related_skills: [opencode, hermes-agent]
---

# Memanto Local Setup on macOS

## Overview

This skill captures the working path from a successful OpenCode session that installed Memanto locally, connected it to Cursor and OpenCode, and configured the on-prem backend on a macOS machine that prefers OrbStack over Docker Desktop.

The key facts from that session:
- Memanto required Python 3.11 on this machine. The system `python3` was 3.9.6, but `python3.11` was available.
- `pipx` was not installed, so the CLI was installed with `python3.11 -m pip install --user memanto`.
- The CLI landed in `~/Library/Python/3.11/bin/memanto`, then was symlinked to `~/bin/memanto` for easier shell access.
- Global integrations were added for Cursor and OpenCode.
- The on-prem setup initially failed because the Docker context/runtime was wrong, then because the OrbStack Docker disk was full.
- The durable fix path was: switch Docker context to OrbStack, free unused Docker images/cache, rerun the backend setup, then verify with `memanto status` and `memanto connect list`.

## When to Use

Use this skill when:
- The user wants Memanto installed locally on this Mac
- The user wants Cursor and/or OpenCode connected to Memanto
- The user wants the on-prem backend instead of cloud
- `memanto status` shows the backend or server offline and OrbStack is the intended runtime
- `memanto config backend on-prem` fails during image pull or Docker checks

Do not use this skill when:
- The user wants Docker Desktop specifically
- The user wants a cloud-only Memanto setup
- Python 3.11 is not available and you need a Python install workflow first

## Procedure

1. Check prerequisites and the actual runtime state.

```bash
python3 --version
python3.11 --version
python3.11 -m pip --version
~/bin/memanto --version
ollama --version
docker context ls
```

Completion criteria:
- `python3.11` exists
- `ollama` exists if using local embeddings/answers
- you know which Docker context is active before touching backend setup

2. Install Memanto with Python 3.11 if needed.

```bash
python3.11 -m pip install --user memanto
python3.11 -m site --user-base
```

Expected binary path on this machine:
```bash
~/Library/Python/3.11/bin/memanto
```

If `memanto` is not on PATH, expose it via `~/bin`:

```bash
mkdir -p ~/bin
ln -sf ~/Library/Python/3.11/bin/memanto ~/bin/memanto
~/bin/memanto --help
```

Completion criteria:
- `~/bin/memanto --help` works

3. Inspect Memanto’s supported integrations before guessing flags.

```bash
~/bin/memanto connect --help
~/bin/memanto connect list
~/bin/memanto connect cursor --help
~/bin/memanto connect opencode --help
```

Completion criteria:
- you have confirmed the integration names and available flags from the live CLI

4. Connect Cursor and OpenCode globally.

```bash
~/bin/memanto connect cursor --global
~/bin/memanto connect opencode --global
~/bin/memanto connect list
```

Observed files from the successful session included:
- `~/.cursor/skills/memanto/SKILL.md`
- `~/.config/opencode/AGENTS.md`
- `~/.config/opencode/skills/memanto/SKILL.md`

Completion criteria:
- `memanto connect list` shows global installs for `cursor` and `opencode`
- the expected instruction/skill files exist

5. Configure the on-prem backend with OrbStack, not Docker Desktop.

First prove the intended Docker runtime is reachable:

```bash
docker context ls
docker context use orbstack
docker info
```

If the user wants OrbStack and `docker info` fails, stop and fix the runtime instead of switching to Docker Desktop behind their back.

Then run backend setup:

```bash
printf '1\n' | ~/bin/memanto config backend on-prem
```

If the CLI asks for multiple numbered selections in your environment, re-run with the exact number of answers needed rather than guessing broadly.

Completion criteria:
- backend setup completes without Docker/socket/image-pull failure

6. If backend setup fails, diagnose by actual failure mode.

Common checks from the session:

```bash
docker info
docker system df
df -h ~/.orbstack
docker ps -a
moorcheh status
```

Observed failure classes:
- wrong or dead Docker socket/context
- OrbStack daemon not running
- Docker disk full while pulling Moorcheh image (`no space left on device`)

If disk is the blocker and the user approves pruning, use:

```bash
docker system prune -af
```

Then retry:

```bash
printf '1\n' | ~/bin/memanto config backend on-prem
```

Completion criteria:
- the previous failing cause is explicitly gone, not just retried blindly

7. Verify both installation and runtime.

```bash
~/bin/memanto status
~/bin/memanto connect list
moorcheh status
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
```

Interpretation:
- `memanto connect list` verifies agent integrations
- `memanto status` verifies active backend selection
- `moorcheh status` verifies the on-prem server health endpoint
- `docker ps` shows whether the Moorcheh container is actually running

8. If Memanto itself is installed but idle/offline after setup, start the missing layers explicitly.

Memanto local REST API:

```bash
memanto serve
```

Moorcheh on-prem runtime:

```bash
moorcheh up
```

Shut down Moorcheh when needed:

```bash
moorcheh down
```

Completion criteria:
- `memanto status` no longer reports the on-prem server offline when the backend is expected to be live

## Common Pitfalls

1. Using `python3` on this Mac by default.
   - In the recorded session, `python3` was 3.9.6. Memanto needed `python3.11`.

2. Assuming `pipx` exists.
   - It did not. The working install path used `python3.11 -m pip install --user memanto`.

3. Assuming the CLI is on PATH after install.
   - It was not. The working fix was a symlink from `~/Library/Python/3.11/bin/memanto` to `~/bin/memanto`.

4. Switching runtimes against the user’s stated preference.
   - The user explicitly preferred OrbStack over Docker Desktop. Respect that and debug OrbStack first.

5. Treating integration success as backend success.
   - `memanto connect list` can be correct while `memanto status` still shows the on-prem server offline.

6. Ignoring Docker disk pressure.
   - The successful session only finished after freeing unused Docker images/cache.

7. Believing the final success message without re-checking current runtime.
   - Re-run `memanto status`, `moorcheh status`, and `docker ps` after the session. Runtime state can drift later.

## Verification Checklist

- [ ] `python3.11` exists and is the interpreter used for install
- [ ] `~/bin/memanto --help` works
- [ ] `memanto connect list` shows the expected global integrations
- [ ] `docker context ls` confirms OrbStack when OrbStack is intended
- [ ] `docker info` succeeds before backend setup
- [ ] `memanto status` shows the intended backend
- [ ] `moorcheh status` succeeds when the on-prem backend is expected to be running
- [ ] `docker ps` shows the Moorcheh container when the on-prem backend is live
- [ ] Any disk-space or dead-socket issue is proven fixed before declaring success
