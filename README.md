# ui-demo-preview

Turn a rough software-demo idea into five clickable SVG scenes before paying the cost of screenshots, generated imagery, Playwright recording, or video rendering.

[Open the pitch landing page](https://liush2yuxjtu.github.io/ui-demo-preview-skill/) · [Try the interactive product demo](https://liush2yuxjtu.github.io/ui-demo-preview-skill/product-demo/)

<video controls muted playsinline poster="https://raw.githubusercontent.com/liush2yuxjtu/ui-demo-preview-skill/main/docs/assets/demo/poster.png" src="https://raw.githubusercontent.com/liush2yuxjtu/ui-demo-preview-skill/main/docs/assets/demo/ui-demo-preview.mp4">
  <a href="https://liush2yuxjtu.github.io/ui-demo-preview-skill/assets/demo/ui-demo-preview.mp4">Watch the 25-second UI demo</a>
</video>

[Watch or download the MP4 demo](https://liush2yuxjtu.github.io/ui-demo-preview-skill/assets/demo/ui-demo-preview.mp4)

`ui-demo-preview` creates a fast review layer between an idea and production:

- five editable, local SVG UI mockups;
- one static `storyboard.svg` contact sheet;
- one offline `preview.html` with scene switching;
- per-scene Keep, Revise, or Cut decisions and notes;
- local autosave and JSON feedback export;
- a clear approval gate before recording or image generation.

## Install

```bash
npx skills add liush2yuxjtu/ui-demo-preview-skill
```

Or install only this skill when using a multi-skill-aware client:

```bash
npx skills add liush2yuxjtu/ui-demo-preview-skill --skill ui-demo-preview
```

## Use

Example prompts:

```text
Before recording our admin walkthrough, make five clickable SVG scenes so I can revise the story and cursor targets.
```

```text
先把登录、导入、字段映射、成功结果和历史记录做成五场可点击故事板，评审通过后再录屏。
```

The skill writes this structure into the target project:

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

Open `preview.html` to switch scenes, record feedback, and export review notes. Use `storyboard.svg` for a one-page static review.

## Workflow boundary

This skill owns pre-production story review. After approval:

- recorded walkthroughs continue with a UI recording workflow such as `ui-demo`;
- persistent interactive website simulations route to a product-demo workflow;
- image generation remains optional and requires approval;
- video rendering follows the host environment's video-render policy.

It does not handle ordinary single-screen UI design, browser testing, already-approved recording, or editing an existing video.

## Validation

```bash
python3 -m py_compile skills/ui-demo-preview/scripts/build_preview.py skills/ui-demo-preview/scripts/validate_preview.py
python3 tests/smoke.py
```

The smoke test builds five SVG scenes, generates both review artifacts, runs the bundled validator, and checks offline feedback controls.

## Evaluation evidence

Functional evaluation used three paired scenarios with and without the skill:

- with skill: 15/15 checks passed;
- without skill: 7/15 checks passed;
- browser checks confirmed five-button switching and feedback autosave;
- all generated skill artifacts passed `validate_preview.py`.

Trigger evaluation used 20 Chinese boundary cases with three runs per case. The published description reached 60/60 correct classifications on the approved set.

Evaluation prompts are included under `evals/` for inspection and reuse.

## Security and privacy

Generated previews are local and offline. The SVG sanitizer rejects scripts, event handlers, `foreignObject`, embedded active media, and external references. The builder does not upload project data or call image-generation services.

## License

MIT
