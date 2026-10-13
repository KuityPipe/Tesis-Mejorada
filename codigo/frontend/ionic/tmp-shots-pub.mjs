import { chromium } from '@playwright/test';
const OUT = process.argv[2];
const rutas = process.argv.slice(3);
const b = await chromium.launch();
for (const [nombre, w, h] of [['pc', 1440, 1500], ['movil', 390, 2000]]) {
  const p = await (await b.newContext({ viewport: { width: w, height: h } })).newPage();
  for (const r of rutas) {
    await p.goto('http://localhost:8100' + r, { waitUntil: 'networkidle', timeout: 40000 });
    await p.waitForTimeout(900);
    await p.screenshot({ path: `${OUT}/pub_${nombre}${r.replace(/\//g, '_')}.png` });
  }
}
await b.close(); console.log('listo');
