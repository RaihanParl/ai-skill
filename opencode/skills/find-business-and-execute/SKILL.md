---
name: find-business-and-execute
description: >
  Scan businesses from OpenStreetMap, detect WhatsApp/phone/website, generate
  personalized landing pages via opencode zen (DeepSeek V4 Flash), validate
  via opencode zen (MiMo V2.5 Free + Playwright), export xlsx.
---

# Skill: find-business-and-execute

## Prerequisites

- OpenCode Zen provider connected (`/connect` → OpenCode Zen)
- Models: `opencode/deepseek-v4-flash` (gen), `opencode/mimo-v2.5-free` (validation)

## Workflow

### Step 1 — Parse input
Extract area and business_types from user message. Default area: ID-JK, types: restaurant,cafe,fast_food. Never ask.

### Step 2 — Scan businesses
Run scanner:

```bash
python3 skills/find-business-and-execute/scripts/run.py \
  --area "$AREA" \
  --types "$TYPES" \
  --output "$OUTPUT_DIR"
```

This:
- Queries Overpass API
- Saves raw JSON to `output/raw_businesses.json`
- Parses & deduplicates to `output/businesses.json`
- Checks each business: `has_website`, `has_phone`, `has_whatsapp`

### Step 3 — Classify
Three buckets:
- **has_website** → "Complete"
- **has_whatsapp + no_website** → generate landing page via opencode zen
- **no_whatsapp + no_website** → "Phase 2"

### Step 4 — Generate landing pages (DeepSeek V4 Flash)
For each WhatsApp business, calls `opencode run -m opencode/deepseek-v4-flash` with:
- Business data (name, address, category, cuisine, phone, lat/lon) as JSON context
- Prompt to create UNIQUE, personalized landing page
  - Full-viewport hero with Unsplash image matching cuisine
  - About, menu grid, contact, WhatsApp CTA
  - Responsive, Playfair Display + Inter, smooth scroll
  - Indonesian language
- Saves HTML to `output/websites/{slug}/index.html`

Each page is generated fresh by the model — never a template. Every business gets unique design, colors, layout.

### Step 5 — Validate (MiMo V2.5 Free + Playwright)
For each generated page, calls `opencode run -m opencode/mimo-v2.5-free` with:
- Playwright checks: visual layout, links, responsive (375px + 1024px), SEO meta, resources
- Saves validation report to `output/websites/{slug}/validation.json`

### Step 6 — Export xlsx
`output/businesses.xlsx` with: business_name, address, category, has_website, has_phone, has_whatsapp, action_taken

### Step 7 — Deliver
Print summary: total, WhatsApp, pages created, validated, Phase 2.

## Output structure
```
{output_dir}/
├── raw_businesses.json
├── businesses.json
├── businesses.xlsx
└── websites/
    └── {business_name}/
        ├── business.json        # Business data used for generation
        ├── index.html           # Generated landing page
        └── validation.json      # MiMo validation report
```

## Rules
- NEVER reuse templates. Each page must be uniquely generated.
- Use Unsplash images relevant to cuisine/category.
- Overpass API (free, no key). User-Agent: find-business-execute/1.0.
- 98% OSM data in Indonesia has no contact info → most Phase 2. Expected.
- If opencode zen auth fails, tell user to run `/connect`.
