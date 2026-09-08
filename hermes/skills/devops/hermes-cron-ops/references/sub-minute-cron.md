# Sub-minute Hermes cron notes

Observed operational pattern:

- Some scheduler entry points may reject `every 30s` even when the CLI edit path accepts it.
- For existing jobs, prefer `hermes cron edit <job> --schedule 'every 30s'` over direct file edits.
- `cron.wrap_response: false` removes the `Cronjob Response: ...` header/footer wrapper from delivered cron output.
- After changing cron config, restart the gateway and verify with `hermes cron list`.

Useful verification commands:

```bash
hermes cron list
hermes gateway status
hermes gateway restart
```

Log files to inspect when cron delivery looks stale:

- `~/.hermes/logs/gateway.log`
- `~/.hermes/logs/agent.log`

If a no-agent job goes silent, check whether the script printed anything at all. Empty stdout is a valid silent delivery.
