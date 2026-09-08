# Repo resolution pitfalls

## Drift case from 2026-06-25

User asked for CI/MR work on `https://repo.transjakarta.co.id/gate/tj_tap_sync_sender`.
The workflow drifted for a while into sibling repo/worktree `gate_c` and `sqlite-tap-sync-sender` because the names looked close.

### Fix

1. Resolve exact GitLab repo URL from user message.
2. Inspect local clone remotes before editing:
   - `git remote -v`
   - `git branch --show-current`
3. If clone is missing, clone exact repo URL first.
4. Use worktree only after remote matches target repo.
5. If repo or worktree path does not match user URL, stop and switch.

### Example checks

- Target repo path: `gate/tj_tap_sync_sender`
- Wrong sibling that caused drift: `gate/gate_c/.loop-worktrees/sqlite-tap-sync-sender`
- Correct clone found later: `/Users/mraihanparlaungan/worktrees/tj_tap_sync_sender`

### Lesson

Close names are not enough. Git remote identity is source of truth.
