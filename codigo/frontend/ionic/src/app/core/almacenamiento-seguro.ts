import { Injectable } from '@angular/core';
import { SecureStoragePlugin } from 'capacitor-secure-storage-plugin';

/**
 * Wrapper fino sobre `capacitor-secure-storage-plugin` — Keychain en iOS,
 * `EncryptedSharedPreferences` (Android Keystore) en Android nativo. En web
 * (`ng serve`/build de navegador, no la app nativa) el plugin ya trae su
 * propio fallback a `localStorage` (con un prefijo `cap_sec_` y valores en
 * base64, ver su `web.ts`) — **no cifrado de verdad en ese caso**, pero es
 * el único terreno común posible en un navegador; sigue siendo mejor que
 * nada y no hace falta ninguna rama `Capacitor.isNativePlatform()` acá, el
 * plugin ya resuelve cuál implementación usar solo.
 *
 * Reemplaza el uso directo de `localStorage` para los tokens JWT en
 * `Auth` (ver auth.ts) — la razón por la que existía ese TODO en
 * CLAUDE.md/docs/PLAN_MIGRACION_IONIC.md ("Hardening"): `localStorage` no
 * está cifrado en disco, y ni `@capacitor/preferences` tampoco.
 */
@Injectable({ providedIn: 'root' })
export class AlmacenamientoSeguro {
  /** `undefined` (no `null`) si la clave nunca se guardó — el plugin rechaza la promesa en ese caso en vez de resolver con un valor vacío. */
  async obtener(clave: string): Promise<string | undefined> {
    try {
      const { value } = await SecureStoragePlugin.get({ key: clave });
      return value;
    } catch {
      return undefined;
    }
  }

  async guardar(clave: string, valor: string): Promise<void> {
    await SecureStoragePlugin.set({ key: clave, value: valor });
  }

  async eliminar(clave: string): Promise<void> {
    try {
      await SecureStoragePlugin.remove({ key: clave });
    } catch {
      /* la clave ya no existía — mismo resultado final que borrarla. */
    }
  }
}
