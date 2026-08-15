import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

// Campos de ConversacionResumenSerializer — mismos datos calculados que
// arma chat_view del lado Django (no son campos reales de Conversacion,
// ver el comentario en ese serializer).
export interface ConversacionResumen {
  id_conversacion: number;
  contratacion_id: number | null;
  publicacion_titulo: string | null;
  contratacion_estado: string | null;
  contraparte_nombre: string | null;
  no_leidos: number;
  ultimo_mensaje_contenido: string | null;
  ultimo_mensaje_fecha: string | null;
  ultimo_mensaje_es_propio: boolean;
}

/** Cliente de `GET /api/conversaciones/` (KeyServApp/api/views.py) — bandeja de entrada, ver `mensajes.page`. */
@Injectable({
  providedIn: 'root',
})
export class Conversaciones {
  constructor(private readonly http: HttpClient) {}

  listar(): Observable<ConversacionResumen[]> {
    return this.http.get<ConversacionResumen[]>(`${environment.apiUrl}/conversaciones/`);
  }

  /** `GET /api/mensajes/no-leidos/` — solo el total, para el polling del badge (ver core/notificaciones.ts). Más liviano que `listar()`, que trae preview de cada chat. */
  noLeidos(): Observable<{ no_leidos: number }> {
    return this.http.get<{ no_leidos: number }>(`${environment.apiUrl}/mensajes/no-leidos/`);
  }
}
