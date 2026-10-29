// node render.js <scene.json> <out.png>    (needs a static server on :8765 serving this folder)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [scene, out] = process.argv.slice(2);
  const s = JSON.parse(fs.readFileSync(scene));
  const w = s.views.reduce((a, v) => a + (v.w || s.w || 520), 0), h = s.h || 1100;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: w, height: h } });
  p.on('pageerror', e => console.log('err:', e.message));
  p.on('console', m => { if (m.type() === 'error') console.log('console:', m.text()); });
  await p.goto(`http://127.0.0.1:8765/render.html?scene=${encodeURIComponent(scene)}`);
  await p.waitForFunction('window.READY === true', null, { timeout: 900000 });
  await p.screenshot({ path: out });
  await b.close();
})();
