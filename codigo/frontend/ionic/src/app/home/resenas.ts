import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

// Campos de ResenaRecibidaSerializer — misma info que perfil.html muestra
// en "Reseñas y calificaciones recibidas" (más estado_moderacion, que
// Django no expone ahí pero Ionic sí usa para la misma nota "Pendiente
// de revisión" que ya tiene contratacion/detalle).
export interface ResenaRecibida {
  id_valoracion: number;
  puntuacion: number;
  comentario: string | null;
  fecha_valoracion: string;
  estado_moderacion: 'PENDIENTE' | 'APROBADA' | 'RECHAZADA';
  usuario_emisor: string;
}

/** Cliente de `GET /api/perfil/resenas-recibidas/` (KeyServApp/api/views.py) — ver home.page, sección "Reseñas recibidas". */
@Injectable({
  providedIn: 'root',
})
export class Resenas {
  constructor(private readonly http: HttpClient) {}

  recibidas(): Observable<ResenaRecibida[]> {
    return this.http.get<ResenaRecibida[]>(`${environment.apiUrl}/perfil/resenas-recibidas/`);
  }
}
