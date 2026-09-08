---
name: agent-session-observability
description: Build or improve local dashboards and observability views for Hermes, OpenCode, Cursor, and similar agent runtimes, with session-centric UX instead of process-centric inspection.
---

# Agent Session Observability

Use this when the user wants a web UI, dashboard, mirror, monitor, or readable activity view for one or more local agent systems such as Hermes, OpenCode, and Cursor.

This skill is about making agent activity legible. The default goal is not "show that processes exist". The default goal is "show what happened in each session".

## Triggers

- User says they cannot see what happened when driving agents from Telegram or another remote surface.
- User asks for a webserver or dashboard that mirrors running agents.
- User complains that the current result looks like a TUI or process inspector.
- User wants to see agent responses, tool actions, reasoning traces, and message history per session.
- User asks for a more human-readable view across multiple agent systems.

## Outcome

Produce a working local dashboard backed by real data from the agents' persisted state, not a mocked UI.

Minimum outcome:
1. Sessions from each requested agent source are discoverable.
2. Each session has a readable detail view.
3. Agent responses are visible, not just user prompts.
4. Tool calls and reasoning/thought traces are separated visually from normal replies.
5. Newest sessions appear at the top.
6. Inside a session, newest events appear at the top unless the user explicitly asks for chronological order.
7. Browser behavior is validated with Playwright or an equivalent real-browser path before claiming success.

## Preferred UX for this user

When building this class of dashboard for this user:

- Make it session-centric, not process-centric.
- Show what happened in every session, not only whether a process is running.
- Show agent responses clearly as first-class blocks.
- Keep runtime/process information secondary in a side panel or collapsed section.
- Put the newest sessions on top.
- Put the newest events within a session on top.
- If the latest raw event is a tool call, still make agent responses easy to spot visually.
- Use a TUI-like visual language by default for observability views: dark terminal palette, monospace typography, square borders, pane layout, dense spacing, and terminal-style headers instead of polished card UI.
- If the user says the UI should look like "our TUI", treat that as a direct style correction and restyle the surface toward terminal panes rather than defending the previous web-app aesthetic.

## Recommended workflow

1. Inspect real local persistence first.
   - Hermes: inspect the session/message store.
   - OpenCode: inspect the session/message/part store.
   - Cursor: inspect transcript JSONL and terminal snapshots.
   - Do not guess schemas.

2. Normalize all sources into one unified session model.
   Suggested fields:
   - source
   - session id
   - title
   - updated_at
   - subtitle/path/cwd
   - preview
   - assistant_count
   - timeline[]

3. Normalize each timeline event into a human-readable event shape.
   Suggested fields:
   - ts
   - role
   - kind
   - title
   - preview
   - body
   - raw
   - accent/class

4. Extract readable text from nested payloads.
   Do not stop at raw JSON if the payload contains actual assistant text, tool input, tool output, or reasoning text.

5. Build the UI around three layers:
   - session list
   - selected session detail
   - secondary runtime/process side panel

6. In the detail view, visually separate:
   - Agent response
   - User message
   - Agent thought / reasoning
   - Tool call / tool result
   - System event
   - Terminal output

7. Add summary chips for fast scanning.
   Good defaults:
   - total events
   - agent responses
   - thoughts
   - tool actions

8. Sort newest-first in both places.
   - session list sorted by updated_at descending
   - timeline sorted by ts descending

9. Validate in a real browser.
   Minimum checks:
   - page loads
   - session list renders
   - newest session is at top
   - selected session detail renders
   - at least one visible agent response card is present when the source data contains one
   - any UX copy describing newest-first behavior is actually visible

10. Report the live URL, process handle, changed files, and what browser validation actually proved.

## Pitfalls

- Do not build a process list and call it observability.
- Do not show only user messages and hide agent responses.
- Do not dump raw JSON everywhere when a readable response can be extracted.
- Do not leave ordering ambiguous. Default to newest-first for this user.
- Do not claim the UI is verified until a browser check has run.
- If a direct Playwright import path fails in the environment, fall back to Playwright CLI plus browser/DOM verification. Save the lesson as a verification pattern, not as a permanent claim that Playwright is broken.
- If the user gives a screenshot path under macOS TemporaryItems and it is permission-blocked, do not stall on the reference image. Explain the limitation briefly, restyle toward the stated direction, and verify the live result visually in-browser.
- Do not misread intentional restarts plus `BrokenPipeError` as proof that the dashboard crashed. When logs show repeated `GET /api/state 200` followed by a traceback during response write, treat client disconnect on a large payload as the first hypothesis and verify current health before claiming failure.

## Verification

- Validate the backing API returns unified session data.
- Validate the page in a browser.
- Prefer Playwright. If the package import path is awkward, use Playwright CLI for screenshot or page actions and cross-check with browser DOM inspection.
- Confirm the page visibly contains:
  - newest-first cues
  - session list items
  - session detail
  - agent response labels or readable assistant text

## References

- See `references/session-centric-dashboard-ui.md` for concrete UX requirements and verification notes from a real multi-agent dashboard implementation.
- See `references/tui-observability-restyle-notes.md` for TUI-oriented styling cues, screenshot-path limitations on macOS TemporaryItems, and how to interpret noisy `BrokenPipeError` traces during local dashboard polling.
