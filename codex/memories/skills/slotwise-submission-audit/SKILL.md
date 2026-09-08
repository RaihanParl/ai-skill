---
name: slotwise-submission-audit
description: Audit the SlotWise challenge repo for submission readiness or "is this good enough to submit?" requests. Use when the user wants a company-style verdict, a highest-quality objective audit, or a fix-plan handoff.
argument-hint: "[mode]"
allowed-tools:
  - Read
  - Grep
  - Bash
---

# SlotWise Submission Audit

Use this when:
1. The user asks whether the SlotWise repo is ready to submit.
2. The user wants a review "as if you are the company."
3. The user asks to verify `OBJECTIVES.md` at the highest quality.
4. The user wants a fix plan handoff before implementation.

Do not use this when:
1. The task is only to answer a narrow repo-orientation question like frontend URL or whether Playwright exists.
2. The task is a generic PR review unrelated to submission readiness.

## Inputs / context to gather first

1. Confirm the working tree scope:
   - repo root or a worktree under `worktrees/*`
   - current branch and any existing diff
2. Read the challenge and evidence docs first:
   - `OBJECTIVES.md`
   - `RESULT.md`
   - `SECURITY.md`
   - `PERF.md`
   - `NOTES.md`
   - `docs/adr/recurring-bookings.md` if recurring bookings are part of the claimed scope
3. Read the relevant test/config surfaces before judging readiness:
   - `package.json`
   - `playwright.config.ts`
   - `playwright.web.config.ts` if present
   - `e2e/api.spec.ts`
   - `e2e/web.spec.ts` if present
   - touched API/frontend files named in the diff or PR

## Procedure

1. Start with the verdict frame.
   - If the user wants a company-style review, plan to answer with a clear submit/not-submit verdict.
   - If they want a handoff plan, separate "audit findings" from "execution plan."

2. Verify objective coverage against `OBJECTIVES.md`.
   - Map each objective to code, tests, docs, or evidence.
   - Treat `RESULT.md` as a claim sheet, not authority.
   - Look for semantic gaps even if tests are green.

3. Check the high-risk areas that previously hid real issues.
   - Booking creation and tenant-local date handling.
   - Availability boundary behavior near tenant day edges.
   - Utilization math and range clipping.
   - Webhook authentication in `services/api/src/routes/payments.ts`.
   - Browser-test selector realism and keyboard interaction.
   - Evidence quality in screenshots and packaging outputs.

4. Run or inspect verification in this order when the environment allows it.
   - `npm test`
   - `npm run typecheck`
   - `npm run benchmark:availability`
   - `npm run test:e2e`
   - `npm run test:e2e:web` if browser UI flows are part of the claim
   - `npm audit --omit=dev`
   - `npm run submit` if packaging/readiness is part of the request

5. Judge evidence quality, not just pass/fail status.
   - Weak assertions like `if (!paymentId) return` are not strong proof.
   - A screenshot must show the actual SlotWise UI.
   - Self-contained Playwright setup is stronger than "tests pass if the API is already running."

6. If asked to fix, move from findings to edits.
   - Keep reviewer findings terse and line-specific.
   - Use a worktree + branch flow if the user asks for isolation.
   - Re-run the affected checks after each task, using Playwright where needed.

7. If asked for a handoff plan instead of edits, write an ordered plan.
   - Put the highest-risk blocker first.
   - Add acceptance criteria and stop conditions for each phase.
   - Preferred order from prior successful handoff:
     1. Webhook auth
     2. Self-contained Playwright
     3. Stronger E2E assertions
     4. Browser-level UI validation
     5. Screenshot replacement
     6. Claims/doc cleanup
     7. Final verification and packaging

## Efficiency plan

1. Read docs and test config before opening many implementation files.
2. Grep for exact strings first:
   - `x-provider-signature`
   - `evaluateCancellation`
   - `refundedCents`
   - `reuseExistingServer`
   - `if (!paymentId) return`
3. If reviewing a PR, inspect the changed-file list before guessing file paths.
4. Cache the current verification totals and exact blocker strings so the final report stays concrete.
5. Stop broad searching once the verdict can be supported by direct code/test/doc evidence.

## Pitfalls and fixes

- Symptom: green tests but repo still is not submission-ready.
  - Likely cause: semantic gaps or misleading evidence docs.
  - Fix: audit against `OBJECTIVES.md` directly and inspect the business rule, not just the suite output.

- Symptom: `npm run test:e2e` fails with `connect EPERM ::1:4000` or only passes when a server is already running.
  - Likely cause: missing self-contained Playwright `webServer` setup or local-process restrictions.
  - Fix: treat this as a readiness gap until Playwright can start the needed app itself or you can verify in an environment that allows it.

- Symptom: benchmark fails with `listen EPERM` from `tsx`.
  - Likely cause: local IPC socket blocked by the environment.
  - Fix: rerun in an environment that allows the local pipe and record the measured result.

- Symptom: browser tests pass without proving real accessibility or UI flow behavior.
  - Likely cause: selectors are stale or the test uses `.focus()` instead of actual keyboard input.
  - Fix: drive the real UI (`.service-card`, `Tab`, `Enter`/`Space`) and assert visible state changes.

- Symptom: cancellation or refund behavior looks correct at a glance but is still wrong.
  - Likely cause: overwrite of `refundedCents`, hard-coded future dates, or route logic bypassing `evaluateCancellation`.
  - Fix: preserve cumulative refunds, derive dates relative to a controlled clock, and verify the route calls the policy logic.

## Verification checklist

- `OBJECTIVES.md` claims are matched to current code/tests/docs, not only `RESULT.md`.
- Any readiness verdict names the blocking issues explicitly.
- Test totals in docs match the actual rerun you performed or the exact evidence you inspected.
- Security-sensitive routes are checked for real validation, not header presence.
- Playwright evidence is self-contained or clearly called out as not self-contained.
- If a fix plan was requested, it is ordered, actionable, and includes acceptance criteria.
