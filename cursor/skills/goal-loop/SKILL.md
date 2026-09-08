---
name: goal-loop
description: Use when /goal runs, resumes, plans, builds, reviews, publishes, or finishes a configured multi-repository goal.
---

# Goal Loop

Configuration lives in `.goal/state.json`. Never infer ticket system, repository roles, target branch, code host, remote, or models when configured values exist. Ticket system controls issue operations; each repo's verified remote URL and `code_host` control push and PR/MR operations.

## Run files

Create `.goal/runs/<run-id>/` with:

- `state.json`: goal, status, phase, repo branches/worktrees, ticket IDs, PR/MR URLs, review rounds/comments, attempts, blocker, next action.
- `plan.md`: scope, assumptions, acceptance criteria, repo-specific tasks, test commands, dependencies, risks, rollback.
- `review.md`: reviewer findings and resolution.
- `artifacts/`: screenshots or other evidence only.

Update state after every external side effect. Write valid JSON via the file editing tool, never shell interpolation. Do not store credentials, tokens, environment dumps, or unredacted secrets.

Statuses: `planning`, `awaiting_approval`, `building`, `reviewing`, `publishing`, `completed`, `blocked`.

## Parallel safety

Multiple runs execute in parallel unless they conflict. Each run acquires only its own lock at `.goal/locks/<run-id>`. Never use `.goal/lock` or root-level run ownership. If that per-run lock already exists, stop; never delete a possibly live lock automatically. Release it on completed, blocked, or other orderly exit. After a crash, require explicit stale-lock verification before removal.

Different run IDs do not block each other just because they touch the same repository, branch from different base SHAs, or may edit overlapping files. Isolation comes from per-run locks, unique branches, unique worktrees, and unique runtime slots. If later integration or PR merge conflicts happen, block only the affected run with the exact conflict; never stop unrelated runs.

The orchestrator is the only writer of its run state and the only process allowed to create/remove worktrees, integrate commits, push, or publish for that run. Before any code, preflight, integration, push, review, QA, or publish operation, create or resume a per-run orchestrator worktree at `worktree_root/<run-id>/<repo>/orchestrator`; the main user worktree is only for shared `.goal/` state.

Plan work as a dependency DAG. Every build task must record:

- unique task ID and repository
- immutable base commit SHA
- dependency task IDs
- conservative file/symbol write set
- unique branch `goal/<run-id>/<task-id>`
- unique worktree under configured `worktree_root/<run-id>/<repo>/<task-id>`
- validation commands and runtime slot

Dispatch ready tasks concurrently up to `max_parallel_builders` only when dependencies are complete and their write sets do not overlap. Unknown or broad write sets count as overlapping. Tasks touching the same migration chain, lockfile, generated output, schema, API contract, shared type, or central configuration must run serially unless the planner proves independence.

Route each task by repository role and actual change:

- frontend UI/client task -> `goal-frontend-builder`
- backend/API/data task -> `goal-backend-builder`
- infrastructure/CI/container/deployment task -> `goal-infra-builder`
- auxiliary, mixed, or unknown task -> `goal-builder`

Do not route by folder name alone. Planner records the chosen builder for every task; orchestrator verifies it against repository evidence.

Create a task branch/worktree only when the task becomes ready. Its immutable base SHA is the repository integration HEAD after all dependencies have been integrated. Each builder commits its own task branch and returns the commit SHA. Builders never share a branch, worktree, state file, service port, writable artifact path, database, or deployment environment. Quote all paths and never interpolate goal text into shell commands. Assign unique ports/temp/artifact directories when tests can run concurrently; serialize tests that require a shared database, singleton service, device, emulator, or external environment.

## Runtime isolation

Use `runtime_port_base` and `runtime_port_stride` from root state. Slot `n` owns the half-open port range `[base + n*stride, base + (n+1)*stride)`. Before launch, probe the entire requested subset; if occupied, assign another free recorded block. Bind development/test servers to `127.0.0.1`, never all interfaces.

For each slot also assign:

- `TMPDIR` and writable caches under the task artifact directory
- unique `COMPOSE_PROJECT_NAME=goal_<run-id>_<slot>` when Compose is used
- unique test database/schema name when database tests run
- unique log, trace, screenshot, and coverage paths
- recorded process IDs/container names and bounded readiness timeout

Detect each stack's supported port flag/environment variable from repository scripts and documentation; never assume every app uses `PORT`. If a service has an unavoidable fixed port or shared writable dependency, serialize it. The owner of a runtime slot must terminate every process/container it starts and verify ports are released, including failure paths.

For each repository, create one integration branch/worktree from the recorded base SHA. After builders finish, the orchestrator integrates task commits there one at a time in dependency order. Run repository-level checks after each integration batch and full relevant checks before review. On cherry-pick/rebase conflict, abort the operation, preserve task commits/worktrees, mark the run blocked or replan, and never auto-resolve by discarding either side.

## Flow

Steps 1-9 are shared by both modes. The orchestrator selects mode based on whether "fast" appears in the goal description.

### Shared steps (both modes)

1. Read root state for shared config and the run registry, then read this run's state. Resume idempotently; never recreate recorded tickets, branches, or PRs/MRs.
2. Inspect every configured repo and its instructions. Confirm clean enough operation without reverting unrelated changes.
3. Delegate planning to `goal-planner`. Ask one consolidated clarification only when needed to avoid incorrect work.
4. Save plan hash and request one explicit approval before ticket creation, code changes, pushes, or publishing. Persist `approved_at` and `approved_plan_hash`.
5. Preflight required CLIs/auth and repository remotes. Missing publisher auth blocks publishing, not local planning. For every non-local code remote, verify actual push capability before code changes using a non-destructive git write probe from the same repo/worktree family that will later push (for example `git push --dry-run <remote> HEAD:refs/heads/goal-preflight/<run-id>`). `gh auth status`, `glab auth status`, `ssh -T`, and `git ls-remote` are not sufficient by themselves because they can pass while write access still fails.
6. Create only useful tickets. Do not create empty FE/BE children for repos unaffected by the goal.
7. Record latest target commit SHA per repository, then create isolated orchestrator, task, and integration worktrees without modifying existing user worktrees. Never force-push or rewrite shared history.
8. Dispatch safe ready tasks in parallel to `goal-builder` with exact worktree, branch, base SHA, write set, runtime slot, acceptance criteria, and test commands.
9. Verify returned commits and integrate them serially per repository. Run unit tests for changed logic and repository-level integration tests for changed boundaries, plus relevant lint, type, and build checks. A missing or genuinely inapplicable test layer must be recorded with reason; never silently skip it.

### Fast path (keyword "fast" in goal)
Review locally before push. Fix cycles stay local — only push once clean.

10. Delegate the integrated local diff and acceptance criteria to `goal-reviewer`. Do NOT push or open PR/MR yet — review against the local integration branch diff. Post findings without external APIs. Use `diff` against the base SHA, not a remote.
11. Fix actionable reviewer findings on new isolated task branches from current integration HEAD, reintegrate, and rerun affected unit/integration checks. Repeat until clean or `fix_cycle_limit`.
12. Delegate the fixed integrated product to `goal-qa` with isolated startup commands, health checks, acceptance scenarios, runtime allocation, integration SHAs, and artifact paths. For changed user-facing UI, delegate QA evidence to `goal-visual-reviewer` after QA.
13. Only when local review and QA pass clean: push each integration branch to its configured remote and open or update one draft PR/MR against its configured target branch. Derive GitHub/GitLab from `repo_map`, not ticket system. Verify and record remote URL, PR/MR URL, number/IID, base SHA, and head SHA. If earlier write preflight was skipped or has gone stale due to auth/remote changes, rerun it before the real push.
14. Mark draft PR/MR ready immediately — the diff was already reviewed and fixed locally. No remote review needed.
15. When `merge_mode` is `auto_after_checks`, merge without another approval only after verifying remote required checks, required external approvals, branch protections, mergeability, and reviewed head SHA still match. Never bypass protections. In `review_only`, leave the clean PR/MR ready for humans.
16. Verify merge commit and target branch contains the reviewed head before closing/transitioning tickets. Clean up only worktrees, runtime resources, remote task branches allowed by policy, and lock created by this run. Mark complete only when requested merge/ticket transitions are verified.

### Remote review mode (default, no "fast" keyword)
Push first, then review on the PR/MR. Standard push/fix/review loop.

10. Delegate the integrated product to `goal-qa` with isolated startup commands, health checks, acceptance scenarios, runtime allocation, integration SHAs, and artifact paths. For changed user-facing UI, delegate QA evidence to `goal-visual-reviewer` after QA.
11. Push each integration branch to its configured remote and open or update one draft PR/MR against its configured target branch. Derive GitHub/GitLab from `repo_map`, not ticket system. Verify and record remote URL, PR/MR URL, number/IID, base SHA, and head SHA. If earlier write preflight was skipped or has gone stale due to auth/remote changes, rerun it before the real push.
12. Delegate the exact remote PR/MR diff and acceptance criteria to `goal-reviewer`. Post each actionable finding as an inline PR/MR comment only when its path and changed-line position are valid; otherwise post it in one review summary. Never invent a line position. Record comment/discussion URLs.
13. Fix actionable reviewer or QA findings on new isolated task branches from current integration HEAD, reintegrate, push updated commits, and rerun affected unit/integration checks plus full required QA and review. Continue until clean. Stop without merge on hard blocker, repeated no-progress result, or `fix_cycle_limit`; record exact unresolved findings.
14. Mark draft PR/MR ready only after latest head SHA has passing checks, QA, visual review when applicable, and zero unresolved actionable review findings.
15. When `merge_mode` is `auto_after_checks`, merge without another approval only after verifying remote required checks, required external approvals, branch protections, mergeability, and reviewed head SHA still match. Never bypass protections or merge stale review results. In `review_only`, leave the clean PR/MR ready for humans.
16. Verify merge commit and target branch contains the reviewed head before closing/transitioning tickets. Clean up only worktrees, runtime resources, remote task branches allowed by policy, and lock created by this run. Mark complete only when requested merge/ticket transitions are verified.

## Approval policy

One approved plan has one approval gate. Before that gate, ask at most one consolidated clarification when execution would otherwise be wrong. After approval, do not ask permission to create tickets, branches, worktrees, commits, pushes, reviews, fixes, PRs/MRs, cleanup, or configured merge/ticket transitions. Apply safe reversible defaults within approved scope and continue.

On resume, never ask again when the current plan hash equals `approved_plan_hash`. If credentials are missing, a destructive operation was not approved, or scope must materially change, do not pepper the user with confirmations: record a precise blocker and next action. A materially replaced plan requires one new approval in a future resume; minor implementation details do not.

## Publisher mapping

- GitHub tickets: `gh issue`; GitLab tickets: `glab issue`; Jira tickets: configured Atlassian tools. Use configured ticket destination explicitly.
- GitHub code remote: `gh pr` and GitHub API for inline review comments on exact changed lines. Push, open, review, and merge GitHub PRs with the `gh` CLI, not raw git push to the remote branch alone.
- GitLab code remote: `glab mr` and GitLab API for inline discussions with verified diff position SHAs.
- Local code remote: commit locally; no PR/MR or merge claim.

## PR/MR conventions

- PR/MR title must mirror the source issue title exactly, including its prefix (for example `S2B: Customers only see and book real capacity`, `S2H: Refund requests are exact and retry-safe`). Do not invent a paraphrased title.
- PR/MR body must include a closing reference to the issue so merge auto-closes it: `Closes #<number>` (GitHub) or `Closes #<iid>` / `Resolves #<iid>` (GitLab). Verify `closingIssuesReferences` (GitHub) or the linked issue (GitLab) is populated after creation.
- Use the code host CLI for the full publish path: `gh` for GitHub (push, `gh pr create`, review, `gh pr merge`) and `glab` for GitLab.

Preflight every distinct configured code host plus the configured ticket system. Never push to a remote whose current URL differs from recorded `remote_url`; block for reconfiguration instead. For Git remotes, preflight both read access and write access: verify the configured target branch exists or record why it does not, then run a non-destructive dry-run push probe against the verified remote. Record the exact probe command/result in run state.

If current agent lacks a required publisher, delegate exact approved payload to a capable agent. If none exists, or if write auth fails in this agent session while a user may still be able to publish manually outside it, save exact push/PR/review commands and bodies, mark `blocked`, and report truthfully. Do this as soon as the write-capability failure is known; do not wait until after push retries.

## Evidence

Tests must exercise changed behavior. UI evidence must show loaded final state; interactive changes require interaction plus assertion. Reject blank, loading, skeleton, error, clipped, or stale screenshots.
