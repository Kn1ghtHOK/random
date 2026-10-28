// node render.js <out.png> '<views json>' [w] [h] [title]
const { chromium } = require('playwright');
(async () => {
  const [out, views, w = 520, h = 1100, title = ''] = process.argv.slice(2);
  const n = JSON.parse(views).length;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: n * +w, height: +h } });
  p.on('console', m => console.log('page:', m.text()));
  p.on('pageerror', e => console.log('err:', e.message));
  await p.goto(`http://127.0.0.1:8765/render.html?w=${w}&h=${h}&title=${encodeURIComponent(title)}&views=${encodeURIComponent(views)}`);
  await p.waitForFunction('window.READY === true', null, { timeout: 300000 });
  await p.waitForTimeout(500);
  await p.screenshot({ path: out });
  await b.close();
})();
