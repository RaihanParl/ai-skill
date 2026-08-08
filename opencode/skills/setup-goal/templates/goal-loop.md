---
name: goal-loop
description: Use when /goal runs, resumes, plans, builds, reviews, publishes, or finishes a configured multi-repository goal.
---

# Goal Loop

Immutable configuration lives in `.goal/state.json`. It is not a run registry and `/goal` never rewrites it. Never infer ticket system, repository roles, target branch, code host, remote, or models when configured values exist. Ticket system controls issue operations; each repo's verified remote URL and `code_host` control push and PR/MR operations.

## Run files

Create `.goal/runs/<run-id>/` with:

- `state.json`: canonical goal key, verified source requirements, status, phase, repo branches/worktrees, ticket IDs, PR/MR URLs, review rounds/comments, attempts, blocker, next action.
- `plan.md`: scope, assumptions, acceptance criteria, repo-specific tasks, test commands, dependencies, risks, rollback.
- `review.md`: reviewer findings and resolution.
- `artifacts/`: screenshots or other evidence only.

Update state after every external side effect. Write valid JSON via the file editing tool, never shell interpolation. Do not store credentials, tokens, environment dumps, or unredacted secrets.

Statuses: `planning`, `awaiting_approval`, `building`, `reviewing`, `publishing`, `completed`, `blocked`.

## Parallel safety

Derive `goal_key` from verified identity: `github:<owner>/<repo>#<number>`, `gitlab:<project>#<iid>`, `jira:<PROJECT-123>`, or `local:<sha256-of-normalized-goal>`. Atomically create `.goal/claims/<sha256-goal-key>` with session identity and acquisition time before scanning `.goal/runs/*/state.json`, so simultaneous invocations cannot create duplicate runs for one goal. If the claim exists, stop unless its owner is proven stale; never delete it automatically. Resume only one unfinished exact-key match. More than one match is a state-integrity blocker; no match creates a unique run. Release the short-lived claim only after the selected run lock is acquired. Never select by substring, title similarity, recency, or a root-state pointer.

Multiple runs execute concurrently. The orchestrator is the only writer of its run state and the only process allowed to create/remove worktrees, integrate commits, push, or publish for that run. Acquire only an atomic per-run lock at `.goal/locks/<run-id>` containing run ID, process/session identity, and acquisition time. Never use `.goal/lock` or mutate root state. A lock for another run ID is not a blocker. Release this run's lock on completed, blocked, or other orderly exit. After a crash, require explicit stale-lock verification before removal.

Mutable `.goal/runs/`, `.goal/claims/`, `.goal/locks/`, and `.goal/resource-locks/` must be ignored and untracked so worktrees cannot inherit stale run state. Before repository operations, create or resume an orchestrator worktree under `worktree_root/<run-id>/<repo>/orchestrator`; the user's workspace root is only the control location for shared config and run files.

Plan work as a dependency DAG. Every build task must record:

- unique task ID and repository
- immutable base commit SHA
- dependency task IDs
- conservative file/symbol write set
- unique branch `goal/<run-id>/<task-id>`
- unique worktree under configured `worktree_root/<run-id>/<repo>/<task-id>`
- validation commands and runtime slot

Dispatch ready tasks concurrently up to `max_parallel_builders` only when dependencies are complete and their write sets do not overlap within this run. Unknown or broad write sets count as overlapping. Tasks touching the same migration chain, lockfile, generated output, schema, API contract, shared type, or central configuration must run serially unless the planner proves independence. Different runs remain isolated; a later git conflict blocks only the affected run.

Route each task by repository role and actual change:

- frontend UI/client task -> `goal-frontend-builder`
- backend/API/data task -> `goal-backend-builder`
- infrastructure/CI/container/deployment task -> `goal-infra-builder`
- auxiliary, mixed, or unknown task -> `goal-builder`

Do not route by folder name alone. Planner records the chosen builder for every task; orchestrator verifies it against repository evidence.

Use exact configured OpenCode subagent types for every delegation: `goal-planner`, `goal-builder`, `goal-frontend-builder`, `goal-backend-builder`, `goal-infra-builder`, `goal-reviewer`, `goal-qa`, and `goal-visual-reviewer`. Planning must use exact subagent type `goal-planner`. Keep these IDs unchanged. If an exact named agent is unavailable, record a hard blocker and rerun `/setup-goal` instead of guessing an alias.

Create a task branch/worktree only when the task becomes ready. Its immutable base SHA is the repository integration HEAD after all dependencies have been integrated. Each builder commits its own task branch and returns the commit SHA. Builders never share a branch, worktree, state file, service port, writable artifact path, database, or deployment environment. Quote all paths and never interpolate goal text into shell commands. Assign unique ports/temp/artifact directories when tests can run concurrently; serialize tests that require a shared database, singleton service, device, emulator, or external environment.

Before dispatch, verify every task and integration worktree is under `worktree_root/<run-id>/`, is not `workspace_root`, is unique to one owner, and has the recorded branch and base SHA. Any mismatch blocks before editing.

## Runtime isolation

Use `runtime_port_base` and `runtime_port_stride` from root state. Before assigning a slot, atomically acquire `.goal/resource-locks/port-<first>-<last>`; then probe the requested ports. If locked or occupied, try another block and record it. Shared databases, devices, emulators, and deployment environments require equivalent named resource locks. Release resource locks on every exit path. Bind development/test servers to `127.0.0.1`, never all interfaces.

For each slot also assign:

- `TMPDIR` and writable caches under the task artifact directory
- unique `COMPOSE_PROJECT_NAME=goal_<run-id>_<slot>` when Compose is used
- unique test database/schema name when database tests run
- unique log, trace, screenshot, and coverage paths
- recorded process IDs/container names and bounded readiness timeout

Detect each stack's supported port flag/environment variable from repository scripts and documentation; never assume every app uses `PORT`. If a service has an unavoidable fixed port or shared writable dependency, serialize it. The owner of a runtime slot must terminate every process/container it starts and verify ports are released, including failure paths.

For each repository, create one integration branch/worktree from the recorded base SHA. After builders finish, the orchestrator integrates task commits there one at a time in dependency order. Defer repository-wide and full-product checks until the integrated diff has passed review; builders still run their task-level validation. On cherry-pick/rebase conflict, abort the operation, preserve task commits/worktrees, mark the run blocked or replan, and never auto-resolve by discarding either side.

## Flow

Steps 1-9 are shared by both modes. The orchestrator selects mode based on whether "fast" appears in the goal description.

### Shared steps (both modes)

1. Read immutable root config, derive the canonical goal key, scan run states, and resume only its exact unfinished match. Resume idempotently; never recreate recorded tickets, branches, or PRs/MRs.
2. Fetch the full verified ticket/spec requirements, then inspect every configured repo and its instructions. Confirm clean enough operation without reverting unrelated changes.
3. Delegate planning to `goal-planner`. Require source-to-acceptance traceability and ask one consolidated clarification only when needed to avoid incorrect work.
4. Save plan hash and request one explicit approval before ticket creation, code changes, pushes, or publishing. Persist the actual user approval message, `approved_at`, and `approved_plan_hash`. Never write `auto-approved` or infer approval.
5. Preflight required CLIs/auth and repository remotes. Missing publisher auth blocks publishing, not local planning. For every non-local code remote, verify actual push capability before code changes using a non-destructive git write probe from the same repo/worktree family that will later push (for example `git push --dry-run <remote> HEAD:refs/heads/goal-preflight/<run-id>`). `gh auth status`, `glab auth status`, `ssh -T`, and `git ls-remote` are not sufficient by themselves because they can pass while write access still fails.
6. Create only useful tickets. Do not create empty FE/BE children for repos unaffected by the goal.
7. Record latest target commit SHA per repository, then create isolated orchestrator, task, and integration worktrees under this run's worktree root without modifying existing user worktrees. Never force-push or rewrite shared history.
8. Validate worktree ownership/path/branch/base invariants, then dispatch safe ready tasks in parallel to each task's selected specialist builder with exact worktree, branch, base SHA, write set, runtime slot, acceptance criteria, and test commands.
9. Verify returned commits and integrate them serially per repository. Do not run repository-wide test, lint, type, build, or full-product QA yet; review the integrated diff first. Record the focused validation already run by each builder.

### Fast path (keyword "fast" in goal)
Review locally before push. Fix cycles stay local — only push once clean.

10. Delegate the integrated local diff and acceptance criteria to `goal-reviewer`. Do NOT push or open PR/MR yet — review against the local integration branch diff. Post findings without external APIs. Use `diff` against the base SHA, not a remote.
11. Fix actionable reviewer findings on new isolated task branches from current integration HEAD, reintegrate, and run only focused checks for the fixes. Repeat review until clean or `fix_cycle_limit`.
12. After review is clean, run full relevant repository tests, lint, type, and build checks, then delegate the integrated product to `goal-qa` with isolated startup commands, health checks, acceptance scenarios, runtime allocation, integration SHAs, and artifact paths. For changed user-facing UI, delegate QA evidence to `goal-visual-reviewer` after QA. A missing or genuinely inapplicable test layer must be recorded with reason; never silently skip it. If a failure requires source changes, apply the fix, run focused checks, and return to step 10 before rerunning full checks.
13. Only when local review and QA pass clean: push each integration branch to its configured remote and open or update one draft PR/MR against its configured target branch. Derive GitHub/GitLab from `repo_map`, not ticket system. Verify and record remote URL, PR/MR URL, number/IID, base SHA, and head SHA. If earlier write preflight was skipped or has gone stale due to auth/remote changes, rerun it before the real push.
14. Mark draft PR/MR ready immediately — the diff was already reviewed and fixed locally. No remote review needed.
15. When `merge_mode` is `auto_after_checks`, merge without another approval only after verifying remote required checks, required external approvals, branch protections, mergeability, and reviewed head SHA still match. Never bypass protections. In `review_only`, leave the clean PR/MR ready for humans.
16. Verify merge commit and target branch contains the reviewed head before closing/transitioning tickets. Clean up only worktrees, runtime resources, remote task branches allowed by policy, and lock created by this run. Mark complete only when requested merge/ticket transitions are verified.

### Remote review mode (default, no "fast" keyword)
Push first, review on the PR/MR, then run full checks. Standard push/review/fix/test loop.

10. Push each integration branch to its configured remote and open or update one draft PR/MR against its configured target branch. Derive GitHub/GitLab from `repo_map`, not ticket system. Verify and record remote URL, PR/MR URL, number/IID, base SHA, and head SHA. If earlier write preflight was skipped or has gone stale due to auth/remote changes, rerun it before the real push.
11. Delegate the exact remote PR/MR diff and acceptance criteria to `goal-reviewer`. Post each actionable finding as an inline PR/MR comment only when its path and changed-line position are valid; otherwise post it in one review summary. Never invent a line position. Record comment/discussion URLs.
12. Fix actionable reviewer findings on new isolated task branches from current integration HEAD, reintegrate, run only focused checks for the fixes, push updated commits, and repeat review. Continue until review is clean. Stop without merge on hard blocker, repeated no-progress result, or `fix_cycle_limit`; record exact unresolved findings.
13. After review is clean, run full relevant repository tests, lint, type, and build checks, then delegate the integrated product to `goal-qa` with isolated startup commands, health checks, acceptance scenarios, runtime allocation, integration SHAs, and artifact paths. For changed user-facing UI, delegate QA evidence to `goal-visual-reviewer` after QA. A missing or genuinely inapplicable test layer must be recorded with reason; never silently skip it. If a failure requires source changes, apply the fix, run focused checks, push it, and return to step 11 before rerunning full checks.
14. Mark draft PR/MR ready only after latest head SHA has passing checks, QA, visual review when applicable, and zero unresolved actionable review findings.
15. When `merge_mode` is `auto_after_checks`, merge without another approval only after verifying remote required checks, required external approvals, branch protections, mergeability, and reviewed head SHA still match. Never bypass protections or merge stale review results. In `review_only`, leave the clean PR/MR ready for humans.
16. Verify merge commit and target branch contains the reviewed head before closing/transitioning tickets. Clean up only worktrees, runtime resources, remote task branches allowed by policy, and lock created by this run. Mark complete only when requested merge/ticket transitions are verified.

## Approval policy

One approved plan has one approval gate. Before that gate, ask at most one consolidated clarification when execution would otherwise be wrong. After approval, do not ask permission to create tickets, branches, worktrees, commits, pushes, reviews, fixes, PRs/MRs, cleanup, or configured merge/ticket transitions. Apply safe reversible defaults within approved scope and continue.

On resume, never ask again when the current plan hash equals `approved_plan_hash`. If credentials are missing, a destructive operation was not approved, or scope must materially change, do not pepper the user with confirmations: record a precise blocker and next action. A materially replaced plan requires one new approval in a future resume; minor implementation details do not.

## Publisher mapping

- GitHub tickets: `gh issue`; GitLab tickets: `glab issue`; Jira tickets: configured Atlassian tools. Use configured ticket destination explicitly.
- GitHub code remote: `gh pr` and GitHub API for inline review comments on exact changed lines.
- GitLab code remote: `glab mr` and GitLab API for inline discussions with verified diff position SHAs.
- Local code remote: commit locally; no PR/MR or merge claim.

Preflight every distinct configured code host plus the configured ticket system. Never push to a remote whose current URL differs from recorded `remote_url`; block for reconfiguration instead. For Git remotes, preflight both read access and write access: verify the configured target branch exists or record why it does not, then run a non-destructive dry-run push probe against the verified remote. Record the exact probe command/result in run state.

If current agent lacks a required publisher, delegate exact approved payload to a capable agent. If none exists, or if write auth fails in this agent session while a user may still be able to publish manually outside it, save exact push/PR/review commands and bodies, mark `blocked`, and report truthfully. Do this as soon as the write-capability failure is known; do not wait until after push retries.

## Evidence

Tests must exercise changed behavior. UI evidence must show loaded final state; interactive changes require interaction plus assertion. Reject blank, loading, skeleton, error, clipped, or stale screenshots.
