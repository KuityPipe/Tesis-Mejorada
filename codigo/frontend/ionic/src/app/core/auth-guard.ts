import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Auth } from './auth';

/** Protege rutas que requieren sesión — sin token, redirige a /login en vez de dejar pasar la navegación. */
export const authGuard: CanActivateFn = () => {
  if (inject(Auth).estaAutenticado()) {
    return true;
  }

  inject(Router).navigateByUrl('/login');
  return false;
};
