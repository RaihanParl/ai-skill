# Codex/GitHub auth diagnosis

Observed pattern: host `gh pr view` succeeded with token variables unset, while Codex child preflight reported invalid auth. A stale `GH_TOKEN` can override valid macOS keychain auth. First compare host and child contexts; do not assume one proves the other.

Safe host probe:

```bash
env -u GH_TOKEN -u GITHUB_TOKEN -u GH_ENTERPRISE_TOKEN gh auth status -h github.com
env -u GH_TOKEN -u GITHUB_TOKEN -u GH_ENTERPRISE_TOKEN gh pr view N --repo OWNER/REPO --json number,state,headRefOid
```

Wrapper pattern must be reachable in worker environment and must not print secrets:

```bash
#!/bin/zsh
unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN
exec /opt/homebrew/bin/gh "$@"
```

Validate wrapper outside and inside provider sandbox. If sandbox cannot access host keychain, do not claim auth fixed. Use an approved secret injection mechanism or run authenticated preflight in a context the review contract permits. Never store a token in a wrapper, prompt, receipt, log, or skill reference.
