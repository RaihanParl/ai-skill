---
description: Plan, build, review, publish, and finish one goal across configured repositories.
agent: goal-orchestrator
model: {{PLAN_MODEL}}
---
Use `goal-loop` skill.

Goal: $ARGUMENTS

Derive a canonical goal key from the verified ticket identity or normalized free-form goal. Resume only the unfinished run with that exact key; otherwise create a new run without blocking unrelated runs. Ask at most one consolidated clarification for missing requirements, then request exactly one plan approval. Persist the user's actual approval message, timestamp, and plan hash; never synthesize or auto-approve them. After approval, review integrated changes before full repository tests and QA, then execute without per-step confirmations until completion or a recorded hard blocker; unchanged-plan resumes never ask again.
