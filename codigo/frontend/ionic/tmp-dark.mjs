import { chromium } from '@playwright/test';
const OUT = process.argv[2];
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 1500 } });
await ctx.addInitScript(() => localStorage.setItem('ks-theme', 'dark'));
const p = await ctx.newPage();
for (const r of ['/', '/catalogo/21', '/registro', '/rostro']) {
  await p.goto('http://localhost:8100' + r, { waitUntil: 'networkidle' });
  await p.waitForTimeout(1000);
  await p.screenshot({ path: `${OUT}/dark${r.replace(/\//g, '_')}.png` });
}
await b.close(); console.log('listo');
