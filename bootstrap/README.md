# Bootstrap AI stack

This folder contains a rerunnable shell bootstrap for a new machine.

Main script:
- `bootstrap/bootstrap_ai_stack.sh`

What it does:
- installs core packages needed by this setup (`git`, `tmux`, `python`, `node`)
- installs Hermes Agent
- installs OpenCode
- installs GitNexus
- runs `gitnexus setup`
- copies repo-managed OpenCode and Hermes helper files into your home directory
- writes Telegram and provider secrets into `~/.hermes/.env`
- installs and starts the Hermes gateway service
- recreates the recurring cron jobs used by this setup

Expected usage on a new machine:

```bash
git clone git@github.com:RaihanParl/ai-skill.git ~/ai-skill
cd ~/ai-skill
bash bootstrap/bootstrap_ai_stack.sh
```

Non-interactive example:

```bash
TELEGRAM_BOT_TOKEN='123:abc' \
TELEGRAM_ALLOWED_USERS='1724955702' \
TELEGRAM_HOME_CHANNEL='1724955702' \
OPENROUTER_API_KEY='or-...' \
bash bootstrap/bootstrap_ai_stack.sh
```

Dry-run validation:

```bash
DRY_RUN=1 NONINTERACTIVE=1 bash bootstrap/bootstrap_ai_stack.sh
```

Useful toggles:
- `INSTALL_HERMES=0` skip Hermes install
- `INSTALL_OPENCODE=0` skip OpenCode install
- `INSTALL_GITNEXUS=0` skip GitNexus install
- `RUN_GITNEXUS_SETUP=0` skip `gitnexus setup`
- `SETUP_TELEGRAM=0` skip Telegram prompts and `.env` updates
- `INSTALL_GATEWAY_SERVICE=0` do not install/start Hermes gateway service
- `SETUP_CRON_JOBS=0` do not create cron jobs
- `AUTO_RUN_HERMES_MODEL=1` launch `hermes model` during bootstrap
- `AUTO_RUN_HERMES_GATEWAY_SETUP=1` launch `hermes gateway setup` during bootstrap

Files synced into the new machine:
- `~/.config/opencode/opencode.jsonc`
- `~/.hermes/scripts/opencode_telegram_bridge.py`
- `~/.hermes/scripts/opencode_telegram_bridge_tick.sh`
- `~/.hermes/scripts/opencode_bridge_launch.sh`
- `~/.hermes/scripts/opencode_monitor.py`
- `~/.hermes/scripts/sync_memory_to_ai_skill.py`

Cron jobs it recreates:
- `opencode-telegram-bridge`
- `opencode-telegram-monitor`
- `sync-hermes-memory-to-ai-skill`

Notes:
- The script is optimized for macOS because that is the current primary environment.
- Linux is best-effort for `apt-get` and `dnf` systems.
- It does not log you into OpenCode providers automatically. After bootstrap, run `opencode providers login`.
- If you do not pass provider API keys, run `hermes model` after installation.
