# AI-Skill Publishing Reference

Session-derived details for the `assistant-config-publishing` umbrella.

## User preference captured

When local AI assistant configuration changes are made, the user wants them pushed to:

- `git@github.com:RaihanParl/ai-skill.git`

This applies to:
- skills
- rules
- `Agent.md` / `AGENTS.md`-style instruction files
- similar assistant helper scripts or config docs

## Local repo used in this session

- Clone path: `~/ai-skill`
- Remote:
  - `origin git@github.com:RaihanParl/ai-skill.git`

## Mirror structure used

```text
ai-skill/
  README.md
  cursor/rules/
  hermes/scripts/
```

Files synced in this session:
- `cursor/rules/evidence-first-debugging.mdc`
- `cursor/rules/gitlab-mr-review-priority.mdc`
- `cursor/rules/gitlab-mr-review.mdc`
- `cursor/rules/playwright-validation.mdc`
- `hermes/scripts/opencode_monitor.py`
- `hermes/scripts/opencode_telegram_bridge.py`
- `hermes/scripts/opencode_telegram_bridge_tick.sh`
- `hermes/scripts/opencode_bridge_launch.sh`
- `README.md`

## Verified push from this session

- Commit: `71e06bea1d8ce7d3f217702a74a5dc640aa4ce08`
- Message: `Add Hermes bridge scripts and assistant rules`

## Related second repo push pattern

The user explicitly asked to also push the OpenCode-adjacent repo when relevant.
In this session that meant:

- Repo: `~/proj/opencode-research`
- Remote: `git@repo.transjakarta.co.id:raihan/opencode-agent.git`
- Validation: `npm --prefix ~/proj/opencode-research/agents/tije-smpob-pilot run build`
- Commit: `c6708a9234893e3fd2ee826032b6a77374f26d0a`
- Message: `Improve OpenCode runner logging and stdin control`

Use that second push pattern only when the user explicitly broadens scope beyond the assistant-config repo.
