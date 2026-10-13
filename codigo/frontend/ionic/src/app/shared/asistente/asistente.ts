import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { Asistente, MensajeAsistente, ServicioSugerido } from '../../core/asistente';

interface BurbujaAsistente {
  rol: 'user' | 'assistant';
  texto: string;
  servicios?: ServicioSugerido[];
}

/**
 * Botón flotante + panel de chat del asistente (preguntas frecuentes y búsqueda en el catálogo), disponible en
 * todas las pantallas. El historial vive solo en memoria: al recargar la app se pierde, a propósito (privacidad).
 * Con aviso visible de que usa un servicio de IA externo y de que no hay que escribir datos personales.
 */
@Component({
  selector: 'app-asistente',
  templateUrl: './asistente.html',
  styleUrls: ['./asistente.scss'],
  standalone: false,
})
export class AsistenteComponent {
  abierto = false;
  enviando = false;
  texto = '';
  error: string | null = null;
  avisoIa = 'Este chat usa un servicio de inteligencia artificial externo. No escribas datos personales (RUT, correo, teléfono, tarjetas).';
  sugerencias = ['¿Cómo contrato un servicio?', '¿Cómo funciona la verificación de identidad?', '¿Cómo protegen mis datos?', 'Busco un gasfíter'];
  burbujas: BurbujaAsistente[] = [
    { rol: 'assistant', texto: '¡Hola! Soy el asistente de KeyServ. Puedo explicarte cómo funciona la plataforma o ayudarte a encontrar un servicio.' },
  ];

  @ViewChild('campo') campo?: ElementRef<HTMLInputElement>;
  @ViewChild('registro') registro?: ElementRef<HTMLElement>;

  constructor(private readonly asistente: Asistente) {}

  alternar(): void {
    this.abierto = !this.abierto;
    if (this.abierto) {
      setTimeout(() => this.campo?.nativeElement.focus(), 50);
    }
  }

  @HostListener('document:keydown.escape')
  cerrarConEscape(): void {
    if (this.abierto) {
      this.abierto = false;
    }
  }

  usarSugerencia(sugerencia: string): void {
    this.texto = sugerencia;
    this.enviar();
  }

  enviar(): void {
    const texto = this.texto.trim();
    if (!texto || this.enviando) {
      return;
    }
    this.burbujas.push({ rol: 'user', texto });
    this.texto = '';
    this.error = null;
    this.enviando = true;
    this.desplazar();

    // Solo mensajes de texto: nunca viaja nada más que lo que la persona escribió y las respuestas previas.
    const historial: MensajeAsistente[] = this.burbujas.map((b) => ({ rol: b.rol, texto: b.texto }));
    this.asistente.preguntar(historial).subscribe({
      next: (r) => {
        this.burbujas.push({ rol: 'assistant', texto: r.respuesta, servicios: r.servicios });
        this.avisoIa = r.aviso_ia || this.avisoIa;
        this.sugerencias = r.sugerencias?.length ? r.sugerencias : this.sugerencias;
        this.enviando = false;
        this.desplazar();
      },
      error: (error: HttpErrorResponse) => {
        this.error =
          error.status === 429
            ? 'Has usado el asistente muchas veces seguidas. Prueba de nuevo en unos minutos.'
            : 'No pudimos responder ahora. Inténtalo nuevamente o usa el formulario de contacto.';
        this.enviando = false;
      },
    });
  }

  precio(servicio: ServicioSugerido): string {
    return servicio.precio ? `$${servicio.precio.toLocaleString('es-CL')}` : 'Precio a convenir';
  }

  private desplazar(): void {
    setTimeout(() => {
      const el = this.registro?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }, 0);
  }
}
