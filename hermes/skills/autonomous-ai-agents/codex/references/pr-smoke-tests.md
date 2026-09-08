# Codex PR Smoke-Test Evidence

Validated pattern on a live GitHub PR:

- Read path: `codex exec --sandbox danger-full-access ...`; Codex ran wrapper-backed `gh pr view` and `gh pr diff --name-only`, returned exit 0, and reported title/author/head/files.
- Comment path: Codex ran wrapper-backed `gh pr comment`; returned exit 0 and a GitHub issue-comment URL.
- Combined path: Codex read `title,headRefOid`, then posted deterministic top-level comment; returned exit 0 and URL.

Use explicit smoke-test text for mutation tests. Verify returned URLs through `gh api repos/OWNER/REPO/issues/PR/comments` with the same wrapper. A provider websocket warning may appear while Codex still completes; classify separately from CLI result and review-contract status.

For service workers, keep captured logs per attempt. Do not append unrelated Codex sessions into one review log; mixed logs can falsely combine old blocked/approved output with a current run.
