# Bootstrap telegram ping cron

Pattern:
- Keep the heartbeat as a tiny standalone script in `~/.hermes/scripts/`.
- Gate creation behind an env flag, e.g. `ENABLE_TELEGRAM_PING_CRON=1`.
- Keep the schedule configurable, e.g. `TELEGRAM_PING_CRON_SCHEDULE='every 6h'`.
- Create the job with Hermes cron and deliver to `telegram:<home-channel>`.

Example shape:
- script: `telegram_ping.sh`
- cron name: `telegram-ping`
- deliver: `telegram:$TELEGRAM_HOME_CHANNEL`
- mode: `--no-agent`

Verification:
- `bash -n` on the bootstrap script and the ping script.
- `hermes cron list` shows the job.
- Run the ping script once and confirm it prints one short line.
