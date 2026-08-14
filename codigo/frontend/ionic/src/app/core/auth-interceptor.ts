import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { environment } from '../../environments/environment';
import { Auth } from './auth';

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
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiUrl)) {
    return next(req);
  }

  const token = inject(Auth).obtenerAccessToken();
  if (!token) {
    return next(req);
  }

  // Las `HttpRequest` son inmutables — `.clone()` devuelve una copia con
  // el header agregado en vez de mutar `req` (Angular podría estar
  // reintentando o cacheando la request original en otro lado).
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
