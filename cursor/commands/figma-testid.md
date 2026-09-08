---
name: figma-testid
description: QA — map Figma UI to data-testid names and pin Figma Comments on each element.
---

Act as QA. Follow the skill `figma-data-testid-comments` exactly
(`SKILL.md` next to this command’s skill folder, or
`~/.cursor/skills/figma-data-testid-comments/SKILL.md` /
`cursor/skills/figma-data-testid-comments/SKILL.md` in ai-skill).

If a project `data-test-id-conventions` / `data-testid-conventions` skill exists, apply it for naming. Otherwise use the naming rules inside `figma-data-testid-comments`.

Input: everything the user typed after `/figma-testid` (usually a Figma URL; optional module/page hint).

Steps:
1. Parse `fileKey` + `node-id` from the URL. If the node is only a Flow Title/cover, find the real UI frames on that page.
2. Inventory interactive / test-relevant elements (title, tabs, filters, actions, list/table, dialogs, empty/error/loading). Skip decorative chrome unless asked.
3. For each element: reuse an existing codebase `data-testid` if found; **if none exists yet, invent one** from naming rules. Still pin the comment. Summarize `existing` vs `proposed (new)`.
4. Require `FIGMA_TOKEN` (Personal Access Token with file comments write). If missing, stop and tell the user where to create one — do not use OAuth client id/secret.
5. Post **Figma Comments** (not Dev Mode annotations) with message `QA data-testid: <id>`. Prefer the skill’s `scripts/post-figma-comments.sh`.
6. For instance-child nodes that 400, retry via parent node + `node_offset`.
7. Verify posted count via comments GET. Report ok/fail + existing/proposed counts + file link.
8. If the user pasted a `figd_` token in chat, remind them to revoke it after the run.

Do not implement UI code unless the user explicitly asks.
