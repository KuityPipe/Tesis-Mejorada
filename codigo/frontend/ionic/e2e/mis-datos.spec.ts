import { test, expect } from '@playwright/test';
import { login, CLIENTE_DEMO } from './fixtures';

/**
 * "Mis datos": solo comprueba que las opciones de derechos del titular están a la vista. No envía solicitudes,
 * ni bloquea, ni elimina la cuenta: la data demo es compartida y esas acciones la dejarían alterada.
 */
test.describe('Mis datos (derechos del titular)', () => {
  test('las opciones de derechos son visibles para quien inició sesión', async ({ page }) => {
    await login(page, CLIENTE_DEMO);
    await page.goto('/preferencias');
    await expect(page.getByText('Tus derechos sobre tus datos')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Pedir rectificación' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Oponerme al tratamiento biométrico' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Descargar mis datos' })).toBeVisible();
  });
});
