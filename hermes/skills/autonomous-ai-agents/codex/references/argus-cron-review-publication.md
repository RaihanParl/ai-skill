# Argus Cron Review Publication

Use when a Codex subprocess drives an Argus review watcher.

## Required sequence

1. Run `/review` against live PR metadata and exact head.
2. Require receipt, helper-provenance, ledger, trust-gate, identity, and live-state checks.
3. In explicitly authorized cron mode only, run `/post-review` on unchanged validated evidence.
4. Verify returned review ID/URL with wrapper-backed `gh api`, including `commit_id == reviewed head`.
5. Mark `completed` only after publication verification. Mark `blocked` for a valid blocked publication; mark `failed` for process/publication errors.

## Durable pitfalls

- Normal `/review` is read-only; cron publication needs explicit prompt and contract authorization. Do not infer permission from a generic review request.
- A watcher filtering `review-requested:@me` will skip explicitly supplied PRs without that GitHub review request. Provide a direct-target path for manual smoke tests.
- Use a unique log per attempt. Appending Codex transcripts lets old `blocked` or `approve` text corrupt current-result classification.
- Classify only the final Codex response, not the full transcript. Contract text can contain words such as `configuration blocker` without being the terminal verdict. Recognize phrasing variants such as `was blocked by:`.
- A blocked review may legitimately publish one clearly marked `COMMENT` review through `/post-review`; distinguish `blocked_published` from successful approval/comment publication.
- Codex exit 0 is insufficient. Confirm exact-head review URL and live GitHub state independently.

## Evidence

Record target, reviewed head, report path, publication status, review ID/URL, and final state. Preserve unrelated checkout modifications. Never publish stale evidence after PR head changes.
