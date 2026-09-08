# GitHub/GitLab access

- Use `gh` CLI for anything on GitHub (issues, PRs, repos, reads).
- Use `glab` CLI for anything on GitLab (MRs, issues, reads).
- Never webfetch GitHub/GitLab URLs when the CLI works — CLI auth covers private repos.
- Verify repo exists via `gh repo view <owner>/<repo>` before fetching issues.

# Images in PRs/issues

- Never commit screenshot binaries for PR/issue docs — upload to GitHub's CDN with `gh image` (extension `drogers0/gh-image`) and embed the returned `user-attachments` URL in the body. Full workflow: use the `/pr-image` skill.
- Private `github.com/user-attachments/assets/...` images require authenticated redirect handling. Do not rely on plain `curl -L`: capture the GitHub `302` `Location` with `Authorization: token $(gh auth token)`, strip the trailing CR, then download that short-lived S3 URL in a second request. Keep the token out of output and never commit downloaded image files.

```bash
url='https://github.com/user-attachments/assets/<asset-id>'
token=$(gh auth token)
location=$(curl -sS -D - -o /dev/null -H "Authorization: token $token" "$url" | awk 'tolower($1)=="location:" {sub(/^[^:]*: /, ""); sub(/\r$/, ""); print; exit}')
curl -sS --fail "$location" -o /tmp/github-attachment.png
```

# Stacked Pull Requests

- Use GitHub's native stacked PR workflow for dependent pull requests. Manage stacks with `gh stack`, not manual base-branch wiring alone.
- For new stacks, use `gh stack init`, `gh stack add`, `gh stack push`, and `gh stack submit` as appropriate.
- For existing dependent PRs, use `gh stack link` to register the stack on GitHub, then verify it with `gh stack view`.
- Before merging or rebasing a stack, use `gh stack sync` or `gh stack rebase` so all stack metadata and PR bases stay consistent.
- Install/update the tooling when missing with `gh extension install github/gh-stack` and `gh skill install github/gh-stack`.
