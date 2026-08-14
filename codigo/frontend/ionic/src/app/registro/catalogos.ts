import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface RegionCatalogo {
  id_region: number;
  nombre_region: string;
}

export interface ComunaCatalogo {
  id_comuna: number;
  nombre_comuna: string;
  region_id: number;
}

export interface TipoCuentaCatalogo {
  id_tipo_cuenta: number;
  nombre_tipo_cuenta: string;
  valor_cuenta: number;
}

/** Catálogos de referencia fijos (`/api/catalogos/*`) — usados por los selects del formulario de registro. Sin paginar del lado del backend (son chicos: 16 regiones, 330 comunas, 4 tipos de cuenta). */
@Injectable({
  providedIn: 'root',
})
export class Catalogos {
  constructor(private readonly http: HttpClient) {}

  regiones(): Observable<RegionCatalogo[]> {
    return this.http.get<RegionCatalogo[]>(`${environment.apiUrl}/catalogos/regiones/`);
  }

  /** Equivalente API de `/ajax/load-comunas/` — el `<select>` de comuna se repuebla cada vez que cambia la región elegida (ver registro.page.ts). */
  comunas(regionId: number): Observable<ComunaCatalogo[]> {
    const params = new HttpParams().set('region', regionId);
    return this.http.get<ComunaCatalogo[]>(`${environment.apiUrl}/catalogos/comunas/`, { params });
  }

  tiposCuenta(): Observable<TipoCuentaCatalogo[]> {
    return this.http.get<TipoCuentaCatalogo[]>(`${environment.apiUrl}/catalogos/tipos-cuenta/`);
  }

  /** `GET /api/catalogos/categorias/` — lista fija de categorías de servicio (`CATEGORIAS_PUBLICACION`, forms.py), usada por el perfil de proveedor (`perfil/proveedor/proveedor.page.ts`). */
  categorias(): Observable<string[]> {
    return this.http.get<string[]>(`${environment.apiUrl}/catalogos/categorias/`);
  }
}
