#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/docs/assets/demo"
PORT="${UI_DEMO_PORT:-43173}"
mkdir -p "$OUT"
cd "$ROOT"

npm ci --no-audit --no-fund
CHROME_PATH="${CHROME_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
test -x "$CHROME_PATH"
export CHROME_PATH
node -e 'require("playwright").chromium.launch({headless:true,executablePath:process.env.CHROME_PATH}).then(b=>b.close())'

python3 -m http.server "$PORT" --bind 127.0.0.1 --directory docs >"$OUT/server.log" 2>&1 &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 40); do
  if curl -fsS "http://127.0.0.1:$PORT/product-demo/" >/dev/null; then break; fi
  sleep .25
done
curl -fsS "http://127.0.0.1:$PORT/product-demo/" >/dev/null

BASE_URL="http://127.0.0.1:$PORT" node tools/demo-video/record.cjs --rehearse | tee "$OUT/rehearsal.log"
BASE_URL="http://127.0.0.1:$PORT" node tools/demo-video/record.cjs | tee "$OUT/record.log"

ffmpeg -y -hide_banner -loglevel error \
  -i "$OUT/ui-demo-preview.webm" \
  -an -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart \
  "$OUT/ui-demo-preview.mp4"

ffmpeg -y -hide_banner -loglevel error -i "$OUT/ui-demo-preview.mp4" \
  -filter_complex "fps=8,scale=720:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" \
  "$OUT/ui-demo-preview.gif"
ffprobe -v error -show_format -show_streams -of json "$OUT/ui-demo-preview.mp4" > "$OUT/probe.json"
ffmpeg -y -hide_banner -loglevel error -ss 2 -i "$OUT/ui-demo-preview.mp4" -frames:v 1 "$OUT/poster.png"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/ui-demo-preview.mp4" \
  -vf "fps=1/2,scale=320:-1,tile=4x4:padding=4:margin=4:color=0x07111f" -frames:v 1 "$OUT/contact-sheet.png"
ffmpeg -y -hide_banner -loglevel error -ss 7 -t 12 -i "$OUT/ui-demo-preview.mp4" \
  -vf "fps=2,scale=256:-1,tile=6x4:padding=3:margin=3:color=0x07111f" -frames:v 1 "$OUT/interaction-strip.png"

python3 - "$OUT/probe.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1]))
v=next(s for s in p['streams'] if s['codec_type']=='video')
assert v['codec_name']=='h264', v
assert v['pix_fmt']=='yuv420p', v
assert int(v['width'])==1280 and int(v['height'])==720, v
assert float(p['format']['duration'])>15, p['format']
print('REMOTE VIDEO QA PASS', v['codec_name'], v['pix_fmt'], v['width'], v['height'], p['format']['duration'])
PY
