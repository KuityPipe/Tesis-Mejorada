import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Camera } from '@capacitor/camera';
import { Capacitor } from '@capacitor/core';

import { Rostro } from './rostro';

const DURACION_CAPTURA_MS = 2000;
const INTERVALO_FRAME_MS = 120;

/**
 * Reconocimiento facial por cámara — equivalente Ionic de `/rostro/`
 * (`rostro_view`/`registro_rostro_view`/`verificacion_facial_view`),
 * puerto directo de la prueba de vida por parpadeo de
 * `_captura_camara.html`/`rostro.html` (mismos `DURACION_CAPTURA_MS`/
 * `INTERVALO_FRAME_MS`) a TypeScript. `getUserMedia` funciona igual en un
 * navegador de escritorio/móvil que dentro del WebView de una build
 * nativa de Capacitor — no hace falta un plugin de cámara para la
 * captura en sí. `@capacitor/camera` se usa solo una vez, al entrar a la
 * pantalla, para "cebar" el permiso real de cámara de Android/iOS
 * (`Camera.requestPermissions`) — sin eso, `getUserMedia` puede fallar
 * silenciosamente en una build nativa aunque el manifiesto ya declare el
 * permiso. No se guarda ninguna foto tomada por `@capacitor/camera` en
 * sí — solo se usa por su efecto secundario de pedir el permiso.
 *
 * A diferencia de la biometría nativa (`biometria.page`), acá el
 * navegador SÍ manda datos biométricos reales (los cuadros) al
 * servidor — coherente con que el reconocimiento facial es el método
 * alternativo para cuando no hay Face ID/huella nativos disponibles.
 */
@Component({
  selector: 'app-rostro',
  templateUrl: './rostro.page.html',
  styleUrls: ['./rostro.page.scss'],
  standalone: false,
})
export class RostroPage implements OnInit, OnDestroy {
  @ViewChild('video') videoRef!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvas') canvasRef!: ElementRef<HTMLCanvasElement>;

  cargando = true;
  tieneReferencia = false;
  // 'registrar' cuando todavía no hay rostro de referencia; 'verificar' es
  // el modo por defecto una vez que ya existe uno (mismo criterio que
  // rostro.html) — el usuario puede volver a 'registrar' si quiere
  // reemplazarlo.
  modo: 'registrar' | 'verificar' = 'registrar';

  camaraActiva = false;
  capturando = false;
  instruccion = 'Mirá a la cámara y capturá — vas a tener que parpadear una vez durante la captura.';
  error: string | null = null;
  exito: string | null = null;
  enviando = false;

  private stream: MediaStream | null = null;

  constructor(private readonly rostroApi: Rostro) {}

  ngOnInit(): void {
    if (Capacitor.isNativePlatform()) {
      // Solo pide el permiso nativo — no se usa el resultado, ver el
      // comentario de la clase.
      Camera.requestPermissions({ permissions: ['camera'] }).catch(() => {
        // Si el usuario lo rechaza acá, el error real y más específico
        // igual va a aparecer al intentar getUserMedia más abajo.
      });
    }

    this.rostroApi.estado().subscribe({
      next: (respuesta) => {
        this.tieneReferencia = respuesta.tiene_referencia;
        this.modo = this.tieneReferencia ? 'verificar' : 'registrar';
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  ngOnDestroy(): void {
    this.detenerCamara();
  }

  cambiarModo(modo: 'registrar' | 'verificar'): void {
    this.modo = modo;
    this.error = null;
    this.exito = null;
  }

  async iniciarCamara(): Promise<void> {
    this.error = null;
    if (!navigator.mediaDevices?.getUserMedia) {
      this.error = 'Este navegador no soporta acceso a la cámara — no se puede continuar sin ella.';
      return;
    }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      this.videoRef.nativeElement.srcObject = this.stream;
      this.camaraActiva = true;
    } catch {
      this.error = 'No se pudo acceder a la cámara (¿denegaste el permiso?) — no se puede continuar sin ella.';
    }
  }

  private detenerCamara(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.camaraActiva = false;
  }

  async capturar(): Promise<void> {
    if (this.capturando) {
      return;
    }
    this.capturando = true;
    this.error = null;
    this.exito = null;
    this.instruccion = 'Parpadeá una vez mientras se captura…';

    const video = this.videoRef.nativeElement;
    const canvas = this.canvasRef.nativeElement;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const contexto = canvas.getContext('2d')!;

    const cuadrosTotales = Math.round(DURACION_CAPTURA_MS / INTERVALO_FRAME_MS);
    const frames: File[] = [];

    while (frames.length < cuadrosTotales) {
      contexto.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85));
      if (blob) {
        frames.push(new File([blob], `captura-${frames.length}.jpg`, { type: 'image/jpeg' }));
      }
      if (frames.length < cuadrosTotales) {
        await new Promise((resolve) => setTimeout(resolve, INTERVALO_FRAME_MS));
      }
    }

    this.instruccion = 'Mirá a la cámara y capturá — vas a tener que parpadear una vez durante la captura.';
    this.enviarCaptura(frames);
  }

  private enviarCaptura(frames: File[]): void {
    this.enviando = true;

    if (this.modo === 'registrar') {
      this.rostroApi.registrar(frames).subscribe({
        next: () => {
          this.alTenerExito('Rostro registrado. Ahora podés verificarlo.');
          this.tieneReferencia = true;
          this.modo = 'verificar';
        },
        error: (error: HttpErrorResponse) => this.alFallar(error),
      });
    } else {
      this.rostroApi.verificar(frames).subscribe({
        next: () => this.alTenerExito('¡Rostro verificado correctamente!'),
        error: (error: HttpErrorResponse) => this.alFallar(error),
      });
    }
  }

  private alTenerExito(mensaje: string): void {
    this.enviando = false;
    this.capturando = false;
    this.detenerCamara();
    this.exito = mensaje;
  }

  private alFallar(error: HttpErrorResponse): void {
    this.enviando = false;
    this.capturando = false;
    this.error = error.error?.detail ?? 'No se pudo validar la captura — probá de nuevo.';
    // Se queda con la cámara prendida para reintentar, mismo criterio que rostro.html.
  }
}
