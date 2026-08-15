import { Injectable } from '@angular/core';
import { BehaviorSubject, interval, Subscription } from 'rxjs';

import { Auth } from './auth';
import { Conversaciones } from '../mensajes/conversaciones';

const INTERVALO_MS = 15000;

/**
 * Polling del badge de mensajes no leídos — equivalente Ionic del script de
 * `base.html` en el sitio Django (mismo intervalo de 15s, mismo criterio de
 * "sonar solo si el conteo subió respecto de la última consulta", mismo
 * beep sintetizado con Web Audio, sin archivo externo). A diferencia de
 * Django (un único documento con un solo `<script>` por página cargada),
 * acá es un servicio singleton (`providedIn: 'root'`) para que el conteo
 * sobreviva la navegación entre páginas de Angular sin reiniciar el
 * intervalo ni perder el último valor conocido — se arranca una sola vez
 * desde `AppComponent`.
 *
 * El sonido respeta `Usuario.notificaciones_sonido` (mismo campo que
 * `PreferenciasCuentaForm`/`preferencias.page`) — se relee en cada tick vía
 * `Auth.me()` en vez de cachearlo, para que un cambio de preferencia hecho
 * en otra pestaña/dispositivo se refleje sin recargar.
 */
@Injectable({ providedIn: 'root' })
export class Notificaciones {
  private readonly _noLeidos$ = new BehaviorSubject<number>(0);
  readonly noLeidos$ = this._noLeidos$.asObservable();

  private suscripcion: Subscription | null = null;
  private ultimoConteo = 0;

  constructor(
    private readonly auth: Auth,
    private readonly conversaciones: Conversaciones,
  ) {}

  /** Arranca el polling si todavía no está corriendo — llamado una sola vez desde AppComponent. Sin efecto si ya estaba activo (p. ej. tras un logout/login sin recargar la página). */
  iniciar(): void {
    if (this.suscripcion) {
      return;
    }
    this.consultar();
    this.suscripcion = interval(INTERVALO_MS).subscribe(() => this.consultar());
  }

  private consultar(): void {
    if (!this.auth.estaAutenticado()) {
      return;
    }
    this.conversaciones.noLeidos().subscribe({
      next: ({ no_leidos }) => {
        if (no_leidos > this.ultimoConteo) {
          this.sonarSiCorresponde();
        }
        this.ultimoConteo = no_leidos;
        this._noLeidos$.next(no_leidos);
      },
      // Si falla una consulta (p. ej. token vencido), se reintenta en el siguiente intervalo — mismo criterio que el polling de Django.
      error: () => {},
    });
  }

  private sonarSiCorresponde(): void {
    this.auth.me().subscribe({
      next: (usuario) => {
        if (usuario.notificaciones_sonido) {
          this.sonarAlerta();
        }
      },
      error: () => {},
    });
  }

  /** Beep sintetizado con Web Audio API — mismo tono (880Hz, envolvente exponencial de 0.35s) que el de base.html, sin archivo de audio externo. */
  private sonarAlerta(): void {
    try {
      const AudioContextCtor = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioContextCtor();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.35);
    } catch {
      /* navegador sin soporte de Web Audio: falla en silencio, igual que en Django. */
    }
  }
}
