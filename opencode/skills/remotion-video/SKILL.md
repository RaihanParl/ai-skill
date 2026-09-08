---
name: remotion-video
description: >
  Use when the user wants to create, edit, animate, render, or debug a video
  with Remotion or asks for promo videos, captions, motion graphics, vertical
  ads, timeline-based animation, or mp4 rendering from React code. Covers
  composition setup, scene timing, media layout, audio sync, rendering, and
  final review of the exported video.
---

# Remotion Video

Use this skill for Remotion-based video work. Prefer small, reviewable
compositions over giant one-file experiments.

## Goals

- Create or edit Remotion compositions quickly.
- Keep animation readable and intentional.
- Avoid broken aspect ratios, cropped media, and unreviewed renders.
- Always render and inspect output before claiming the video is done.

## Workflow

1. Inspect the existing project first.
2. Find the Remotion entrypoint, compositions, public assets, render scripts, and output paths.
3. Check media dimensions before laying them out.
4. Build or edit the smallest composition that satisfies the request.
5. Render a real output video.
6. Review the exported file, not just the source code.
7. If visuals are wrong, fix and render again before reporting success.

## Project Checks

Before editing, check these:

- `package.json` scripts for `remotion studio` / `remotion render`
- Remotion entry files such as `src/remotion/index.ts`, `src/remotion/Root.tsx`
- public asset paths used by `staticFile()`
- composition dimensions, fps, and duration
- source media dimensions with `ffprobe` or `sips`

## Layout Rules

- Match the composition aspect ratio to the target output first.
- For screenshots and stills, never assume the ratio. Measure it.
- If the user wants the whole screenshot visible, do not use crop-style fitting.
- Prefer raw screenshots with radius and shadow over fake device frames unless the user explicitly wants a device mockup.
- If a frame or container adds padding, account for that in the sizing math.
- Keep typography large, high-contrast, and sparse for ad-style videos.

## Animation Rules

- Default to clean motion: fade, slide, scale, masked reveal.
- Avoid floaty idle motion unless explicitly requested.
- One strong movement per element is usually enough.
- Sync scene changes to voiceover phrases when possible.
- Prefer fewer scenes with better pacing over many scenes with weak transitions.

## Audio Rules

- Reuse existing voiceover/audio when provided.
- Keep music below voiceover.
- If timing feels off, adjust scene boundaries to the audio instead of forcing the audio to fit weak timing.
- Verify the final duration against the actual exported video.

## Render Rules

Always do all of these before saying the video is good:

- render the final video
- check width, height, fps, and duration with `ffprobe`
- extract review frames from key timestamps
- inspect for cropping, aspect-ratio mistakes, dead space, overlap, and bad text breaks
- if anything looks wrong, fix and re-render

## Review Checklist

- [ ] composition ratio matches requested output
- [ ] screenshots or videos are not unintentionally cropped
- [ ] text is readable on mobile-sized output
- [ ] motion looks intentional, not chaotic
- [ ] audio levels are balanced
- [ ] final video was rendered successfully
- [ ] exported file was reviewed after render

## Useful Commands

Measure media:

```bash
ffprobe -v error -show_entries format=duration:stream=width,height,avg_frame_rate -of default=noprint_wrappers=1 path/to/file.mp4
sips -g pixelWidth -g pixelHeight path/to/image.png
```

Render still review frames:

```bash
ffmpeg -y -ss 3.0 -i output.mp4 -frames:v 1 -update 1 review-frame.png
```

Common Remotion commands:

```bash
npm run remotion:studio
npm run remotion:render
```

## Implementation Pattern

Prefer this structure:

- `src/remotion/index.ts` for `registerRoot()`
- `src/remotion/Root.tsx` for compositions
- `src/remotion/...` for scene components
- `public/...` for static assets

Keep scene data declarative when possible:

```ts
const scenes = [
  {start: 0, duration: 60, title: '...'},
]
```

## When Docs Matter

If Remotion API details are uncertain or stale, fetch current docs before guessing:

- `https://www.remotion.dev/docs/`
- `https://www.remotion.dev/docs/ai/skills`

## Output Expectations

When finishing:

- give the final output path
- mention verified width, height, fps, and duration
- mention any remaining visual compromises
- remind the user to restart opencode if this skill was just added
