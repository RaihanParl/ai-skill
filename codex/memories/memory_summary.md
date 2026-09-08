v1

## User Profile
The user works with Codex in terse, compressed language and expects the agent to translate shorthand into the likely technical path without making them restate the request. They prefer plain, direct wording, and if they ask for a named artifact they want that file created, not just an answer in chat. In review-heavy coding workflows, they want evaluator-style judgment: say clearly whether something is ready, leave terse actionable comments, then fix and re-check when they ask. They also reuse SlotWise challenge workflows where `OBJECTIVES.md` is the anchor for quality audits, submission readiness, and PR follow-up. The user values visible execution tracking while work is in progress and expects code tasks to be tested as they go, including Playwright when relevant, then pushed via branch/MR flow when the environment permits [ad-hoc note].

## User preferences
- When the user asks a terse setup question like `i want to use u on opencode, as model provider?`, answer directly and map the shorthand to the likely intended path instead of making them restate it.
- When the user asks command-meaning questions like `"tell me what the fuck are /goal do?"`, use plain, direct wording rather than a formal definition.
- When the user asks for a doc `"exact same shit"` or names a file like `skills.md`, preserve the same blunt/practical tone and create the standalone file they asked for instead of leaving the answer only in chat.
- For reviewer-style coding requests, be decisive: if they ask whether work is good enough to submit, answer like an evaluator and say submit/not-submit clearly.
- For PR review requests, keep comments terse, line-specific, and limited to actionable findings.
- When the user says `"fix it, check again please"` or `"check the comment and fix it"`, convert findings into code changes and re-verify instead of stopping at analysis.
- When the user asks for "highest quality as possible," do not stop at a green suite; verify semantics against the spec and leave reproducible evidence.
- If the user asks for a plan before handing work to another model, provide an ordered handoff with acceptance criteria and stop conditions.
- Keep track of what you did, including plan/doing steps, and refer to the active plan while working [ad-hoc note].
- For code tasks, test after each task, use Playwright if needed, then push to a new branch and turn it into an MR using `gh` when the environment allows it [ad-hoc note].
- For current product/model questions, verify live docs in the same run rather than relying on remembered model names or provider steps.

## General Tips
- Read `phase2_workspace_diff.md` first; this repo uses incremental consolidation, and the diff is the authoritative ingestion/cleanup queue.
- Read every `extensions/*/instructions.md` before consolidating; this repo currently has `extensions/ad_hoc/instructions.md`, and anything derived from those notes should keep the `[ad-hoc note]` tag here.
- For SlotWise submission-readiness runs, start with `OBJECTIVES.md`, `RESULT.md`, `SECURITY.md`, `PERF.md`, `NOTES.md`, Playwright configs, and the touched test files before trusting repo claims.
- Use `skills/slotwise-submission-audit/SKILL.md` for recurring SlotWise "is this ready to submit?", company-style audit, or fix-plan handoff work.
- In git repos, switch to `git grep` if `rg` hits regex parse errors or if you need symbol tracing from a PR diff.
- Time-sensitive tests should use controlled-clock or relative-date helpers, not hard-coded future dates.
- Browser keyboard coverage should use real `Tab` and `Enter`/`Space` interaction rather than `.focus()`.
- If `rtk find` complains about compound predicates/actions, switch to plain `find`.
- If docs lookups fail with `Could not resolve host`, prefer retrying the live docs page rather than assuming GitHub raw/API fetches will work.
- In sparse workspaces where `rg --files` finds nothing useful, inspect `outputs/` and `work/` before inventing a larger structure.

## What's in Memory

### /Users/mraihanparlaungan/personal/slotwise-raihanparl

#### 2026-06-28

- SlotWise PR review, fix follow-up, and worktree-based submission flow: PR #17, worktrees/fix-submit-quality, evaluateCancellation, refundedCents, glowBookingStart, reuseExistingServer
  - desc: Search this first for SlotWise review/fix runs involving inline PR comments, isolated worktrees, or re-verification after reviewer findings; applies to `cwd=/Users/mraihanparlaungan/personal/slotwise-raihanparl` and its `worktrees/fix-submit-quality` checkout.
  - learnings: Strong review targets here were time-dependent tests, refund-accounting regressions, and fake keyboard coverage; use `c.del`, preserve cumulative refunds, prefer `glowBookingStart(...)`, and report git/worktree blockers explicitly if final push fails.

- SlotWise objective audit and submission-quality verification: OBJECTIVES.md, webhook signature, benchmark:availability, plans/SUBMISSION_QUALITY_FIXES.md, npm audit --omit=dev, PR #11
  - desc: Search this for highest-quality objective audits, company-style submit/not-submit verdicts, or fix-plan handoffs in SlotWise; pairs well with `skills/slotwise-submission-audit/SKILL.md`.
  - learnings: Green tests and polished docs were not enough; the decisive checks were semantic objective validation, real webhook auth review, self-contained Playwright expectations, and evidence quality for screenshots/packaging.

- SlotWise repo orientation, local dev URLs, and Playwright coverage shape: apps/web, localhost:5173, localhost:4000, npm run dev:web, test:e2e, webServer, data-testid
  - desc: Search this for quick repo-shape answers, frontend/API local URLs, or "do we already have integration tests / can we add FE E2E?" routing in SlotWise.
  - learnings: `apps/web` is the React frontend at `http://localhost:5173`, API is `http://localhost:4000`, existing Playwright is API-level, and browser E2E likely wants `webServer` plus stable test hooks.

### /Users/mraihanparlaungan/Documents/Codex/2026-06-19/tell-me-what-the-fuck-are

#### 2026-06-19

- /goal explanation and standalone skills.md authoring: /goal, outputs/skills.md, task tracker, blocked, complete, empty workspace
  - desc: Search this for terse `/goal` explanation requests or for writing a standalone explainer in a sparse workspace with no repo-specific command definition.
  - learnings: If `.codex` and `.agents` are absent, explain `/goal` generically as the thread objective tracker; when only `outputs/` and `work/` exist, place the requested doc in `outputs/` and keep the wording blunt/practical.

### /Users/mraihanparlaungan/Documents/Codex/2026-06-17/i-want-to-use-u-on

#### 2026-06-17

- OpenCode OpenAI/Codex provider setup: opencode, openai provider, /connect, /models, @ai-sdk/openai, @ai-sdk/openai-compatible, gpt-5.5
  - desc: Search this for questions about using OpenAI/Codex inside OpenCode; reuse only with fresh docs verification because provider/model guidance is time-sensitive.
  - learnings: The validated path here was the built-in OpenAI provider via `/connect` and `/models`; keep the `/v1/chat/completions` vs `/v1/responses` distinction and re-check latest-model guidance in the same run.

### Older Memory Topics

No additional older high-signal topics currently.
