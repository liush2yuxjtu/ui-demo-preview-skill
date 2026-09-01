#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DEMO = DOCS / "product-demo" / "index.html"
LANDING = DOCS / "index.html"
ASSETS = DOCS / "assets" / "demo"


def main() -> int:
    landing = LANDING.read_text(encoding="utf-8")
    demo = DEMO.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for markup, name in ((landing, "landing"), (demo, "product demo")):
        assert "Source project:" in markup and "Pi session ID:" in markup, name
        assert not re.search(r'<(?:script|img|source|link)[^>]+(?:src|href)=["\']https?://', markup, re.I), name

    for marker in ("story-select", "build-scenes", "scene-tabs", "data-value=\"keep\"", "data-value=\"revise\"", "data-value=\"cut\"", "export-feedback", "reset-layout"):
        assert marker in demo, marker
    assert "STORIES=" in demo and "Inventory operations" in demo

    required = [
        "ui-demo-preview.mp4",
        "ui-demo-preview.webm",
        "poster.png",
        "contact-sheet.png",
        "interaction-strip.png",
        "markers.json",
        "probe.json",
        "rehearsal.log",
    ]
    for filename in required:
        path = ASSETS / filename
        assert path.is_file() and path.stat().st_size > 0, filename

    markers = json.loads((ASSETS / "markers.json").read_text(encoding="utf-8"))["chapters"]
    assert list(markers) == ["orient", "build", "compare", "revise", "approve"]
    assert all(0 <= markers[key] < markers[next_key] for key, next_key in zip(markers, list(markers)[1:]))

    probe = json.loads((ASSETS / "probe.json").read_text(encoding="utf-8"))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    assert video["codec_name"] == "h264" and video["pix_fmt"] == "yuv420p"
    assert (int(video["width"]), int(video["height"])) == (1280, 720)
    assert float(probe["format"]["duration"]) > 20

    assert "<video" in readme and "ui-demo-preview.mp4" in readme
    assert "ui-demo-preview-skill/product-demo/" in readme
    print("PASS: landing, product demo, video assets, chapters, README embed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
