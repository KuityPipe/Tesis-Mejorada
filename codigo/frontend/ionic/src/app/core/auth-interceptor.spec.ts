import { TestBed } from '@angular/core/testing';
import { HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { authInterceptor } from './auth-interceptor';
import { Auth } from './auth';
import { environment } from '../../environments/environment';

describe('authInterceptor', () => {
  const interceptor: HttpInterceptorFn = (req, next) =>
    TestBed.runInInjectionContext(() => authInterceptor(req, next));

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
  });

  it('agrega el header Authorization en requests a la API cuando hay token', () => {
    spyOn(TestBed.inject(Auth), 'obtenerAccessToken').and.returnValue('un-token');
    const request = new HttpRequest('GET', `${environment.apiUrl}/auth/me/`);
    const next = jasmine.createSpy('next').and.callFake((r: HttpRequest<unknown>) => r as any);

    interceptor(request, next);

    const requestEnviada = next.calls.mostRecent().args[0] as HttpRequest<unknown>;
    expect(requestEnviada.headers.get('Authorization')).toBe('Bearer un-token');
  });

  it('no toca requests fuera de la API', () => {
    spyOn(TestBed.inject(Auth), 'obtenerAccessToken').and.returnValue('un-token');
    const request = new HttpRequest('GET', 'https://otro-servicio.cl/algo');
    const next = jasmine.createSpy('next').and.callFake((r: HttpRequest<unknown>) => r as any);

    interceptor(request, next);

    expect(next).toHaveBeenCalledWith(request);
  });
});
