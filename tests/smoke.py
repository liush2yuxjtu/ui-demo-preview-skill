#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "skills" / "ui-demo-preview"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ui-demo-preview-") as tmp:
        work = Path(tmp)
        scene_dir = work / "scenes"
        scene_dir.mkdir()
        scenes = []
        names = ["entry", "context", "action", "result", "proof"]
        for index, name in enumerate(names, 1):
            relative = f"scenes/{index:02d}-{name}.svg"
            (work / relative).write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                '<rect width="1280" height="720" fill="#0f172a"/>'
                f'<text x="80" y="140" fill="white" font-size="64">{name}</text>'
                "</svg>",
                encoding="utf-8",
            )
            scenes.append(
                {
                    "id": name,
                    "button": name.title(),
                    "title": f"{name.title()} scene",
                    "goal": "Make the scene intent visible",
                    "action": "Move the cursor to the primary target",
                    "subtitle": f"Step {index}",
                    "duration_seconds": 4,
                    "svg": relative,
                }
            )
        manifest = work / "scenes.json"
        manifest.write_text(
            json.dumps(
                {"title": "Smoke test", "source": str(work), "scenes": scenes},
                indent=2,
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_preview.py"), str(manifest), "--output-dir", str(work)],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_preview.py"),
                str(manifest),
                str(work / "preview.html"),
                str(work / "storyboard.svg"),
            ],
            check=True,
        )
        preview = (work / "preview.html").read_text(encoding="utf-8")
        assert preview.count('class="scene-button') == 5
        for marker in ("Keep", "Revise", "Cut", "localStorage", "Export feedback JSON"):
            assert marker in preview, marker
    print("PASS: ui-demo-preview smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
