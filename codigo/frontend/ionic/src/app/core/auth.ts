import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';

const CLAVE_ACCESS_TOKEN = 'keyserv_access_token';
const CLAVE_REFRESH_TOKEN = 'keyserv_refresh_token';

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
}

interface RespuestaLogin {
  access_token: string;
  refresh_token: string;
  usuario: Usuario;
}

/**
 * Cliente de la API REST (KeyServApp/api/) para login/perfil — ver
 * "API + Ionic migration" en CLAUDE.md. Guarda los tokens en localStorage
 * (simple y suficiente mientras el target sea solo web; pasar a
 * @capacitor/preferences cuando haya build nativo real).
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
  constructor(private readonly http: HttpClient) {}

  login(email: string, password: string): Observable<RespuestaLogin> {
    return this.http
      .post<RespuestaLogin>(`${environment.apiUrl}/auth/login/`, { email, password })
      .pipe(tap((respuesta) => this.guardarTokens(respuesta.access_token, respuesta.refresh_token)));
  }

  me(): Observable<Usuario> {
    return this.http.get<Usuario>(`${environment.apiUrl}/auth/me/`);
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
