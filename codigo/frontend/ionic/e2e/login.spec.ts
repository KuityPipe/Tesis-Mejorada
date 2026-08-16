import { test, expect } from '@playwright/test';
import { login, CLIENTE_DEMO } from './fixtures';

test.describe('Login', () => {
  test('inicia sesión con una cuenta demo real y llega al dashboard', async ({ page }) => {
    await login(page, CLIENTE_DEMO);
  });

  test('credenciales incorrectas muestran un error y no navegan', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Correo electrónico').fill(CLIENTE_DEMO.email);
    await page.getByLabel('Contraseña').fill('contraseña-incorrecta');
    await page.getByRole('button', { name: 'Iniciar sesión' }).click();

    await expect(page.getByText(/incorrect|no coincide|inválid/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('una sesión sin iniciar es redirigida a /login al pedir una pantalla protegida', async ({ page }) => {
    await page.goto('/home');
    await expect(page).toHaveURL(/\/login/);
  });
});
