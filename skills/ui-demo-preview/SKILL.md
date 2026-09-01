---
name: ui-demo-preview
description: Use this skill whenever the user is shaping an audience-facing software product demo from an idea or revising its story and interactions before production. Cover both recorded walkthroughs and persistent interactive website demos; first clarify which deliverable is intended, routing long-running React simulations to product-demo. For video-bound demos, create a cheap five-scene clickable SVG storyboard for review before screenshots, Playwright recording, image generation, or rendering. Do not use for ordinary UI design prototypes, non-software storyboards, browser testing, skill evaluation, already-approved recording, or video editing.
compatibility: Python 3 standard library; browser only for reviewing generated standalone HTML
license: MIT
---

# UI demo preview

Turn an idea into something clickable before spending time on images or video. The first deliverable is always cheap to change: five SVG mockups, one static storyboard, and one interactive scene preview.

## Core rule

Do not begin image generation, browser recording, video rendering, or final asset work until the user has reviewed the SVG storyboard stage.

The SVG stage is not decoration. It settles scene order, framing, copy, cursor target, interaction, and pacing while changes still cost seconds.

If image generation may help later, explain which approved scene needs it and why. Image generation requires user approval because it consumes quota. UI-only scenes usually need no generated images.

## Default output

Create a folder in the target project, normally `ui-demo-preview/`:

```text
ui-demo-preview/
├── scenes.json
├── scenes/
│   ├── 01-entry.svg
│   ├── 02-context.svg
│   ├── 03-action.svg
│   ├── 04-result.svg
│   └── 05-proof.svg
├── storyboard.svg
└── preview.html
```

Use exactly five scenes for the first pass unless the user explicitly gives another count. Five buttons make comparison fast and force a clear story:

1. Entry: starting state and viewer orientation.
2. Context: problem, input, or feature choice.
3. Action: main interaction and cursor target.
4. Result: visible state change or generated output.
5. Proof: saved state, confirmation, metric, or next step.

A scene can later split during recording. Do not increase first-pass scope to solve uncertainty.

## Workflow

### 1. Capture intent from existing evidence

Use the user's prompt, URL, screenshots, repo, brief, or current app. Infer missing low-risk details from project conventions. Do not make the user design the file structure.

Write one sentence that states the assumed audience, outcome, and five-scene arc.

### 2. Inspect real UI when it exists

If a runnable app exists, follow `ui-demo` discovery guidance to inspect visible controls and exact labels. Keep this phase read-only. Do not record.

If only an idea exists, make intentionally schematic SVGs. Label uncertain controls as assumptions rather than inventing polished product behavior.

### 3. Write `scenes.json`

Use this shape:

```json
{
  "title": "Demo title",
  "source": "/absolute/path/to/project",
  "scenes": [
    {
      "id": "entry",
      "button": "Start",
      "title": "Open dashboard",
      "goal": "Orient viewer",
      "action": "Cursor enters and pauses over primary navigation",
      "subtitle": "Open the workspace",
      "duration_seconds": 4,
      "svg": "scenes/01-entry.svg"
    }
  ]
}
```

Keep button labels under 18 characters and subtitles under 60 characters. Give each scene one main action and one visible outcome.

### 4. Draw five SVG mockups

Use plain SVG. No raster image generation, screenshots, remote fonts, external assets, JavaScript, `foreignObject`, animation, or network references.

Default canvas: `1280x720`, matching `ui-demo`. Show:

- app chrome and important regions;
- readable placeholder copy;
- cursor position or interaction target;
- changed state for result scenes;
- one small annotation when an assumption matters.

Favor boxes, labels, icons made from SVG paths, and simple color tokens. Match known product colors when evidence exists. Keep structure editable by hand.

### 5. Build artifacts

Resolve `<skill-directory>` from this loaded `SKILL.md` location; do not assume a username or install root. From the target project directory, run:

```bash
python3 "<skill-directory>/scripts/build_preview.py" \
  ui-demo-preview/scenes.json \
  --output-dir ui-demo-preview
```

This produces:

- `storyboard.svg`: static five-panel contact sheet for instant review;
- `preview.html`: standalone scene switcher with five buttons, Keep/Revise/Cut choices, notes, keyboard navigation, local autosave, and JSON feedback export.

The builder rejects active SVG content and external references.

### 6. Validate before presenting

Run:

```bash
python3 "<skill-directory>/scripts/validate_preview.py" \
  ui-demo-preview/scenes.json \
  ui-demo-preview/preview.html \
  ui-demo-preview/storyboard.svg
```

Fix every reported error. Then report both artifacts as explicit Markdown links targeting absolute `file:///` URLs, plus plain absolute paths as copyable fallback. Do not output only raw paths: Pi assistant-body paths are not reliably clickable in Ghostty. Percent-encode spaces and other URL-sensitive characters in link targets.

```markdown
[打开交互预览](file:///absolute/path/to/preview.html)

路径：`/absolute/path/to/preview.html`
```

On macOS Ghostty, use `Command+点击`; if a TUI captures mouse input, use `Shift+Command+点击`. Do not activate a browser or steal foreground focus. If the user explicitly asks Pi to display local HTML in Herdr, use `ghostty-browser`; otherwise provide the explicit file link for review.

### 7. Apply scene feedback

Treat feedback as storyboard edits, not video edits:

- Reorder: change scene order in `scenes.json`.
- Copy: update labels and subtitles.
- Interaction: move cursor target and revise action.
- Framing: change SVG hierarchy or viewport.
- Cut: remove only after explicit feedback, then rebuild the five-scene arc by merging or replacing a scene.

Rebuild `storyboard.svg` and `preview.html` after every revision. Preserve exported feedback JSON beside the preview when available.

### 8. Gate expensive work

Proceed only when the user approves the storyboard or clearly asks to record the approved version.

Then:

1. Use `ui-demo` for Discover, Rehearse, Record.
2. Translate each approved scene into selectors, cursor motion, subtitle, and pause timing.
3. Keep button labels and scene order as recording chapter markers.
4. If the final artifact adds five seek buttons, map each button to the recorded scene start time with `video.currentTime`.
5. Route every draft and final video render or encoding command through `video-render-macmini`. Never render video on the MacBook.

## Acceptance checklist

- [ ] First pass has five scene buttons.
- [ ] Each button switches scene without video playback.
- [ ] Every scene uses a local static SVG mockup.
- [ ] `storyboard.svg` exists and shows all scenes at once.
- [ ] `preview.html` works offline and contains no CDN or remote request.
- [ ] Reviewers can Keep, Revise, or Cut each scene and add notes.
- [ ] Feedback autosaves and can export as JSON.
- [ ] No image generation or recording happened before storyboard review.
- [ ] Approved flow can map directly to `ui-demo` steps.
- [ ] Any video output runs on `macmini`.

## Boundary

Use this skill for pre-recording story and interaction design. Use `ui-demo` after approval for Playwright discovery, rehearsal, cursor movement, subtitles, and recording. Use `product-demo` instead when the requested deliverable is a persistent interactive product simulation rather than a video plan.
