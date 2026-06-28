# Bootstrap AI stack

This folder contains rerunnable workflows for a new machine and for cloning this machine as closely as possible.

Main script:
- `bootstrap/bootstrap_ai_stack.sh`

Exact-machine export / restore:
- `bootstrap/export_hermes_stack.sh`
- `bootstrap/restore_hermes_stack.sh`

What the bootstrap installs:
- core packages needed by this setup (`git`, `tmux`, `python`, `node`)
- Hermes Agent
- OpenCode
- GitNexus
- `gitnexus setup`
- repo-managed OpenCode and Hermes helper files into home directory
- Telegram and provider secrets into `~/.hermes/.env`
- Hermes gateway service
- recurring cron jobs used by this setup

What the export bundle captures:
- `~/.hermes/config.yaml`
- `~/.hermes/memories/`
- `~/.hermes/profiles/`
- `~/.hermes/skills/`
- `~/.hermes/plugins/`
- `~/.hermes/scripts/`
- `~/.config/opencode/`
- optional: `~/.hermes/sessions/` and `~/.hermes/state.db`
- optional: `~/.hermes/.env` and `~/.hermes/auth.json`

Expected usage on a new machine:

```bash
git clone git@github.com:RaihanParl/ai-skill.git ~/ai-skill
cd ~/ai-skill
bash bootstrap/bootstrap_ai_stack.sh
```

Clone this machine into a bundle:

```bash
bash bootstrap/export_hermes_stack.sh ~/Desktop/hermes-stack.tar.gz
```

Restore bundle on new machine:

```bash
bash bootstrap/restore_hermes_stack.sh ~/Desktop/hermes-stack.tar.gz
```

Non-interactive bootstrap example:

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
DRY_RUN=1 bash bootstrap/export_hermes_stack.sh /tmp/hermes-stack.tar.gz
DRY_RUN=1 bash bootstrap/restore_hermes_stack.sh /tmp/hermes-stack.tar.gz
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
- `INCLUDE_SECRETS=1` include `.env` and `auth.json` in export bundle
- `INCLUDE_SESSIONS=1` include `sessions/` and `state.db` in export bundle
- `INCLUDE_OPENCODE_CACHE=0` skip `opencode.json` if you only want source config
- `FORCE=1` allow restore to overwrite existing destination files

Notes:
- The script is optimized for macOS because that is the current primary environment.
- Linux is best-effort for `apt-get` and `dnf` systems.
- It does not log you into OpenCode providers automatically. After bootstrap, run `opencode providers login`.
- If you do not pass provider API keys, run `hermes model` after installation.
- Export bundles can contain secrets if you ask for them. Treat them like private backups.
