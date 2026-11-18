---
name: herdr-orchestration
description: Execute grouped tasks with parallel Herdr workers in the current workspace, using isolated worktrees and push-only blocker/result messages. Use when the user invokes $herdr-orchestration or requests a Herdr team to execute a task list or larger assignment. For ordinary pane control, use herdr.
---

# Herdr orchestration

Coordinate the task to its authorized endpoint. Keep fixes small, workers independent,
and communication restricted to this team in the current Herdr workspace.

## Define the delivery

- Extract the user's task, grouping key, worker count, exclusions and endpoint. Use
  explicit groups; otherwise choose independent groups that serve the requested outcome.
  Do not require a list: a larger prompt can be split into bounded work packages.
- Default to one worker per independent group, adjusted for dependencies and host
  resources. Honor an explicit worker count; queue groups if there are fewer workers.
  Workers do not spawn extra agents without authorization.
- For repository delivery, default to one full-scope PR per group when PRs are part
  of the requested/repository workflow. Multiple issues in one group share that PR.
  Preserve an explicit exact-PR-count requirement; do not create partial/substitute PRs.
  For other work, define the corresponding artifact or observable result per group.
- Read applicable AGENTS.md, delivery guidance and relevant skills. Reuse current
  issues, decisions and evidence. Do not copy this skill's source project's rules into
  another repository. For UI work, inspect its governing design/mockup before coding.
- Record authorization separately for local work, publication, merge, deployment and
  shared-data writes. Execution or PR creation alone does not authorize the latter
  actions. A request to close issues through merged PRs includes that delivery intent;
  honor applicable session/repository gates. Do not ask again for authorization already given.

## Establish the team and push route

Read the installed **herdr** skill before Herdr commands; use its verified Linux
caller wrapper and installed CLI help. This skill requests Herdr orchestration,
not a replacement team through another agent launcher.

1. Verify the coordinator's caller identity. Capture its actual workspace/pane IDs;
   never infer them from focus or inherited environment alone. If verification fails,
   follow herdr's bounded diagnostic path; do not forge context or bypass the binding.
2. Select the push transport and verified coordinator address before launching workers.
   Prefer the available native task-message tool (for Codex, discover
   `send_message_to_thread`). Otherwise use the worker's verified Herdr wrapper:
   `agent prompt <coordinator-pane> <message>` **without `--wait`**. Respect the live
   schema/message size limits. Never copy a prior run's IDs. This skill's no-wait and
   coding-worktree rules specialize herdr's generic dispatch examples.
3. Supply the **currently verified** team allowlist: coordinator/worker panes, names
   and conversation IDs when available. Add members as they are verified and notify
   existing members before peer communication; never invent future IDs. Validate each
   target belongs to this workspace before reading, messaging or controlling it. Scope
   listings to this workspace; no unrelated conversations, agents, machines or sessions.
   Existing panes/agents are not automatically team members.
4. Launch the first worker for identity/bootstrap only; require one pushed receipt
   confirming its identity, cwd and notification route before assigning substantive
   work or launching the remainder. Submission acknowledgement alone is insufficient.
   If no receipt arrives, leave dispatch unconfirmed and yield; silence is not a
   detected stall. Diagnose once upon an actual delivery error or reported failure,
   not through a timeout/watcher. If neither push route works, report the precise
   prerequisite and continue authorized coordinator-local work without pretending a
   team ran. Do not invent a polling substitute.

## No polling

**Workers push; the coordinator reacts.** This is an operational constraint.

- No routine agent/status/list/read loops, periodic progress prompts, timed filesystem
  scans, repeated timeout waits, inotify restart loops, lifecycle watchers, or shell
  daemons that poll on the coordinator's behalf. Calling these "event-driven" does
  not make them acceptable. Do not use `agent wait` or prompt `--wait` for orchestration.
- A file is a durable report, not a notification channel. Write the details, then push
  its path and event directly to the coordinator. Do not expect the coordinator to
  discover files. Do not replace push with a sleeping/background scanner.
- Workers push only a bootstrap receipt, actionable BLOCKED, READY, REVIEW/FIX, or
  COMPLETE handoff. Coordinator assignments, repair/review instructions and final
  notices are allowed; heartbeat/status chatter is not. Waiting for a build/test command to
  finish is distinct from polling workers. One-time prerequisite inspection, diagnosis
  of a reported failure, and post-action verification are allowed.
- When only workers have actionable work, yield the coordinator turn with an honest
  running status. Direct worker messages resume coordination. Do not keep the turn
  alive through checks or empty updates, and do not label the assignment complete.

## Launch isolated workers

Before launching the first worker, read the local preference at
`~/.config/herdr-orchestration/worker.json`. It contains a Herdr agent `kind`
and an `args` array of native agent command-line arguments, for example
`{"kind":"opencode","args":["--model","provider/model-id"]}`. Do not put
credentials in this file or commit it to a repository.

If the file is absent, ask the user which supported agent and model to use and
whether to save that choice as the default. Check the installed agent help and
available models to determine the correct native arguments. Save the preference
only if requested, creating the parent directory as needed. A choice for the
current task also permits proceeding without saving. An explicit choice in the
current request overrides the saved preference for that task; update the saved
preference only when the user asks. If a configured agent or model is unavailable,
report the prerequisite and do not silently substitute another one.

Start workers using the chosen `--kind` and pass each configured native argument
after `--` in `herdr agent start`, preserving argument boundaries. Apply the same
choice to all workers unless the user specifies otherwise.

For code changes, give each coding worker a separate branch/worktree from the correct
current base. Preserve the existing checkout and others' dirty files. Read-only work
need not create a worktree. Invocation authorizes these local worker checkouts unless
user constraints say otherwise; honor explicit topology and location choices.

Use sibling panes in the current workspace by default, sensible split geometry and
`--no-focus`. Parse returned IDs; start each agent only in its available shell pane,
with the worktree as cwd. Do not create another workspace. Do not close unrelated panes.
Allocate distinct local ports/data directories and bound heavy parallel builds to
available resources. Give shared-file/dependency changes a clear owner to avoid races.

Keep a small durable ledger: group/tasks, worker/pane, worktree/branch, authorized
endpoint, current head, result/PR, evidence, blockers, review and actual closure.
No custom queue service, scheduler, notification daemon or framework is needed.

Each dispatch must supply:

```text
Read herdr-orchestration/SKILL.md and the installed herdr skill.
Group/task and complete acceptance scope: ...
Workspace/team allowlist and coordinator push target: ...
Work location; worktree/branch/base if coding; shared ownership/resources: ...
Deliverable count, authorized endpoint and separate action limits: ...
Report directory and applicable source/repository/design guidance: ...
Execute independently. Push BLOCKED with exact failure, affected outcomes,
attempts and requested help; continue independent work. Push READY with result,
revision when applicable, outcome evidence/limits and remaining actions.
Keep the work focused. No polling, outside-team contact or extra agents.
```

## Resolve blockers and concurrent changes

The coordinator owns resolution, not merely relaying a status report. Diagnose the
concrete failure and pursue a safe, authorized workaround while other work continues.

- Repair local dependencies, fixtures, ports and resource settings. For stale test
  pins/selectors/expected text, reconcile against the actual source contract, preserve
  strict assertions/preflight and obtain required technical re-review. Keep original
  and derived revisions plus failed attempts. Retire consumed owned baselines intact;
  do not delete claims/history or bypass data-isolation checks.
- A frozen candidate protects an active check's inputs, not future necessary fixes.
  After a check finishes, fix an observed in-scope defect, retain its old evidence and
  reverify affected inputs. Reuse valid unaffected results; do not rerun for unrelated
  main commits, evidence-only changes or formatting preferences.
- A closed issue or merged PR is not proof of acceptance. Inspect existing delivery
  before duplicating it. Reuse a complete fix; preserve/credit partial concurrent work
  and deliver only the remaining scope plus full acceptance evidence. Resolve any
  conflict with the user's exact deliverable count before publishing duplicates.
- Keep unrelated failures and unresolved BA decisions separate from assigned outcomes.
  A failed full run stays failed even if the assigned checks pass. Do not silently drop
  criteria, manufacture approval, change expectations to hide defects or call a mock
  a real-server result. Follow the repository's provisional-decision policy if any.
- Never turn "find a workaround" into bypassing an explicit hold, enforced protection,
  authorization boundary or privacy rule. Ask for the specific unavoidable action only
  after completing useful authorized preparation. Keep secrets/signed media URLs private.

## Review and finish

Reuse existing team members for required independent reviews, after the repository's
readiness conditions are met. Review the exact head, repair actionable findings in the
same deliverable, and re-review affected changes. Preserve the initial finding/fix
trail. Do not add reviewers or gates merely to make the process larger.

For authorized merges, use ordinary supported methods with an expected-head guard,
respect enforced protections, and prevent unintended deployment using an existing
supported control when applicable. After a merge error, read authoritative state
before deciding whether another attempt is appropriate; never replay a confirmed merge.

After each delivery, verify the observable endpoint: actual merge and intended issue
closures, creator assignment where required, or the requested artifact/result. Compare
reviewed/tested inputs with the delivered revision; concurrent unrelated changes need
not make whole trees identical. Update the ledger and existing trackers without erasing
others' edits. Keep pending approvals and separate failures explicit.

Finish only when every assigned group reaches its authorized endpoint or no authorized
unblocked work remains. Send a concise group→deliverable→actual-outcome summary. Preserve
worktrees/evidence by default, stop only owned disposable processes when finished, tell
workers the assignment is complete, and leave no monitoring loops running.

<!-- Evidence: observed five-worker grouped delivery, 2026-11-12; actual closures/review
receipts: https://github.com/letargusdev/argus-javoo/issues/395#issuecomment-6828257455 .
The user's explicit no-polling correction is implemented by direct worker pushes. -->
