import { defineConfig, devices } from '@playwright/test';

/**
 * Tests E2E reales contra la app Ionic servida de verdad (`ng serve`, `:8100`) hablando con la
 * API Django real (`:8000`, con Postgres + datos demo ya sembrados vía `sembrar_datos_demo`) —
 * a diferencia de los tests unitarios (`ng test`), acá no se mockea `HttpClient`: es la misma
 * app que usaría una persona real, clickeada por un navegador real.
 *
 * Requiere que el backend (`manage.py runserver 8000`, con migraciones + datos demo aplicados)
 * ya esté corriendo — ver "E2E (Playwright)" en CLAUDE.md. El frontend (`ng serve`) lo levanta
 * este config solo si no está corriendo ya (`reuseExistingServer`), igual que un desarrollador
 * probando a mano no necesita reiniciar su propio `npm start`.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['list']] : 'list',
  timeout: 30_000,

  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:8100',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: {
    command: 'npm start',
    url: 'http://localhost:8100',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
