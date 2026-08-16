import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';

import { authInterceptor } from './auth-interceptor';
import { Auth } from './auth';
import { environment } from '../../environments/environment';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let auth: Auth;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(withInterceptors([authInterceptor])), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(Auth);
  });

  afterEach(() => httpMock.verify());

  it('agrega el header Authorization en requests a la API cuando hay token', () => {
    spyOn(auth, 'obtenerAccessToken').and.returnValue('un-token');

    http.get(`${environment.apiUrl}/auth/me/`).subscribe();

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
    expect(req.request.headers.get('Authorization')).toBe('Bearer un-token');
    req.flush({});
  });

  it('no toca requests fuera de la API', () => {
    spyOn(auth, 'obtenerAccessToken').and.returnValue('un-token');

    http.get('https://otro-servicio.cl/algo').subscribe();

    const req = httpMock.expectOne('https://otro-servicio.cl/algo');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('en un 401 con refresh token disponible, refresca y reintenta la request original con el token nuevo', () => {
    spyOn(auth, 'obtenerAccessToken').and.returnValue('token-vencido');
    spyOn(auth, 'obtenerRefreshToken').and.returnValue('un-refresh');
    spyOn(auth, 'refrescarToken').and.returnValue(of({ access_token: 'token-nuevo', refresh_token: 'refresh-nuevo' }));

    let resultado: unknown;
    http.get(`${environment.apiUrl}/auth/me/`).subscribe((r) => (resultado = r));

    const primerIntento = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
    expect(primerIntento.request.headers.get('Authorization')).toBe('Bearer token-vencido');
    primerIntento.flush({ detail: 'no autenticado' }, { status: 401, statusText: 'Unauthorized' });

    const reintento = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
    expect(reintento.request.headers.get('Authorization')).toBe('Bearer token-nuevo');
    reintento.flush({ ok: true });

    expect(resultado).toEqual({ ok: true });
  });

  it('si el refresh también falla, desloguea y propaga el error original', () => {
    spyOn(auth, 'obtenerAccessToken').and.returnValue('token-vencido');
    spyOn(auth, 'obtenerRefreshToken').and.returnValue('un-refresh');
    spyOn(auth, 'refrescarToken').and.returnValue(throwError(() => new Error('refresh vencido')));
    const logoutSpy = spyOn(auth, 'logout');

    let huboError = false;
    http.get(`${environment.apiUrl}/auth/me/`).subscribe({ error: () => (huboError = true) });

    httpMock.expectOne(`${environment.apiUrl}/auth/me/`).flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(huboError).toBeTrue();
    expect(logoutSpy).toHaveBeenCalled();
  });

  it('sin refresh token guardado, un 401 se propaga directo sin intentar refrescar', () => {
    spyOn(auth, 'obtenerAccessToken').and.returnValue('token-vencido');
    spyOn(auth, 'obtenerRefreshToken').and.returnValue(null);
    const refrescarSpy = spyOn(auth, 'refrescarToken');

    let huboError = false;
    http.get(`${environment.apiUrl}/auth/me/`).subscribe({ error: () => (huboError = true) });

    httpMock.expectOne(`${environment.apiUrl}/auth/me/`).flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(huboError).toBeTrue();
    expect(refrescarSpy).not.toHaveBeenCalled();
  });

  it('un 401 en /auth/login/ no dispara un intento de refresh (evita el loop y no es un token vencido)', () => {
    spyOn(auth, 'obtenerRefreshToken').and.returnValue('un-refresh');
    const refrescarSpy = spyOn(auth, 'refrescarToken');

    let huboError = false;
    http.post(`${environment.apiUrl}/auth/login/`, {}).subscribe({ error: () => (huboError = true) });

    httpMock
      .expectOne(`${environment.apiUrl}/auth/login/`)
      .flush({ detail: 'Correo o contraseña incorrectos.' }, { status: 401, statusText: 'Unauthorized' });

    expect(huboError).toBeTrue();
    expect(refrescarSpy).not.toHaveBeenCalled();
  });
});
