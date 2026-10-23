import { test, expect } from '@playwright/test';
import { login, CLIENTE_DEMO } from './fixtures';

/**
 * Preguntas voluntarias de impacto (ADR 0008): se contestan desde Preferencias y se pueden borrar. El test deja la
 * cuenta demo como la encontró (sin responder) para no alterar los datos compartidos.
 */
test.describe('Medición de impacto (preguntas voluntarias)', () => {
  test('se explican con su finalidad, se guardan y se pueden borrar', async ({ page }) => {
    await login(page, CLIENTE_DEMO);
    await page.goto('/preferencias');
    await expect(page.getByText('Medición de impacto (opcional)')).toBeVisible();
    await expect(page.getByText(/medir el impacto de KeyServ en el empleo/).first()).toBeVisible();

    await page.getByLabel('Situación laboral antes de KeyServ').click({ force: true });
    await page.locator('ion-popover').getByText('Sin trabajo', { exact: true }).click();
    await page.getByRole('button', { name: 'Guardar respuestas' }).click();
    await expect(page.getByText('Respuestas actualizadas.')).toBeVisible();

    await page.getByLabel('Situación laboral antes de KeyServ').click({ force: true });
    await page.locator('ion-popover').getByText('Sin responder', { exact: true }).click();
    await page.getByRole('button', { name: 'Guardar respuestas' }).click();
    await expect(page.getByText('Respuestas actualizadas.')).toBeVisible();
  });
});
