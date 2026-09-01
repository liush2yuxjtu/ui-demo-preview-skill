#!/usr/bin/env python3
"""Build offline SVG storyboard and clickable scene preview from scenes.json."""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ET.register_namespace("", "http://www.w3.org/2000/svg")

BANNED_TAGS = {"script", "foreignObject", "iframe", "object", "embed", "audio", "video"}
URL_ATTRS = {"href", "{http://www.w3.org/1999/xlink}href", "src"}
MAX_SVG_BYTES = 2_000_000


def fail(message: str) -> None:
    raise ValueError(message)


def clean_svg(path: Path) -> str:
    if not path.is_file():
        fail(f"Missing SVG: {path}")
    if path.stat().st_size > MAX_SVG_BYTES:
        fail(f"SVG exceeds {MAX_SVG_BYTES} bytes: {path}")
    raw = path.read_text(encoding="utf-8")
    raw_lower = raw.lower()
    if "<!doctype" in raw_lower or "<!entity" in raw_lower:
        fail(f"DTD and entity declarations are not allowed: {path}")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        fail(f"Invalid SVG {path}: {exc}")
    if root.tag.split("}")[-1] != "svg":
        fail(f"Root element must be svg: {path}")
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag in BANNED_TAGS:
            fail(f"Active SVG tag <{tag}> is not allowed: {path}")
        if tag == "style":
            css = "".join(node.itertext()).strip().lower()
            if "@import" in css:
                fail(f"CSS imports are not allowed: {path}")
            refs = re.findall(r"url\(([^)]+)\)", css)
            if any(not ref.strip(" '\"").startswith("#") for ref in refs):
                fail(f"External CSS reference is not allowed: {path}")
        for key, value in node.attrib.items():
            local_key = key.split("}")[-1].lower()
            value_lower = value.strip().lower()
            if local_key.startswith("on"):
                fail(f"Event handler {key} is not allowed: {path}")
            if key in URL_ATTRS or local_key in URL_ATTRS:
                if value_lower and not value_lower.startswith("#") and not value_lower.startswith("data:image/"):
                    fail(f"External reference is not allowed in {path}: {value}")
            if "url(" in value_lower:
                refs = re.findall(r"url\(([^)]+)\)", value_lower)
                if any(not ref.strip(" '\"").startswith("#") for ref in refs):
                    fail(f"External CSS reference is not allowed: {path}")
    root.set("width", "100%")
    root.set("height", "100%")
    root.set("preserveAspectRatio", "xMidYMid meet")
    if "viewBox" not in root.attrib:
        root.set("viewBox", "0 0 1280 720")
    return ET.tostring(root, encoding="unicode")


def text(value: object, fallback: str = "") -> str:
    value = fallback if value is None else str(value)
    return html.escape(value, quote=True)


def load_manifest(path: Path) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("scenes.json root must be an object")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        fail("scenes.json must contain a non-empty scenes array")
    seen: set[str] = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            fail(f"Scene {index} must be an object")
        for key in ("id", "button", "title", "goal", "action", "subtitle", "svg"):
            if not str(scene.get(key, "")).strip():
                fail(f"Scene {index} missing {key}")
        scene_id = str(scene["id"])
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", scene_id):
            fail(f"Scene id must use lowercase letters, numbers, hyphens: {scene_id}")
        if scene_id in seen:
            fail(f"Duplicate scene id: {scene_id}")
        seen.add(scene_id)
    return data, scenes


def make_storyboard(data: dict, scenes: list[dict], svgs: list[str], source: str, session: str) -> str:
    panel_w, panel_h, gap, margin = 560, 315, 36, 64
    cols = 2
    rows = (len(scenes) + cols - 1) // cols
    width = margin * 2 + cols * panel_w + (cols - 1) * gap
    height = 150 + rows * (panel_h + 102) + 70
    panels = []
    for index, (scene, svg) in enumerate(zip(scenes, svgs), 1):
        col, row = (index - 1) % cols, (index - 1) // cols
        x = margin + col * (panel_w + gap)
        y = 118 + row * (panel_h + 102)
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        panels.append(f'''<g transform="translate({x} {y})">
  <rect width="{panel_w}" height="{panel_h}" rx="16" fill="#111827" stroke="#334155"/>
  <image href="data:image/svg+xml;base64,{encoded}" x="8" y="8" width="{panel_w-16}" height="{panel_h-16}" preserveAspectRatio="xMidYMid meet"/>
  <circle cx="22" cy="{panel_h+34}" r="15" fill="#2563eb"/><text x="22" y="{panel_h+39}" text-anchor="middle" fill="white" font-size="14" font-weight="700">{index}</text>
  <text x="48" y="{panel_h+39}" fill="#f8fafc" font-size="18" font-weight="700">{text(scene['title'])}</text>
  <text x="0" y="{panel_h+72}" fill="#94a3b8" font-size="14">{text(scene['subtitle'])}</text>
</g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#07111f"/>
<text x="{margin}" y="54" fill="#f8fafc" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="30" font-weight="750">{text(data.get('title'), 'UI demo storyboard')}</text>
<text x="{margin}" y="82" fill="#94a3b8" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="15">Static SVG storyboard · {len(scenes)} scenes · review before recording</text>
<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">{''.join(panels)}</g>
<text x="{margin}" y="{height-36}" fill="#64748b" font-family="monospace" font-size="12">Source: {text(source)} · Pi session: {text(session)}</text>
</svg>'''


def make_html(data: dict, scenes: list[dict], svgs: list[str], source: str, session: str) -> str:
    buttons = []
    panels = []
    for index, (scene, svg) in enumerate(zip(scenes, svgs), 1):
        active = " active" if index == 1 else ""
        hidden = "" if index == 1 else " hidden"
        buttons.append(f'<button class="scene-button{active}" data-scene="{text(scene["id"])}"><span>{index:02d}</span>{text(scene["button"])}</button>')
        duration = text(scene.get("duration_seconds", "?"))
        panels.append(f'''<section class="scene" data-panel="{text(scene['id'])}"{hidden}>
  <div class="canvas">{svg}</div>
  <div class="scene-copy">
    <div><p class="eyebrow">SCENE {index:02d} · {duration}s</p><h2>{text(scene['title'])}</h2><p>{text(scene['goal'])}</p></div>
    <dl><dt>Action</dt><dd>{text(scene['action'])}</dd><dt>Subtitle</dt><dd>{text(scene['subtitle'])}</dd></dl>
  </div>
  <div class="review" data-review="{text(scene['id'])}">
    <div class="choices" role="group" aria-label="Scene decision">
      <button data-choice="keep">Keep</button><button data-choice="revise">Revise</button><button data-choice="cut">Cut</button>
    </div>
    <textarea rows="3" placeholder="What should change in this scene?"></textarea>
  </div>
</section>''')
    title = text(data.get("title"), "UI demo preview")
    manifest = json.dumps(
        {"title": data.get("title", "UI demo preview"), "source": source, "session": session, "scenes": scenes},
        ensure_ascii=False,
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · storyboard preview</title>
<style>
:root{{--bg:#07111f;--panel:#0d1b2c;--line:#24354a;--text:#f8fafc;--muted:#91a1b6;--accent:#5ea3ff}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 50% -10%,#173557 0,#07111f 42%);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:42px 0 28px}}header{{display:flex;justify-content:space-between;gap:28px;align-items:end;margin-bottom:22px}}h1,h2,p{{margin:0}}h1{{font-size:clamp(28px,4vw,48px);letter-spacing:-.04em}}header p{{color:var(--muted);max-width:480px}}.scene-nav{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:24px 0}}button{{font:inherit;color:inherit}}.scene-button{{border:1px solid var(--line);background:#0b1828;padding:13px 14px;border-radius:12px;text-align:left;cursor:pointer}}.scene-button span{{display:block;color:#68809b;font:11px/1.2 ui-monospace,monospace;margin-bottom:5px}}.scene-button.active{{border-color:var(--accent);background:#132944;box-shadow:0 0 0 1px #5ea3ff55}}.scene{{border:1px solid var(--line);background:#091625;border-radius:20px;overflow:hidden;box-shadow:0 28px 80px #0007}}.canvas{{aspect-ratio:16/9;background:#020617;display:grid;place-items:center;border-bottom:1px solid var(--line)}}.canvas svg{{display:block;width:100%;height:100%}}.scene-copy{{display:grid;grid-template-columns:1fr 1fr;gap:36px;padding:26px 28px}}.scene-copy h2{{font-size:27px;margin:3px 0 5px}}.scene-copy p,.scene-copy dd{{color:var(--muted)}}.eyebrow{{font:12px/1.2 ui-monospace,monospace;color:var(--accent)!important}}dl{{display:grid;grid-template-columns:74px 1fr;gap:8px 12px;margin:0}}dt{{font-weight:700}}dd{{margin:0}}.review{{display:grid;grid-template-columns:auto 1fr;gap:18px;padding:0 28px 28px}}.choices{{display:flex;gap:8px}}.choices button,.export{{border:1px solid var(--line);background:#101f32;border-radius:9px;padding:9px 13px;cursor:pointer}}.choices button.selected{{border-color:var(--accent);background:#173a62}}textarea{{width:100%;resize:vertical;border:1px solid var(--line);background:#07111f;color:var(--text);border-radius:10px;padding:10px 12px;font:inherit}}footer{{display:flex;justify-content:space-between;gap:18px;align-items:center;color:#6f8299;font:12px ui-monospace,monospace;margin-top:18px}}.export{{color:#dbeafe}}[hidden]{{display:none!important}}@media(max-width:760px){{header,.scene-copy,.review,footer{{display:block}}.scene-nav{{grid-template-columns:1fr 1fr}}.scene-button:last-child{{grid-column:1/-1}}.review>*{{margin-top:12px}}}}
</style></head><body><main>
<header><div><p class="eyebrow">SVG FIRST · RECORD LATER</p><h1>{title}</h1></div><p>Switch scenes, mark Keep, Revise, or Cut, then export notes. No video or generated images used.</p></header>
<nav class="scene-nav" aria-label="Scenes">{''.join(buttons)}</nav>
{''.join(panels)}
<footer><span>Source: {text(source)} · Pi session: {text(session)}</span><button class="export" id="export">Export feedback JSON</button></footer>
</main><script id="manifest" type="application/json">{manifest}</script><script>
const buttons=[...document.querySelectorAll('.scene-button')];
const panels=[...document.querySelectorAll('.scene')];
const key='ui-demo-preview:'+location.pathname;
let state={{}};try{{state=JSON.parse(localStorage.getItem(key)||'{{}}')}}catch{{state={{}}}}
function show(id){{buttons.forEach(b=>b.classList.toggle('active',b.dataset.scene===id));panels.forEach(p=>p.hidden=p.dataset.panel!==id);location.hash=id}}
buttons.forEach(b=>b.addEventListener('click',()=>show(b.dataset.scene)));
document.querySelectorAll('.review').forEach(r=>{{const id=r.dataset.review;const note=r.querySelector('textarea');const saved=state[id]||{{}};note.value=saved.note||'';r.querySelectorAll('[data-choice]').forEach(b=>{{b.classList.toggle('selected',b.dataset.choice===saved.choice);b.addEventListener('click',()=>{{state[id]={{...(state[id]||{{}}),choice:b.dataset.choice,note:note.value}};localStorage.setItem(key,JSON.stringify(state));r.querySelectorAll('[data-choice]').forEach(x=>x.classList.toggle('selected',x===b))}})}});note.addEventListener('input',()=>{{state[id]={{...(state[id]||{{}}),note:note.value}};localStorage.setItem(key,JSON.stringify(state))}})}});
document.addEventListener('keydown',e=>{{if(e.target.matches('textarea'))return;const i=buttons.findIndex(b=>b.classList.contains('active'));if(e.key==='ArrowRight')show(buttons[(i+1)%buttons.length].dataset.scene);if(e.key==='ArrowLeft')show(buttons[(i-1+buttons.length)%buttons.length].dataset.scene)}});
document.getElementById('export').addEventListener('click',()=>{{const manifest=JSON.parse(document.getElementById('manifest').textContent);const blob=new Blob([JSON.stringify({{...manifest,feedback:state,exported_at:new Date().toISOString()}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='ui-demo-preview-feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}});
const requested=location.hash.slice(1);if(buttons.some(b=>b.dataset.scene===requested))show(requested);
</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = (args.output_dir or manifest_path.parent).resolve()
    data, scenes = load_manifest(manifest_path)
    svgs = [clean_svg((manifest_path.parent / str(scene["svg"])).resolve()) for scene in scenes]
    output_dir.mkdir(parents=True, exist_ok=True)
    source = str(data.get("source") or manifest_path.parent)
    session = os.environ.get("PI_SESSION_ID", "unknown")
    (output_dir / "storyboard.svg").write_text(make_storyboard(data, scenes, svgs, source, session), encoding="utf-8")
    (output_dir / "preview.html").write_text(make_html(data, scenes, svgs, source, session), encoding="utf-8")
    print(output_dir / "storyboard.svg")
    print(output_dir / "preview.html")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
