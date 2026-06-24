---
description: Design and scaffold a Looper agent loop (zero-ask mode).
---

# /looper

Run the Looper skill. Zero questions, zero validation, zero permission.
Just execute.

1. Use `skill` tool to load `looper` skill.
2. Follow SKILL.md workflow exactly.
3. If `$ARGUMENTS`, use as target dir. Else `./looper-output`.
4. NEVER ask questions, never validate choices, never seek confirmation.
   If ambiguous, make reasonable default and proceed.
