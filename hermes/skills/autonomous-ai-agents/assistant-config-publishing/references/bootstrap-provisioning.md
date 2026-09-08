# Bootstrap provisioning pattern for assistant config repos

Use this reference when the user wants a single command or shell script to recreate their assistant environment on a new machine.

## Durable pattern

Repo layout:
- `bootstrap/bootstrap_ai_stack.sh`
- `bootstrap/README.md`
- existing mirrored config under paths such as `hermes/scripts/`, `opencode/`, `cursor/rules/`, `memory/`

The bootstrap script should:
1. Detect the repo root from the script location.
2. Install base dependencies for the target OS where practical.
3. Install Hermes, OpenCode, and GitNexus if they are part of the user's standard toolchain.
4. Run `gitnexus setup` when the user wants GitNexus as the default workflow helper.
5. Copy repo-managed files into live locations such as:
   - `~/.config/opencode/opencode.jsonc`
   - `~/.hermes/scripts/...`
6. Update `~/.hermes/.env` idempotently rather than appending duplicate keys.
7. Install or recreate Hermes cron jobs only if they do not already exist.
8. Print a final checklist with follow-up commands like `hermes doctor`, `hermes gateway status`, `hermes cron list`, `opencode providers login`, and `hermes model`.

## Validation pattern

Always validate the bootstrap script before publishing:

```bash
bash -n bootstrap/bootstrap_ai_stack.sh
DRY_RUN=1 NONINTERACTIVE=1 bash bootstrap/bootstrap_ai_stack.sh
```

Use environment variables in the dry-run to cover the Telegram path without prompting, for example:

```bash
DRY_RUN=1 NONINTERACTIVE=1 \
TELEGRAM_BOT_TOKEN='***' \
TELEGRAM_ALLOWED_USERS='1724955702' \
TELEGRAM_HOME_CHANNEL='1724955702' \
OPENROUTER_API_KEY='***' \
bash bootstrap/bootstrap_ai_stack.sh
```

## Why this matters

Without a checked-in bootstrap workflow, assistant configuration repos drift into documentation-only snapshots. The repo should be able to recreate the live environment, not just describe it.
