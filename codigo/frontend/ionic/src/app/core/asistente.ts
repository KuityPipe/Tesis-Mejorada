import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface MensajeAsistente {
  rol: 'user' | 'assistant';
  texto: string;
}

export interface ServicioSugerido {
  id: number;
  titulo: string;
  categoria: string;
  precio: number | null;
  comuna: string;
  puntuacion: number | null;
}

export interface RespuestaAsistente {
  respuesta: string;
  servicios: ServicioSugerido[];
  origen: 'ia' | 'guiado';
  aviso_ia: string;
  sugerencias: string[];
}

/**
 * Asistente de preguntas frecuentes y búsqueda de servicios — `POST /api/asistente/` (ver
 * `KeyServApp/asistente.py`). El servidor enmascara RUT/correo/teléfono antes de hablar con el proveedor de IA
 * y no usa ningún dato de la cuenta; el historial vive solo en memoria del componente (no se guarda).
 */
@Injectable({ providedIn: 'root' })
export class Asistente {
  constructor(private readonly http: HttpClient) {}

  preguntar(mensajes: MensajeAsistente[]): Observable<RespuestaAsistente> {
    return this.http.post<RespuestaAsistente>(`${environment.apiUrl}/asistente/`, { mensajes });
  }
}
