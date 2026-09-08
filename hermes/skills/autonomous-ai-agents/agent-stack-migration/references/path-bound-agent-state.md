# Path-Bound Agent State

Observed durable pattern:

- Hermes session records contain `cwd`.
- OpenCode tracks project worktree, project directories, workspace directory, and session directory/path.
- Codex tracks thread `cwd` and rollout paths.
- Cursor project state can key off filesystem paths.

Implication: restoring agent databases while changing `/Users/<name>` or project roots can leave history present but disconnected from normal workspace views. Same username plus same directory layout is safest.

Fallback migration:

1. Make immutable backup.
2. Stop all agent processes.
3. Restore projects at new paths.
4. Update path-bearing fields with tool-specific scripts, not blind global replacement.
5. Run SQLite integrity checks.
6. Launch each agent in known workspace and test session resume.
7. Retain original session IDs and old-path mapping for troubleshooting.
