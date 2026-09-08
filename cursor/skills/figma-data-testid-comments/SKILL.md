---
name: figma-data-testid-comments
description: >-
  QA workflow that maps interactive Figma UI elements to data-testid names and
  posts Figma Comments (pins) via the REST API. Invents ids from naming rules
  when none exist in the codebase yet. Use when the user asks to comment
  data-testid on a Figma file, runs /figma-testid, or wants QA pins for E2E
  selectors on a design.
---

# Figma data-testid Comments (QA)

Post **Figma Comments** (comment pins), not Dev Mode annotations and not canvas labels.

## Prerequisites

1. Naming source (pick first available):
   - Project skill `data-test-id-conventions` / `data-testid-conventions` if present
   - Else use [Naming rules](#naming-rules) in this file
2. Figma URL with `fileKey` + `node-id` (page/flow/screen).
3. `FIGMA_TOKEN` env var = Personal Access Token with **File comments: Write**.
   - Create at: Figma → Settings → Security → Personal access tokens  
     or https://www.figma.com/developers/api#access-tokens
   - OAuth client id/secret is **wrong** for this flow.
   - Never commit the token. If pasted in chat, tell user to revoke after the run.

## Do / Don't

| Do | Don't |
| -- | ----- |
| Pin Comments via REST `POST /v1/files/:key/comments` | Use Dev Mode `node.annotations` |
| Tag interactive / test-relevant controls only | Tag decorative icons, logos, cell text |
| Prefer semantic ids (`button-edit-employee`) | Per-row uid/index suffixes |
| Reuse existing codebase ids when present | Invent a second name for the same control |
| Invent new ids from naming rules when none exist | Block / skip just because code has no testid yet |
| Put pin on real control; instance children → parent + `node_offset` | Assume instance child node ids always accept comments |

## Workflow

### 1. Parse URL

- `https://www.figma.com/design/:fileKey/...?node-id=116-6841` → `fileKey`, `nodeId` (`116:6841`)
- If node is a Flow Title / cover, switch to the real UI page/frame (use `use_figma` + `setCurrentPageAsync`).

### 2. Inventory UI

Use Figma MCP (`get_screenshot`, `get_metadata`, `use_figma` read-only):

- Module title, tabs
- Filters / dropdowns / date pickers / search inputs / apply-clear
- Primary actions (download, add, submit)
- List/table root, sort, pagination
- Row actions (one semantic id for the action type)
- Dialogs / map / empty / error / loading if present in frames

Skip app chrome (global sidebar) unless the ticket asks for it.

### 3. Resolve ids (existing OR invent)

For each interactive element:

1. **Search codebase** for the same feature/module:
   - `data-testid`, `dataTestId`, `titleDataTestId`
   - Nearby labels, route segments, TAB config
2. **If a stable id already exists** → reuse it exactly. Mark as `existing` in the chat summary.
3. **If none exists yet** → **invent** one using [Naming rules](#naming-rules) (and project conventions skill if present). Mark as `proposed (new)`.
4. Still **post the Figma Comment** for both existing and proposed ids. Missing code is not a reason to skip.

Chat summary table (required):

| Element | data-testid | Source |
| --- | --- | --- |
| Apply | `button-apply-filter-overspeed` | existing |
| Lihat kejadian | `button-view-overspeed-incident` | proposed (new) |

### 4. Post Comments

Message format (exact prefix):

```text
QA data-testid: <kebab-case-id>
```

Keep the pin message to the id only. Put `existing` vs `proposed (new)` in the chat summary, not in every pin (unless user asks).

Auth header: `X-FIGMA-TOKEN: $FIGMA_TOKEN`

Body:

```json
{
  "message": "QA data-testid: button-apply-filter-overspeed",
  "client_meta": {
    "node_id": "73:4677",
    "node_offset": { "x": 0, "y": 0 }
  }
}
```

**Instance children** (`I…;…` ids often 400): pin on nearest non-instance ancestor (or page frame) with `node_offset` = child `x/y` relative to that ancestor.

Prefer script (path relative to this skill):

```bash
FIGMA_TOKEN="$FIGMA_TOKEN" \
  <skill-root>/scripts/post-figma-comments.sh \
  <fileKey> < comments.tsv
```

TSV columns: `node_id`, `offset_x`, `offset_y`, `message`  
(`message` may omit the `QA data-testid:` prefix; script adds it if missing.)

Sleep ~300ms between posts. Retry failures once with parent+offset.

### 5. Verify

```bash
curl -sS -H "X-FIGMA-TOKEN: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/<fileKey>/comments" \
  | jq '[.comments[] | select(.message|test("QA data-testid"))] | length'
```

Report: posted count, failures, existing vs proposed counts, file link. Remind user to open comment panel.

## Naming rules

Use when the project has no conventions skill, or as fallback when inventing new ids.

### Core

- lower-kebab-case only
- Pattern: `[type]-[context]` (e.g. `button-apply`, `dropdown-country`, `title-route-halte`)
- Slugify visible labels when helpful (`Upload File` → related to `upload-file`)
- Prefer one semantic id per action type — no uid/index on row actions
- Put id on the interactive control, not a decorative wrapper

### Common patterns

| UI | id pattern |
| --- | --- |
| Module page title | `title-<module-slug>-module` |
| Module tab | `button-tab-<module-slug>-<tab-path>` |
| Dropdown trigger | `dropdown-<context>` |
| Dropdown search | `input-search-<context>` |
| Dropdown option | `dropdown-item-<context>-<index>` |
| Date/calendar open | `button-open-<context>-calendar` |
| Filter apply / clear | `button-apply-filter-<feature>` / `button-clear-filter-<feature>` |
| Download | `button-download-<feature>` |
| Table / list root | `table-<feature>` / `list-<feature>` |
| Sort | `button-sort-<field>` |
| Pagination | `pagination-<feature>` |
| Empty / error / loading | `empty-<feature>` / `alert-<feature>-error` / `loading-<feature>` |
| Dialog root | `dialog-<action>-<feature>` |
| Map open / close | `button-open-<feature>-map` / `button-close-<feature>-map` |

`<module-slug>` / `<feature>` should match route segments or domain terms when known; otherwise slugify the screen/feature name from Figma.

### Skip

Decorative icons, logos, static cell values, per-row text labels, global sidebar unless requested.

## Token missing

If `FIGMA_TOKEN` unset and user did not paste a token:

1. Stop posting.
2. Tell them where to create a **Personal Access Token** (not OAuth app).
3. Ask them to `export FIGMA_TOKEN='figd_...'` or paste once, then continue.

## Security

- Do not write tokens into repo files, skills, or commits.
- If user pastes `figd_…` in chat: use for the run, then tell them to **revoke** it.
