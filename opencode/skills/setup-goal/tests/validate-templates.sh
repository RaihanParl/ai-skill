#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
loop="$root/templates/goal-loop.md"
setup_agent="$root/../../agent/setup-goal.md"
if [ ! -f "$setup_agent" ]; then
  setup_agent="$root/../../agents/setup-goal.md"
fi

head -n 1 "$root/SKILL.md" | grep -qx -- '---'
sed -n '2p' "$root/SKILL.md" | grep -qx -- 'name: setup-goal'
grep -q '\.goal/locks/<run-id>' "$loop"
grep -q '\.goal/claims/<sha256-goal-key>' "$loop"
grep -q 'canonical goal key' "$loop"
grep -q 'Never write `auto-approved`' "$loop"
grep -q 'is not `workspace_root`' "$loop"
grep -q 'resource-locks' "$loop"
if grep -q 'lock at `.goal/lock`' "$loop"; then
  echo 'global goal lock still present' >&2
  exit 1
fi

grep -q 'never synthesize or auto-approve' "$root/templates/goal-command.md"
grep -q 'Never rewrite root state' "$root/templates/goal-orchestrator.md"
grep -q 'exact subagent type `goal-planner`' "$loop"
if grep -R -q 'general-purpose' "$root/templates"; then
  echo 'unsupported delegation alias present in generated templates' >&2
  exit 1
fi

for planner in "$root/templates/goal-planner.md" "$root/templates/cursor-agent-planner.md" "$root/templates/codex-agent-planner.toml"; do
  grep -q 'never plan from the title or URL alone' "$planner"
done

for builder in "$root"/templates/*builder*; do
  grep -q 'worktree_root/<run-id>/' "$builder"
  grep -q 'workspace_root' "$builder"
done

grep -q '\.agents/skills/goal-loop/SKILL.md' "$setup_agent"
grep -q 'Root state is immutable setup configuration' "$setup_agent"
grep -q 'opencode debug config' "$setup_agent"
if grep -q '"status": "ready"' "$setup_agent"; then
  echo 'legacy mutable root state template present' >&2
  exit 1
fi
