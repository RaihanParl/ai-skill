# Argus review automation notes

## Weekly Codex usage probe

OpenCode's `opencode stats --days 7` reports local token/cost totals, not subscription quota percentage. With an authenticated OpenAI OAuth credential already stored by OpenCode, query:

```text
GET https://chatgpt.com/backend-api/wham/usage
Authorization: Bearer <openai.access token>
```

Use `rate_limit.primary_window.used_percent` only if `limit_window_seconds >= 518400` and preferably equals `604800`. Current response shape includes `allowed`, `limit_reached`, `used_percent`, `reset_after_seconds`, and `reset_at`. Keep token, email, and user ID out of logs.

Model rule: `used_percent > 30` selects `openai/gpt-5.6-sol`; otherwise select `openai/gpt-5.6-luna`. Treat malformed/auth/network responses as Luna fallback.

## Argus preflight

Argus review helpers are receipt-managed. Before PR inspection, `review-preflight.sh` requires exactly one receipt and validates helper hashes. Diagnose with:

```bash
python3 scripts/install-receipt.py doctor \
  --target . --receipt .agents/local/harness.install-receipt.json --format json
```

`hash_mismatch` on `.agents/scripts/*` is a safety blocker, not a GitHub or OpenCode model failure. Do not bypass it. Use the repository's prescribed `manage-installation.py repair --target .` flow, then rerun preflight.

## Telegram completion alerts

Send a lightweight preflight connectivity test before costly review execution:

```bash
hermes send --to telegram:<chat_id> --quiet "Argus watcher test"
```

Have the review child send one alert after process exit. Classify output separately: successful process exit can still contain `Review blocked` or `configuration blocker`; report that as blocked, not completed. Do not poll Telegram Bot API when Hermes gateway already owns the bot.