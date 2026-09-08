---
name: goal
description: Plan, build, review, publish, and finish one goal across configured repositories.
---

Delegate this run to the `goal-orchestrator` subagent. It must follow the `goal-loop` skill exactly.

Goal: everything the user typed after `/goal` is the goal description.

Resume an unfinished run when its recorded goal matches. Otherwise create a new run. Ask at most one consolidated clarification for missing requirements, then request exactly one plan approval. Persist approval by plan hash. After approval, execute without per-step confirmations until completion or a recorded hard blocker; unchanged-plan resumes never ask again.
