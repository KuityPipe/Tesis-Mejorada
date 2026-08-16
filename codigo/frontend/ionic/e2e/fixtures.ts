import { Page, expect } from '@playwright/test';

/** Mismas cuentas demo que sembrar_datos_demo (ver CLAUDE.md) — nunca se crean cuentas nuevas
 * desde los tests E2E para no ensuciar los datos demo compartidos con el resto del equipo. */
export const CLIENTE_DEMO = { email: 'cliente.demo@demo.keyserv', password: 'Demo1234' };
export const PROVEEDOR_DEMO = { email: 'marcelo.gasfiteria@demo.keyserv', password: 'Demo1234' };

export async function login(page: Page, credenciales: { email: string; password: string }): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill(credenciales.email);
  await page.getByLabel('Contraseña').fill(credenciales.password);
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await expect(page).toHaveURL(/\/home/);
  await expect(page.getByRole('heading', { name: /^Hola,/ })).toBeVisible();
}
