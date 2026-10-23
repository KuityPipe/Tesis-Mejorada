import { test, expect } from '@playwright/test';

/** La calculadora es pública: se prueba sin iniciar sesión y sin dejar rastro en los datos demo. */
test.describe('Calculadora de valorización', () => {
  test('calcula con boleta de honorarios sin pedir cuenta', async ({ page }) => {
    await page.goto('/calculadora');
    await expect(page.getByRole('heading', { name: /cobrar por/i })).toBeVisible();

    await page.getByLabel('Horas de trabajo').fill('3');
    await page.getByLabel('Valor por hora ($)').fill('8000');
    await page.locator('ion-segment-button[value="BOLETA_HONORARIOS"]').click({ force: true });

    // 3 h × $8.000 = $24.000 → ×1,10 ×1,15 = $30.360 netos → con retención del 16 % se cobran $36.143.
    await expect(page.getByText('$36.143').first()).toBeVisible();
    await expect(page.getByText(/líquidos/)).toBeVisible();
  });

  test('ofrece descargar el PDF y la planilla', async ({ page }) => {
    await page.goto('/calculadora');
    await expect(page.getByRole('button', { name: /Descargar PDF/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Descargar planilla/ })).toBeVisible();
  });
});
