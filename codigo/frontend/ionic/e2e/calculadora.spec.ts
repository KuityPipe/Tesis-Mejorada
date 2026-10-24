import { test, expect } from '@playwright/test';

/** La calculadora es pública: se prueba sin iniciar sesión y sin dejar rastro en los datos demo. */
test.describe('Calculadora de valorización', () => {
  test('asistente, modo normal: tres cifras con boleta, sin pedir cuenta', async ({ page }) => {
    await page.goto('/calculadora');
    await expect(page.getByText('Paso 1 de 4')).toBeVisible();
    await page.getByRole('button', { name: /Ya sé cuánto quiero que me quede/ }).click();

    await page.getByLabel('¿Cuánto quieres que te quede por el servicio? ($)').fill('30000');
    await page.getByRole('button', { name: 'Siguiente' }).click();

    await page.locator('ion-segment-button[value="BOLETA_HONORARIOS"]').first().click({ force: true });
    await page.getByRole('button', { name: /¿Qué es la retención\?/ }).click();
    await expect(page.getByRole('note')).toContainText('adelanto de tu impuesto');
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // $30.000 netos con retención del 16 % → se cobran $35.715; el detalle queda plegado.
    await expect(page.getByText('Cobras', { exact: true })).toBeVisible();
    await expect(page.getByText('El cliente paga')).toBeVisible();
    await expect(page.getByText('Te quedan', { exact: true })).toBeVisible();
    await expect(page.getByText('$35.715').first()).toBeVisible();
    await expect(page.locator('details.ks-calc-detalle')).not.toHaveAttribute('open', '');
  });

  test('asistente, costos: recorre los pasos y se puede saltar lo opcional', async ({ page }) => {
    await page.goto('/calculadora');
    await page.getByRole('button', { name: /Quiero calcularlo desde mis costos/ }).click();
    await expect(page.getByText('Paso 2 de 8')).toBeVisible();
    await page.getByRole('button', { name: 'Siguiente' }).click(); // materiales → traslado
    await page.getByRole('button', { name: /Saltar o seguir/ }).click(); // traslado → tu trabajo
    await page.getByLabel('Horas de trabajo').fill('3');
    await page.getByLabel('Valor por hora ($)').fill('8000');
    await page.getByRole('button', { name: 'Siguiente' }).click(); // → herramientas
    await page.getByRole('button', { name: /Saltar o seguir/ }).click(); // → imprevistos y ganancia
    await page.getByRole('button', { name: /Saltar o seguir/ }).click(); // → documento
    await page.locator('ion-segment-button[value="BOLETA_HONORARIOS"]').first().click({ force: true });
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // 3 h × $8.000 = $24.000 → ×1,10 ×1,15 = $30.360 netos → con retención del 16 % se cobran $36.143.
    await expect(page.getByText('$36.143').first()).toBeVisible();
  });

  test('«Ver todo junto» muestra la calculadora completa', async ({ page }) => {
    await page.goto('/calculadora');
    await page.getByRole('button', { name: 'Ver todo junto' }).click();
    await expect(page.getByText('Cobrar un servicio')).toBeVisible();
    await page.getByLabel('¿Cuánto quieres que te quede por el servicio? ($)').fill('20000');
    await page.locator('ion-segment-button[value="DOCUMENTO_IVA"]').first().click({ force: true });
    // $20.000 netos + 19 % de IVA = $23.800; el IVA ($3.800) se traspasa al SII.
    await expect(page.getByText('$23.800').first()).toBeVisible();
    await expect(page.getByText('El IVA no es tuyo')).toBeVisible();
    await expect(page.getByText('Materiales', { exact: true })).toHaveCount(0);
  });

  test('todo junto, calculadora de costos: calcula con boleta de honorarios', async ({ page }) => {
    await page.goto('/calculadora');
    await expect(page.getByRole('heading', { name: /cobrar por/i })).toBeVisible();
    await page.getByRole('button', { name: 'Ver todo junto' }).click();
    await page.locator('ion-segment-button[value="costos"]').click({ force: true });
    await expect(page.getByText('Materiales').first()).toBeVisible();

    await page.getByLabel('Horas de trabajo').fill('3');
    await page.getByLabel('Valor por hora ($)').fill('8000');
    await page.locator('ion-segment-button[value="BOLETA_HONORARIOS"]').first().click({ force: true });

    await expect(page.getByText('$36.143').first()).toBeVisible();
    await expect(page.getByText(/líquidos/)).toBeVisible();
  });

  test('ofrece descargar el PDF y la planilla al final del asistente', async ({ page }) => {
    await page.goto('/calculadora');
    await page.getByRole('button', { name: /Ya sé cuánto quiero que me quede/ }).click();
    await page.getByRole('button', { name: 'Siguiente' }).click();
    await page.getByRole('button', { name: 'Siguiente' }).click();
    await expect(page.getByRole('button', { name: /Descargar PDF/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Descargar planilla/ })).toBeVisible();
  });
});
