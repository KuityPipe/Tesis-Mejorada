import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { Auth } from './auth';
import { AlmacenamientoSeguro } from './almacenamiento-seguro';
import { environment } from '../../environments/environment';

describe('Auth', () => {
  let service: Auth;
  let almacenamiento: AlmacenamientoSeguro;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Auth);
    almacenamiento = TestBed.inject(AlmacenamientoSeguro);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('inicializar() carga los tokens guardados en AlmacenamientoSeguro a la copia en memoria', async () => {
    spyOn(almacenamiento, 'obtener').and.callFake((clave: string) =>
      Promise.resolve(clave.includes('refresh') ? 'un-refresh-token' : 'un-access-token'),
    );

    await service.inicializar();

    expect(service.estaAutenticado()).toBeTrue();
    expect(service.obtenerAccessToken()).toBe('un-access-token');
  });

  it('inicializar() deja la sesión como no autenticada si no había tokens guardados (primera vez / logout previo)', async () => {
    spyOn(almacenamiento, 'obtener').and.returnValue(Promise.resolve(undefined));

    await service.inicializar();

    expect(service.estaAutenticado()).toBeFalse();
    expect(service.obtenerAccessToken()).toBeNull();
  });

  it('login() deja la sesión autenticada de inmediato (en memoria) y persiste los tokens en AlmacenamientoSeguro', () => {
    const guardarSpy = spyOn(almacenamiento, 'guardar').and.returnValue(Promise.resolve());

    service.login('demo@keyserv.cl', 'clave').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
    req.flush({ access_token: 'nuevo-access', refresh_token: 'nuevo-refresh', usuario: {} });

    expect(service.estaAutenticado()).toBeTrue();
    expect(service.obtenerAccessToken()).toBe('nuevo-access');
    expect(guardarSpy).toHaveBeenCalledWith(jasmine.stringMatching(/access/), 'nuevo-access');
    expect(guardarSpy).toHaveBeenCalledWith(jasmine.stringMatching(/refresh/), 'nuevo-refresh');
  });

  it('logout() limpia la sesión en memoria de inmediato y pide borrar ambos tokens del almacenamiento seguro', () => {
    const eliminarSpy = spyOn(almacenamiento, 'eliminar').and.returnValue(Promise.resolve());
    spyOn(almacenamiento, 'guardar').and.returnValue(Promise.resolve());

    service.login('demo@keyserv.cl', 'clave').subscribe();
    httpMock.expectOne(`${environment.apiUrl}/auth/login/`).flush({ access_token: 'a', refresh_token: 'r', usuario: {} });
    expect(service.estaAutenticado()).toBeTrue();

    service.logout();

    expect(service.estaAutenticado()).toBeFalse();
    expect(service.obtenerAccessToken()).toBeNull();
    expect(eliminarSpy).toHaveBeenCalledTimes(2);
  });
});
