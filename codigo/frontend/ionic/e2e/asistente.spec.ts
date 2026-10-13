import { test, expect } from '@playwright/test';

/**
 * Asistente flotante: sin sesión, en el catálogo. El CI no tiene clave de NVIDIA, así que responde con el flujo
 * guiado; con clave real (local) responde la IA. La aserción vale para los dos: llega una respuesta y se ve el aviso.
 */
test.describe('Asistente', () => {
  test('se abre, muestra el aviso de IA externa y responde una pregunta', async ({ page }) => {
    await page.goto('/catalogo');
    await page.getByRole('button', { name: 'Abrir el asistente de KeyServ' }).click();

    const panel = page.getByRole('dialog', { name: 'Asistente de KeyServ' });
    await expect(panel).toBeVisible();
    await expect(panel.locator('.ks-asistente-aviso')).toContainText('inteligencia artificial');

    await panel.getByLabel('Escribe tu pregunta al asistente').fill('¿Cómo pago un servicio?');
    await page.keyboard.press('Enter');

    const respuestas = panel.locator('.ks-asistente-fila:not(.ks-asistente-propio) .ks-asistente-burbuja:not(.ks-asistente-escribiendo)');
    await expect(respuestas).toHaveCount(2, { timeout: 60000 }); // saludo inicial + respuesta
  });

  test('Escape cierra el panel', async ({ page }) => {
    await page.goto('/catalogo');
    await page.getByRole('button', { name: 'Abrir el asistente de KeyServ' }).click();
    await expect(page.getByRole('dialog', { name: 'Asistente de KeyServ' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog', { name: 'Asistente de KeyServ' })).toBeHidden();
  });
});
