import { test, expect } from '@playwright/test';

/** La calculadora es pública: se prueba sin iniciar sesión y sin dejar rastro en los datos demo. */
test.describe('Calculadora de valorización', () => {
  test('modo normal: cobra un servicio simple con boleta sin pedir cuenta', async ({ page }) => {
    await page.goto('/calculadora');
    await expect(page.getByText('Cobrar un servicio')).toBeVisible();
    await page.getByLabel('¿Cuánto quieres que te quede por el servicio? ($)').fill('30000');
    await page.locator('ion-segment-button[value="BOLETA_HONORARIOS"]').first().click({ force: true });
    // $30.000 netos con retención del 16 % → se cobran $35.715.
    await expect(page.getByText('$35.715').first()).toBeVisible();
    await expect(page.getByText('Materiales', { exact: true })).toHaveCount(0);
  });

  test('modo normal: con IVA el IVA no cuenta en lo que recibes', async ({ page }) => {
    await page.goto('/calculadora');
    await page.getByLabel('¿Cuánto quieres que te quede por el servicio? ($)').fill('20000');
    await page.locator('ion-segment-button[value="DOCUMENTO_IVA"]').first().click({ force: true });
    // $20.000 netos + 19 % de IVA = $23.800; el IVA ($3.800) se traspasa al SII.
    await expect(page.getByText('$23.800').first()).toBeVisible();
    await expect(page.getByText('El IVA no es tuyo')).toBeVisible();
  });

  test('calculadora de costos: calcula con boleta de honorarios sin pedir cuenta', async ({ page }) => {
    await page.goto('/calculadora');
    await expect(page.getByRole('heading', { name: /cobrar por/i })).toBeVisible();
    await page.locator('ion-segment-button[value="costos"]').click({ force: true });
    await expect(page.getByText('Materiales').first()).toBeVisible();

    await page.getByLabel('Horas de trabajo').fill('3');
    await page.getByLabel('Valor por hora ($)').fill('8000');
    await page.locator('ion-segment-button[value="BOLETA_HONORARIOS"]').first().click({ force: true });

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
