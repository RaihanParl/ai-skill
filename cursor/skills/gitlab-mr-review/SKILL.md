---
name: gitlab-mr-review
description: >-
  Review GitLab merge requests on repo.transjakarta.co.id via glab: fetch MR
  context, read existing threads, pull Jira AC via Atlassian-Rovo-MCP
  (mcp-remote), map AC vs diff, post inline comments, resolve fixed
  open_code_agent threads, and report verdict. Use when the user says
  "mr this", "pr this", shares a repo.transjakarta.co.id merge request URL,
  or asks to review a GitLab MR.
---

# GitLab MR Review (glab)

GitLab host: `repo.transjakarta.co.id`

Applies to any project group on that host (including `smpob` and `tj-ai`). Do not treat examples as the only supported groups.

This skill overrides `creating-pull-requests` / `gh` / Bugbot for TransJakarta GitLab MRs.

## Triggers

Run this workflow immediately (no clarifying questions) when any of these appear:

- User says **"mr this"** or **"pr this"** with a GitLab MR URL
- Any URL containing `repo.transjakarta.co.id` and `merge_requests`
- Any URL containing `/-/merge_requests/`
- User asks to review a GitLab merge request or MR

Skip posting comments only if the user explicitly says not to (e.g. "review only", "don't comment").

## Workflow

1. Parse `project path` and `MR ID` from the URL.
   - Example: `https://repo.transjakarta.co.id/smpob/weltevreden/-/merge_requests/42`
   - Project: `smpob/weltevreden`, MR: `42`

2. Fetch context with glab (run commands, do not guess). Default host is `repo.transjakarta.co.id`:
   ```bash
   glab mr view <id> -R <project> --comments
   glab mr diff <id> -R <project> --color=never
   glab api "projects/<encoded-project>/merge_requests/<id>/discussions"
   ```
   If commands fail with auth errors, retry with `GLAB_HOST=repo.transjakarta.co.id` prefix.

3. Read all existing MR comments and discussion replies before reviewing. This includes top-level notes, inline diff discussions, resolved and unresolved threads, and replies from the author or other reviewers. If a finding is already covered by an existing thread, do not duplicate it; read the replies and either follow up inline only if the issue is still unresolved, or resolve it if the latest diff clearly fixes it and the thread is eligible to resolve.

4. **Jira acceptance criteria (required when ticket key is present).** Prefer **`user-Atlassian-Rovo-MCP`** / **`Atlassian-Rovo-MCP`** (mcp-remote in `~/.cursor/mcp.json`). Do **not** rely on marketplace `plugin-atlassian-atlassian` (often stuck on OAuth / Not Found).

   - Extract ticket key from branch name, MR title, or description (e.g. `feature/TOTS-150-...`, `refactor/TOTS-150: ...` → `TOTS-150`).
   - Fetch with Atlassian Rovo MCP:
     - `cloudId`: `smpobtransjakarta.atlassian.net` (or hostname from the Jira URL)
     - `getJiraIssue` with `issueIdOrKey`, `responseContentFormat: "markdown"`
     - If needed, `getAccessibleAtlassianResources` first
   - Build an **AC vs MR** checklist: each acceptance criterion → Met / Partial / Not met / Out of scope, with evidence from the diff.
   - Review engineering risks even when AC is met (tests, regressions, security). Mark side changes outside ticket AC as warnings, not AC fails, unless they break the ticket.
   - If Rovo MCP is not `ready`, say so briefly, continue the code review without blocking, and note AC was not verified.

5. Review **only** the MR changes. Prioritize:
   - Bugs and regressions
   - Security risks
   - Unclear or risky behavior
   - Missing tests
   - AC gaps from step 4

6. If the MR title/description is missing, vague, or lacks enough context to review confidently, say so clearly and recommend what the author should add.

7. **Post inline diff comments automatically** on each exact changed line that has a finding. Do not ask the user for permission before posting comments when they use "mr this" or "pr this". This is mandatory when findings can be anchored to changed code. Every distinct bad/risky changed line must get its own inline comment. Do not bundle multiple findings into one comment, and do not post one big top-level review summary when line anchors exist.
   ```bash
   ~/.cursor/scripts/glab-mr-inline-comment.sh <mr-id> <project> <file> <line> "<comment>"
   ```
   Use the user-level helper script instead of rechecking `glab mr note --help`. If the helper script is missing, recreate it under `~/.cursor/scripts/glab-mr-inline-comment.sh` with the canonical `glab mr note create <id> -R <project> --file <path> --line <n> -m "<comment>"` command. Use `--old-line` for comments on removed lines. Resolve exact line numbers from the MR branch file via GitLab API if needed.
   Skip posting only if the user explicitly says not to (e.g. "review only", "don't comment"). If a top-level summary note was posted by mistake, delete it and repost every finding inline on its own line.

8. **If the MR is already good and has no findings**, post a top-level approval/no-blockers note automatically. Do not stay silent. Use a concise comment that states the MR was reviewed and is approved or has no blockers, with 1-2 concrete reasons from the review.
   ```bash
   glab mr note create <id> -R <project> -m "<approval/no-blockers comment>"
   ```
   Example comment: `Reviewed and approved. No blockers found: the migration chain is valid, existing rows are covered by the server default, and rollback is consistent with the existing migration style.`

9. **On re-review**, fetch open discussion threads via the GitLab API and resolve any that are addressed in the latest diff:
   ```bash
   glab api "projects/<encoded-project>/merge_requests/<id>/discussions"
   glab api --method PUT "projects/<encoded-project>/merge_requests/<id>/discussions/<discussion_id>" -f resolved=true
   ```
   Only resolve threads that are `resolvable=true`, authored by `open_code_agent`, and whose issue is clearly fixed in the new diff. Never resolve threads created by other people.

10. Writing style for posted comments: plain, direct, no em dashes.

11. Output format in chat:
    - **Summary** (1-2 sentences)
    - **Description quality** (sufficient / needs improvement + why)
    - **Jira AC** (ticket key + checklist: each AC → Met / Partial / Not met / Out of scope; or "not verified" if MCP unavailable)
    - **Findings** grouped by severity: Critical, Warning, Suggestion
    - **Verdict**: approve / request changes / needs better description first
      - AC met does not auto-approve if Critical/Warning engineering blockers remain
      - AC gaps alone can justify request changes
