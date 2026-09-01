'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '../..');
const OUT = path.join(ROOT, 'docs/assets/demo');
const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:4173';
const REHEARSE = process.argv.includes('--rehearse');
fs.mkdirSync(OUT, { recursive: true });

async function injectOverlays(page) {
  await page.evaluate(() => {
    const cursor = document.createElement('div');
    cursor.id = 'recording-cursor';
    cursor.innerHTML = '<svg viewBox="0 0 24 32"><path d="M2 1v25l6-6 8 11 5-3-8-11h9z" fill="#07111f" stroke="#fff" stroke-width="1.8"/></svg>';
    cursor.style.cssText = 'position:fixed;left:0;top:0;width:28px;height:36px;z-index:999999;pointer-events:none;filter:drop-shadow(0 2px 3px rgba(0,0,0,.35));transition:left .08s linear,top .08s linear';
    document.body.appendChild(cursor);
    document.addEventListener('mousemove', e => { cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px'; });
    const subtitle = document.createElement('div');
    subtitle.id = 'recording-subtitle';
    subtitle.style.cssText = 'position:fixed;left:50%;top:18px;transform:translateX(-50%);z-index:999998;max-width:760px;padding:10px 18px;border-radius:999px;background:rgba(7,17,31,.9);color:white;font:700 15px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;letter-spacing:.01em;opacity:0;transition:opacity .2s;pointer-events:none;box-shadow:0 8px 28px rgba(0,0,0,.28)';
    document.body.appendChild(subtitle);
  });
}

async function subtitle(page, text) {
  await page.evaluate(t => { const el = document.getElementById('recording-subtitle'); el.textContent = t || ''; el.style.opacity = t ? '1' : '0'; }, text);
  if (text) await page.waitForTimeout(650);
}

async function ensureVisible(locator, label) {
  if (!await locator.isVisible().catch(() => false)) throw new Error(`REHEARSAL FAIL: ${label} not visible`);
  const box = await locator.boundingBox();
  if (!box) throw new Error(`REHEARSAL FAIL: ${label} has no box`);
  if (box.x < 0 || box.y < 0 || box.x + box.width > 1280 || box.y + box.height > 720) throw new Error(`FRAMING FAIL: ${label} ${JSON.stringify(box)}`);
  console.log(`REHEARSAL OK: ${label} ${JSON.stringify(box)}`);
}

async function moveAndClick(page, locator, label, hold = 900) {
  await ensureVisible(locator, label);
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 12 });
  await page.waitForTimeout(350);
  await locator.click();
  await page.waitForTimeout(hold);
}

async function typeSlowly(page, locator, value, label) {
  await moveAndClick(page, locator, label, 250);
  await locator.fill('');
  await locator.pressSequentially(value, { delay: 32 });
  await page.waitForTimeout(700);
}

async function discover(page) {
  const evidence = await page.evaluate(() => ({
    viewport: { width: innerWidth, height: innerHeight },
    document: { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight },
    controls: [...document.querySelectorAll('button,select,textarea')].filter(el => el.offsetParent !== null).map(el => ({
      tag: el.tagName,
      label: (el.getAttribute('aria-label') || el.textContent || el.getAttribute('placeholder') || '').trim().slice(0, 80),
      rect: (() => { const r = el.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) }; })()
    }))
  }));
  fs.writeFileSync(path.join(OUT, 'discovery.json'), JSON.stringify(evidence, null, 2));
  console.log(`DISCOVERY OK: ${evidence.controls.length} controls, document ${evidence.document.width}x${evidence.document.height}`);
}

async function runFlow(page, markers) {
  const started = Date.now();
  async function mark(label, extra = {}) {
    const state = await page.evaluate(({ label, extra, started }) => ({ label, elapsedMs: Date.now() - started, scrollY, viewport: { width: innerWidth, height: innerHeight }, ...extra }), { label, extra, started });
    markers[label] = Number((state.elapsedMs / 1000).toFixed(3));
    console.log(JSON.stringify({ marker: 'ui-demo', ...state }));
  }

  const story = page.locator('#story-select');
  const build = page.locator('#build-scenes');
  const scene2 = page.locator('[data-scene="1"]');
  const scene3 = page.locator('[data-scene="2"]');
  const scene4 = page.locator('[data-scene="3"]');
  const scene5 = page.locator('[data-scene="4"]');
  const revise = page.locator('[data-value="revise"]');
  const keep = page.locator('[data-value="keep"]');
  const note = page.locator('#note');
  const exportButton = page.locator('#export-feedback');

  for (const [locator, label] of [[story, 'Product story selector'], [build, 'Build five scenes'], [scene3, 'Scene 3 tab'], [revise, 'Revise decision'], [note, 'Revision note'], [exportButton, 'Export feedback']]) await ensureVisible(locator, label);
  await subtitle(page, 'Start with the product story, not the recorder');
  await page.mouse.move(440, 155, { steps: 12 });
  await page.waitForTimeout(1500);
  await mark('orient', { state: 'rough idea visible' });

  await subtitle(page, 'Generate five editable SVG scenes');
  await moveAndClick(page, build, 'Build five scenes', 300);
  await page.locator('#build-scenes').filter({ hasText: 'Five scenes ready' }).waitFor();
  await page.waitForTimeout(1600);
  await mark('build', { state: 'five scenes ready' });

  await subtitle(page, 'Compare and review every scene');
  await moveAndClick(page, keep, 'Keep scene 1', 350);
  await moveAndClick(page, scene2, 'Scene 2 tab', 300);
  await moveAndClick(page, keep, 'Keep scene 2', 350);
  await moveAndClick(page, scene3, 'Scene 3 tab', 700);
  await moveAndClick(page, keep, 'Keep scene 3', 700);
  await mark('compare', { scene: 3, reviewed: 3 });

  await subtitle(page, 'Leave one actionable revision');
  await moveAndClick(page, scene4, 'Scene 4 tab', 700);
  await moveAndClick(page, revise, 'Revise decision', 500);
  await typeSlowly(page, note, 'Move the cursor target closer to Create request.', 'Revision note');
  await page.waitForTimeout(1000);
  await mark('revise', { decision: 'revise', note: 'saved' });

  await subtitle(page, 'Approve the storyboard, then unlock recording');
  await moveAndClick(page, scene5, 'Scene 5 tab', 650);
  await moveAndClick(page, keep, 'Keep final scene', 550);
  await moveAndClick(page, exportButton, 'Export feedback', 600);
  await page.locator('#mock-proof').filter({ hasText: 'Recording unlocked' }).waitFor();
  await page.waitForTimeout(3000);
  await mark('approve', { state: 'recording unlocked' });
  await subtitle(page, '');
  await page.waitForTimeout(900);
}

(async () => {
  const launchOptions = { headless: true };
  if (process.env.CHROME_PATH) launchOptions.executablePath = process.env.CHROME_PATH;
  const browser = await chromium.launch(launchOptions);
  const contextOptions = { viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce', deviceScaleFactor: 1 };
  if (!REHEARSE) contextOptions.recordVideo = { dir: OUT, size: { width: 1280, height: 720 } };
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();
  await page.goto(`${BASE_URL}/product-demo/`, { waitUntil: 'networkidle' });
  await injectOverlays(page);
  await discover(page);
  const markers = {};
  await runFlow(page, markers);
  if (REHEARSE) {
    console.log('REHEARSAL PASSED: semantics, selectors, state transitions, framing');
    await context.close();
    await browser.close();
    return;
  }
  const video = page.video();
  await context.close();
  if (!video) throw new Error('Recording video missing');
  await video.saveAs(path.join(OUT, 'ui-demo-preview.webm'));
  fs.writeFileSync(path.join(OUT, 'markers.json'), JSON.stringify({ chapters: markers, generatedFrom: 'runtime markers' }, null, 2));
  await browser.close();
  console.log(`VIDEO SAVED: ${path.join(OUT, 'ui-demo-preview.webm')}`);
})().catch(error => { console.error(error.stack || error.message); process.exit(1); });
