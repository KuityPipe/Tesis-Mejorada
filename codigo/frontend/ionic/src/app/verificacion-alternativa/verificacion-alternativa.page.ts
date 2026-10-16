import { Component, OnInit } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { EstadoVerificacionAlternativa, VerificacionAlternativa } from './verificacion-alternativa';

/**
 * Verificación de identidad SIN biometría: advertencia aceptada → código por correo → documento
 * de identidad → video corto con la cédula junto a la cara → revisión del staff. La biometría del teléfono (/biometria) sigue siendo la vía
 * principal; esta es más lenta y menos robusta, y se avisa explícitamente.
 */
@Component({
  selector: 'app-verificacion-alternativa',
  templateUrl: './verificacion-alternativa.page.html',
  styleUrls: ['./verificacion-alternativa.page.scss'],
  standalone: false,
})
export class VerificacionAlternativaPage implements OnInit {
  estado: EstadoVerificacionAlternativa | null = null;
  cargando = true;
  trabajando = false;
  error: string | null = null;

  aceptoAdvertencia = false;
  aceptoVideo = false;
  codigo = '';
  archivo: File | null = null;
  archivoVideo: File | null = null;

  constructor(private readonly api: VerificacionAlternativa) {}

  ngOnInit(): void {
    this.api.estado().subscribe({
      next: (estado) => {
        this.estado = estado;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
        this.error = 'No pudimos cargar tu estado de verificación.';
      },
    });
  }

  /** Paso en el que está la persona, para mostrar solo el formulario que corresponde. */
  get paso(): 'verificada' | 'revision' | 'advertencia' | 'codigo' | 'documento' | 'video' {
    const e = this.estado;
    if (!e) return 'advertencia';
    if (e.identidad_verificada) return 'verificada';
    const faltaVideo = e.requiere_video && !e.video_enviado;
    if (e.estado === 'PENDIENTE_REVISION' && !faltaVideo) return 'revision';
    if (!e.advertencia_aceptada) return 'advertencia';
    if (!e.correo_verificado) return 'codigo';
    if (!e.documento_enviado) return 'documento';
    return faltaVideo ? 'video' : 'revision';
  }

  /** Para habilitar el botón del primer paso: la advertencia siempre, y la grabación solo si el servidor exige video. */
  get puedeIniciar(): boolean {
    return this.aceptoAdvertencia && (!this.estado?.requiere_video || this.aceptoVideo);
  }

  iniciar(): void {
    this.ejecutar(this.api.iniciar(this.aceptoVideo));
  }

  confirmarCodigo(): void {
    this.ejecutar(this.api.confirmarCodigo(this.codigo.trim()));
  }

  seleccionarArchivo(evento: Event): void {
    this.archivo = (evento.target as HTMLInputElement).files?.[0] ?? null;
  }

  seleccionarVideo(evento: Event): void {
    this.archivoVideo = (evento.target as HTMLInputElement).files?.[0] ?? null;
  }

  enviarVideo(): void {
    if (this.archivoVideo) {
      this.ejecutar(this.api.enviarVideo(this.archivoVideo));
    }
  }

  enviarDocumento(): void {
    if (this.archivo) {
      this.ejecutar(this.api.enviarDocumento(this.archivo));
    }
  }

  private ejecutar(peticion: ReturnType<VerificacionAlternativa['iniciar']>): void {
    if (this.trabajando) {
      return;
    }
    this.trabajando = true;
    this.error = null;
    peticion.subscribe({
      next: (estado) => {
        this.estado = estado;
        this.trabajando = false;
      },
      error: (error: HttpErrorResponse) => {
        this.error = error.error?.detail ?? 'No pudimos completar este paso. Intenta nuevamente.';
        this.trabajando = false;
      },
    });
  }
}
