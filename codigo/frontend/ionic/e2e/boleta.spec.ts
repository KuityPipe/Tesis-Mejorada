import { test, expect } from '@playwright/test';
import { login, PROVEEDOR_DEMO } from './fixtures';

const API = process.env.E2E_API_URL || 'http://localhost:8000/api';

/**
 * Fase 1 de la boleta de honorarios: el proveedor registra el folio de un trabajo ya pagado y lo quita. Busca por API un
 * trabajo pagado de la cuenta demo (la data demo trae varios) y deja todo como estaba: registra y quita el mismo folio.
 */
test.describe('Boleta de honorarios (folio)', () => {
  test('el proveedor registra y quita el folio de un trabajo pagado', async ({ page, request }) => {
    const sesion = await request.post(`${API}/auth/login/`, { data: PROVEEDOR_DEMO });
    const { access_token, usuario } = await sesion.json();
    const lista = await request.get(`${API}/contrataciones/`, { headers: { Authorization: `Bearer ${access_token}` } });
    const cuerpo = await lista.json();
    const contrataciones = Array.isArray(cuerpo) ? cuerpo : cuerpo.results;
    const propias = (contrataciones as { id_contratacion: number; proveedor: number; estado: string }[]).filter(
      (c) => c.proveedor === usuario.id_usuario && ['EN_CURSO', 'COMPLETADA'].includes(c.estado),
    );
    let pagado: { id_contratacion: number } | undefined;
    for (const c of propias) {
      const detalle = await (await request.get(`${API}/contrataciones/${c.id_contratacion}/`, { headers: { Authorization: `Bearer ${access_token}` } })).json();
      if (detalle.pago?.estado === 'PAGADO') {
        pagado = c;
        break;
      }
    }
    test.skip(!pagado, 'La cuenta demo no tiene un trabajo pagado como proveedor');

    await login(page, PROVEEDOR_DEMO);
    await page.goto(`/contratacion/${pagado!.id_contratacion}`);
    await expect(page.getByText('Boleta de honorarios', { exact: true })).toBeVisible();
    await expect(page.getByText(/KeyServ no emite boletas/)).toBeVisible();
    await expect(page.getByRole('link', { name: 'sii.cl' }).first()).toHaveAttribute('href', 'https://www.sii.cl');

    await page.getByLabel('Folio de la boleta').fill('99001234');
    await page.getByLabel('¿Es tu primera boleta?').click({ force: true });
    await page.locator('ion-popover').getByText('No, ya había emitido otras').click();
    await page.getByRole('button', { name: 'Registrar folio' }).click();
    await expect(page.getByText('Folio registrado.')).toBeVisible();

    await page.getByRole('button', { name: 'Quitar el folio' }).click();
    await expect(page.getByText('Folio quitado.')).toBeVisible();
  });
});
