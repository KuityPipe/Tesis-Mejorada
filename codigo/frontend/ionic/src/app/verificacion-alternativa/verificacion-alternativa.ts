import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

/** Estado de la vía de identidad sin biometría (`/api/auth/verificacion-alternativa/`). */
export interface EstadoVerificacionAlternativa {
  identidad_verificada: boolean;
  estado: 'INICIADA' | 'PENDIENTE_REVISION' | 'APROBADA' | 'RECHAZADA' | null;
  advertencia: string;
  advertencia_aceptada: boolean;
  correo_verificado: boolean;
  documento_enviado: boolean;
  motivo_rechazo: string;
}

/**
 * Vía alternativa a la biometría: advertencia + código por correo + documento de identidad
 * revisado por el staff. Más lenta a propósito; la biometría del teléfono es la vía principal.
 */
@Injectable({
  providedIn: 'root',
})
export class VerificacionAlternativa {
  private readonly base = `${environment.apiUrl}/auth/verificacion-alternativa`;

  constructor(private readonly http: HttpClient) {}

  estado(): Observable<EstadoVerificacionAlternativa> {
    return this.http.get<EstadoVerificacionAlternativa>(`${this.base}/`);
  }

  iniciar(): Observable<EstadoVerificacionAlternativa> {
    return this.http.post<EstadoVerificacionAlternativa>(`${this.base}/iniciar/`, { acepto_advertencia: true });
  }

  confirmarCodigo(codigo: string): Observable<EstadoVerificacionAlternativa> {
    return this.http.post<EstadoVerificacionAlternativa>(`${this.base}/codigo/`, { codigo });
  }

  enviarDocumento(archivo: File): Observable<EstadoVerificacionAlternativa> {
    const formData = new FormData();
    formData.append('documento', archivo);
    return this.http.post<EstadoVerificacionAlternativa>(`${this.base}/documento/`, formData);
  }
}
