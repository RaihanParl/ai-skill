---
name: long-form-research-digests
description: Build dense, evidence-backed research summaries from large link collections, repo reading lists, or article bundles; generate readable deliverables like markdown reports and PDFs.
version: 1.0.0
author: Hermes Agent
created_by: agent
license: MIT
---

# Long-form research digests

Use this when the user wants more than a quick summary from a large corpus such as:
- awesome lists
- reading lists / benchmark repos
- many linked articles or papers
- mixed corpora with papers, blog posts, repos, talks, and docs
- a report artifact, PDF, or Telegram-delivered deliverable

This skill is for class-level synthesis work, not single-URL summaries.

## Trigger phrases
- "read all of this"
- "every article"
- "make me a real summary"
- "not a short summary"
- "make a PDF"
- "send it to Telegram"
- "compact but highlighted"

## Outcome standard
Deliver a summary that is:
- compact in shape, not shallow in substance
- evidence-backed: say what was actually fetched and what was inferred from metadata
- highlighted: surface the strongest recurring ideas, disagreements, and practical takeaways
- artifact-backed: produce a real file when asked, not just chat text

## User preference captured from session
When the user asks for a summary in this class of task and rejects a short summary, default to:
- dense synthesis over breezy recap
- strong highlight sections
- direct bottom-line first
- explicit coverage statement: how many sources, what kinds, what was directly read vs lightly classified
Do not give a thin executive-summary-only answer unless the user explicitly asks for short.

## Recommended workflow
1. Fetch the primary source first.
   - For GitHub awesome lists, pull the raw README.
   - Parse section structure and outbound links.

2. Build a source inventory.
   - Deduplicate URLs.
   - Classify into article, paper, repo, video/talk/podcast, or other.
   - Keep section membership so the final report preserves the source taxonomy.

3. Use the cheapest reliable extraction per type.
   - Papers: fetch title/abstract from a structured endpoint when possible, such as arXiv API.
   - Articles: use readable-text extraction first; if thin, backfill with HTML title/meta description.
   - Repos/videos: usually title + section role is enough unless the user explicitly wants deeper review.

4. Be explicit about coverage quality.
   - Count total unique links.
   - Count how many were directly summarized from fetched text.
   - Say where fallback metadata was used.
   - Do not pretend every linked resource was deeply read if it was not.

5. Synthesize across the corpus, not item by item.
   Good structure:
   - bottom line
   - major recurring ideas
   - section-by-section synthesis
   - what is overhyped
   - what seems durable
   - practical build order / recommendations

6. Generate the requested artifact.
   - Markdown report first.
   - PDF from markdown/report text when asked.
   - Verify the file exists and can be read.

7. Deliver through the requested channel when possible.
   - If Telegram delivery is requested and direct messaging tools are unavailable, a scripted bot-token send can be acceptable if credentials already exist locally and the user asked for Telegram delivery.
   - Verify API success before claiming delivery.

## Good report shape
- Opening coverage block with real counts
- One-paragraph bottom line
- 5 to 10 strongest cross-source takeaways
- Section-by-section summary grouped by the source taxonomy
- "What matters" / "What is noisy" split
- Practical next steps or reading order

## Pitfalls
- Do not confuse "compact" with "brief". In this task class, compact means tight and information-dense.
- Do not claim you fully read every link if some sources only yielded metadata.
- Do not dump one bullet per link with no synthesis. The value is pattern extraction.
- Do not stop after markdown if the user asked for a PDF or a delivery action.
- Do not omit a coverage note; otherwise the user cannot tell how real the summary is.

## Verification
Before finishing, verify:
- source counts are real
- output file path exists
- PDF opens or yields readable extracted text
- delivery API or message send returned success

## Support files
- See `references/collection-pipeline.md` for a concrete link-heavy collection and reporting pipeline.
