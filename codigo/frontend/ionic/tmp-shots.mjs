import { chromium } from '@playwright/test';
const OUT = process.argv[2];
const sel = process.argv[3] ? new RegExp(process.argv[3]) : null;
const rutas = ['/', '/catalogo', '/catalogo/21', '/login', '/registro', '/acerca-de-nosotros', '/contacto',
  '/home', '/reservas', '/mensajes', '/perfil/editar', '/perfil/proveedor', '/perfil/publicaciones', '/perfil/pagos',
  '/preferencias', '/rostro', '/biometria', '/verificacion-alternativa', '/catalogo/crear', '/contratacion/9'];
const b = await chromium.launch();
async function sesion(w, h) {
  const ctx = await b.newContext({ viewport: { width: w, height: h } });
  const p = await ctx.newPage();
  await p.goto('http://localhost:8100/login');
  await p.getByLabel('Correo electrónico').fill('marcelo.gasfiteria@demo.keyserv');
  await p.getByLabel('Contraseña').fill('Demo1234');
  await p.getByRole('button', { name: 'Iniciar sesión' }).click();
  await p.waitForURL(/\/home/, { timeout: 40000 });
  return p;
}
for (const [nombre, w, h] of [['pc', 1440, 1900], ['movil', 390, 2300]]) {
  const p = await sesion(w, h);
  for (const r of rutas) {
    if (sel && !sel.test(r)) continue;
    try {
      await p.goto('http://localhost:8100' + r, { waitUntil: 'networkidle', timeout: 40000 });
      await p.waitForTimeout(900);
      await p.screenshot({ path: `${OUT}/${nombre}${r.replace(/\//g, '_') || '_inicio'}.png`, fullPage: true });
    } catch (e) { console.log('fallo', nombre, r, e.message.slice(0, 80)); }
  }
}
await b.close();
console.log('listo');
