import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { Auth } from './auth';

/** Rutas que nunca disparan un intento de refresh — evita el loop obvio (un 401 de /auth/refresh/ reintentando /auth/refresh/) y el caso real de LoginView devolviendo 401 por "correo o contraseña incorrectos", que no tiene nada que ver con un token vencido. */
const RUTAS_SIN_REINTENTO = [`${environment.apiUrl}/auth/login/`, `${environment.apiUrl}/auth/refresh/`];

/**
 * Interceptor HTTP funcional (la forma moderna en Angular ≥15; la
 * alternativa vieja era una clase que implementa `HttpInterceptor` y se
 * registra con el multi-provider `HTTP_INTERCEPTORS`). Angular pasa por
 * acá **toda** request que sale por `HttpClient`, sin importar qué
 * servicio la disparó — es el lugar correcto para agregar un header común
 * en un solo sitio en vez de repetirlo en cada llamada a la API.
 *
 * Se registra una sola vez en app.module.ts:
 * `provideHttpClient(withInterceptors([authInterceptor]))`.
 *
 * `inject(Auth)` (en vez de recibirlo por constructor) es la forma de
 * pedir DI dentro de una función suelta, no de una clase — los
 * interceptors funcionales no tienen constructor.
 *
 * Agrega `Authorization: Bearer <token>` solo a las requests hacia la API
 * propia — nunca a otros orígenes (ej. si en el futuro se pide una imagen
 * desde un CDN externo, no le llegaría el token por error).
 *
 * Fase 7 ("hardening"): además, si una request protegida vuelve con 401
 * (access token vencido — ver JWTAuthentication en el backend, un token
 * vencido se trata como "sin credenciales", así que `IsAuthenticated` es
 * quien responde el 401, no una excepción de autenticación dura), intenta
 * `Auth.refrescarToken()` una vez y reintenta la request original con el
 * access token nuevo. Si el refresh también falla (refresh token vencido
 * o ya revocado), `Auth.logout()` limpia la sesión local — no navega a
 * `/login` a mano: el próximo guard que corra (`authGuard`) ya la va a
 * redirigir, y navegar desde acá duplicaría esa responsabilidad.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiUrl)) {
    return next(req);
  }

  const auth = inject(Auth);
  const token = auth.obtenerAccessToken();
  const request = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(request).pipe(
    catchError((error: unknown) => {
      const puedeReintentar =
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !RUTAS_SIN_REINTENTO.includes(req.url) &&
        !!auth.obtenerRefreshToken();

      if (!puedeReintentar) {
        return throwError(() => error);
      }

      return auth.refrescarToken().pipe(
        switchMap((respuesta) => next(req.clone({ setHeaders: { Authorization: `Bearer ${respuesta.access_token}` } }))),
        catchError((errorDeRefresh: unknown) => {
          auth.logout();
          return throwError(() => errorDeRefresh);
        }),
      );
    }),
  );
};
