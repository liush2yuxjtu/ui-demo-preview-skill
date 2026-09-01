#!/usr/bin/env python3
"""Validate ui-demo-preview manifest and generated artifacts."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_SVG_BYTES = 2_000_000


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: validate_preview.py scenes.json preview.html storyboard.svg", file=sys.stderr)
        return 2
    manifest_path, html_path, storyboard_path = map(lambda p: Path(p).resolve(), sys.argv[1:])
    errors: list[str] = []
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: invalid manifest: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("ERROR: manifest root must be an object", file=sys.stderr)
        return 1
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("Manifest scenes must be an array")
        scenes = []
    check(len(scenes) == 5, "First-pass storyboard must contain exactly 5 scenes", errors)
    ids = [str(scene.get("id", "")) for scene in scenes if isinstance(scene, dict)]
    check(len(ids) == len(set(ids)), "Scene ids must be unique", errors)
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            errors.append(f"Scene {index} must be an object")
            continue
        for field in ("id", "button", "title", "goal", "action", "subtitle", "svg"):
            check(bool(str(scene.get(field, "")).strip()), f"Scene {index} missing {field}", errors)
        check(len(str(scene.get("button", ""))) <= 18, f"Scene {index} button exceeds 18 characters", errors)
        check(len(str(scene.get("subtitle", ""))) <= 60, f"Scene {index} subtitle exceeds 60 characters", errors)
        svg_path = (manifest_path.parent / str(scene.get("svg", ""))).resolve()
        check(svg_path.is_file(), f"Scene {index} SVG missing: {svg_path}", errors)
        if svg_path.is_file():
            check(svg_path.stat().st_size <= MAX_SVG_BYTES, f"Scene {index} SVG exceeds {MAX_SVG_BYTES} bytes", errors)
            raw = svg_path.read_text(encoding="utf-8")
            raw_lower = raw.lower()
            check("<!doctype" not in raw_lower and "<!entity" not in raw_lower, f"Scene {index} SVG contains DTD or entity declaration", errors)
            check("<script" not in raw_lower, f"Scene {index} SVG contains script", errors)
            check("foreignobject" not in raw_lower, f"Scene {index} SVG contains foreignObject", errors)
            check(not re.search(r"\son[a-z]+\s*=", raw, re.I), f"Scene {index} SVG contains event handler", errors)
            try:
                root = ET.fromstring(raw)
                for node in root.iter():
                    if node.tag.split("}")[-1] != "style":
                        continue
                    css = "".join(node.itertext()).strip().lower()
                    check("@import" not in css, f"Scene {index} SVG contains CSS import", errors)
                    refs = re.findall(r"url\(([^)]+)\)", css)
                    check(all(ref.strip(" '\"").startswith("#") for ref in refs), f"Scene {index} SVG contains external CSS reference", errors)
            except ET.ParseError as exc:
                errors.append(f"Scene {index} SVG invalid: {exc}")
    check(html_path.is_file() and html_path.stat().st_size > 1000, "preview.html missing or empty", errors)
    check(storyboard_path.is_file() and storyboard_path.stat().st_size > 1000, "storyboard.svg missing or empty", errors)
    if html_path.is_file():
        markup = html_path.read_text(encoding="utf-8")
        check(markup.count('class="scene-button') == 5, "preview.html must contain 5 scene buttons", errors)
        check("Export feedback JSON" in markup, "preview.html missing feedback export", errors)
        check("localStorage" in markup, "preview.html missing feedback autosave", errors)
        check(not re.search(r"(?:src|href)=[\"']https?://", markup, re.I), "preview.html contains remote request", errors)
        check("Source:" in markup and "Pi session:" in markup, "preview.html missing source/session labels", errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: 5 SVG scenes, static storyboard, offline clickable preview, feedback export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
