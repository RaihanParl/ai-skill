# Argus own-PR session lessons

## Live workflow

A live own-PR fixer was built and exercised against PR #578. The PR was open, non-draft, user-owned, and had an external `CHANGES_REQUESTED` review. It initially conflicted with main. Remediation reconciled main, made a bounded descriptor change, pushed, and posted a reviewer-ping comment. A remaining real-provider evidence blocker was preserved rather than falsely marked clean.

## Important eligibility lessons

- Review IDs from GitHub REST JSON are integers. Convert IDs to strings before passing them to `subprocess.Popen`; otherwise detached worker launch fails with `TypeError: expected str, bytes or os.PathLike object, not int`.
- Do not require external review `commit_id` to equal current head during discovery. Review feedback on an older head is precisely what should trigger current-head reconciliation and a fresh read-only `/review`.
- Account aliases can appear in GitHub data. Maintain an explicit self-login set and exclude all of it from external-review selection and ownership checks.

## Cron lessons

- Hermes cron parent must launch detached workers because remediation and Codex runs exceed the scheduler foreground cap.
- Close worker stdin with `subprocess.DEVNULL`, use `start_new_session=True`, persist PID/head/review ID, and use a nonblocking lock.
- Same-head/same-review state must suppress duplicate launches. A blocked state is retryable only when head or review changes, unless user explicitly requests a retry.
- Cron `last_status: ok` proves launcher execution only. It does not prove worker completion, GitHub push, reviewer comment, or Telegram delivery.
- Script-owned Telegram delivery can use `deliver=local`, but completion notification must be verified independently from scheduler status.

## Verification recipe

1. Compile script with `python3 -m py_compile`.
2. Run no-apply URL dry-run and confirm author, review, head, mergeability, and eligibility.
3. Run full apply launcher and verify detached worker state files and logs.
4. Verify live GitHub head, push commit, comment URL, and review/fix blocker result.
5. Verify cron with `hermes cron list`, gateway health, and a manual cron tick.
6. If no Telegram arrives, inspect worker completion and explicit send result; do not infer delivery from an old message timestamp.

## Failure handling

A verified native transport failure was routed through the requested fallback: capture evidence, create an Argus issue through `/issue`, then continue with another native path or isolated fallback worker. Keep the issue URL in final reporting.
