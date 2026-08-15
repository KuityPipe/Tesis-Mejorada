import { Injectable } from '@angular/core';

const CLAVE_TEMA = 'ks-theme';

export type Tema3Estados = 'light' | 'dark';

/**
 * Toggle de tema claro/oscuro manual — equivalente Ionic del botón de
 * `base.html` en el sitio Django (mismo criterio de tres estados: sin
 * elección guardada sigue la preferencia del SO, una elección explícita la
 * pisa en cualquier dirección). El bootstrap antes del primer pintado vive
 * en `src/index.html` (aplica `data-theme` desde `localStorage` antes de
 * que Angular cargue, para evitar el flash de tema incorrecto); este
 * servicio es lo que usa la UI en caliente para leer/cambiar el estado
 * después de eso. Los tres estados los interpreta `src/theme/variables.scss`
 * vía `[data-theme="dark"]`/`:not([data-theme="light"])`.
 */
@Injectable({ providedIn: 'root' })
export class Tema {
  /** Lee el atributo puesto en el `<html>` — null significa "sin elección explícita, sigue al SO". */
  obtenerElegido(): Tema3Estados | null {
    const valor = document.documentElement.getAttribute('data-theme');
    return valor === 'light' || valor === 'dark' ? valor : null;
  }

  /** Tema realmente en pantalla ahora mismo: la elección explícita si existe, si no la preferencia del SO. */
  obtenerActual(): Tema3Estados {
    const elegido = this.obtenerElegido();
    if (elegido) {
      return elegido;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  alternar(): void {
    this.aplicar(this.obtenerActual() === 'dark' ? 'light' : 'dark');
  }

  private aplicar(tema: Tema3Estados): void {
    document.documentElement.setAttribute('data-theme', tema);
    try {
      localStorage.setItem(CLAVE_TEMA, tema);
    } catch {
      /* localStorage bloqueado (modo privado): el cambio se aplica igual, solo no persiste. */
    }
  }
}
