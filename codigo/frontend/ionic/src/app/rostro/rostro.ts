import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Usuario } from '../core/auth';

interface RespuestaEstadoRostro {
  tiene_referencia: boolean;
}

/**
 * Cliente de `/api/auth/rostro/*` (KeyServApp/api/views.py) — reconocimiento
 * facial por cámara, alternativa a la biometría nativa del dispositivo
 * (`biometria.ts`) para cuando esta última no está disponible (o viceversa
 * — RF001 trata ambos métodos como alternativos, no obligatorios los dos).
 * A diferencia de la biometría nativa, acá el navegador SÍ manda datos
 * biométricos reales al servidor (los cuadros de la cámara), por eso
 * `registrar()`/`verificar()` reciben un array de `File` — arma el
 * `FormData` con el mismo campo repetido `rostro_frames` que ya usaba el
 * template (`_captura_camara.html`), no el componente que llama a esto.
 */
@Injectable({
  providedIn: 'root',
})
export class Rostro {
  constructor(private readonly http: HttpClient) {}

  /** Si el usuario ya tiene un rostro de referencia guardado — nunca expone el encoding en sí, ver `RostroEstadoView`. */
  estado(): Observable<RespuestaEstadoRostro> {
    return this.http.get<RespuestaEstadoRostro>(`${environment.apiUrl}/auth/rostro/estado/`);
  }

  registrar(frames: File[]): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${environment.apiUrl}/auth/rostro/registrar/`, this.armarFormData(frames));
  }

  verificar(frames: File[]): Observable<Usuario> {
    return this.http.post<Usuario>(`${environment.apiUrl}/auth/rostro/verificar/`, this.armarFormData(frames));
  }

  private armarFormData(frames: File[]): FormData {
    const formData = new FormData();
    for (const frame of frames) {
      formData.append('rostro_frames', frame);
    }
    return formData;
  }
}
