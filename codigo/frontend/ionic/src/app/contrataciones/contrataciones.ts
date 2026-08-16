import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

// Mismos campos que HistorialEstadoSerializer/ItemPresupuestoSerializer/
// ValoracionImagenSerializer/ValoracionSerializer (KeyServApp/api/serializers.py).
export interface HistorialEstado {
  estado: string;
  fecha: string;
}

export interface ItemPresupuesto {
  id_item_presupuesto: number;
  descripcion: string;
  categoria: string;
  monto: number;
  orden: number;
}

export interface ValoracionImagen {
  id_valoracion_imagen: number;
  url: string | null;
  estado_moderacion: string;
}

export interface ValoracionDetalle {
  id_valoracion: number;
  puntuacion: number;
  comentario: string | null;
  fecha_valoracion: string;
  estado_moderacion: string;
  imagenes: ValoracionImagen[];
}

// Campos de ContratacionListSerializer — `cliente`/`proveedor` son el pk
// plano: el rol propio ("¿soy cliente o proveedor acá?") se resuelve
// comparando contra `Auth.me()`, no viene calculado desde el backend.
export interface ContratacionResumen {
  id_contratacion: number;
  estado: string;
  monto_acordado: number | null;
  fecha_creacion: string;
  publicacion: number;
  publicacion_titulo: string;
  publicacion_imagen: string | null;
  cliente: number;
  cliente_nombre: string;
  proveedor: number;
  proveedor_nombre: string;
  tiene_valoracion: boolean;
}

// Igual que PagoSerializer (api/serializers.py).
export interface Pago {
  id_pago: number;
  metodo: 'WEBPAY' | 'KHIPU';
  estado: 'PENDIENTE' | 'PAGADO' | 'RECHAZADO' | 'ANULADO';
  monto: number;
  fecha_creacion: string;
  fecha_confirmacion: string | null;
}

// Campos extra de ContratacionDetailSerializer.
export interface ContratacionDetalle extends ContratacionResumen {
  historial: HistorialEstado[];
  items_presupuesto: ItemPresupuesto[];
  valoracion: ValoracionDetalle | null;
  pago: Pago | null;
  publicacion_descripcion: string | null;
  publicacion_imagenes: string[];
}

export interface Mensaje {
  id_mensaje: number;
  contenido: string | null;
  fecha_envio: string;
  usuario: number;
  usuario_nombre: string;
  /** `null` si el mensaje no tiene foto adjunta (Fase 7) — nunca una URL de /media/ directa, la storage es privada del lado del backend (ver ContratacionMensajeImagenView). */
  imagen_url: string | null;
}

interface RespuestaValoracion {
  valoracion: ValoracionDetalle;
  imagenes_rechazadas: string[];
}

/**
 * Cliente de `/api/contrataciones/*` (KeyServApp/api/views.py) — núcleo
 * transaccional (Fase 4 del plan de migración): solicitar, ver detalle,
 * chatear, confirmar/completar (con reautenticación) y valorar. Los pagos
 * (Webpay/Khipu) son la última pieza de esta fase, todavía no migrados —
 * `EN_CURSO` hoy solo se alcanza confirmando manualmente contra la BD o
 * desde el sitio Django mientras tanto.
 */
@Injectable({
  providedIn: 'root',
})
export class Contrataciones {
  constructor(private readonly http: HttpClient) {}

  listar(): Observable<ContratacionResumen[]> {
    return this.http.get<ContratacionResumen[]>(`${environment.apiUrl}/contrataciones/`);
  }

  /** `POST /api/contrataciones/` — "solicitar" un servicio (SOLICITADA), equivalente de `contratacion_crear_view`. */
  solicitar(publicacionId: number): Observable<ContratacionDetalle> {
    return this.http.post<ContratacionDetalle>(`${environment.apiUrl}/contrataciones/`, { publicacion: publicacionId });
  }

  detalle(id: number): Observable<ContratacionDetalle> {
    return this.http.get<ContratacionDetalle>(`${environment.apiUrl}/contrataciones/${id}/`);
  }

  /** También marca la conversación como leída por quien pide esto, igual que `contratacion_detalle_view`. */
  mensajes(id: number): Observable<Mensaje[]> {
    return this.http.get<Mensaje[]>(`${environment.apiUrl}/contrataciones/${id}/mensajes/`);
  }

  /**
   * `FormData`, no un objeto plano (Fase 7: foto adjunta) — mismo criterio
   * que `Auth.actualizarPerfil`/`Publicaciones.crear`: `HttpClient` arma
   * `Content-Type: multipart/form-data` con el boundary correcto solo, a
   * mano quedaría mal formado. `contenido`/`imagen` son ambos opcionales
   * acá (el backend exige al menos uno de los dos) — un mensaje puede ser
   * solo una foto, sin texto.
   */
  enviarMensaje(id: number, contenido: string, imagen?: File): Observable<Mensaje> {
    const formData = new FormData();
    if (contenido) {
      formData.set('contenido', contenido);
    }
    if (imagen) {
      formData.set('imagen', imagen);
    }
    return this.http.post<Mensaje>(`${environment.apiUrl}/contrataciones/${id}/mensajes/`, formData);
  }

  /** El PROVEEDOR confirma (SOLICITADA -> CONFIRMADA), re-ingresando su contraseña. `monto` es opcional — sin él, se usa el precio de la publicación. */
  confirmar(id: number, password: string, monto?: number): Observable<ContratacionDetalle> {
    return this.http.post<ContratacionDetalle>(`${environment.apiUrl}/contrataciones/${id}/confirmar/`, { password, monto });
  }

  /** El CLIENTE marca el servicio como completado (EN_CURSO -> COMPLETADA), re-ingresando su contraseña. */
  completar(id: number, password: string): Observable<ContratacionDetalle> {
    return this.http.post<ContratacionDetalle>(`${environment.apiUrl}/contrataciones/${id}/completar/`, { password });
  }

  /** `datos` es un FormData (`puntuacion`, `comentario`, opcionalmente varios `imagenes`) — mismo motivo que `Auth.actualizarPerfil`, puede llevar archivos. */
  valorar(id: number, datos: FormData): Observable<RespuestaValoracion> {
    return this.http.post<RespuestaValoracion>(`${environment.apiUrl}/contrataciones/${id}/valoracion/`, datos);
  }

  /**
   * Mismo mapeo estado→color que `.ks-badge-*` en base.css del sitio
   * Django: coral (`tertiary`) para lo que espera acción, teal
   * (`secondary`) para confirmada/en curso, navy (`primary`) para
   * completada, gris (`medium`) para rechazada/cancelada. Vive acá (no
   * duplicado en reservas.page.ts/detalle.page.ts) porque ambas pantallas
   * necesitan exactamente el mismo criterio.
   */
  colorEstado(estado: string | undefined): string {
    switch (estado) {
      case 'SOLICITADA':
        return 'tertiary';
      case 'CONFIRMADA':
      case 'EN_CURSO':
        return 'secondary';
      case 'COMPLETADA':
        return 'primary';
      default:
        return 'medium';
    }
  }

  /**
   * Mismo texto que `Contratacion.get_estado_display()` (models.py,
   * ESTADOS_CONTRATACION) — Django no muestra el código crudo del estado
   * en ningún badge, siempre la etiqueta descriptiva ("Confirmada por el
   * proveedor", no "CONFIRMADA"). Vive acá junto a `colorEstado` por el
   * mismo motivo: varias pantallas (home, reservas, detalle) necesitan el
   * mismo criterio.
   */
  etiquetaEstado(estado: string | undefined): string {
    switch (estado) {
      case 'SOLICITADA':
        return 'Solicitada por el cliente';
      case 'CONFIRMADA':
        return 'Confirmada por el proveedor';
      case 'EN_CURSO':
        return 'Servicio en curso';
      case 'COMPLETADA':
        return 'Completada';
      case 'CANCELADA':
        return 'Cancelada';
      default:
        return estado ?? '';
    }
  }
}
