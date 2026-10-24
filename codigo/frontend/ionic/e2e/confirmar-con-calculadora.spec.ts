import { test, expect } from '@playwright/test';
import { login, PROVEEDOR_DEMO } from './fixtures';

const API = process.env.E2E_API_URL || 'http://localhost:8000/api';

/**
 * "Confirmar contratación" lleva a la calculadora de ese trabajo, con el precio de la publicación grande a la vista.
 * No llega a confirmar (cambiaría el estado de la data demo compartida): solo comprueba el recorrido y que una contraseña
 * incorrecta no confirma nada.
 */
test.describe('Confirmar un trabajo desde la calculadora', () => {
  test('el botón lleva a la calculadora de ese trabajo con el precio sugerido', async ({ page, request }) => {
    const sesion = await request.post(`${API}/auth/login/`, { data: PROVEEDOR_DEMO });
    const { access_token, usuario } = await sesion.json();
    const lista = await (await request.get(`${API}/contrataciones/`, { headers: { Authorization: `Bearer ${access_token}` } })).json();
    const pendiente = (lista as { id_contratacion: number; proveedor: number; estado: string }[]).find(
      (c) => c.proveedor === usuario.id_usuario && c.estado === 'SOLICITADA',
    );
    test.skip(!pendiente, 'La cuenta demo no tiene una solicitud pendiente como proveedor');

    await login(page, PROVEEDOR_DEMO);
    await page.goto(`/contratacion/${pendiente!.id_contratacion}`);
    await page.getByRole('button', { name: /Confirmar contratación/ }).click();

    await expect(page).toHaveURL(new RegExp(`/calculadora\\?contratacion=${pendiente!.id_contratacion}`));
    await expect(page.getByText('Precio sugerido en tu publicación')).toBeVisible();
    await expect(page.locator('.ks-calc-sugerido-grande strong')).toContainText('$');
    await expect(page.getByRole('button', { name: /Confirmar con \$.*\(tu publicación\)/ })).toBeVisible();

    // Con una contraseña incorrecta no se confirma nada.
    await page.getByLabel('Confirma tu contraseña').fill('incorrecta-123');
    await page.getByRole('button', { name: /Confirmar con \$.*\(tu publicación\)/ }).click();
    await expect(page.getByText(/Contraseña incorrecta/)).toBeVisible();
    await expect(page).toHaveURL(/\/calculadora/);
  });
});
