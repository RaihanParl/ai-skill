# TUI observability restyle notes

Use this when a session-observability UI is structurally correct but the user rejects the aesthetic and asks for it to look like their TUI.

## Durable preference signal

For this user, observability views should feel like a terminal dashboard by default, not a polished card-heavy web app.

Reliable cues:
- dark near-black background
- monospace typography throughout
- square borders instead of rounded cards
- pane headers like `[ Sessions ]`, `[ Session Detail ]`, `[ Runtime ]`
- dense spacing
- muted terminal palette with small accent colors by source/type
- runtime/process data present but visually secondary

## Keep these from the existing dashboard shape

Do not regress on the structural wins while restyling:
- session-centric layout
- newest sessions on top
- newest events on top
- agent responses clearly visible
- tools, reasoning, user, and system events visually distinct

## Verification pattern

If Playwright package imports are awkward, use a layered check:
1. confirm the server is live
2. load the page in the browser tool
3. inspect DOM text for pane headers and newest-first cues
4. use browser vision to confirm the page actually looks TUI-like

## macOS screenshot-path pitfall

User-provided screenshots under `/var/folders/.../TemporaryItems/...` may exist but still be unreadable because of macOS permission restrictions.

When that happens:
- do not overfocus on the inaccessible file
- state the permission limitation briefly
- use the user's textual direction as the style source of truth
- restyle the live UI and verify the result directly in-browser

## Local server log interpretation

For local polling dashboards backed by Python `http.server` or `ThreadingHTTPServer`:
- repeated `GET /api/state HTTP/1.1" 200 -` lines indicate the dashboard is serving normally
- `BrokenPipeError` during `self.wfile.write(payload)` often means the client disconnected mid-response
- if a previous process was intentionally killed during restart, do not report it as an app crash
- verify the current process and live `/healthz` or `/api/state` before concluding the server is unhealthy
