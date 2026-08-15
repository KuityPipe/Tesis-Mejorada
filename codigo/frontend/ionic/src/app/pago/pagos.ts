import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

interface RespuestaIniciarWebpay {
  token: string;
  url_pago: string;
}

interface RespuestaConfirmarWebpay {
  aprobado: boolean;
  mensaje: string;
  contratacion_id: number | null;
}

interface RespuestaIniciarKhipu {
  payment_url: string;
}

interface RespuestaEstadoPago {
  aprobado: boolean;
  mensaje: string;
}

// Campos de PagoHistorialSerializer — a diferencia de los tipos de arriba
// (que son respuestas puntuales del flujo de pago en sí), esto es lo que
// lista /perfil/pagos (equivalente Ionic de historial_pagos.html).
export interface PagoHistorial {
  id_pago: number;
  metodo: 'WEBPAY' | 'KHIPU';
  estado: 'PENDIENTE' | 'PAGADO' | 'RECHAZADO' | 'ANULADO';
  monto: number;
  fecha_creacion: string;
  fecha_confirmacion: string | null;
  contratacion_id: number;
  publicacion_titulo: string;
}

/**
 * Cliente de `/api/contrataciones/<id>/pagos/*` + `/api/pagos/webpay/confirmar/`
 * (KeyServApp/api/views.py) — última pieza de Fase 4 del plan de
 * migración. El pago en sí siempre implica una navegación completa fuera
 * de la SPA (a Transbank o a Khipu) — este servicio solo arma/lee las
 * requests a la API, la navegación real la maneja quien lo llama
 * (`contratacion/detalle/detalle.page`, `pago/webpay/retorno`,
 * `pago/khipu/retorno`).
 */
@Injectable({
  providedIn: 'root',
})
export class Pagos {
  constructor(private readonly http: HttpClient) {}

  /** Crea la transacción en Transbank — el `<form>` que hace el POST real a `url_pago` (Transbank exige POST, no un GET común) se arma en el propio componente que llama a esto. */
  iniciarWebpay(contratacionId: number): Observable<RespuestaIniciarWebpay> {
    return this.http.post<RespuestaIniciarWebpay>(`${environment.apiUrl}/contrataciones/${contratacionId}/pagos/webpay/iniciar/`, {});
  }

  /** Sin token JWT — mismo criterio que el backend (`PagoWebpayConfirmarView`, `AllowAny`): quien vuelve de Transbank puede tener una sesión vencida tras el rato afuera de la SPA. */
  confirmarWebpay(datos: { token_ws?: string; TBK_TOKEN?: string }): Observable<RespuestaConfirmarWebpay> {
    return this.http.post<RespuestaConfirmarWebpay>(`${environment.apiUrl}/pagos/webpay/confirmar/`, datos);
  }

  iniciarKhipu(contratacionId: number): Observable<RespuestaIniciarKhipu> {
    return this.http.post<RespuestaIniciarKhipu>(`${environment.apiUrl}/contrataciones/${contratacionId}/pagos/khipu/iniciar/`, {});
  }

  /** Reconsulta contra Khipu si el pago sigue pendiente — la fuente de verdad real es el webhook servidor-a-servidor (que sigue en Django, nunca lo llama el navegador), esto es solo para no hacer esperar al usuario. */
  estadoKhipu(contratacionId: number): Observable<RespuestaEstadoPago> {
    return this.http.get<RespuestaEstadoPago>(`${environment.apiUrl}/contrataciones/${contratacionId}/pagos/khipu/estado/`);
  }

  /** `GET /api/pagos/historial/` — equivalente API de `historial_pagos_view`, ver `perfil/pagos/pagos.page`. */
  historial(): Observable<PagoHistorial[]> {
    return this.http.get<PagoHistorial[]>(`${environment.apiUrl}/pagos/historial/`);
  }
}
