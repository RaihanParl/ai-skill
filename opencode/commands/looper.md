---
description: Design and scaffold a review-gated agent loop with best-practice coaching.
argument-hint: "[target-dir]"
---

# /looper

Run the Looper skill to design a review-gated agent loop.

Arguments from user: `$ARGUMENTS`

1. Use `skill` tool to load `looper` skill.
2. Follow SKILL.md workflow: interview → critique → validate → scaffold.
3. If `$ARGUMENTS`, use as target dir. Else `./looper-output`.
4. After loop design, if target dir contains `DESIGN.md`, read it as design token spec for any asset generation (websites, UI, graphics). Apply colors, typography, spacing, rounded, component styles — never inline random styles.
5. If Google Maps API key unavailable, fall back to Overpass API (free, no key). Jakarta: `ISO3166-2=ID-JK` query, Depok: bbox fallback. Always set `User-Agent` header. 98% of OSM data in Indonesia has no contact info → mark Phase 2.
6. Landing pages MUST be uniquely personalized per business: distinct hero, colors, fonts, emoji, menu, layout. Never reuse same template.
7. After durable findings, write back to user memory so future OpenCode runs can improve from prior loops.
