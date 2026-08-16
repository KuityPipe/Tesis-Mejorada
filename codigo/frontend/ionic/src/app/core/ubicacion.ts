import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';
import { Geolocation } from '@capacitor/geolocation';

export interface Coordenada {
  lat: number;
  lng: number;
}

/**
 * Posición real del dispositivo (GPS/red), para el filtro de radio del
 * catálogo (ver catalogo.page.ts) — `@capacitor/geolocation` cubre web
 * (wrappea `navigator.geolocation` por debajo) y nativo con la misma API de
 * `getCurrentPosition()`.
 *
 * `requestPermissions()` sí hay que distinguirlo por plataforma —
 * verificado en vivo contra `:8100` real: la implementación web del plugin
 * no lo tiene implementado (`throw this.unimplemented('Not implemented on
 * web.')`, ver node_modules/@capacitor/geolocation/dist/esm/web.js), así
 * que llamarlo sin más en web siempre caía al `catch` de abajo y el botón
 * no hacía nada — un bug real, no solo teórico. En web no hace falta
 * pedirlo antes: el propio navegador muestra su prompt nativo de permiso
 * la primera vez que se llama a `getCurrentPosition()`.
 *
 * Sin fallback a la comuna guardada del usuario todavía (ver
 * docs/BACKLOG.md, "Búsqueda por geolocalización") — queda para una
 * siguiente sesión; por ahora, sin geolocalización real el filtro de radio
 * simplemente no aparece.
 */
@Injectable({
  providedIn: 'root',
})
export class Ubicacion {
  /** `null` si el usuario niega el permiso o el dispositivo no puede resolver la posición — nunca revienta, el catálogo sigue funcionando sin el filtro de radio. */
  async posicionActual(): Promise<Coordenada | null> {
    try {
      if (Capacitor.isNativePlatform()) {
        const permiso = await Geolocation.requestPermissions();
        if (permiso.location !== 'granted' && permiso.coarseLocation !== 'granted') {
          return null;
        }
      }
      // `enableHighAccuracy: true` — verificado en vivo en el emulador
      // Android: con `false` (proveedor de red) la llamada da timeout
      // siempre ahí, porque `adb emu geo fix` solo alimenta al proveedor
      // GPS, no al de red — y de todos modos, para un botón que el usuario
      // toca activamente esperando su ubicación (no un tracking pasivo en
      // segundo plano), vale la pena pedir la posición más precisa con más
      // margen de tiempo.
      const posicion = await Geolocation.getCurrentPosition({ enableHighAccuracy: true, timeout: 15000 });
      return { lat: posicion.coords.latitude, lng: posicion.coords.longitude };
    } catch {
      return null;
    }
  }
}
