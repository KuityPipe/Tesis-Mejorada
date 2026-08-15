import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

// Mismos campos que ProveedorSerializer (KeyServApp/api/serializers.py).
// `puntuacion_promedio` llega como string ("4.50") — DRF serializa
// DecimalField como texto por defecto (COERCE_DECIMAL_TO_STRING), para no
// perder precisión al pasar por JSON (que solo tiene "number" de punto
// flotante, sin decimales exactos).
export interface Proveedor {
  id_usuario: number;
  nombre_usuario: string;
  apellido_usuario: string;
  foto_perfil: string | null;
  comuna: string | null;
  region: string | null;
  puntuacion_promedio: string | null;
  total_valoraciones: number;
}

// Campos de PublicacionListSerializer — versión liviana para el listado.
export interface PublicacionResumen {
  id_publicacion: number;
  titulo: string;
  sub_titulo: string | null;
  categoria: string | null;
  precio: number | null;
  fecha_publicacion: string;
  imagen_portada: string | null;
  proveedor: Proveedor;
}

export interface Imagen {
  id_imagen: number;
  url: string | null;
}

export interface Resena {
  id_valoracion: number;
  puntuacion: number;
  comentario: string | null;
  fecha_valoracion: string;
  usuario_emisor: string;
}

// Campos de PublicacionDetailSerializer — el detalle trae todas las
// imágenes (no solo la portada) y las reseñas ya moderadas.
export interface PublicacionDetalle {
  id_publicacion: number;
  titulo: string;
  sub_titulo: string | null;
  descripcion_publicacion: string | null;
  categoria: string | null;
  precio: number | null;
  fecha_publicacion: string;
  imagenes: Imagen[];
  proveedor: Proveedor;
  resenas: Resena[];
}

// Campos de PublicacionPropiaSerializer — lo que muestra "Mis
// publicaciones" (antes, sección de perfil.html): a diferencia de
// PublicacionResumen, incluye el estado_moderacion real (pendiente/
// aprobada/rechazada) porque acá el dueño necesita verlo, no solo lo que
// ya está aprobado y visible al público.
export interface PublicacionPropia {
  id_publicacion: number;
  titulo: string;
  categoria: string | null;
  precio: number | null;
  fecha_publicacion: string;
  imagen_portada: string | null;
  estado_moderacion: 'PENDIENTE' | 'APROBADA' | 'RECHAZADA';
  estado_moderacion_display: string;
}

// Mismos campos que PublicacionForm (KeyServApp/forms.py) — el backend lo
// reusa directo en PublicacionCrearView, igual criterio que Auth.registrar.
export interface DatosPublicacion {
  titulo: string;
  sub_titulo?: string;
  descripcion_publicacion?: string;
  categoria: string;
  categoria_otra?: string;
  precio: number;
}

interface RespuestaCrearPublicacion {
  publicacion: PublicacionDetalle;
  imagenes_rechazadas: string[];
  documentos_rechazados: string[];
}

/** Forma estándar de una respuesta paginada de DRF (`PageNumberPagination`) — la misma para cualquier listado paginado de la API, no solo publicaciones. */
interface RespuestaPaginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FiltrosCatalogo {
  q?: string;
  region?: number | string;
  calificacion?: number | string;
  orden?: 'recientes' | 'calificacion';
}

/** Cliente de `/api/publicaciones/` — ver PublicacionListView/PublicacionDetailView (KeyServApp/api/views.py). Público: no pasa por authInterceptor con token porque no hace falta uno (endpoint AllowAny), aunque el interceptor igual se fijaría si hay uno guardado. */
@Injectable({
  providedIn: 'root',
})
export class Publicaciones {
  constructor(private readonly http: HttpClient) {}

  listar(pagina: number, filtros: FiltrosCatalogo = {}): Observable<RespuestaPaginada<PublicacionResumen>> {
    let params = new HttpParams().set('page', pagina);
    for (const [clave, valor] of Object.entries(filtros)) {
      if (valor !== undefined && valor !== '') {
        params = params.set(clave, String(valor));
      }
    }
    return this.http.get<RespuestaPaginada<PublicacionResumen>>(`${environment.apiUrl}/publicaciones/`, { params });
  }

  detalle(id: number): Observable<PublicacionDetalle> {
    return this.http.get<PublicacionDetalle>(`${environment.apiUrl}/publicaciones/${id}/`);
  }

  /** `GET /api/publicaciones/mias/` — publicaciones propias con cualquier estado_moderacion, requiere sesión (solo proveedores llegan a tener alguna). */
  mias(): Observable<PublicacionPropia[]> {
    return this.http.get<PublicacionPropia[]>(`${environment.apiUrl}/publicaciones/mias/`);
  }

  /**
   * `POST /api/publicaciones/crear/` — recibe `FormData` (no un objeto
   * plano) porque puede incluir `imagenes`/`documentos` (archivos
   * múltiples); `HttpClient` arma el `Content-Type: multipart/form-data`
   * solo, mismo criterio que `Auth.actualizarPerfilProveedor`.
   */
  crear(datos: FormData): Observable<RespuestaCrearPublicacion> {
    return this.http.post<RespuestaCrearPublicacion>(`${environment.apiUrl}/publicaciones/crear/`, datos);
  }
}
