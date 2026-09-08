# Task Group: SlotWise PR review, fix follow-up, and worktree-based submission flow
scope: reviewing SlotWise submission readiness, posting terse actionable PR comments, fixing the issues in an isolated worktree, and re-verifying before MR/PR handoff
applies_to: cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl; reuse_rule=safe for similar SlotWise PR review/fix runs in this repo family, but treat file paths, test counts, and worktree state as checkout-specific

## Task 1: Review PR #17 and post inline comments, outcome success

### rollout_summary_files

- rollout_summaries/2026-06-28T11-48-06-UPlU-pr_17_inline_review_comments.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T18-48-06-019f0e0e-eb17-7a41-8f03-f9d01c1c334a.jsonl, updated_at=2026-06-28T11:56:36+00:00, thread_id=019f0e0e-eb17-7a41-8f03-f9d01c1c334a, success; review-only pass that posted 3 inline findings)

### keywords

- slotwise-raihanparl, PR #17, github-pr-review, gh api, inline comments, git grep, rg parse error, evaluateCancellation, refundedCents, keyboard navigation, time-dependent test

## Task 2: Submission review and initial fix pass in a new worktree, outcome partial

### rollout_summary_files

- rollout_summaries/2026-06-28T11-41-05-qSrc-slotwise_pr_review_fix_worktree_and_comment_followup.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl/worktrees/fix-submit-quality, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T18-41-05-019f0e08-7d00-7ce1-9be9-d510953a012e.jsonl, updated_at=2026-06-28T11:56:05+00:00, thread_id=019f0e08-7d00-7ce1-9be9-d510953a012e, partial; reviewer-style readiness check before opening PR)

### keywords

- OBJECTIVES.md, RESULT.md, worktrees/fix-submit-quality, codex/fix-submit-quality, DELETE /bookings/:id, evaluateCancellation, .service-card, .field__control, Playwright, EPERM tsx pipe
- Related skill: skills/slotwise-submission-audit/SKILL.md

## Task 3: Fix PR #17 issues and recheck after review comments, outcome partial

### rollout_summary_files

- rollout_summaries/2026-06-28T11-41-05-qSrc-slotwise_pr_review_fix_worktree_and_comment_followup.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl/worktrees/fix-submit-quality, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T18-41-05-019f0e08-7d00-7ce1-9be9-d510953a012e.jsonl, updated_at=2026-06-28T11:56:05+00:00, thread_id=019f0e08-7d00-7ce1-9be9-d510953a012e, partial; fix pass hit final git/worktree blocker after tests)

### keywords

- createTestClient del, cancelling a partially refunded booking preserves prior refunds, glowBookingStart, reuseExistingServer false, Tab Enter, refund overwrite, index.lock, usage limit, 60/60, 38/38, 7/7

## User preferences

- when the user asked, "act as if you are the company i applied to, check my work here, check the [OBJECTIVES.md](OBJECTIVES.md) are all of my work good enough? should i submit it now?" -> answer like a reviewer, be blunt about readiness, and say submit/not submit clearly instead of giving a soft summary [Task 2]
- when the user asked, "review this, comment on every line if you find something worth reviewing" -> keep PR reviews terse, line-specific, and limited to actionable findings rather than broad commentary [Task 1]
- when the user followed with "fix it, check again please" and "check the comment and fix it" -> turn review findings into concrete code changes, then re-verify instead of stopping at analysis [Task 1][Task 3]
- when the user asked, "create new worktree folder, fix it, create mr" -> prefer isolated worktree + branch + MR/PR flow for repair work in this repo family [Task 2]

## Reusable knowledge

- For SlotWise submission checks, read `OBJECTIVES.md`, `RESULT.md`, `SECURITY.md`, `PERF.md`, `NOTES.md`, and the touched test files before deciding whether the work is ready; this surfaced real blockers instead of trusting the summary doc alone [Task 2]
- In this repo, `DELETE /bookings/:id` originally only flipped booking status; cancellation quote logic lived in `services/api/src/routes/payments.ts` via `evaluateCancellation`, so correct cancellation behavior required calling `evaluateCancellation`, rejecting disallowed cancellations with `409`, updating payment refund/status, and writing a `booking.cancelled` audit entry [Task 2][Task 3]
- The new booking UI uses `.service-card` buttons, not `.field__control`, so browser tests for the booking flow should drive the card interaction and then assert the availability panel appears [Task 2][Task 3]
- Good PR-review targets from this repo were time-dependent tests, refund-accounting regressions, and accessibility coverage that used `.focus()` instead of real keyboard input; the three landed comments on PR #17 all came from tracing those concrete risks through the diff [Task 1]
- `createTestClient` exposes `get`, `post`, `patch`, and `del`, not `delete`; use `c.del(...)` in API regressions [Task 3]
- The stable cancellation test helper here is `glowBookingStart(daysAhead = 30)` in `e2e/api.spec.ts`, which derives a future weekday booking start relative to the test clock instead of hardcoding a date [Task 3]
- `playwright.config.ts` and `playwright.web.config.ts` were hardened with `reuseExistingServer: false` to reduce stale local-server failures during browser verification [Task 3]
- `RESULT.md` needed to reflect actual verification totals instead of aspirational claims; this rollout updated it to `60/60` unit tests, `38/38` API E2E tests, and `7/7` browser E2E tests [Task 3]

## Failures and how to do differently

- Symptom: `rg` failed while tracing review targets. Cause: unescaped pattern / regex parse issues. Fix: switch to `git grep` or quote the pattern carefully in this repo before assuming the symbol is absent [Task 1]
- Symptom: guessed code path like `packages/core/src/cancellation.ts` did not exist. Cause: path was assumed from concept name instead of the actual tree. Fix: inspect the PR file list and trace from touched files; the relevant policy code lived in `packages/core/src/policy.ts` [Task 1]
- Symptom: cancellation tests became time-dependent after 2026-06-29. Cause: E2E used a hard-coded start like `2026-07-01T03:00:00.000Z`. Fix: derive booking dates relative to a controlled clock with `glowBookingStart(...)` [Task 1][Task 3]
- Symptom: cancellation could reduce previously recorded refunds. Cause: code overwrote `refundedCents` with the latest policy result. Fix: preserve prior refunds with `Math.max(existing refundedCents, policy-entitled refund)` and add a regression for partially refunded bookings [Task 1][Task 3]
- Symptom: keyboard coverage passed without proving real keyboard navigation. Cause: the browser test used `.focus()` directly. Fix: use actual `Tab` and `Enter`/`Space` interaction and assert resulting state or availability [Task 1][Task 3]
- Symptom: `npm run test:e2e` / `npm run test:e2e:web` hit `EPERM ... tsx-*.pipe` or stale Playwright server behavior. Cause: sandbox IPC restrictions and server reuse flakiness. Fix: run with the needed permissions in environments that allow it and keep `reuseExistingServer: false` when re-verifying browser flows [Task 2][Task 3]
- Symptom: regression test failed on `c.delete`. Cause: wrong helper name. Fix: use `c.del` from `createTestClient` [Task 3]
- Symptom: final rerun / commit / push failed with `fatal: Unable to create '/Users/mraihanparlaungan/personal/slotwise-raihanparl/.git/worktrees/fix-submit-quality/index.lock': Operation not permitted`. Cause: git/worktree write was blocked after an account usage limit / approval gate. Fix: treat final commit/push as incomplete, report the blocker explicitly, and do not claim the last fixes were pushed without re-running in an environment that allows the git write [Task 3]

# Task Group: SlotWise objective audit and submission-quality verification
scope: auditing SlotWise challenge completeness against OBJECTIVES.md, fixing hidden semantic gaps, judging submission readiness, and preparing a handoff plan when implementation is deferred
applies_to: cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl; reuse_rule=safe for similar quality-audit or submission-readiness runs in this repo family, but treat exact test totals, benchmark numbers, and branch/PR references as checkout-specific

## Task 1: Audit OBJECTIVES.md against the repo and fix semantic correctness gaps, outcome success

### rollout_summary_files

- rollout_summaries/2026-06-28T10-23-39-bju8-slotwise_objectives_audit_quality_fix.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T17-23-39-019f0dc1-9a44-7671-87ce-ba56170f56e0.jsonl, updated_at=2026-06-28T10:30:19+00:00, thread_id=019f0dc1-9a44-7671-87ce-ba56170f56e0, success; objective audit, semantic bug fixes, benchmark, and PR #11)

### keywords

- OBJECTIVES.md, RESULT.md, tenant-local day, computeAvailability, reports utilization, formatTenantLocalTime, benchmark:availability, npm audit --omit=dev, PR #11
- Related skill: skills/slotwise-submission-audit/SKILL.md

## Task 2: Review the challenge submission like a hiring-company evaluator, outcome partial

### rollout_summary_files

- rollout_summaries/2026-06-28T10-35-33-cnUu-slotwise_submission_audit_and_fix_plan.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T17-35-33-019f0dcc-80ca-7f52-a6c2-8fc19260e50a.jsonl, updated_at=2026-06-28T10:40:24+00:00, thread_id=019f0dcc-80ca-7f52-a6c2-8fc19260e50a, partial; reviewer-style ship/no-ship audit that found security and evidence gaps)

### keywords

- SECURITY.md, PERF.md, RESULT.md, webhook signature, x-provider-signature, 31 passed (559ms), screenshot evidence, submission.tgz, evaluator-style review
- Related skill: skills/slotwise-submission-audit/SKILL.md

## Task 3: Create a handoff plan for the next model instead of implementing immediately, outcome success

### rollout_summary_files

- rollout_summaries/2026-06-28T10-35-33-cnUu-slotwise_submission_audit_and_fix_plan.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T17-35-33-019f0dcc-80ca-7f52-a6c2-8fc19260e50a.jsonl, updated_at=2026-06-28T10:40:24+00:00, thread_id=019f0dcc-80ca-7f52-a6c2-8fc19260e50a, success; executable fix-plan handoff in plans/SUBMISSION_QUALITY_FIXES.md)

### keywords

- plans/SUBMISSION_QUALITY_FIXES.md, gpt5.4 mini, acceptance criteria, stop conditions, webhook auth, self-contained Playwright, submit packaging
- Related skill: skills/slotwise-submission-audit/SKILL.md

## User preferences

- when the user asked to "read the [OBJECTIVES.md] ... make sure we already done everything there, with the highest quality as possible" -> do not stop at a green suite; verify objective semantics against spec and inspect the whole objective surface [Task 1]
- when the user wanted "highest quality as possible" -> proactively fix latent correctness issues and leave reproducible evidence instead of only a prose claim [Task 1]
- when the user asked to judge the repo "as if you are the company i applied to" and whether "all of my work good enough" -> frame the response like an evaluator and give an explicit readiness verdict [Task 2]
- when the user said "create a plan to fix it all, then i will change to gpt5.4 mini to execute it" -> produce an ordered handoff plan with acceptance criteria and stop conditions before edits when they ask for model handoff [Task 2][Task 3]

## Reusable knowledge

- `OBJECTIVES.md` is the authoritative checklist for this challenge; `RESULT.md` can overstate completeness and should be revalidated against the actual implementation [Task 1]
- `npm test` and `npm run typecheck` can both pass while spec-level correctness still has gaps, so SlotWise audits should inspect semantic behaviors like tenant-local day derivation, availability boundary blocking, utilization range clipping, and tenant-local UI labels [Task 1]
- booking creation must derive the local day using the tenant offset, not a raw UTC date slice, and `/availability` should pass all tenant bookings into `computeAvailability` because UTC-prefiltering can miss boundary-crossing conflicts [Task 1]
- `/reports/utilization` needs validated `from`/`to` inputs plus range-aware booked-minute math clipped to the requested window; output-shape tests alone were not enough [Task 1]
- final acceptance for this repo should include unit tests, typecheck, Playwright E2E, performance evidence, and `npm audit --omit=dev`; production audit can be clean even when dev-only Vite/esbuild advisories remain [Task 1]
- `services/api/src/routes/payments.ts` originally had webhook idempotency by event id but only checked whether `x-provider-signature` existed; reviewer-style submission audits should treat header presence as a real security blocker, not a minor note [Task 2]
- `plans/SUBMISSION_QUALITY_FIXES.md` is the durable handoff artifact when implementation is deferred; it orders work as webhook auth, self-contained Playwright, stronger E2E assertions, browser-level UI validation, screenshot replacement, claims cleanup, then final verification/packaging [Task 3]

## Failures and how to do differently

- Symptom: the repo looked complete because tests were green and `RESULT.md` was polished. Cause: objective semantics and evidence quality were not fully rechecked. Fix: audit against `OBJECTIVES.md` directly and spot-check the real behaviors instead of trusting the summary doc [Task 1][Task 2]
- Symptom: first utilization and frontend time-label fixes still had hidden correctness gaps. Cause: initial checks focused on grouping/output shape rather than boundary semantics and displayed labels. Fix: verify range clipping, capacity semantics, tenant-local grouping, and tenant-local labels separately [Task 1]
- Symptom: Playwright verification failed with `connect EPERM ::1:4000` or needed a manually running API. Cause: localhost access and self-contained `webServer` setup were missing. Fix: rerun where local process access is allowed and treat non-self-contained E2E as a submission gap until Playwright starts the app itself [Task 1][Task 2]
- Symptom: benchmark scripts failed with `listen EPERM` from `tsx`. Cause: the CLI opened a local IPC pipe that sandboxed execution blocked. Fix: run `tsx`-based benchmark steps in an environment that allows the local IPC socket and record the measured output in docs [Task 1]
- Symptom: E2E evidence was weaker than the test count implied. Cause: some assertions could pass vacuously (`if (!paymentId) return`) or only proved endpoint existence/404 behavior. Fix: prefer tests that create concrete fixture state and prove the business rule being claimed [Task 2]
- Symptom: screenshot evidence and packaging claims were misleading or incomplete. Cause: the screenshot was not a real dashboard capture and `submission.tgz` was missing at review time. Fix: verify that evidence artifacts show the actual SlotWise UI and that packaging outputs exist before calling the submission ready [Task 2]

# Task Group: SlotWise repo orientation, local dev URLs, and Playwright coverage shape
scope: quickly locating the frontend, dev URLs, existing integration coverage, and the likely prerequisites for adding browser E2E in the SlotWise monorepo
applies_to: cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl; reuse_rule=safe for similar repo-orientation and test-feasibility questions in this checkout family, but treat ports, scripts, and test totals as checkout-specific

## Task 1: Confirm the repo has a frontend and give the frontend URL, outcome success

### rollout_summary_files

- rollout_summaries/2026-06-28T10-20-29-vd25-slotwise_frontend_url_and_repo_shape.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T17-20-29-019f0dbe-b220-7b21-bd22-2c6a9549c24d.jsonl, updated_at=2026-06-28T10:21:28+00:00, thread_id=019f0dbe-b220-7b21-bd22-2c6a9549c24d, success; repo shape and local dev URLs confirmed from config)

### keywords

- apps/web, localhost:5173, localhost:4000, npm run dev:web, vite.config.ts, scripts/dev.ts, workspaces, React dashboard

## Task 2: Check existing Playwright integration coverage and assess FE/browser E2E feasibility, outcome uncertain

### rollout_summary_files

- rollout_summaries/2026-06-28T11-18-04-4sqf-existing_playwright_e2e_and_fe_e2e_feasibility.md (cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/28/rollout-2026-06-28T18-18-04-019f0df3-6a39-75c0-84e0-0ffa590494fb.jsonl, updated_at=2026-06-28T11:20:23+00:00, thread_id=019f0df3-6a39-75c0-84e0-0ffa590494fb, uncertain; API-style Playwright already exists and browser E2E looked feasible but not yet implemented)

### keywords

- test:e2e, playwright.config.ts, e2e/api.spec.ts, baseURL http://localhost:4000, webServer, data-testid, hash router, NewBooking, Dashboard

## User preferences

- when the user asked, "i want to make sure, are this repo backend only or have frontend also?" and "did we already have integration test here?" -> inspect the repo directly and answer from evidence rather than speculate [Task 1][Task 2]
- when the user asked, "where are the url for the frontend?" -> give the concrete local dev URL and the supporting startup command, not just the app location [Task 1]
- when the user asked, "can we also create FE e2e test?" -> assess feasibility concretely and identify the next implementation prerequisites before editing [Task 2]

## Reusable knowledge

- The repo is a TypeScript monorepo using npm workspaces; `apps/web` is the React frontend, while `services/api`, `services/worker`, and `services/legacy-v1` are backend surfaces [Task 1]
- The README stack section is a fast place to verify repo shape, and `apps/web/vite.config.ts` plus `scripts/dev.ts` are the fastest route to the local URLs [Task 1]
- Frontend dev URL is `http://localhost:5173`, backend API dev URL is `http://localhost:4000`, and `npm run dev:web` starts both for local development with Vite proxying `/api` to the API server [Task 1]
- The existing Playwright suite is API-level coverage in `e2e/api.spec.ts`, wired as `npm run test:e2e` with `baseURL: 'http://localhost:4000'`; it is not browser UI-flow coverage [Task 2]
- FE/browser E2E looked feasible because `apps/web/src/App.tsx`, `apps/web/src/pages/NewBooking.tsx`, and `apps/web/src/pages/Dashboard.tsx` already expose stable user-facing text for booking and dashboard flows [Task 2]
- The likely next maintainability steps for browser E2E are adding a Playwright `webServer` entry and a few `data-testid` hooks so selectors are less brittle [Task 2]

## Failures and how to do differently

- Symptom: repo-shape questions could be answered incorrectly from the repo name alone. Cause: assuming backend-only or frontend presence without checking the tree. Fix: inspect `package.json`, README stack docs, and the top-level directories before answering [Task 1]
- Symptom: `rtk find` failed with `rtk: rtk find does not support compound predicates or actions`. Cause: compound search predicates were used with a tool that does not support them. Fix: use plain `find` when compound file predicates/actions are needed [Task 2]
- Symptom: FE/browser E2E readiness stayed fuzzy. Cause: the rollout stopped at feasibility analysis and current selectors looked brittle. Fix: add stable hooks (`data-testid` or equivalent) and `webServer` setup before writing or trusting browser-flow tests [Task 2]

# Task Group: /goal explanation and standalone skills.md authoring in empty workspaces
scope: explaining `/goal` and creating a direct workspace doc when the user wants a blunt practical write-up and the workspace has no existing project structure
applies_to: cwd=/Users/mraihanparlaungan/Documents/Codex/2026-06-19/tell-me-what-the-fuck-are; reuse_rule=safe for similar Codex command-explanation or standalone-doc tasks in sparse workspaces, but treat any repo-specific `/goal` implementation as checkout-specific and search for it first

## Task 1: Explain `/goal` as the thread task tracker when no repo-specific definition exists, outcome success

### rollout_summary_files

- rollout_summaries/2026-06-19T08-04-19-eaHL-goal_explanation_skills_doc.md (cwd=/Users/mraihanparlaungan/Documents/Codex/2026-06-19/tell-me-what-the-fuck-are, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/19/rollout-2026-06-19T15-04-19-019edee8-cc79-74d1-86b8-784b6033a921.jsonl, updated_at=2026-06-19T08:11:26+00:00, thread_id=019edee8-cc79-74d1-86b8-784b6033a921, success; empty workspace fallback explanation)

### keywords

- /goal, task tracker, objective, complete, blocked, rg -n "\\/goal|goal", .codex, .agents, empty workspace

## Task 2: Create `outputs/skills.md` documenting how goals should work, outcome success

### rollout_summary_files

- rollout_summaries/2026-06-19T08-04-19-eaHL-goal_explanation_skills_doc.md (cwd=/Users/mraihanparlaungan/Documents/Codex/2026-06-19/tell-me-what-the-fuck-are, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/19/rollout-2026-06-19T15-04-19-019edee8-cc79-74d1-86b8-784b6033a921.jsonl, updated_at=2026-06-19T08:11:26+00:00, thread_id=019edee8-cc79-74d1-86b8-784b6033a921, success; standalone doc created in `outputs/`)

### keywords

- skills.md, outputs/skills.md, verb + object + expected result, complete vs blocked, empty workspace, rg --files, ls -la

## User preferences

- when the user asked, "tell me what the fuck are /goal do?" -> give the explanation in plain, direct wording rather than a formal definition [Task 1]
- when the user asked for a doc "exact same shit with how goals should do" -> preserve the same blunt/practical tone in the written artifact instead of polishing it into generic product docs [Task 1][Task 2]
- when the user asked, "create skills.md for that will you?" -> create the standalone file they named instead of leaving the answer only in chat [Task 2]

## Reusable knowledge

- In an empty workspace, search for project-specific command definitions first, but if `rg -n "\/goal|goal" .codex .agents . -g '!**/.git/**'` finds nothing because `.codex` and `.agents` are absent, explain `/goal` generically as the thread/session objective tracker that starts an objective, keeps work focused, and marks it `complete` or `blocked` [Task 1]
- When `rg --files` and `ls -la` show only `outputs/` and `work/`, treat the request as a fresh deliverable and place the requested document in `outputs/` rather than inventing a larger docs structure [Task 2]
- A useful goal-writing pattern from the created doc is `verb + object + expected result`; the examples framed good goals as concrete, scoped, and finishable [Task 2]
- Preserve the definition of `blocked` from the doc: real blockers such as missing access, missing input, or dependency failure, not frustration or delay [Task 2]

## Failures and how to do differently

- Symptom: searches for `/goal` return missing-directory errors for `.codex` and `.agents`. Cause: the workspace is effectively empty, so there is no repo-specific command definition to quote. Fix: acknowledge the lack of local implementation and fall back to a generic thread-level explanation instead of pretending the repo defines it [Task 1]
- Symptom: `rg --files` returns exit code 1 with no project files. Cause: there is no existing docs structure to extend. Fix: create the requested standalone artifact in the visible writable docs area, which was `outputs/` in this rollout [Task 2]

# Task Group: OpenCode OpenAI/Codex provider setup
scope: using OpenAI/Codex as a model provider in OpenCode; reuse this for terse provider-setup questions, but re-verify current docs/model guidance because provider steps and latest-model names can change
applies_to: cwd=/Users/mraihanparlaungan/Documents/Codex/2026-06-17/i-want-to-use-u-on; reuse_rule=safe for similar OpenCode/OpenAI provider-setup questions, but treat model names and docs details as time-sensitive

## Task 1: Determine how to use OpenAI/Codex in OpenCode, answered with the built-in OpenAI provider path

### rollout_summary_files

- rollout_summaries/2026-06-17T04-40-37-c1m3-opencode_openai_provider_gpt55.md (cwd=/Users/mraihanparlaungan/Documents/Codex/2026-06-17/i-want-to-use-u-on, rollout_path=/Users/mraihanparlaungan/.codex/sessions/2026/06/17/rollout-2026-06-17T11-40-37-019ed3e1-98bc-7642-9db8-2bef46a13cfb.jsonl, updated_at=2026-06-17T04:44:06+00:00, thread_id=019ed3e1-98bc-7642-9db8-2bef46a13cfb, success; first real Phase 2 task memory)

### keywords

- opencode, openai provider, codex, gpt-5.5, responses api, openai-compatible, /connect, /models, Could not resolve host

## User preferences

- when the user asked `i want to use u on opencode, as model provider?` -> answer directly and map the shorthand to the likely OpenAI/Codex provider path instead of making them restate the whole setup [Task 1]

## Reusable knowledge

- For OpenCode, verify the provider docs first instead of guessing the config shape; in this rollout, the correct path was the built-in OpenAI provider via `/connect`, choosing `ChatGPT Plus/Pro` or `Manually enter API Key`, then `/models` [Task 1]
- Preserve the docs distinction between `@ai-sdk/openai-compatible` and `@ai-sdk/openai`: `@ai-sdk/openai-compatible` is for OpenAI-compatible `/v1/chat/completions`, while `@ai-sdk/openai` is for providers/models using `/v1/responses` [Task 1]
- When the question is about current OpenAI/Codex models, verify the latest model guide in the same run; this rollout recorded `gpt-5.5` as current and noted the Responses API recommendation for reasoning/tool-calling workflows, but that guidance is time-sensitive [Task 1]

## Failures and how to do differently

- Symptom: docs fetch fails with `Could not resolve host`. Cause: network/DNS resolution issues in the environment. Fix: retry with available network access and prefer the live docs page over assumptions or stale memory [Task 1]
- Symptom: GitHub raw/API lookups fail during docs confirmation. Cause: DNS resolution failures made GitHub a bad source in this environment. Fix: use the live docs page when available instead of blocking on GitHub fetches [Task 1]
