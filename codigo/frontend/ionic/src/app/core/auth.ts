import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';

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

// Mismos nombres de campo que `RegistroForm` (KeyServApp/forms.py) — el
// backend reusa ese Form directamente en vez de un serializer aparte (ver
// api/views.py `RegistroView`), así que el contrato es literalmente el
// mismo formulario de siempre, solo que ahora en JSON. `region`/`comuna`/
// `tipo_cuenta` son los IDs (pk) elegidos en los <ion-select>, no objetos.
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
  tipo_cuenta: number;
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
 * SEGURIDAD (ver docs/PLAN_MIGRACION_IONIC.md, sección "Nota de
 * seguridad"): los tokens se guardan en `localStorage`, que **no está
 * cifrado en disco**. Esto es aceptable solo mientras el target sea el
 * navegador de desarrollo — antes de una build nativa real (Capacitor)
 * hay que migrar a un plugin de almacenamiento seguro respaldado por
 * Keychain (iOS) / Keystore (Android), no alcanza ni con `localStorage`
 * ni con `@capacitor/preferences` (ninguno de los dos cifra). Eso está
 * planeado para la fase de "Hardening" del plan de migración, no antes.
 *
 * `estaAutenticado()` solo comprueba que exista un access token, no que
 * siga vigente — todavía no hay endpoint de refresh (ver plan de
 * migración), así que un token expirado recién se detecta cuando el
 * backend responde 401 a una request real.
 */
@Injectable({
  providedIn: 'root',
})
export class Auth {
  // Inyección por constructor: Angular resuelve `HttpClient` solo (fue
  // registrado por `provideHttpClient(...)` en app.module.ts) y lo pasa
  // acá — no hace falta instanciarlo a mano en ningún lado.
  constructor(private readonly http: HttpClient) {}

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

  logout(): void {
    localStorage.removeItem(CLAVE_ACCESS_TOKEN);
    localStorage.removeItem(CLAVE_REFRESH_TOKEN);
  }

  estaAutenticado(): boolean {
    return !!this.obtenerAccessToken();
  }

  obtenerAccessToken(): string | null {
    return localStorage.getItem(CLAVE_ACCESS_TOKEN);
  }

  private guardarTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(CLAVE_ACCESS_TOKEN, accessToken);
    localStorage.setItem(CLAVE_REFRESH_TOKEN, refreshToken);
  }
}
