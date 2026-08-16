import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { finalize, Observable, shareReplay, tap, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { AlmacenamientoSeguro } from './almacenamiento-seguro';

const CLAVE_ACCESS_TOKEN = 'keyserv_access_token';
const CLAVE_REFRESH_TOKEN = 'keyserv_refresh_token';

// Los mismos campos que devuelve `UsuarioMeSerializer` en el backend
// (KeyServApp/api/serializers.py) — mantenerlos sincronizados a mano, ya
// que todavía no hay un cliente TypeScript generado desde el schema OpenAPI
// (`/api/schema/`, ver docs/PLAN_MIGRACION_IONIC.md).
export interface Usuario {
  id_usuario: number;
  rut_usuario: string;
  nombre_usuario: string;
  nombre2_usuario: string | null;
  apellido_usuario: string;
  apellido2_usuario: string | null;
  telefono: string;
  email: string;
  direccion_usuario: string;
  edad: number;
  es_proveedor: boolean;
  verificado_biometricamente: boolean;
  foto_perfil: string | null;
  areas_servicio: string;
  experiencia: string;
  notificaciones_sonido: boolean;
  // Agregados para precargar el cascade región→comuna de "editar perfil"
  // (perfil/editar/editar.page.ts) sin una request aparte — `comuna` es el
  // pk crudo (no un objeto anidado), `region` se deriva en el backend de
  // `comuna.region_id` (ver UsuarioMeSerializer.get_region).
  comuna: number | null;
  region: number | null;
}

// Igual que `DocumentoPerfilSerializer` (api/serializers.py) — solo lo
// necesario para listar/borrar, nunca el archivo en sí (la descarga sigue
// sin migrar, ver CLAUDE.md Known Issues).
export interface DocumentoPerfil {
  id_documento: number;
  nombre_documento: string;
  fecha_subida_documento: string;
}

interface RespuestaPerfilProveedor {
  usuario: Usuario;
  documentos_rechazados: string[];
}

interface RespuestaLogin {
  access_token: string;
  refresh_token: string;
  usuario: Usuario;
}

interface RespuestaRefresh {
  access_token: string;
  refresh_token: string;
}

// Mismos nombres de campo que `RegistroForm` (KeyServApp/forms.py) — el
// backend reusa ese Form directamente en vez de un serializer aparte (ver
// api/views.py `RegistroView`), así que el contrato es literalmente el
// mismo formulario de siempre, solo que ahora en JSON. `region`/`comuna`
// son los IDs (pk) elegidos en los <ion-select>, no objetos. No hay
// `tipo_cuenta` — ver comentario en forms.py sobre por qué ya no se elige
// al registrarse (era redundante con `es_proveedor`).
export interface DatosRegistro {
  rut: string;
  nombre1: string;
  nombre2?: string;
  apellido1: string;
  apellido2?: string;
  edad: number;
  telefono: string;
  email: string;
  direccion?: string;
  region: number;
  comuna: number;
  es_proveedor: boolean;
  password: string;
  password_confirm: string;
}

/**
 * Cliente de la API REST (KeyServApp/api/) para login/perfil — ver
 * "API + Ionic migration" en CLAUDE.md y docs/PLAN_MIGRACION_IONIC.md.
 *
 * `@Injectable({ providedIn: 'root' })` es el mecanismo de inyección de
 * dependencias (DI) de Angular: registra esta clase como un singleton a
 * nivel de toda la app — cualquier componente/servicio que la pida por
 * constructor (como hacen LoginPage y HomePage) recibe la misma instancia,
 * sin necesidad de declararla en ningún NgModule a mano (a diferencia de
 * componentes/páginas, que sí hay que `declarations: [...]` en su módulo).
 *
 * SEGURIDAD (Fase 7, "Hardening" — ver docs/PLAN_MIGRACION_IONIC.md): los
 * tokens ahora se persisten vía `AlmacenamientoSeguro` (Keychain en iOS,
 * Android Keystore en Android nativo — `capacitor-secure-storage-plugin`),
 * no directamente en `localStorage` como en las fases anteriores de la
 * migración (`localStorage` ni `@capacitor/preferences` cifran en disco).
 * En un build de navegador (no nativo) el propio plugin cae a su fallback
 * de `localStorage`, así que en ese contexto sigue sin ser un cifrado
 * real — no hay equivalente de Keychain/Keystore en un navegador, es una
 * limitación del entorno, no algo que este código pueda resolver.
 *
 * El acceso síncrono que necesitan `authInterceptor`/`authGuard` (agregar
 * el header `Authorization` o decidir si una ruta protegida puede activarse
 * no pueden esperar una Promise en el medio) se resuelve con una copia en
 * memoria (`accessTokenEnMemoria`/`refreshTokenEnMemoria`) que se carga una
 * sola vez desde `AlmacenamientoSeguro` en `inicializar()` — enganchado
 * como `APP_INITIALIZER` en `app.module.ts`, así que Angular no arranca el
 * router hasta que esa carga inicial (async) terminó, y ningún guard/
 * interceptor puede correr antes de que la memoria esté poblada. Después
 * de esa carga inicial, `login()`/`logout()`/etc. mantienen ambas copias
 * (memoria + almacenamiento seguro) sincronizadas en cada escritura.
 *
 * `estaAutenticado()` solo comprueba que exista un access token, no que
 * siga vigente — un token expirado recién se detecta cuando el backend
 * responde 401 a una request real; `authInterceptor` (Fase 7) es quien
 * reacciona a eso llamando a `refrescarToken()`, no este servicio por sí
 * solo (evita medir el reloj del cliente contra el del servidor).
 */
@Injectable({
  providedIn: 'root',
})
export class Auth {
  private accessTokenEnMemoria: string | null = null;
  private refreshTokenEnMemoria: string | null = null;

  /**
   * Fase 7 ("hardening"): comparte una única request de refresh en vuelo
   * entre todos los que la pidan al mismo tiempo — si tres requests reciben
   * 401 juntas, `authInterceptor` no dispara tres `POST /auth/refresh/`
   * (el primero rotaría el refresh token y dejaría a los otros dos con uno
   * ya revocado). `shareReplay(1)` hace que quien se suscriba mientras
   * sigue en vuelo reciba el mismo resultado, no una request nueva;
   * `finalize` limpia la referencia cuando termina (éxito o error) para
   * que la próxima vez sí dispare una request real.
   */
  private refrescoEnVuelo$: Observable<RespuestaRefresh> | null = null;

  // Inyección por constructor: Angular resuelve `HttpClient` solo (fue
  // registrado por `provideHttpClient(...)` en app.module.ts) y lo pasa
  // acá — no hace falta instanciarlo a mano en ningún lado.
  constructor(
    private readonly http: HttpClient,
    private readonly almacenamiento: AlmacenamientoSeguro,
  ) {}

  /**
   * `APP_INITIALIZER` (app.module.ts) llama esto una sola vez antes de que
   * Angular termine de bootstrapear — carga los tokens ya guardados de una
   * sesión anterior desde `AlmacenamientoSeguro` a la copia en memoria, así
   * `estaAutenticado()` da la respuesta correcta desde el primer guard que
   * corra, sin una carrera contra la carga async.
   */
  async inicializar(): Promise<void> {
    const [access, refresh] = await Promise.all([
      this.almacenamiento.obtener(CLAVE_ACCESS_TOKEN),
      this.almacenamiento.obtener(CLAVE_REFRESH_TOKEN),
    ]);
    this.accessTokenEnMemoria = access ?? null;
    this.refreshTokenEnMemoria = refresh ?? null;
  }

  /**
   * `HttpClient.post<T>` devuelve un `Observable<T>` (RxJS), no una
   * Promise: la request HTTP recién se dispara cuando alguien se
   * suscribe (ver `login.page.ts`, `.subscribe({...})`) — hasta entonces
   * esto es solo una "receta" de la request, no la request en sí.
   * `.pipe(tap(...))` deja pasar la respuesta sin transformarla, pero
   * ejecuta un efecto secundario (guardar los tokens) en el camino.
   */
  login(email: string, password: string): Observable<RespuestaLogin> {
    return this.http
      .post<RespuestaLogin>(`${environment.apiUrl}/auth/login/`, { email, password })
      .pipe(tap((respuesta) => this.guardarTokens(respuesta.access_token, respuesta.refresh_token)));
  }

  /**
   * `POST /api/auth/refresh/` (Fase 7) — la llama `authInterceptor` cuando
   * una request real devuelve 401, no por polling. El backend rota el
   * refresh token (el usado queda revocado), así que `guardarTokens` acá
   * es obligatorio, no solo una optimización: si no se guardara el
   * refresh token nuevo, el siguiente 401 fallaría con el viejo ya
   * revocado.
   */
  refrescarToken(): Observable<RespuestaRefresh> {
    if (this.refrescoEnVuelo$) {
      return this.refrescoEnVuelo$;
    }
    const refreshToken = this.refreshTokenEnMemoria;
    if (!refreshToken) {
      return throwError(() => new Error('No hay sesión que refrescar.'));
    }
    this.refrescoEnVuelo$ = this.http
      .post<RespuestaRefresh>(`${environment.apiUrl}/auth/refresh/`, { refresh_token: refreshToken })
      .pipe(
        tap((respuesta) => this.guardarTokens(respuesta.access_token, respuesta.refresh_token)),
        finalize(() => (this.refrescoEnVuelo$ = null)),
        shareReplay(1),
      );
    return this.refrescoEnVuelo$;
  }

  /** Síncrono, igual que `obtenerAccessToken()` — lo necesita `authInterceptor` para decidir si vale la pena intentar `refrescarToken()` o directamente dejar pasar el 401. */
  obtenerRefreshToken(): string | null {
    return this.refreshTokenEnMemoria;
  }

  /** El `Authorization: Bearer <token>` lo agrega `authInterceptor` (core/auth-interceptor.ts) — esta llamada no necesita pasarlo a mano. */
  me(): Observable<Usuario> {
    return this.http.get<Usuario>(`${environment.apiUrl}/auth/me/`);
  }

  /**
   * `POST /api/auth/registro/` — a propósito **no** guarda tokens ni deja
   * la sesión iniciada (mismo criterio que `register_view` del lado
   * template: "cuenta creada, ahora iniciá sesión"). Si el backend
   * responde 400, el body es el `form.errors` de Django tal cual
   * (`{ campo: ["mensaje"] }`, con errores generales bajo la clave
   * `"__all__"`) — `registro.page.ts` lo mapea a los controles del form.
   */
  registrar(datos: DatosRegistro): Observable<Usuario> {
    return this.http.post<Usuario>(`${environment.apiUrl}/auth/registro/`, datos);
  }

  /**
   * `PUT /api/auth/perfil/` — recibe un `FormData` (no un objeto plano
   * como `login`/`registrar`) porque puede incluir `foto_perfil` (un
   * archivo); `HttpClient` detecta un body `FormData` y arma el header
   * `Content-Type: multipart/form-data` con el boundary correcto solo —
   * si se lo pasara a mano quedaría mal formado. Ver `editar.page.ts`
   * para cómo se arma el `FormData`.
   */
  actualizarPerfil(datos: FormData): Observable<Usuario> {
    return this.http.put<Usuario>(`${environment.apiUrl}/auth/perfil/`, datos);
  }

  /**
   * `POST /api/auth/recuperar/` — Paso 1 de recuperación de contraseña.
   * La respuesta es siempre el mismo mensaje genérico, exista o no la
   * cuenta (mismo criterio que el backend, ver `RecuperarView`) — no hay
   * nada específico que mapear del lado del éxito, solo mostrarlo tal cual.
   */
  solicitarRecuperacion(email: string, telefono: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${environment.apiUrl}/auth/recuperar/`, { email, telefono });
  }

  /** `GET /api/auth/recuperar/confirmar/<token>/` — valida el link antes de mostrar el formulario de nueva contraseña (`confirmar.page.ts`). 404 si el token es inválido o venció. */
  validarTokenRecuperacion(token: string): Observable<{ valido: boolean }> {
    return this.http.get<{ valido: boolean }>(`${environment.apiUrl}/auth/recuperar/confirmar/${token}/`);
  }

  /** `POST /api/auth/recuperar/confirmar/<token>/` — Paso 2, elegir la contraseña nueva. Mismo formato de errores 400 que `registrar`. */
  confirmarRecuperacion(token: string, password: string, passwordConfirm: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${environment.apiUrl}/auth/recuperar/confirmar/${token}/`, {
      password,
      password_confirm: passwordConfirm,
    });
  }

  /**
   * `PUT /api/auth/perfil-proveedor/` — igual que `actualizarPerfil`, recibe
   * un `FormData` (áreas de servicio como campos `areas_servicio` repetidos
   * — `FormData.append` con la misma clave varias veces, no un array — más
   * `otra_area_servicio`/`experiencia`/`foto_perfil`/`documentos`, ver
   * `proveedor.page.ts`). La respuesta trae `documentos_rechazados`: los
   * certificados que no pasaron la validación del backend (formato/tamaño/
   * contenido) no tiran un 400 — el resto del perfil se guarda igual.
   */
  actualizarPerfilProveedor(datos: FormData): Observable<RespuestaPerfilProveedor> {
    return this.http.put<RespuestaPerfilProveedor>(`${environment.apiUrl}/auth/perfil-proveedor/`, datos);
  }

  /** `GET /api/auth/perfil-proveedor/documentos/` — certificados ya subidos del proveedor logueado. */
  documentosPerfil(): Observable<DocumentoPerfil[]> {
    return this.http.get<DocumentoPerfil[]>(`${environment.apiUrl}/auth/perfil-proveedor/documentos/`);
  }

  /** `DELETE /api/auth/perfil-proveedor/documentos/<id>/` — solo borra un certificado propio (el backend devuelve 404 para uno ajeno). */
  eliminarDocumentoPerfil(documentoId: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/auth/perfil-proveedor/documentos/${documentoId}/`);
  }

  /** `PUT /api/auth/preferencias/` — hoy el único toggle real (ver PreferenciasCuentaForm, backend). */
  actualizarPreferencias(notificacionesSonido: boolean): Observable<Usuario> {
    return this.http.put<Usuario>(`${environment.apiUrl}/auth/preferencias/`, { notificaciones_sonido: notificacionesSonido });
  }

  /** `POST /api/auth/cambiar-password/` — cambiar la contraseña estando logueado (a diferencia de `confirmarRecuperacion`, pide la contraseña actual). */
  cambiarPassword(passwordActual: string, password: string, passwordConfirm: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${environment.apiUrl}/auth/cambiar-password/`, {
      password_actual: passwordActual,
      password,
      password_confirm: passwordConfirm,
    });
  }

  /**
   * `POST /api/auth/alternar-proveedor/` — equivalente API de
   * `alternar_proveedor_view`: única forma de cambiar `es_proveedor`
   * después del registro. Sin body — invierte el booleano del lado del
   * servidor y devuelve el perfil ya actualizado.
   */
  alternarProveedor(): Observable<Usuario> {
    return this.http.post<Usuario>(`${environment.apiUrl}/auth/alternar-proveedor/`, {});
  }

  /**
   * `POST /api/auth/verificar-biometria-nativa/` — la llama
   * `biometria/biometria.page` recién después de que
   * `NativeBiometric.verifyIdentity()` (plugin Capacitor) confirmó la
   * huella/Face ID en el propio dispositivo. Alcanza con el JWT ya
   * autenticado (sin re-pedir la contraseña) — decisión tomada con el
   * usuario: el servidor nunca ve el dato biométrico en sí (se valida
   * enteramente en el enclave seguro del teléfono), así que la única
   * garantía real que puede pedir es una sesión ya válida.
   */
  verificarBiometriaNativa(): Observable<Usuario> {
    return this.http.post<Usuario>(`${environment.apiUrl}/auth/verificar-biometria-nativa/`, {});
  }

  /**
   * Limpia la copia en memoria de forma síncrona (así `estaAutenticado()`
   * ya da `false` para el siguiente guard/interceptor que corra, incluso
   * antes de que termine el borrado async) y dispara el borrado en
   * `AlmacenamientoSeguro` en segundo plano — ningún caller de este método
   * espera una Promise hoy (ver `home.page.ts`), así que mantenerlo
   * síncrono evita tocar esos call sites.
   *
   * Fase 7: también dispara `POST /api/auth/logout/` para revocar el
   * refresh token del lado del servidor — antes de esto, "cerrar sesión"
   * solo borraba los tokens del dispositivo, pero el refresh token seguía
   * técnicamente vigente en `TokenSesion` (alguien con acceso previo al
   * almacenamiento del dispositivo, o un backup de él, lo podría haber
   * copiado antes del logout). Fire-and-forget: no hay nada útil que hacer
   * si esta llamada falla (el logout local ya pasó) más que loguear el
   * error, y ningún caller necesita esperarla.
   */
  logout(): void {
    const refreshToken = this.refreshTokenEnMemoria;
    this.accessTokenEnMemoria = null;
    this.refreshTokenEnMemoria = null;
    void this.almacenamiento.eliminar(CLAVE_ACCESS_TOKEN);
    void this.almacenamiento.eliminar(CLAVE_REFRESH_TOKEN);
    if (refreshToken) {
      this.http.post(`${environment.apiUrl}/auth/logout/`, { refresh_token: refreshToken }).subscribe({ error: () => {} });
    }
  }

  estaAutenticado(): boolean {
    return !!this.accessTokenEnMemoria;
  }

  /** Síncrono a propósito — lo usan `authInterceptor`/`authGuard`, que no pueden esperar una Promise en el medio de una request/navegación. Lee la copia en memoria, poblada por `inicializar()` al arrancar la app. */
  obtenerAccessToken(): string | null {
    return this.accessTokenEnMemoria;
  }

  /** Igual que `logout()`: actualiza la memoria en el momento (síncrono, dentro del `tap` de `login()`) y persiste en `AlmacenamientoSeguro` en segundo plano. */
  private guardarTokens(accessToken: string, refreshToken: string): void {
    this.accessTokenEnMemoria = accessToken;
    this.refreshTokenEnMemoria = refreshToken;
    void this.almacenamiento.guardar(CLAVE_ACCESS_TOKEN, accessToken);
    void this.almacenamiento.guardar(CLAVE_REFRESH_TOKEN, refreshToken);
  }
}
