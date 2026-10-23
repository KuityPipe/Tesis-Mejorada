import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export type Documento = 'SIN_DOCUMENTO' | 'BOLETA_HONORARIOS';

export interface MaterialValorizacion {
  descripcion: string;
  cantidad: number;
  unidad: string;
  precio_unitario: number;
  reutilizado: boolean;
}

/** Cuerpo que entiende `POST /api/calculadora/calcular/` (ver KeyServApp/calculadora.py). */
export interface DatosValorizacion {
  materiales: MaterialValorizacion[];
  traslado: { modo: 'km' | 'fijo'; km_ida_vuelta: number; costo_km: number; monto_fijo: number; peajes_estacionamiento: number };
  mano_obra: { horas: number; valor_hora: number; personas: number };
  herramientas: { modo: 'monto' | 'porcentaje'; monto: number; porcentaje: number };
  imprevistos_pct: number;
  ganancia_pct: number;
  documento: Documento;
}

export interface ItemValorizacion {
  descripcion: string;
  categoria: string;
  monto: number;
  cantidad?: number;
  unidad?: string;
  precio_unitario?: number;
  reutilizado?: boolean;
}

export interface ResultadoValorizacion {
  materiales_total: number;
  traslado_total: number;
  mano_obra_total: number;
  herramientas_total: number;
  costo_directo: number;
  imprevistos_pct: number;
  imprevistos_monto: number;
  ganancia_pct: number;
  ganancia_monto: number;
  precio_neto: number;
  documento: Documento;
  retencion_pct: number;
  retencion_monto: number;
  precio_boleta: number;
  liquido: number;
  comision_porcentaje: number;
  comision_monto: number;
  total_cliente: number;
  tiene_reutilizado: boolean;
  items: ItemValorizacion[];
}

export interface ConfigCalculadora {
  retencion_porcentaje: number;
  imprevistos_porcentaje: number;
  ganancia_porcentaje: number;
  comision_tramos: [number | null, number][];
  comision_minima: number;
}

export interface PlantillaValorizacion {
  id_plantilla: number;
  nombre: string;
  tipo_trabajo: string;
  datos: DatosValorizacion;
  actualizada_en: string;
}

const CLAVE_VISITANTE = 'ks_visitante_calculadora';

/**
 * Valor por hora que hace falta para llegar a un ingreso mensual deseado trabajando `horasCobrables` horas al mes
 * (las horas que de verdad se cobran, no las de toda la jornada). Redondea hacia arriba al peso.
 */
export function valorHora(ingresoMensualDeseado: number, horasCobrablesAlMes: number): number {
  if (!(ingresoMensualDeseado > 0) || !(horasCobrablesAlMes > 0)) {
    return 0;
  }
  return Math.ceil(ingresoMensualDeseado / horasCobrablesAlMes);
}

/**
 * Cliente de `/api/calculadora/*` (KeyServ, bloque 2). El cálculo y las exportaciones son públicos: no piden cuenta.
 * Para el contador anónimo de uso se manda un identificador aleatorio que se guarda solo en este navegador; el servidor
 * lo mezcla con una sal secreta y el mes, así que no sirve para reconocer a nadie.
 */
@Injectable({ providedIn: 'root' })
export class Calculadora {
  constructor(private readonly http: HttpClient) {}

  private get base(): string {
    return `${environment.apiUrl}/calculadora`;
  }

  /** Identificador aleatorio de este navegador (sin relación con ninguna cuenta). Si no hay almacenamiento, uno por visita. */
  visitante(): string {
    try {
      const guardado = localStorage.getItem(CLAVE_VISITANTE);
      if (guardado) {
        return guardado;
      }
      const nuevo = this.nuevoIdentificador();
      localStorage.setItem(CLAVE_VISITANTE, nuevo);
      return nuevo;
    } catch {
      return this.nuevoIdentificador();
    }
  }

  private nuevoIdentificador(): string {
    return typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `v${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
  }

  config(): Observable<ConfigCalculadora> {
    return this.http.get<ConfigCalculadora>(`${this.base}/config/`);
  }

  calcular(datos: DatosValorizacion): Observable<ResultadoValorizacion> {
    return this.http.post<ResultadoValorizacion>(`${this.base}/calcular/`, { ...datos, visitante: this.visitante() });
  }

  exportar(tipo: 'pdf' | 'xlsx', datos: DatosValorizacion): Observable<Blob> {
    return this.http.post(`${this.base}/exportar/${tipo}/`, { ...datos, visitante: this.visitante() }, { responseType: 'blob' });
  }

  plantillas(): Observable<PlantillaValorizacion[]> {
    return this.http.get<PlantillaValorizacion[]>(`${this.base}/plantillas/`);
  }

  guardarPlantilla(nombre: string, tipoTrabajo: string, datos: DatosValorizacion): Observable<PlantillaValorizacion> {
    return this.http.post<PlantillaValorizacion>(`${this.base}/plantillas/`, { nombre, tipo_trabajo: tipoTrabajo, datos, visitante: this.visitante() });
  }

  eliminarPlantilla(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/plantillas/${id}/`);
  }

  /** La plantilla como filas de la hoja de presupuesto, para cargarla al confirmar una contratación. */
  itemsDePlantilla(id: number): Observable<{ items: ItemValorizacion[]; total: number }> {
    return this.http.get<{ items: ItemValorizacion[]; total: number }>(`${this.base}/plantillas/${id}/items/`);
  }
}
