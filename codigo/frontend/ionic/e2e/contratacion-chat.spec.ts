import { test, expect } from '@playwright/test';
import { login, CLIENTE_DEMO } from './fixtures';

/**
 * Flujo real: login -> Mis contrataciones -> abrir un trabajo -> mandar un mensaje de chat y
 * verlo aparecer como burbuja. No toca estados de la contratación (confirmar/completar/pagar/
 * valorar) a propósito — la data demo sembrada (sembrar_datos_demo) trae un ejemplo de cada
 * estado del BPMN para el portafolio/demo, y una transición real la rompería. Mandar un mensaje
 * de chat es seguro: no cambia el estado de nada, solo agrega una fila a la conversación — mismo
 * criterio que ya se verificó en vivo al construir el rediseño del chat.
 */
test.describe('Chat de una contratación', () => {
  test('manda un mensaje de texto y aparece como burbuja propia', async ({ page }) => {
    await login(page, CLIENTE_DEMO);

    await page.goto('/reservas');
    await expect(page.locator('a[href*="/contratacion/"]').first()).toBeVisible();
    await page.locator('a[href*="/contratacion/"]').first().click();
    await expect(page).toHaveURL(/\/contratacion\/\d+/);

    const mensaje = `Mensaje de prueba E2E — ${Date.now()}`;
    // ion-input expone el placeholder tanto en el custom element como en su <input> interno —
    // apuntar al <input> real evita la ambigüedad de "dos elementos" para Playwright.
    const campoMensaje = page.locator('.ks-chat-input input');
    await campoMensaje.scrollIntoViewIfNeeded();
    await campoMensaje.fill(mensaje);
    await campoMensaje.press('Enter');

    await expect(page.locator('.ks-chat-fila-propio', { hasText: mensaje })).toBeVisible();
  });
});
