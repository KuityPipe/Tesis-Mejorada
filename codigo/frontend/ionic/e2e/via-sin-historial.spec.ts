import { test, expect } from '@playwright/test';

/** La vía sin historial (cédula + video) se explica en la portada y al elegir "Ofrezco servicios", con lo que de verdad hace. */
test.describe('Vía sin historial', () => {
  test('la portada la explica y aclara que revisa una persona', async ({ page }) => {
    await page.goto('/');
    const aviso = page.locator('.ks-prov-sinhistorial');
    await aviso.scrollIntoViewIfNeeded();
    await expect(aviso).toContainText('Empieza aunque nunca hayas trabajado con boleta');
    await expect(aviso).toContainText('revisa una persona del equipo');
    await expect(aviso).toContainText('no una consulta al Registro Civil');
  });

  test('el registro la muestra solo a quien ofrece servicios', async ({ page }) => {
    await page.goto('/registro');
    await expect(page.locator('.ks-reg-sinhistorial')).toHaveCount(0);
    await page.getByRole('radio', { name: /Ofrezco servicios/ }).click();
    await expect(page.locator('.ks-reg-sinhistorial')).toContainText('Puedes empezar igual');
    await expect(page.locator('.ks-reg-sinhistorial')).toContainText('No es una consulta al Registro Civil');
  });
});
