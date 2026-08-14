import { TestBed } from '@angular/core/testing';
import { CanActivateFn, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { authGuard } from './auth-guard';
import { Auth } from './auth';

describe('authGuard', () => {
  const executeGuard: CanActivateFn = (...guardParameters) =>
      TestBed.runInInjectionContext(() => authGuard(...guardParameters));

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule, RouterTestingModule] });
  });

  it('deja pasar cuando hay sesión', () => {
    spyOn(TestBed.inject(Auth), 'estaAutenticado').and.returnValue(true);

    expect(executeGuard(null as any, null as any)).toBeTrue();
  });

  it('redirige a /login cuando no hay sesión', () => {
    spyOn(TestBed.inject(Auth), 'estaAutenticado').and.returnValue(false);
    const router = TestBed.inject(Router);
    spyOn(router, 'navigateByUrl');

    expect(executeGuard(null as any, null as any)).toBeFalse();
    expect(router.navigateByUrl).toHaveBeenCalledWith('/login');
  });
});
