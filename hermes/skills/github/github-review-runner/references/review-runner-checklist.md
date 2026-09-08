# Automated review runner checklist

- [ ] Read AGENTS.md and review contract.
- [ ] Direct host `gh auth status` and live `gh pr view` pass.
- [ ] Worker uses same authenticated command/context; test child path separately.
- [ ] Installation doctor passes; receipt/source identity understood.
- [ ] Usage signal is quota/limit telemetry, not token or cost totals.
- [ ] Threshold test covers exactly 30, above 30, missing, invalid.
- [ ] Codex uses `exec`, explicit model, and read-only sandbox; if full access is required for credential isolation, record `danger-full-access` and retain explicit no-write contract.
- [ ] Prompt names repository review contract and forbids generic provider review.
- [ ] Preflight reviews against PR-recorded `baseSha`; current base tip is tracked separately as `liveBaseSha` and never replaces the exact diff base.
- [ ] Same head skips only after matching GitHub review or terminal `completed` state; new head launches; active process dedupes.
- [ ] `blocked`, `failed`, and timeout states retry after child exit; they are not permanent dedup states.
- [ ] Child output classifies blocked/failed separately from completed.
- [ ] Notification test sent before real run.
- [ ] Terminal notification sent after child exit with PR/model/status.
- [ ] Final report includes exact blocker/artifact and avoids false completion claims.
