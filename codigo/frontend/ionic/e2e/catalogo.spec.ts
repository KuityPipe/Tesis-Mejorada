import { test, expect } from '@playwright/test';

test.describe('Catálogo público', () => {
  test('el catálogo carga publicaciones reales sin necesitar sesión', async ({ page }) => {
    await page.goto('/catalogo');

    // Al menos una card real de la data demo sembrada (sembrar_datos_demo) — no un mock.
    await expect(page.locator('.ks-card-tile').first()).toBeVisible();
    const cantidadCards = await page.locator('.ks-card-tile').count();
    expect(cantidadCards).toBeGreaterThan(0);
  });

  test('buscar filtra los resultados', async ({ page }) => {
    await page.goto('/catalogo');
    await expect(page.locator('.ks-card-tile').first()).toBeVisible();
    const totalSinFiltrar = await page.locator('.ks-card-tile').count();

    // ion-searchbar expone el placeholder tanto en el custom element como en su <input> interno
    // (shadow DOM) — hay que apuntar al <input> real, si no Playwright ve dos matches. El filtro
    // real dispara en (ionChange), que ion-searchbar solo emite al perder el foco/Enter (no en
    // cada tecleo como ionInput), así que hace falta un blur explícito, no solo esperar.
    await page.locator('ion-searchbar input').fill('xxxxxxxxxxninguncoincidenciaxxxxxxxxxxx');
    await page.locator('ion-searchbar input').press('Tab');
    await page.waitForTimeout(500);

    const totalFiltrado = await page.locator('.ks-card-tile').count();
    expect(totalFiltrado).toBeLessThan(totalSinFiltrar);
  });

  test('abrir una publicación muestra su detalle', async ({ page }) => {
    await page.goto('/catalogo');
    await expect(page.locator('.ks-card-tile').first()).toBeVisible();

    await page.locator('.ks-card-tile').first().click();

    await expect(page).toHaveURL(/\/catalogo\/\d+/);
    await expect(page.getByRole('button', { name: /contrat/i })).toBeVisible();
  });
});
