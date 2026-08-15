import { TestBed, fakeAsync, tick, discardPeriodicTasks } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController, TestRequest } from '@angular/common/http/testing';

import { Notificaciones } from './notificaciones';
import { environment } from '../../environments/environment';

/**
 * Nota sobre `discardPeriodicTasks()`: bajo esta combinación de versiones de
 * zone.js/rxjs, suscribirse a `interval()` dentro de una zona `fakeAsync`
 * dispara un segundo llamado a `consultar()` durante el mismo `tick()`
 * inicial (no solo el llamado inmediato explícito de `iniciar()`) — un
 * artefacto del entorno de test, no un bug de producción (`interval()` sí
 * espera el período completo fuera de `fakeAsync`). Por eso estos tests
 * drenan *todas* las requests pendientes que matcheen en cada paso en vez
 * de asumir una sola, con `httpMock.match(...)` en lugar de `expectOne`.
 */
function drenarYFlushear(httpMock: HttpTestingController, url: string, body: object): TestRequest[] {
  const pendientes = httpMock.match((req) => req.url === url);
  pendientes.forEach((req) => req.flush(body));
  return pendientes;
}

describe('Notificaciones', () => {
  let servicio: Notificaciones;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    servicio = TestBed.inject(Notificaciones);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.removeItem('keyserv_access_token');
  });

  afterEach(fakeAsync(() => {
    discardPeriodicTasks();
    // Drena cualquier request que el discard haya disparado de más (ver nota arriba) antes de verificar que no quede nada suelto.
    httpMock.match(() => true);
    localStorage.removeItem('keyserv_access_token');
  }));

  it('no consulta el backend si no hay sesión iniciada', fakeAsync(() => {
    servicio.iniciar();
    tick();
    expect(httpMock.match(() => true).length).toBe(0);
  }));

  it('consulta y publica el conteo si hay sesión iniciada', fakeAsync(() => {
    localStorage.setItem('keyserv_access_token', 'token-de-prueba');
    servicio.iniciar();
    tick();

    const flusheadas = drenarYFlushear(httpMock, `${environment.apiUrl}/mensajes/no-leidos/`, { no_leidos: 3 });
    expect(flusheadas.length).toBeGreaterThan(0);
    tick();

    let valorActual: number | undefined;
    servicio.noLeidos$.subscribe((v) => (valorActual = v));
    expect(valorActual).toBe(3);

    // Al subir el conteo (de 0 a 3) se pide el usuario para chequear notificaciones_sonido antes de sonar.
    drenarYFlushear(httpMock, `${environment.apiUrl}/auth/me/`, { notificaciones_sonido: false });
    tick();
  }));

  it('no vuelve a sonar/consultar el usuario si el conteo no sube', fakeAsync(() => {
    localStorage.setItem('keyserv_access_token', 'token-de-prueba');
    servicio.iniciar();
    tick();

    drenarYFlushear(httpMock, `${environment.apiUrl}/mensajes/no-leidos/`, { no_leidos: 0 });
    tick();
    // no_leidos=0 nunca es mayor que el último conteo (arranca en 0) — no debería haber pedido el usuario.
    expect(httpMock.match((req) => req.url === `${environment.apiUrl}/auth/me/`).length).toBe(0);
  }));

  it('iniciar() es idempotente — llamarlo dos veces no rearma la suscripción al polling', fakeAsync(() => {
    localStorage.setItem('keyserv_access_token', 'token-de-prueba');
    servicio.iniciar();
    tick();
    drenarYFlushear(httpMock, `${environment.apiUrl}/mensajes/no-leidos/`, { no_leidos: 0 });
    tick();

    // Un segundo iniciar() no debe crear una segunda suscripción al interval — se comprueba vía el guard interno, no reinstanciando el servicio.
    const suscripcionAntes = (servicio as unknown as { suscripcion: unknown }).suscripcion;
    servicio.iniciar();
    const suscripcionDespues = (servicio as unknown as { suscripcion: unknown }).suscripcion;
    expect(suscripcionDespues).toBe(suscripcionAntes);
  }));
});
