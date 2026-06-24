#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AI_SKILL_DIR="${AI_SKILL_DIR:-$REPO_ROOT}"
DRY_RUN="${DRY_RUN:-0}"
NONINTERACTIVE="${NONINTERACTIVE:-0}"
INSTALL_HERMES="${INSTALL_HERMES:-1}"
INSTALL_OPENCODE="${INSTALL_OPENCODE:-1}"
INSTALL_GITNEXUS="${INSTALL_GITNEXUS:-1}"
RUN_GITNEXUS_SETUP="${RUN_GITNEXUS_SETUP:-1}"
SETUP_TELEGRAM="${SETUP_TELEGRAM:-1}"
INSTALL_GATEWAY_SERVICE="${INSTALL_GATEWAY_SERVICE:-1}"
SYNC_REPO_FILES="${SYNC_REPO_FILES:-1}"
SETUP_CRON_JOBS="${SETUP_CRON_JOBS:-1}"
ENABLE_MEMORY_SYNC_CRON="${ENABLE_MEMORY_SYNC_CRON:-1}"
ENABLE_OPENCODE_MONITOR_CRON="${ENABLE_OPENCODE_MONITOR_CRON:-1}"
ENABLE_HERMES_SESSION_MONITOR_CRON="${ENABLE_HERMES_SESSION_MONITOR_CRON:-1}"
ENABLE_OPENCODE_BRIDGE_CRON="${ENABLE_OPENCODE_BRIDGE_CRON:-1}"
ENABLE_TELEGRAM_PING_CRON="${ENABLE_TELEGRAM_PING_CRON:-1}"
TELEGRAM_PING_CRON_SCHEDULE="${TELEGRAM_PING_CRON_SCHEDULE:-every 6h}"
AUTO_RUN_HERMES_MODEL="${AUTO_RUN_HERMES_MODEL:-0}"
AUTO_RUN_HERMES_GATEWAY_SETUP="${AUTO_RUN_HERMES_GATEWAY_SETUP:-0}"

TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"
TELEGRAM_HOME_CHANNEL="${TELEGRAM_HOME_CHANNEL:-}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_ENV_PATH="$HERMES_HOME/.env"
HERMES_SCRIPTS_DIR="$HERMES_HOME/scripts"
OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
OPENCODE_CONFIG_PATH="$OPENCODE_CONFIG_DIR/opencode.jsonc"
SHELL_NAME="$(basename "${SHELL:-sh}")"
case "$SHELL_NAME" in
  zsh) SHELL_RC="$HOME/.zshrc" ;;
  bash) SHELL_RC="$HOME/.bashrc" ;;
  *) SHELL_RC="$HOME/.profile" ;;
esac

log() {
  printf '[bootstrap] %s\n' "$*"
}

warn() {
  printf '[bootstrap][warn] %s\n' "$*" >&2
}

fail() {
  printf '[bootstrap][error] %s\n' "$*" >&2
  exit 1
}

run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  log "run: $*"
  "$@"
}

run_shell() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  log "run: $*"
  bash -lc "$*"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

ensure_line_in_file() {
  local file="$1"
  local line="$2"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if grep -Fqx "$line" "$file" 2>/dev/null; then
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    printf '[dry-run] append to %s: %s\n' "$file" "$line"
    return 0
  fi
  printf '\n%s\n' "$line" >> "$file"
}

prompt_if_missing() {
  local var_name="$1"
  local prompt_text="$2"
  local secret="${3:-0}"
  local current_value="${!var_name:-}"
  if [ -n "$current_value" ]; then
    return 0
  fi
  if [ "$NONINTERACTIVE" = "1" ]; then
    return 0
  fi
  if [ ! -t 0 ]; then
    return 0
  fi
  if [ "$secret" = "1" ]; then
    read -r -s -p "$prompt_text: " current_value
    printf '\n'
  else
    read -r -p "$prompt_text: " current_value
  fi
  printf -v "$var_name" '%s' "$current_value"
}

set_env_key() {
  local file="$1"
  local key="$2"
  local value="$3"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if grep -qE "^${key}=" "$file"; then
    if [ "$DRY_RUN" = "1" ]; then
      printf '[dry-run] update %s in %s\n' "$key" "$file"
    else
      python3 - "$file" "$key" "$value" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text().splitlines()
out = []
replaced = False
for line in lines:
    if line.startswith(f"{key}="):
        out.append(f"{key}={value}")
        replaced = True
    else:
        out.append(line)
if not replaced:
    out.append(f"{key}={value}")
path.write_text("\n".join(out) + "\n")
PY
    fi
  else
    if [ "$DRY_RUN" = "1" ]; then
      printf '[dry-run] add %s to %s\n' "$key" "$file"
    else
      printf '%s=%s\n' "$key" "$value" >> "$file"
    fi
  fi
}

first_csv_item() {
  local input="$1"
  input="${input%%,*}"
  printf '%s' "${input// /}"
}

ensure_macos_brew() {
  if have_cmd brew; then
    return 0
  fi
  if [ "$(uname -s)" != "Darwin" ]; then
    return 0
  fi
  log 'Homebrew not found. Installing Homebrew.'
  run_shell '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_system_packages() {
  local os
  os="$(uname -s)"
  case "$os" in
    Darwin)
      ensure_macos_brew
      if have_cmd brew; then
        run brew update
        run brew install git tmux python node
      else
        fail 'Homebrew is required on macOS but is still unavailable.'
      fi
      ;;
    Linux)
      if have_cmd apt-get; then
        run sudo apt-get update
        run sudo apt-get install -y git curl tmux python3 python3-venv python3-pip nodejs npm
      elif have_cmd dnf; then
        run sudo dnf install -y git curl tmux python3 python3-pip nodejs npm
      else
        warn 'No supported package manager detected. Skipping system package installation.'
      fi
      ;;
    *)
      warn "Unsupported OS for automatic package bootstrap: $os"
      ;;
  esac
}

ensure_local_bin_on_path() {
  ensure_line_in_file "$SHELL_RC" 'export PATH="$HOME/.local/bin:$PATH"'
  export PATH="$HOME/.local/bin:$PATH"
}

install_hermes() {
  if [ "$INSTALL_HERMES" != "1" ]; then
    return 0
  fi
  if have_cmd hermes; then
    log 'Hermes already installed. Skipping install.'
    return 0
  fi
  ensure_local_bin_on_path
  run_shell 'curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash'
  export PATH="$HOME/.local/bin:$PATH"
  have_cmd hermes || fail 'Hermes install completed but hermes is still not on PATH.'
}

install_global_npm_package() {
  local package_name="$1"
  local binary_name="$2"
  if have_cmd "$binary_name"; then
    log "$binary_name already installed. Skipping npm install."
    return 0
  fi
  have_cmd npm || fail 'npm is required but was not found.'
  run npm install -g "$package_name"
  have_cmd "$binary_name" || warn "$binary_name was installed but is not yet on PATH in this shell."
}

install_opencode() {
  if [ "$INSTALL_OPENCODE" = "1" ]; then
    install_global_npm_package opencode-ai@latest opencode
  fi
}

install_gitnexus() {
  if [ "$INSTALL_GITNEXUS" = "1" ]; then
    install_global_npm_package gitnexus@latest gitnexus
  fi
  if [ "$RUN_GITNEXUS_SETUP" = "1" ] && have_cmd gitnexus; then
    run gitnexus setup
  fi
}

sync_repo_files() {
  if [ "$SYNC_REPO_FILES" != "1" ]; then
    return 0
  fi
  mkdir -p "$HERMES_SCRIPTS_DIR" "$OPENCODE_CONFIG_DIR"
  run cp "$AI_SKILL_DIR/opencode/opencode.jsonc" "$OPENCODE_CONFIG_PATH"
  run cp "$AI_SKILL_DIR/hermes/scripts/opencode_telegram_bridge.py" "$HERMES_SCRIPTS_DIR/opencode_telegram_bridge.py"
  run cp "$AI_SKILL_DIR/hermes/scripts/opencode_telegram_bridge_tick.sh" "$HERMES_SCRIPTS_DIR/opencode_telegram_bridge_tick.sh"
  run cp "$AI_SKILL_DIR/hermes/scripts/opencode_bridge_launch.sh" "$HERMES_SCRIPTS_DIR/opencode_bridge_launch.sh"
  run cp "$AI_SKILL_DIR/hermes/scripts/opencode_monitor.py" "$HERMES_SCRIPTS_DIR/opencode_monitor.py"
  run cp "$AI_SKILL_DIR/hermes/scripts/hermes_session_monitor.py" "$HERMES_SCRIPTS_DIR/hermes_session_monitor.py"
  run cp "$AI_SKILL_DIR/hermes/scripts/sync_memory_to_ai_skill.py" "$HERMES_SCRIPTS_DIR/sync_memory_to_ai_skill.py"
  run cp "$AI_SKILL_DIR/hermes/scripts/telegram_ping.sh" "$HERMES_SCRIPTS_DIR/telegram_ping.sh"
  run chmod +x "$HERMES_SCRIPTS_DIR/opencode_telegram_bridge.py" "$HERMES_SCRIPTS_DIR/opencode_telegram_bridge_tick.sh" "$HERMES_SCRIPTS_DIR/opencode_bridge_launch.sh" "$HERMES_SCRIPTS_DIR/opencode_monitor.py" "$HERMES_SCRIPTS_DIR/hermes_session_monitor.py" "$HERMES_SCRIPTS_DIR/sync_memory_to_ai_skill.py" "$HERMES_SCRIPTS_DIR/telegram_ping.sh"
}

configure_hermes_env() {
  mkdir -p "$HERMES_HOME"
  touch "$HERMES_ENV_PATH"

  if [ "$SETUP_TELEGRAM" = "1" ]; then
    prompt_if_missing TELEGRAM_BOT_TOKEN 'Telegram bot token' 1
    prompt_if_missing TELEGRAM_ALLOWED_USERS 'Telegram allowed user IDs (comma-separated)' 0
    if [ -z "$TELEGRAM_HOME_CHANNEL" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
      TELEGRAM_HOME_CHANNEL="$(first_csv_item "$TELEGRAM_ALLOWED_USERS")"
    fi
  fi

  prompt_if_missing OPENROUTER_API_KEY 'OpenRouter API key (optional)' 1
  prompt_if_missing ANTHROPIC_API_KEY 'Anthropic API key (optional)' 1
  prompt_if_missing OPENAI_API_KEY 'OpenAI API key (optional)' 1

  if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    set_env_key "$HERMES_ENV_PATH" TELEGRAM_BOT_TOKEN "$TELEGRAM_BOT_TOKEN"
  fi
  if [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
    set_env_key "$HERMES_ENV_PATH" TELEGRAM_ALLOWED_USERS "$TELEGRAM_ALLOWED_USERS"
  fi
  if [ -n "$TELEGRAM_HOME_CHANNEL" ]; then
    set_env_key "$HERMES_ENV_PATH" TELEGRAM_HOME_CHANNEL "$TELEGRAM_HOME_CHANNEL"
  fi
  if [ -n "$OPENROUTER_API_KEY" ]; then
    set_env_key "$HERMES_ENV_PATH" OPENROUTER_API_KEY "$OPENROUTER_API_KEY"
  fi
  if [ -n "$ANTHROPIC_API_KEY" ]; then
    set_env_key "$HERMES_ENV_PATH" ANTHROPIC_API_KEY "$ANTHROPIC_API_KEY"
  fi
  if [ -n "$OPENAI_API_KEY" ]; then
    set_env_key "$HERMES_ENV_PATH" OPENAI_API_KEY "$OPENAI_API_KEY"
  fi
}

maybe_run_hermes_model() {
  if [ "$AUTO_RUN_HERMES_MODEL" = "1" ]; then
    run hermes model
  else
    log 'Skipping hermes model picker. Set AUTO_RUN_HERMES_MODEL=1 to launch it automatically.'
  fi
}

maybe_run_gateway_setup() {
  if [ "$AUTO_RUN_HERMES_GATEWAY_SETUP" = "1" ]; then
    run hermes gateway setup
  fi
}

install_gateway_service() {
  if [ "$INSTALL_GATEWAY_SERVICE" != "1" ]; then
    return 0
  fi
  if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_ALLOWED_USERS" ]; then
    warn 'Telegram values are incomplete. Skipping gateway service install/start.'
    return 0
  fi
  run hermes gateway install
  run hermes gateway start
}

cron_job_exists() {
  local job_name="$1"
  if ! have_cmd hermes; then
    return 1
  fi
  hermes cron list 2>/dev/null | grep -Fq "Name:      $job_name"
}

ensure_cron_job() {
  local name="$1"
  shift
  if cron_job_exists "$name"; then
    log "Cron job already exists: $name"
    return 0
  fi
  run hermes cron create "$@" --name "$name"
}

setup_cron_jobs() {
  if [ "$SETUP_CRON_JOBS" != "1" ]; then
    return 0
  fi
  if [ "$ENABLE_OPENCODE_BRIDGE_CRON" = "1" ]; then
    ensure_cron_job opencode-telegram-bridge 'every 1m' --deliver local --script opencode_telegram_bridge_tick.sh --no-agent
  fi
  if [ "$ENABLE_OPENCODE_MONITOR_CRON" = "1" ] && [ -n "$TELEGRAM_HOME_CHANNEL" ]; then
    ensure_cron_job opencode-telegram-monitor 'every 1m' --deliver "telegram:$TELEGRAM_HOME_CHANNEL" --script opencode_monitor.py --no-agent
  fi
  if [ "$ENABLE_HERMES_SESSION_MONITOR_CRON" = "1" ] && [ -n "$TELEGRAM_HOME_CHANNEL" ]; then
    ensure_cron_job hermes-session-monitor 'every 1m' --deliver "telegram:$TELEGRAM_HOME_CHANNEL" --script hermes_session_monitor.py --no-agent
  fi
  if [ "$ENABLE_TELEGRAM_PING_CRON" = "1" ] && [ -n "$TELEGRAM_HOME_CHANNEL" ]; then
    ensure_cron_job telegram-ping 'every 6h' --deliver "telegram:$TELEGRAM_HOME_CHANNEL" --script telegram_ping.sh --no-agent
  fi
  if [ "$ENABLE_MEMORY_SYNC_CRON" = "1" ]; then
    ensure_cron_job sync-hermes-memory-to-ai-skill 'every 1h' --deliver local --script sync_memory_to_ai_skill.py --no-agent --workdir "$AI_SKILL_DIR"
  fi
}

print_summary() {
  printf '\n'
  log 'Bootstrap complete.'
  log "Repo root: $AI_SKILL_DIR"
  if have_cmd opencode; then
    log "OpenCode version: $(opencode --version 2>/dev/null || true)"
  fi
  if have_cmd gitnexus; then
    log "GitNexus version: $(gitnexus --version 2>/dev/null || true)"
  fi
  if have_cmd hermes; then
    log "Hermes version: $(hermes --version 2>/dev/null | head -n 1 || true)"
  fi
  log "Hermes env: $HERMES_ENV_PATH"
  log "OpenCode config: $OPENCODE_CONFIG_PATH"
  log 'Next useful commands:'
  printf '  - hermes doctor\n'
  printf '  - hermes gateway status\n'
  printf '  - hermes cron list\n'
  printf '  - opencode providers login\n'
  printf '  - hermes model\n'
}

main() {
  log "Using ai-skill repo at: $AI_SKILL_DIR"
  [ -d "$AI_SKILL_DIR" ] || fail "Repo directory does not exist: $AI_SKILL_DIR"
  install_system_packages
  install_hermes
  install_opencode
  install_gitnexus
  sync_repo_files
  configure_hermes_env
  maybe_run_gateway_setup
  install_gateway_service
  maybe_run_hermes_model
  setup_cron_jobs
  print_summary
}

main "$@"
