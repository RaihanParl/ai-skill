# Hermes memory sync to publishing repo

Use this when the user expects Hermes "learning" to show up in the GitHub repo of assistant configs.

Problem pattern:
- The publishing repo is clean.
- Hermes clearly learned durable preferences.
- The missing piece is that built-in Hermes memory is local state, not automatically mirrored into the repo.

Observed durable local source paths:
- `~/.hermes/memories/USER.md`
- `~/.hermes/memories/MEMORY.md`

Recommended repo layout:
- `memory/README.md`
- `memory/hermes/USER.md`
- `memory/hermes/MEMORY.md`
- `memory/hermes/manifest.json`
- `hermes/scripts/sync_memory_to_ai_skill.py`

Useful automation pattern:
- Keep the real sync logic in the repo script.
- If Hermes cron needs a script under `~/.hermes/scripts/`, add a tiny wrapper there that `runpy.run_path(...)` executes the repo script.
- Make the sync script stage the mirrored files, commit only when `git diff --cached --quiet` shows a real change, and push to `origin` on the current branch.
- For quiet recurring sync, schedule the wrapper as a `no_agent=True` cron job and rely on empty stdout when nothing changed.

Verification checklist:
- Local memory files exist before mirroring.
- Repo `git status --short` shows only intended files.
- Local `HEAD` equals `origin/<current-branch>` after push.
- The recurring cron job can be triggered once manually and finishes with `last_status: ok`.
