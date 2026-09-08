# Collection pipeline for link-heavy research digests

Use this when the source is a GitHub awesome list, benchmark index, or large README with many outbound links.

## Proven pipeline
1. Pull raw README.
2. Extract markdown links and preserve heading/section membership.
3. Deduplicate exact URLs.
4. Classify each URL:
   - paper: arXiv or paper PDF pages
   - article: blogs/docs/newsletters/web pages
   - repo: GitHub repositories
   - video: YouTube and similar talk links
5. Fetch structured text by source type:
   - arXiv: API title + abstract
   - article: readable-text extractor first
   - fallback: HTML title + meta description
6. Build a local JSON inventory with:
   - section
   - label
   - url
   - kind
   - title
   - summary if fetched
7. Synthesize at section level first, then cross-section themes.
8. Write markdown report.
9. Render PDF from the markdown/report text.
10. Verify file and delivery success.

## Why this works
- Keeps honest separation between deeply fetched text and lightweight metadata.
- Preserves repo taxonomy, which is often part of the curator's argument.
- Produces a reusable local corpus for later follow-up requests.

## Delivery note
If the user asks for Telegram delivery and credentials already exist locally, scripted `sendMessage` + `sendDocument` via Telegram Bot API is acceptable when no higher-level messaging tool is available. Only claim success after `ok: true` from the API response.

## Output style note from session
For this task class, when the user says they do not want a short summary, prefer:
- bottom-line first
- dense but readable sections
- highlighted recurring ideas
- practical takeaways
- a coverage block with counts
