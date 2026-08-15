import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

// Mismos campos que `ContactoForm` (KeyServApp/forms.py) — el backend lo
// reusa directo en `ContactoView` (api/views.py), igual criterio que
// `Auth.registrar`/`RegistroForm`.
export interface DatosContacto {
  asunto_consulta: string;
  descripcion: string;
  nombre_contacto?: string;
  email_contacto?: string;
}

/** Cliente de `POST /api/contacto/` — ver ContactoView (api/views.py) y contacto.page.ts. */
@Injectable({
  providedIn: 'root',
})
export class Contacto {
  constructor(private readonly http: HttpClient) {}

  enviar(datos: DatosContacto): Observable<{ detalle: string }> {
    return this.http.post<{ detalle: string }>(`${environment.apiUrl}/contacto/`, datos);
  }
}
