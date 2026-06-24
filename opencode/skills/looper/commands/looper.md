---
description: Design and scaffold a Looper agent loop (zero-ask mode).
argument-hint: [target-dir]
---

# /looper

Run the Looper skill. Zero questions, zero validation, zero permission.
Just execute.

Arguments from user: `$ARGUMENTS`

1. Use `skill` tool to load `looper` skill.
2. Follow SKILL.md workflow exactly.
3. If `$ARGUMENTS`, use as target dir. Else `./looper-output`.
4. Check for `DESIGN.md` in target dir. If present, read it as the design token spec for any asset generation (websites, UI, graphics). Apply colors, typography, spacing, rounded, and component styles from DESIGN.md — never inline random styles.
5. If Google Maps API key unavailable, fall back to Overpass API (free, no key). Jakarta: `ISO3166-2=ID-JK` query, Depok: bbox fallback. Always set `User-Agent` header. 98% of OSM data in Indonesia has no contact info → mark Phase 2.
6. Landing pages MUST be uniquely personalized per business: distinct hero, colors, fonts, emoji, menu, layout. Never reuse same template.
7. NEVER ask questions, never validate choices, never seek confirmation.
   If ambiguous, make reasonable default and proceed.
