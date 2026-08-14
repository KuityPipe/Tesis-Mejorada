import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Auth } from './auth';

/**
 * Guard funcional de ruta (`CanActivateFn`) — Angular lo corre *antes* de
 * activar la ruta que lo tiene asignado (ver `canActivate: [authGuard]`
 * en `app-routing.module.ts`, puesto en la ruta `home`). Si devuelve
 * `false`, la navegación se cancela ahí mismo — la página protegida ni
 * siquiera llega a construirse.
 *
 * Sin sesión, en vez de solo bloquear, redirige a `/login` — mismo
 * espíritu que `login_requerido` (decorators.py) del lado Django, pero acá
 * la redirección es explícita (`Router.navigateByUrl`) porque no hay un
 * mecanismo de "next querystring" implementado todavía.
 */
export const authGuard: CanActivateFn = () => {
  if (inject(Auth).estaAutenticado()) {
    return true;
  }

  inject(Router).navigateByUrl('/login');
  return false;
};
