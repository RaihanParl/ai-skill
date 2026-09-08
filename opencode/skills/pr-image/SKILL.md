---
name: pr-image
description: >
  Attach screenshots/images to GitHub PRs and issues via GitHub's CDN (user-attachments),
  NOT committed binaries. Use when the user says "add screenshot to PR", "PR image",
  "attach image", "/pr-image", or when creating a PR that should include screenshots.
  Prevents the review finding "screenshot binaries bloat the repo".
---

# PR Images via GitHub CDN

Never commit screenshot binaries to a repo for PR/issue documentation. Upload to
GitHub's user-attachments CDN instead: not in git history, no repo size impact,
renders inline, private-repo-safe.

## Workflow

1. Upload image, capture markdown:

```bash
IMG=$(gh image <file.png> --repo owner/repo 2>/dev/null) || IMG=$(gh image <file.png>)
# => ![name](https://github.com/user-attachments/assets/<uuid>)
```

`--repo` optional; inferred from git remote in cwd. Requires `gh` extension
`drogers0/gh-image` (install once per machine):

```bash
gh extension install drogers0/gh-image
```

2. Embed URL in PR body:

```bash
gh pr create --title "..." --body "$(cat pr.md)

$IMG"
```

or `gh pr edit <n> --body-file pr.md` with the URL already inside `pr.md`.

3. Verify it landed (optional): `gh pr view <n> --json body -q .body | grep user-attachments`

## Rules

- Auth = browser session cookie. Works on signed-in dev machines. Breaks headless/CI —
  there say so and skip inline image rather than committing binaries.
- Multiple images: one `gh image` call accepts multiple files (`gh image a.png b.png`),
  returns one markdown line each.
- If `gh image` missing, install the extension before falling back to anything else.
- Never paste `raw.githubusercontent.com` links to committed images — broken rendering
  in private repos.
